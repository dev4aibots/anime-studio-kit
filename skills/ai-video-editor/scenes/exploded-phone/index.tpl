<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="assets/vendor/gsap.min.js"></script>
    <script type="importmap">
      { "imports": { "three": "./assets/vendor/three/three.module.js", "three/addons/": "./assets/vendor/three/addons/" } }
    </script>
    <style>
/*FONTS*/
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: #040405; }
      #stage { position: absolute; inset: 0; width: 1920px; height: 1080px; display: block; z-index: 1; }
      canvas[layoutsubtree] { position: absolute; left: 0; top: 0; z-index: -1; pointer-events: none; }
      .rb { font-family: Roboto, sans-serif; }
      .gs { font-family: Geist, sans-serif; }

      /* light at the edges of the frame — the colour lives in the room, never on the UI */
      .edge { width: 1400px; height: 2600px; background: radial-gradient(ellipse 50% 50% at 50% 50%, rgba(255,30,60,0.95) 0%, rgba(255,24,56,0.55) 30%, rgba(255,20,50,0.12) 62%, rgba(255,20,50,0) 80%); }
      .floor { width: 2600px; height: 900px; background: radial-gradient(ellipse 50% 50% at 50% 50%, rgba(255,36,64,0.55) 0%, rgba(255,30,60,0.18) 40%, rgba(255,30,60,0) 72%); }

      /* the search */
      .sb { width: 1180px; height: 150px; display: flex; align-items: center; gap: 30px; padding: 0 52px; background: #121214; border: 2px solid #2c2c30; border-radius: 75px; color: #f1f1f1; }
      .sb svg { width: 54px; height: 54px; flex: none; }
      .sb .q { font-size: 54px; white-space: nowrap; letter-spacing: -0.005em; }
      .sb .car { display: inline-block; width: 3px; height: 60px; background: #f1f1f1; vertical-align: -11px; margin-left: 4px; }
      .sg { width: 1180px; height: 600px; background: #161618; border: 2px solid #26262a; border-radius: 40px; padding: 24px 0; color: #d8d8d8; position: relative; overflow: hidden; }
      .sg .r { height: 110px; display: flex; align-items: center; gap: 32px; padding: 0 52px; font-size: 46px; position: relative; }
      .sg .r svg { width: 42px; height: 42px; flex: none; opacity: 0.6; }
      .sg .r b { color: #fff; font-weight: 500; }
      .sgr { width: 1180px; height: 110px; display: flex; align-items: center; gap: 32px; padding: 0 52px; font-size: 46px; color: #d8d8d8; background: #141416; border-radius: 26px; border: 2px solid #232327; }
      .sgr svg { width: 42px; height: 42px; flex: none; opacity: 0.6; }
      .sgr b { color: #fff; font-weight: 500; }
      .ol svg { display: block; }
      .wmh { font-family: Geist, sans-serif; font-weight: 800; letter-spacing: -0.05em; color: transparent; white-space: nowrap; display: flex; align-items: center; justify-content: center; height: 100%;
             text-shadow: 0 0 30px rgba(255,40,70,1), 0 0 70px rgba(255,30,60,0.85), 0 0 130px rgba(255,30,60,0.55); }
      .sg .hl { position: absolute; left: 0; top: 24px; height: 110px; width: 100%; background: #26262a; transform-origin: 0 50%; }

      /* the phone's screen: 390 × 844 points */
      .scr { width: 390px; height: 844px; position: relative; overflow: hidden; background: #0f0f0f; border-radius: 56px; }
      .scr .pg { position: absolute; inset: 0; }
      .sbar { position: absolute; left: 0; right: 0; top: 0; height: 48px; display: flex; align-items: center; justify-content: space-between; padding: 6px 30px 0 36px; font-family: Roboto, sans-serif; font-weight: 600; font-size: 16px; z-index: 5; }
      .sbar .bt { width: 26px; height: 12px; border: 1.5px solid currentColor; border-radius: 4px; padding: 1.5px; opacity: 0.85; }
      .sbar .bt i { display: block; width: 80%; height: 100%; background: currentColor; border-radius: 2px; }
      .island { position: absolute; left: 50%; top: 11px; width: 120px; height: 35px; margin-left: -60px; background: #000; border-radius: 18px; z-index: 6; }
      .hi { position: absolute; left: 50%; bottom: 8px; width: 132px; height: 5px; margin-left: -66px; border-radius: 3px; z-index: 6; }

      #yt { background: #0f0f0f; color: #f1f1f1; font-family: Roboto, sans-serif; }
      #yt .player { position: absolute; left: 0; top: 48px; width: 390px; height: 219px; }
      #yt .player img { width: 390px; height: 219px; object-fit: cover; display: block; }
      #yt .player .prog { position: absolute; left: 0; bottom: 0; height: 3px; width: 100%; background: rgba(255,255,255,0.25); }
      #yt .player .prog i { display: block; height: 100%; width: 36%; background: #ff0033; }
      #yt .t { position: absolute; left: 14px; right: 14px; top: 280px; font-size: 18px; font-weight: 500; line-height: 1.3; }
      #yt .meta { position: absolute; left: 14px; top: 333px; font-size: 12.5px; color: #aaaaaa; }
      #yt .ch { position: absolute; left: 14px; right: 14px; top: 362px; height: 40px; display: flex; align-items: center; gap: 10px; }
      #yt .ch .av { width: 36px; height: 36px; border-radius: 50%; background-size: cover; background-position: center; }
      #yt .ch .n { font-size: 15px; font-weight: 500; }
      #yt .ch .s { font-size: 12px; color: #aaaaaa; margin-left: 2px; }
      #yt .ch .sub { margin-left: auto; background: #f1f1f1; color: #0f0f0f; font-size: 14px; font-weight: 500; padding: 9px 16px; border-radius: 18px; }
      #yt .acts { position: absolute; left: 14px; top: 418px; display: flex; gap: 8px; }
      #yt .acts span { background: #272727; border-radius: 18px; padding: 9px 14px; font-size: 13.5px; font-weight: 500; display: flex; gap: 7px; align-items: center; }
      #yt .acts svg { width: 17px; height: 17px; }
      #yt .dbox { position: absolute; left: 14px; right: 14px; top: 470px; background: #272727; border-radius: 12px; padding: 12px 14px; font-size: 13px; line-height: 1.4; color: #e6e6e6; }
      #yt .dbox b { color: #f1f1f1; }
      #yt .cbox { position: absolute; left: 14px; right: 14px; top: 568px; background: #272727; border-radius: 12px; padding: 12px 14px; font-size: 14px; font-weight: 500; }
      #yt .cbox span { color: #aaaaaa; font-weight: 400; margin-left: 6px; }
      #yt .next { position: absolute; left: 14px; right: 14px; top: 628px; height: 160px; border-radius: 12px; overflow: hidden; opacity: 0.5; }
      #yt .next img { width: 100%; height: 100%; object-fit: cover; }

      /* the description sheet */
      #ds { position: absolute; left: 0; right: 0; top: 196px; bottom: 0; background: #212121; border-radius: 18px 18px 0 0; color: #f1f1f1; font-family: Roboto, sans-serif; padding: 16px 18px; }
      #ds .hd { display: flex; justify-content: space-between; font-size: 17px; font-weight: 500; padding-bottom: 14px; border-bottom: 1px solid #333; }
      #ds .tt { font-size: 16px; font-weight: 500; line-height: 1.3; margin-top: 16px; }
      #ds .st { display: flex; justify-content: space-around; margin-top: 18px; text-align: center; }
      #ds .st b { display: block; font-size: 18px; font-weight: 500; }
      #ds .st span { font-size: 12px; color: #aaaaaa; }
      #ds .tx { margin-top: 18px; font-size: 14px; line-height: 1.45; color: #e2e2e2; }
      #ds .lk { margin-top: 12px; font-size: 14px; color: #3ea6ff; }

      /* the community page (light) */
      #sk { background: #f8f7f5; color: #202124; font-family: Roboto, sans-serif; }
      #sk .nav { position: absolute; left: 0; right: 0; top: 48px; height: 52px; background: #fff; border-bottom: 1px solid #e4e4e4; display: flex; align-items: center; padding: 0 16px; gap: 10px; font-weight: 500; font-size: 16px; }
      #sk .nav i { width: 28px; height: 28px; border-radius: 6px; background: linear-gradient(135deg, #b9f3d0, #1f2937); display: block; }
      #sk .card { position: absolute; left: 12px; right: 12px; top: 112px; background: #fff; border: 1px solid #e4e4e4; border-radius: 12px; overflow: hidden; }
      #sk .card img { width: 100%; height: 194px; object-fit: cover; display: block; }
      #sk .card .bd { padding: 14px 16px 16px; }
      #sk .card .nm { font-size: 19px; font-weight: 700; }
      #sk .card .url { font-size: 12.5px; color: #909090; font-weight: 700; margin-top: 3px; }
      #sk .card .tx { font-size: 14px; line-height: 1.42; margin-top: 10px; }
      #sk .card .stt { display: grid; grid-template-columns: 1fr 1fr 1fr; border-top: 1px solid #e4e4e4; margin-top: 14px; padding-top: 10px; text-align: center; }
      #sk .card .stt div + div { border-left: 1px solid #e4e4e4; }
      #sk .card .stt b { display: block; font-size: 17px; font-weight: 400; }
      #sk .card .stt span { font-size: 12.5px; color: #909090; }
      #sk .card .jn { margin-top: 14px; height: 44px; border-radius: 8px; background: #f8d481; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700; letter-spacing: 0.04em; position: relative; overflow: hidden; }
      .tap { position: absolute; width: 120px; height: 120px; margin: -60px 0 0 -60px; border-radius: 50%; background: rgba(255,255,255,0.55); transform: scale(0); z-index: 8; }
      .tap.dk { background: rgba(0,0,0,0.18); }

      /* pop-outs (copies of on-screen elements, lifted off the glass) */
      .pl img { width: 390px; height: 219px; object-fit: cover; display: block; border-radius: 10px; }
      .lkp { width: 362px; height: 64px; background: #212121; border-radius: 14px; display: flex; align-items: center; gap: 10px; padding: 0 16px; font-family: Roboto, sans-serif; font-size: 15.5px; color: #3ea6ff; }
      .lkp svg { width: 20px; height: 20px; flex: none; }
      .mem { width: 150px; height: 90px; background: #fff; border-radius: 14px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: Roboto, sans-serif; color: #202124; border: 1px solid #e4e4e4; }
      .mem b { font-size: 34px; font-weight: 500; line-height: 1; }
      .mem span { font-size: 15px; color: #909090; margin-top: 6px; }
      .pk { width: 230px; height: 150px; background: #121215; border: 1px solid #2b2b31; border-radius: 18px; padding: 20px 22px; font-family: Geist, sans-serif; color: #f4f4f5; }
      .pk .ic { width: 34px; height: 26px; }
      .pk .kw { font-weight: 700; font-size: 36px; letter-spacing: -0.01em; margin-top: 12px; white-space: nowrap; }
      .pk .ft { font-size: 14px; color: #8b8b93; margin-top: 4px; font-family: Roboto, sans-serif; }

      /* type */
      .ty { font-family: Geist, sans-serif; font-weight: 800; color: #fafafa; letter-spacing: -0.045em; line-height: 0.95; white-space: nowrap; display: flex; align-items: center; height: 100%; }
      .ty em { font-style: normal; color: #ff2a48; }
      .wm { font-family: Geist, sans-serif; font-weight: 800; letter-spacing: -0.05em; color: #fff; white-space: nowrap; display: flex; align-items: center; justify-content: center; height: 100%; }
      .wsub { font-family: Roboto, sans-serif; font-weight: 500; color: #b9b9c0; display: flex; align-items: center; justify-content: center; height: 100%; letter-spacing: 0.01em; }
      .wsub i { font-style: normal; color: #fff; }
    
      .lb { font-family: Geist, sans-serif; font-weight: 800; font-size: 100px; letter-spacing: -0.045em; color: #fafafa; white-space: nowrap; display: flex; align-items: center; gap: 30px; line-height: 1; }
      .lb i { width: 18px; height: 18px; border-radius: 50%; background: #ff2440; box-shadow: 0 0 0 8px rgba(255,36,64,0.2); flex: none; }
      .lb em, .ls em { font-style: normal; color: #ff2a48; }
      .ls { font-family: Roboto, sans-serif; font-weight: 500; font-size: 40px; color: #b9b9c0; white-space: nowrap; display: flex; align-items: center; padding-left: 48px; }
      #yt.empty > * { visibility: hidden; }
</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="19.33" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>
      <canvas id="c-scr" layoutsubtree width="1170" height="2532" style="width:390px;height:844px">
        <div id="scr" class="scr">
          <div class="pg" id="yt">
            <div class="player"><img id="ytPlayer" src="assets/brand/player.jpg" alt="" /><div class="prog"><i></i></div></div>
            <div class="t">Your video title, as it is on the page</div>
            <div class="meta">views · date · ...more</div>
            <div class="ch"><div class="av" style="background-image:url(assets/brand/avatar.jpg)"></div><span class="n">Your Channel</span><span class="s"></span><span class="sub">Subscribe</span></div>
            <div class="acts">
              <span><svg viewBox="0 0 24 24" fill="#f1f1f1"><path d="M2 21h4V9H2v12Zm20-11a2 2 0 0 0-2-2h-6.3l1-4.6v-.3a1.5 1.5 0 0 0-.4-1L13.2 1 6.6 7.6A2 2 0 0 0 6 9v10a2 2 0 0 0 2 2h9a2 2 0 0 0 1.8-1.2l3-7.1c.1-.2.2-.5.2-.7v-2Z"/></svg><b id="likes">—</b></span>
              <span><svg viewBox="0 0 24 24" fill="#f1f1f1"><path d="M14 9V5l7 7-7 7v-4.1c-5 0-8.5 1.6-11 5.1 1-5 4-10 11-11Z"/></svg>Share</span>
              <span><svg viewBox="0 0 24 24" fill="#f1f1f1"><path d="M17 3H7a2 2 0 0 0-2 2v16l7-3 7 3V5a2 2 0 0 0-2-2Z"/></svg>Save</span>
            </div>
            <div class="dbox"><b>views · date</b><br/>The first line of your description… <b>more</b></div>
            <div class="cbox">Comments<span>2</span></div>
            <div class="next"><img src="assets/brand/player.jpg" alt="" style="filter:brightness(0.6)" /></div>
            <div class="pg" id="ds" style="inset:auto;left:0;right:0;top:196px;bottom:0">
              <div class="hd"><span>Description</span><span>✕</span></div>
              <div class="tt">Your video title, as it is on the page</div>
              <div class="st"><div><b>—</b><span>Likes</span></div><div><b>—</b><span>Views</span></div><div><b>Date</b><span>Year</span></div></div>
              <div class="tx">The first lines of your real description go here.</div>
              <div class="tx">The link you send people to:</div>
              <div class="lk" id="lk">https://example.com/your-link</div>
            </div>
          </div>
          <div class="pg" id="sk">
            <div class="nav"><i></i>Your Community</div>
            <div class="card"><img src="assets/brand/community_cover.jpg" alt="" />
              <div class="bd"><div class="nm">Your Community</div><div class="url">example.com/your-link</div>
                <div class="tx">Your community's own description, from its page.</div>
                <div class="stt"><div id="memCell"><b>—</b><span>Members</span></div><div><b>—</b><span>Online</span></div><div><b>—</b><span>Admin</span></div></div>
                <div class="jn" id="jn">JOIN GROUP</div>
              </div>
            </div>
          </div>
          <div class="sbar" id="sbar"><span>9:41</span><span class="bt"><i></i></span></div>
          <i class="tap" id="tap"></i>
          <div class="island"></div><i class="hi" id="hi"></i>
        </div>
      </canvas>
      <canvas id="c-L1" layoutsubtree width="1170" height="657" style="width:390px;height:219px"><div id="L1"><div style="width:390px;height:219px;position:relative;background:#000"><img src="assets/brand/player.jpg" style="width:390px;height:219px;object-fit:cover;display:block"/><div style="position:absolute;left:0;right:0;bottom:0;height:3px;background:rgba(255,255,255,.25)"><i style="display:block;height:100%;width:36%;background:#ff0033"></i></div></div></div></canvas>
      <canvas id="c-L2" layoutsubtree width="1086" height="228" style="width:362px;height:76px"><div id="L2"><div style="width:362px;height:76px;background:#0f0f0f;font-family:Roboto,sans-serif;color:#f1f1f1;padding-top:4px"><div style="font-size:18px;font-weight:500;line-height:1.3">Your video title, as it is on the page</div><div style="font-size:12.5px;color:#aaa;margin-top:6px">views · date · ...more</div></div></div></canvas>
      <canvas id="c-L3" layoutsubtree width="1086" height="132" style="width:362px;height:44px"><div id="L3"><div style="width:362px;height:44px;background:#0f0f0f;display:flex;align-items:center;gap:10px;font-family:Roboto,sans-serif;color:#f1f1f1"><div style="width:36px;height:36px;border-radius:50%;background:url(assets/brand/avatar.jpg) center/cover"></div><span style="font-size:15px;font-weight:500">Your Channel</span><span style="font-size:12px;color:#aaa"></span><span style="margin-left:auto;background:#f1f1f1;color:#0f0f0f;font-size:14px;font-weight:500;padding:9px 16px;border-radius:18px">Subscribe</span></div></div></canvas>
      <canvas id="c-L4" layoutsubtree width="1086" height="120" style="width:362px;height:40px"><div id="L4"><div style="width:362px;height:40px;background:#0f0f0f;display:flex;gap:8px;font-family:Roboto,sans-serif;color:#f1f1f1;font-size:13.5px;font-weight:500"><span style="background:#272727;border-radius:18px;padding:10px 16px">👍</span><span style="background:#272727;border-radius:18px;padding:10px 16px">Share</span><span style="background:#272727;border-radius:18px;padding:10px 16px">Save</span></div></div></canvas>
      <canvas id="c-L5" layoutsubtree width="1086" height="264" style="width:362px;height:88px"><div id="L5"><div style="width:362px;height:88px;background:#272727;border-radius:12px;padding:12px 14px;font-family:Roboto,sans-serif;font-size:13px;line-height:1.4;color:#e6e6e6"><b style="color:#f1f1f1">views · date</b><br/>The first line of your description… <b>more</b></div></div></canvas>
      <canvas id="c-L6" layoutsubtree width="1086" height="138" style="width:362px;height:46px"><div id="L6"><div style="width:362px;height:46px;background:#272727;border-radius:12px;padding:13px 14px;font-family:Roboto,sans-serif;font-size:14px;font-weight:500;color:#f1f1f1">Comments<span style="color:#aaa;font-weight:400;margin-left:6px">2</span></div></div></canvas>
      <canvas id="c-L7" layoutsubtree width="1086" height="480" style="width:362px;height:160px"><div id="L7"><div style="width:362px;height:160px;border-radius:12px;overflow:hidden"><img src="assets/brand/player.jpg" style="width:100%;height:100%;object-fit:cover;filter:brightness(.6)"/></div></div></canvas>
      <canvas id="c-oL1" layoutsubtree width="1212" height="699" style="width:404px;height:233px"><div id="oL1"><svg width="404" height="233" viewBox="0 0 404 233"><rect id="oL1r" x="3" y="3" width="398" height="227" rx="12" fill="none" stroke="#ff2440" stroke-width="2.6"/></svg></div></canvas>
      <canvas id="c-oL2" layoutsubtree width="1128" height="270" style="width:376px;height:90px"><div id="oL2"><svg width="376" height="90" viewBox="0 0 376 90"><rect id="oL2r" x="3" y="3" width="370" height="84" rx="12" fill="none" stroke="#ff2440" stroke-width="2.6"/></svg></div></canvas>
      <canvas id="c-oL3" layoutsubtree width="1128" height="174" style="width:376px;height:58px"><div id="oL3"><svg width="376" height="58" viewBox="0 0 376 58"><rect id="oL3r" x="3" y="3" width="370" height="52" rx="12" fill="none" stroke="#ff2440" stroke-width="2.6"/></svg></div></canvas>
      <canvas id="c-oL4" layoutsubtree width="1128" height="162" style="width:376px;height:54px"><div id="oL4"><svg width="376" height="54" viewBox="0 0 376 54"><rect id="oL4r" x="3" y="3" width="370" height="48" rx="12" fill="none" stroke="#ff2440" stroke-width="2.6"/></svg></div></canvas>
      <canvas id="c-oL5" layoutsubtree width="1128" height="306" style="width:376px;height:102px"><div id="oL5"><svg width="376" height="102" viewBox="0 0 376 102"><rect id="oL5r" x="3" y="3" width="370" height="96" rx="12" fill="none" stroke="#ff2440" stroke-width="2.6"/></svg></div></canvas>
      <canvas id="c-oL6" layoutsubtree width="1128" height="180" style="width:376px;height:60px"><div id="oL6"><svg width="376" height="60" viewBox="0 0 376 60"><rect id="oL6r" x="3" y="3" width="370" height="54" rx="12" fill="none" stroke="#ff2440" stroke-width="2.6"/></svg></div></canvas>
      <canvas id="c-oL7" layoutsubtree width="1128" height="522" style="width:376px;height:174px"><div id="oL7"><svg width="376" height="174" viewBox="0 0 376 174"><rect id="oL7r" x="3" y="3" width="370" height="168" rx="12" fill="none" stroke="#ff2440" stroke-width="2.6"/></svg></div></canvas>
      <canvas id="c-grid" layoutsubtree width="1500" height="1500" style="width:3000px;height:3000px"><svg id="grid" width="3000" height="3000" viewBox="0 0 3000 3000"><defs><pattern id="gp" width="100" height="100" patternUnits="userSpaceOnUse"><path d="M100 0H0V100" fill="none" stroke="#ff1e3c" stroke-width="2.2"/></pattern><radialGradient id="gf"><stop offset="0" stop-color="#fff"/><stop offset="0.7" stop-color="#fff" stop-opacity="0.35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient><mask id="gm"><rect width="3000" height="3000" fill="url(#gf)"/></mask></defs><rect width="3000" height="3000" fill="url(#gp)" mask="url(#gm)"/></svg></canvas>
      <canvas id="c-lb1" layoutsubtree width="1800" height="300" style="width:900px;height:150px"><div id="lb1" class="lb"><i></i><span>three.js</span></div></canvas>
      <canvas id="c-ls1" layoutsubtree width="1800" height="140" style="width:900px;height:70px"><div id="ls1" class="ls">which is JavaScript<em>.</em></div></canvas>
      <canvas id="c-lb2" layoutsubtree width="1800" height="300" style="width:900px;height:150px"><div id="lb2" class="lb"><i></i><span>real web pages</span></div></canvas>
      <canvas id="c-ls2" layoutsubtree width="1800" height="140" style="width:900px;height:70px"><div id="ls2" class="ls">printed on top of the 3D surface<em>.</em></div></canvas>
      <canvas id="c-ls3" layoutsubtree width="1800" height="140" style="width:900px;height:70px"><div id="ls3" class="ls">the phone itself</div></canvas>
      <canvas id="c-lb3" layoutsubtree width="1800" height="300" style="width:900px;height:150px"><div id="lb3" class="lb"><i></i><span>a 3D model<em>.</em></span></div></canvas>
    </div>
    <script type="module">
      import { Stage, ground, loadDevice, reflectiveFloor, THREE } from "./assets/vendor/launch.js";
      import { director, noir } from "./assets/vendor/kit.js";
      import { LineSegments2 } from "three/addons/lines/LineSegments2.js";
      import { LineSegmentsGeometry } from "three/addons/lines/LineSegmentsGeometry.js";
      import { LineMaterial } from "three/addons/lines/LineMaterial.js";
      await document.fonts.ready;
      await Promise.all([...document.images].map((im) => (im.complete ? 0 : new Promise((r) => (im.onload = im.onerror = r)))));
      const spring = (t, k, d) => { if (t <= 0) return 0; const w0 = Math.sqrt(k), z = d / (2 * w0);
        if (z < 1) { const wd = w0 * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t)); }
        return 1 - Math.exp(-w0 * t) * (1 + w0 * t); };
      const SPR = { ui: [300, 24], card: [190, 25], heavy: [130, 23], snap: [420, 32] };
      const sp = (kind, dur) => { const [k, d] = SPR[kind]; const end = spring(dur, k, d); return (p) => spring(p * dur, k, d) / end; };
      const S = (tg, v, t, kind = "card", dur = 0.8) => tl.to(tg, { ...v, duration: dur, ease: sp(kind, dur) }, t);
      const SF = (tg, f, v, t, kind = "card", dur = 0.8) => tl.fromTo(tg, f, { ...v, duration: dur, ease: sp(kind, dur), immediateRender: false }, t);

      const stage = new Stage({ canvas: document.getElementById("stage"), width: 1920, height: 1080, background: "#040405", samples: 8,
                                dof: { strength: 30, max: 40 }, grain: 0.03, vignette: 0.38, bloom: { strength: 1.1, threshold: 1.0 } });
      ground(stage, { colorA: "#050506", colorB: "#050506", dots: 0, size: 60, z: -4 });
      await stage.studio({ env: 0.8, key: 2.0, fill: 0.55, rim: 2.6, warm: "#ffe6e8", cool: "#ffc9d1" });
      stage.renderer.localClippingEnabled = true;
      const FLOOR_Y = -0.545;
      await reflectiveFloor(stage, { y: FLOOR_Y, size: 14, color: "#2a2a30" });
      const tl = gsap.timeline({ paused: true });
      const d = director(stage, tl), { cam } = d;
      const U = stage.presentMat.uniforms; const look = noir(stage, tl);   // NEON NOIR edge light: subtle, one place (kit.js)
      const pulse = (t, k = 0.5) => look.pulse(t, k);

      // the scene grid on the floor: "a real 3D scene"
      const grid = d.panel("grid", 3000, 3000, { scale: 0.5 }); grid.group.rotation.x = -Math.PI / 2; grid.group.position.set(0, FLOOR_Y + 0.003, -0.4);
      grid.state.glow = 0.9; grid.state.opacity = 0;
      tl.to(grid.state, { opacity: 0.85, duration: 0.7, ease: "power2.out" }, 0.45);

      // ── the phone: a real 3D model with the real page on its screen ─────────────────────────────────────────────────
      const scr = d.panel("scr", 390, 844, { live: true, scale: 3 });
      const phone = await loadDevice(stage, { url: "assets/vendor/models/iphone.glb", kind: "phone", screen: scr, size: 1.02, finish: "#26262a" });
      phone.group.updateMatrixWorld(true);
      // its neon edges (feature edges at 8°, fat lines): the model as Three.js sees it. A scan line turns edges into metal.
      const scan = { y: -0.7 };
      const solidClip = new THREE.Plane(new THREE.Vector3(0, -1, 0), scan.y);   // the solid keeps y < scan
      const wireClip = new THREE.Plane(new THREE.Vector3(0, 1, 0), -scan.y);    // the edges keep y > scan
      const wireMat = new LineMaterial({ linewidth: 2.2, worldUnits: false, transparent: true, depthWrite: false });
      wireMat.color.setRGB(1.75, 0.05, 0.12); wireMat.resolution.set(1920, 1080); wireMat.clippingPlanes = [wireClip]; wireMat.opacity = 0;
      const meshes = []; phone.model.traverse((c) => { if (c.isMesh && c.visible) meshes.push(c); });
      const seen = new Set();
      meshes.forEach((c) => {
        const ls = new LineSegments2(new LineSegmentsGeometry().fromEdgesGeometry(new THREE.EdgesGeometry(c.geometry, 8)), wireMat);
        c.add(ls);
        for (const m of [].concat(c.material)) if (!seen.has(m)) { seen.add(m); m.clippingPlanes = [solidClip]; }
      });
      const scanLine = new THREE.Mesh(new THREE.PlaneGeometry(0.66, 0.0045),
        new THREE.MeshBasicMaterial({ color: new THREE.Color(4.0, 0.3, 0.45), toneMapped: false, transparent: true, opacity: 0, depthWrite: false }));
      scanLine.position.set(0, scan.y, 0.075); phone.group.add(scanLine);
      const dispMat = phone.display.material; dispMat.color.setRGB(0, 0, 0);       // the screen is off until it powers on

      // the page's real parts, as separate layers placed exactly over the glass
      const disp = phone.display, pos = disp.geometry.attributes.position, uv = disp.geometry.attributes.uv;
      let iTL = 0, iTR = 0, iBL = 0;
      for (let i = 0; i < uv.count; i++) { const u = uv.getX(i), v = uv.getY(i);
        if (u - v < uv.getX(iTL) - uv.getY(iTL)) iTL = i; if (u + v > uv.getX(iTR) + uv.getY(iTR)) iTR = i; if (-u - v > -uv.getX(iBL) - uv.getY(iBL)) iBL = i; }
      const wp = (i) => phone.group.worldToLocal(disp.localToWorld(new THREE.Vector3(pos.getX(i), pos.getY(i), pos.getZ(i))));
      const TL = wp(iTL), TR = wp(iTR), BL = wp(iBL), ux = TR.clone().sub(TL), vy = BL.clone().sub(TL);
      const GLASS_Z = Math.max(TL.z, TR.z, BL.z) + 0.003, PX = ux.length() / 390;
      const holder = new THREE.Group(); stage.scene.add(holder);
      const LAY = { L1: [0, 48, 390, 219], L2: [14, 274, 362, 76], L3: [14, 360, 362, 44], L4: [14, 416, 362, 40], L5: [14, 470, 362, 88], L6: [14, 568, 362, 46], L7: [14, 628, 362, 160] };
      const DEPTH = { L1: 0.46, L2: 0.37, L3: 0.3, L4: 0.24, L5: 0.18, L6: 0.12, L7: 0.07 };
      const layers = Object.entries(LAY).map(([k, [x, y, w, h]], i) => {
        const p = d.panel(k, w, h, { radius: k === "L1" ? 0 : 12, scale: 3, shadow: { blur: 30, y: 18, opacity: 0.55, color: "#000" } });
        const o = d.panel("o" + k, w + 14, h + 14, { live: true });
        holder.add(p.group); p.group.add(o.group); o.group.position.set(0, 0, 0.004); o.state.glow = 2.2; o.state.opacity = 0;
        const c = TL.clone().add(ux.clone().multiplyScalar((x + w / 2) / 390)).add(vy.clone().multiplyScalar((y + h / 2) / 844));
        p.group.position.set(c.x, c.y, GLASS_Z); p.group.scale.setScalar(PX / 0.001); p.state.opacity = 0;
        return { k, p, o, c, depth: DEPTH[k], side: i % 2 ? 1 : -1, dash: { v: 1 } };
      });
      const ex = { v: 0 };

      // ── the words, on the left (the phone lives right of centre) ───────────────────────────────────────────────────
      const LX = -960 + 120 + 450;                                                              // a 120 px margin
      const lb1 = d.hud("lb1", 900, 150, LX, -40), ls1 = d.hud("ls1", 900, 70, LX, 50);
      const lb2 = d.hud("lb2", 900, 150, LX, -40), ls2 = d.hud("ls2", 900, 70, LX, 50);
      const ls3 = d.hud("ls3", 900, 70, LX, -95), lb3 = d.hud("lb3", 900, 150, LX, -10);
      const k = 0.5 / d.D;
      const tIn = (p, t, kind = "heavy") => { const x0 = p.group.position.x; tl.set(p.state, { opacity: 1 }, t);
        SF(p.group.position, { x: x0 - 0.028 * k }, { x: x0 }, t, kind, 0.7); };
      const tOut = (ps, t) => { for (const p of ps) tl.to(p.state, { opacity: 0, duration: 0.22, ease: "power1.in" }, t); };

      // ═══ 0 – 2.4 · "a real 3D scene, built on three.js" — the model as edges, then a scan turns it into metal ═══════
      phone.group.rotation.set(0.04, 0.5, 0.0); holder.rotation.copy(phone.group.rotation);
      Object.assign(cam, { x: 0.3, y: 0.18, z: 2.4, tx: -0.24, ty: 0.0, tz: 0, roll: -0.015, focus: -1, aperture: 0 });
      tl.to(cam, { x: -0.12, y: 0.1, z: 2.1, roll: 0, duration: 4.6, ease: "power1.inOut" }, 0);
      tl.to([phone.group.rotation, holder.rotation], { y: 0.14, duration: 5.6, ease: "power1.inOut" }, 0);
      tl.to(wireMat, { opacity: 1, duration: 0.35, ease: "power2.out" }, 0.04);
      tl.set(scanLine.material, { opacity: 1 }, 1.0);
      tl.fromTo(scan, { y: -0.62 }, { y: 0.62, duration: 1.3, ease: "power2.inOut", immediateRender: false }, 1.0);
      tl.set(scanLine.material, { opacity: 0 }, 2.31);
      tl.to(cam, { aperture: 0.55, duration: 0.5, ease: "power1.inOut" }, 2.35);
      tIn(lb1, 2.15); pulse(2.15, 0.55);
      // the screen powers on (the real YouTube page, live HTML)
      tl.to(dispMat.color, { r: 1.7, g: 1.7, b: 1.7, duration: 0.07, ease: "power2.in" }, 2.82);
      tl.to(dispMat.color, { r: 1, g: 1, b: 1, duration: 0.45, ease: "power2.out" }, 2.9);
      pulse(2.86, 0.45);
      tIn(ls1, 3.25, "card");
      tOut([lb1, ls1], 4.6);

      // ═══ 5.95 · "the app screens are real web pages" — the page lifts off the glass in its layers ══════════════════
      const EX = 5.95;
      tl.to(cam, { x: -0.95, y: 0.28, z: 1.85, tx: -0.14, ty: 0.02, tz: 0.18, focus: 1.86, duration: 1.5, ease: "power3.inOut" }, 4.75);
      tl.set(ex, { v: 1 }, EX);
      layers.forEach((L, i) => {
        const t = EX + i * 0.055;
        tl.set(L.p.state, { opacity: 1 }, EX); tl.set(L.o.state, { opacity: 1 }, t);
        SF(L.p.group.position, { z: GLASS_Z, x: L.c.x }, { z: GLASS_Z + L.depth, x: L.c.x + L.side * 0.035 }, t, "ui", 1.0);
        SF(L.dash, { v: 1 }, { v: 0 }, t + 0.15, "card", 0.7);
      });
      S(phone.group.position, { z: -0.1 }, EX, "card", 0.9);
      pulse(EX, 0.65);
      tIn(lb2, 6.8); pulse(6.8, 0.45);
      tIn(ls2, 7.9, "card");
      tl.to(cam, { x: -1.0, y: 0.24, z: 1.8, duration: 3.6, ease: "none" }, 7.6);
      tOut([lb2, ls2], 11.15);

      // ═══ 11.47 · "so the camera can fly around them" — an orbit to the other side of the stack ════════════════════
      tl.to(cam, { x: 1.05, y: 0.2, z: 1.65, tx: 0.06, tz: 0.2, focus: 1.7, duration: 2.6, ease: "power2.inOut" }, 11.35);
      tl.to(cam, { x: 0.62, y: 0.36, z: 1.95, tz: 0.12, focus: 1.98, duration: 1.7, ease: "power2.inOut" }, 13.95);
      pulse(14.07, 0.55);

      // ═══ 16.05 · "and the phone itself is actually a 3D model" — collapse, spin, back to its edges ════════════════
      const CO = 16.05;
      [...layers].reverse().forEach((L, i) => {
        const t = CO + i * 0.03;
        S(L.p.group.position, { z: GLASS_Z, x: L.c.x }, t, "snap", 0.45);
        tl.set(L.o.state, { opacity: 0 }, t + 0.3);
      });
      S(phone.group.position, { z: 0 }, CO, "snap", 0.45);
      tl.set(ex, { v: 0 }, CO + 0.62); layers.forEach((L) => tl.set(L.p.state, { opacity: 0 }, CO + 0.62));
      tl.to(cam, { x: -0.1, y: 0.1, z: 2.15, tx: -0.24, ty: 0.0, tz: 0, focus: -1, duration: 1.0, ease: "power3.inOut" }, CO);
      tIn(ls3, 16.12, "card");
      tl.to([phone.group.rotation, holder.rotation], { y: 0.14 + Math.PI * 2, duration: 1.1, ease: "power3.inOut" }, 17.1);
      tIn(lb3, 17.62); pulse(17.62, 0.6);
      tl.to(cam, { aperture: 0, duration: 0.3 }, 17.5);
      tl.set(scanLine.material, { opacity: 1 }, 17.66);
      tl.fromTo(scan, { y: 0.62 }, { y: -0.62, duration: 0.75, ease: "power2.inOut", immediateRender: false }, 17.66);
      tl.set(scanLine.material, { opacity: 0 }, 18.42);
      tl.to(cam, { z: 2.0, duration: 1.7, ease: "none" }, 17.62);
      tl.to({}, { duration: 0.001 }, 19.33);

      const yt = document.getElementById("yt"), sk = document.getElementById("sk"), ds = document.getElementById("ds");
      sk.style.opacity = "0"; ds.style.transform = "translateY(720px)";
      d.onSync(() => {
        yt.classList.toggle("empty", !!ex.v);
        for (const L of layers) { const r = document.getElementById("o" + L.k + "r"); if (!L.len) { L.len = r.getTotalLength(); r.style.strokeDasharray = L.len; } r.style.strokeDashoffset = L.len * L.dash.v; }
        holder.position.copy(phone.group.position).setZ(0);
        solidClip.constant = scan.y; wireClip.constant = -scan.y; scanLine.position.y = scan.y;
      });
      await d.bind();
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
