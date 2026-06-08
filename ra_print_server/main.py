"""
RA Print Server — FastAPI Application
Royal Alwaha Trading Co. | RISC Division

Listens on PORT for JSON print payloads from the Odoo POS bridge.
Renders receipts as ESC/P and dispatches to the USB printer.

Run modes:
  Development : python main.py
  Production  : ra_print_server.exe (PyInstaller bundle)
"""

import sys
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import HOST, PORT, ALLOWED_ORIGINS, RECEIPT_COPIES, PRINTER_NAME
from renderer import render_receipt
from printer import send_raw, list_printers
from logger import get_logger

log = get_logger("main")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="RA Print Server",
    description="Local POS receipt printing bridge for Royal Alwaha",
    version="1.0.0",
    docs_url="/docs",      # Disable in production by setting to None
    redoc_url=None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Required: Odoo POS web view sends cross-origin requests from the Odoo server
# domain to this local server IP. Without this, the browser will block the request.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "X-Source"],
)

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Quick connectivity check from the Odoo POS client."""
    available_printers = list_printers()
    from config import PRINTER_NAME
    return {
        "status": "ok",
        "server": "RA Print Server v1.0",
        "printer_configured": PRINTER_NAME,
        "printer_available": PRINTER_NAME in available_printers,
        "all_printers": available_printers,
    }


@app.post("/print")
async def print_receipt(request: Request):
    """
    Main print endpoint.

    Accepts JSON receipt payload from Odoo POS bridge,
    renders it as ESC/P, and dispatches to the USB printer.

    Returns:
        { "success": true, "bytes_sent": N }   on success
        { "success": false, "error": "..." }   on failure (HTTP 200 so JS can read body)
    """
    # ── Parse Body ────────────────────────────────────────────────────────────
    try:
        body = await request.body()
        if not body:
            raise ValueError("Empty request body")
        data = json.loads(body)
    except Exception as e:
        log.warning(f"Bad request body: {e}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Invalid JSON: {str(e)}"}
        )

    order_ref = data.get("order_ref", "unknown")
    log.info(f"Print request received: order={order_ref}")

    # ── Render ────────────────────────────────────────────────────────────────
    try:
        raw_bytes = render_receipt(data)
    except Exception as e:
        log.error(f"Render failed for order {order_ref}: {e}", exc_info=True)
        return JSONResponse(
            content={"success": False, "error": f"Render error: {str(e)}"}
        )

    # ── Print (with optional copies) ─────────────────────────────────────────
    try:
        for copy_num in range(RECEIPT_COPIES):
            send_raw(raw_bytes)
            if RECEIPT_COPIES > 1:
                log.info(f"Printed copy {copy_num + 1}/{RECEIPT_COPIES}")
    except Exception as e:
        log.error(f"Print dispatch failed for order {order_ref}: {e}", exc_info=True)
        return JSONResponse(
            content={"success": False, "error": f"Printer error: {str(e)}"}
        )

    log.info(f"Order {order_ref} printed successfully ({len(raw_bytes)} bytes)")
    return JSONResponse(content={"success": True, "bytes_sent": len(raw_bytes)})


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Everything is wrapped so that any startup failure is written to the log
    # file. A --noconsole build has no visible console, so without this an
    # exception (e.g. a missing bundled module or a printer enumeration error)
    # would kill the process silently and the server would simply never listen.
    try:
        log.info("=" * 60)
        log.info("RA Print Server starting...")
        log.info(f"Listening on {HOST}:{PORT}")
        log.info(f"Configured printer: {PRINTER_NAME}")
        try:
            log.info(f"Available printers: {list_printers()}")
        except Exception:
            log.exception("Could not enumerate printers at startup")
        log.info("=" * 60)

        # Pass the app object (not "main:app") so it works in a frozen
        # PyInstaller build where the module isn't importable by name.
        # log_config=None disables uvicorn's default colourized logging, which
        # calls sys.stdout.isatty() and crashes in a --noconsole build where
        # stdout is None. We log to file anyway.
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_config=None,
            log_level="warning",   # Use file logger above; suppress uvicorn verbosity
            access_log=False,
        )
    except Exception:
        log.exception("RA Print Server failed to start")
        raise
