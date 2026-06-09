"""
RA Print Server — HTML Receipt Renderer
Royal Alwaha Trading Co. | RISC Division

Converts raw HTML from the Odoo POS receipt screen to PDF bytes
using WeasyPrint + print.css, ready for silent printing via SumatraPDF.

Design principle:
    Python knows NOTHING about the receipt layout.
    All layout is controlled by print.css on the Windows PC.
    Changing the receipt appearance = editing print.css only.
    No Python code changes. No EXE rebuild. No redeployment.
"""

import os
import sys
from weasyprint import HTML, CSS
from logger import get_logger
from config import PRINT_CSS_FILE

log = get_logger("html_renderer")


def _resolve_path(filename: str) -> str:
    """
    Resolve a filename relative to the EXE location.
    Works both in development (script directory) and in PyInstaller bundle.
    """
    if getattr(sys, "frozen", False):
        # Running as PyInstaller EXE
        base = os.path.dirname(sys.executable)
    else:
        # Running as .py script
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


def _load_print_css() -> str:
    """
    Load print.css from the deployment folder.
    Falls back to minimal embedded CSS if the file is missing.
    """
    css_path = _resolve_path(PRINT_CSS_FILE)
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            log.info(f"Loaded print.css from {css_path}")
            return f.read()
    else:
        log.warning(
            f"print.css not found at {css_path}. "
            "Using minimal fallback CSS. Place print.css next to the EXE."
        )
        return _fallback_css()


def _fallback_css() -> str:
    """
    Minimal fallback CSS used if print.css is missing.
    Produces a readable but unstyled receipt.
    """
    return """
    @page { size: 20cm auto; margin: 0.4cm; }
    body  { font-family: Arial, sans-serif; font-size: 9pt; color: #000; }
    table { width: 100%; border-collapse: collapse; }
    td    { vertical-align: top; padding: 1px 3px; }
    img:not(#qrcode) { display: none; }
    #qrcode { max-width: 2.5cm; max-height: 2.5cm; }
    """


def render_to_pdf(html_fragment: str) -> bytes:
    """
    Convert a .pos-receipt HTML fragment to PDF bytes.

    Args:
        html_fragment:  outerHTML of the .pos-receipt div from the browser.

    Returns:
        PDF bytes ready to write to a temp file for printing.

    Raises:
        RuntimeError: if WeasyPrint fails to render.
    """
    css_string = _load_print_css()

    # Wrap fragment in a minimal valid HTML document.
    # charset meta is critical for Arabic text (cp1256 / UTF-8 round-trip).
    full_html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width"/>
</head>
<body>
{html_fragment}
</body>
</html>"""

    try:
        pdf_bytes = HTML(string=full_html, base_url=None).write_pdf(
            stylesheets=[CSS(string=css_string)],
            presentational_hints=True,   # honour font/color attributes in HTML
        )
        log.info(f"PDF rendered: {len(pdf_bytes)} bytes")
        return pdf_bytes
    except Exception as e:
        raise RuntimeError(f"WeasyPrint render failed: {e}") from e
