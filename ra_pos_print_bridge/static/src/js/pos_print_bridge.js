/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { BRIDGE_CONFIG } from "./bridge_config";

// ── Payload Builder (HTML Mode) ────────────────────────────────────────────────
//
// Captures the rendered .pos-receipt DOM element as a raw HTML string.
// Python's WeasyPrint + print.css renders it to PDF for printing.
// No order field extraction needed — the browser already rendered the receipt.

function buildPrintPayload(order) {
    // Locate the rendered receipt element in the POS DOM
    const receiptEl = document.querySelector(".pos-receipt");
    if (!receiptEl) {
        throw new Error(
            "[POS Bridge] .pos-receipt element not found in DOM. " +
            "Ensure the receipt screen is fully rendered before printing."
        );
    }

    // Capture outerHTML — includes the root element and all children.
    // CSS classes and inline styles from the template are preserved.
    // WeasyPrint on the server applies print.css for paper layout.
    const html = receiptEl.outerHTML;

    // Minimal meta for server-side logging only — not used for rendering
    const orderRef = (order && order.name) ? order.name : "unknown";

    if (BRIDGE_CONFIG.debug_log) {
        console.log(
            `[POS Bridge] HTML payload: ${html.length} chars, order=${orderRef}` 
        );
    }

    return {
        schema_version: "2.0",
        mode: "html",
        order_ref: orderRef,
        html: html,
        copies: 1,
    };
}

// ── OWL Patch ─────────────────────────────────────────────────────────────────
// Patches printReceipt() only.
// tis_pos_receipt_a4_formate patches setup() — no conflict.

patch(ReceiptScreen.prototype, {

    async printReceipt() {

        if (!BRIDGE_CONFIG.enabled) {
            return super.printReceipt();
        }

        const order = this.currentOrder;

        // Give the OWL template one render cycle to fully paint the receipt DOM
        // before we capture it. The existing module already has a 1-second delay
        // for its image capture; we use a shorter wait since we only need HTML.
        await new Promise(resolve => setTimeout(resolve, 300));

        const notify = (message, type = "info") => {
            try {
                if (this.notification && this.notification.add) {
                    this.notification.add(message, { type, duration: 3000 });
                }
            } catch (_) { /* silent */ }
        };

        let payload;
        try {
            payload = buildPrintPayload(order);
        } catch (err) {
            console.error("[POS Bridge] Payload build failed:", err);
            notify("Could not capture receipt HTML — using device print", "warning");
            return super.printReceipt();
        }

        const url = `http://${BRIDGE_CONFIG.ip}:${BRIDGE_CONFIG.port}${BRIDGE_CONFIG.endpoint}`;
        const controller = new AbortController();
        const timeoutHandle = setTimeout(() => controller.abort(), BRIDGE_CONFIG.timeout_ms);

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Source": "odoo-pos-bridge",
                },
                body: JSON.stringify(payload),
                signal: controller.signal,
            });

            clearTimeout(timeoutHandle);

            if (response.ok) {
                const result = await response.json().catch(() => ({ success: true }));
                if (result.success !== false) {
                    if (BRIDGE_CONFIG.show_success_toast) {
                        notify("Receipt sent to printer ✓", "success");
                    }
                    return;
                }
                throw new Error(result.error || "Bridge reported failure");
            }
            throw new Error(`Bridge HTTP ${response.status}`);

        } catch (err) {
            clearTimeout(timeoutHandle);
            const isTimeout = err.name === "AbortError";
            const msg = isTimeout
                ? "Print bridge timeout — is the server running?"
                : `Print bridge error: ${err.message}`;
            console.error("[POS Bridge]", msg);
            if (BRIDGE_CONFIG.show_error_toast) {
                notify(
                    BRIDGE_CONFIG.fallback_to_native
                        ? "Bridge unreachable — using device print"
                        : msg,
                    BRIDGE_CONFIG.fallback_to_native ? "warning" : "danger"
                );
            }
            if (BRIDGE_CONFIG.fallback_to_native) {
                return super.printReceipt();
            }
        }
    },
});
