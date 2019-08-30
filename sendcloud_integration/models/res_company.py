# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    sendcloud_api_key = fields.Char(string='API Key')
    sendcloud_secret_key = fields.Char(string='Secret Key')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sc_street_number = fields.Char(string='House No.')
