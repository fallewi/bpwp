# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

from odoo import fields, models


class SendcloudWizard(models.TransientModel):
    _name = 'sendcloud.wizard'

    text = fields.Text(string='Message', readonly=True, translate=True)
