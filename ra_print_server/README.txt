RA PRINT SERVER
Royal Alwaha Trading Co. | RISC Division
==========================================

SETUP STEPS:
1. Edit config.py → set PRINTER_NAME to exact Windows printer name
2. Run: build_exe.bat         → creates dist\ra_print_server.exe
3. Copy ra_print_server.exe to your deployment folder (e.g. C:\PrintBridge\)
4. Run: install_autostart.bat → registers EXE to run at Windows login
5. Verify: open browser → http://localhost:8080/health

VERIFY INSTALLATION:
  http://localhost:8080/health         → Server status + printer check
  http://localhost:8080/docs           → API documentation (dev only)

LOG FILE:
  ra_print_server.log (same folder as EXE)

TO REMOVE AUTOSTART:
  REG DELETE "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /V "RAPrintServer" /F

NETWORK REQUIREMENTS:
  - Windows Firewall must allow inbound TCP on port 8080
  - Android devices must be on the same LAN/Wi-Fi as this PC

FIREWALL RULE (run as Administrator if needed):
  netsh advfirewall firewall add rule name="RA Print Server" ^
    dir=in action=allow protocol=TCP localport=8080

==========================================
