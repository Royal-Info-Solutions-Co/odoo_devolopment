"""
RA Print Server — PDF Printer Dispatcher
Royal Alwaha Trading Co. | RISC Division

Writes PDF bytes to a temporary file then invokes SumatraPDF
for silent, zero-dialog printing to the configured Windows printer.

SumatraPDF command used:
    SumatraPDF.exe -print-to "<printer>" -print-settings "noscale" -silent <file>

Why SumatraPDF:
  - Portable EXE, no installation required
  - True silent print (no dialog, no UI flash)
  - Handles PDF → Windows GDI conversion reliably
  - -print-settings "noscale" prevents auto-scaling the receipt
"""

import os
import sys
import subprocess
import tempfile
from logger import get_logger
from config import PRINTER_NAME, SUMATRA_EXE, SUMATRA_TIMEOUT, RECEIPT_COPIES

log = get_logger("printer")


def _resolve_path(filename: str) -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    full = os.path.join(base, filename)
    return full if os.path.exists(full) else filename


def send_pdf(pdf_bytes: bytes, printer_name: str = PRINTER_NAME) -> None:
    """
    Write pdf_bytes to a temp file and print silently via SumatraPDF.

    Args:
        pdf_bytes:    Raw PDF bytes from html_renderer.render_to_pdf()
        printer_name: Windows printer name (from config.py)

    Raises:
        RuntimeError: if SumatraPDF is not found or print job fails.
    """
    sumatra = _resolve_path(SUMATRA_EXE)
    if not os.path.exists(sumatra):
        raise RuntimeError(
            f"SumatraPDF not found at '{sumatra}'. "
            "Download SumatraPDF.exe (portable) and place it next to ra_print_server.exe. "
            "Get it from: https://www.sumatrapdfreader.org/download-free-pdf-viewer"
        )

    # Write PDF to a named temp file (SumatraPDF needs a file path, not stdin)
    tmp = tempfile.NamedTemporaryFile(
        suffix=".pdf", delete=False, prefix="ra_receipt_"
    )
    try:
        tmp.write(pdf_bytes)
        tmp.close()

        for copy_num in range(RECEIPT_COPIES):
            cmd = [
                sumatra,
                "-print-to", printer_name,
                "-print-settings", "noscale",
                "-silent",
                tmp.name,
            ]

            log.info(f"Printing copy {copy_num + 1}/{RECEIPT_COPIES} to '{printer_name}'")

            result = subprocess.run(
                cmd,
                timeout=SUMATRA_TIMEOUT,
                capture_output=True,
            )

            if result.returncode != 0:
                stderr = result.stderr.decode(errors="replace").strip()
                raise RuntimeError(
                    f"SumatraPDF exited with code {result.returncode}: {stderr}"
                )

        log.info(
            f"Print job complete: {len(pdf_bytes)} bytes, "
            f"{RECEIPT_COPIES} copies to '{printer_name}'"
        )

    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass  # temp file cleanup failure is non-fatal


def list_printers() -> list:
    """Return list of installed Windows printers (for /health endpoint)."""
    try:
        import win32print
        return [p[2] for p in win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )]
    except Exception:
        return []
