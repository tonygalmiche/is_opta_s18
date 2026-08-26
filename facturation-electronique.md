# Problèmes rencontrés pour faire fonctionner la facturation électronique sur `opta-s18` (03/08/2026)

Récapitulatif des trois problèmes distincts rencontrés lors de la mise en place de la facturation électronique (EN16931/Factur-X) sur la base `opta-s18`, et de leurs corrections.

## 1. Installation de `is_facturation_electronique` : vue introuvable (xpath)

### Symptôme

L'installation du module plante avec :

```
odoo.tools.convert.ParseError: while parsing .../is_facturation_electronique/views/account_move_view.xml:3
Erreur lors du parsing ou de la validation de la vue :
L'élément '<xpath expr="//button[@name='action_post'][contains(@invisible, 'display_inactive_currency_warning')]">'
ne peut être localisé dans la vue parente
```

### Cause réelle

Le module maison `is_opta_s18` (vue `is_invoice_form`, `opta-s/is_opta_s18/views/account_invoice_view.xml`) remplace entièrement les deux boutons standards `action_post` d'Odoo (`position="replace"`) par un seul bouton personnalisé (`invisible="state!='diffuse'"`, classe `o_invoice_validate`, libellé "Valider"). Ce bouton perso n'a plus du tout la condition `display_inactive_currency_warning` que la vue de `is_facturation_electronique` essayait de cibler par xpath : l'élément recherché n'existe donc plus dans la vue combinée (`ir.ui.view.get_combined_arch()`).

Vérifié en lecture seule via `odoo-bin shell -d opta-s18` : la vue combinée de `account.move` ne contient bien qu'un seul bouton `action_post`, celui d'`is_opta_s18`.

### Solution appliquée

Dans `is_facturation_electronique/views/account_move_view.xml`, le xpath cible maintenant `(//button[@name='action_post'])[last()]` au lieu de chercher la condition `display_inactive_currency_warning` spécifique à Odoo standard. Ça fonctionne :
- quand `is_opta_s18` est installé (un seul bouton `action_post` restant) ;
- sur un Odoo standard sans `is_opta_s18` (deux boutons `action_post` existent — "Post" pour les écritures, "Confirm" pour les factures ; `[last()]` prend le second, sans dupliquer le bouton ajouté).

## 2. Clic sur "Tester si la facture est valide" : External ID `account_tax_unece.tax_vatex_eu_o` introuvable

### Symptôme

```
ValueError: External ID not found in the system: account_tax_unece.tax_vatex_eu_o
```
levée depuis `account_invoice_en16931/models/account_move.py::_prepare_en16931_speedy`.

### Cause réelle

Il existe **deux copies** du module `account_tax_unece` référencées dans `addons_path` (fichier `/etc/odoo/opta-s18.conf`) :

- `OCA/account_invoice_facturx-18.0.1.1.0/account_tax_unece` — version incomplète, sans `data/unece_tax_vatex.xml` (seulement types et catégories UNECE) ;
- `facturation-electronique/account_tax_unece` — version complète, avec `data/unece_tax_vatex.xml` (contient `tax_vatex_eu_o` et tous les autres codes VATEX).

Le dossier OCA est listé **avant** celui de `facturation-electronique` dans `addons_path`. Odoo charge le premier module trouvé dans l'ordre du path : c'est donc la copie OCA incomplète qui a été installée, pas celle attendue.

Vérifié : `select count(*) from ir_model_data where module='account_tax_unece' and name like 'tax_vatex%'` renvoie `0` alors que 88 autres enregistrements du module (types/catégories) existent bien.

### Solution

Réordonner `addons_path` dans `/etc/odoo/opta-s18.conf` pour que le dossier `facturation-electronique` passe **avant** celui de `OCA/account_invoice_facturx-18.0.1.1.0`, puis mettre à jour le module `account_tax_unece` (Apps → Mettre à jour, ou `-u account_tax_unece`).

## 3. Bouton "Tester..." : pays non renseigné sur "Opta S", puis mauvaise devise à la sélection du pays

### Symptôme

En cliquant sur "Tester si la facture est valide" :

```
Opération invalide
Le pays n'est pas renseigné sur le contact 'Opta S'. Le pays est requis pour EN16931.
```

Puis, en essayant de renseigner le pays sur la fiche société "Opta S" (Paramètres → Sociétés) : sélectionner "France" affiche automatiquement **Devise = ZWD** au lieu d'EUR, et la sauvegarde échoue avec :

```
Oh mince !
Vous ne pouvez pas modifier la devise de la société car certaines écritures comptables existent déjà
```

### Cause réelle

Corruption classique de migration Odoo 14.0 → 18.0 (même famille de problème que celui déjà documenté dans [uom.md](uom.md) pour `uom.uom`/`uom.category`), mais ici sur `res.currency`/`res.country` :

- La table `res_currency` de cette base est restée celle d'Odoo 14.0 (même nombre de lignes, mêmes ids).
- La table `ir_model_data` a été mise à jour avec la liste des devises d'Odoo 18.0 (qui contient davantage de devises insérées par ordre alphabétique), ce qui décale la correspondance code → id pour la quasi-totalité des devises. Exemple constaté : `base.EUR` pointait vers la ligne id 125, qui contient en réalité `ZWD` (inactif) ; `base.USD` pointait vers la ligne id 1, qui contient en réalité `EUR`.
- La colonne `res_country.currency_id` (ex. France) avait elle aussi été **enregistrée directement** avec le mauvais id lors du chargement initial des données (`res_country_data.xml` fait `<field name="currency_id" ref="EUR" />`), donc corrigier uniquement `ir_model_data` ne suffit pas : cette colonne déjà écrite en base reste fausse tant qu'elle n'est pas recorrigée explicitement.

Séquence du bug observée : sélectionner France sur la société → `onchange('country_id')` de `res.company` fait `currency_id = country_id.currency_id` → lit directement la colonne stockée (fausse) → tente de changer la devise de la société → bloqué par la contrainte Odoo (écritures comptables existantes) → toute la sauvegarde échoue, y compris le champ pays.

### Solution appliquée

Deux scripts de migration ajoutés dans le module maison `opta-s/is_opta_s18` (même principe que le correctif déjà fait pour `uom` dans `is_coheliance18`, cf. [uom.md](uom.md)) :

- **`migrations/18.0.0.2/post-migrate.py`** — recorrige le mapping `ir_model_data` pour toutes les devises `base.<CODE>` (recherche la ligne `res_currency` dont le `name` correspond réellement au code, et repointe l'xmlid si besoin). Crée aussi les quelques devises ajoutées après Odoo 14 et physiquement absentes de la table (CLF, CNH, COU, CUC, MRU, SLE, SOS, SRD, STN, TMT, UYI, UYW, VES, ZIG, ZMW), avec les valeurs reprises du fichier core `res_currency_data.xml`.
- **`migrations/18.0.0.3/post-migrate.py`** — recorrige la colonne `res_country.currency_id` pour les 250 pays, d'après le mapping code pays → code devise repris tel quel de `res_country_data.xml`.

Ces scripts ne touchent que `ir_model_data` et les colonnes `currency_id`/`res_country` : aucune écriture comptable ni devise métier existante n'est modifiée (les écritures référencent une devise par son id concret, jamais par xmlid).

**Important** : comme pour `uom`, seule la résolution *future* (`env.ref()`, sélection d'un pays dans un formulaire) est corrigée. Un enregistrement déjà créé par le passé avec la mauvaise devise (résolue via un xmlid alors corrompu) garde sa valeur figée — à auditer au cas par cas si une incohérence de devise est suspectée sur une donnée existante.

## Où voir la liste des pays et de leurs devises dans Odoo

Mode développeur activé : **Paramètres → Technique → Localisation → Pays**. La colonne Devise n'est pas affichée par défaut dans la vue liste : l'ajouter via l'icône de colonnes (⚙️), ou ouvrir chaque fiche pays. Les devises elles-mêmes : **Paramètres → Technique → Devises**, ou **Comptabilité → Configuration → Devises**.

## 4. Ligne de facture : "should have exactly one VAT tax and not 0"

Cause : la taxe appliquée sur la ligne n'a pas son champ **Type de taxe de l'UNECE** renseigné à `VAT`. Solution : appliquer une taxe dont `unece_type_id` = `[VAT] Value added tax`.

## 5. Configuration UNECE d'une taxe "0% intracom"

- **Type de taxe de l'UNECE** : `VAT`
- **Catégorie de taxe de l'UNECE** : `K` (VAT exempt for intra-community supply)

Le champ **Motif d'exonération TVA** se remplit alors automatiquement sur `VATEX-EU-IC` (`account_tax_unece/models/account_tax.py::_compute_unece_vatex_id`).

## 6. Échec schématron BR-IC-02 (n° TVA client manquant)

```
[BR-IC-02] Invoice line VAT category "Intra-community supply" shall contain the
Seller VAT Identifier (BT-31) ... and the Buyer VAT identifier (BT-48).
```

Cause : catégorie `K` utilisée sur la ligne, mais le client n'a pas de n° de TVA renseigné (champ `vat` vide).

Solution : renseigner le n° de TVA du client. **À vérifier sur le fond** : la catégorie `K` ne s'applique qu'aux clients assujettis dans un autre État membre UE — si le client est français (ex. organisme public), ce n'est probablement pas la bonne taxe/catégorie à utiliser.
