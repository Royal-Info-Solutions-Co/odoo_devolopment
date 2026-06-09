/** @odoo-module **/

/**
 * RA POS Print Bridge — Behaviour Configuration
 * Royal Alwaha Trading Co. | RISC Division
 *
 * Network settings (IP, port, enabled) are now configured per POS in Odoo:
 *   Point of Sale → Configuration → Settings → Print Bridge
 *
 * This file controls non-network behaviour only.
 * Changes here require an Odoo asset upgrade (./odoo-bin -u ra_pos_print_bridge).
 */
export const BRIDGE_CONFIG = {
    // ── Endpoint ──────────────────────────────────────────────────────────
    // The URL path on the Windows server. Rarely needs changing.
    endpoint: "/print",

    // ── Timing ────────────────────────────────────────────────────────────
    // How long to wait for the server to respond before giving up (ms)
    timeout_ms: 6000,

    // Delay before capturing the receipt DOM (ms).
    // Gives OWL time to finish rendering before we grab the HTML.
    render_wait_ms: 300,

    // ── Fallback ──────────────────────────────────────────────────────────
    // If true: fall back to native device print when bridge is unreachable.
    // If false: show error toast only, no native print.
    fallback_to_native: true,

    // ── Notifications ─────────────────────────────────────────────────────
    show_success_toast: true,
    show_error_toast:   true,

    // ── Debug ─────────────────────────────────────────────────────────────
    // Set true to log payload details and routing decisions to browser console.
    debug_log: false,
};
