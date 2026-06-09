@echo off
echo ================================================
echo  RA Print Server - EXE Builder (HTML Mode)
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
    --collect-all weasyprint ^
    --collect-all fonttools ^
    --collect-all cssselect2 ^
    --collect-all tinycss2 ^
    --collect-all html5lib ^
    --collect-all Brotli ^
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
    --add-data "config.py;." ^
    --add-data "print.css;." ^
    main.py

echo.
echo ================================================
echo  Build complete: dist\ra_print_server.exe
echo.
echo  IMPORTANT: After copying to deployment folder,
echo  also copy these files alongside the EXE:
echo    - print.css       (receipt layout - edit this for changes)
echo    - SumatraPDF.exe  (silent PDF printer - download separately)
echo ================================================
pause
