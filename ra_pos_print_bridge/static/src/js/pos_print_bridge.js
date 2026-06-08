/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { BRIDGE_CONFIG } from "./bridge_config";

// ── Payload Builder ────────────────────────────────────────────────────────────
// Extracts structured receipt data from the Odoo POS order object.
// Uses order.export_for_printing() which is Odoo's canonical receipt data source.

function buildPrintPayload(order) {
    const r = order.export_for_printing();

    return {
        // ── Meta ──────────────────────────────────────────────────────────
        schema_version: "1.0",
        printed_at: new Date().toISOString(),

        // ── Order Identity ────────────────────────────────────────────────
        order_ref: r.name || "",
        pos_reference: r.pos_reference || r.name || "",
        date: r.date || {},
        note: r.note || "",

        // ── Company ───────────────────────────────────────────────────────
        company: {
            name: (r.company && r.company.name) ? r.company.name : "",
            address: (r.company && r.company.contact_address) ? r.company.contact_address : "",
            phone: (r.company && r.company.phone) ? r.company.phone : "",
            vat: (r.company && r.company.vat) ? r.company.vat : "",
            email: (r.company && r.company.email) ? r.company.email : "",
            website: (r.company && r.company.website) ? r.company.website : "",
        },

        // ── People ────────────────────────────────────────────────────────
        cashier: r.cashier || "",
        customer: r.client ? (r.client.name || "") : "Walk-in Customer",
        customer_phone: r.client ? (r.client.phone || "") : "",

        // ── Order Lines ───────────────────────────────────────────────────
        lines: (r.orderlines || []).map(line => ({
            name: line.product_name || "",
            qty: line.quantity || 0,
            unit_price: line.price || 0,
            discount: line.discount || 0,
            price_with_tax: line.price_with_tax || 0,
            price_without_tax: line.price_without_tax || (line.price || 0),
            note: line.customer_note || "",
            unit: line.unit_name || "",
        })),

        // ── Payments ─────────────────────────────────────────────────────
        payments: (r.paymentlines || []).map(p => ({
            name: p.name || "",
            amount: p.amount || 0,
        })),

        // ── Totals ────────────────────────────────────────────────────────
        totals: {
            subtotal: r.total_without_tax || 0,
            tax: r.total_tax || 0,
            total: r.total_with_tax || 0,
            paid: r.total_paid || 0,
            change: r.change || 0,
            discount: r.total_discount || 0,
            rounding: r.rounding_applied || 0,
        },

        // ── Tax Details ───────────────────────────────────────────────────
        tax_details: (r.tax_details || []).map(t => ({
            name: t.tax_name || t.tax_group_name || "",
            base: t.base_amount || 0,
            amount: t.tax_amount || 0,
        })),

        // ── Header / Footer ───────────────────────────────────────────────
        header: r.header || "",
        footer: r.footer || "",
    };
}

// ── OWL Patch ─────────────────────────────────────────────────────────────────

patch(ReceiptScreen.prototype, {

    async printReceipt() {

        // If bridge is disabled globally, fall through to native Odoo print
        if (!BRIDGE_CONFIG.enabled) {
            return super.printReceipt();
        }

        const order = this.currentOrder;
        if (!order) {
            console.warn("[POS Bridge] No current order — falling back to native print.");
            return super.printReceipt();
        }

        // Helper to show OWL notification
        const notify = (message, type = "info") => {
            try {
                if (this.notification && this.notification.add) {
                    this.notification.add(message, { type, duration: 3000 });
                }
            } catch (_) {
                // Notification service may not be available in all contexts — silent fail
            }
        };

        // Build payload
        let payload;
        try {
            payload = buildPrintPayload(order);
        } catch (err) {
            console.error("[POS Bridge] Failed to build payload:", err);
            return super.printReceipt();
        }

        if (BRIDGE_CONFIG.debug_log) {
            console.log("[POS Bridge] Payload:", JSON.stringify(payload, null, 2));
        }

        // Send to bridge
        const url = `http://${BRIDGE_CONFIG.ip}:${BRIDGE_CONFIG.port}${BRIDGE_CONFIG.endpoint}`;
        const controller = new AbortController();
        const timeoutHandle = setTimeout(
            () => controller.abort(),
            BRIDGE_CONFIG.timeout_ms
        );

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
                    return;  // ← Success: skip native print entirely
                }
                // Server returned ok=true but success=false in body
                throw new Error(result.error || "Bridge reported print failure");
            }

            throw new Error(`Bridge HTTP ${response.status}`);

        } catch (err) {
            clearTimeout(timeoutHandle);

            const isTimeout = err.name === "AbortError";
            const msg = isTimeout
                ? "Print bridge timeout — check if server is running"
                : `Print bridge error: ${err.message}`;

            console.error("[POS Bridge]", msg);

            if (BRIDGE_CONFIG.show_error_toast && BRIDGE_CONFIG.fallback_to_native) {
                notify("Bridge unreachable — using device print", "warning");
            } else if (BRIDGE_CONFIG.show_error_toast) {
                notify(msg, "danger");
            }

            if (BRIDGE_CONFIG.fallback_to_native) {
                return super.printReceipt();
            }
        }
    },
});
