# -*- coding: utf-8 -*-
"""诊断：输入桥接 findTarget() 的稳健性 + 真实鼠标 vs 直接派发对照。

背景：index.html 的「输入桥接」靠 Laya.__classmap['laya.renders.Render'].canvas
      找到迷你画布；若这一步失败，fire() 会静默 return，所有点击被丢弃。
      这正好解释「画面正常但按钮点不动」。

本脚本回答四件事：
  1) 迷你 DOM 是否生效、迷你画布叫什么、tagName/width 是什么
  2) findTarget() 的主路径与兜底路径分别能否命中
  3) 真实鼠标点击（走 window 桥接）能否进关
  4) 对照：绕过 window 监听、直接把事件喂给迷你画布，能否进关
"""
import time, json
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8123/index.html"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT = r"D:\B++\WorkBuddy\2026-10-09-09-35-40"

PROBE = r"""() => {
  var o = {};
  try {
    var map = Laya.__classmap || {};
    o.classmapKeys = Object.keys(map).length;
    o.renderKeyPresent = !!map['laya.renders.Render'];
    var R = map['laya.renders.Render'];
    if (R) {
      o.renderCanvas = R.canvas ? 'yes' : 'no';
      if (R.canvas) {
        var c = R.canvas;
        o.tagName = c.tagName;
        o.w = c.width; o.h = c.height;
        o.hasDispatch = typeof c.dispatchEvent;
        o.hasListeners = typeof c.addEventListener;
        o.hasBBox = typeof c.getBoundingClientRect;
        o.attrW = c.getAttribute ? c.getAttribute('width') : null;
        try { o.offsetW = c.offsetWidth; o.clientW = c.clientWidth; } catch(e){ o.offsetW = 'err'; }
      }
    }
    // 兜底扫描（index.html 里的第二条路径）
    var hits = [], hits2 = [], n = 0;
    for (var k in map) { n++;
      var v = map[k];
      try {
        if (v && v.canvas && v.canvas.width && v.canvas.tagName === 'CANVAS' && typeof v.canvas.dispatchEvent === 'function') hits.push(k);
      } catch(e){}
      try { if (v && v.canvas && typeof v.canvas.dispatchEvent === 'function') hits2.push(k); } catch(e){}
    }
    o.scanned = n;
    o.fallbackStrict = hits.slice(0, 6);
    o.fallbackLoose  = hits2.slice(0, 6);
    o.docIsNative = (typeof HTMLDocument !== 'undefined' && document instanceof HTMLDocument);
    var lc = document.getElementById('layaCanvas');
    o.layaCanvas = lc ? ('nodeType=' + lc.nodeType + ' tag=' + lc.tagName + ' w=' + lc.width) : 'none';
    o.stageScale = Laya.stage ? (Laya.stage.scaleMode + '/' + Laya.stage.screenMode + '/' + Laya.stage.alignH + ',' + Laya.stage.alignV) : 'no-stage';
    o.design = Laya.stage ? (Laya.stage.designWidth + 'x' + Laya.stage.designHeight) : '?';
    o.win = window.innerWidth + 'x' + window.innerHeight + '@' + (window.devicePixelRatio || 1);
    // Laya 当前 stage 尺寸（这是 Laya 自己认的，不是 CSS）
    o.stageSize = Laya.stage ? (Laya.stage.width + 'x' + Laya.stage.height) : '?';
    var m = Laya.stage && Laya.stage._canvasTransform;
    if (m) { o.mtx = [ +m.a.toFixed(4), +m.d.toFixed(4), Math.round(m.tx), Math.round(m.ty) ]; }
  } catch(e) { o.err = '' + e; }
  return JSON.stringify(o);
}"""

TREE = r"""() => {
  var out = [];
  (function w(n, d) {
    if (d > 6 || !n || out.length > 90) return;
    var nm = n.name || '';
    var cn = (n.constructor && n.constructor.name) || '?';
    out.push('  '.repeat(d) + nm + ' <' + cn + '> ' + Math.round(n.width) + 'x' + Math.round(n.height) + ' vis=' + n.visible);
    try { for (var i = 0; i < n.numChildren; i++) w(n.getChildAt(i), d + 1); } catch(e){}
  })(Laya.stage, 0);
  return out.join('\n');
}"""

SKIP = r"""() => {
  var st = {panel: false, skipFound: false};
  (function w(n, d) { if (d > 20 || !n) return;
    try { if (n.SelectSkinPanel) st.panel = true; } catch(e){}
    try { if (n.SkipBtn) {
      st.skipFound = true;
      var b = n.SkipBtn;
      st.vis = b.visible;
      st.disabled = !!b.disabled;
      var g1 = b.localToGlobal(new Laya.Point(0, 0));
      var g2 = b.localToGlobal(new Laya.Point(b.width, b.height));
      st.rect = [Math.round(g1.x), Math.round(g1.y), Math.round(g2.x), Math.round(g2.y)];
      st.cx = Math.round((g1.x + g2.x) / 2);
      st.cy = Math.round((g1.y + g2.y) / 2);
      st.size = Math.round(b.width) + 'x' + Math.round(b.height);
      st.alpha = b.alpha;
      st.mouseEnabled = b.mouseEnabled;
      st.hitArea = b.hitArea ? 'yes' : 'no';
      st.parentName = b.parent ? (b.parent.name || '?') : '?';
    } } catch(e){ st.skipErr = '' + e; }
    try { for (var i = 0; i < n.numChildren; i++) w(n.getChildAt(i), d + 1); } catch(e){}
  })(Laya.stage, 0);
  var d = {}; try { d = JSON.parse(Laya.LocalStorage.getItem('userData') || '{}'); } catch(e){}
  st.saveKeys = Object.keys(d).length;
  st.saveDump = JSON.stringify(d).slice(0, 400);
  return JSON.stringify(st);
}"""

DIRECT = r"""() => {
  // 绕过 window 桥接：直接给迷你画布喂 mousedown/mouseup（模拟桥接成功后应有的效果）
  var map = Laya.__classmap || {};
  var R = map['laya.renders.Render'];
  if (!R || !R.canvas) return 'no-canvas';
  var c = R.canvas;
  var m = Laya.stage._canvasTransform;
  var dw = Laya.stage.designWidth || 720, dh = Laya.stage.designHeight || 1280;
  var vw = window.innerWidth, vh = window.innerHeight, r = dw / dh;
  var w = Math.min(vw, vh * r), h = w / r, s = w / dw;
  var left = (vw - w) / 2, top = (vh - h) / 2;
  try { m.identity(); m.scale(s, s); m.tx = left; m.ty = top; } catch(e){}
  var pt = window.__tgt || [0, 0];
  var sx = pt[0], sy = pt[1];
  // 屏幕坐标 -> stage 坐标
  var stx = (sx - left) / s, sty = (sy - top) / s;
  function fire(type) {
    var ev = { type: type, clientX: sx, clientY: sy, pageX: sx, pageY: sy,
               button: 0, buttons: 1, detail: 1, wheelDelta: 0, identifier: 0,
               target: c, currentTarget: c,
               preventDefault: function(){}, stopPropagation: function(){} };
    try { c.dispatchEvent(ev); } catch(e){ return '' + e; }
    return 'ok';
  }
  return JSON.stringify({ scale: +s.toFixed(4), left: Math.round(left), top: Math.round(top),
                          stagePt: [Math.round(stx), Math.round(sty)],
                          down: fire('mousedown'), up: fire('mouseup') });
}"""


def clear_and_load(page):
    page.goto(URL, wait_until="load", timeout=30000); time.sleep(11)
    page.evaluate("() => Laya.LocalStorage.removeItem('userData')")
    page.goto(URL, wait_until="load", timeout=30000); time.sleep(11)


def to_skin(page):
    page.mouse.click(360, 740); time.sleep(3.5)
    page.mouse.click(359, 889); time.sleep(2.6)


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=EDGE)
    page = browser.new_page(viewport={"width": 720, "height": 1280})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))

    clear_and_load(page)

    print("=== 1) 桥接环境探测 ===")
    print(" ", page.evaluate(PROBE))

    to_skin(page)

    print("\n=== 2) 皮肤弹窗状态 ===")
    st = json.loads(page.evaluate(SKIP))
    print(" ", json.dumps(st, ensure_ascii=False))

    print("\n=== 3) 场景树（前 6 层）===")
    print(page.evaluate(TREE))

    if not st.get("skipFound"):
        print("\n!! 没找到 SkipBtn，后续对照无法进行")
        browser.close(); raise SystemExit

    # --- 3) 真实鼠标点击（走 window 桥接）---
    print("\n=== 4) 真实鼠标点击 SkipBtn 中心（走 window 桥接）===")
    page.mouse.move(st["cx"], st["cy"]); time.sleep(0.3)
    page.mouse.down(); time.sleep(0.2); page.mouse.up()
    time.sleep(5)
    after = json.loads(page.evaluate(SKIP))
    print(f"  点后: panelAlive={after.get('panel')} skipFound={after.get('skipFound')}")
    print(f"  → {'进关了（面板已关）' if not after.get('panel') else '面板还在（点击无效！）'}")
    if errs:
        print("  PAGEERROR:", errs[0][:200])
    page.screenshot(path=f"{OUT}\\br_real.png")

    # --- 4) 对照：直接派发 ---
    if after.get("panel"):
        print("\n=== 5) 对照：绕过 window 桥接，直接派发给迷你画布 ===")
        page.evaluate("(p) => { window.__tgt = p; }", [st["cx"], st["cy"]])
        print("  直接派发:", page.evaluate(DIRECT))
        time.sleep(5)
        after2 = json.loads(page.evaluate(SKIP))
        print(f"  点后: panelAlive={after2.get('panel')} skipFound={after2.get('skipFound')}")
        print(f"  → {'直接派发能关面板 ⇒ window 桥接没把事件送达' if not after2.get('panel') else '直接派发也无效 ⇒ 问题在按钮本身'}")
        page.screenshot(path=f"{OUT}\\br_direct.png")
    else:
        print("\n(真实鼠标已能进关，跳过对照)")

    browser.close()
