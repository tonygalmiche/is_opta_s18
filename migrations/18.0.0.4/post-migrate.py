# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


# Copie du mapping code pays -> code devise de la migration 18.0.0.3
# (odoo/addons/base/data/res_country_data.xml), necessaire ici pour
# recorriger res_country.currency_id avec la recherche de devise corrigee.
COUNTRY_CURRENCY = {
    "AD": "EUR", "AE": "AED", "AF": "AFN", "AG": "XCD", "AI": "XCD", "AL": "ALL",
    "AM": "AMD", "AO": "AOA", "AQ": "XCD", "AR": "ARS", "AS": "USD", "AT": "EUR",
    "AU": "AUD", "AW": "AWG", "AX": "EUR", "AZ": "AZN", "BA": "BAM", "BB": "BBD",
    "BD": "BDT", "BE": "EUR", "BF": "XOF", "BG": "EUR", "BH": "BHD", "BI": "BIF",
    "BJ": "XOF", "BL": "EUR", "BM": "BMD", "BN": "BND", "BO": "BOB", "BQ": "USD",
    "BR": "BRL", "BS": "BSD", "BT": "BTN", "BV": "NOK", "BW": "BWP", "BY": "BYN",
    "BZ": "BZD", "CA": "CAD", "CC": "AUD", "CF": "XAF", "CD": "CDF", "CG": "XAF",
    "CH": "CHF", "CI": "XOF", "CK": "NZD", "CL": "CLP", "CM": "XAF", "CN": "CNY",
    "CO": "COP", "CR": "CRC", "CU": "CUP", "CV": "CVE", "CW": "XCG", "CX": "AUD",
    "CY": "EUR", "CZ": "CZK", "DE": "EUR", "DJ": "DJF", "DK": "DKK", "DM": "XCD",
    "DO": "DOP", "DZ": "DZD", "EC": "USD", "EE": "EUR", "EG": "EGP", "EH": "MAD",
    "ER": "ERN", "ES": "EUR", "ET": "ETB", "FI": "EUR", "FJ": "FJD", "FK": "FKP",
    "FM": "USD", "FO": "DKK", "FR": "EUR", "GA": "XAF", "GD": "XCD", "GE": "GEL",
    "GF": "EUR", "GH": "GHS", "GI": "GIP", "GG": "GBP", "GL": "DKK", "GM": "GMD",
    "GN": "GNF", "GP": "EUR", "GQ": "XAF", "GR": "EUR", "GS": "GBP", "GT": "GTQ",
    "GU": "USD", "GW": "XOF", "GY": "GYD", "HK": "HKD", "HM": "AUD", "HN": "HNL",
    "HR": "EUR", "HT": "HTG", "HU": "HUF", "ID": "IDR", "IE": "EUR", "IL": "ILS",
    "IM": "GBP", "IN": "INR", "IO": "USD", "IQ": "IQD", "IR": "IRR", "IS": "ISK",
    "IT": "EUR", "JE": "GBP", "JM": "JMD", "JO": "JOD", "JP": "JPY", "KE": "KES",
    "KG": "KGS", "KH": "KHR", "KI": "AUD", "KM": "KMF", "KN": "XCD", "KP": "KPW",
    "KR": "KRW", "KW": "KWD", "KY": "KYD", "KZ": "KZT", "LA": "LAK", "LB": "LBP",
    "LC": "XCD", "LI": "CHF", "LK": "LKR", "LR": "LRD", "LS": "LSL", "LT": "EUR",
    "LU": "EUR", "LV": "EUR", "LY": "LYD", "MA": "MAD", "MC": "EUR", "MD": "MDL",
    "ME": "EUR", "MF": "EUR", "MG": "MGA", "MH": "USD", "MK": "MKD", "ML": "XOF",
    "MM": "MMK", "MN": "MNT", "MO": "MOP", "MP": "USD", "MQ": "EUR", "MR": "MRU",
    "MS": "XCD", "MT": "EUR", "MU": "MUR", "MV": "MVR", "MW": "MWK", "MX": "MXN",
    "MY": "MYR", "MZ": "MZN", "NA": "NAD", "NC": "XPF", "NE": "XOF", "NF": "AUD",
    "NG": "NGN", "NI": "NIO", "NL": "EUR", "NO": "NOK", "NP": "NPR", "NR": "AUD",
    "NU": "NZD", "NZ": "NZD", "OM": "OMR", "PA": "PAB", "PE": "PEN", "PF": "XPF",
    "PG": "PGK", "PH": "PHP", "PK": "PKR", "PL": "PLN", "PM": "EUR", "PN": "NZD",
    "PR": "USD", "PS": "ILS", "PT": "EUR", "PW": "USD", "PY": "PYG", "QA": "QAR",
    "RE": "EUR", "RO": "RON", "RS": "RSD", "RU": "RUB", "RW": "RWF", "SA": "SAR",
    "SB": "SBD", "SC": "SCR", "SD": "SDG", "SE": "SEK", "SG": "SGD", "SH": "SHP",
    "SI": "EUR", "SJ": "NOK", "SK": "EUR", "SL": "SLE", "SM": "EUR", "SN": "XOF",
    "SO": "SOS", "SR": "SRD", "SS": "SSP", "ST": "STD", "SV": "SVC", "SX": "XCG",
    "SY": "SYP", "SZ": "SZL", "TC": "USD", "TD": "XAF", "TF": "EUR", "TG": "XOF",
    "TH": "THB", "TJ": "TJS", "TK": "NZD", "TM": "TMT", "TN": "TND", "TO": "TOP",
    "TL": "USD", "TR": "TRY", "TT": "TTD", "TV": "AUD", "TW": "TWD", "TZ": "TZS",
    "UA": "UAH", "UG": "UGX", "GB": "GBP", "UM": "USD", "US": "USD", "UY": "UYU",
    "UZ": "UZS", "VA": "EUR", "VC": "XCD", "VE": "VEF", "VG": "USD", "VI": "USD",
    "VN": "VND", "VU": "VUV", "WF": "XPF", "WS": "WST", "YE": "YER", "YT": "EUR",
    "ZA": "ZAR", "ZM": "ZMW", "ZW": "ZIG", "XK": "EUR",
}


def migrate(cr, version):
    """Complete les correctifs des migrations 18.0.0.2 (xmlids base.<CODE>
    pour res.currency) et 18.0.0.3 (res_country.currency_id), qui partagent
    tous les deux le meme bug : `env["res.currency"].search([("name", "=",
    code)])` utilise le contexte de recherche par defaut d'Odoo, qui exclut
    silencieusement les devises inactives (active=False). Or la quasi
    totalite des devises de cette base (toutes sauf EUR/USD/JPY) sont
    inactives : leur xmlid `base.<CODE>` et le `currency_id` des pays
    correspondants (ex: Suisse, Royaume-Uni, Canada...) sont donc restes
    incorrects apres les deux migrations precedentes.

    Ce script refait exactement le meme travail, en ajoutant simplement
    `active_test=False` sur la recherche de devise. Sans effet sur les
    devises/pays deja corrects.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    imd_model = env["ir.model.data"]
    currency_model = env["res.currency"].with_context(active_test=False)

    # --- xmlids base.<CODE> (comme 18.0.0.2) ---------------------------
    currency_xmlids = imd_model.search(
        [("module", "=", "base"), ("model", "=", "res.currency")]
    )
    for imd in currency_xmlids:
        correct_currency = currency_model.search([("name", "=", imd.name)], limit=1)
        if correct_currency and imd.res_id != correct_currency.id:
            imd.write({"res_id": correct_currency.id})

    # --- res_country.currency_id (comme 18.0.0.3) ----------------------
    country_model = env["res.country"]
    for code, currency_code in COUNTRY_CURRENCY.items():
        country = country_model.search([("code", "=", code)], limit=1)
        if not country:
            continue
        correct_currency = currency_model.search([("name", "=", currency_code)], limit=1)
        if correct_currency and country.currency_id.id != correct_currency.id:
            country.currency_id = correct_currency.id
