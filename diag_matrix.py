# -*- coding: utf-8 -*-
"""最小复现：new_context(device_scale_factor=1) 下，进皮肤弹窗后为什么扫不到 SkipBtn？
   diag_bridge（browser.new_page）能找到，test_matrix（browser.new_context）找不到。
   逐项对比两种建页方式下的环境差异，并统计场景树规模。
"""
import time, json
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8123/index.html"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

ENVQ = r"""() => {
  var o = {};
  try { o.layaType = typeof Laya; } catch(e){ o.layaType = 'ERR:' + e; }
  try { o.hasStage = !!Laya.stage; } catch(e){ o.hasStage = 'ERR'; }
  try { o.numChildren = Laya.stage ? Laya.stage.numChildren : 'n/a'; } catch(e){ o.numChildren = 'ERR'; }
  try { o.stageSize = Laya.stage ? (Laya.stage.width + 'x' + Laya.stage.height) : 'n/a'; } catch(e){}
  try { o.localStorageType = typeof Laya.LocalStorage; } catch(e){}
  o.win = window.innerWidth + 'x' + window.innerHeight;
  o.dpr = window.devicePixelRatio;
  return JSON.stringify(o);
}"""

# 统计整棵树：总节点数、最大深度、名字里含 Skin/Skip 的节点
CENSUS = r"""() => {
  var total = 0, maxD = 0, hits = [], named = 0;
  function w(n, d) {
    if (!n || d > 30) return;
    total++;
    if (d > maxD) maxD = d;
    var nm = (n.name || '') + '|' + ((n.constructor && n.constructor.name) || '');
    if (n.name) named++;
    if (/skin|skip|panel|dialog|ui/i.test(nm)) hits.push(d + ':' + nm);
    try { if (n.SelectSkinPanel) hits.push(d + ':PROP:SelectSkinPanel'); } catch(e){}
    try { if (n.SkipBtn) hits.push(d + ':PROP:SkipBtn'); } catch(e){}
    try { for (var i = 0; i < n.numChildren; i++) w(n.getChildAt(i), d + 1); } catch(e){}
  }
  try { w(Laya.stage, 0); } catch(e){ return JSON.stringify({err: '' + e}); }
  return JSON.stringify({total: total, maxDepth: maxD, named: named, hits: hits.slice(0, 15)});
}"""


def run(browser, mode):
    if mode == "new_page":
        page = browser.new_page(viewport={"width": 720, "height": 1280})
    else:
        ctx = browser.new_context(viewport={"width": 720, "height": 1280}, device_scale_factor=1)
        page = ctx.new_page()
    page.goto(URL, wait_until="load", timeout=60000); time.sleep(26)
    page.evaluate("() => { try { Laya.LocalStorage.removeItem('userData'); } catch(e){} }")
    page.goto(URL, wait_until="load", timeout=60000); time.sleep(26)

    print(f"\n########## mode = {mode} ##########")
    print("  环境:", page.evaluate(ENVQ))

    # 点击坐标：两种方式都用纯 Python 算好的固定值（720x1280 下 stage 坐标 == 屏幕坐标）
    page.mouse.click(360, 740); time.sleep(3.5)
    page.mouse.click(359, 889); time.sleep(2.6)

    print("  进皮肤后 census:", page.evaluate(CENSUS))
    page.screenshot(path=rf"D:\B++\WorkBuddy\2026-10-09-09-35-40\rep_{mode}.png")
    if mode == "new_context":
        ctx.close()
    else:
        page.close()


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=EDGE)
    run(browser, "new_page")
    run(browser, "new_context")
    browser.close()
