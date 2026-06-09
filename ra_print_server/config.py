"""
RA Print Server — Configuration
Royal Alwaha Trading Co. | RISC Division

Edit these values to match your environment.
"""

# ── Network ───────────────────────────────────────────────────────────────────
HOST = "0.0.0.0"           # Listen on all interfaces (LAN accessible)
PORT = 8080                # Must match BRIDGE_CONFIG.port in Odoo JS
ALLOWED_ORIGINS = ["*"]    # Allow all LAN origins (restrict to Odoo server IP if needed)

# ── HTTPS / TLS ───────────────────────────────────────────────────────────────
# Required when the POS runs inside the Odoo Android app: its WebView blocks the
# bridge's insecure http call made from the https POS page (mixed content). Serve
# this print server over https so the call becomes https -> https.
#
# The certificate MUST be issued by a CA that Android trusts (e.g. Let's Encrypt)
# for the HOSTNAME the bridge connects to (BRIDGE_CONFIG.ip in the Odoo module).
# Self-signed certs do NOT work inside the app's WebView. That hostname must
# resolve to this PC on the LAN (public A record to the LAN IP, or local DNS).
USE_HTTPS = False                 # Set True to serve over https (needs cert below)
SSL_CERTFILE = "fullchain.pem"    # PEM: server cert + intermediate chain
SSL_KEYFILE = "privkey.pem"       # PEM: matching private key

# ── Printer ───────────────────────────────────────────────────────────────────
PRINTER_NAME = "[PRINTER_NAME]"   # ← Exact name from Windows "Devices and Printers"
                                  # Example: "EPSON LQ-690"

# ── Paper Layout ─────────────────────────────────────────────────────────────
PAPER_COLS = 80            # Characters per line (80 @ 10 CPI on 8-inch paper)
LINE_SEPARATOR = "-" * 80  # Standard divider line
DOUBLE_SEPARATOR = "=" * 80

# ── Receipt Content ───────────────────────────────────────────────────────────
COMPANY_NAME_OVERRIDE = ""         # Leave empty to use name from payload
RECEIPT_COPIES = 1                 # Number of copies to print per job
FEED_LINES_AFTER = 4               # Blank lines to advance paper after receipt
CUT_AFTER_PRINT = False            # LQ-690 is continuous feed; set False
FORM_FEED_AFTER = False            # Append a Form Feed (0x0C) at the end of the job.
                                  # Keep False for the Epson LQ-690 (continuous feed).
                                  # Set True for page printers (laser/inkjet) that
                                  # only eject a page on a form feed.

# ── Text Encoding ─────────────────────────────────────────────────────────────
# cp1256 = Windows Arabic (recommended for Saudi market)
# cp850  = Western European (if printer has no Arabic ROM)
TEXT_ENCODING = "cp1256"
ENCODING_ERRORS = "replace"        # Replace unencodable chars with '?'

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE = "ra_print_server.log"
LOG_MAX_BYTES = 5 * 1024 * 1024   # 5 MB
LOG_BACKUP_COUNT = 3
