# -*- coding: utf-8 -*-
##############################################################################
#
# Part of Caret IT Solutions Pvt. Ltd. (Website: www.caretit.com).
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

import time
import datetime
import logging
import requests
import urllib3
import phonenumbers
from odoo.http import request
from odoo import api, models

_logger = logging.getLogger(__name__)

AIRCALL_API_URL = 'https://api.aircall.io/v1'


class AircallWebhook(models.TransientModel):
    _name = 'aircall.webhook'
    _description = 'Aircall Webhook'

    @api.model
    def validate_webhook_token(self, token):
        """ Method for validate the aircall webhook token. """
        true_token = self.env['ir.config_parameter'].sudo(
            ).get_param('aircall_api_integration.default_aircall_integration_token')
        if true_token is False:
            _logger.warning(
                'Aircall integration token has not been set. Webhooks cannot work without it.')
        return true_token == token

    @api.model
    def get_aircall_api_config(self):
        """ Will throw an error if the config is not set """
        sudo_param = self.sudo().env['ir.config_parameter']
        return sudo_param.get_param(
            'aircall_api_integration.default_api_id'), sudo_param.get_param(
            'aircall_api_integration.default_api_token')

    @api.model
    def register(self, payload):
        """ Method where all webhook events are defined. """
        register_map = {
            'call.created': self._send_insight_card,
            'call.ended': self._register_call,
            'call.commented': self._register_call,
            'contact.created': self._register_contact,
        }
        try:
            method = register_map[payload['event']]
        except KeyError:
            _logger.warning(
                'An unimplemented webhook of type [{}] has been received. Uncheck it in aircall dashboard.'.format(
                    payload['event']))
            return
        method(payload)

    @api.model
    def _register_call(self, payload):
        """ Method called when the call event is performed. """
        _logger.warning(payload)
        assert payload['resource'] == 'call'
        data = payload['data']
        talk_time, waiting_time = 0, 0
        started_at = datetime.datetime.utcfromtimestamp(int(data['started_at']))
        comments, conf_num = [], []
        recording = False
        company = request.env.company
        number = data['number']

        if company.number_config_ids:
            _logger.warning(company.number_config_ids)
            num_search = self.env['number.number'].sudo().search([('id', 'in', company.number_config_ids.ids)])
            _logger.warning(num_search)
            for num in num_search:
                if str(num.number_id) == str(number['id']) and str(num.digits) == str(number['digits']):
                    conf_num.append(num)
        
        _logger.warning(conf_num)
        if conf_num:
            if data['recording'] and data['asset']:
                recording = self._create_audio_attachment(
                    data['asset'], 'recording_' + str(started_at.date()))
            for comment in data['comments']:
                comments.append('\n{}'.format(comment['content']))
            tags = []
            for tag in data['tags']:
                tags.append('\n{}'.format(tag['name']))
            external_entity_id = self.env['res.partner'].sudo().search(
                [('phone', 'ilike', data['raw_digits']),('is_company','=',True)], limit=1)
            if not external_entity_id:
                external_entity_id = self.env['res.partner'].sudo().search(
                    [('phone', 'ilike', data['raw_digits'])], limit=1)
            tags = '\n'.join(tags)

            if external_entity_id:
                if data['answered_at']:
                    talk_time = time.strftime('%H:%M:%S', time.gmtime(
                        data['ended_at'] - data['answered_at']))
                    waiting_time = time.strftime(
                        '%H:%M:%S', time.gmtime(data['answered_at'] - data['started_at']))
                check_msg = self.env['mail.message'].sudo().search(
                    [('aircall_call_id', '=', data['id'])], limit=1)
                message = """
                    Call ID: %s <br/>\n
                    Number: %s <br/>\n
                    Call Qualification: %s , User: %s <br/>\n
                    Call Duration: %s <br/>\n
                    Waiting Time: %s <br/>\n
                    Talk Time: %s <br/>\n
                    Tags: %s <br/>\n
                    Comments: %s <br/>\n
                    """ % (data['id'], external_entity_id.phone, data["direction"], data['user']['name'], time.strftime(
                        '%H:%M:%S', time.gmtime(data['duration'])), waiting_time, talk_time, tags, "\n".join(comments))
                _logger.warning(message)
                lead = self.env['crm.lead'].sudo().search([
                    ('partner_id', '=', external_entity_id.id)], order='id desc', limit=1)
                if lead and not self.env['mail.message'].sudo().search([
                    ('model', '=', 'crm.lead'), ('aircall_call_id', '=', data['id'])], limit=1):
                    lead_data = lead.sudo().message_post(body=message)
                    if lead_data:
                        lead_data.aircall_call_id = data['id']

                if not check_msg:
                    mail_data = external_entity_id.sudo().message_post(body=message)
                    if mail_data:
                        mail_data.aircall_call_id = data['id']
                        mail_data.recording_attachment_id = recording
                        if recording:
                            external_entity_id.recording_attachment_ids = [(4, recording)]
                else:
                    if not check_msg.recording_attachment_id and recording:
                        check_msg.recording_attachment_id = recording
                        external_entity_id.recording_attachment_ids = [(4, recording)]

    @api.model
    def _send_insight_card(self, payload):
        """ Method for sending the insight card """
        api_id, api_token = self.get_aircall_api_config()
        if False in [api_id, api_token]:
            _logger.warning(
                "Aircall api credentials are not set. Some features won't work")
            return
        json_field = self._populate_insight_card(payload['data'])
        if json_field is False:
            # Callee was not found on the system on the system
            return
        aircall_url = AIRCALL_API_URL + "/calls/" + \
            str(payload['data']['id']) + "/insight_cards"
        requests.post(aircall_url, auth=(
            api_id, api_token), json=json_field)

    @api.model
    def _populate_insight_card(self, data):
        """ Method for populate the insight card to the current call. """
        partner = self.env['res.partner'].sudo().search(
            [('phone', 'ilike', data['raw_digits']),('is_company','=',True)], limit=1)
        if not partner:
            partner = self.env['res.partner'].sudo().search(
                [('phone', 'ilike', data['raw_digits'])], limit=1)
        if partner.id is False:
            return False

        base_url = self.env['ir.config_parameter'].sudo(
            ).get_param('web.base.url')
        params = {
            'id': partner.id,
            'model': 'res.partner',
            'view_type': 'form',
            'menu_id': self.env['ir.ui.menu'].sudo().search(
                [('name', '=', 'Contacts')], limit=1).id
        }
        json_field = {'contents': [
            {
                'type': 'title',
                'text': 'Odoo',
                'link': base_url,
            },
            {
                'type': 'shortText',
                'label': 'Odoo Contact',
                'text': partner.name,
                'link': base_url + '#' + urllib3.request.urlencode(params),
            }
        ]}
        # Add company line if it is set on the partner
        if partner.company_type == 'person' and partner.parent_id != False:
            json_field['contents'].append({
                'type': 'shortText',
                'label': 'Company name',
                'text': partner.parent_id.name
            })
        # Add Lead/Opportunity if it is related to partner
        leads = self.env['crm.lead'].sudo().search([
            ('partner_id', '=', partner.id)])
        if leads and len(leads) == 1:
            kwargs = {
                'id': leads.id,
                'model': 'crm.lead',
                'view_type': 'form',
                'menu_id': self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'Pipeline')], limit=1).id
            }
            json_field['contents'].append({
                'type': 'shortText',
                'label': 'Leads/Opportunities',
                'text': leads.name,
                'link': base_url + '#' + urllib3.request.urlencode(kwargs),
            })
        else:
            kwargs = {
                'model': 'crm.lead',
                'view_type': 'kanban',
                'action': self.env['ir.actions.actions']._for_xml_id(
                    'crm.crm_lead_opportunities')['id'],
                'menu_id': self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'Pipeline')], limit=1).id
            }
            json_field['contents'].append({
                'type': 'shortText',
                'label': 'Leads/Opportunities',
                'text': 'Leads/Opportunities of %s' % (partner.name),
                'link': base_url + '#' + urllib3.request.urlencode(kwargs),
            })
        _logger.warning(json_field)
        return json_field

    @api.model
    def _create_audio_attachment(self, url, filename):
        """ Method for create audio attachment. """
        if self._dl_audio(url):
            return self.env['ir.attachment'].sudo().create({
                'name': filename,
                'type': 'url',
                'url': url,
                'mimetype': 'audio/mpeg'
            }).id
        return False

    @staticmethod
    def _dl_audio(url):  # utils method
        """ Method for create audio. """
        re = requests.get(url)
        if re.status_code != requests.codes.ok:
            _logger.warning(
                'Could not reach URL [{}] to download audio'.format(url))
            return False
        return re.content

    @api.model
    def _register_contact(self, payload):
        """ Method called when contact is created in aircall. """
        _logger.warning(payload)
        phone_format = ''
        res_partner = self.env['res.partner']
        phone_details = self.env['phone.details']
        email_details = self.env['email.details']
        contact = payload['data']
        company = False
        if contact['phone_numbers']:
            phone = phonenumbers.parse(contact['phone_numbers'][0]['value'])
            phone_format = phonenumbers.format_number(
                phone, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        partner = res_partner.sudo().search([
            ('name', '=', contact['first_name']),
            ('last_name', '=', contact['last_name']),
            ('phone', '=', phone_format)
        ])
        if not partner:
            if contact['company_name']:
                company = res_partner.sudo().search(
                    [('name', '=', contact['company_name'])], limit=1)
                if not company:
                    company = res_partner.sudo().create({
                        'name': contact['company_name'],
                        'company_type': 'company',
                        'is_company': True,
                        'aircall_id': contact['id']
                    })
            partner = res_partner.sudo().create({
                'name': contact['first_name'],
                'last_name': contact['last_name'] or '',
                'comment': contact['information'],
                'phone': phone_format if contact['phone_numbers'] else '',
                'email': contact['emails'][0]['value'] if contact['emails'] else '',
                'parent_id': company and company.id or False,
                'aircall_id': contact['id'],
                'direct_link': contact['direct_link'],
                'is_shared': contact['is_shared'],
            })
            for phone in contact['phone_numbers']:
                phone_details.sudo().create({
                    'phone_id': phone['id'],
                    'label': phone['label'],
                    'value': phone['value'],
                    'partner_id': partner.id,
                })
            for email in contact['emails']:
                email_details.sudo().create({
                    'email_id': email['id'],
                    'label': email['label'],
                    'value': email['value'],
                    'partner_id': partner.id,
                })
