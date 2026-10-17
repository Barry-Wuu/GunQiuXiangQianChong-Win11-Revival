# -*- coding: utf-8 -*-
"""验证 index.html 的「诊断模式」：
  1) 默认（不带参数）不显示诊断面板，但版本号已挂上
  2) 按 F9 开关面板
  3) 进皮肤弹窗后，面板显示「皮肤弹窗在」
  4) 点「不了谢谢」后，红点落在按钮上，面板变「已进关」
"""
import time, json
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8123/index.html"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT = r"D:\B++\WorkBuddy\2026-10-09-09-35-40"

SKIP = r"""() => {
  var st = {found: false, total: 0, fatal: null, skin: false, prop: []};
  function w(n, d) {
    if (!n || d > 30) return;
    st.total++;
    try { if (n.SelectSkinPanel) st.skin = true; } catch(e){}
    try { if (n.SkipBtn) {
      st.prop.push('SkipBtn@' + d);
      st.found = true;
      var b = n.SkipBtn;
      var g1 = b.localToGlobal(new Laya.Point(0, 0));
      var g2 = b.localToGlobal(new Laya.Point(b.width, b.height));
      var dw = Laya.stage.designWidth || 720, dh = Laya.stage.designHeight || 1280;
      var vw = window.innerWidth, vh = window.innerHeight, r = dw / dh;
      var ww = Math.min(vw, vh * r), s = ww / dw;
      st.cx = Math.round((vw - ww) / 2 + (g1.x + g2.x) / 2 * s);
      st.cy = Math.round((vh - ww / r) / 2 + (g1.y + g2.y) / 2 * s);
    } } catch(e){ st.err = '' + e; }
    try { for (var i = 0; i < n.numChildren; i++) w(n.getChildAt(i), d + 1); } catch(e){}
  }
  try { w(Laya.stage, 0); } catch(e){ st.fatal = '' + e; }
  return JSON.stringify(st);
}"""

PANEL = r"""() => {
  var d = document.getElementById('__gqxqc_diag');
  return JSON.stringify({
    exists: !!d,
    text: d ? d.textContent : null,
    dots: document.getElementsByClassName('__gqxqc_dot').length
  });
}"""

WAIT = 26
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=EDGE)
    page = browser.new_page(viewport={"width": 720, "height": 1280})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.on("console", lambda m: print("   [console]", m.type, m.text[:120])
            if m.type in ("error", "warning") else None)

    # networkidle：等资源真正下载完（单线程 http.server + 3.2MB main.js，固定 sleep 不可靠）
    page.goto(URL, wait_until="networkidle", timeout=180000); time.sleep(6)

    print("=== 1) 默认状态 ===")
    print("  版本号:", page.evaluate("() => window.__GQXQC_VER__"))
    print("  面板:", page.evaluate(PANEL))

    print("\n=== 2) 按 F9 开启 ===")
    page.keyboard.press("F9"); time.sleep(0.6)
    print("  面板:", page.evaluate(PANEL))
    page.screenshot(path=f"{OUT}\\dbg_on.png")

    # 进皮肤弹窗（720x1280 下 stage 坐标 == 屏幕坐标）
    page.mouse.click(360, 740); time.sleep(3.5)
    page.mouse.click(359, 889); time.sleep(2.6)
    st = json.loads(page.evaluate(SKIP))
    print("\n=== 3) 皮肤弹窗 ===")
    print("  SkipBtn:", st)
    print("  面板:", page.evaluate(PANEL))
    page.screenshot(path=f"{OUT}\\dbg_skin.png")

    if st.get("found"):
        print("\n=== 4) 点「不了谢谢」===")
        page.mouse.move(st["cx"], st["cy"]); time.sleep(0.25)
        page.mouse.down(); time.sleep(0.05)
        page.screenshot(path=f"{OUT}\\dbg_clicked.png")   # 抓红点还在的瞬间
        page.mouse.up()
        time.sleep(4)
        print("  点后:", page.evaluate(PANEL))
        page.screenshot(path=f"{OUT}\\dbg_after.png")

    print("\n=== 5) 再按 F9 关闭 ===")
    page.keyboard.press("F9"); time.sleep(0.5)
    print("  面板:", page.evaluate(PANEL))

    if errs:
        print("\nPAGEERROR:", errs[:3])
    browser.close()
