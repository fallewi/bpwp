# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

from odoo import fields, models, api


class sendcloud_shipment(models.Model):
    _name = 'sendcloud.shipment'

    name = fields.Char(string='Odoo ID')
    stock_picking_id = fields.Many2one('stock.picking', string='Odoo Shipment')
    shipment_id = fields.Char(string='Sendcloud ID')


class ShipmentValuePrices(models.Model):
    _name = 'shipment.value.prices'

    shipping_method_id = fields.Char(string='Shipment Method ID')
    name = fields.Char(string='Country Name')
    country_code = fields.Char(string="Country Code")
    price = fields.Char(string="Price")
    carrier_id = fields.Many2one('sendcloud.shipping.method', string='carrier')


class sendcloudShippingMethod(models.Model):
    _name = 'sendcloud.shipping.method'

    shipping_id = fields.Char(string='shipping ID')
    name = fields.Char(string='shipping Name')
    shipping_value_ids = fields.One2many(
         'shipment.value.prices',
         'carrier_id',
         string='Shipping Price/Data'
         )
    min_weight = fields.Float()
    max_weight = fields.Float()
    carrier = fields.Char()


class SCMappingConfig(models.Model):
    _name = 'sc.mapping.config'

    odoo_delivery_method_id = fields.Many2one(
          'delivery.carrier',
          string="Odoo Delivery Method",
          required=True
          )
    sendclould_shipping_method_id = fields.Many2one(
          'sendcloud.shipping.method',
          string="Sendclould Shipping Method",
          required=True
          )
    sendclould_config_id = fields.Many2one(
           'sendcloud.config',
           string="Sendcloud Config"
           )


class SendcloudConfig(models.Model):
    _name = 'sendcloud.config'

    default_label_request = fields.Integer(
       string="Default Label Request",
       default=1,
       help="Default=1, it means single shipment send single request to sendcloud,\
       if you select > 1 then multiple request would be generate on sendcloud \
       for same shipment,\nReason: Sendcloud does not support\
       multi labels for single shipment."
       )
    mapping_ids = fields.One2many(
        'sc.mapping.config',
        'sendclould_config_id',
        string="Mapping"
        )
    send_email_to_customer = fields.Boolean(
        "Would you like to send an email to customer with tracking number ?")
    outside_countries = fields.Many2many(
        "res.country",
        "res_country_sendcloud_table",
        'country_id',
        'wizard_id',
        string="Outside Europe Countries",
        help="Put here outside europe countries so when sync order it will "
        "sync a more information from order ")

    @api.model
    def get_config(self):
        return self.env.ref('sendcloud_integration.default_sendcloud_config')

    @api.multi
    def apply(self):
        return True
