# -*- coding: utf-8 -*-
##############################################################################
#
# Part of Caret IT Solutions Pvt. Ltd. (Website: www.caretit.com).
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

import logging
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.aircall_api_integration.models.authorization import AuthorizeAircallApi

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    aircall_auth = fields.Boolean(default=True,
        config_parameter='aircall_api_integration.default_aircall_auth')
    api_url = fields.Char(string='URL', default='https://api.aircall.io',
        config_parameter='aircall_api_integration.default_api_url')
    api_id = fields.Char(string='API ID', default='dummy',
        config_parameter='aircall_api_integration.default_api_id')
    api_token = fields.Char(string='API Token', default='dummy',
        config_parameter='aircall_api_integration.default_api_token')
    aircall_integration_token = fields.Char(string='Aircall Integration Token', default='dummy',
        config_parameter='aircall_api_integration.default_aircall_integration_token')
    number_config_ids = fields.Many2many(
        "number.number", string="Numbers",
        related='company_id.number_config_ids', readonly=False)

    def get_aircall_config(self):
        """ Method for get aircall configuration. """
        get_param = self.env['ir.config_parameter'].sudo().get_param
        return {
            'aircall_auth': get_param('aircall_api_integration.default_aircall_auth'),
            'api_url': get_param('aircall_api_integration.default_api_url'),
            'api_id': get_param('aircall_api_integration.default_api_id'),
            'api_token': get_param('aircall_api_integration.default_api_token'),
            'aircall_integration_token': get_param(
                'aircall_api_integration.default_aircall_integration_token'),
        }

    def set_aircall_config(self):
        """ Method for set aircall configuration. """
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('aircall_api_integration.default_aircall_auth', self.aircall_auth)
        set_param('aircall_api_integration.default_api_url', self.api_url)
        set_param('aircall_api_integration.default_api_id', self.api_id)
        set_param('aircall_api_integration.default_api_token', self.api_token)
        set_param('aircall_api_integration.default_aircall_integration_token',
                  self.aircall_integration_token)

    def get_aircall_auth(self):
        """ Method for get authentication values. """
        get_param = self.env['ir.config_parameter'].sudo().get_param
        url = get_param('aircall_api_integration.default_api_url', default='https://api.aircall.io')
        api_id = get_param('aircall_api_integration.default_api_id', default='dummy')
        api_token = get_param('aircall_api_integration.default_api_token', default='dummy')
        auth = False
        if get_param('aircall_api_integration.aircall_auth', default=True):
            auth = AuthorizeAircallApi(url, api_id, api_token).get_authentication()
        return auth, url, api_id, api_token

    def create_number(self, NumObj, number):
        '''Create Number's record'''
        return NumObj.create({
            'number_id': number['id'],
            'name': number['name'],
            'direct_link': number['direct_link'],
            'digits': number['digits'],
            'country': number['country'],
            'tz': number['time_zone'],
            'open_status': number['open'],
            'availability_status': number['availability_status'],
            'priority': number['priority'] and str(number['priority']) or 'null',
            'is_ivr': number['is_ivr'],
            'live_recording_activated': number['live_recording_activated'],
        })

    def fetch_numbers(self):
        """ Method for fetch numbers from aircall to odoo. """
        auth, url, api_id, api_token = self.get_aircall_auth()
        NumObj = self.env['number.number']
        num_list = []
        if auth and auth.json():
            numbers = AuthorizeAircallApi(url, api_id, api_token).get_numbers()
            count = 0
            for number_data in numbers:
                for number in number_data.json()['numbers']:
                    count = count + 1
                    exist_num = NumObj.search([
                        ('number_id', '=', number['id']), ('digits', '=', number['digits'])])
                    if not exist_num:
                        num_list.append(self.create_number(NumObj, number).id)
                    else:
                        num_list.append(exist_num.id)
                    if num_list:
                        self.company_id.write(
                            {'number_config_ids': [(6, 0, num_list)]})
        elif auth.json() and auth.json().get('error'):
            raise ValidationError(_('Please %s', (auth.json().get('troubleshoot'))))
