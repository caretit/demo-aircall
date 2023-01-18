# -*- coding: utf-8 -*-
##############################################################################
#
# Part of Caret IT Solutions Pvt. Ltd. (Website: www.caretit.com).
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    number_config_ids = fields.Many2many(
        "number.number",
        string="Numbers",
    )
