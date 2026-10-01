# Dictionnaire des données de l'ERP Atelier

## Périmètre

Ce document décrit les tables physiques de `atelier.db` au 1er octobre 2026. Les exemples sont fictifs et ne doivent pas être importés tels quels. Les champs `type_production` séparent les lignes des pôles `3D` et `Résine` dans les tables communes.

La base contient 9 tables physiques : les 7 tables métier décrites en premier, plus `pieces_maintenance` et `config_email`. Elle ne contient ni vue SQL ni table métier suffixée `_resine`.

Aucune clé étrangère n'est déclarée dans SQLite. Les liens entre références, commandes et consommables sont conservés principalement sous forme de textes (`reference_complete`, `reference_piece`, `consommable_lie`). Les champs date/heure sont stockés comme texte, pas comme type date SQLite.

**Attention données sensibles :** `config_email.mot_de_passe` contient un secret SMTP. Ne jamais exporter sa valeur dans un document, un ticket ou un exemple partagé. Utiliser un coffre de secrets ou le canal approuvé par l'IT.

## Conventions communes

- `INTEGER PRIMARY KEY` : identifiant SQLite attribué automatiquement.
- Sauf mention contraire, les colonnes sont nullables dans le schéma SQLite.
- `type_production` : valeur attendue par l'application, `3D` ou `Résine`.
- Les dates affichées par les écrans sont généralement au format `JJ/MM/AAAA HH:MM`.
- Les statuts sont stockés en texte. Le schéma ne déclare pas de contrainte `CHECK` ni de liste enum ; les valeurs d'exemple illustrent l'usage observé dans l'application.

## 1. `commandes_clients`

**Rôle :** demandes client destinées à être planifiées/produites. La même référence peut exister pour les deux pôles ; toujours filtrer par `type_production`.

| Colonne | Type SQLite | Null | Défaut | Clé / usage |
|---|---|---:|---|---|
| `id` | INTEGER | Non (PK) | auto | Identifiant technique |
| `type_production` | TEXT | Non | aucun | `3D` ou `Résine` |
| `reference_piece` | TEXT | Oui | NULL | Référence de la demande client |
| `quantite` | INTEGER | Oui | 0 | Quantité demandée |
| `temps_unitaire` | INTEGER | Oui | 0 | Temps estimé par pièce, en minutes dans l'interface |
| `statut` | TEXT | Oui | NULL | État/priorité de la demande |
| `date_saisie` | TEXT | Oui | NULL | Date de saisie |
| `echeance` | TEXT | Oui | NULL | Échéance éventuelle |
| `consommable_lie` | TEXT | Oui | chaîne vide | Nom du consommable associé |
| `quantite_conso` | REAL | Oui | 0 | Consommation estimée par pièce |
| `designation` | TEXT | Oui | chaîne vide | Description de la pièce |
| `date_lancement` | TEXT | Oui | NULL | Date de lancement/planification |

Exemple fictif :
```json
{"id": 101, "type_production": "Résine", "reference_piece": "CMD-EX-001", "quantite": 12, "temps_unitaire": 8, "statut": "Dans le flux", "date_saisie": "01/10/2026 08:30", "echeance": "05/10/2026 17:00", "consommable_lie": "Résine modèle", "quantite_conso": 0.02, "designation": "Guide de démonstration", "date_lancement": null}
```

## 2. `consommables`

**Rôle :** catalogue et stocks de matières/consommables. Les écrans magasin séparent les lignes en fonction de `type_production`.

| Colonne | Type SQLite | Null | Défaut | Clé / usage |
|---|---|---:|---|---|
| `id` | INTEGER | Non (PK) | auto | Identifiant technique |
| `type_production` | TEXT | Non | aucun | `3D` ou `Résine` |
| `nom` | TEXT | Oui | NULL | Nom affiché et utilisé par `consommable_lie` |
| `categorie` | TEXT | Oui | NULL | Famille de consommable |
| `quantite_stock` | REAL | Oui | 0 | Quantité gérée par l'écran consommables |
| `unite` | TEXT | Oui | NULL | Unité de stock |
| `seuil_alerte` | REAL | Oui | 0 | Seuil d'alerte consommables |
| `code_barre` | TEXT | Oui | NULL | Code de scan |
| `type_matiere` | TEXT | Oui | NULL | Type de matière utilisé par le magasin |
| `couleur` | TEXT | Oui | NULL | Couleur de matière |
| `poids_unitaire` | REAL | Oui | 1000 | Quantité ajoutée/retirée par scan dans le magasin |
| `quantite` | REAL | Oui | 0 | Quantité physique utilisée dans les projections de stock du magasin |
| `stock_min` | REAL | Oui | 0 | Stock minimum magasin |
| `lien_achat` | TEXT | Oui | chaîne vide | Lien fournisseur/achat |

**Point à valider avec l'IT/métier :** `quantite_stock` et `quantite` coexistent et sont utilisées par des écrans différents. Ne pas les fusionner ou les renommer sans confirmer leur sémantique fonctionnelle.

Exemple fictif :
```json
{"id": 204, "type_production": "3D", "nom": "Résine démo grise", "categorie": "Matière", "quantite_stock": 5.0, "unite": "Litre", "seuil_alerte": 1.0, "code_barre": "EX-000204", "type_matiere": "Résine", "couleur": "Gris", "poids_unitaire": 1000, "quantite": 5000, "stock_min": 1000, "lien_achat": "https://fournisseur.example/article"}
```

## 3. `historique_production`

**Rôle :** archives de production terminée. Les écrans planning/suivi filtrent ce journal par pôle.

| Colonne | Type SQLite | Null | Défaut | Clé / usage |
|---|---|---:|---|---|
| `id` | INTEGER | Non (PK) | auto | Identifiant technique |
| `type_production` | TEXT | Non | aucun | `3D` ou `Résine` |
| `reference` | TEXT | Oui | NULL | Référence réalisée |
| `quantite` | INTEGER | Oui | 0 | Quantité archivée |
| `temps_unitaire` | INTEGER | Oui | 0 | Temps unitaire en minutes |
| `statut_final` | TEXT | Oui | NULL | Résultat final, par ex. `Terminé` |
| `date_realisation` | TEXT | Oui | NULL | Date de fin |
| `designation` | TEXT | Oui | chaîne vide | Description de la référence |

Exemple fictif :
```json
{"id": 501, "type_production": "3D", "reference": "CDT-001-01", "quantite": 4, "temps_unitaire": 35, "statut_final": "Terminé", "date_realisation": "01/10/2026 15:45", "designation": "Pièce de démonstration"}
```

## 4. `machines`

**Rôle :** parc machine commun ; chaque écran ne lit et ne modifie que les machines de son pôle.

| Colonne | Type SQLite | Null | Défaut | Clé / usage |
|---|---|---:|---|---|
| `id` | INTEGER | Non (PK) | auto | Identifiant technique |
| `type_production` | TEXT | Non | aucun | `3D` ou `Résine` |
| `nom` | TEXT | Oui | NULL | Nom de machine |
| `statut` | TEXT | Oui | NULL | État, utilisé notamment avec `ON`/`OFF` |
| `prefixes_autorises` | TEXT | Oui | NULL | `ALL` ou liste de préfixes séparés par des virgules |

Exemple fictif :
```json
{"id": 12, "type_production": "Résine", "nom": "Machine Résine Démo", "statut": "ON", "prefixes_autorises": "ALL"}
```

## 5. `parametres_atelier`

**Rôle :** horaires de fonctionnement propres à chaque pôle. Une ligne est attendue par valeur de `type_production`.

| Colonne | Type SQLite | Null | Défaut | Clé / usage |
|---|---|---:|---|---|
| `id` | INTEGER | Non (PK) | auto | Identifiant technique |
| `type_production` | TEXT | Non | aucun | `3D` ou `Résine` |
| `heure_debut` | TEXT | Oui | NULL | Heure locale `HH:MM` |
| `heure_fin_lancement` | TEXT | Oui | NULL | Heure locale `HH:MM` |

Exemple fictif :
```json
{"id": 2, "type_production": "Résine", "heure_debut": "07:00", "heure_fin_lancement": "17:30"}
```

## 6. `parametres_references`

**Rôle :** table commune des préfixes, secteurs, catégories et autres paramètres de références. La contrainte unique porte sur `(type_production, nature, prefix)`.

| Colonne | Type SQLite | Null | Défaut | Clé / usage |
|---|---|---:|---|---|
| `id` | INTEGER | Non (PK) | auto | Identifiant technique |
| `type_production` | TEXT | Non | aucun | `3D` ou `Résine` |
| `nature` | TEXT | Non | `parametre` | Application actuelle : `parametre`, `secteur` ou `categorie` |
| `prefix` | TEXT | Oui | NULL | Code court associé à la valeur |
| `nom` | TEXT | Oui | NULL | Libellé affiché |

Correspondance actuelle des natures : `secteur` pour les zones 3D, `categorie` pour les catégories de résines, `parametre` pour les préfixes configurés. Filtrer à la fois par `type_production` et `nature`.

Exemple fictif :
```json
{"id": 34, "type_production": "Résine", "nature": "categorie", "prefix": "DEM", "nom": "Résine de démonstration"}
```

## 7. `references_generees`

**Rôle :** références internes créées et planifiées. Une référence identique est autorisée dans les deux pôles ; ne pas rechercher/modifier une ligne sans son type de production.

| Colonne | Type SQLite | Null | Défaut | Clé / usage |
|---|---|---:|---|---|
| `id` | INTEGER | Non (PK) | auto | Identifiant technique |
| `type_production` | TEXT | Non | aucun | `3D` ou `Résine` |
| `prefix` | TEXT | Oui | NULL | Préfixe secteur/catégorie |
| `reference_complete` | TEXT | Oui | NULL | Référence affichée, par ex. `CDT-001-01` |
| `numero_sequentiel` | INTEGER | Oui | NULL | Numéro de la pièce dans la séquence |
| `version` | INTEGER | Oui | NULL | Version de la référence |
| `quantite` | INTEGER | Oui | 0 | Quantité demandée/planifiée utilisée par l'ERP |
| `temps_unitaire` | INTEGER | Oui | 0 | Temps unitaire en minutes |
| `statut` | TEXT | Oui | NULL | État de la référence/production |
| `date_creation` | TEXT | Oui | NULL | Date de création |
| `consommable_lie` | TEXT | Oui | chaîne vide | Nom du consommable associé |
| `quantite_conso` | REAL | Oui | 0 | Consommation estimée par pièce |
| `designation` | TEXT | Oui | chaîne vide | Description de la pièce |
| `quantite_a_produire` | INTEGER | Oui | 0 | Champ présent dans le schéma ; valider son usage avant toute nouvelle intégration |
| `quantite_produite` | INTEGER | Oui | 0 | Quantité déjà réalisée |
| `date_lancement` | TEXT | Oui | NULL | Date/heure de lancement planifié |

Exemple fictif :
```json
{"id": 42, "type_production": "3D", "prefix": "CDT", "reference_complete": "CDT-001-01", "numero_sequentiel": 1, "version": 1, "quantite": 8, "temps_unitaire": 35, "statut": "Dans le flux", "date_creation": "01/10/2026 08:30", "consommable_lie": "Matière démo", "quantite_conso": 2.5, "designation": "Support de démonstration", "quantite_a_produire": 8, "quantite_produite": 2, "date_lancement": "01/10/2026 10:00"}
```

## 8. `pieces_maintenance`

**Rôle :** pièces détachées et consommables du stock de maintenance, indépendants des consommables de production.

| Colonne | Type SQLite | Null | Défaut | Clé / usage |
|---|---|---:|---|---|
| `ref` | TEXT | Non (PK) | aucun | Référence unique de pièce |
| `designation` | TEXT | Oui | NULL | Description |
| `quantite` | INTEGER | Oui | 0 | Quantité en stock |
| `stock_min` | INTEGER | Oui | 0 | Seuil minimum |
| `lien_achat` | TEXT | Oui | chaîne vide | Lien fournisseur/achat |
| `code_barre` | TEXT | Oui | chaîne vide | Code de scan |

Exemple fictif :
```json
{"ref": "MAINT-EX-01", "designation": "Filtre de démonstration", "quantite": 3, "stock_min": 1, "lien_achat": "https://fournisseur.example/filtre", "code_barre": "EX-MAINT-01"}
```

## 9. `config_email`

**Rôle :** configuration SMTP de l'envoi de courriels. L'application utilise la ligne d'identifiant `1`.

| Colonne | Type SQLite | Null | Défaut | Clé / usage |
|---|---|---:|---|---|
| `id` | INTEGER | Non (PK) | aucun | Identifiant de configuration, généralement `1` |
| `destinataire` | TEXT | Oui | NULL | Adresse du destinataire |
| `expediteur` | TEXT | Oui | NULL | Adresse d'expédition |
| `mot_de_passe` | TEXT | Oui | NULL | Secret SMTP ; ne jamais exposer |
| `serveur_smtp` | TEXT | Oui | `smtp.gmail.com` | Hôte SMTP |
| `port` | INTEGER | Oui | 587 | Port SMTP |
| `heure_envoi` | TEXT | Oui | `08:00` | Heure d'envoi `HH:MM` |

Exemple fictif, secret volontairement remplacé :
```json
{"id": 1, "destinataire": "destinataire@example.test", "expediteur": "erp@example.test", "mot_de_passe": "__SECRET_A_FOURNIR_HORS_DOCUMENT__", "serveur_smtp": "smtp.example.test", "port": 587, "heure_envoi": "08:00"}
```

## Recommandations d'intégration IT

- Ajouter systématiquement `type_production` aux lectures, mises à jour et suppressions des 7 tables communes ; filtrer par `nature` pour `parametres_references`.
- Ne pas supposer que `reference_complete` ou `reference_piece` est unique globalement : le périmètre minimal est le couple `(type_production, référence)`.
- Les dates sont du texte au format applicatif ; prévoir une normalisation ISO 8601 si une intégration externe doit trier ou calculer sur les dates.
- Aucun index métier n'est défini actuellement. Pour des volumes importants, discuter d'index composites sur les colonnes de filtrage les plus utilisées avant de les créer.
- Les exemples JSON sont documentaires ; ils ne constituent pas une spécification d'API ni des contraintes SQL supplémentaires.
