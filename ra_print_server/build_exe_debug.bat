@echo off
echo ================================================
echo  RA Print Server - DEBUG (console) Builder
echo  Royal Alwaha Trading Co.
echo ================================================
echo.
echo This builds a CONSOLE version (ra_print_server_debug.exe) so that
echo startup errors are printed to the screen. Use this only to diagnose
echo problems; deploy the normal ra_print_server.exe in production.
echo.

REM Install dependencies
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist ra_print_server_debug.spec del /q ra_print_server_debug.spec

echo.
echo Building DEBUG executable (console enabled)...

REM Note: NO --noconsole here, so the console window and tracebacks are visible.
pyinstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --console ^
    --name "ra_print_server_debug" ^
    --add-data "config.py;." ^
    --collect-all uvicorn ^
    --hidden-import win32print ^
    --hidden-import win32api ^
    --hidden-import win32con ^
    --hidden-import uvicorn.logging ^
    --hidden-import uvicorn.lifespan ^
    --hidden-import uvicorn.lifespan.on ^
    --hidden-import uvicorn.lifespan.off ^
    --hidden-import uvicorn.protocols ^
    --hidden-import uvicorn.protocols.http ^
    --hidden-import uvicorn.protocols.http.auto ^
    --hidden-import uvicorn.protocols.websockets ^
    --hidden-import uvicorn.protocols.websockets.auto ^
    --hidden-import uvicorn.loops ^
    --hidden-import uvicorn.loops.auto ^
    --hidden-import fastapi ^
    main.py

echo.
echo ================================================
echo  Debug build complete!
echo  Output: dist\ra_print_server_debug.exe
echo.
echo  Now run it from a terminal to see any error:
echo     dist\ra_print_server_debug.exe
echo  Leave the window open; if it crashes, copy the traceback.
echo ================================================
pause
