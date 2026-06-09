"""
RA Print Server — Configuration
Royal Alwaha Trading Co. | RISC Division

Edit these values to match your environment.
"""

# ── Network ───────────────────────────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 8080
ALLOWED_ORIGINS = ["*"]

# ── Printer ───────────────────────────────────────────────────────────────────
PRINTER_NAME = "[PRINTER_NAME]"   # ← Exact name from Windows Devices and Printers

# ── SumatraPDF ────────────────────────────────────────────────────────────────
# SumatraPDF is used for silent PDF printing.
# Download portable version from https://www.sumatrapdfreader.org/download-free-pdf-viewer
# Place SumatraPDF.exe in the same folder as ra_print_server.exe
SUMATRA_EXE = "SumatraPDF.exe"       # relative to EXE location; or full path
SUMATRA_TIMEOUT = 20                  # seconds to wait for print job to dispatch

# ── Receipt Layout ────────────────────────────────────────────────────────────
# print.css controls the receipt appearance on paper.
# Edit this file to adjust layout — no EXE rebuild needed.
PRINT_CSS_FILE = "print.css"          # relative to EXE location; or full path

RECEIPT_COPIES = 1                    # copies per print job

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE          = "ra_print_server.log"
LOG_MAX_BYTES     = 5 * 1024 * 1024
LOG_BACKUP_COUNT  = 3
