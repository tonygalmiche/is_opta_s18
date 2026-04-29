# -*- coding: utf-8 -*-
import calendar
from datetime import date
from odoo import api, fields, models  # type: ignore


class IsDispoUserMois(models.Model):
    _name = 'is.dispo.user.mois'
    _description = "Disponibilité par utilisateur et par mois"
    _order = 'mois, user_id'

    user_id       = fields.Many2one('res.users', 'Utilisateur', required=True, index=True, ondelete='cascade')
    mois          = fields.Char('Mois', required=True, help="Format AAAA-MM")
    disponibilite = fields.Integer('Disponibilité', help="Nombre de jours disponibles")
    charge        = fields.Integer('Charge')
    delta         = fields.Integer('Delta', compute='_compute_delta', store=True)

    @api.depends('disponibilite', 'charge')
    def _compute_delta(self):
        for obj in self:
            obj.delta = obj.disponibilite - obj.charge

    _sql_constraints = [
        ('unique_user_mois', 'unique(user_id, mois)', "Une ligne existe déjà pour cet utilisateur et ce mois."),
    ]

    @api.model
    def _nb_jours_ouvres(self, annee, mois_num):
        """Retourne le nombre de jours ouvrés (lundi-vendredi) du mois."""
        _, nb_jours = calendar.monthrange(annee, mois_num)
        total = 0
        for jour in range(1, nb_jours + 1):
            if date(annee, mois_num, jour).weekday() < 5:  # 0=lundi, 4=vendredi
                total += 1
        return total

    def action_saisie_12_mois(self):
        """Crée (si nécessaire) les 12 prochains mois pour le user connecté et retourne la vue liste."""
        user_id = self.env.uid
        today = date.today()
        annee = today.year
        mois_num = today.month
        for _ in range(12):
            mois_str = "%04d-%02d" % (annee, mois_num)
            existing = self.search([('user_id', '=', user_id), ('mois', '=', mois_str)], limit=1)
            if not existing:
                self.create({
                    'user_id'      : user_id,
                    'mois'         : mois_str,
                    'disponibilite': self._nb_jours_ouvres(annee, mois_num),
                })
            mois_num += 1
            if mois_num > 12:
                mois_num = 1
                annee += 1
        return {
            'name'     : 'Saisie des disponibilités sur 12 mois',
            'type'     : 'ir.actions.act_window',
            'res_model': 'is.dispo.user.mois',
            'view_mode': 'list,graph',
            'views'    : [
                (self.env.ref('is_opta_s18.is_dispo_user_mois_saisie_tree').id, 'list'),
                (self.env.ref('is_opta_s18.is_dispo_user_mois_graph').id, 'graph'),
            ],
            'domain'   : [('user_id', '=', user_id)],
            'context'  : {'default_user_id': user_id},
        }


class IsAnalyseAcr(models.Model):
    _name = 'is.analyse.acr'
    _description = "Analyse ACR"
    _order = 'ordre'

    ordre      = fields.Integer('Ordre')
    consultant = fields.Html('Consultant', sanitize=False)
    mois_1     = fields.Html('Mois 1',  sanitize=False)
    mois_2     = fields.Html('Mois 2',  sanitize=False)
    mois_3     = fields.Html('Mois 3',  sanitize=False)
    mois_4     = fields.Html('Mois 4',  sanitize=False)
    mois_5     = fields.Html('Mois 5',  sanitize=False)
    mois_6     = fields.Html('Mois 6',  sanitize=False)
    mois_7     = fields.Html('Mois 7',  sanitize=False)
    mois_8     = fields.Html('Mois 8',  sanitize=False)
    mois_9     = fields.Html('Mois 9',  sanitize=False)
    mois_10    = fields.Html('Mois 10', sanitize=False)
    mois_11    = fields.Html('Mois 11', sanitize=False)
    mois_12       = fields.Html('Mois 12',      sanitize=False)
    total_12_mois = fields.Html('Total 12 mois', sanitize=False)

    @api.model
    def action_generer(self, type_analyse='delta'):
        """Régénère toutes les lignes et retourne la vue liste."""
        self.search([]).unlink()

        labels = {
            'disponibilite': 'Disponibilité',
            'charge'       : 'Charge',
            'delta'        : 'Delta',
        }
        titres = {
            'disponibilite': 'Analyse ACR disponibilité',
            'charge'       : 'Analyse ACR charge',
            'delta'        : 'Analyse ACR reste dispo',
        }
        label = labels.get(type_analyse, 'Delta')

        today = date.today()
        mois_list = []
        annee, mois_num = today.year, today.month
        for _ in range(12):
            mois_list.append("%04d-%02d" % (annee, mois_num))
            mois_num += 1
            if mois_num > 12:
                mois_num = 1
                annee += 1

        grey = 'background:#cccccc;font-weight:bold;display:block;padding:2px 4px;text-align:center'

        # Ligne d'entête des mois (gris)
        header_vals = {'ordre': 0, 'consultant': '<span style="%s">%s</span>' % (grey, label)}
        for i, mois in enumerate(mois_list, 1):
            header_vals['mois_%d' % i] = '<span style="%s">%s</span>' % (grey, mois)
        header_vals['total_12_mois'] = '<span style="%s">Total</span>' % grey
        self.create(header_vals)

        # Lignes par utilisateur
        DispoModel = self.env['is.dispo.user.mois']
        users = DispoModel.search([('mois', 'in', mois_list)]).mapped('user_id')
        totals = {mois: 0 for mois in mois_list}

        for ordre, user in enumerate(users, 1):
            vals = {'ordre': ordre, 'consultant': user.name or ''}
            user_total = 0
            for i, mois in enumerate(mois_list, 1):
                dispo = DispoModel.search([('user_id', '=', user.id), ('mois', '=', mois)], limit=1)
                if dispo:
                    valeur = getattr(dispo, type_analyse, 0)
                    totals[mois] += valeur
                    user_total += valeur
                    if valeur < 0:
                        style = 'background:red;color:white;display:block;padding:2px 4px;text-align:center'
                    else:
                        style = 'display:block;padding:2px 4px;text-align:center'
                    html = '<span style="%s">%d</span>' % (style, valeur)
                else:
                    html = ''
                vals['mois_%d' % i] = html
            if user_total < 0:
                style_total = 'background:red;color:white;font-weight:bold;display:block;padding:2px 4px;text-align:center'
            else:
                style_total = 'font-weight:bold;display:block;padding:2px 4px;text-align:center'
            vals['total_12_mois'] = '<span style="%s">%d</span>' % (style_total, user_total)
            self.create(vals)

        # Ligne total (gris)
        grand_total = sum(totals.values())
        total_vals = {'ordre': 9999, 'consultant': '<span style="%s">Total</span>' % grey}
        for i, mois in enumerate(mois_list, 1):
            total_vals['mois_%d' % i] = '<span style="%s">%d</span>' % (grey, totals[mois])
        total_vals['total_12_mois'] = '<span style="%s">%d</span>' % (grey, grand_total)
        self.create(total_vals)

        return {
            'name'     : titres.get(type_analyse, 'Analyse ACR'),
            'type'     : 'ir.actions.act_window',
            'res_model': 'is.analyse.acr',
            'view_mode': 'list',
            'views'    : [(self.env.ref('is_opta_s18.is_analyse_acr_tree').id, 'list')],
        }
