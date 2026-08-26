# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


# Devises ajoutees a la liste standard Odoo apres la version 14.0, absentes
# de la table res_currency de cette base (migree depuis Odoo 14.0). Valeurs
# reprises telles quelles depuis odoo/addons/base/data/res_currency_data.xml.
MISSING_CURRENCIES = {
    "CLF": dict(
        name="CLF", iso_numeric="990", full_name="Unidad de Fomento", symbol="$",
        rounding=0.0001, active=False, position="before",
        currency_unit_label="Peso", currency_subunit_label="Centavos",
    ),
    "CNH": dict(
        name="CNH", full_name="Chinese yuan - Offshore", symbol="¥",
        rounding=0.01, active=False, position="before",
        currency_unit_label="Yuan", currency_subunit_label="Fen",
    ),
    "COU": dict(
        name="COU", iso_numeric="970", full_name="Unidad de Valor Real", symbol="$",
        rounding=0.01, active=False, position="before",
        currency_unit_label="Peso", currency_subunit_label="centavo",
    ),
    "CUC": dict(
        name="CUC", iso_numeric="931", full_name="Cuban convertible peso", symbol="$",
        rounding=0.01, active=False,
        currency_unit_label="Cuban convertible peso",
    ),
    "MRU": dict(
        name="MRU", iso_numeric="478", full_name="Mauritanian ouguiya", symbol="UM",
        rounding=0.01, active=False,
        currency_unit_label="Ouguiya", currency_subunit_label="Khoums",
    ),
    "SLE": dict(
        name="SLE", iso_numeric="694", full_name="Sierra Leonean leone", symbol="Le",
        rounding=0.01, active=False,
        currency_unit_label="Leone", currency_subunit_label="Cents",
    ),
    "SOS": dict(
        name="SOS", iso_numeric="706", full_name="Somali shilling", symbol="Sh.",
        rounding=0.01, active=False,
        currency_unit_label="Shillings", currency_subunit_label="Senti",
    ),
    "SRD": dict(
        name="SRD", iso_numeric="968", full_name="Surinamese dollar", symbol="$",
        rounding=0.01, active=False,
        currency_unit_label="Dollars", currency_subunit_label="Cents",
    ),
    "STN": dict(
        name="STN", iso_numeric="678", full_name="São Tomé and Príncipe dobra", symbol="Db",
        rounding=0.01, active=False,
        currency_unit_label="Dobra", currency_subunit_label="cêntimo",
    ),
    "TMT": dict(
        name="TMT", iso_numeric="934", full_name="Turkmenistan manat", symbol="T",
        rounding=0.01, active=False,
        currency_unit_label="Manat", currency_subunit_label="Tenge",
    ),
    "UYI": dict(
        name="UYI", iso_numeric="940", full_name="Uruguay Peso en Unidades Indexadas", symbol="$",
        rounding=0.0001, active=False,
        currency_unit_label="Peso", currency_subunit_label="centésimo",
    ),
    "UYW": dict(
        name="UYW", iso_numeric="858", full_name="Unidad previsional", symbol="$",
        rounding=0.0001, active=False,
        currency_unit_label="peso", currency_subunit_label="centésimo",
    ),
    "VES": dict(
        name="VES", iso_numeric="937", full_name="Venezuelan bolívar soberano", symbol="Bs",
        rounding=0.01, active=False,
    ),
    "ZIG": dict(
        name="ZIG", full_name="Zimbabwe Gold", symbol="ZiG",
        rounding=0.01, active=False,
        currency_unit_label="ZiGs",
    ),
    "ZMW": dict(
        name="ZMW", iso_numeric="967", full_name="Zambian kwacha", symbol="ZK",
        rounding=0.01, active=False,
        currency_unit_label="Kwacha", currency_subunit_label="Ngwee",
    ),
}


def migrate(cr, version):
    """Repare le mapping ir_model_data <-> res.currency laisse incoherent par
    la migration Odoo 14.0 -> 18.0 (meme defaut que celui deja identifie et
    corrige sur uom.uom/uom.category, cf. is_coheliance18).

    Constat : la table res_currency de cette base est restee celle d'Odoo
    14.0 (nombre de devises et ids inchanges), alors que ir_model_data a ete
    mis a jour avec la liste des devises d'Odoo 18.0 (qui compte davantage
    de devises inserees par ordre alphabetique, ce qui decale tous les ids
    suivants). Resultat : la quasi-totalite des xmlids standards base.<CODE>
    pointent vers la mauvaise ligne (ex: base.EUR pointait vers la ligne
    "ZWD" desactivee, base.USD vers la ligne "EUR").

    Cela ne touche que la table ir_model_data (+ creation des quelques
    devises physiquement absentes, ajoutees a la liste standard apres la
    v14) : aucune devise ni ecriture comptable existante n'est modifiee,
    puisque celles-ci referencent une devise par son id concret, jamais par
    xmlid.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    imd_model = env["ir.model.data"]
    currency_model = env["res.currency"]

    currency_xmlids = imd_model.search(
        [("module", "=", "base"), ("model", "=", "res.currency")]
    )
    for imd in currency_xmlids:
        code = imd.name
        correct_currency = currency_model.search([("name", "=", code)], limit=1)
        if not correct_currency:
            vals = MISSING_CURRENCIES.get(code)
            if not vals:
                continue
            correct_currency = currency_model.create(vals)
        if imd.res_id != correct_currency.id:
            imd.write({"res_id": correct_currency.id})
