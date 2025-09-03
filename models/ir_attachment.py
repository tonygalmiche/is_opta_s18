# -*- coding: utf-8 -*-
from odoo import api, fields, models  # type: ignore
from odoo.exceptions import AccessError  # type: ignore



# class IrAttachment(models.Model):
#     _inherit = 'ir.attachment'

#     # Relation indirecte: pièces jointes référencées par les frais via la table M2M
#     # Ce champ permet d’écrire une règle d’accès simple et sûre, sans surcharger la logique d’Odoo.
#     is_frais_ids = fields.Many2many(
#         comodel_name='is.frais',
#         relation='is_frais_justificatif_rel',
#         column1='file_id',  # colonne ir.attachment dans la table M2M
#         column2='doc_id',   # colonne is.frais dans la table M2M
#         string='Fiches Frais liées',
#         readonly=True,
#     )


