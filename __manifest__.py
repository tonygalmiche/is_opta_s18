# -*- coding: utf-8 -*-
{
    'name'     : 'InfoSaône - Module Odoo 18 pour Opta-S / SGP',
    'version'  : '0.1',
    'author'   : 'InfoSaône',
    'category' : 'InfoSaône',
    'description': """
InfoSaône - Module Odoo 18 pour Opta-S / SGP 
===================================================
""",
    'maintainer' : 'InfoSaône',
    'website'    : 'http://www.infosaone.com',
    'depends'    : [
        'base',
        'account',
        'l10n_fr',
        'l10n_fr_account',
        'mail',
        'web_chatter_position',
    ],
    'data' : [
        'security/res.groups.xml',
        'security/ir.model.access.csv',
        'security/ir.model.access.xml',
        'views/res_company_views.xml',
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
        'views/product_views.xml',
        'views/is_affaire_views.xml',
        'views/is_affaire_vendue_par_view_views.xml',
        'views/is_activite_views.xml',
        'views/is_suivi_temps_views.xml',
        'views/is_frais_views.xml',
        'views/is_frais_lignes_view_views.xml',
        'views/account_invoice_view.xml',
        'views/is_activite_suivi_temps_views.xml',
        'views/is_export_compta_view.xml',
        'views/is_export_compta_ana_view.xml',
        'views/is_affaire_activite_views.xml',
        # 'views/is_invoice_activite_views.xml',
        'views/is_facture_st_views.xml',
        'views/is_suivi_production_affaire.xml',
        # 'views/is_google_agenda_view.xml',
        'views/menu.xml',
        # 'report/report_templates.xml',
        # 'report/report_invoice.xml',
    ],
    "assets": {
        'web.assets_backend': [
            'is_opta_s18/static/src/**/*',
         ],
        # 'web.report_assets_common': [
        #     'is_plastigray16/static/src/scss/plastigray_report.scss',
        # ]
    },
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
}
