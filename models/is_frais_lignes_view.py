# -*- coding: utf-8 -*-
from odoo import models,fields,tools     # type: ignore


class IsFraisLignesView(models.Model):
    _description = "Lignes des frais"
    _name = 'is.frais.lignes.view'
    _order='id desc'
    _auto = False


    chrono           = fields.Char("Chrono", readonly=True, index=True)
    chrono_long      = fields.Char("Chrono long", compute='compute_chrono', readonly=True, store=True)
    createur_id      = fields.Many2one('res.users', "Créateur", required=True, default=lambda self: self.env.user)
    login            = fields.Char("Login" , compute='compute_chrono', readonly=True, store=True)
    date_creation    = fields.Date("Date de création", required=True, index=True, default=lambda *a: fields.Date.today())
    mois_creation    = fields.Char("Mois" , compute='compute_chrono', readonly=True, store=True)
    annee_creation   = fields.Char("Année", compute='compute_chrono', readonly=True, store=True)
    affaire_id       = fields.Many2one('is.affaire' , 'Affaire' , required=False)
    activite_id      = fields.Many2one('is.activite', 'Activite', required=True)
    type_activite    = fields.Selection([
            ('formation', u'Formation'),
            ('conseil'  , u'Conseil'),
            ('divers'   , u'Divers'),
        ], u"Type d'activité", index=True, required=True)
    state = fields.Selection([
            ('brouillon', u'Brouillon'),
            ('diffuse'  , u'Diffusé'),
            ('valide'   , u'Validé'),
        ], u"État", index=True, default='brouillon')


    partner_id         = fields.Many2one('res.partner', 'Fournisseur') # domain=[('supplier','=',True),('is_company','=',True)])
    product_id         = fields.Many2one('product.product', 'Type de dépense', required=True) #, domain=[('is_type_intervenant','=',False)])
    effectuee_par_id   = fields.Many2one('is.depense.effectuee.par', 'Dépense effectuée par', required=True)
    montant_ttc        = fields.Float("Montant"                , digits='Product Price')
    montant_tva        = fields.Float("Montant TVA récupérable", digits='Product Price')
    refacturable       = fields.Selection([
            ('oui', u'Oui'),
            ('non', u'Non'),
        ], u"Refacturable", index=True, default='non')
    commentaire        = fields.Text("Commentaire")
    justificatif_joint = fields.Selection([
            ('oui', u'Oui'),
            ('non', u'Non'),
        ], u"Justificatif joint", index=True, default='oui')

    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(cr, 'is_frais_lignes_view')
        cr.execute("""
            CREATE OR REPLACE view is_frais_lignes_view AS (
                select
                    ifl.id,
                    if.chrono,
                    if.chrono_long,
                    if.createur_id,
                    if.login,
                    if.date_creation,
                    if.mois_creation,
                    if.annee_creation,
                    if.affaire_id,
                    if.activite_id,
                    if.type_activite,
                    if.state,
                    ifl.partner_id,
                    ifl.product_id,
                    ifl.effectuee_par_id,
                    ifl.montant_ttc,
                    ifl.montant_tva,
                    ifl.refacturable,
                    ifl.commentaire,
                    ifl.justificatif_joint
                from is_frais if inner join is_frais_lignes ifl on ifl.frais_id=if.id
            )
        """)

