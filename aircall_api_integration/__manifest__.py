# -*- coding: utf-8 -*-
##############################################################################
#
# Part of Caret IT Solutions Pvt. Ltd. (Website: www.caretit.com).
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

{
    'name': 'Aircall API Integration',
    'version': '16.0.0.1',
    'license': 'OPL-1',
    'summary': """
        Aircall API Integration, it will sync contacts, call log activities
        and make click to dial and insight cards view.
    """,
    'category': 'CRM',
    'description': """
        Aircall API Integration, it will sync contacts, call log activities
        and make click to dial and insight cards view.
    """,
    'author': 'Caret IT Solutions Pvt. Ltd.',
    'website': 'http://www.caretit.com',
    'depends': ['web', 'crm', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_jobs_data.xml',
        'views/number_views.xml',
        'views/res_company_view.xml',
        'views/res_config_settings_view.xml',
        'views/res_partner_view.xml',
        'views/mail_message_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'aircall_api_integration/static/src/js/aircallPhone.js',
            'aircall_api_integration/static/src/js/aircall.js',
            'aircall_api_integration/static/src/js/aircall_dial.js',
            ('include', 'aircall_api_integration.assets_frontend'),
            
        ],
        'aircall_api_integration.assets_frontend': [
            ('include', 'web._assets_helpers'),
            'aircall_api_integration/static/src/xml/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'price': 299.00,
    'currency': 'USD',
}
