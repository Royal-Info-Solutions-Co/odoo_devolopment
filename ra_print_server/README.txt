RA PRINT SERVER (HTML Mode)
Royal Alwaha Trading Co. | RISC Division
==========================================

SETUP STEPS:
1. Edit config.py  →  set PRINTER_NAME exactly as shown in Windows Devices and Printers
2. Download SumatraPDF (portable EXE):
   https://www.sumatrapdfreader.org/download-free-pdf-viewer
   → Click "Portable version"
   → Place SumatraPDF.exe in your deployment folder (e.g. C:\PrintBridge\)
3. Run: build_exe.bat  →  creates dist\ra_print_server.exe
4. Copy to deployment folder:
     ra_print_server.exe   (the built EXE)
     SumatraPDF.exe        (portable, downloaded in step 2)
     print.css             (from ra_print_server\ source folder)
5. Run: install_autostart.bat  →  registers EXE to start at Windows login
6. Verify: open browser → http://localhost:8080/health

DEPLOYMENT FOLDER CONTENTS (C:\PrintBridge\):
    ra_print_server.exe   ← the server
    SumatraPDF.exe        ← PDF printer (never needs reinstalling)
    print.css             ← receipt layout ← EDIT THIS FOR CHANGES
    ra_print_server.log   ← auto-created

CHANGING THE RECEIPT LAYOUT:
    Edit print.css → save.
    No restart needed. No rebuild needed.
    The next print job picks up the changes automatically.

VERIFY INSTALLATION:
    http://localhost:8080/health    → server status + printer check
    http://localhost:8080/docs      → API docs (dev only)

FIREWALL RULE (run as Administrator):
    netsh advfirewall firewall add rule name="RA Print Server" ^
        dir=in action=allow protocol=TCP localport=8080

LOG FILE:
    ra_print_server.log  (same folder as EXE, auto-rotated at 5MB)

REMOVE AUTOSTART:
    REG DELETE "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /V "RAPrintServer" /F

==========================================
