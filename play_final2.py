# -*- coding: utf-8 -*-
"""滚球向前冲 · 最终进关：选 Ball_01(白球,已解锁) -> 进关 -> 方向键滚球"""
import time
from playwright.sync_api import sync_playwright
from PIL import Image

URL = "http://127.0.0.1:8123/index.html"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT = r"D:\B++\WorkBuddy\2026-10-09-09-35-40"

def shot(page, fn):
    import os, shutil
    for i, e in enumerate(page.query_selector_all("canvas")):
        tmp = fn.replace(".png", "_c%d.png" % i)
        try:
            e.screenshot(path=tmp)
        except Exception:
            continue
    big = None
    for i in range(10):
        f = fn.replace(".png", "_c%d.png" % i)
        if not os.path.exists(f):
            break
        try:
            im = Image.open(f).convert("RGB"); w, h = im.size
        except Exception:
            continue
        if w > 100 and h > 100:
            big = f
    if big:
        shutil.copyfile(big, fn)
        return True
    return False

def diff(f1, f2):
    a = Image.open(f1).convert("RGB"); b = Image.open(f2).convert("RGB")
    if a.size != b.size:
        return 1.0
    w, h = a.size; pa, pb = a.load(), b.load(); n = d = 0
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            r1, g1, b1 = pa[x, y]; r2, g2, b2 = pb[x, y]
            n += 1
            if abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2) > 30:
                d += 1
    return round(d / n, 3)

def slow_click(page, x, y, hover=0.8, hold=0.25):
    page.mouse.move(x, y); time.sleep(hover)
    page.mouse.down(); time.sleep(hold); page.mouse.up()

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=EDGE)
    page = browser.new_page(viewport={"width": 720, "height": 1280})
    page.goto(URL, wait_until="load", timeout=30000)
    time.sleep(12)
    page.mouse.click(360, 640)
    time.sleep(2)

    # 1. 关卡模式
    shot(page, OUT + r"\gg_0_menu.png")
    slow_click(page, 360, 773); time.sleep(3)
    shot(page, OUT + r"\gg_1_level.png")
    print("[1] 关卡模式:", diff(OUT + r"\gg_0_menu.png", OUT + r"\gg_1_level.png"))

    # 2. 开始游戏
    slow_click(page, 359, 889); time.sleep(3.5)
    shot(page, OUT + r"\gg_2_skin.png")
    print("[2] 开始游戏(弹窗):", diff(OUT + r"\gg_1_level.png", OUT + r"\gg_2_skin.png"))

    # 3. 点 Ball_01 白球（已解锁）-> SelectPiFu(1) -> 进关
    slow_click(page, 192, 348, hover=1.0); time.sleep(5)
    shot(page, OUT + r"\gg_3_ingame.png")
    d3 = diff(OUT + r"\gg_2_skin.png", OUT + r"\gg_3_ingame.png")
    print("[3] 点 Ball_01 进关:", d3)

    # 4. HUD 稳定
    time.sleep(2)
    shot(page, OUT + r"\gg_4_ingame2.png")
    print("[4] HUD 稳定:", diff(OUT + r"\gg_3_ingame.png", OUT + r"\gg_4_ingame2.png"))

    # 5. 方向键滚球：右 -> 上 -> 左，每方向 3 帧
    seqs = []
    for key, tag in [("ArrowRight", "r"), ("ArrowUp", "u"), ("ArrowLeft", "l")]:
        page.keyboard.down(key)
        frames = []
        for i in range(5):
            time.sleep(0.55)
            fn = OUT + r"\gg_5_%s%d.png" % (tag, i)
            shot(page, fn)
            frames.append(fn)
        page.keyboard.up(key)
        dd = sum(diff(frames[i], frames[i+1]) for i in range(4))
        seqs.append((tag, round(dd, 3)))
        print(f"[5] {key} 长按 2.75s 帧间变化率合计={round(dd,3)}")
        time.sleep(0.8)

    # 6. 键盘映射验证
    pk = page.evaluate("""() => {
        try {
            var kb = Laya.__classmap['laya.events.KeyBoardManager'];
            return kb ? Object.keys(kb._pressKeys) : null;
        } catch(e){ return 'ERR ' + e; }
    }""")
    print("[6] _pressKeys:", pk)

    browser.close()

print()
print("=== 总结 ===")
print("进关:", "OK" if d3 > 0.05 else "FAIL", f"(变化率 {d3})")
print("方向键帧间变化率:", seqs)
