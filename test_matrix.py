# -*- coding: utf-8 -*-
"""矩阵验证：视口比例 × devicePixelRatio（= Windows 显示缩放 / 浏览器缩放）下，
皮肤弹窗「不了谢谢」是否仍可点击进关。

动机：headless 在 720x1280@dsf1 下 100% 正常，但用户侧「毫无反应」。
      高分屏笔记本常见 dsf=1.25/1.5；若某组合失效即锁定根因。
"""
import time, json, sys
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8123/index.html"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT = r"D:\B++\WorkBuddy\2026-10-09-09-35-40"

SKIP = r"""() => {
  var st = {panel: false, found: false, total: 0, fatal: null};
  function w(n, d) {
    if (!n || d > 30) return;
    st.total++;
    try { if (n.SelectSkinPanel) st.panel = true; } catch(e){}
    try { if (n.SkipBtn) {
      st.found = true;
      var b = n.SkipBtn;
      var g1 = b.localToGlobal(new Laya.Point(0, 0));
      var g2 = b.localToGlobal(new Laya.Point(b.width, b.height));
      var dw = Laya.stage.designWidth || 720, dh = Laya.stage.designHeight || 1280;
      var vw = window.innerWidth, vh = window.innerHeight, r = dw / dh;
      var ww = Math.min(vw, vh * r), s = ww / dw;
      var left = (vw - ww) / 2, top = (vh - ww / r) / 2;
      st.scr = [Math.round(left + g1.x * s), Math.round(top + g1.y * s),
                Math.round(left + g2.x * s), Math.round(top + g2.y * s)];
      st.cx = Math.round((st.scr[0] + st.scr[2]) / 2);
      st.cy = Math.round((st.scr[1] + st.scr[3]) / 2);
      st.vis = b.visible;
    } } catch(e){ st.err = '' + e; }
    try { for (var i = 0; i < n.numChildren; i++) w(n.getChildAt(i), d + 1); } catch(e){}
  }
  try { w(Laya.stage, 0); } catch(e){ st.fatal = '' + e; }
  st.win = window.innerWidth + 'x' + window.innerHeight + '@' + window.devicePixelRatio;
  return JSON.stringify(st);
}"""

VIEWS = [(720, 1280), (1366, 768)]
DSFS = [1, 1.5]
WAIT = 26      # 冷缓存 + 单线程 http.server，3.2MB main.js 下载慢，固定等待要放宽

rows = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=EDGE)
    for (vw, vh) in VIEWS:
        for dsf in DSFS:
            ctx = browser.new_context(viewport={"width": vw, "height": vh}, device_scale_factor=dsf)
            page = ctx.new_page()
            errs = []
            page.on("pageerror", lambda e: errs.append(str(e)))
            try:
                page.goto(URL, wait_until="load", timeout=60000); time.sleep(WAIT)
                page.evaluate("() => Laya.LocalStorage.removeItem('userData')")
                page.goto(URL, wait_until="load", timeout=60000); time.sleep(WAIT)
                # 进皮肤弹窗：主菜单 Play -> 关卡模式 -> 开始游戏
                # 用 stage 坐标换算成屏幕坐标来点，保证任意视口都对
                def click_stage(sx, sy):
                    m = page.evaluate("""(p) => {
                      var dw = Laya.stage.designWidth||720, dh = Laya.stage.designHeight||1280;
                      var vw = window.innerWidth, vh = window.innerHeight, r = dw/dh;
                      var w = Math.min(vw, vh*r), h = w/r, s = w/dw;
                      return [ (vw-w)/2 + p[0]*s, (vh-h)/2 + p[1]*s ];
                    }""", [sx, sy])
                    page.mouse.click(m[0], m[1])
                click_stage(360, 740); time.sleep(3.5)   # 关卡模式
                click_stage(359, 889); time.sleep(2.6)   # 开始游戏
                st = json.loads(page.evaluate(SKIP))
                if not st.get("found"):
                    page.screenshot(path=f"{OUT}\\mat_{vw}x{vh}_{dsf}_fail.png")
                    rows.append((vw, vh, dsf, "未找到 SkipBtn", st.get("win"),
                                 f'total={st.get("total")} panel={st.get("panel")} fatal={st.get("fatal")}'))
                    ctx.close(); continue
                page.mouse.move(st["cx"], st["cy"]); time.sleep(0.25)
                page.mouse.down(); time.sleep(0.18); page.mouse.up()
                time.sleep(5)
                after = json.loads(page.evaluate(SKIP))
                ok = not after.get("panel")
                rows.append((vw, vh, dsf, "进关 OK" if ok else "!! 无效 !!",
                             st.get("win"), f'戳点({st["cx"]},{st["cy"]}) err={errs[0][:60] if errs else "-"}'))
            except Exception as e:
                rows.append((vw, vh, dsf, "异常: " + str(e)[:60], "", ""))
            ctx.close()
            print(f"  完成 {vw}x{vh}@{dsf}", flush=True)
    browser.close()

print("\n===== 结果矩阵 =====")
print(f'{"视口":>12} {"dsf":>5}  {"结果":<10} {"window":<18} 备注')
for vw, vh, dsf, res, win, note in rows:
    print(f'{str(vw)+"x"+str(vh):>12} {dsf:>5}  {res:<10} {win:<18} {note}')
