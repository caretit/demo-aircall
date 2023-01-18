# -*- coding: utf-8 -*-
##############################################################################
#
# Part of Caret IT Solutions Pvt. Ltd. (Website: www.caretit.com).
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

from odoo import fields, models, api
from odoo.exceptions import ValidationError
import phonenumbers


class ResPartner(models.Model):
    _inherit = 'res.partner'

    synced_to_aircall = fields.Boolean(string='Synced to Aircall')
    last_name = fields.Char(string='Last Name', required=True)
    aircall_id = fields.Char(string='Aircall ID')
    direct_link = fields.Char(string='Direct Link')
    is_shared = fields.Boolean(string='Is Shared')
    is_log_send = fields.Boolean(string='Is Log Send')
    phone_details_ids = fields.One2many(
        'phone.details', 'partner_id', string='Phone Details')
    email_details_ids = fields.One2many(
        'email.details', 'partner_id', string='Email Details')
    recording_attachment_ids =fields.Many2many(
        'ir.attachment', 'res_partner_attachment_rel', 'pid', 'attachment_id',
        string='Audio Recording', readonly=True)

    def write(self, vals):
        """ Write method for set the phone number in valid format. """
        if 'phone' in vals and vals['phone']:
            try:
                phone = phonenumbers.parse(vals['phone'])
                phone_format = phonenumbers.format_number(
                    phone, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                vals['phone'] = phone_format
            except Exception as e:
                return False
        return super(ResPartner, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """ Create method for set the phone number in valid format. """
        for vals in vals_list:
            if 'phone' in vals and vals['phone']:
                try:
                    vals['phone'] = phonenumbers.format_number(
                        phonenumbers.parse(vals['phone']),
                        phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                except Exception as e:
                    raise ValidationError("Phone field must have correct value/country code/region")
        return super(ResPartner, self).create(vals_list)
