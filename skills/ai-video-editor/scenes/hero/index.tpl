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
             text-shadow: 0 0 26px rgba(255,40,70,0.85), 0 0 64px rgba(255,30,60,0.55), 0 0 120px rgba(255,30,60,0.3); }
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
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="15.7" data-width="1920" data-height="1080">
      <canvas id="stage" width="1920" height="1080"></canvas>

      <canvas id="c-floor" layoutsubtree width="1300" height="450" style="width:2600px;height:900px"><div id="floor" class="floor"></div></canvas>

      <canvas id="c-sb" layoutsubtree width="2360" height="300" style="width:1180px;height:150px"><div id="sb" class="sb rb"><svg viewBox="0 0 24 24" fill="#f1f1f1"><path d="M15.5 14h-.8l-.3-.3A6.5 6.5 0 1 0 14 15.5l.3.3v.8l5 5 1.5-1.5-5-5Zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14Z"/></svg><span class="q"><span id="qt"></span><span class="car" id="car"></span></span></div></canvas>
      <canvas id="c-sg0" layoutsubtree width="2360" height="220" style="width:1180px;height:110px"><div id="sg0" class="sgr rb"><svg viewBox="0 0 24 24" fill="#fff"><path d="M15.5 14h-.8l-.3-.3A6.5 6.5 0 1 0 14 15.5l.3.3v.8l5 5 1.5-1.5-5-5Zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14Z"/></svg><span>claude code <b>motion graphics</b></span></div></canvas>
      <canvas id="c-sg1" layoutsubtree width="2360" height="220" style="width:1180px;height:110px"><div id="sg1" class="sgr rb"><svg viewBox="0 0 24 24" fill="#fff"><path d="M15.5 14h-.8l-.3-.3A6.5 6.5 0 1 0 14 15.5l.3.3v.8l5 5 1.5-1.5-5-5Zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14Z"/></svg><span>claude code <b>motion design</b></span></div></canvas>
      <canvas id="c-sg2" layoutsubtree width="2360" height="220" style="width:1180px;height:110px"><div id="sg2" class="sgr rb"><svg viewBox="0 0 24 24" fill="#fff"><path d="M15.5 14h-.8l-.3-.3A6.5 6.5 0 1 0 14 15.5l.3.3v.8l5 5 1.5-1.5-5-5Zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14Z"/></svg><span>claude code <b>skills tutorial</b></span></div></canvas>
      <canvas id="c-sg3" layoutsubtree width="2360" height="220" style="width:1180px;height:110px"><div id="sg3" class="sgr rb"><svg viewBox="0 0 24 24" fill="#fff"><path d="M15.5 14h-.8l-.3-.3A6.5 6.5 0 1 0 14 15.5l.3.3v.8l5 5 1.5-1.5-5-5Zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14Z"/></svg><span>claude code <b>skills explained</b></span></div></canvas>
      <canvas id="c-sg4" layoutsubtree width="2360" height="220" style="width:1180px;height:110px"><div id="sg4" class="sgr rb"><svg viewBox="0 0 24 24" fill="#fff"><path d="M15.5 14h-.8l-.3-.3A6.5 6.5 0 1 0 14 15.5l.3.3v.8l5 5 1.5-1.5-5-5Zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14Z"/></svg><span>claude code <b>skills guide</b></span></div></canvas>
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

      <canvas id="c-pPl" layoutsubtree width="1170" height="657" style="width:390px;height:219px"><div id="pPl" class="pl"><img src="assets/brand/player.jpg" alt="" /></div></canvas>
      <canvas id="c-pLk" layoutsubtree width="1086" height="192" style="width:362px;height:64px"><div id="pLk" class="lkp"><svg viewBox="0 0 24 24" fill="#3ea6ff"><path d="M10.6 13.4a1 1 0 0 0 1.4 1.4l3.5-3.5a3 3 0 0 0-4.2-4.2L9.1 9.3a1 1 0 0 0 1.4 1.4l2.2-2.2a1 1 0 0 1 1.4 1.4l-3.5 3.5Zm2.8-2.8a1 1 0 0 0-1.4-1.4l-3.5 3.5a3 3 0 0 0 4.2 4.2l2.2-2.2a1 1 0 0 0-1.4-1.4l-2.2 2.2a1 1 0 0 1-1.4-1.4l3.5-3.5Z"/></svg>https://example.com/your-link</div></canvas>
      <canvas id="c-pMem" layoutsubtree width="450" height="270" style="width:150px;height:90px"><div id="pMem" class="mem"><b>—</b><span>Members</span></div></canvas>

      <canvas id="c-olPl" layoutsubtree width="1218" height="705" style="width:406px;height:235px"><div id="olPl" class="ol"><svg width="406" height="235" viewBox="0 0 406 235"><rect id="olPlr" x="3" y="3" width="400" height="229" rx="15" fill="none" stroke="#ff2440" stroke-width="3.2"/></svg></div></canvas>
      <canvas id="c-olLk" layoutsubtree width="1134" height="240" style="width:378px;height:80px"><div id="olLk" class="ol"><svg width="378" height="80" viewBox="0 0 378 80"><rect id="olLkr" x="3" y="3" width="372" height="74" rx="19" fill="none" stroke="#ff2440" stroke-width="3.2"/></svg></div></canvas>
      <canvas id="c-olMem" layoutsubtree width="498" height="318" style="width:166px;height:106px"><div id="olMem" class="ol"><svg width="166" height="106" viewBox="0 0 166 106"><rect id="olMemr" x="3" y="3" width="160" height="100" rx="19" fill="none" stroke="#ff2440" stroke-width="3.2"/></svg></div></canvas>
      <canvas id="c-nt1" layoutsubtree width="2600" height="1500" style="width:2600px;height:1500px"><svg id="nt1" width="2600" height="1500" viewBox="0 0 2600 1500"><path id="nt1p" d="M -60 1180 C 520 1240, 760 260, 1290 380 S 2140 1180, 2680 300" fill="none" stroke="#ff1e3c" stroke-width="9" stroke-linecap="round"/></svg></canvas>
      <canvas id="c-nt2" layoutsubtree width="2600" height="1500" style="width:2600px;height:1500px"><svg id="nt2" width="2600" height="1500" viewBox="0 0 2600 1500"><path id="nt2p" d="M 2680 1260 C 2040 1300, 1840 520, 1300 620 S 420 200, -80 520" fill="none" stroke="#ff1e3c" stroke-width="7" stroke-linecap="round"/></svg></canvas>
      <canvas id="c-wmh" layoutsubtree width="1800" height="400" style="width:1800px;height:400px"><div id="wmh" class="wmh" style="font-size:200px">Your Community</div></canvas>
      <canvas id="c-tyA" layoutsubtree width="2400" height="420" style="width:1200px;height:210px"><div id="tyA" class="ty" style="font-size:150px">Your line here<em>.</em></div></canvas>
      <canvas id="c-wm" layoutsubtree width="3200" height="520" style="width:1600px;height:260px"><div id="wm" class="wm" style="font-size:200px">Your Community</div></canvas>
      <canvas id="c-wsub" layoutsubtree width="3200" height="160" style="width:1600px;height:80px"><div id="wsub" class="wsub" style="font-size:44px">Your call to action&nbsp;·&nbsp;<i>example.com/your-link</i></div></canvas>
    </div>

    <script type="module">
      import { Stage, ground, loadDevice, reflectiveFloor, THREE } from "./assets/vendor/launch.js";
      import { beatGrid, director, makePanelDom, noir } from "./assets/vendor/kit.js";

      const PACKS = Array.from({ length: 25 }, (_, i) => `PACK ${String(i + 1).padStart(2, "0")}`);   // your own items: the names of what you give away
      const FOLDER = `<svg class="ic" viewBox="0 0 34 26"><path d="M2 4a3 3 0 0 1 3-3h7l3 3.5h14a3 3 0 0 1 3 3V22a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3Z" fill="#ff2a48"/></svg>`;
      const root = document.getElementById("root");
      const packDom = PACKS.map((k) => makePanelDom(root, `${FOLDER}<div class="kw">${k}</div><div class="ft">Free resource</div>`, 230, 150, { className: "pk", scale: 2.5 }));
      await document.fonts.ready;
      await Promise.all([...document.images].map((im) => (im.complete ? 0 : new Promise((r) => (im.onload = im.onerror = r)))));
      for (const { el } of packDom) { const kw = el.querySelector(".kw"); let fs = 36; while (kw.getBoundingClientRect().width > 190 && fs > 20) { fs -= 2; kw.style.fontSize = fs + "px"; } }

      // closed-form springs: a pure function of time. Tiny overshoot on UI, none on type.
      const spring = (t, k, d) => { if (t <= 0) return 0; const w0 = Math.sqrt(k), z = d / (2 * w0);
        if (z < 1) { const wd = w0 * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t)); }
        return 1 - Math.exp(-w0 * t) * (1 + w0 * t); };
      const SPR = { ui: [300, 24], card: [190, 25], heavy: [130, 23], snap: [420, 32] };
      const sp = (kind, dur) => { const [k, d] = SPR[kind]; const end = spring(dur, k, d); return (p) => spring(p * dur, k, d) / end; };
      const S = (target, vars, t, kind = "card", dur = 0.8) => tl.to(target, { ...vars, duration: dur, ease: sp(kind, dur) }, t);
      const SF = (target, from, to, t, kind = "card", dur = 0.8) => tl.fromTo(target, from, { ...to, duration: dur, ease: sp(kind, dur), immediateRender: false }, t);

      // "Thunder" (Arulo, Mixkit) from 17.375 s, 95.1 BPM: melody only, the low end goes silent at promo 1.63 s,
      // and the bass slams in (+60 dB) on bar 1 = 2.523 s
      const g = beatGrid(0.6307), { B, b, cut } = g;
      const stage = new Stage({ canvas: document.getElementById("stage"), width: 1920, height: 1080, background: "#040405", samples: 8,
                                dof: { strength: 32, max: 42 }, grain: 0.03, vignette: 0.38, bloom: { strength: 1.15, threshold: 1.0 } });
      ground(stage, { colorA: "#050506", colorB: "#050506", dots: 0, size: 60, z: -4 });
      await stage.studio({ env: 0.8, key: 2.0, fill: 0.55, rim: 2.6, warm: "#ffe6e8", cool: "#ffc9d1" });
      const FLOOR_Y = -0.545;
      await reflectiveFloor(stage, { y: FLOOR_Y, size: 14, color: "#2a2a30" });
      const tl = gsap.timeline({ paused: true, defaults: { ease: "power2.out" } });
      const d = director(stage, tl), { cam, D } = d;

      // ── the room: neon on the sides of the frame (screen-space), a red pool of light on the floor ─────────────────────
      const U = stage.presentMat.uniforms;
      const look = noir(stage, tl);   // NEON NOIR edge light: subtle, one place (kit.js)
      const edge = (t, v, dur = 0.12) => tl.to(U.edge, { value: v, duration: dur, ease: "power2.out" }, t);
      const pulse = (t, k = 0.95) => look.pulse(t, k);
      const floor = d.panel("floor", 2600, 900); floor.group.rotation.x = -Math.PI / 2; floor.group.position.set(0, FLOOR_Y + 0.004, 0.05); floor.state.glow = 0.4;
      // two neon tubes far behind, drawn on the big moments
      const nt1 = d.panel("nt1", 2600, 1500, { live: true }), nt2 = d.panel("nt2", 2600, 1500, { live: true });
      nt1.group.position.set(0, 0.25, -1.3); nt2.group.position.set(0, 0.1, -1.6); nt1.state.glow = 2.2; nt2.state.glow = 2.0;
      const tube = { a: 1, b: 1 };

      // ═══ BAR 0 · the search — a macro on the cursor, the list cascades, the freeze in the silence, the dive ═══════════
      const sb = d.panel("sb", 1180, 150, { live: true, radius: 75, shadow: { blur: 70, y: 36, opacity: 0.7, color: "#000" } });
      const rows = [0, 1, 2, 3, 4].map((i) => d.panel("sg" + i, 1180, 110, { radius: 26, shadow: { blur: 40, y: 20, opacity: 0.55, color: "#000" } }));
      const S1 = new THREE.Group(); stage.scene.add(S1); S1.add(sb.group); rows.forEach((r) => S1.add(r.group));
      sb.group.position.set(0, 0.36, 0.06);
      rows.forEach((r, i) => { r.group.position.set(0, 0.18 - i * 0.128, 0); r.state.opacity = 0; });
      S1.rotation.set(-0.3, 0.3, 0.03); S1.position.set(0, -0.05, 0);
      Object.assign(cam, { x: -0.26, y: 0.36, z: 0.62, tx: -0.33, ty: 0.33, tz: 0.06, roll: 0.03 });   // macro: the cursor
      const q = { n: 0 }, QT = "claude code motion graphics";
      tl.to(q, { n: QT.length, duration: 0.9, ease: "none" }, 0.04);
      tl.to(cam, { x: 0.12, y: 0.12, z: 1.95, tx: 0.0, ty: 0.06, tz: 0, roll: 0.0, duration: 1.15, ease: "power3.inOut" }, 0.45);   // reveal the bar
      rows.forEach((r, i) => {                                                                    // the cascade
        const t = 0.95 + i * 0.07;
        tl.set(r.state, { opacity: 1 }, t);
        SF(r.group.position, { y: 0.32, z: -0.06 }, { y: 0.18 - i * 0.128, z: 0 }, t, "ui", 0.7);
        SF(r.group.rotation, { x: -0.5 }, { x: 0 }, t, "ui", 0.7);
      });
      const pick = { on: 0 };
      tl.set(pick, { on: 1 }, b(2));                                                               // beat 2: the pick
      S(rows[0].group.position, { z: 0.06 }, b(2), "snap", 0.35);
      tl.set(cam, { focus: -1 }, 0);
      // the silence before the drop: everything holds, the room goes dark, a tube starts drawing
      edge(1.6, 0.05, 0.15);
      tl.to(tube, { a: 0.55, duration: 0.9, ease: "power2.in" }, 1.62);
      tl.to(cam, { x: 0.02, y: 0.2, z: 0.6, tx: 0.0, ty: 0.22, roll: -0.04, duration: B(1) - 1.9 - 0.02, ease: "power4.in" }, 1.9);   // the dive

      // ═══ the phone ════════════════════════════════════════════════════════════════════════════════════════════════════
      const scr = d.panel("scr", 390, 844, { live: true, scale: 3 });
      const phone = await loadDevice(stage, { url: "assets/vendor/models/iphone.glb", kind: "phone", screen: scr, size: 1.02, finish: "#26262a" });
      phone.group.visible = false; scr.state.opacity = 0;
      phone.group.updateMatrixWorld(true);
      const disp = phone.display, pos = disp.geometry.attributes.position, uv = disp.geometry.attributes.uv;
      let iTL = 0, iTR = 0, iBL = 0;
      for (let i = 0; i < uv.count; i++) { const u = uv.getX(i), v = uv.getY(i);
        if (u - v < uv.getX(iTL) - uv.getY(iTL)) iTL = i; if (u + v > uv.getX(iTR) + uv.getY(iTR)) iTR = i; if (-u - v > -uv.getX(iBL) - uv.getY(iBL)) iBL = i; }
      const wp = (i) => phone.group.worldToLocal(disp.localToWorld(new THREE.Vector3(pos.getX(i), pos.getY(i), pos.getZ(i))));
      const TL = wp(iTL), TR = wp(iTR), BL = wp(iBL), ux = TR.clone().sub(TL), vy = BL.clone().sub(TL);
      const GLASS_Z = Math.max(TL.z, TR.z, BL.z) + 0.004, PX = ux.length() / 390;
      const scrEl = document.getElementById("scr");
      const rectIn = (el) => { const R = scrEl.getBoundingClientRect(), r = el.getBoundingClientRect(); return { x: r.left - R.left, y: r.top - R.top, w: r.width, h: r.height }; };
      const dsEl = document.getElementById("ds"); dsEl.style.transform = "none";
      const rLk = rectIn(document.getElementById("lk")), rMem = rectIn(document.getElementById("memCell")), rJn = rectIn(document.getElementById("jn"));
      dsEl.style.transform = "";
      const cx = (r) => r.x + r.w / 2, cy = (r) => r.y + r.h / 2;
      const onGlass = (p, x, y, w, h, lift = 0.002) => {
        phone.group.add(p.group);
        const c = TL.clone().add(ux.clone().multiplyScalar((x + w / 2) / 390)).add(vy.clone().multiplyScalar((y + h / 2) / 844));
        p.group.position.set(c.x, c.y, GLASS_Z + lift); p.group.scale.setScalar(PX / 0.001);
        p.home = { x: c.x, y: c.y, z: GLASS_Z + lift, s: PX / 0.001 }; p.state.opacity = 0; return p;
      };
      // each pop-out carries its neon outline (a child, so it moves with it)
      const withOutline = (p, ol) => { p.group.add(ol.group); ol.group.position.set(0, 0, 0.004); ol.group.scale.setScalar(1); ol.state.glow = 2.4; ol.state.opacity = 0; p.ol = ol; return p; };
      const pPl = withOutline(onGlass(d.panel("pPl", 390, 219, { radius: 10, scale: 3, shadow: { blur: 40, y: 26, opacity: 0.6, color: "#000" } }), 0, 48, 390, 219), d.panel("olPl", 406, 235, { live: true }));
      const pLk = withOutline(onGlass(d.panel("pLk", 362, 64, { radius: 14, scale: 3, shadow: { blur: 40, y: 22, opacity: 0.6, color: "#000" } }), cx(rLk) - 181, cy(rLk) - 32, 362, 64), d.panel("olLk", 378, 80, { live: true }));
      const pMem = withOutline(onGlass(d.panel("pMem", 150, 90, { radius: 14, scale: 3, shadow: { blur: 40, y: 22, opacity: 0.45, color: "#000" } }), cx(rMem) - 75, cy(rMem) - 45, 150, 90), d.panel("olMem", 166, 106, { live: true }));
      const ol = { pl: 1, lk: 1, mem: 1 };                                                       // outline draw-on (dash offset 1 → 0)
      // a pop: lift off the glass toward the camera and the open side, the outline draws on, focus follows it
      const pop = (p, key, t, to, focusTo, holdTo, focusBack) => {
        tl.set(p.state, { opacity: 1 }, t); tl.set(p.ol.state, { opacity: 1 }, t);
        SF(p.group.position, { x: p.home.x, y: p.home.y, z: p.home.z }, { x: p.home.x + to.x, y: p.home.y + to.y, z: p.home.z + to.z }, t, "ui", 0.85);
        SF(p.group.rotation, { y: 0, x: 0 }, { y: to.ry, x: to.rx || 0 }, t, "ui", 0.85);
        SF(p.group.scale, { x: p.home.s, y: p.home.s }, { x: p.home.s * to.s, y: p.home.s * to.s }, t, "ui", 0.85);
        SF(ol, { [key]: 1 }, { [key]: 0 }, t + 0.1, "card", 0.6);
        tl.to(cam, { focus: focusTo, duration: 0.45, ease: "power2.inOut" }, t + 0.05);       // rack focus onto it
        S(p.group.position, { x: p.home.x, y: p.home.y, z: p.home.z }, holdTo, "snap", 0.36);
        S(p.group.rotation, { y: 0, x: 0 }, holdTo, "snap", 0.36);
        S(p.group.scale, { x: p.home.s, y: p.home.s }, holdTo, "snap", 0.36);
        tl.set([p.state, p.ol.state], { opacity: 0 }, holdTo + 0.36);
        if (focusBack) tl.to(cam, { focus: focusBack, duration: 0.3, ease: "power2.inOut" }, holdTo);
      };

      // ═══ BAR 1 · THE DROP — the phone spins in on the bass ═══════════════════════════════════════════════════════════
      const D1 = cut(B(1));
      tl.set(S1, { visible: false }, D1);
      tl.set(phone.group, { visible: true }, D1); tl.set(scr.state, { opacity: 1 }, D1);
      d.flash(D1, 0.16, 0.2); pulse(D1, 1.15);
      phone.group.position.set(-0.3, 0, 0);
      SF(phone.group.position, { y: -0.28, z: -0.5 }, { y: 0, z: 0 }, D1, "heavy", 0.95);
      SF(phone.group.rotation, { x: 0.25, y: -3.3, z: 0.18 }, { x: 0.05, y: 0.36, z: 0.02 }, D1, "heavy", 1.1);
      tl.set(cam, { x: 0.3, y: 0.02, z: 1.55, tx: 0.0, ty: 0.0, tz: 0, roll: -0.05, focus: 2.0, aperture: 1.15 }, D1);
      tl.to(cam, { x: 0.18, y: 0.08, z: 2.15, tx: 0.04, ty: 0.02, roll: 0, focus: 2.12, duration: 1.0, ease: "expo.out" }, D1 + 0.002);
      tl.fromTo(tube, { a: 0.55 }, { a: 0, duration: 0.7, ease: "power3.out", immediateRender: false }, D1);   // the tube completes
      tl.to(phone.group.rotation, { y: 0.16, duration: 1.4, ease: "power1.inOut" }, D1 + 1.1);
      pop(pPl, "pl", B(1) + b(1) - 0.02, { x: 0.5, y: -0.06, z: 0.28, ry: -0.4, s: 1.55 }, 1.87, B(2) - 0.42, 2.2);
      tl.to(cam, { x: 0.32, tx: 0.14, duration: 1.3, ease: "power2.inOut" }, B(1) + b(1));
      pulse(B(1) + b(2), 0.7);

      // ═══ BAR 2 · the description — the link comes out of the glass ════════════════════════════════════════════
      const ui = { ds: 0, sk: 0, tapX: 0, tapY: 0, tap: 0, tapDk: 0, join: 0 };
      SF(ui, { ds: 0 }, { ds: 1 }, B(2) - 0.05, "card", 0.6);
      pulse(cut(B(2)), 0.85);
      tl.to(phone.group.position, { x: 0.3, duration: 0.7, ease: "power3.inOut" }, B(2) - 0.25);
      tl.to(phone.group.rotation, { y: -0.34, x: 0.04, z: -0.02, duration: 0.8, ease: "power3.inOut" }, B(2) - 0.25);
      tl.to(cam, { x: -0.2, y: 0.04, z: 2.05, tx: -0.02, ty: 0.0, focus: 2.04, duration: 0.8, ease: "power3.inOut" }, B(2) - 0.25);
      pop(pLk, "lk", B(2) + b(1), { x: -0.58, y: 0.08, z: 0.3, ry: 0.42, s: 2.0 }, 1.78, B(3) - 0.34, 2.1);
      const TAP2 = B(2) + b(2.5);
      tl.set(ui, { tapX: cx(rLk), tapY: cy(rLk), tapDk: 0 }, TAP2 - 0.06);
      SF(ui, { tap: 0 }, { tap: 1 }, TAP2 - 0.04, "card", 0.5);
      S(pLk.group.scale, { x: pLk.home.s * 1.85, y: pLk.home.s * 1.85 }, TAP2 - 0.05, "snap", 0.22);
      tl.to(phone.group.rotation, { y: -0.34 + Math.PI * 2, duration: 0.55, ease: "power3.inOut" }, B(3) - 0.28);   // the spin to the community page
      tl.set(ui, { ds: 0, sk: 1, tap: 0 }, B(3) - 0.01);
      tl.set(phone.group.rotation, { y: -0.34 }, B(3) + 0.28);

      // ═══ BAR 3 · the community — the member count comes out, JOIN gets tapped ═══════════════════════════════════════════════════
      pulse(cut(B(3)), 1.0);
      tl.to(phone.group.position, { x: -0.3, duration: 0.7, ease: "power3.inOut" }, B(3) + 0.28);
      tl.to(phone.group.rotation, { y: 0.34, x: 0.03, duration: 0.8, ease: "power3.inOut" }, B(3) + 0.28);
      tl.to(cam, { focus: 2.12, duration: 0.25, ease: "power2.inOut" }, B(3) - 0.3);
      tl.to(cam, { x: 0.24, y: 0.03, z: 2.1, tx: 0.04, ty: 0.0, duration: 0.8, ease: "power3.inOut" }, B(3) + 0.2);
      pop(pMem, "mem", B(3) + b(1.5), { x: 0.62, y: 0.08, z: 0.32, ry: -0.42, s: 2.8 }, 1.79, B(4) - 0.34, 2.17);
      const TAP3 = B(3) + b(3);
      tl.set(ui, { tapX: cx(rJn), tapY: cy(rJn), tapDk: 1 }, TAP3 - 0.06);
      SF(ui, { tap: 0 }, { tap: 1 }, TAP3 - 0.04, "card", 0.5);
      SF(ui, { join: 0 }, { join: 1 }, TAP3 - 0.05, "snap", 0.35);
      pulse(TAP3, 0.8);

      // ═══ BAR 4 · the vault bursts out of the glass ═════════════════════════════════════════════════════════════════
      const V0 = cut(B(4));
      pulse(V0, 1.2);
      const packs = packDom.map((dm, i) => {
        const p = d.panelEl(dm, 230, 150, { radius: 18, shadow: { blur: 40, y: 24, opacity: 0.55, color: "#000" } });
        stage.scene.add(p.group); p.state.opacity = 0;
        const a = (i / PACKS.length) * Math.PI * 2 + 0.3, ring = i % 2 ? 1.0 : 0.76;
        return { p, x: Math.cos(a) * ring * 1.2, y: 0.05 + Math.sin(a) * ring * 0.55, z: -0.2 + (i % 3) * 0.13, ry: -Math.cos(a) * 0.55 };
      });
      tl.to(phone.group.rotation, { y: 0, x: 0, z: 0, duration: 0.5, ease: "power3.inOut" }, V0 - 0.2);
      tl.to(phone.group.position, { x: 0, y: 0, z: -0.1, duration: 0.5, ease: "power3.inOut" }, V0 - 0.2);
      packs.forEach((P, i) => {
        const t = V0 + 0.03 + i * 0.022;
        tl.set(P.p.state, { opacity: 1 }, t);
        SF(P.p.group.position, { x: 0, y: 0.05, z: 0.03 }, { x: P.x, y: P.y, z: P.z }, t, "ui", 0.95);
        SF(P.p.group.rotation, { y: 0, z: i % 2 ? 0.45 : -0.45 }, { y: P.ry, z: 0 }, t, "ui", 0.95);
        SF(P.p.group.scale, { x: 0.2, y: 0.2 }, { x: 1, y: 1 }, t, "ui", 0.95);
      });
      tl.fromTo(tube, { b: 1 }, { b: 0, duration: 0.8, ease: "power3.out", immediateRender: false }, V0);
      tl.set(cam, { focus: -1, aperture: 1.1 }, V0);
      tl.to(cam, { x: 0, y: 0.06, z: 2.9, tx: 0, ty: 0.02, tz: 0, roll: 0, duration: 1.3, ease: "expo.out" }, V0);
      const tyA = d.hud("tyA", 1200, 210, -250, 380);
      tl.set(tyA.state, { opacity: 1 }, B(4) + b(2));
      SF(tyA.group.position, { x: tyA.group.position.x - 0.01 }, { x: tyA.group.position.x }, B(4) + b(2), "heavy", 0.8);
      packs.forEach((P) => tl.to(P.p.state, { dim: 0.35, duration: 0.3 }, B(4) + b(2)));         // the type reads clean
      pulse(B(4) + b(2), 0.9);

      // ═══ BAR 5 · the wordmark, in front of the vault — crisp letters, a red halo behind them ═══════════════════════
      const W0 = cut(B(5));
      d.out([tyA], W0 - 0.001);
      pulse(W0, 1.3);
      const wmh = d.at(d.panel("wmh", 1800, 400), 0, 0.12, 1.19), wm = d.at(d.panel("wm", 1600, 260), 0, 0.12, 1.2), wsub = d.at(d.panel("wsub", 1600, 80), 0, -0.1, 1.2);
      for (const p of [wmh, wm, wsub]) p.state.opacity = 0;
      wmh.state.glow = 1.3;
      tl.to(cam, { x: 0, y: 0.1, z: 3.25, tx: 0, ty: 0.06, tz: 0.6, roll: 0, focus: 2.08, aperture: 1.35, duration: 0.9, ease: "power3.out" }, W0);
      tl.to(cam, { z: 3.08, duration: 15.7 - W0 - 0.9, ease: "none" }, W0 + 0.9);
      packs.forEach((P) => tl.to(P.p.state, { dim: 0.55, duration: 0.4 }, W0));
      tl.to(phone.group.position, { y: -1.6, z: -0.6, duration: 0.55, ease: "power3.in" }, W0 - 0.15);
      tl.set(phone.group, { visible: false }, W0 + 0.45);
      tl.set(wm.state, { opacity: 1 }, W0); tl.set(wmh.state, { opacity: 1 }, W0);
      SF(wm.group.scale, { x: 1.14, y: 1.14 }, { x: 1, y: 1 }, W0, "heavy", 1.0);
      SF(wmh.group.scale, { x: 1.14, y: 1.14 }, { x: 1, y: 1 }, W0, "heavy", 1.0);
      SF(wmh.state, { glow: 1.4 }, { glow: 0.55 }, W0, "heavy", 1.2);
      tl.set(wsub.state, { opacity: 1 }, B(5) + b(1.5));
      SF(wsub.group.position, { y: -0.13 }, { y: -0.1 }, B(5) + b(1.5), "heavy", 0.8);
      tl.to({}, { duration: 0.001 }, 15.7);

      // ── the live layers ─────────────────────────────────────────────────────────────────────────────────────────────
      const $ = (id) => document.getElementById(id);
      const qt = $("qt"), car = $("car"), ds = $("ds"), yt = $("yt"), sk = $("sk"), sbar = $("sbar"), hi = $("hi"), tap = $("tap"),
            lk = $("lk"), jn = $("jn"), memCell = $("memCell"), ytPlayer = $("ytPlayer"), sg0 = $("sg0"),
            p1 = $("nt1p"), p2 = $("nt2p"), r1 = $("olPlr"), r2 = $("olLkr"), r3 = $("olMemr");
      const L1 = p1.getTotalLength(), L2 = p2.getTotalLength(), R1 = r1.getTotalLength(), R2 = r2.getTotalLength(), R3 = r3.getTotalLength();
      p1.style.strokeDasharray = L1; p2.style.strokeDasharray = L2; r1.style.strokeDasharray = R1; r2.style.strokeDasharray = R2; r3.style.strokeDasharray = R3;
      d.onSync((ts) => {
        qt.textContent = QT.slice(0, Math.floor(q.n)); car.style.opacity = Math.floor(ts / 0.32) % 2 ? 1 : 0;
        sg0.style.background = pick.on ? "#2c2c32" : "#141416"; sg0.style.borderColor = pick.on ? "#ff2440" : "#232327";
        p1.style.strokeDashoffset = L1 * tube.a; p2.style.strokeDashoffset = L2 * tube.b;
        r1.style.strokeDashoffset = R1 * ol.pl; r2.style.strokeDashoffset = R2 * ol.lk; r3.style.strokeDashoffset = R3 * ol.mem;
        ds.style.transform = `translateY(${(1 - ui.ds) * 680}px)`;
        sk.style.opacity = ui.sk; yt.style.opacity = 1 - ui.sk;
        sbar.style.color = ui.sk > 0.5 ? "#202124" : "#f1f1f1"; sbar.style.background = ui.sk > 0.5 ? "#f8f7f5" : "#0f0f0f";
        hi.style.background = ui.sk > 0.5 ? "#202124" : "#f1f1f1";
        tap.className = "tap" + (ui.tapDk ? " dk" : ""); tap.style.left = ui.tapX + "px"; tap.style.top = ui.tapY + "px";
        tap.style.transform = `scale(${ui.tap * 1.6})`; tap.style.opacity = ui.tap > 0 && ui.tap < 1 ? String(1 - ui.tap) : "0";
        ytPlayer.style.visibility = pPl.state.opacity > 0.5 ? "hidden" : "visible";
        lk.style.visibility = pLk.state.opacity > 0.5 ? "hidden" : "visible";
        memCell.style.visibility = pMem.state.opacity > 0.5 ? "hidden" : "visible";
        jn.style.transform = `scale(${1 - 0.05 * Math.sin(Math.min(1, ui.join) * Math.PI)})`; jn.style.background = ui.join > 0.15 && ui.join < 0.95 ? "#efc35f" : "#f8d481";
      });
      await d.bind();
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
