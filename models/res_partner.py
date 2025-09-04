# -*- coding: utf-8 -*-
from odoo import api, fields, models  # type: ignore


class IsTypeSociete(models.Model):
    _name = 'is.type.societe'
    _description = "Type de société"
    _order = 'name'

    name = fields.Char("Type de société", required=True, index=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_type_societe_id              = fields.Many2one('is.type.societe', 'Type de société', tracking=True)
    is_compte_auxilaire_client      = fields.Char("Compte auxilaire client", tracking=True)
    is_compte_auxilaire_fournisseur = fields.Char("Compte auxilaire fournisseur", tracking=True)
    is_dynacase_ids                 = fields.Many2many('is.dynacase', 'res_partner_dynacase_rel', 'doc_id', 'dynacase_id', 'Ids Dynacase', readonly=True)
    is_evaluation = fields.Selection([
            ('tres_satisfaisant','Très satisfaisant'),
            ('satisfaisant'     ,'Satisfaisant'),
            ('a_surveiller'     ,'A surveiller'),
        ], string='Évaluation', tracking=True)
    customer = fields.Boolean("Client"     , default=True, tracking=True)
    supplier = fields.Boolean("Fournisseur", default=False, tracking=True)

    is_secteur_id  = fields.Many2one('is.secteur', "Secteur", help="Secteur ou Type de politique publique", tracking=True)
    is_code_client = fields.Char("Code client", tracking=True)
