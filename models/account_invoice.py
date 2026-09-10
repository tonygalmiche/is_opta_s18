# -*- coding: utf-8 -*-
from odoo import api, fields, models, _                         # type: ignore
from odoo.exceptions import ValidationError,UserError           # type: ignore
from odoo.addons.account.models.chart_template import template  # type: ignore
from markupsafe import Markup


#TODO : 
#- Le menu 'Export Cegid' est utilsé unoquement par 'Nouvelle trajecoire'


def f0(number):
    return '{0:,.0f}'.format(number).replace(',', ' ').replace('.', ',')

def f2(number):
    return '{0:,.2f}'.format(number).replace(',', ' ').replace('.', ',')


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    is_code_analytique = fields.Char("Code analytique")


class AccountAccount(models.Model):
    _inherit = "account.account"

    is_code_analytique = fields.Char("Code analytique")


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    is_dates_intervention = fields.Char("Dates d'intervention")
    is_activite_id        = fields.Many2one('is.activite', 'Activité')
    is_frais_id           = fields.Many2one('is.frais', 'Frais')
    is_frais_ligne_id     = fields.Many2one('is.frais.lignes', 'Ligne de frais')
    is_account_invoice_line_id = fields.Integer('Lien entre account_invoice_line et account_move_line pour la migration', index=True)


    def uptate_onchange_product_id(self):
        # for obj in self:
        #     obj._onchange_product_id()
        return True



class AccountInvoice(models.Model):
    _inherit = "account.move"

    state = fields.Selection(
        selection_add=[
            ('diffuse','Diffusé'),
        ], ondelete={'diffuse': 'set default'}
    )
    is_createur_id = fields.Many2one('res.users', string='Créateur', readonly=True,
        default=lambda self: self.env.user, copy=False) #, track_visibility='onchange', states={'draft': [('readonly', False)]},
    is_affaire_id           = fields.Many2one('is.affaire', u'Affaire')
    is_activites            = fields.Many2many('is.activite', 'is_account_invoice_activite_rel', 'invoice_id', 'activite_id')
    is_detail_activite      = fields.Boolean(u'Afficher le détail des activités',default=True)
    is_phase                = fields.Boolean(u'Afficher les phases',default=False)
    is_intervenant          = fields.Boolean(u'Afficher les intervenants sur la facture', default=True)
    is_prix_unitaire        = fields.Boolean(u'Afficher les quantités et prix unitaire sur la facture')
    is_frais                = fields.Monetary(u'Total des frais refacturables')
    is_detail_frais         = fields.Boolean(u'Afficher le détail des frais',default=False)
    is_date_encaissement    = fields.Date(u'Date encaissement')
    is_montant_encaissement = fields.Float(u'Montant encaissement', digits=(14,2))
    is_code_service         = fields.Char(u"Code service")
    is_ref_engagement       = fields.Char(u"Réf engagement")
    is_frais_commentaire    = fields.Char("Facturation des frais", compute='_is_frais_commentaire', readonly=True, store=False)
    is_autoriser_retour_brouillon = fields.Boolean(
        "Autoriser le retour en brouillon",
        default=False,
        tracking=True,
        copy=False,
        help="Permet de repasser cette facture en brouillon même si le "
             "module de facturation électronique (l10n_fr_einvoicing) s'y "
             "oppose (facture déjà envoyée au client hors plateforme AP "
             "alors qu'elle y est soumise, ou flux e-invoicing déjà généré).",
    )


    #** Surcharge de la fonction de base pour ne pas générer de séquence à l'état Diffusé
    @api.depends('posted_before', 'state', 'journal_id', 'date', 'move_type', 'origin_payment_id')
    def _compute_name(self):
        self = self.sorted(lambda m: (m.date, m.ref or '', m._origin.id))

        for move in self:
            if move.state == 'cancel':
                continue

            move_has_name = move.name and move.name != '/'
            if not move.posted_before and not move._sequence_matches_date():
                # The name does not match the date and the move is not the first in the period:
                # Reset to draft
                move.name = False
                continue
            if move.date and not move_has_name and move.state != 'draft' and move.state != 'diffuse':
                move._set_next_sequence()

        self._inverse_name()



    def _is_frais_commentaire(self):
        for obj in self:
            x = False
            if obj.is_affaire_id:
                nature_frais = obj.is_affaire_id.nature_frais
                if nature_frais=='au_reel' or nature_frais=='reel_plafonne':
                    x = u"Frais de déplacement : débours : cf justificatifs"
                if obj.is_affaire_id.nature_frais == 'frais_inclus':
                    x = u"Frais de déplacement inclus"
                if obj.is_affaire_id.nature_frais == 'forfait':
                    x = u"Forfait Frais de déplacement"
            obj.is_frais_commentaire = x


    @api.onchange('partner_id', 'company_id', 'is_affaire_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.is_affaire_id:
            self.fiscal_position_id = self.is_affaire_id.fiscal_position_id.id
        return res


    #** Le champ 'ref' (Référence client) sert au numéro d'engagement exigé
    #** par Chorus Pro pour certains clients publics (cf. fr_directory_line
    #** commitment_required), mais n'est pas utilisé par ailleurs sur
    #** opta-s18 : on le synchronise automatiquement avec 'is_ref_engagement'.
    @api.onchange('is_ref_engagement')
    def _onchange_is_ref_engagement(self):
        self.ref = self.is_ref_engagement

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_ref_engagement') and not vals.get('ref'):
                vals['ref'] = vals['is_ref_engagement']
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('is_ref_engagement'):
            vals['ref'] = vals['is_ref_engagement']
        return super().write(vals)


    def acceder_facture_action(self):
        for obj in self:

            res= {
                'name': 'Facture',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'account.move',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
                # 'view_id': self.env.ref('account.invoice_form').id,
                'domain': [('type','=','out_invoice')],
            }
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
                'notification'  : True,
                'message_type'  : 'comment',
            }
            email=self.env['mail.mail'].create(vals)
            if email:
                self.env['mail.mail'].send(email)


    def vers_diffuse_action(self):
        for obj in self:
            subject=u'[Facture] '+obj.partner_id.name+u' Diffusé'
            user  = self.env.user
            email_to = user.company_id.is_mail_facture
            if not email_to:
                raise ValidationError(u"Mail diffusion facture de la société non configuré")
            email_from = user.email
            if not email_from:
                raise ValidationError(u"Votre mail n'est pas configuré")
            nom   = user.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url=base_url+u'/web#id='+str(obj.id)+u'&view_type=form&model='+self._name
            body_html=u"""
                <p>Bonjour,</p>
                <p>"""+nom+""" vient de passer la facture du client <a href='"""+url+"""'>"""+obj.partner_id.name+"""</a> à l'état 'Diffusé'.</p>
                <p>Merci d'en prendre connaissance.</p>
            """
            #self.envoi_mail(email_from,email_to,subject,body_html)
            obj.state='diffuse'


    def _en16931_checks_upon_invoice_generation(self):
        #** Surcharge de account_invoice_en16931 pour autoriser la génération
        #** EN16931 (bouton "Tester si la facture est valide") à l'état
        #** personnalisé 'diffuse', en plus de 'draft' et 'posted' (le code
        #** d'origine ne connaît pas cet état ajouté par is_opta_s18).
        self.ensure_one()
        if self.state != 'diffuse':
            return super()._en16931_checks_upon_invoice_generation()
        self.company_id._en16931_checks()
        if self.move_type not in ("out_invoice", "out_refund"):
            raise UserError(u"La génération EN16931 n'est utilisée que pour les factures et avoirs clients. Ce n'est pas le cas de '"+self.display_name+u"'.")


    #** Ces 3 méthodes surchargent account_invoice_en16931 : le code d'origine
    #** ne connaît pas l'état personnalisé 'diffuse' (ajouté par is_opta_s18),
    #** qui doit être traité comme 'draft' (facture pas encore numérotée).

    def _prepare_bt1(self, speedy):
        self.ensure_one()
        if self.state == 'diffuse':
            return self.env._("DRAFT-FOR_TEST_ONLY")
        return super()._prepare_bt1(speedy)

    def _prepare_bt2(self, speedy):
        self.ensure_one()
        if self.state == 'diffuse':
            return self.invoice_date or fields.Date.context_today(self)
        return super()._prepare_bt2(speedy)

    def _prepare_en16931_filename(self, invoice_format):
        self.ensure_one()
        if self.state != 'diffuse':
            return super()._prepare_en16931_filename(invoice_format)
        filename = self.env._("draft_invoice")
        if invoice_format:
            if invoice_format.startswith(("facturx", "pdf_")):
                filename += ".pdf"
            elif invoice_format.startswith("ubl"):
                filename += "_ubl.xml"
            elif invoice_format.startswith("cii"):
                filename += "_cii.xml"
        return filename


    #** Surcharge pour permettre le retour en brouillon d'une facture postée
    #** malgré le blocage de l10n_fr_einvoicing (cf. is_autoriser_retour_brouillon),
    #** via le context sudo_draftable_fr_einvoicing_flow déjà prévu par ce module.
    def button_draft(self):
        forced = self.filtered('is_autoriser_retour_brouillon')
        if forced:
            super(AccountInvoice, forced.with_context(sudo_draftable_fr_einvoicing_flow=True)).button_draft()
            remaining = self - forced
            if remaining:
                super(AccountInvoice, remaining).button_draft()
            return True
        return super().button_draft()

    def vers_brouillon_action(self):
        for obj in self:
            obj.state='draft'


    def vers_open_action(self):
        for obj in self:
            obj.state='draft'
            obj.action_invoice_open()


    def activites_vers_lignes_action(self):
        for obj in self:
            obj.invoice_line_ids.unlink()
            activites=self.env['is.activite'].search([('invoice_id', '=', obj.id)])
            for act in activites:
                act.sudo().invoice_id=False
            for act in obj.is_activites:
                act.sudo().invoice_id=obj.id
                product_id=act.intervenant_id.intervenant_id
                account_id=product_id.property_account_income_id.id
                if not account_id:
                    raise ValidationError(u"Compte de revenus non défini pour l'article "+product_id.name+u' (id='+str(product_id.product_tmpl_id.id)+u')')
                vals={
                    'move_id'              : obj.id,
                    'product_id'           : product_id.id,
                    'name'                 : ' ',
                    'price_unit'           : 0,
                    'account_id'           : account_id,
                    'is_dates_intervention': act.dates_intervention,
                    'is_activite_id'       : act.id,
                }
                line=self.env['account.move.line'].create(vals)
                line._compute_account_id()
                #line._onchange_product_id()
                line.quantity   = act.nb_facturable
                line.price_unit = act.montant
                line.name       = act.nature_activite


            #** Recherche article si frais au forfait **************************
            products=self.env['product.product'].search([('name', 'ilike', 'Frais au forfait')])
            product=False
            if products:
                product=products[0]
            else:
                raise ValidationError(u"Aucun article 'Frais au forfait' trouvé")
            #*******************************************************************


            is_frais=0
            obj.is_detail_frais=False
            for act in obj.is_activites:
                for frais in act.frais_ids:
                    if product and frais.frais_forfait:
                        account_id=product.property_account_income_id.id
                        if account_id==False:
                            raise ValidationError(u"Compte de revenu non renseigné pour l'article "+product.name)
                        vals={
                            'move_id'              : obj.id,
                            'product_id'           : product.id,
                            'name'                 : product.name,
                            'price_unit'           : 0,
                            'account_id'           : account_id,
                            'is_activite_id'       : act.id,
                            'is_frais_id'          : frais.id,
                        }
                        line=self.env['account.move.line'].create(vals)
                        #line._onchange_product_id()
                        line.quantity   = frais.nb_jours
                        line.price_unit = frais.montant_forfait
                        is_frais+=line.quantity*line.price_unit

                    for ligne in frais.ligne_ids:
                        if ligne.refacturable=='oui' and not frais.frais_forfait:
                            obj.is_detail_frais=True
                            account_id=ligne.product_id.property_account_income_id.id
                            if account_id==False:
                                raise ValidationError(u"Compte de revenu non renseigné pour l'article "+ligne.product_id.name)
                            vals={
                                'move_id'              : obj.id,
                                'product_id'           : ligne.product_id.id,
                                'name'                 : ligne.product_id.name,
                                'price_unit'           : 0,
                                'account_id'           : account_id,
                                'is_activite_id'       : act.id,
                                'is_frais_id'          : frais.id,
                                'is_frais_ligne_id'    : ligne.id,
                            }
                            line=self.env['account.move.line'].create(vals)
                            #line._onchange_product_id()
                            line.quantity   = 1
                            line.price_unit = ligne.montant_ttc
                            is_frais+=ligne.montant_ttc
            #obj.compute_taxes()
            obj.is_frais=is_frais
            return True


    def _add_tr(self,line):
        for obj in self:
            html='<tr>'
            html+='<td class="text-left">' + (line.name or '').replace('\n', '<br/>')+'</td>'
            if obj.is_intervenant:
                html+='<td class="text-left">'+(line.is_activite_id.intervenant_id.intervenant_id.name or '')+'</td>'
                html+='<td class="text-left">'+(line.is_activite_id.dates_intervention or '')+'</td>'

            if obj.is_prix_unitaire:
                html+='<td class="text-end" style="white-space: nowrap">'+f2(line.quantity)+'</td>'
                html+='<td class="text-end" style="white-space: nowrap">'+f2(line.price_unit)+' €</td>'
            html+='<td class="text-end"     style="white-space: nowrap">'+f2(line.price_subtotal)+' €</td>'
            html+='</tr>'
            return html


    def _add_tr_total_sous_phase(self,sous_phase):
        for obj in self:
            colspan=1
            if obj.is_intervenant:
                colspan+=2
            if obj.is_prix_unitaire:
                colspan+=2
            montant=0
            for line in obj.invoice_line_ids:
                if line.is_activite_id.phase_activite_id.id==sous_phase.id:
                    if line.is_frais_ligne_id.id==False:
                        montant+=line.price_subtotal
            html='<tr>'
            html+='<td class="text-left bg-100" colspan="'+str(colspan)+'">' +sous_phase.name+'</td>'
            html+='<td class="text-end bg-100"">'+f2(montant)+' €</td>'
            html+='</tr>'
            return html


    def get_invoice_line(self):
        for obj in self:
            colspan=3
            html="""
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th class="text-left"><span>Description</span></th>
            """
            if obj.is_intervenant:
                colspan+=2
                html+="""
                                <th class="text-left"><span>Intervenant</span></th>
                                <th class="text-left"><span>Date d'intervention</span></th>
            """
            if obj.is_prix_unitaire:
                colspan+=2
                html+="""
                                <th class="text-end"><span>Quantité</span></th>
                                <th class="text-end"><span>Prix unitaire</span></th>
            """
            html+="""
                                <th class="text-end"><span>Montant HT</span></th>
                            </tr>
                        </thead>
                        <tbody class="invoice_tbody">
            """


            if obj.is_phase:
                #Recherche des phases et sous-phases à afficher ****************
                phase_ids=[]
                sous_phase_ids=[]
                for phase in obj.is_affaire_id.phase_ids:

                    for sous_phase in obj.is_affaire_id.activite_phase_ids:
                        if sous_phase.affaire_phase_id.id==phase.id:
                            for line in obj.invoice_line_ids:
                                if line.is_activite_id.phase_activite_id.id==sous_phase.id:
                                    if phase not in phase_ids:
                                        phase_ids.append(phase)
                                    if sous_phase not in sous_phase_ids:
                                        sous_phase_ids.append(sous_phase)
                #***************************************************************
                for phase in phase_ids:
                    html+='<tr><td colspan="'+str(colspan)+'" class="bg-200">' +phase.name+'</td></tr>'
                    for sous_phase in sous_phase_ids:
                        if sous_phase.affaire_phase_id.id==phase.id:
                            html+=self._add_tr_total_sous_phase(sous_phase)
                            for line in obj.invoice_line_ids:
                                if line.is_activite_id.phase_activite_id.id==sous_phase.id:
                                    if line.is_frais_ligne_id.id==False and line.is_frais_id.id==False:
                                        if obj.is_detail_activite:
                                            html+=self._add_tr(line)
            else:
                for line in obj.invoice_line_ids:
                    if line.is_frais_ligne_id.id==False and line.is_frais_id.id==False:
                        html+=self._add_tr(line)
            html+='</tbody>'
            html+='</table>'
            res=Markup(html)
            return res

    def _get_invoice_proforma_pdf_report_filename(self):
        # Ne pas suffixer le PDF de secours par "_proforma" : la facture
        # n'est jamais réellement envoyée via "Imprimer & Envoyer" ici,
        # donc invoice_pdf_report_id ne sera jamais créé et ce nom
        # resterait indéfiniment marqué "proforma".
        self.ensure_one()
        return f"{self._get_move_display_name().replace(' ', '_').replace('/', '_')}.pdf"



