# -*- coding: utf-8 -*-
from odoo import fields, models # type: ignore


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_type_intervenant = fields.Selection([
            ('consultant'   , 'Consultant'),
            ('co-traitant'  , 'Co-traitant'),
            ('sous-traitant', 'Sous-Traitant'),
        ], "Type d'intervenant",)
    is_consultant_id = fields.Many2one('res.users', "Utilisateur associé")
    is_code_analytique = fields.Char("Code analytique")

