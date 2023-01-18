# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of Caret IT Solutions Pvt. Ltd. (Website: www.caretit.com).           #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

import logging
from odoo import models
from odoo.addons.aircall_api_integration.models.authorization import AuthorizeAircallApi

_logger = logging.getLogger(__name__)


class AircallConnection(models.Model):
    _name = 'aircall.connection'
    _description = 'Aircall Connection'

    def get_contact_values(self, partner):
        """ Method for get contact value. """
        return {
            'id': partner.id,
            'first_name': partner.name,
            'last_name': partner.last_name,
            'information': 'external_custom_id:%s'%(partner.id),
            'phone_numbers': [{
                'label': 'Work',
                'value': partner.phone,
            }],
            'emails': [{
                'label': 'Office',
                'value': partner.email,
            }]
        }

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

    def post_contacts(self):
        """ Method for post contact from odoo to aircall. """
        auth, url, api_id, api_token = self.get_aircall_auth()
        if auth and auth.json():
            partners = self.env['res.partner'].sudo().search(
                [('synced_to_aircall', '=', False), ('aircall_id', '=', False)])
            for partner in partners:
                contacts = AuthorizeAircallApi(url, api_id, api_token).post_contacts(
                    self.get_contact_values(partner))
                _logger.warning(contacts.json())
                if contacts and contacts.json():
                    partner.synced_to_aircall = True
                    partner.message_post(
                        body='Contact is synced to Aircall successfully.')
                else:
                    if not partner.is_log_send:
                        partner.message_post(
                            body='Contact is not synced to the Aircall due to this error, %s' % (
                            contacts.json()['troubleshoot']))
                        partner.is_log_send = True
