# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)


import json
import requests
import base64

from odoo.exceptions import UserError, Warning
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

#sendcloud_integration/models/sendcloud.py
#import sys
#reload(sys)
#sys.setdefaultencoding('utf8')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sync_sendcloud = fields.Boolean(
        string='Synced to SendCloud',
        copy=False)
    sendcloud_shipping_method_id = fields.Char(
      string='SendCloud Shipping ID',
      copy=False)
    sendcloud_shipping_method = fields.Char(
      string='SendCloud Shipping Method',
      copy=False)
    sendcloud_tracking_number = fields.Char(
      string='SendCloud Tracking Number',
      copy=False)
    sendcloud_tracking_url = fields.Text(
      string='SendCloud Tracking Url',
      copy=False)
#     all_parcel_ids = fields.Char(
#       string='SendCloud Parcel Ids',
#       copy=False)

    @api.model
    def _get_urlheader(self):
        API_KEY = self.company_id.sendcloud_api_key
        SECRET_KEY = self.company_id.sendcloud_secret_key
        return 'https://%s:%s@panel.sendcloud.sc/api/v2/parcels/' % (
                                                                     API_KEY,
                                                                     SECRET_KEY
                                                                     )

    @api.model
    def _get_labelurl(self):
        API_KEY = self.company_id.sendcloud_api_key
        SECRET_KEY = self.company_id.sendcloud_secret_key
        return 'https://%s:%s@panel.sendcloud.sc/api/v2/labels/' % (
                                                                     API_KEY,
                                                                     SECRET_KEY
                                                                     )

    @api.model
    def download_label(self, number_url):
        API_KEY = self.company_id.sendcloud_api_key
        SECRET_KEY = self.company_id.sendcloud_secret_key
        return 'https://%s:%s@panel.sendcloud.sc/api/v2/labels/label_printer/%s' % (
                                                                     API_KEY,
                                                                     SECRET_KEY,
                                                                     number_url
                                                                     )

    @api.model
    def _get_partner_address(self, i):
        part = i.partner_id
        street_name = ''
        if 'street_name' in self.env['res.partner']._fields:
            street_name = part['street_name'] or ''
        address = [
                   part.street or '',
                   street_name,
                   part.street2 or '',
                   ]
        return " ".join([x for x in address if x])

    @api.model
    def _get_shipping_values(self, i, shipping_method_id):
        if not i.partner_id.country_id.code:
            raise Warning(_(""" Please put country on customer form."""))
        company_name = i.partner_id.parent_id\
            and i.partner_id.commercial_partner_id.name or ''
        partner_record = i.partner_id
        if hasattr(partner_record, 'wk_company'):
            company_name = i.partner_id.wk_company
        if not company_name:
            company_name = i.partner_id.commercial_partner_id.name or ''
        sendcloud_value = {
                           'parcel':
                               {
                                'name': i.partner_id.name,
                                'company_name': company_name,
                                'address': self._get_partner_address(i),
                                'house_number': i.partner_id.sc_street_number or '',
                                'city': i.partner_id.city or '',
                                'postal_code': i.partner_id.zip or '',
                                'telephone': i.partner_id.phone or '',
                                'request_label': True,
                                'data': [],
                                'country': i.partner_id.country_id.code or '',
                                'email': i.partner_id.email or '',
                                'weight': '1',
                                'order_number': i.name or '',
                                'country_state': i.partner_id.state_id.code or i.partner_id.commercial_partner_id.state_id.code or '',
                                #'to_state': i.partner_id.state_id.code or i.partner_id.commercial_partner_id.state_id.code or '',
                                'insured_value': 0,
                                'shipment': {
                                             'id': shipping_method_id
                                             },
                               }
                           }
        country_code = i.partner_id.country_id.code
        if country_code and country_code in ('US', 'CA'):
            sendcloud_value['parcel'].update({
                                    'to_state': i.partner_id.state_id.code or i.partner_id.commercial_partner_id.state_id.code or ''
                                    })

        order = self.env['sale.order'].search([
                               ('name', '=', i.origin or '/#j')], limit=1)
        total_amount = order and str(order.amount_total) or '0.1'
        total_qty = sum([x.product_uom_qty for x in i.move_lines])
        config = self.env['sendcloud.config'].search([], limit=1)
        outside_countries_code = [x.code for x in config.outside_countries]
        if country_code and country_code in outside_countries_code:
            sendcloud_value['parcel'].update({
                    'customs_invoice_nr': i.origin or '/',
                    'customs_shipment_type': 2,
                    'parcel_items':[
                                    {
                                        "description": "Toy Parts",
                                        "quantity": int(total_qty),
                                        "weight": str(i.weight or '0.1'),
                                        "value": total_amount or '0.10',
                                        "hs_code": "950395",
                                        "origin_country": country_code
                                      }
                                    ]
                    })
        return sendcloud_value

    @api.multi
    def _check_validation(self):
        self.ensure_one()
        if self.sync_sendcloud:
            raise UserError(_('Shipment %s Already synced\
                with SendCloud') % str(self.name))

    @api.model
    def _get_all_urls(self):
        url = self._get_urlheader()
        label_url = self._get_labelurl()
        headers = {
                   'Content-Type': 'application/json',
                   'charset': 'utf-8'
                   }
        return url, label_url, headers

    @api.multi
    def sync_to_sendcloud(self,
                          shipping_method_id,
                          default_label_request
                          ):
        attach_obj = self.env["ir.attachment"]
        self.ensure_one()
        self._check_validation()
        url, label_url, headers = self._get_all_urls()
        sendcloud_value = self._get_shipping_values(
                                                    self,
                                                    shipping_method_id
                                                    )
        shipping_syncronized = False
        shipment_ids, all_tracking_numbers, all_tracking_urls,\
            ship_methods_name, all_parcel_ids = [], [], [], [], []
        _logger.info('(%s)', sendcloud_value)
        for loop in range(0, default_label_request):
            r = requests.post(
                              url,
                              data=json.dumps(sendcloud_value),
                              headers=headers
                              )
            _logger.info('(%s)', r.text)
            response = json.loads(r.text)
            if response.get('error'):
                raise UserError(_(
                      response.get('error') and
                      response['error'].get('message', '') or ''
                      ))
            else:
                shipping_syncronized = True
                shipment_ids.append(str(self.name))
                parcel_id = response['parcel']['id']
                self.env['sendcloud.shipment'].create({
                                               'name': str(self.id),
                                               'stock_picking_id': self.id,
                                               'shipment_id': parcel_id,
                                               })
                prcl = response and response.get('parcel', {}) or {}
                all_tracking_numbers.append(prcl.get('tracking_number', '') or '')
                all_tracking_urls.append(prcl.get('tracking_url', '') or '')
                ship_methods_name.append(prcl.get('shipment') and prcl['shipment'].get('name') or '')
                all_parcel_ids.append(str(parcel_id))
        ship_methods_name = list(set(ship_methods_name))
        if shipping_syncronized:
            self.write({
                'sync_sendcloud': True,
                'sendcloud_shipping_method_id': str(shipping_method_id),
                'sendcloud_shipping_method': ship_methods_name and ship_methods_name[0] or '',
                'sendcloud_tracking_number': ", ".join(list(set(all_tracking_numbers))),
                'sendcloud_tracking_url':  all_tracking_urls and all_tracking_urls[0] or '',
                'carrier_tracking_ref':  all_tracking_urls and all_tracking_urls[0] or '',
                 })

            for parcel in all_parcel_ids:
                get_parcel_req = requests.get(self.download_label(parcel))
                attach_obj.create({
                                'res_model': 'stock.picking',
                                'name': str(parcel)+'.pdf',
                                'res_id': self.id,
                                #'datas': base64.encodestring(bytes(get_parcel_req.text, 'utf-8')),
                                'datas': base64.encodestring(get_parcel_req.content),
                                'datas_fname': str(parcel)+'.pdf',
                           })

        return shipment_ids

    @api.multi
    def open_sendcloud_tracking_url(self):
        self.ensure_one()
        if not self.sendcloud_tracking_url:
            raise UserError(_("Your delivery method has no redirect on courier provider's website to track this order."))

        urls_splits = (self.sendcloud_tracking_url).split(',')
        client_action = {'type': 'ir.actions.act_url',
                         'name': "Shipment Tracking Page",
                         'target': 'new',
                         'url': urls_splits[0],
                         }
        return client_action

    @api.model
    def sendcloud_traking_email_to_customer(self):
        """
            Send Tracking information to customer
        """
        template = self.env.ref(
            'sendcloud_integration.send_tracking_number_to_customer')
        self.env['mail.template'].browse(template.id).send_mail(
                self.id, force_send=True)
