from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_config(self):
        """
        Extend the pos.config fields loaded into the POS frontend
        to include the Print Bridge settings.

        These fields become accessible in JS as:
            this.pos.config.bridge_enabled
            this.pos.config.bridge_printer_ip
            this.pos.config.bridge_printer_port
        """
        result = super()._loader_params_pos_config()
        result['search_params']['fields'] += [
            'bridge_enabled',
            'bridge_printer_ip',
            'bridge_printer_port',
        ]
        return result
