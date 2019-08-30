# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

from odoo import api, models, fields, _
from odoo.exceptions import UserError, Warning


class ShipSendcloudWizard(models.TransientModel):
    _name = 'ship.sendcloud.wizard'

    def _get_default_requst(self):
        config = self.env['sendcloud.config'].search([], limit=1)
        return config.default_label_request

    no_label_request = fields.Integer(
       string="Label Request",
       default=_get_default_requst,
       help="Default=1, it means single shipment send single request to sendcloud,\
       if you select > 1 then multiple request would be generate on sendcloud \
       for same shipment,\nReason: Sendcloud does not support\
       multi labels for single shipment"
       )
#     send_email_to_customer = fields.Boolean(
#         "Would you like to send an email to customer with tracking number ?")

    @api.model
    def _check_validation(self):
        if not self.env.user.company_id.sendcloud_api_key:
            raise UserError(_('No SendCloud API Key missing, Kindly\
                put SendCloud API Key in Company Form'))
        if not self.env.user.company_id.sendcloud_secret_key:
            raise UserError(_('No SendCloud Secret Key missing, Kindly\
                put SendCloud Secret Key in Company Form'))
        if not self.no_label_request > 0:
            raise Warning(_('Label request should be > 0'))

    @api.model
    def _mapping_all_methods(self):
        """
            mapping shipping methods
        """
        config = self.env['sendcloud.config'].search([], limit=1)
        mapping = {}
        for map in config.mapping_ids:
            mapping[map.odoo_delivery_method_id.id] =\
                map.sendclould_shipping_method_id.shipping_id
        return mapping

    @api.multi
    def synchronize(self):
        self.ensure_one()
        record_ids = self._context.get('active_ids', []) or []
        config = self.env['sendcloud.config'].search([], limit=1)
        picking_rec = self.env['stock.picking'].browse(
           record_ids).filtered(lambda s: s.picking_type_code == 'outgoing')
        if not picking_rec:
            raise Warning(_('Only Outgoing picking \
                would be sync to sendcloud'))

        self._check_validation()
        mapping = self._mapping_all_methods()

        for pick in picking_rec:
            country = pick.partner_id.country_id
            if not pick.partner_id.sc_street_number:
                self._street_not_found_warning(pick.partner_id.name)
            if not country:
                self._country_not_found_warning(pick.partner_id.name)
            if not pick.carrier_id:
                self._carrier_not_found(pick.name)
            if not mapping.get(pick.carrier_id.id):
                self._carrier_not_mapped(pick.carrier_id.name)

        total_shipment_ids = []
        for pick in picking_rec:
            shipment_method_id = mapping.get(
                 pick.carrier_id.id,
                 False) or False
            if not shipment_method_id:
                self._carrier_not_mapped(pick.carrier_id.name)
            ship_ids = pick.sync_to_sendcloud(
                                   shipment_method_id,
                                   self.no_label_request,
                                   )
            if config.send_email_to_customer:
                pick.sendcloud_traking_email_to_customer()
            total_shipment_ids.extend(ship_ids)

        message = 'Shipment Ids %s successfully Synchronized To SendCloud.' % str(list(set(total_shipment_ids)))
        partial = self.env['sendcloud.wizard'].create({'text': message})
        return {
           'name': 'Information',
           'view_mode': 'form',
           'view_type': 'form',
           'res_model': 'sendcloud.wizard',
           'view_id': self.env.ref('sendcloud_integration.sendcloud_wizard_form').id,
           'res_id': partial.id,
           'type': 'ir.actions.act_window',
           'nodestroy': True,
           'target': 'new'
           }

    @api.model
    def _carrier_not_found(self, pick_name):
        raise Warning(_('Delivery method not found for'
                        ' picking(%s)!' % (pick_name, )))

    @api.model
    def _carrier_not_mapped(self, d_name):
        raise Warning(_('Mapping not found for Delivery method(%s)!\nPlease\
            navigate to Inventory > Sendcloud > Configuration, \
            then map odoo delivery method to sendcloud shipment \
             method' % (d_name,)))

    @api.model
    def _check_shipment_method(self):
        raise Warning(_('Please configure proper shipping method '
                        'from configuration menu, please go to \
                        Inventory > Sendcloud > Configuration,\
                        then set proper shipment method'))

    @api.model
    def _country_code_notin_warning(self, pick_name):
        raise Warning(_('Shipping method cannot allow \
                        customer country code for(%s), please go \
                        Inventory > Sendcloud > Configuration,\
                        add customer country to related shipment method'
                        % (pick_name,)))

    @api.model
    def _country_not_found_warning(self, partner_name):
        raise Warning(_('No customer country found for(%s)' % (partner_name,)
                        ))

    @api.model
    def _street_not_found_warning(self, partner_name):
        raise Warning(_('Please mention house no on customer(%s) \
                        address.\n Please go to customer form \
                        then update house no.' % (partner_name,)
                        ))
