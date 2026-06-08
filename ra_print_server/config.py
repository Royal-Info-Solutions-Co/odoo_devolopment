"""
RA Print Server — Configuration
Royal Alwaha Trading Co. | RISC Division

Edit these values to match your environment.
"""

# ── Network ───────────────────────────────────────────────────────────────────
HOST = "0.0.0.0"           # Listen on all interfaces (LAN accessible)
PORT = 8080                # Must match BRIDGE_CONFIG.port in Odoo JS
ALLOWED_ORIGINS = ["*"]    # Allow all LAN origins (restrict to Odoo server IP if needed)

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

# ── Text Encoding ─────────────────────────────────────────────────────────────
# cp1256 = Windows Arabic (recommended for Saudi market)
# cp850  = Western European (if printer has no Arabic ROM)
TEXT_ENCODING = "cp1256"
ENCODING_ERRORS = "replace"        # Replace unencodable chars with '?'

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE = "ra_print_server.log"
LOG_MAX_BYTES = 5 * 1024 * 1024   # 5 MB
LOG_BACKUP_COUNT = 3
