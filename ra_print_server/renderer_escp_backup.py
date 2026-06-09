"""
ESC/P Receipt Renderer for Epson LQ-690
Royal Alwaha Trading Co. | RISC Division

Updated for tis_pos_receipt_a4_formate field schema (v1.1):
  - invoice_type: "tax" | "simplified" | "return"
  - date: string "DD/MM/YYYY HH:MM:SS"
  - totals.discount_ex_tax: pre-tax discount (already divided by 1.15 in JS)
  - totals.grand_total: amount_total + rounding_applied
  - employee: fulfilled_by_employee_name
  - customer: object with name/ref/street/vat/email/phone

ESC/P Command Reference:
  ESC @       Initialize printer
  ESC E       Bold on
  ESC F       Bold off
  SI (0x0F)   Condensed on  (~17 CPI → fits more chars per line)
  DC2 (0x12)  Condensed off (back to 10 CPI → 80 cols standard)
  ESC W 1/0   Double-width on/off
  ESC a 0/1/2 Left/Center/Right justify (ESC/P2, supported on LQ-690)
  CR+LF       Line end
"""

from datetime import datetime
from typing import Dict, Any, Optional
from config import (
    PAPER_COLS, LINE_SEPARATOR, DOUBLE_SEPARATOR,
    FEED_LINES_AFTER, TEXT_ENCODING, ENCODING_ERRORS,
    COMPANY_NAME_OVERRIDE,
)

# ── ESC/P Commands ────────────────────────────────────────────────────────────
ESC           = b"\x1b"
INIT          = ESC + b"@"
BOLD_ON       = ESC + b"E"
BOLD_OFF      = ESC + b"F"
CONDENSED_ON  = b"\x0f"
CONDENSED_OFF = b"\x12"
DBL_WIDTH_ON  = ESC + b"W\x01"
DBL_WIDTH_OFF = ESC + b"W\x00"
JUSTIFY_LEFT  = ESC + b"a\x00"
JUSTIFY_CENTER = ESC + b"a\x01"
JUSTIFY_RIGHT  = ESC + b"a\x02"
LF   = b"\x0a"
CR   = b"\x0d"
CRLF = CR + LF

# ── ZATCA invoice type labels ─────────────────────────────────────────────────
INVOICE_TYPE_LABELS = {
    "tax":        "Tax Invoice",
    "simplified": "Simplified Tax Invoice",
    "return":     "Return Invoice",
}
INVOICE_TYPE_ARABIC = {
    "tax":        "  \u0641\u0627\u062a\u0648\u0631\u0629 \u0636\u0631\u064a\u0628\u064a\u0629",
    "simplified": "  \u0641\u0627\u062a\u0648\u0631\u0629 \u0636\u0631\u064a\u0628\u064a\u0629 \u0645\u0628\u0633\u0637\u0629",
    "return":     "  \u0641\u0627\u062a\u0648\u0631\u0629 \u0627\u0644\u0625\u0631\u062c\u0627\u0639",
}


# ── Text Helpers ──────────────────────────────────────────────────────────────

def enc(text: str) -> bytes:
    return str(text).encode(TEXT_ENCODING, errors=ENCODING_ERRORS)

def line(text: str = "") -> bytes:
    return enc(text) + CRLF

def blank(count: int = 1) -> bytes:
    return CRLF * count

def center(text: str, width: int = PAPER_COLS) -> str:
    if len(text) >= width:
        return text
    pad = (width - len(text)) // 2
    return " " * pad + text

def right_pad(left: str, right: str, width: int = PAPER_COLS) -> str:
    gap = width - len(left) - len(right)
    return left + " " * max(1, gap) + right

def fmt(amount: float, decimals: int = 2) -> str:
    return f"{float(amount):,.{decimals}f}"

def total_row(label: str, amount: float, bold: bool = False,
              width: int = PAPER_COLS) -> bytes:
    row_str = right_pad(label, fmt(amount), width)
    if bold:
        return BOLD_ON + line(row_str) + BOLD_OFF
    return line(row_str)

def parse_date(date_val) -> str:
    """
    Handle date as string "DD/MM/YYYY HH:MM:SS" (tis_pos_receipt_a4_formate format)
    or as a dict (standard Odoo format) or ISO string.
    Returns a printable string.
    """
    if not date_val:
        return datetime.now().strftime("%d/%m/%Y  %H:%M")
    if isinstance(date_val, str):
        # Already formatted — just return as-is or normalise spacing
        return date_val.replace("T", "  ").strip()
    if isinstance(date_val, dict):
        try:
            y  = date_val.get("year", "")
            mo = str(date_val.get("month", "")).zfill(2)
            d  = str(date_val.get("date", "")).zfill(2)
            h  = str(date_val.get("hours", "")).zfill(2)
            mi = str(date_val.get("minutes", "")).zfill(2)
            return f"{d}/{mo}/{y}  {h}:{mi}"
        except Exception:
            pass
    return datetime.now().strftime("%d/%m/%Y  %H:%M")


# ── Main Renderer ─────────────────────────────────────────────────────────────

def render_receipt(data: Dict[str, Any]) -> bytes:
    """
    Build the complete ESC/P byte sequence for one receipt.
    Returns raw bytes ready for win32print RAW dispatch.
    """
    buf = bytearray()

    def w(b: bytes):
        buf.extend(b)

    totals   = data.get("totals", {})
    company  = data.get("company", {})
    customer = data.get("customer")     # object or None (cash customer)
    lines_   = data.get("lines", [])
    payments = data.get("payments", [])

    invoice_type = data.get("invoice_type", "simplified")
    date_str     = parse_date(data.get("date", ""))

    # ── Initialize ────────────────────────────────────────────────────────────
    w(INIT)
    w(JUSTIFY_LEFT)
    w(blank(1))

    # ── Company Header ────────────────────────────────────────────────────────
    company_name = COMPANY_NAME_OVERRIDE or company.get("name", "")
    if company_name:
        w(JUSTIFY_CENTER)
        w(BOLD_ON + DBL_WIDTH_ON)
        w(line(company_name[:38]))
        w(BOLD_OFF + DBL_WIDTH_OFF)

    for field in ("address", "phone", "vat", "email"):
        val = company.get(field, "").strip()
        if val:
            prefix = {"phone": "Tel: ", "vat": "VAT: ", "email": ""}.get(field, "")
            # Address may have embedded newlines
            for part in val.replace("\n", " | ").split(" | "):
                part = part.strip()
                if part:
                    w(line(center(f"{prefix}{part}")))

    # ── Receipt header text (from POS config) ─────────────────────────────────
    header_text = data.get("header", "").strip()
    if header_text:
        for hline in header_text.splitlines():
            if hline.strip():
                w(line(center(hline.strip())))

    w(JUSTIFY_LEFT)
    w(line(DOUBLE_SEPARATOR))

    # ── ZATCA Invoice Type ────────────────────────────────────────────────────
    label_en = INVOICE_TYPE_LABELS.get(invoice_type, "Simplified Tax Invoice")
    label_ar = INVOICE_TYPE_ARABIC.get(invoice_type, "")
    w(JUSTIFY_CENTER)
    w(BOLD_ON)
    # Print English label; Arabic appended if encoding supports it
    combined_label = f"{label_en}{label_ar}"
    w(line(center(combined_label)))
    w(BOLD_OFF)
    w(JUSTIFY_LEFT)
    w(line(LINE_SEPARATOR))

    # ── Order Identity ────────────────────────────────────────────────────────
    order_ref = data.get("order_ref", "")
    cashier   = data.get("cashier", "")
    employee  = data.get("employee", "")

    if order_ref:
        # Date is "DD/MM/YYYY HH:MM:SS" — split on space for two-column layout
        date_parts = date_str.split(" ")
        date_col = date_parts[0] if date_parts else date_str
        time_col = date_parts[1] if len(date_parts) > 1 else ""
        w(line(right_pad(f"Order: {order_ref}", f"{date_col} {time_col}".strip())))

    if cashier:
        customer_name = (customer.get("name") if customer else None) or "Cash Customer"
        w(line(right_pad(f"Cashier: {cashier}", f"Customer: {customer_name}")))

    # ── Customer Detail Block ─────────────────────────────────────────────────
    if customer and customer.get("vat"):
        # Show full customer details only for B2B (Tax Invoice)
        w(line(LINE_SEPARATOR))
        if customer.get("name"):
            w(CONDENSED_ON)
            w(line(f"  Bill To: {customer['name']}"))
        if customer.get("ref"):
            w(line(f"  Ref:     {customer['ref']}"))
        if customer.get("street"):
            w(line(f"  Address: {customer['street']}"))
        if customer.get("vat"):
            w(line(f"  VAT:     {customer['vat']}"))
        if customer.get("phone"):
            w(line(f"  Phone:   {customer['phone']}"))
        w(CONDENSED_OFF)

    w(line(LINE_SEPARATOR))

    # ── Column Header ─────────────────────────────────────────────────────────
    # DESCRIPTION(40) | QTY(6) | UNIT PRICE(10) | DISC%(5) | TOTAL(13) + gaps = 80
    w(BOLD_ON + CONDENSED_ON)
    col_hdr = f"{'DESCRIPTION':<40}{'QTY':>6}{'UNIT PRC':>10}{'DISC':>5}{'TOTAL':>13}"
    w(line(col_hdr[:PAPER_COLS]))
    w(BOLD_OFF)
    w(line(LINE_SEPARATOR))
    w(CONDENSED_OFF)

    # ── Order Lines ───────────────────────────────────────────────────────────
    w(CONDENSED_ON)
    for ln in lines_:
        name      = str(ln.get("name", ""))
        qty       = float(ln.get("qty", 0))
        unit_prc  = float(ln.get("unit_price_before_tax", ln.get("unit_price", 0)))
        discount  = float(ln.get("discount", 0))
        # Use price_without_tax_before_discount for the "total" column
        # (matches template's priceWithoutTaxBeforeDiscount column)
        line_total = float(
            ln.get("price_without_tax_before_discount")
            or ln.get("price_with_tax")
            or 0
        )

        if len(name) > 40:
            name = name[:38] + ".."

        disc_str = f"{int(discount)}%" if discount > 0 else "-"
        row = (
            f"{name:<40}"
            f"{qty:>6.2f}"
            f"{unit_prc:>10.2f}"
            f"{disc_str:>5}"
            f"{line_total:>13.2f}"
        )
        w(line(row[:PAPER_COLS]))

        note = str(ln.get("note", "")).strip()
        if note:
            w(line(f"    \u2514 {note[:72]}"))

    w(CONDENSED_OFF)
    w(line(LINE_SEPARATOR))

    # ── Totals Block (mirrors TotalOrderReceipt template) ─────────────────────
    subtotal_before_disc = float(totals.get("subtotal_before_discount", 0))
    discount_ex_tax      = float(totals.get("discount_ex_tax", 0))
    subtotal             = float(totals.get("subtotal", 0))
    tax                  = float(totals.get("tax", 0))
    amount_total         = float(totals.get("amount_total", 0))
    rounding             = float(totals.get("rounding", 0))
    grand_total          = float(totals.get("grand_total", amount_total + rounding))
    paid                 = float(totals.get("paid", 0))
    change               = float(totals.get("change", 0))

    # Subtotal before discount
    w(total_row("Subtotal (before discount):", subtotal_before_disc))

    # Discount line — only if non-zero
    if discount_ex_tax > 0:
        w(total_row("Discount:", -abs(discount_ex_tax)))

    # Net subtotal (after discount, ex-tax)
    w(total_row("Net Subtotal:", subtotal))

    # Tax (15% VAT)
    w(total_row("VAT (15%):", tax))

    # Rounding — only if non-zero
    if abs(rounding) > 0.001:
        w(total_row("Rounding:", rounding))

    # Employee / fulfilled_by separator + grand total
    employee_label = employee if employee else "TOTAL"
    w(line(DOUBLE_SEPARATOR))
    w(BOLD_ON + DBL_WIDTH_ON)
    # Grand total in double-width; right-align manually (double-width halves effective cols)
    grand_str = fmt(grand_total)
    gt_label  = "TOTAL:"
    dw_width  = PAPER_COLS // 2
    gt_row    = right_pad(gt_label, grand_str, dw_width)
    w(line(gt_row))
    w(BOLD_OFF + DBL_WIDTH_OFF)
    w(line(DOUBLE_SEPARATOR))

    # ── Payments ──────────────────────────────────────────────────────────────
    w(blank(1))
    w(JUSTIFY_CENTER)
    w(BOLD_ON)
    w(line(center("─── PAYMENT ───")))
    w(BOLD_OFF)
    w(JUSTIFY_LEFT)
    w(line(LINE_SEPARATOR))

    for pay in payments:
        pay_name   = str(pay.get("name", ""))
        pay_amount = float(pay.get("amount", 0))
        w(total_row(f"{pay_name}:", pay_amount))

    if change > 0:
        w(BOLD_ON)
        w(total_row("Change:", change))
        w(BOLD_OFF)

    # ── Footer ────────────────────────────────────────────────────────────────
    w(blank(1))
    w(JUSTIFY_CENTER)

    footer_text = data.get("footer", "").strip()
    if footer_text:
        for fline in footer_text.splitlines():
            if fline.strip():
                w(line(center(fline.strip())))
    else:
        w(line(center("Thank you for your business!")))

    w(line(center(f"Printed: {datetime.now().strftime('%d/%m/%Y  %H:%M:%S')}")))
    w(line(DOUBLE_SEPARATOR))

    # ── Paper Feed ────────────────────────────────────────────────────────────
    w(JUSTIFY_LEFT)
    for _ in range(FEED_LINES_AFTER):
        w(blank(1))

    return bytes(buf)
