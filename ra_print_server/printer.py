"""
Windows Printer Dispatcher
Sends raw ESC/P bytes directly to the named Windows printer,
bypassing the Windows print spooler's GDI rendering.

Uses win32print with RAW data type for true dot-matrix output.
"""

import win32print
from logger import get_logger
from config import PRINTER_NAME

log = get_logger("printer")


def list_printers() -> list:
    """Return list of all installed Windows printers."""
    return [p[2] for p in win32print.EnumPrinters(
        win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    )]


def send_raw(data: bytes, printer_name: str = PRINTER_NAME) -> None:
    """
    Send raw bytes to the specified Windows printer.

    Uses DOC_INFO_1 with "RAW" datatype to bypass Windows GDI and
    send ESC/P commands directly to the printer driver.

    Args:
        data:         Raw ESC/P byte sequence from renderer.
        printer_name: Windows printer name (from config.py).

    Raises:
        RuntimeError: If printer cannot be opened or job fails.
    """
    available = list_printers()
    if printer_name not in available:
        raise RuntimeError(
            f"Printer '{printer_name}' not found. "
            f"Available printers: {available}"
        )

    handle = win32print.OpenPrinter(printer_name)
    try:
        job = win32print.StartDocPrinter(
            handle,
            1,
            ("RA POS Receipt", None, "RAW")
        )
        try:
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, data)
            win32print.EndPagePrinter(handle)
        finally:
            win32print.EndDocPrinter(handle)
    finally:
        win32print.ClosePrinter(handle)

    log.info(f"Sent {len(data)} bytes to '{printer_name}'")
