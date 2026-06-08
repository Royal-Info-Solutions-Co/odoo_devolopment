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
echo Building executable...

pyinstaller ^
    --onefile ^
    --noconsole ^
    --name "ra_print_server" ^
    --add-data "config.py;." ^
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
