{
    'name': 'RA POS Print Bridge',
    'version': '17.0.2.0.0',
    'category': 'Point of Sale',
    'summary': 'Routes POS receipt printing to a local Windows USB printer via LAN bridge',
    'author': 'Royal Alwaha Trading Co. - RISC Division',
    'depends': ['point_of_sale', 'tis_pos_receipt_a4_formate'],
    'data': [
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'ra_pos_print_bridge/static/src/js/bridge_config.js',
            'ra_pos_print_bridge/static/src/js/pos_print_bridge.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
