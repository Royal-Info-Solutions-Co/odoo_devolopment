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
    ip: "[BRIDGE_IP]",               // ← YOUR WINDOWS PC STATIC IP (e.g. "192.168.1.50")
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
