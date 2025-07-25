# -*- coding: utf-8 -*-
from odoo import models,fields,tools  # type: ignore


class IsInvoiceActivite(models.Model):
    _description = "Suivi activités par facture"
    _name = 'is.invoice.activite'
    _order='id desc'
    _auto = False


    product_id = fields.Many2one('product.product', "Intervenant")
    is_type_intervenant = fields.Selection([
            ('consultant'   , 'Consultant'),
            ('co-traitant'  , 'Co-traitant'),
            ('sous-traitant', 'Sous-Traitant'),
        ], u"Type d'intervenant",)
    is_activite_id         = fields.Many2one('is.activite', 'Activité')
    is_frais_id            = fields.Many2one('is.frais', 'Frais')
    price_subtotal         = fields.Float("Montant HT", digits=(14,2))
    invoice_id             = fields.Many2one('account.move', 'Facture')
    is_affaire_id          = fields.Many2one('is.affaire', 'Affaire')
    partner_id             = fields.Many2one('res.partner', "Client facturable")
    state = fields.Selection([
            ('draft','Draft'),
            ('diffuse','Diffusé'),
            ('open', 'Open'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ], string='État')
    invoice_date       = fields.Date("Date facture")
    annee_invoice      = fields.Char("Année facture")
    annee_mois_invoice = fields.Char("Année-Mois facture")
    mois_invoice       = fields.Char("Mois facture")

    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(cr, 'is_invoice_activite')

            #TODO : Utiliser les nouvzrax champs 'signed'

          



        cr.execute("""

            CREATE OR REPLACE FUNCTION fsens(t text) RETURNS integer AS $$
            BEGIN
                RETURN (
                    SELECT
                    CASE
                    WHEN t::text = ANY (ARRAY['out_refund'::character varying::text, 'in_refund'::character varying::text])
                        THEN -1::int
                        ELSE 1::int
                    END
                );
            END;
            $$ LANGUAGE plpgsql;


            CREATE OR REPLACE view is_invoice_activite AS (
                select
                    ail.id,
                    ail.product_id,
                    pt.is_type_intervenant,
                    ail.is_activite_id,
                    ail.is_frais_id,
                    fsens(ai.move_type)*ail.price_subtotal price_subtotal,
                    ail.move_id invoice_id,
                    ai.is_affaire_id,
                    ai.partner_id,
                    ai.invoice_date,
                    to_char(ai.invoice_date,'YYYY')    annee_invoice,
                    to_char(ai.invoice_date,'YYYY-MM') annee_mois_invoice,
                    to_char(ai.invoice_date,'MM')      mois_invoice,
                    ai.state
                from account_move_line ail inner join account_move  ai on ail.move_id=ai.id
                                           inner join product_product  pp on ail.product_id=pp.id
                                           inner join product_template pt on pp.product_tmpl_id=pt.id
                where pt.is_type_intervenant is not null and ai.state not in ('cancel','draft')
            )
        """)

