# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

{
    'name': 'Odoo Integration With Sendcloud',
    'version': '2.0',
    'author': 'TidyWay',
    'category': 'Warehouse',
    'summary': 'Shipment integration to sendcloud',
    'website': 'https://tidyway.in/',
    'description': """
Sendcloud integration
=========================
    * Synchronize all shipments to sendcloud
""",
    'depends': [
                'sale_stock',
                'delivery',
                'document'
                ],
    'data': [
            'security/ir.model.access.csv',
            'data/sendcloud_template.xml',
            'views/sendcloud_config.xml',
            'views/res_company_view.xml',
            'wizard/sendcloud_wizard_view.xml',
            'wizard/synchronization_wizard_view.xml',
            'wizard/refresh_shipment_methods.xml',
            'views/stock_picking_view.xml',
            'views/sendcloud_view.xml'
            ],
    'price': 190,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'license': 'OPL-1',
    'auto_install': False,
    'images': ['images/sendcloud.png'],
}
