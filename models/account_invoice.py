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
    is_phase                = fields.Boolean(u'Afficher les phases',default=True)
    is_intervenant          = fields.Boolean(u'Afficher les intervenants sur la facture')
    is_prix_unitaire        = fields.Boolean(u'Afficher les quantités et prix unitaire sur la facture')
    is_frais                = fields.Monetary(u'Total des frais refacturables')
    is_detail_frais         = fields.Boolean(u'Afficher le détail des frais',default=False)
    is_date_encaissement    = fields.Date(u'Date encaissement')
    is_montant_encaissement = fields.Float(u'Montant encaissement', digits=(14,2))
    is_code_service         = fields.Char(u"Code service")
    is_ref_engagement       = fields.Char(u"Réf engagement")
    is_frais_commentaire    = fields.Char("Facturation des frais", compute='_is_frais_commentaire', readonly=True, store=False)


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
                        line=self.env['account.invoice.line'].create(vals)
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
            html+='<td class="text-left">' +line.name+'</td>'
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





