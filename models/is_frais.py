# -*- coding: utf-8 -*-
from odoo import api, fields, models, _          # type: ignore
from odoo.exceptions import ValidationError      # type: ignore
from odoo.addons import decimal_precision as dp  # type: ignore


class IsDepenseEffectueePar(models.Model):
    _name = 'is.depense.effectuee.par'
    _description = "Dépense effectuée par"
    _order = 'name'

    name = fields.Char("Dépense effectuée par", required=True, index=True)


class IsFraisLigne(models.Model):
    _name = 'is.frais.lignes'
    _description = "Frais"
    _order = 'id'

    frais_id           = fields.Many2one('is.frais', 'Frais', required=True, ondelete='cascade')
    partner_id         = fields.Many2one('res.partner', 'Fournisseur', domain=[('supplier','=',True),('is_company','=',True)])
    product_id         = fields.Many2one('product.product', 'Type de dépense', required=True, domain=[('is_type_intervenant','=',False)])
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

    def copie_frais_action(self):
        for obj in self:
            obj.copy()

    @api.onchange('partner_id')
    def onchange_partner_idd(self):
        product_id = False
        if self.partner_id:
            product_id = self.partner_id.is_type_depense_id.id
        self.product_id = product_id


class IsFrais(models.Model):
    _name = 'is.frais'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Frais"
    _order = 'date_creation desc'
    _rec_name = 'rec_name'


    @api.depends('date_creation','createur_id','chrono')
    def compute_chrono(self):
        for obj in self:
            if obj.date_creation:
                obj.mois_creation  = str(obj.date_creation)[:7]
                obj.annee_creation = str(obj.date_creation)[:4]
            if obj.createur_id and obj.createur_id.is_initiales:
                obj.login=obj.createur_id.is_initiales.upper()
            obj.chrono_long=(obj.login or '')+'-'+(obj.mois_creation or '')+'-'+(obj.chrono or '')


    @api.depends('ligne_ids','nb_jours','montant_forfait','frais_forfait')
    def _compute_total(self):
        for obj in self:
            total_consultant      = 0
            total_refacturable = 0
            if obj.frais_forfait:
                total_refacturable = obj.nb_jours*obj.montant_forfait
            total_frais           = 0
            total_tva_recuperable = 0
            for l in obj.ligne_ids:
                if l.effectuee_par_id.name=='CONSULTANT':
                    total_consultant      += l.montant_ttc
                if l.refacturable=='oui':
                    total_refacturable    += l.montant_ttc
                total_frais           += l.montant_ttc
                total_tva_recuperable += l.montant_tva
            obj.total_consultant      = total_consultant
            obj.total_refacturable    = total_refacturable
            obj.total_frais           = total_frais
            obj.total_tva_recuperable = total_tva_recuperable


    @api.onchange('forfait_jour_id')
    def onchange_product(self):
        if self.forfait_jour_id:
            self.montant_forfait = self.forfait_jour_id.montant


    chrono           = fields.Char("Chrono", readonly=True, index=True,tracking=True)
    chrono_long      = fields.Char("Chrono long", compute='compute_chrono', readonly=True, store=True,tracking=True)
    createur_id      = fields.Many2one('res.users', "Créateur", required=True, default=lambda self: self.env.user,tracking=True)
    login            = fields.Char("Login" , compute='compute_chrono', readonly=True, store=True)
    date_creation    = fields.Date("Date de création", required=True, index=True, default=lambda *a: fields.Date.today(),tracking=True)
    mois_creation    = fields.Char("Mois" , compute='compute_chrono', readonly=True, store=True,tracking=True)
    annee_creation   = fields.Char("Année", compute='compute_chrono', readonly=True, store=True,tracking=True)
    affaire_id       = fields.Many2one('is.affaire' , 'Affaire' , required=False,tracking=True)
    activite_id      = fields.Many2one('is.activite', 'Activite', required=True,tracking=True)
    type_activite    = fields.Selection([
            ('formation', u'Formation'),
            ('conseil'  , u'Conseil'),
            ('divers'   , u'Divers'),
        ], u"Type d'activité", index=True, required=True,tracking=True)
    frais_forfait    = fields.Boolean("Frais au forfait",default=False,tracking=True)
    nb_jours         = fields.Float("Nb jours (si frais au forfait)", digits=(14,2),tracking=True)
    forfait_jour_id  = fields.Many2one('is.affaire.forfait.jour', "Forfait jour de l'affaire",tracking=True)
    montant_forfait  = fields.Float("Montant forfait", digits=(14,2),tracking=True)
    parcours         = fields.Text("Parcours",tracking=True)
    dates            = fields.Char("Dates",tracking=True)
    ligne_ids        = fields.One2many('is.frais.lignes', 'frais_id', u'Lignes')
    justificatif_ids = fields.Many2many('ir.attachment', 'is_frais_justificatif_rel', 'doc_id', 'file_id', 'Justificatifs')
    total_consultant      = fields.Float("Total TTC Consultant à rembourser", digits=(14,2), compute='_compute_total', readonly=True, store=True,tracking=True)
    total_refacturable    = fields.Float("Total TTC refacturable"           , digits=(14,2), compute='_compute_total', readonly=True, store=True,tracking=True)
    total_frais           = fields.Float("Total TTC de tous les frais"      , digits=(14,2), compute='_compute_total', readonly=True, store=True,tracking=True)
    total_tva_recuperable = fields.Float("Total TVA récupérable"            , digits=(14,2), compute='_compute_total', readonly=True, store=True,tracking=True)
    state = fields.Selection([
            ('brouillon', u'Brouillon'),
            ('diffuse'  , u'Diffusé'),
            ('valide'   , u'Validé'),
        ], u"État", index=True, default='brouillon',tracking=True)
    is_dynacase_ids = fields.Many2many('is.dynacase', 'is_frais_dynacase_rel', 'doc_id', 'dynacase_id', 'Ids Dynacase', readonly=True)
    rec_name = fields.Char("Nom du document", compute='_compute_rec_name', readonly=True, store=True,tracking=True)


    @api.depends('login','mois_creation','chrono')
    def _compute_rec_name(self):
        for obj in self:
            name = '%s-%s-%s'%(obj.login,obj.mois_creation,obj.chrono)
            obj.rec_name = name


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'activite_id' in vals:
                activite_id=vals['activite_id']
                affaire_id=self.env['is.activite'].browse(activite_id).affaire_id.id
                vals['affaire_id']=affaire_id
            vals['chrono'] = self.env['ir.sequence'].next_by_code('is.frais')
        records = super().create(vals_list)
        # Lier les PJ aux enregistrements créés
        #records._link_justificatifs_to_record()
        return records

    # def write(self, vals):
    #     res = super().write(vals)
    #     # À chaque modification, s'assurer que les PJ sont correctement liées
    #     self._link_justificatifs_to_record()
    #     return res

    # def _link_justificatifs_to_record(self):
    #     """Force res_model/res_id sur les pièces jointes de justificatifs."""
    #     for rec in self:
    #         atts = rec.justificatif_ids.sudo().filtered(lambda a: a.res_id != rec.id or a.res_model != rec._name)
    #         for att in atts:
    #             att.write({'res_model': rec._name, 'res_id': rec.id})

    # def action_backfill_justificatifs_links(self):
    #     """Action utilitaire: corrige toutes les PJ existantes des frais."""
    #     self.sudo().search([])._link_justificatifs_to_record()


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        ids = []
        if name:
            ids = self._search(['|','|',('login', 'ilike', name),('mois_creation', 'ilike', name),('chrono', 'ilike', name)] + args, limit=limit, access_rights_uid=name_get_uid)
        else:
            ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(ids).name_get()


    def envoi_mail(self, email_from,email_to,subject,body_html):
        for obj in self:
            vals={
                'email_from'    : email_from, 
                'email_to'      : email_to, 
                'subject'       : subject,
                'body'          : body_html, 
                'body_html'     : body_html, 
                'model'         : self._name,
                'res_id'        : obj.id,
                # 'notification'  : True,
                'message_type'  : 'comment',
            }
            email=self.env['mail.mail'].create(vals)
            if email:
                self.env['mail.mail'].send(email)


    def creer_notification(self, subject):
        for obj in self:
            vals={
                'subject'       : subject,
                'body'          : subject, 
                'body_html'     : subject, 
                'model'         : self._name,
                'res_id'        : obj.id,
                #'notification'  : True,
                'message_type'  : 'comment',
            }
            email=self.env['mail.mail'].create(vals)


    def vers_diffuse(self):
        for obj in self:
            subject=u'[Frais]['+obj.chrono_long+u'] '+obj.activite_id.nature_activite+u' Diffusé'
            user  = self.env.user
            email_to = user.company_id.is_mail_frais
            if not email_to:
                raise ValidationError(u"Mail diffusion frais de la société non configuré")
            email_from = user.email
            if not email_from:
                raise ValidationError(u"Votre mail n'est pas configuré")
            nom   = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url=base_url+u'/web#id='+str(obj.id)+u'&view_type=form&model='+self._name
            body_html=u"""
                <p>Bonjour,</p>
                <p>"""+nom+""" vient de passer la fiche de frais <a href='"""+url+"""'>"""+obj.activite_id.nature_activite+"""</a> à l'état 'Diffusé'.</p>
                <p>Merci d'en prendre connaissance.</p>
            """
            self.envoi_mail(email_from,email_to,subject,body_html)
            obj.state='diffuse'


    def vers_valide(self):
        for obj in self:
            obj.creer_notification(u'Vers Validé')
            obj.state='valide'


    def vers_brouillon(self):
        for obj in self:
            obj.sudo().write({'state': 'brouillon'})
            obj.creer_notification(u'Vers Brouillon')


    def acceder_frais_action(self):
        for obj in self:
            res= {
                'name': 'Frais',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.frais',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res

