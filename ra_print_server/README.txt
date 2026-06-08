RA PRINT SERVER
Royal Alwaha Trading Co. | RISC Division
==========================================

SETUP STEPS:
1. Edit config.py → set PRINTER_NAME to exact Windows printer name
   (For a laser/inkjet test printer, also set FORM_FEED_AFTER = True so the
    page is ejected. Keep it False for the Epson LQ-690 continuous feed.)
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

HTTPS / TLS (REQUIRED FOR THE ODOO ANDROID APP)
==========================================
The Odoo Android app runs the POS inside a WebView. When Odoo is served over
https, that WebView BLOCKS the bridge's insecure http call to this server
(mixed content) — the request never arrives, so nothing prints and nothing
shows in the log. Serving this print server over https fixes it (https->https).
(A normal desktop browser on http does not have this problem.)

IMPORTANT: the certificate must be trusted by Android's SYSTEM trust store.
Self-signed / user-installed certs do NOT work inside the app's WebView. Use a
real CA such as Let's Encrypt, issued for a HOSTNAME (not a bare IP).

STEP 1 — Pick a hostname for this PC, e.g.:
  printbridge.royalalwaha.com

STEP 2 — Make that hostname resolve to this PC's LAN IP on the POS network:
  - a public DNS A record pointing to the LAN IP, OR
  - your router's / internal DNS (split-horizon), OR
  - per-device hosts entry (not possible on stock Android — prefer DNS).

STEP 3 — Get a trusted cert for that hostname (no inbound ports needed):
  Use Let's Encrypt DNS-01, e.g. with certbot or win-acme. You will get:
    fullchain.pem   (certificate + intermediate chain)
    privkey.pem     (private key)
  Note: Let's Encrypt files are usually named fullchain.pem / privkey.pem.
  If your tool outputs .crt/.key or .pfx, convert to PEM.

STEP 4 — Put the two PEM files next to ra_print_server.exe (or anywhere) and
set in config.py:
    USE_HTTPS    = True
    SSL_CERTFILE = "C:\\PrintBridge\\fullchain.pem"   # absolute path recommended
    SSL_KEYFILE  = "C:\\PrintBridge\\privkey.pem"
  (Absolute paths are safest — when launched at login the working directory
   may not be the exe folder.)

STEP 5 — Rebuild (build_exe.bat) and restart. Verify from the PC:
    https://printbridge.royalalwaha.com:8080/health   (should load, valid lock)

STEP 6 — In the Odoo module ra_pos_print_bridge (bridge_config.js):
    use_https: true
    ip:        "printbridge.royalalwaha.com"   # hostname must match the cert
    port:      8080

CERT RENEWAL: Let's Encrypt certs expire every 90 days. Re-copy the renewed
fullchain.pem / privkey.pem and restart the server.

==========================================
