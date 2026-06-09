@echo off
echo ================================================
echo  RA Print Server - EXE Builder
echo  Royal Alwaha Trading Co.
echo ================================================
echo.

REM Install dependencies
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist ra_print_server.spec del /q ra_print_server.spec

echo.
echo Building executable...

pyinstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --noconsole ^
    --name "ra_print_server" ^
    --add-data "config.py;." ^
    --collect-all uvicorn ^
    --collect-all PIL ^
    --hidden-import qr_render ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
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
echo  Build complete!
echo  Output: dist\ra_print_server.exe
echo  Copy dist\ra_print_server.exe to your deployment folder.
echo ================================================
pause
