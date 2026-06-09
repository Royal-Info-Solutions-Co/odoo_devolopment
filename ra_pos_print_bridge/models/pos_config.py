from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    # ── Print Bridge Settings ──────────────────────────────────────────────
    bridge_enabled = fields.Boolean(
        string='Enable Print Bridge',
        default=True,
        help='Enable local network receipt printing via the Windows print bridge server.'
    )
    bridge_printer_ip = fields.Char(
        string='Bridge Server IP',
        size=15,
        help=(
            'Static IP address of the Windows PC running ra_print_server.exe '
            'for this POS terminal (e.g. 192.168.1.50).'
        )
    )
    bridge_printer_port = fields.Integer(
        string='Bridge Server Port',
        default=8080,
        help='Listening port of the Windows print bridge server. Default: 8080.'
    )
