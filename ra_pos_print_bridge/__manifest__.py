{
    'name': 'RA POS Print Bridge',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Routes POS receipt printing to a local Windows USB printer via LAN bridge',
    'author': 'Royal Alwaha Trading Co. - RISC Division',
    'depends': ['point_of_sale'],
    'data': [],
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
