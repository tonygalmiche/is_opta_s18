# -*- coding: utf-8 -*-
from odoo import models,fields,tools     # type: ignore


class IsAffaireVendueParView(models.Model):
    _name = 'is.affaire.vendue.par.view'
    _description = "Affaire vendue par"
    _order='date_creation desc'
    _auto = False


    affaire_id              = fields.Many2one('is.affaire', 'Affaire')
    partner_id              = fields.Many2one('res.partner', "Client")
    type_intervention_id    = fields.Many2one('is.type.intervention', "Type d'intervention")
    secteur_id              = fields.Many2one('is.secteur', "Secteur")
    type_offre_id           = fields.Many2one('is.type.offre', "Type d'offre")
    date_creation           = fields.Date("Date de création")
    annee_creation          = fields.Char("Année")
    createur_id             = fields.Many2one('res.users', "Créateur")
    cause_id                = fields.Many2one('is.cause', "Cause si offre perdue")
    responsable_id          = fields.Many2one('res.users', "Responsable de l'affaire")
    state                   = fields.Selection([
            ('offre_en_cours', 'Offre en cours'),
            ('affaire_gagnee', 'Affaire gagnée'),
            ('affaire_soldee', 'Affaire soldée'),
            ('offre_perdue'  , 'Offre perdue')
        ], u"État")
    user_id                 = fields.Many2one('res.users', "Affaire vendue par")
    login                   = fields.Char("Vendue par")
    repartition             = fields.Integer("% répartition CA vendu")
    ca_previsionnel_reparti = fields.Float("CA vendu", digits=(14,2))
    commentaire             = fields.Char("Commentaire")


    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(cr, 'is_affaire_vendue_par_view')
        cr.execute("""
            CREATE OR REPLACE view is_affaire_vendue_par_view AS (
                select
                    iavp.id,
                    iavp.affaire_id,
                    ia.partner_id,
                    ia.type_intervention_id,
                    ia.secteur_id,
                    ia.type_offre_id,
                    ia.date_creation,
                    ia.annee_creation,
                    ia.createur_id,
                    ia.cause_id,
                    ia.responsable_id,
                    ia.state,
                    iavp.user_id,
                    ru.login,
                    iavp.repartition,
                    (ia.ca_previsionnel*iavp.repartition/100) ca_previsionnel_reparti,
                    iavp.commentaire
                from is_affaire ia inner join is_affaire_vendue_par iavp on iavp.affaire_id=ia.id
                                   left outer join res_users ru on iavp.user_id=ru.id
            )
        """)

