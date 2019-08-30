# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

from odoo import api, models, _
from odoo.exceptions import Warning
import requests
import json


class refresh_shipment_methods(models.TransientModel):
    _name = 'refresh.shipment.methods'

    @api.multi
    def refresh(self):
        """
            Refresh shipping methods with detail
        """
        shipment_obj = self.env['sendcloud.shipping.method']
        prices_obj = self.env['shipment.value.prices']
        self.ensure_one()
        API_KEY = self.env.user.company_id.sendcloud_api_key
        SECRET_KEY = self.env.user.company_id.sendcloud_secret_key
        url = 'https://%s:%s@panel.sendcloud.sc/api/v2/shipping_methods/'%(API_KEY, SECRET_KEY)
        try:
            all_shipment_methods = requests.get(url)
        except:
            raise Warning(_(""" Please check your internet connection."""))
        response = json.loads(all_shipment_methods.text)
        selections = []
        all_methods = response.get('shipping_methods', [])
        prices_obj.search([]).sudo().unlink()
        shipment_obj.search([]).sudo().unlink()
        for values in all_methods:
            selection_id = values.get('id')
            shipping_method_name = values.get('name')
            countries = values.get('countries')
            min_weight = values.get('min_weight')
            max_weight = values.get('max_weight')
            carrier = values.get('carrier')
            if selection_id and shipping_method_name:
                selections.append((
                                   selection_id,
                                   shipping_method_name,
                                   min_weight,
                                   max_weight,
                                   carrier,
                                   countries
                                   ))
        for methods in selections:
            shipment = shipment_obj.create({
                                          'shipping_id': methods[0],
                                          'name': methods[1],
                                          'min_weight': methods[2],
                                          'max_weight': methods[3],
                                          'carrier': methods[4],
                                          })
            for price_rec in methods[5]:
                prices_obj.create({
                                   'shipping_method_id': price_rec.get('id','') or '',
                                   'name': price_rec.get('name','') or '',
                                   'country_code': price_rec.get('iso_2','') or '',
                                   'price': price_rec.get('price','') or '',
                                   'carrier_id': shipment.id,
                                   })

