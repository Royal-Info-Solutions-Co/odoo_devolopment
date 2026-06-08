"""
ESC/P Receipt Renderer for Epson LQ-690
Converts JSON receipt payload → raw ESC/P byte sequence

ESC/P Reference:
  ESC @       : Initialize printer
  ESC E       : Bold on
  ESC F       : Bold off
  SI (0x0F)   : Condensed on  (17.14 CPI → ~137 chars on 8-inch)
  DC2 (0x12)  : Condensed off (back to 10 CPI → 80 chars)
  ESC W 1     : Double-width on
  ESC W 0     : Double-width off
  ESC a 0/1/2 : Left / Center / Right justify (ESC/P2, supported on LQ-690)
  LF          : Line feed
  CR          : Carriage return
  FF          : Form feed (page advance)
"""

from datetime import datetime
from typing import Dict, Any
from config import (
    PAPER_COLS, LINE_SEPARATOR, DOUBLE_SEPARATOR,
    FEED_LINES_AFTER, TEXT_ENCODING, ENCODING_ERRORS,
    COMPANY_NAME_OVERRIDE, FORM_FEED_AFTER,
)

# ── ESC/P Command Constants ────────────────────────────────────────────────────
ESC = b"\x1b"
INIT          = ESC + b"@"
BOLD_ON       = ESC + b"E"
BOLD_OFF      = ESC + b"F"
CONDENSED_ON  = b"\x0f"           # SI
CONDENSED_OFF = b"\x12"           # DC2
DBL_WIDTH_ON  = ESC + b"W\x01"
DBL_WIDTH_OFF = ESC + b"W\x00"
JUSTIFY_LEFT   = ESC + b"a\x00"
JUSTIFY_CENTER = ESC + b"a\x01"
JUSTIFY_RIGHT  = ESC + b"a\x02"
LF  = b"\x0a"
CR  = b"\x0d"
FF  = b"\x0c"
CRLF = CR + LF


def enc(text: str) -> bytes:
    """Encode a string to printer bytes, replacing unencodable chars."""
    return text.encode(TEXT_ENCODING, errors=ENCODING_ERRORS)


def line(text: str = "") -> bytes:
    """Encode a text line followed by CRLF."""
    return enc(text) + CRLF


def blank(count: int = 1) -> bytes:
    """Emit `count` blank lines."""
    return CRLF * count


def center(text: str, width: int = PAPER_COLS) -> str:
    """Center text within the paper width (manual, for reliability)."""
    if len(text) >= width:
        return text
    pad = (width - len(text)) // 2
    return " " * pad + text


def right_pad(left: str, right: str, width: int = PAPER_COLS) -> str:
    """Place `right` at the far right, `left` at the far left, space between."""
    gap = width - len(left) - len(right)
    if gap < 1:
        gap = 1
    return left + " " * gap + right


def two_col(left: str, right: str, width: int = PAPER_COLS) -> str:
    return right_pad(left, right, width)


def to_float(value: Any, default: float = 0.0) -> float:
    """Coerce a value to float. The Odoo POS payload often sends numbers as
    strings (e.g. "2.0"), so accept those and fall back to `default` on
    anything non-numeric (None, "", text)."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt_amount(amount: Any, decimals: int = 2) -> str:
    return f"{to_float(amount):,.{decimals}f}"


def fmt_date(date_dict: dict) -> str:
    """Convert Odoo date dict to readable string."""
    try:
        if isinstance(date_dict, str):
            return date_dict
        y = date_dict.get("year", "")
        mo = str(date_dict.get("month", "")).zfill(2)
        d = str(date_dict.get("date", "")).zfill(2)
        h = str(date_dict.get("hours", "")).zfill(2)
        mi = str(date_dict.get("minutes", "")).zfill(2)
        return f"{d}/{mo}/{y}  {h}:{mi}"
    except Exception:
        return datetime.now().strftime("%d/%m/%Y  %H:%M")


# ── Main Renderer ─────────────────────────────────────────────────────────────

def render_receipt(data: Dict[str, Any]) -> bytes:
    """
    Build the complete ESC/P byte sequence for one receipt.
    Returns raw bytes ready to be sent directly to the printer.
    """
    buf = bytearray()

    def w(b: bytes):
        buf.extend(b)

    # ── Initialize ────────────────────────────────────────────────────────────
    w(INIT)
    w(JUSTIFY_LEFT)
    w(blank(1))

    # ── Company Header ────────────────────────────────────────────────────────
    company = data.get("company", {})
    company_name = COMPANY_NAME_OVERRIDE or company.get("name", "")

    if company_name:
        w(JUSTIFY_CENTER)
        w(BOLD_ON + DBL_WIDTH_ON)
        w(line(company_name[:40]))   # Double-width: max ~40 chars on 80-col
        w(BOLD_OFF + DBL_WIDTH_OFF)

    if company.get("address"):
        addr = company["address"].replace("\n", " ").strip()
        w(line(center(addr)))

    if company.get("phone"):
        w(line(center(f"Tel: {company['phone']}")))

    if company.get("vat"):
        w(line(center(f"VAT: {company['vat']}")))

    if company.get("email"):
        w(line(center(company["email"])))

    # ── Custom Header ─────────────────────────────────────────────────────────
    header_text = data.get("header", "").strip()
    if header_text:
        for hline in header_text.split("\n"):
            w(line(center(hline.strip())))

    w(JUSTIFY_LEFT)
    w(line(DOUBLE_SEPARATOR))

    # ── Order Info ────────────────────────────────────────────────────────────
    order_ref  = data.get("order_ref", "")
    order_date = fmt_date(data.get("date", {}))
    cashier    = data.get("cashier", "")
    customer   = data.get("customer", "Walk-in Customer")

    if order_ref:
        w(line(two_col(f"Order: {order_ref}", order_date)))
    if cashier:
        w(line(two_col(f"Cashier: {cashier}", f"Customer: {customer}")))
    elif customer and customer != "Walk-in Customer":
        w(line(f"Customer: {customer}"))

    w(line(LINE_SEPARATOR))

    # ── Column Header Row ─────────────────────────────────────────────────────
    # Layout: DESCRIPTION(40) QTY(6) PRICE(10) DISC(6) TOTAL(12) + 6 gap = 80
    w(BOLD_ON + CONDENSED_ON)
    col_header = (
        f"{'DESCRIPTION':<40}"
        f"{'QTY':>6}"
        f"{'PRICE':>10}"
        f"{'DISC%':>6}"
        f"{'TOTAL':>12}"
    )
    w(line(col_header[:PAPER_COLS]))
    w(BOLD_OFF)
    w(line(LINE_SEPARATOR))
    w(CONDENSED_OFF)

    # ── Order Lines ───────────────────────────────────────────────────────────
    w(CONDENSED_ON)
    for ln in data.get("lines", []):
        name = str(ln.get("name", ""))
        qty  = to_float(ln.get("qty", 0))
        unit_price = to_float(ln.get("unit_price", 0))
        discount   = to_float(ln.get("discount", 0))
        total      = to_float(ln.get("price_with_tax", 0))

        # Truncate product name to 40 chars
        if len(name) > 40:
            name = name[:38] + ".."

        row = (
            f"{name:<40}"
            f"{qty:>6.2f}"
            f"{unit_price:>10.2f}"
            f"{(str(int(discount)) + '%'):>6}"
            f"{total:>12.2f}"
        )
        w(line(row[:PAPER_COLS]))

        # Customer note (if any)
        note = str(ln.get("note", "")).strip()
        if note:
            w(CONDENSED_ON)
            w(line(f"  ↳ {note[:75]}"))

    w(CONDENSED_OFF)
    w(line(LINE_SEPARATOR))

    # ── Totals ────────────────────────────────────────────────────────────────
    totals = data.get("totals", {})
    subtotal = to_float(totals.get("subtotal", 0))
    tax      = to_float(totals.get("tax", 0))
    total    = to_float(totals.get("total", 0))
    paid     = to_float(totals.get("paid", 0))
    change   = to_float(totals.get("change", 0))
    discount = to_float(totals.get("discount", 0))

    label_col = 60  # Where labels end

    def total_row(label: str, amount: float, bold: bool = False) -> bytes:
        row_str = right_pad(label, fmt_amount(amount))
        if bold:
            return BOLD_ON + line(row_str) + BOLD_OFF
        return line(row_str)

    if discount > 0:
        w(total_row("Discount:", -abs(discount)))
    w(total_row("Subtotal:", subtotal))

    # Itemized tax details (if available)
    tax_details = data.get("tax_details", [])
    if tax_details:
        for td in tax_details:
            label = f"  {td.get('name', 'Tax')} ({fmt_amount(td.get('base', 0))}):"
            w(total_row(label, td.get("amount", 0)))
    else:
        w(total_row("Tax:", tax))

    w(line(DOUBLE_SEPARATOR))
    w(total_row("TOTAL:", total, bold=True))
    w(line(DOUBLE_SEPARATOR))

    # ── Payments ──────────────────────────────────────────────────────────────
    w(blank(1))
    w(JUSTIFY_CENTER)
    w(BOLD_ON)
    w(line(center("— PAYMENT —")))
    w(BOLD_OFF)
    w(JUSTIFY_LEFT)
    w(line(LINE_SEPARATOR))

    for pay in data.get("payments", []):
        pay_name   = pay.get("name", "")
        pay_amount = pay.get("amount", 0)
        w(total_row(pay_name + ":", pay_amount))

    if change > 0:
        w(total_row("Change:", change))

    w(line(LINE_SEPARATOR))

    # ── Footer ────────────────────────────────────────────────────────────────
    w(blank(1))
    w(JUSTIFY_CENTER)

    footer_text = data.get("footer", "").strip()
    if footer_text:
        for fline in footer_text.split("\n"):
            w(line(center(fline.strip())))
    else:
        w(line(center("Thank you for your business!")))

    w(line(center(f"Printed: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")))
    w(line(DOUBLE_SEPARATOR))

    # ── Paper Feed ────────────────────────────────────────────────────────────
    w(JUSTIFY_LEFT)
    for _ in range(FEED_LINES_AFTER):
        w(blank(1))

    # Page printers (laser/inkjet) only eject a page on a form feed; the Epson
    # LQ-690 (continuous feed) does not need one. Controlled by FORM_FEED_AFTER.
    if FORM_FEED_AFTER:
        w(FF)

    return bytes(buf)
