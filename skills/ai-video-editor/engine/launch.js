// launch.js — the Launch Studio stage for HyperFrames (v2, 2026-10-06).
// A real 3D camera over HTML panels (any live HTML/CSS, painted into a texture), a ground with the brand's paper
// texture, depth of field from a true depth pass (transparent pixels of a panel don't count as "near"), film grain +
// vignette, and TRUE motion blur: each output frame averages N sub-frames spread across the shutter (180° default),
// every one a full render at its own instant. Deterministic: everything is a function of HyperFrames time.
import * as THREE from "three";

export { THREE };

const QUAD_VS = "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }";
const MESH_VS = "varying vec2 vUv; varying float vZ; void main(){ vUv = uv; vec4 mv = modelViewMatrix * vec4(position, 1.0); vZ = -mv.z; gl_Position = projectionMatrix * mv; }";
const RBOX = "float rbox(vec2 p, vec2 b, float r){ vec2 q = abs(p) - b + r; return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r; }";

export class Stage {
  constructor(opts) {
    const o = (this.o = Object.assign(
      {
        width: 1080, height: 1920, fps: 30, samples: 8, shutter: 180, fov: 32, background: "#fbf9f4",
        dof: { strength: 34, max: 40 }, grain: 0.028, vignette: 0.14, exposure: 1.0, bloom: null, // bloom: { strength, threshold }
        transparent: false, // true: a clear background and real alpha out (logo clips to lay over the face) — use with
                            // dof: null, bloom: null, grain: 0, vignette: 0, no edge light, and render --format mov
      },
      opts,
    ));
    const W = o.width, H = o.height;
    const r = (this.renderer = new THREE.WebGLRenderer({
      canvas: o.canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: "high-performance", alpha: !!o.transparent,
    }));
    r.setPixelRatio(1);
    r.setSize(W, H, false);
    r.outputColorSpace = THREE.SRGBColorSpace;
    r.toneMapping = THREE.NoToneMapping; // brand colours stay exact: no filmic curve on UI
    this.scene = new THREE.Scene();
    this.bg = new THREE.Color(o.background);
    this.camera = new THREE.PerspectiveCamera(o.fov, W / H, 0.05, 200);
    this.camera.position.set(0, 0, this.unitDistance());
    this.scene.add(this.camera); // HUD panels are its children
    // the camera rig GSAP animates: position, target, roll, fov, focus (null = auto-focus on the target)
    this.cam = { x: 0, y: 0, z: this.unitDistance(), tx: 0, ty: 0, tz: 0, roll: 0, fov: o.fov, focus: null, aperture: 1 };

    this.colorRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
    this.depthRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.FloatType, samples: 0, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter });
    this.dofRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
    this.accum = new THREE.WebGLRenderTarget(W, H, { type: THREE.FloatType });
    this.quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    const quad = (mat) => { const s = new THREE.Scene(); s.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat)); return s; };

    this.dofMat = new THREE.ShaderMaterial({
      uniforms: {
        tColor: { value: this.colorRT.texture }, tDepth: { value: this.depthRT.texture }, res: { value: new THREE.Vector2(W, H) },
        focus: { value: 3.3 }, strength: { value: o.dof ? o.dof.strength : 0 }, maxCoc: { value: o.dof ? o.dof.max : 0 }, spin: { value: 0 },
      },
      vertexShader: QUAD_VS,
      fragmentShader: `
        uniform sampler2D tColor, tDepth; uniform vec2 res; uniform float focus, strength, maxCoc, spin; varying vec2 vUv;
        float coc(float z){ return min(maxCoc, strength * abs(z - focus) / max(z, 0.01)); }
        void main(){
          float zc = texture2D(tDepth, vUv).r; float cc = coc(zc);
          vec4 base = texture2D(tColor, vUv);
          if (cc < 0.6) { gl_FragColor = base; return; }
          vec3 acc = base.rgb; float wsum = 1.0;
          for (int i = 0; i < 40; i++) {
            float fi = float(i) + 0.5; float rr = sqrt(fi / 40.0); float th = fi * 2.39996323 + spin;
            vec2 o = vec2(cos(th), sin(th)) * rr * cc / res;
            float zs = texture2D(tDepth, vUv + o).r; float cs = coc(zs);
            // a nearer sample only reaches here if its own blur covers the distance (no sharp-object halos)
            float w = zs < zc - 0.02 ? clamp(cs / max(rr * cc, 0.001), 0.0, 1.0) : 1.0;
            acc += texture2D(tColor, vUv + o).rgb * w; wsum += w;
          }
          gl_FragColor = vec4(acc / wsum, 1.0);
        }`,
      depthTest: false, depthWrite: false, toneMapped: false,
    });
    this.dofScene = quad(this.dofMat);
    this.addMat = new THREE.ShaderMaterial({
      uniforms: { tDiffuse: { value: this.dofRT.texture }, weight: { value: 1 } },
      vertexShader: QUAD_VS,
      fragmentShader: "uniform sampler2D tDiffuse; uniform float weight; varying vec2 vUv;" +
        "void main(){ vec4 t = texture2D(tDiffuse, vUv); gl_FragColor = vec4(t.rgb * weight, t.a * weight); }",   // alpha too (coverage, for transparent stages)
      blending: THREE.CustomBlending, blendEquation: THREE.AddEquation, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor,
      depthTest: false, depthWrite: false, transparent: true, toneMapped: false,
    });
    this.addScene = quad(this.addMat);
    this.presentMat = new THREE.ShaderMaterial({
      uniforms: {
        tAccum: { value: this.accum.texture }, seed: { value: 0 }, grain: { value: o.grain }, alphaOut: { value: o.transparent ? 1 : 0 },
        vignette: { value: o.vignette }, exposure: { value: o.exposure }, aspect: { value: W / H }, flash: { value: 0 },
        flashColor: { value: new THREE.Vector3(1, 1, 1) }, // display-space RGB
        edgeColor: { value: new THREE.Color("#ff1e3c") }, edge: { value: 0 }, edgeWidth: { value: 0.22 },
        // the depth pass made visible (white = near, black = far), left of depthSplit (0..1 of the width); 0 = off
        tDepth: { value: this.depthRT.texture }, depthView: { value: 0 }, depthSplit: { value: 1 }, depthNear: { value: 1 }, depthFar: { value: 8 },
      },
      vertexShader: QUAD_VS,
      fragmentShader: `
        uniform sampler2D tAccum, tBloomA, tBloomB, tDepth; uniform float seed, grain, vignette, exposure, aspect, flash, bloom, edge, edgeWidth, alphaOut;
        uniform float depthView, depthSplit, depthNear, depthFar; uniform vec3 flashColor, edgeColor; varying vec2 vUv;
        float hash(vec2 p){ p = fract(p * vec2(443.897, 441.423)); p += dot(p, p.yx + 19.19); return fract((p.x + p.y) * p.x); }
        void main(){
          vec3 c = texture2D(tAccum, vUv).rgb * exposure;
          c += bloom * (texture2D(tBloomA, vUv).rgb * 0.6 + texture2D(tBloomB, vUv).rgb * 0.8);
          vec2 d = (vUv - 0.5) * vec2(aspect, 1.0);
          c *= 1.0 - vignette * smoothstep(0.25, 0.95, length(d) * 1.35);
          // edge light: soft colour pouring in from the left and right edges, strongest at mid-height (a lit room)
          float ex = min(vUv.x, 1.0 - vUv.x) / edgeWidth;
          float ey = 1.0 - smoothstep(0.0, 0.62, abs(vUv.y - 0.52));
          c += edgeColor * edge * exp(-ex * ex * 1.6) * (0.35 + 0.65 * ey);
          if (depthView > 0.0) {
            float zv = 1.0 - smoothstep(depthNear, depthFar, texture2D(tDepth, vUv).r);
            c = mix(c, vec3(zv * zv), depthView * step(vUv.x, depthSplit));
            float ln = (vUv.x - depthSplit) * aspect * 540.0;
            c += edgeColor * 2.4 * depthView * exp(-ln * ln) * step(0.001, depthSplit) * step(depthSplit, 0.999);
          }
          gl_FragColor = vec4(c, mix(1.0, clamp(texture2D(tAccum, vUv).a, 0.0, 1.0), alphaOut));
          #include <colorspace_fragment>
          // the flash mixes in DISPLAY space: in linear light a 0.14 flash lifted black to 41% grey (10-06)
          gl_FragColor.rgb = mix(gl_FragColor.rgb, flashColor, flash);
          float n = hash(gl_FragCoord.xy + seed * 17.13) + hash(gl_FragCoord.xy * 1.7 - seed * 3.71) - 1.0;
          gl_FragColor.rgb += n * grain * (0.6 + 0.4 * (1.0 - dot(gl_FragColor.rgb, vec3(0.333))));
        }`,
      depthTest: false, depthWrite: false, toneMapped: false,
    });
    this.presentScene = quad(this.presentMat);
    // bloom (for dark brands): bright parts of the finished (motion-blurred) frame, blurred at 1/4 and 1/8 res, added back
    this.bloomOn = !!o.bloom;
    const bw = Math.round(W / 4), bh = Math.round(H / 4);
    const brt = (w, h) => new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType });
    this.bl = [brt(bw, bh), brt(bw, bh), brt(Math.round(bw / 2), Math.round(bh / 2)), brt(Math.round(bw / 2), Math.round(bh / 2))];
    this.brightMat = new THREE.ShaderMaterial({
      uniforms: { tSrc: { value: this.accum.texture }, threshold: { value: o.bloom ? o.bloom.threshold : 0.8 } },
      vertexShader: QUAD_VS,
      fragmentShader: `uniform sampler2D tSrc; uniform float threshold; varying vec2 vUv;
        void main(){ vec3 c = texture2D(tSrc, vUv).rgb; float l = max(c.r, max(c.g, c.b));
          float k = smoothstep(threshold, threshold + 0.25, l); gl_FragColor = vec4(c * k, 1.0); }`,
      depthTest: false, depthWrite: false, toneMapped: false,
    });
    this.blurMat = new THREE.ShaderMaterial({
      uniforms: { tSrc: { value: null }, dir: { value: new THREE.Vector2(1, 0) } },
      vertexShader: QUAD_VS,
      fragmentShader: `uniform sampler2D tSrc; uniform vec2 dir; varying vec2 vUv;
        void main(){ vec3 a = vec3(0.0); float ws = 0.0;
          for (int i = -6; i <= 6; i++) { float w = exp(-float(i * i) / 18.0); a += texture2D(tSrc, vUv + dir * float(i)).rgb * w; ws += w; }
          gl_FragColor = vec4(a / ws, 1.0); }`,
      depthTest: false, depthWrite: false, toneMapped: false,
    });
    this.copyMat = new THREE.ShaderMaterial({
      uniforms: { tSrc: { value: null } }, vertexShader: QUAD_VS,
      fragmentShader: "uniform sampler2D tSrc; varying vec2 vUv; void main(){ gl_FragColor = vec4(texture2D(tSrc, vUv).rgb, 1.0); }",
      depthTest: false, depthWrite: false, toneMapped: false,
    });
    this.brightScene = quad(this.brightMat); this.blurScene = quad(this.blurMat); this.copyScene = quad(this.copyMat);
    this.presentMat.uniforms.tBloomA = { value: this.bl[0].texture };
    this.presentMat.uniforms.tBloomB = { value: this.bl[2].texture };
    this.presentMat.uniforms.bloom = { value: o.bloom ? o.bloom.strength : 0 };
    this.panels = [];
    this.depthMeshes = [];
  }

  renderBloom() {
    const r = this.renderer, [a, b, c, d] = this.bl;
    r.setRenderTarget(a); r.render(this.brightScene, this.quadCam);
    const blur = (src, dst, dx, dy) => { this.blurMat.uniforms.tSrc.value = src.texture; this.blurMat.uniforms.dir.value.set(dx / src.width, dy / src.height); r.setRenderTarget(dst); r.render(this.blurScene, this.quadCam); };
    blur(a, b, 1, 0); blur(b, a, 0, 1);                  // 1/4 res
    this.copyMat.uniforms.tSrc.value = a.texture; r.setRenderTarget(c); r.render(this.copyScene, this.quadCam);
    blur(c, d, 1.5, 0); blur(d, c, 0, 1.5);              // 1/8 res, wider
  }

  // Pin a panel to the camera, x/y in CSS px from the frame centre (y down): it rides every move (whips, rolls, shakes)
  // and stays sharp — its depth is reported as the focus distance. dist only has to be nearer than anything in the scene.
  hud(panel, { x = 0, y = 0, dist = 0.5 } = {}) {
    const k = dist / this.unitDistance();
    panel.group.removeFromParent();
    this.camera.add(panel.group);
    panel.group.scale.setScalar(k);
    panel.group.position.set((x / 1000) * k, (-y / 1000) * k, -dist);
    panel.hud = true;
    return panel;
  }

  // Studio light for real 3D objects (devices): a soft room reflected in every surface + a key, a fill and a rim.
  // HTML panels ignore light (they are the brand's own pixels); only PBR materials (loaded models) use it.
  async studio({ env = 1.0, key = 2.4, fill = 0.7, rim = 1.6, warm = "#fff4e8", cool = "#e8f0ff" } = {}) {
    const { RoomEnvironment } = await import("three/addons/environments/RoomEnvironment.js");
    const pm = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene.environmentIntensity = env;
    pm.dispose();
    const k = new THREE.DirectionalLight(warm, key); k.position.set(-3, 4, 5); this.scene.add(k);
    const f = new THREE.DirectionalLight(cool, fill); f.position.set(4, -1, 3); this.scene.add(f);
    const r = new THREE.DirectionalLight("#ffffff", rim); r.position.set(2, 3, -4); this.scene.add(r);
    return { key: k, fill: f, rim: r };
  }

  // the camera distance at which a plane at z=0 shows 1 world unit (= 1000 CSS px) as 1000 screen px
  unitDistance() { return (this.o.height / 1000) / 2 / Math.tan((this.o.fov * Math.PI) / 360); }

  applyCamera() {
    const c = this.cam, cam = this.camera;
    cam.position.set(c.x, c.y, c.z);
    cam.up.set(Math.sin(c.roll), Math.cos(c.roll), 0);
    cam.lookAt(c.tx, c.ty, c.tz);
    if (cam.fov !== c.fov) { cam.fov = c.fov; cam.updateProjectionMatrix(); }
    const f = c.focus != null && c.focus > 0 ? c.focus : Math.hypot(c.x - c.tx, c.y - c.ty, c.z - c.tz); // focus ≤ 0: auto
    this.dofMat.uniforms.focus.value = f;
    for (const p of this.panels) if (p.hud) p.dmat.uniforms.fixedZ.value = f;
    this.dofMat.uniforms.strength.value = (this.o.dof ? this.o.dof.strength : 0) * c.aperture;
  }

  renderOnce() {
    const r = this.renderer, s = this.scene;
    // depth pass: every mesh draws its own depth material (panels discard their transparent pixels)
    const swapped = [];
    s.traverse((m) => { if (m.isMesh) { swapped.push([m, m.material, m.visible, m.onBeforeRender]); if (m.isReflector) m.onBeforeRender = () => {}; // no mirror render in the depth pass
      if (m.userData.depthMat) m.material = m.userData.depthMat; else m.visible = false; } });
    const bg = s.background; s.background = null;
    r.setRenderTarget(this.depthRT); r.setClearColor(0x000000, 1); r.clearColor();
    this.depthClear || (this.depthClear = new THREE.Color(100, 100, 100));
    r.setClearColor(this.depthClear, 1); r.clear();
    r.render(s, this.camera);
    for (const [m, mat, vis, obr] of swapped) { m.material = mat; m.visible = vis; m.onBeforeRender = obr; }
    s.background = this.o.transparent ? null : this.bg;
    r.setRenderTarget(this.colorRT); r.setClearColor(this.bg, this.o.transparent ? 0 : 1); r.clear();
    r.render(s, this.camera);
    s.background = bg;
    r.setRenderTarget(this.dofRT);
    r.render(this.dofScene, this.quadCam);
  }

  // Render HyperFrames time t. apply(ts) puts the whole scene in its state at ts (seek the timeline, sync).
  render(t, apply) {
    const o = this.o, r = this.renderer, N = Math.max(1, o.samples | 0);
    const shutter = o.shutter / 360 / o.fps;
    apply(t);
    for (const p of this.panels) if ((p.live && p.group.visible) || !p.captured) p.capture();
    r.setRenderTarget(this.accum); r.setClearColor(0x000000, 0); r.clear();
    const autoClear = r.autoClear;
    for (let k = 0; k < N; k++) {
      const ts = N === 1 ? t : Math.max(0, t - shutter / 2 + (shutter * (k + 0.5)) / N);
      apply(ts);
      this.applyCamera();
      this.dofMat.uniforms.spin.value = k * 0.7853981;
      this.renderOnce();
      this.addMat.uniforms.weight.value = 1 / N;
      r.setRenderTarget(this.accum);
      r.autoClear = false; // the sub-frames ADD into the buffer: an auto-clear kept only the last one (grey frames, 10-06)
      r.render(this.addScene, this.quadCam);
      r.autoClear = autoClear;
    }
    apply(t); this.applyCamera();
    if (this.bloomOn) this.renderBloom();
    this.presentMat.uniforms.seed.value = Math.round(t * o.fps);
    r.setRenderTarget(null);
    r.render(this.presentScene, this.quadCam);
  }
}

export function depthMaterial(map, extra = "") {   // exported 10-07: 3D logos (gfx.js logo3d) need it to sit at their true depth
  return new THREE.ShaderMaterial({
    uniforms: { map: { value: map }, size: { value: new THREE.Vector2(1, 1) }, radius: { value: 0 }, opacity: { value: 1 }, fixedZ: { value: -1 } },
    vertexShader: MESH_VS,
    fragmentShader: `uniform sampler2D map; uniform vec2 size; uniform float radius, opacity, fixedZ; varying vec2 vUv; varying float vZ; ${RBOX}
      void main(){
        float a = ${map ? "texture2D(map, vUv).a" : "1.0"} * opacity;
        if (radius > 0.0 && rbox((vUv - 0.5) * size, size * 0.5, radius) > 0.0) a = 0.0;
        ${extra}
        if (a < 0.35) discard;
        gl_FragColor = vec4(fixedZ > 0.0 ? fixedZ : vZ, 0.0, 0.0, 1.0);
      }`,
    side: THREE.DoubleSide,
  });
}

// The ground: a large plane behind everything in the brand's canvas colour with its paper texture (dot grid).
// color is animatable: ground.color (THREE.Color) — tween ground.mix 0→1 between colorA and colorB.
export function ground(stage, { colorA = "#fbf9f4", colorB = "#1a1a1a", dots = 0.07, spacing = 22, z = -1.6, size = 40 } = {}) {
  const mat = new THREE.ShaderMaterial({
    uniforms: { a: { value: new THREE.Color(colorA) }, b: { value: new THREE.Color(colorB) }, mixv: { value: 0 },
                dots: { value: dots }, spacing: { value: spacing }, size: { value: size } },
    vertexShader: MESH_VS,
    fragmentShader: `uniform vec3 a, b; uniform float mixv, dots, spacing, size; varying vec2 vUv;
      void main(){
        vec3 c = mix(a, b, mixv);
        vec2 px = vUv * size * 1000.0 / spacing;                 // world px / spacing
        vec2 g = fract(px) - 0.5; float d = length(g * spacing);
        float dot1 = 1.0 - smoothstep(0.7, 1.4, d);
        vec3 ink = mix(vec3(0.0), vec3(1.0), mixv);
        gl_FragColor = vec4(mix(c, ink, dot1 * dots), 1.0);
        #include <colorspace_fragment>
      }`,
    toneMapped: false,
  });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(size, size), mat);
  mesh.position.z = z;
  mesh.userData.depthMat = depthMaterial(null);
  stage.scene.add(mesh);
  return { mesh, mat, get mix() { return mat.uniforms.mixv.value; }, set mix(v) { mat.uniforms.mixv.value = v; } };
}

// A textured plane: rounded corners, optional soft shadow, opacity, a sheen sweep and a dim (state.* tweenable).
// 1 world unit = 1000 CSS px; radius/shadow in CSS px.
function plane(stage, tex, { w, h, radius = 0, shadow = null, opacity = 1, sheen = false }) {
  const U = 1 / 1000, pw = w * U, ph = h * U;
  const group = new THREE.Group();
  const mat = new THREE.ShaderMaterial({
    uniforms: { map: { value: tex }, size: { value: new THREE.Vector2(w, h) }, radius: { value: radius }, opacity: { value: opacity },
                sheenPos: { value: -1 }, sheenAmt: { value: sheen ? 0.16 : 0 }, dim: { value: 0 }, glow: { value: 0 },
                // stage.dimTo (a light theme's ground): dim FADES the panel toward the ground instead of darkening it
                dimTo: { value: stage.dimTo || new THREE.Color(0, 0, 0) }, dimFade: { value: stage.dimTo ? 1 : 0 } },
    vertexShader: MESH_VS,
    fragmentShader: `uniform sampler2D map; uniform vec2 size; uniform float radius, opacity, sheenPos, sheenAmt, dim, glow, dimFade; uniform vec3 dimTo; varying vec2 vUv; ${RBOX}
      void main(){
        vec4 c = texture2D(map, vUv);
        float d = rbox((vUv - 0.5) * size, size * 0.5, radius);
        float a = c.a * opacity * (radius > 0.0 ? 1.0 - smoothstep(-0.75, 0.75, d) : 1.0);
        float band = (vUv.x * 0.8 + (1.0 - vUv.y) * 0.45) - sheenPos;
        // dim is PERCEPTUAL: the shader works in linear light, where ×0.28 still looks 57% bright (found 10-06)
        vec3 rgb0 = c.rgb + sheenAmt * exp(-band * band * 140.0) * c.a;
        vec3 rgb = dimFade > 0.5 ? mix(rgb0, dimTo * c.a, dim * 0.72) : rgb0 * pow(1.0 - dim, 2.2);   // on cream a 0.55 dim still reads
        // glow: emissive gain. Pushes the panel past white in the float buffer, so ONLY it crosses the bloom threshold
        // (neon streaks, glowing outlines) while white UI text stays crisp.
        rgb *= 1.0 + glow;
        gl_FragColor = vec4(rgb, a);
        #include <colorspace_fragment>
      }`,
    transparent: true, depthWrite: false, toneMapped: false, side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(pw, ph), mat);
  const dmat = depthMaterial(tex);
  dmat.uniforms.size.value.set(w, h); dmat.uniforms.radius.value = radius;
  mesh.userData.depthMat = dmat;
  let sh = null;
  if (shadow) {
    const blur = shadow.blur || 40, pad = blur * 2;
    const sm = new THREE.ShaderMaterial({
      uniforms: { size: { value: new THREE.Vector2(w, h) }, radius: { value: radius }, blur: { value: blur },
                  opacity: { value: shadow.opacity ?? 0.16 }, pad: { value: pad }, tint: { value: new THREE.Color(shadow.color || "#1a1712") } },
      vertexShader: MESH_VS,
      fragmentShader: `uniform vec2 size; uniform float radius, blur, opacity, pad; uniform vec3 tint; varying vec2 vUv; ${RBOX}
        void main(){
          vec2 full = size + 2.0 * pad;
          float d = rbox((vUv - 0.5) * full, size * 0.5, radius);
          gl_FragColor = vec4(tint, opacity * (1.0 - smoothstep(-blur * 0.6, blur, d)));
          #include <colorspace_fragment>
        }`,
      transparent: true, depthWrite: false, toneMapped: false,
    });
    sh = new THREE.Mesh(new THREE.PlaneGeometry((w + 2 * pad) * U, (h + 2 * pad) * U), sm);
    sh.position.set(0, -(shadow.y ?? 24) * U, -(shadow.z ?? 0.02));
    group.add(sh);
  }
  group.add(mesh);
  const state = { opacity, sheen: -1, dim: 0, glow: 0 };
  const sync = () => {
    mat.uniforms.opacity.value = state.opacity;
    dmat.uniforms.opacity.value = state.opacity;
    mat.uniforms.sheenPos.value = state.sheen;
    mat.uniforms.dim.value = state.dim;
    mat.uniforms.glow.value = state.glow;
    if (sh) sh.material.uniforms.opacity.value = (shadow.opacity ?? 0.16) * state.opacity;
    group.visible = state.opacity > 0.002;
  };
  stage.scene.add(group);
  return { group, mesh, mat, dmat, tex, shadowMesh: sh, state, sync, w, h };
}

// An HTML element painted into a texture on a plane. The element lives inside <canvas layoutsubtree> (CSS size w × h);
// the canvas bitmap is `scale` × larger so type stays crisp when the camera pushes in. The source canvas must be
// PAINTED to have a paint record: hide it behind the stage with z-index:-1, never opacity:0 (an invisible canvas
// captures 0 pixels — found 2026-10-06).
// live: the HTML changes over time (re-painted + re-captured every frame); otherwise captured once.
export function htmlPanel(stage, { canvas, el, w, h, scale = 2, radius = 0, shadow = null, opacity = 1, live = false, sheen = false }) {
  // the element's box IS the panel: drawElementImage stretches the element's box to the whole canvas, so an element
  // without a width (it shrinks to its text) came out stretched sideways — every headline was 1.3–1.5× too wide (10-06)
  el.style.boxSizing = "border-box"; el.style.width = w + "px"; el.style.height = h + "px";
  const ctx = canvas.getContext("2d");
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = stage.renderer.capabilities.getMaxAnisotropy();
  tex.minFilter = THREE.LinearMipmapLinearFilter;
  tex.generateMipmaps = true;
  const U = 1 / 1000;
  const panel = Object.assign(plane(stage, tex, { w, h, radius, shadow, opacity, sheen }), {
    live, canvas, captured: false,
    waitPaint() {
      return new Promise((resolve) => {
        if (typeof canvas.requestPaint !== "function") return resolve();
        let done = false;
        const fin = () => { if (done) return; done = true; canvas.onpaint = null; resolve(); };
        canvas.onpaint = fin;
        canvas.requestPaint();
        setTimeout(fin, 150);
      });
    },
    capture() {
      if (typeof ctx.drawElementImage !== "function") { if (!panel._warned) { console.warn("[launch] drawElementImage unavailable"); panel._warned = true; } return; }
      try {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawElementImage(el, 0, 0, canvas.width, canvas.height);
        tex.needsUpdate = true;
        panel.captured = true;
      } catch (e) { if (!panel._warned) { console.warn("[launch] capture failed:", e.message); panel._warned = true; } }
    },
    // world position of an element inside this panel (its centre, or {ax, ay} 0..1 within its box) — measured from the
    // layout, so a camera can aim at an exact word instead of a guessed coordinate (missed "ships." by 0.2 units, 10-06)
    locate(sel, ax = 0.5, ay = 0.5) {
      const t = typeof sel === "string" ? el.querySelector(sel) : sel;
      const R = el.getBoundingClientRect(), r = t.getBoundingClientRect();
      const kx = w / R.width, ky = h / R.height;
      const cx = (r.left - R.left + r.width * ax) * kx, cy = (r.top - R.top + r.height * ay) * ky;
      const v = new THREE.Vector3((cx - w / 2) * U, -(cy - h / 2) * U, 0);
      panel.group.updateMatrixWorld(true);
      return panel.group.localToWorld(v);
    },
  });
  stage.panels.push(panel);
  return panel;
}

// A loaded image (thumbnail, screenshot, photo, logo) on a plane — no HTML round trip, native resolution.
export function imagePanel(stage, { img, w, h, radius = 0, shadow = null, opacity = 1, sheen = false }) {
  const tex = new THREE.Texture(img);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = stage.renderer.capabilities.getMaxAnisotropy();
  tex.minFilter = THREE.LinearMipmapLinearFilter;
  tex.generateMipmaps = true;
  tex.needsUpdate = true;
  const panel = Object.assign(plane(stage, tex, { w, h, radius, shadow, opacity, sheen }), {
    live: false, captured: true, waitPaint: () => Promise.resolve(), capture() {},
  });
  stage.panels.push(panel);
  return panel;
}

// A real 3D device (phone / laptop GLB) whose display shows a live HTML panel. The panel is used as a texture only.
// The models (HyperFrames registry, vfx-iphone-device) carry UVs for a tiling material, so the display gets planar
// UVs from its own bounds; the display is turned to face +Z (the camera); maker logos are hidden (not our trademark).
// size: the phone's height / the laptop's width in world units (1 = 1000 px at 1:1).
// A glossy floor that mirrors the scene (three's Reflector): devices and cards reflect on it. Lives at y, faces up.
export async function reflectiveFloor(stage, { y = -0.6, size = 12, color = "#1a1a1e", fade = 0.0 } = {}) {
  const { Reflector } = await import("three/addons/objects/Reflector.js");
  const W = stage.o.width, H = stage.o.height;
  const mirror = new Reflector(new THREE.PlaneGeometry(size, size), { textureWidth: W, textureHeight: H, color: new THREE.Color(color), clipBias: 0.003 });
  mirror.rotation.x = -Math.PI / 2; mirror.position.y = y;
  mirror.userData.depthMat = depthMaterial(null);                // the floor has a true depth: focus treats it right
  stage.scene.add(mirror);
  return mirror;
}

export async function loadDevice(stage, { url, kind = "phone", screen, size = 1.6, hideLogos = true, finish = null }) {
  const { GLTFLoader } = await import("three/addons/loaders/GLTFLoader.js");
  const gltf = await new GLTFLoader().loadAsync(url);
  const m = gltf.scene;
  const box = new THREE.Box3().setFromObject(m), sz = box.getSize(new THREE.Vector3());
  m.scale.setScalar(size / (kind === "phone" ? sz.y : Math.max(sz.x, sz.z)));
  box.setFromObject(m); m.position.sub(box.getCenter(new THREE.Vector3()));
  const isScreen = (n) => (kind === "phone" ? n.indexOf("front-glass") === 0 : n.replace(/\.\d+$/, "") === "display");
  let display = null;
  m.traverse((c) => {
    if (!c.isMesh) return;
    if (hideLogos && /logo/i.test(c.name)) { c.visible = false; return; }
    c.userData.depthMat = depthMaterial(null);
    // finish: recolour the body metal (the phone ships in orange) — e.g. "#2b2b2e" graphite, "#d6d6d8" silver
    if (finish && c.material && /aluminium|space-black|body/i.test(c.material.name || "")) { c.material = c.material.clone(); c.material.color.set(finish); }
    if (isScreen(c.name)) {
      display = c;
      const g = c.geometry; g.computeBoundingBox();
      const bb = g.boundingBox, pos = g.attributes.position, w = bb.max.x - bb.min.x || 1, h = bb.max.y - bb.min.y || 1;
      const uv = new Float32Array(pos.count * 2);
      for (let i = 0; i < pos.count; i++) { uv[i * 2] = (pos.getX(i) - bb.min.x) / w; uv[i * 2 + 1] = (pos.getY(i) - bb.min.y) / h; }
      g.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
      c.material = new THREE.MeshBasicMaterial({ map: screen ? screen.tex : null, color: screen ? 0xffffff : 0x050505, toneMapped: false });
    }
  });
  // face the display toward +Z
  const back = m.getObjectByName(kind === "phone" ? "rear-window" : "deck");
  if (display && back && kind === "phone") {
    m.updateWorldMatrix(true, true);
    const fp = new THREE.Vector3(), bp = new THREE.Vector3();
    display.getWorldPosition(fp); back.getWorldPosition(bp);
    if (fp.z < bp.z) m.rotation.y += Math.PI;
  }
  if (screen) screen.group.removeFromParent();     // the panel lives on the display now, not as its own plane
  const group = new THREE.Group(); group.add(m); stage.scene.add(group);
  return { group, model: m, display, screen };
}

export function loadImage(src) {
  return new Promise((resolve, reject) => {
    const im = new Image();
    im.onload = () => (im.decode ? im.decode().catch(() => {}).then(() => resolve(im)) : resolve(im));
    im.onerror = () => reject(new Error("image failed: " + src));
    im.src = src;
  });
}

// Wire a Stage to HyperFrames: the GSAP timeline is the single source of truth (camera rig, panel states, positions);
// on each seek — and for each motion-blur sub-frame — it is seeked with events suppressed, then `sync(ts)` applies
// derived values (DOM text for live panels, etc.). Await it, THEN register the timeline in the page
// (`window.__timelines[id] = tl`, where lint can see it). Live panels repaint per frame via the seek event's waitUntil.
export async function bindToHyperFrames(stage, tl, sync = () => {}) {
  const apply = (ts) => { tl.seek(ts, true); for (const p of stage.panels) p.sync(); sync(ts); };
  const live = stage.panels.filter((p) => p.live);
  apply(0);
  await Promise.all(stage.panels.map((p) => p.waitPaint()));
  window.addEventListener("hf-seek", (e) => {
    const t = Number(e.detail && e.detail.time) || 0;
    apply(t);
    const now = live.filter((p) => p.group.visible);   // only what is on screen at t needs a fresh paint
    if (now.length && e.detail && typeof e.detail.waitUntil === "function") {
      e.detail.waitUntil(Promise.all(now.map((p) => p.waitPaint())).then(() => stage.render(t, apply)));
    } else stage.render(t, apply);
  });
  stage.render(window.__hfThreeTime || 0, apply);
}
