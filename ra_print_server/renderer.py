"""
ESC/P Receipt Renderer for Epson LQ-690 — Saudi ZATCA-compliant layout.

Converts JSON receipt payload → raw ESC/P byte sequence matching the
CustomOrderReceipt template (Tax Invoice / Simplified Tax Invoice / Return).

Layout sections (top to bottom):
  1. Invoice type title (+ Arabic)
  2. Header text / Company VAT
  3. Order info (ref, date, time, payment, cashier)
  4. Customer info (name, ref, street, VAT, email, phone)
  5. Line items table (5 columns: Name | Qty | UnitPrice | Tax | Total)
  6. Totals (subtotal-before-discount, discount, VAT, rounding, grand total)
  7. QR code (bitmap via ESC/P graphics)

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
    FORM_FEED_AFTER,
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

# Saudi VAT rate (used for fallback computations when before-tax fields missing)
VAT_RATE = 0.15
VAT_MULTIPLIER = 1 + VAT_RATE  # 1.15


# ── Helper Functions ───────────────────────────────────────────────────────────

def enc(text: str) -> bytes:
    """Encode a string to printer bytes, replacing unencodable chars."""
    return text.encode(TEXT_ENCODING, errors=ENCODING_ERRORS)


def pline(text: str = "") -> bytes:
    """Encode a text line followed by CRLF."""
    return enc(text) + CRLF


def blank(count: int = 1) -> bytes:
    """Emit `count` blank lines."""
    return CRLF * count


def center(text: str, width: int = PAPER_COLS) -> str:
    """Center text within the given width."""
    if len(text) >= width:
        return text
    pad = (width - len(text)) // 2
    return " " * pad + text


def right_pad(left: str, right: str, width: int = PAPER_COLS) -> str:
    """Left-align `left`, right-align `right`, fill space between."""
    gap = width - len(left) - len(right)
    if gap < 1:
        gap = 1
    return left + " " * gap + right


def to_float(value: Any, default: float = 0.0) -> float:
    """Coerce a value to float safely (handles strings, None, empty, garbage)."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt_money(amount: Any, decimals: int = 2) -> str:
    """Format a numeric value as money string (no currency symbol)."""
    return f"{to_float(amount):,.{decimals}f}"


def fmt_qty(qty: Any) -> str:
    """Format quantity (show integer if whole, else 2 decimals)."""
    v = to_float(qty)
    if v == int(v):
        return str(int(v))
    return f"{v:.2f}"


def parse_date_string(date_val) -> tuple:
    """
    Parse date value into (date_str, time_str).
    Handles: string "DD/MM/YYYY HH:MM:SS", Odoo date dict, ISO string.
    """
    if isinstance(date_val, str) and date_val.strip():
        parts = date_val.strip().split(" ", 1)
        date_str = parts[0] if parts else ""
        time_str = parts[1] if len(parts) > 1 else ""
        return date_str, time_str
    if isinstance(date_val, dict):
        y = date_val.get("year", "")
        mo = str(date_val.get("month", "")).zfill(2)
        d = str(date_val.get("date", date_val.get("day", ""))).zfill(2)
        h = str(date_val.get("hours", date_val.get("hour", "0"))).zfill(2)
        mi = str(date_val.get("minutes", date_val.get("minute", "0"))).zfill(2)
        return f"{d}/{mo}/{y}", f"{h}:{mi}"
    return datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")


# ── Main Renderer ─────────────────────────────────────────────────────────────

def render_receipt(data: Dict[str, Any]) -> bytes:
    """
    Build the complete ESC/P byte sequence for one ZATCA-compliant receipt.
    Returns raw bytes ready to be sent directly to the printer.
    """
    buf = bytearray()

    def w(b: bytes):
        buf.extend(b)

    # ── Initialize printer ─────────────────────────────────────────────────
    w(INIT)
    w(JUSTIFY_LEFT)
    w(blank(1))

    # ── Extract top-level data ─────────────────────────────────────────────
    totals = data.get("totals", {})
    total_amount = to_float(totals.get("total", 0))
    partner = data.get("partner") or {}
    company = data.get("company", {})
    header_data = data.get("header_data") or data.get("headerData") or {}
    header_text = header_data.get("header", "") if isinstance(header_data, dict) else ""
    if not header_text:
        header_text = data.get("header", "")
    fulfilled_by = ""
    if isinstance(header_data, dict):
        fulfilled_by = header_data.get("fulfilled_by_employee_name", "")

    # ── 1. Invoice Type Title (centered, bold, double-width) ────────────────
    customer_has_vat = bool(partner.get("vat"))

    w(JUSTIFY_CENTER)
    w(BOLD_ON + DBL_WIDTH_ON)

    if total_amount < 0:
        invoice_title = "Return Invoice"
        invoice_title_ar = "\u0641\u0627\u062a\u0648\u0631\u0629 \u0627\u0644\u0625\u0631\u062c\u0627\u0639"
    elif customer_has_vat:
        invoice_title = "Tax Invoice"
        invoice_title_ar = "\u0641\u0627\u062a\u0648\u0631\u0629 \u0636\u0631\u064a\u0628\u064a\u0629"
    else:
        invoice_title = "Simplified Tax Invoice"
        invoice_title_ar = "\u0641\u0627\u062a\u0648\u0631\u0629 \u0636\u0631\u064a\u0628\u064a\u0629 \u0645\u0628\u0633\u0637\u0629"

    # Double-width halves effective columns
    dbl_cols = PAPER_COLS // 2
    title_line = f"{invoice_title} - {invoice_title_ar}"
    if len(title_line) > dbl_cols:
        # Two lines if too long for double-width
        w(pline(invoice_title))
        w(pline(invoice_title_ar))
    else:
        w(pline(title_line))

    w(BOLD_OFF + DBL_WIDTH_OFF)

    # ── 2. Header Text ─────────────────────────────────────────────────────
    if header_text.strip():
        w(BOLD_ON)
        w(pline(header_text.strip()))
        w(BOLD_OFF)

    # ── 3. Company VAT ─────────────────────────────────────────────────────
    company_vat = company.get("vat", "")
    if company_vat:
        w(pline(f"VAT: {company_vat}"))

    w(JUSTIFY_LEFT)
    w(pline(DOUBLE_SEPARATOR))

    # ── 4. Order Info ──────────────────────────────────────────────────────
    order_ref = data.get("order_ref", "")
    date_val = data.get("date", "")
    date_str, time_str = parse_date_string(date_val)
    cashier = data.get("cashier", "")
    if not cashier and fulfilled_by:
        cashier = fulfilled_by

    payments = data.get("payments", [])
    payment_names = [p.get("name", "") for p in payments if p.get("name")]

    if order_ref:
        w(pline(right_pad(f"Order: {order_ref}", f"Date: {date_str}")))
    if time_str:
        w(pline(right_pad("", f"Time: {time_str}")))
    if payment_names:
        w(pline(f"Payment: {', '.join(payment_names)}"))
    if cashier:
        w(pline(f"Cashier: {cashier}"))

    w(pline(LINE_SEPARATOR))

    # ── 5. Customer Info ───────────────────────────────────────────────────
    # Matches the template's left "customer_column"
    partner_name = partner.get("name", "") if partner else ""
    if not partner_name:
        # Fallback to legacy field
        partner_name = data.get("customer", "")

    if not partner_name or partner_name == "Walk-in Customer":
        w(BOLD_ON)
        w(pline("Cash Customer"))
        w(BOLD_OFF)
    else:
        w(BOLD_ON)
        w(pline(partner_name))
        w(BOLD_OFF)
        if partner.get("ref"):
            w(pline(f"Ref: {partner['ref']}"))
        if partner.get("street"):
            w(pline(f"Street: {partner['street']}"))
        if partner.get("vat"):
            w(pline(f"VAT: {partner['vat']}"))
        if partner.get("email"):
            w(pline(f"Email: {partner['email']}"))
        phone_parts = []
        if partner.get("phone"):
            phone_parts.append(partner["phone"])
        if partner.get("mobile"):
            phone_parts.append(partner["mobile"])
        if phone_parts:
            w(pline(f"Phone: {' / '.join(phone_parts)}"))

    w(pline(LINE_SEPARATOR))

    # ── 6. Line Items Table (5 columns, condensed) ─────────────────────────
    # Columns: PRODUCT | QTY | UNIT PRICE | TAX | TOTAL
    # (unit price / tax / total are all BEFORE discount, excl. VAT per ZATCA)
    #
    # Column widths for condensed mode (~132 usable chars):
    NAME_W = 50
    QTY_W = 10
    PRICE_W = 18
    TAX_W = 18
    TOTAL_W = 18
    # Total = 114 (fits in condensed)

    w(CONDENSED_ON)
    w(BOLD_ON)
    col_header = (
        f"{'PRODUCT':<{NAME_W}}"
        f"{'QTY':>{QTY_W}}"
        f"{'UNIT PRICE':>{PRICE_W}}"
        f"{'TAX':>{TAX_W}}"
        f"{'TOTAL':>{TOTAL_W}}"
    )
    w(pline(col_header))
    w(BOLD_OFF)
    w(pline("-" * (NAME_W + QTY_W + PRICE_W + TAX_W + TOTAL_W)))

    for ln in data.get("lines", []):
        name = str(ln.get("name", ""))
        qty = to_float(ln.get("qty", 0))

        # Prefer the custom ZATCA fields from the template; fall back to
        # computing from standard fields + 15% VAT assumption.
        unit_price_bt = ln.get("unitPriceBeforeTax")
        tax_bd = ln.get("taxBeforeDiscount")
        total_bd = ln.get("priceWithoutTaxBeforeDiscount")

        if unit_price_bt is not None:
            unit_price_bt = to_float(unit_price_bt)
        else:
            # Fallback: derive from unit_price (which may be VAT-inclusive)
            raw_price = to_float(ln.get("unit_price", 0))
            unit_price_bt = raw_price / VAT_MULTIPLIER

        if total_bd is not None:
            total_bd = to_float(total_bd)
        else:
            total_bd = qty * unit_price_bt

        if tax_bd is not None:
            tax_bd = to_float(tax_bd)
        else:
            tax_bd = total_bd * VAT_RATE

        # Truncate long product names
        if len(name) > NAME_W:
            name = name[: NAME_W - 2] + ".."

        row = (
            f"{name:<{NAME_W}}"
            f"{fmt_qty(qty):>{QTY_W}}"
            f"{fmt_money(unit_price_bt):>{PRICE_W}}"
            f"{fmt_money(tax_bd):>{TAX_W}}"
            f"{fmt_money(total_bd):>{TOTAL_W}}"
        )
        w(pline(row))

    w(pline("-" * (NAME_W + QTY_W + PRICE_W + TAX_W + TOTAL_W)))
    w(CONDENSED_OFF)

    # ── 7. Totals (ZATCA layout) ──────────────────────────────────────────
    # Matches TotalOrderReceipt template:
    #   Row 1: total_without_tax + (total_discount / 1.15)  → Subtotal before disc.
    #   Row 2: total_discount / 1.15                        → Discount (excl. VAT)
    #   Row 3: amount_tax                                   → VAT (15%)
    #   Row 4: rounding_applied                             → Rounding
    #   Row 5: amount_total + rounding_applied              → Grand Total
    subtotal_excl = to_float(totals.get("subtotal", 0))  # total_without_tax
    discount_incl = to_float(totals.get("discount", 0))  # total_discount (VAT-inclusive)
    tax_amount = to_float(totals.get("tax", 0))          # amount_tax
    rounding = to_float(totals.get("rounding", 0))       # rounding_applied
    grand_total = to_float(totals.get("total", 0))       # amount_total

    # Template computation: discount excl. VAT = discount_incl / 1.15
    discount_excl = discount_incl / VAT_MULTIPLIER if discount_incl else 0.0
    # Template computation: subtotal before discount = subtotal + discount_excl
    subtotal_before_disc = subtotal_excl + discount_excl
    # Template computation: grand total displayed = grand_total + rounding
    grand_total_display = grand_total + rounding

    w(blank(1))

    def total_row(label: str, amount: float, bold: bool = False) -> bytes:
        val_str = fmt_money(amount)
        row_str = right_pad(label, val_str)
        if bold:
            return BOLD_ON + pline(row_str) + BOLD_OFF
        return pline(row_str)

    w(total_row("Subtotal (excl. VAT):", subtotal_before_disc))

    if discount_excl:
        w(total_row("Discount:", discount_excl))

    w(total_row("VAT (15%):", tax_amount))

    if rounding:
        w(total_row("Rounding:", rounding))

    w(pline(DOUBLE_SEPARATOR))

    # Last row: fulfilled_by employee on left, grand total on right
    total_label = "TOTAL:"
    if fulfilled_by:
        left_part = fulfilled_by
    else:
        left_part = ""
    w(BOLD_ON)
    w(pline(right_pad(left_part, f"{total_label} {fmt_money(grand_total_display)}")))
    w(BOLD_OFF)

    w(pline(DOUBLE_SEPARATOR))

    # ── 8. QR Code (bitmap) ────────────────────────────────────────────────
    qr_data = data.get("qr_code", "")
    if qr_data:
        try:
            from qr_render import render_qr_escp
            w(blank(1))
            w(JUSTIFY_CENTER)
            qr_bytes = render_qr_escp(qr_data, target_width_px=200)
            w(qr_bytes)
            w(JUSTIFY_LEFT)
            w(blank(1))
        except Exception:
            # If QR rendering fails (missing Pillow, corrupt image), skip
            w(JUSTIFY_CENTER)
            w(pline("[ QR Code — see electronic invoice ]"))
            w(JUSTIFY_LEFT)

    # ── 9. Paper Feed / Form Feed ──────────────────────────────────────────
    w(JUSTIFY_LEFT)
    for _ in range(FEED_LINES_AFTER):
        w(blank(1))

    if FORM_FEED_AFTER:
        w(FF)

    return bytes(buf)
