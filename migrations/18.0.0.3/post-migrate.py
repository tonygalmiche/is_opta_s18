# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


# Mapping code pays (ISO2 majuscule) -> code devise, repris tel quel depuis
# odoo/addons/base/data/res_country_data.xml (champ currency_id ref="...").
# La migration 18.0.0.2 a corrige le mapping ir_model_data <-> res.currency,
# mais la colonne res_country.currency_id avait deja ete enregistree avec le
# mauvais id lors du chargement initial des donnees (avant correction des
# xmlids) : elle n'est pas revalorisee automatiquement par le fix precedent
# et doit etre recorrigee explicitement ici.
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
    """Recorrige res_country.currency_id, deja enregistre avec le mauvais id
    de devise lors du chargement initial des donnees (avant la correction du
    mapping ir_model_data apportee par la migration 18.0.0.2). Ne touche
    aucune donnee metier : seule la colonne currency_id des pays est mise a
    jour, vers la devise reellement correspondante d'apres la donnee
    standard Odoo (res_country_data.xml).
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    country_model = env["res.country"]
    currency_model = env["res.currency"]

    for country in country_model.search([]):
        code = country.code.upper() if country.code else False
        currency_code = COUNTRY_CURRENCY.get(code)
        if not currency_code:
            continue
        correct_currency = currency_model.search([("name", "=", currency_code)], limit=1)
        if correct_currency and country.currency_id.id != correct_currency.id:
            country.currency_id = correct_currency.id
