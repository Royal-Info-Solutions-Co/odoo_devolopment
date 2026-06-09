/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { BRIDGE_CONFIG } from "./bridge_config";

// ── Bridge Endpoint Resolver ───────────────────────────────────────────────────
// Reads IP and port from the live pos.config record (loaded by pos.session).
// Falls back gracefully if fields are missing or empty.

function resolveBridgeEndpoint(posService) {
    const config = posService && posService.config;

    const enabled = config
        ? (config.bridge_enabled !== undefined ? config.bridge_enabled : true)
        : true;

    const ip   = (config && config.bridge_printer_ip)   || "";
    const port = (config && config.bridge_printer_port) || 8080;
    const name = (config && (config.display_name || config.name)) || "default";

    return { enabled, ip, port, configName: name };
}

// ── Payload Builder (HTML Mode) ────────────────────────────────────────────────

function buildPrintPayload(order, configName) {
    const receiptEl = document.querySelector(".pos-receipt");
    if (!receiptEl) {
        throw new Error(
            "[POS Bridge] .pos-receipt element not found in DOM. " +
            "Ensure the receipt screen is fully rendered before printing."
        );
    }

    const html     = receiptEl.outerHTML;
    const orderRef = (order && order.name) ? order.name : "unknown";

    if (BRIDGE_CONFIG.debug_log) {
        console.log(
            `[POS Bridge] order=${orderRef} | config="${configName}" | ${html.length} chars`
        );
    }

    return {
        schema_version:  "2.1",
        mode:            "html",
        order_ref:       orderRef,
        pos_config_name: configName,
        html:            html,
        copies:          1,
    };
}

// ── OWL Patch ─────────────────────────────────────────────────────────────────

patch(ReceiptScreen.prototype, {

    async printReceipt() {

        // ── Resolve config from live pos.config record ─────────────────────
        const { enabled, ip, port, configName } = resolveBridgeEndpoint(this.pos);

        // If disabled in POS settings, fall through to native print immediately
        if (!enabled) {
            if (BRIDGE_CONFIG.debug_log) {
                console.log("[POS Bridge] Disabled in POS config — using native print.");
            }
            return super.printReceipt();
        }

        // If no IP configured, warn and fall through
        if (!ip) {
            console.warn(
                "[POS Bridge] No Bridge Server IP set for this POS config. " +
                "Go to Point of Sale → Configuration → Settings → Print Bridge."
            );
            return super.printReceipt();
        }

        const order = this.currentOrder;
        const url   = `http://${ip}:${port}${BRIDGE_CONFIG.endpoint}`;

        if (BRIDGE_CONFIG.debug_log) {
            console.log(`[POS Bridge] Routing: ${url} (config: "${configName}")`);
        }

        // Allow OWL render cycle to complete before capturing HTML
        await new Promise(resolve =>
            setTimeout(resolve, BRIDGE_CONFIG.render_wait_ms)
        );

        const notify = (message, type = "info") => {
            try {
                if (this.notification && this.notification.add) {
                    this.notification.add(message, { type, duration: 3000 });
                }
            } catch (_) { /* silent */ }
        };

        let payload;
        try {
            payload = buildPrintPayload(order, configName);
        } catch (err) {
            console.error("[POS Bridge] Payload build failed:", err);
            notify("Could not capture receipt HTML — using device print", "warning");
            return super.printReceipt();
        }

        const controller    = new AbortController();
        const timeoutHandle = setTimeout(
            () => controller.abort(),
            BRIDGE_CONFIG.timeout_ms
        );

        try {
            const response = await fetch(url, {
                method:  "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Source":     "odoo-pos-bridge",
                },
                body:   JSON.stringify(payload),
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
                ? `Print bridge timeout — is ${ip}:${port} reachable?`
                : `Print bridge error: ${err.message}`;

            console.error("[POS Bridge]", msg);

            if (BRIDGE_CONFIG.show_error_toast) {
                notify(
                    BRIDGE_CONFIG.fallback_to_native
                        ? `Bridge unreachable — using device print`
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
