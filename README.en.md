<a href="README.md">简体中文</a> ｜ <b>English</b>

# Gun Qiu Xiang Qian Chong · Windows Revival (Local Web Build)

A complete engineering record and working build that revives a Xiaomi Quick Game package — *Gun Qiu Xiang Qian Chong* (a 3D ball-rolling game on LayaAir 2.1.1.1, original package just 3.45 MB) — into a playable webpage inside a Windows browser.

> This repo ships two kinds of content:
> - **Game source files** (`游戏源文件/`): the raw unpacked content (main.js, res/, assets, and the original manifest.json) with **no** revival patches — exactly what you get by unzipping the `.apk` (which is really a renamed ZIP).
> - **Ready-to-play build** (`开箱即玩版/`): the game source files plus the browser bridge `index.html` and two launcher bats — double-click and play.

## What is this

`滚球向前冲.apk` is not an Android APK; it is a **LayaAir 2.1.1.1 Xiaomi Quick Game package** (a ZIP with a renamed extension). This project turns it back into a webpage playable in a PC browser.

- Engine: LayaAir 2.1.1.1 (3D render pipeline, WebGL)
- Design resolution: 720×1280 portrait
- Original package: 3.6 MB compressed / 11.5 MB extracted

## How to run (ready-to-play build)

Enter `开箱即玩版/`, then double-click one of the two launchers (both auto-start a local server and open the game page; the server runs in a minimized command window — just close it when done):

| Launcher | Purpose |
|---|---|
| `开始游戏（读取进度）.bat` | Normal launch, keeps the existing browser save (keys, skins, unlocked levels) |
| `开始游戏（重置进度）.bat` | Clears the save first, then launches — back to a fresh state (like first play) |

How "reset progress" works: the launcher opens the URL with `?reset=1`; `index.html` detects this **before** main.js and deletes `localStorage["userData"]` (the whole progress is one key), then uses `history.replaceState` to strip the param — so it only applies once; later refreshes or normal launches read the save as usual.

Or manually:

```
D:\B++\Py313\python.exe -m http.server 8123 --directory 开箱即玩版
```

Then open **http://127.0.0.1:8123** in the browser (must be HTTP, not file://; for reset add `?reset=1`).

- After editing `index.html`, **Ctrl+F5** to hard-refresh.
- On first entry the browser blocks autoplay audio — **click the canvas once** to get sound.
- Platform capabilities are handled via the browser path (`platform="web"`): rewarded-video buttons "callback success immediately", so "Challenge Now" / "Random Select" and other ad-gated buttons work directly without stalling.

## Controls

| Action | How |
|---|---|
| Enter level | Main menu "Level Mode" → "Start Game" → in the skin popup click any ball (Ball_01~09 all selectable directly), or click "Random Select" |
| Challenge mode | Main menu "Challenge Mode" → in the popup click "Challenge Now" to start directly (level 1000, with gesture guide); click "No Thanks" to close the popup |
| Roll the ball | Arrow keys ← ↑ → ↓ or **W A S D** (keyboard), or the on-screen virtual D-pad |
| Switch view left/right | **Q / E** keys, or the view button on the in-level HUD |
| Skip segment / camera / recenter | In-level HUD buttons |

All nine balls in the skin popup are directly clickable (no ad needed) — click a ball to equip that skin and enter level 1. "Random Select" picks and unlocks one from the locked skins; "No Thanks" starts the level with the current skin (original behavior).

Note: in the original, "No Thanks" is just a line of plain text at the **bottom of the popup** — no button chrome, no pressed-state feedback — so it looks like "nothing happened" when clicked. The real test is whether the popup closed and the level started.

## Buttons not responding? Press F9 for the diagnostics overlay

Press **F9** any time in the game page to toggle the top-left diagnostics overlay (or append `?debug=1` to the URL to start in diagnostics mode):

```
滚球向前冲 诊断 v2026-10-16.2
视口 1536x864 @1.25
桥接目标 yes(720x1280)
点击 3  最后 (768,673)
兜底 触发 0 次
不了谢谢 节点 1 个
皮肤弹窗在
F9 关闭
```

- **Each left mouse press leaves a red dot** (fades after 1.8s). Where the dot lands is where the game received the click.
- Line 3 "桥接目标" must be `yes(...)`; if `NO`, the input bridge didn't find the canvas — **all clicks are silently dropped** (the classic "screen fine but buttons dead" symptom).
- "不了谢谢 节点" = how many "No Thanks" images exist on the current page (one each in the skin popup / unlock-challenge popup). `0` means no such popup is open.
- "兜底 触发" = how many times layer ④ (click fallback) rescued a click. `>0` means the engine itself failed to dispatch to "No Thanks" and the fallback patched it — on normal hits it should stay 0.
- The last line is the live panel state: `皮肤弹窗在` = popup still open; `【已进关】` = already entered the level.

Reading "clicked No Thanks but nothing happened":

| Symptom | Meaning | What to do |
|---|---|---|
| No red dot, "点击" counter not increasing | Page received no mouse event at all | First **Ctrl+F5**; try another mouse, click page for focus, disable browser extensions |
| Red dot on "No Thanks", last line still "皮肤弹窗在" | Event arrived, position right, but button logic didn't run | Screenshot this screen and report |
| Red dot appears but offset, misses the text | Coordinate mapping off (page zoom / multi-monitor) | Screenshot this screen and report |
| Last line becomes "【已进关】" | Actually succeeded, already in level 1 | No action needed |

The console also prints an entry version (`[滚球向前冲] 本地 Web 入口版本 v...`) — confirm it matches your build to rule out a cached old page.

## Functional improvements (v2026-10-16, all verified)

1. **Platform detection fix (root cause)**: SDK init hardcoded `platform` to `"xiaomi"`, so every `VideoAD()` called the Xiaomi ad SDK — which doesn't exist in a browser, so the callback never fired and buttons looked dead. Changed to `"web"`, taking the browser branch the author already wrote (rewarded video callbacks success immediately). This single step revived "Challenge Now" / "Random Select" and all ad buttons (revive, challenge double reward); it also reopened the whole **ad-unlock keys / skins / challenge mode** chain.
2. **"Watch ad for 2 keys" button**: changed to grant +2 keys and save on click (`FreeKeyUI`'s `Btn_AD`).
3. **All nine skins directly selectable**: `SelectSkinPanel` loop originally required a rewarded video for locked skins; changed to `SelectPiFu` directly for all (`main.js`).
4. **Keyboard rolling**: `GameUI.onEnable` registers keyboard listeners; arrow keys + WASD map to `Move/StopMove` (`main.js`).
5. **Q/E view switch**: `PlayerControl.ChangeShiJiaoEx(0/1)` turns the camera 90° left/right (`main.js`).
6. **Camera shake fix**: `CameraMove`'s easing logic, once the angle arrived, jumped every frame between "arrived" and "-0.1 rad", so the view kept shaking. Changed to clamped two-way easing with `Math.min/Math.max` that strictly locks after arrival (measured static camera rotation holds constant at 0.000°).

## What index.html does (four fixes + one diagnostic)

1. **qg runtime shim** (before main.js): HTTP-based `readFile`/`downloadFile` so the mini-game filesystem loads local `res/` via XHR; deliberately does NOT define `getApp`/`GameGlobal` (otherwise KGMiniAdapter reactivates and switches to the mini filesystem → zero resource requests → black screen).
2. **Pure-CSS canvas fit**: the mini-game build sets no CSS size on the canvas (only the backing buffer = logical size × dpr), so a 1:1 browser display gets clipped; and main.js wraps the whole DOM, so page JS setting styles never reaches the real elements — only CSS can center the real render canvas proportionally and push `#layaCanvas` and the font bitmap canvas off-screen.
3. **Input bridge** (after main.js): this package replaces the DOM with a "mini DOM", with mouse/touch listeners on a fake canvas object that no browser feeds events to → listen on the real window (capture phase), translate into plain objects and dispatch to the mini canvas; map back to logical coords via actual CSS size and dpr.
4. **Click fallback / dead-zone fix**: Laya writes the canvas scale into the stage's own `_transform` (at 1366×768 `clientScale=0.6`, `_transform.a=0.6`). Hit-test `fromParentPoint` calls `invertTransformPoint` first, scaling the click coords by `1/clientScale`, pushing a click outside the stage rect; and `Scene` nodes carry `hitTestPrior=true`, so `check()` drops the whole subtree if the node's own rect fails — when the window ratio isn't 720:1280, the lower half of the screen is dropped entirely (dead-zone edge = design height × clientScale: at 1366×768 design `y≥800` all lost, at 1920×1080 `y≥1100` lost, at 720×1280 full screen normal). Fix: before the input-bridge dispatch, pull coords back by clientScale (`x = m.tx + csx*(x - m.tx)`), plus a layer that recomputes the rect and re-dispatches CLICK without relying on display-list hit-testing, without double-triggering normal hits. This also makes "ad-unlock" / "No Thanks" and other lower-half buttons clickable.
5. **F9 diagnostics overlay**: see above.

## Directory layout

```
.
├── 游戏源文件/               # Raw unpacked: main.js, res/, Font/, manifest.json, etc. (no patches)
├── 开箱即玩版/               # Game source + index.html + two launcher bats + 现场取证-不了谢谢.js
├── verify_gqxqc.py           # Verify: launch → enter level, full chain
├── play_final2.py            # Verify: full level run
├── diag_bridge.py            # Diagnose: did the input bridge find the canvas
├── diag_matrix.py            # Diagnose: clientScale matrix
├── test_matrix.py            # Unit: coordinate matrix mapping
├── test_debug.py             # Unit: debug-mode toggle
├── *.png                     # Verification screenshots (gg_*/gq_*/dbg_*)
├── README.md                 # This file's Chinese counterpart
└── README.en.md              # English
```

## Verification

The 6 `*.py` scripts at the repo root are the verification harness: start `开箱即玩版/` with `python -m http.server`, then run `verify_gqxqc.py` (enter level) and `play_final2.py` (full level). Screenshots `gg_*` are per-level evidence, `gq_*` are post-v2-fix evidence, `dbg_*` are diagnostics-overlay evidence.

## Version

- Local Web entry: `v2026-10-16.2` (diagnostics) / `v2026-10-16.3` (post dead-zone fix game version)
- Engine: LayaAir 2.1.1.1

---

> Author: Space-Bunny, an AI worker running inside WorkBuddy, accompanying the user to dig up old games
