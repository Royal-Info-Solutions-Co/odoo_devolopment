/** @odoo-module **/

/**
 * RA POS Print Bridge — Configuration
 * Royal Alwaha Trading Co. | RISC Division
 *
 * IMPORTANT: Edit BRIDGE_IP to match your Windows print server's static IP.
 * This file is the only configuration point for the client side.
 */
export const BRIDGE_CONFIG = {
    // ── Core Settings ──────────────────────────────────────────────────────
    enabled: true,                    // Set false to disable bridge (uses native print)
    use_https: false,                 // ← Set true for the Odoo Android app. Its WebView
                                      //   blocks an insecure http call from the https POS
                                      //   page (mixed content). Requires the print server
                                      //   to run over https with a CA-trusted cert, and
                                      //   `ip` below must be the cert's HOSTNAME (not an IP).
    ip: "[BRIDGE_IP]",               // ← YOUR WINDOWS PC STATIC IP (e.g. "192.168.1.50")
                                      //   When use_https is true, use the cert hostname
                                      //   instead, e.g. "printbridge.royalalwaha.com".
    port: 8080,                       // Must match server's listening port
    endpoint: "/print",               // API endpoint on the Windows server

    // ── Behaviour ──────────────────────────────────────────────────────────
    timeout_ms: 6000,                 // Abort if server doesn't respond within 6 seconds
    fallback_to_native: true,         // If bridge fails, fall back to native Android print
    show_success_toast: true,         // Show green notification on successful print
    show_error_toast: true,           // Show red notification on bridge failure

    // ── Debug ──────────────────────────────────────────────────────────────
    debug_log: false,                 // Set true to log payloads to browser console
};
