@echo off
echo ================================================
echo  RA Print Server - Windows Autostart Installer
echo  Royal Alwaha Trading Co.
echo ================================================
echo.

REM Get the current directory (where the exe lives)
SET "EXE_PATH=%~dp0ra_print_server.exe"
SET "STARTUP_KEY=HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
SET "APP_NAME=RAPrintServer"

REM Check if exe exists
IF NOT EXIST "%EXE_PATH%" (
    echo ERROR: ra_print_server.exe not found in current directory.
    echo Please build it first using build_exe.bat
    pause
    exit /b 1
)

REM Add to Windows registry startup (current user, no admin needed)
REG ADD "%STARTUP_KEY%" /V "%APP_NAME%" /T REG_SZ /D "\"%EXE_PATH%\"" /F

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: ra_print_server.exe will now start automatically
    echo at Windows login for this user account.
    echo.
    echo Registry key added:
    echo   %STARTUP_KEY%\%APP_NAME%
    echo   Value: "%EXE_PATH%"
    echo.
    echo Starting the server now...
    start "" "%EXE_PATH%"
    echo Server started. Check ra_print_server.log for status.
) ELSE (
    echo ERROR: Failed to add registry key.
)
pause
