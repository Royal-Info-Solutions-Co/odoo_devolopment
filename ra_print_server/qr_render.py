"""
QR Code bitmap renderer for ESC/P 24-pin dot-matrix printers (Epson LQ-690).

Converts a QR code image (base64 data URI or raw PNG bytes) into ESC/P
bit-image graphics commands that the printer renders as a scannable QR code.

Requires: Pillow (PIL)
"""

import base64
import io

from PIL import Image

# ── ESC/P Graphics Constants ──────────────────────────────────────────────────
ESC = b"\x1b"
CRLF = b"\x0d\x0a"
# ESC 3 n : set line spacing to n/180 inch (24/180 = exact 24-pin band height)
SET_LINE_SPACING = ESC + b"3"
# ESC * m nL nH <data> : select bit-image mode
BIT_IMAGE_CMD = ESC + b"*"
# Modes for 24-pin:
#   32 = 180 DPI horizontal (good balance of speed and quality)
#   33 = 360 DPI horizontal (highest resolution, slower)
MODE_180DPI = 32
MODE_360DPI = 33


def decode_qr_image(data_uri_or_bytes) -> Image.Image:
    """Decode a QR image from a base64 data URI string or raw bytes."""
    if isinstance(data_uri_or_bytes, str):
        payload = data_uri_or_bytes
        if "," in payload:
            payload = payload.split(",", 1)[1]
        raw = base64.b64decode(payload)
    elif isinstance(data_uri_or_bytes, bytes):
        raw = data_uri_or_bytes
    else:
        raise ValueError("QR data must be a base64 data URI string or bytes")
    return Image.open(io.BytesIO(raw))


def render_qr_escp(
    data_uri_or_bytes,
    target_width_px: int = 200,
    mode: int = MODE_180DPI,
) -> bytes:
    """
    Render a QR code image as ESC/P 24-pin bit-image data.

    Args:
        data_uri_or_bytes: base64 data URI string (data:image/png;base64,...)
                           or raw PNG/BMP bytes.
        target_width_px:   desired print width in dots (at the mode's DPI).
                           200 px @ 180 DPI ≈ 28 mm — good for receipt QR.
        mode:              ESC * bit-image mode (32=180dpi, 33=360dpi).

    Returns:
        Raw ESC/P bytes that, when sent to the printer, print the QR bitmap.
    """
    img = decode_qr_image(data_uri_or_bytes)

    # Convert to grayscale → resize → threshold to 1-bit
    img = img.convert("L")
    w, h = img.size
    scale = target_width_px / w
    new_w = target_width_px
    new_h = int(h * scale)
    # NEAREST resampling keeps QR edges sharp (no antialiasing blur)
    img = img.resize((new_w, new_h), Image.NEAREST)

    # Threshold: pixels < 128 → black (print), >= 128 → white (no print)
    img = img.point(lambda x: 0 if x < 128 else 255, "1")

    # Pad height to a multiple of 24 (one full 24-pin band)
    remainder = new_h % 24
    if remainder != 0:
        pad_h = 24 - remainder
        padded = Image.new("1", (new_w, new_h + pad_h), 1)  # 1 = white
        padded.paste(img, (0, 0))
        img = padded
        new_h = img.height

    pixels = img.load()
    buf = bytearray()

    # Set line spacing to 24/180 inch (exact band height — no gaps/overlaps)
    buf.extend(SET_LINE_SPACING + bytes([24]))

    # Print in bands of 24 rows (one band = one pass of the 24-pin head)
    for band_start in range(0, new_h, 24):
        # Command header: ESC * mode nL nH
        nL = new_w & 0xFF
        nH = (new_w >> 8) & 0xFF
        buf.extend(BIT_IMAGE_CMD + bytes([mode, nL, nH]))

        # Column data: 3 bytes per column (24 bits, MSB = topmost pin)
        for col in range(new_w):
            b0, b1, b2 = 0, 0, 0
            for pin in range(24):
                row = band_start + pin
                if row < new_h:
                    px = pixels[col, row]
                    if px == 0:  # black pixel → fire pin
                        byte_idx = pin // 8
                        bit_pos = 7 - (pin % 8)
                        if byte_idx == 0:
                            b0 |= (1 << bit_pos)
                        elif byte_idx == 1:
                            b1 |= (1 << bit_pos)
                        else:
                            b2 |= (1 << bit_pos)
            buf.extend(bytes([b0, b1, b2]))

        # Advance paper one band (CRLF with the 24/180 line spacing)
        buf.extend(CRLF)

    # Reset line spacing to default (1/6 inch = 30/180 inch)
    buf.extend(SET_LINE_SPACING + bytes([30]))

    return bytes(buf)
