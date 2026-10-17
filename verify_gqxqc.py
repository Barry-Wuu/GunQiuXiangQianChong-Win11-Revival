# -*- coding: utf-8 -*-
"""滚球向前冲 Web 版 · 第一轮无头验证：资源请求 / JS 报错 / 渲染判定"""
import time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8123/index.html"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT = r"D:\B++\WorkBuddy\2026-10-09-09-35-40"

console_msgs, page_errors, failed, allreq = [], [], [], []

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=EDGE)          # 默认 GL，勿加 swiftshader
    page = browser.new_page(viewport={"width": 720, "height": 1280})
    page.on("console", lambda m: console_msgs.append((m.type, m.text, m.location)))
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    page.on("request", lambda r: allreq.append(r.url))
    page.on("response", lambda r: failed.append((r.status, r.url)) if r.status >= 400 else None)
    page.on("requestfailed", lambda r: failed.append(("FAILED", r.url)))

    t0 = time.time()
    page.goto(URL, wait_until="load", timeout=30000)
    time.sleep(12)                       # 等资源 + 首屏
    try:
        page.mouse.click(360, 640)       # 满足音频/手势门控
    except Exception:
        pass
    time.sleep(5)
    elapsed = round(time.time() - t0, 1)

    info = page.evaluate("""() => ({
        canvases: document.querySelectorAll('canvas').length,
        hasLaya: (typeof window.Laya !== 'undefined'),
        gameGlobal: (typeof window.GameGlobal !== 'undefined'),
        getApp: (typeof window.getApp !== 'undefined'),
        title: document.title
    })""")

    # 逐 canvas 元素截图（唯一可靠路径，整页截图抓不到 WebGL 合成帧）
    shots = []
    for i, e in enumerate(page.query_selector_all("canvas")):
        fn = OUT + r"\gq_canvas_%d.png" % i
        try:
            e.screenshot(path=fn); shots.append(fn)
        except Exception as ex:
            print("shot err", i, ex)

    browser.close()

print("=== 本地资源请求 ===")
local = [u for u in allreq if "127.0.0.1" in u and not u.endswith("index.html")]
print("  total:", len(local))
print("  关卡 .ls? ", any(".ls" in u for u in local))
print("  音频?     ", any(u.endswith(".mp3") or u.endswith(".ogg") for u in local))

print("=== 页面信息 ===", info, "| 载入耗时", elapsed, "s")
print("=== HTTP 非 200 ===")
for s, u in failed:
    print(f"  [{s}] {u}")
if not failed:
    print("  无（全部 200）")

print("=== canvas 像素分析 ===")
from PIL import Image
best = None
for fn in shots:
    try:
        im = Image.open(fn).convert("RGB"); w, h = im.size; px = im.load()
        total = nonblack = 0; colors = set()
        for y in range(0, h, 4):
            for x in range(0, w, 4):
                r, g, b = px[x, y]; total += 1; colors.add((r // 16, g // 16, b // 16))
                if r > 12 or g > 12 or b > 12:
                    nonblack += 1
        ratio = round(nonblack / total, 3)
        print(f"  {fn} {w}x{h} nonblack={ratio} buckets={len(colors)}")
        if best is None or ratio > best[1]:
            best = (fn, ratio)
    except Exception as e:
        print("  err", fn, e)

print("=== 判定 ===")
print("  RENDERED OK -> " + best[0] if best and best[1] > 0.2
      else "  NO VISIBLE RENDER (best=%s) —— 换/去掉 GL 标志重跑" % (best,))

print("=== JS 报错 ===")
for e in page_errors:
    print("  ERR:", e)

print("=== console error/warning（带 location）===")
for t, m, loc in console_msgs:
    if t in ("error", "warning"):
        print(f"  [{t}] {m[:140]}")
        print(f"        loc={loc}")
