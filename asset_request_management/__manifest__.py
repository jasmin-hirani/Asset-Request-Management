{
    'name': 'Asset Request Management',
    'version': '18.0.0.0.0',
    'summary': 'Manage asset requests with multi-stage approval from different departments',
    'category': 'Inventory',
    'author': 'Tatvamasi Labs',
    'depends': ['base', 'stock', 'purchase'],
    'data': [
        'security/asset_request_security.xml',
        'security/ir.model.access.csv',
        'views/asset_request_views.xml',
        'views/asset_request_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
