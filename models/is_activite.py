# -*- coding: utf-8 -*-
from odoo import api, fields, models, _       # type: ignore
from odoo.exceptions import ValidationError   # type: ignore


class IsActivite(models.Model):
    _name = 'is.activite'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Activité"
    _order = 'date_debut desc'
    _rec_name = 'rec_name'
    #_rec_names_search = ['name', 'bic']


    @api.depends('tarification_id','nb_facturable')
    def _compute(self):
        for obj in self:
            if obj.tarification_id:
                obj.montant          = obj.tarification_id.montant
                total_facturable     = obj.montant*obj.nb_facturable
                obj.total_facturable = total_facturable
               


    def _compute_nb_stagiaires(self):
        for obj in self:
            nb=0
            ct=0
            if obj.suivi_temps_ids:
                for line in obj.suivi_temps_ids:
                    if line.nb_stagiaires>0:
                        nb+=line.nb_stagiaires
                        ct+=1
                if ct>0:
                    nb=nb/ct
            obj.nb_stagiaires=nb


    @api.depends('intervenant_id')
    def _compute_product_id(self):
        for obj in self:
            obj.intervenant_product_id=obj.intervenant_id.intervenant_id.id


    @api.depends('affaire_id','affaire_id.responsable_id')
    def _compute_responsable_id(self):
        for obj in self:
            obj.responsable_id = obj.affaire_id.responsable_id.id


    def get_jours_consommes(self,act):
        jours_consommes=0
        unite = act.tarification_id.unite
        if unite=='journee':
            jours_consommes+=act.nb_facturable
        if unite=='demie_journee':
            jours_consommes+=act.nb_facturable/2
        if unite=='heure':
            jours_consommes+=act.nb_facturable/7
        #Pour les participants, il faut compter le nombre de lignes dans le suivi du temps
        if unite=='participant':
            jours_consommes+=len(act.suivi_temps_ids)
        return jours_consommes

    @api.depends('suivi_temps_ids','nb_facturable','tarification_id')
    def _compute_jours_consommes(self):
        for act in self:
            jours_consommes=self.get_jours_consommes(act)
            act.jours_consommes=jours_consommes


    def get_jours_realises(self,act):
        jours_realises=0
        unite = act.tarification_id.unite
        if unite=='journee':
            jours_realises+=act.nb_realise
        if unite=='demie_journee':
            jours_realises+=act.nb_realise/2
        if unite=='heure':
            jours_realises+=act.nb_realise/7
        #Pour les participants, il faut compter le nombre de lignes dans le suivi du temps
        if unite=='participant':
            jours_realises+=len(act.suivi_temps_ids)
        return jours_realises


    @api.depends('suivi_temps_ids','nb_facturable','tarification_id')
    def _compute_jours_realises(self):
        for act in self:
            jours_realises=self.get_jours_realises(act)
            act.jours_realises=jours_realises


    def get_nb_realise_auto(self,act):
        nb_realise_auto=0
        unite = act.tarification_id.unite
        if unite=='journee':
            nb_realise_auto+=act.nb_facturable
        if unite=='demie_journee':
            nb_realise_auto+=act.nb_facturable/2
        if unite=='heure':
            nb_realise_auto+=act.nb_facturable/7
        #Pour les participants, il faut compter le nombre de lignes dans le suivi du temps
        if unite=='participant':
            nb_realise_auto+=len(act.suivi_temps_ids)
        return nb_realise_auto

    @api.depends('suivi_temps_ids','nb_facturable','tarification_id')
    def _compute_nb_realise_auto(self):
        for act in self:
            nb_realise_auto=self.get_nb_realise_auto(act)
            act.nb_realise_auto=nb_realise_auto


    @api.depends('affaire_id','tarification_id')
    def _compute_nb_realise_vsb(self):
        #cr,uid,context = self.env.args
        user = self.env['res.users'].browse(self._uid)
        company  = user.company_id
        for obj in self:
            if company.is_interface=='sgp':
                obj.nb_realise_vsb = False
            else:
                obj.nb_realise_vsb = True


    @api.onchange('affaire_id')
    def onchange_affaire_id(self):
        self.partner_id = self.affaire_id.partner_id.id


    affaire_id             = fields.Many2one('is.affaire', 'Affaire', required=True,index=True,tracking=True)
    responsable_id         = fields.Many2one('res.users', "Responsable de l'affaire", compute='_compute_responsable_id',tracking=True, readonly=True, store=True)
    partner_id             = fields.Many2one('res.partner', "Client facturable",tracking=True, required=True, index=True, domain=[('customer','=',True)])
    phase_activite_id      = fields.Many2one('is.affaire.phase.activite', 'Sous-phase',index=True,tracking=True)
    nature_activite        = fields.Char("Nature de l'activité"     , required=True, index=True,tracking=True)
    date_debut             = fields.Date("Date de début de l'activité", required=True, index=True,tracking=True)
    dates_intervention     = fields.Char("Dates des jours d'intervention",tracking=True)


    def _default_intervenant(self):
        """Par défaut, sélectionne l'intervenant lié à l'utilisateur courant,
        et si une affaire est dans le contexte, limite à cette affaire."""
        uid = self.env.uid
        domain = [('intervenant_id.is_consultant_id', '=', uid)]
        affaire_id = self.env.context.get('default_affaire_id')
        if affaire_id:
            domain.append(('affaire_id', '=', affaire_id))
        return self.env['is.affaire.intervenant'].search(domain, limit=1).id

    intervenant_id = fields.Many2one(
        'is.affaire.intervenant',
        "Intervenant Affaire",
        required=True,
        index=True,
        tracking=True,
        default=_default_intervenant
    )


    intervenant_product_id = fields.Many2one('product.product', "Intervenant", compute='_compute_product_id', readonly=True, store=True,tracking=True)
    tarification_id        = fields.Many2one('is.affaire.taux.journalier', "Tarification",tracking=True)
    montant                = fields.Float("Montant unitaire", compute='_compute', readonly=True, store=True, digits=(14,2),tracking=True)

    nb_realise             = fields.Float("Nb unités réalisées"  , digits=(14,3),tracking=True)
    nb_realise_auto        = fields.Float("Nb unités réalisées (auto)", digits=(14,2), compute='_compute_nb_realise_auto', readonly=True, store=False)
    nb_realise_vsb         = fields.Boolean("Nb unités réalisées visibility", compute='_compute_nb_realise_vsb', readonly=True, store=False)

    nb_facturable          = fields.Float("Nb unités facturables", digits=(14,3),tracking=True)
    jours_consommes        = fields.Float("Nb jours consommés", digits=(14,2), compute='_compute_jours_consommes', readonly=True, store=True,tracking=True)
    jours_realises         = fields.Float("Nb jours réalisés" , digits=(14,2), compute='_compute_jours_realises' , readonly=True, store=True,tracking=True)
    total_facturable       = fields.Float("Total facturable", compute='_compute', readonly=True, store=True, digits=(14,2),tracking=True)
    nb_stagiaires          = fields.Float("Nombre de stagiaires calculé", compute='_compute_nb_stagiaires', readonly=True, store=False, digits=(14,1))
    facture_sur_accompte   = fields.Boolean("Facture sur acompte",tracking=True)
    non_facturable         = fields.Boolean("Activité non facturable", default=False,tracking=True, help="Si cette case est cochée, cette activité ne sera pas proposée à la facturation")
    point_cle              = fields.Text("Points clés de l'activité réalisée",tracking=True)
    suivi_temps_ids        = fields.One2many('is.suivi.temps', 'activite_id', u'Suivi du temps')
    frais_ids              = fields.One2many('is.frais', 'activite_id', u'Frais')
    pieces_jointes_ids     = fields.Many2many('ir.attachment', 'is_activite_pieces_jointes_rel', 'doc_id', 'file_id', u'Pièces jointes')
    invoice_id             = fields.Many2one('account.move', "Facture",index=True, copy=False,tracking=True)
    state                  = fields.Selection([
            ('brouillon', u'Brouillon'),
            ('diffuse'  , u'Diffusé'),
            ('valide'   , u'Validé'),
        ], u"État", index=True, default='brouillon',tracking=True)
    is_dynacase_ids = fields.Many2many('is.dynacase', 'is_activite_dynacase_rel', 'doc_id', 'dynacase_id', 'Ids Dynacase', readonly=True)
    active          = fields.Boolean("Activité active", default=True,tracking=True)
    rec_name       = fields.Char("Nom de l'activité", compute='_compute_rec_name', readonly=True, store=True,tracking=True)







    @api.depends('affaire_id.code_long','nature_activite')
    def _compute_rec_name(self):
        for obj in self:
            name="[%s] %s"%(obj.affaire_id.code_long,obj.nature_activite)
            obj.rec_name = name


    def write(self,vals):
        for obj in self:
            if obj.state=='diffuse' and 'state' not in vals:
                #** Envoi d'un courriel a l'intervenant si modification ********
                if obj.intervenant_id.intervenant_id.is_type_intervenant == 'consultant':
                    subject=u'[Activité] '+obj.nature_activite+u' Modifiée'
                    email_to=obj.intervenant_id.intervenant_id.is_consultant_id.email
                    if not email_to:
                        print(obj.intervenant_id,obj.intervenant_id.intervenant_id,obj.intervenant_id.intervenant_id.is_type_intervenant)
                        raise ValidationError(u"Mail de l'intervenant non configuré pour ")
                    user  = self.env['res.users'].browse(self._uid)
                    email_from = user.email
                    if not email_from:
                        raise ValidationError(u"Votre mail n'est pas configuré")
                    nom   = user.name
                    if email_from!=email_to:
                        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        url         = base_url+u'/web#id='+str(obj.id)+u'&view_type=form&model='+self._name
                        url_affaire = base_url+u'/web#id='+str(obj.affaire_id.id)+u'&view_type=form&model='+obj.affaire_id._name
                        body_html=u"""
                            <p>Bonjour,</p>
                            <p>Pour information, """+nom+""" vient de modifier votre activité <a href='"""+url+"""'>"""+obj.nature_activite+"""</a>.</p>
                            <p>Affaire : <a href='"""+url_affaire+"""'>"""+obj.affaire_id.rec_name+"""</a>.</p>
                        """
                        self.envoi_mail(email_from,email_to,subject,body_html)
                #***************************************************************

        res = super(IsActivite, self).write(vals)
        return res


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


    def vers_diffuse(self):
        for obj in self:
            # Vérification des droits si l'état actuel est "valide"
            if obj.state == 'valide':
                user = self.env['res.users'].browse(self._uid)
                if not user.has_group('is_opta_s18.is_administratif_group'):
                    raise ValidationError("Vous n'avez pas les droits pour passer une activité validée à l'état diffusé")
            
            subject=u'[Activité] '+obj.nature_activite+u' Diffusé'
            email_to=obj.affaire_id.responsable_id.email
            if not email_to:
                raise ValidationError(u"Mail du responsable de l'affaire non configuré")
            user  = self.env['res.users'].browse(self._uid)
            email_from = user.email
            if not email_from:
                raise ValidationError(u"Votre mail n'est pas configuré")
            nom   = user.name
            if email_from!=email_to:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                url         = base_url+u'/web#id='+str(obj.id)+u'&view_type=form&model='+self._name
                url_affaire = base_url+u'/web#id='+str(obj.affaire_id.id)+u'&view_type=form&model='+obj.affaire_id._name
                body_html=u"""
                    <p>Bonjour,</p>
                    <p>"""+nom+""" vient de passer l'activité <a href='"""+url+"""'>"""+obj.nature_activite+"""</a> à l'état 'Diffusé'.</p>
                    <p>Affaire : <a href='"""+url_affaire+"""'>"""+obj.affaire_id.rec_name+"""</a>.</p>
                    <p>Merci d'en prendre connaissance.</p>
                """
                self.envoi_mail(email_from,email_to,subject,body_html)
            obj.state='diffuse'


    def vers_valide(self):
        for obj in self:
            obj.state='valide'


    def vers_brouillon(self):
        for obj in self:
            obj.sudo().state='brouillon'

    def acceder_activite_action(self):
        for obj in self:
            res= {
                'name': 'Activité',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.activite',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res


    def creation_frais(self):
        for obj in self:
            res= {
                'name': 'Frais',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.frais',
                'type': 'ir.actions.act_window',
                'context': {
                    'default_affaire_id' : obj.affaire_id.id,
                    'default_activite_id': obj.id,
                }
            }
            return res


    def creation_activite(self):
        for obj in self:
            res= {
                'name': 'Activité',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.activite',
                'type': 'ir.actions.act_window',
                'context': {'default_affaire_id': obj.affaire_id.id }
            }
            return res


