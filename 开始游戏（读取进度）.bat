@echo off
chcp 936 >nul
setlocal

rem --- 定位游戏目录：bat 在游戏目录内就直接用，在外层则进 gqxqc ---
if exist "%~dp0index.html" (cd /d "%~dp0") else (cd /d "%~dp0gqxqc")

set "PY=D:\B++\Py313\python.exe"
if not exist "%PY%" set "PY=python"
set "PAGE=http://127.0.0.1:8123/"

rem --- 服务器已在运行就直接开页面，避免重复起进程 ---
curl -s -o nul --max-time 1 http://127.0.0.1:8123/ >nul 2>nul
if not errorlevel 1 goto open

echo ============================================
echo     滚球向前冲 - 网页版（读取进度）
echo ============================================
echo.
start "RollingBallServer" /min "%PY%" -m http.server 8123 --bind 127.0.0.1
echo 正在启动本地服务器（端口 8123）...

set /a N=0
:wait
curl -s -o nul --max-time 1 http://127.0.0.1:8123/ >nul 2>nul
if not errorlevel 1 goto open
set /a N+=1
if %N% geq 20 goto fail
ping -n 2 127.0.0.1 >nul
goto wait

:fail
echo.
echo ============================================
echo   服务器未能在二十秒内就绪
echo   请查看最小化的服务器窗口是否有报错
echo ============================================
echo.
pause
exit /b

:open
start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "--app=%PAGE%" --window-size=640,640
echo.
echo 游戏页面已弹出（按上次的进度继续）。
echo 服务器在最小化的命令行窗口中运行，玩完关掉那个窗口即可停止服务。
echo.
pause
