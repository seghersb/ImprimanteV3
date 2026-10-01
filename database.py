import sqlite3


POLES = {"3D": "3D", "resine": "Résine"}

TABLES_UNIFIEES = {
    "parametres_references": """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_production TEXT NOT NULL,
        nature TEXT NOT NULL DEFAULT 'parametre',
        prefix TEXT,
        nom TEXT,
        UNIQUE(type_production, nature, prefix)
    """,
    "references_generees": """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_production TEXT NOT NULL,
        prefix TEXT,
        reference_complete TEXT,
        numero_sequentiel INTEGER,
        version INTEGER,
        quantite INTEGER DEFAULT 0,
        temps_unitaire INTEGER DEFAULT 0,
        statut TEXT,
        date_creation TEXT,
        consommable_lie TEXT DEFAULT '',
        quantite_conso REAL DEFAULT 0,
        designation TEXT DEFAULT '',
        quantite_a_produire INTEGER DEFAULT 0,
        quantite_produite INTEGER DEFAULT 0,
        date_lancement TEXT
    """,
    "commandes_clients": """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_production TEXT NOT NULL,
        reference_piece TEXT,
        quantite INTEGER DEFAULT 0,
        temps_unitaire INTEGER DEFAULT 0,
        statut TEXT,
        date_saisie TEXT,
        echeance TEXT,
        consommable_lie TEXT DEFAULT '',
        quantite_conso REAL DEFAULT 0,
        designation TEXT DEFAULT '',
        date_lancement TEXT
    """,
    "machines": """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_production TEXT NOT NULL,
        nom TEXT,
        statut TEXT,
        prefixes_autorises TEXT
    """,
    "historique_production": """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_production TEXT NOT NULL,
        reference TEXT,
        quantite INTEGER DEFAULT 0,
        temps_unitaire INTEGER DEFAULT 0,
        statut_final TEXT,
        date_realisation TEXT,
        designation TEXT DEFAULT ''
    """,
    "parametres_atelier": """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_production TEXT NOT NULL,
        heure_debut TEXT,
        heure_fin_lancement TEXT
    """,
    "consommables": """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_production TEXT NOT NULL,
        nom TEXT,
        categorie TEXT,
        quantite_stock REAL DEFAULT 0,
        unite TEXT,
        seuil_alerte REAL DEFAULT 0,
        code_barre TEXT,
        type_matiere TEXT,
        couleur TEXT,
        poids_unitaire REAL DEFAULT 1000,
        quantite REAL DEFAULT 0,
        stock_min REAL DEFAULT 0,
        lien_achat TEXT DEFAULT ''
    """,
}

ALIAS_TABLES = {
    "parametres_references": "parametres_references_resine",
    "references_generees": "references_generees_resine",
    "commandes_clients": "commandes_clients_resine",
    "machines": "machines_resine",
    "historique_production": "historique_production_resine",
    "parametres_atelier": "parametres_atelier_resine",
    "consommables": "consommables_resine",
}

VALEURS_DEFAUT_VUES = {
    "quantite": "0",
    "temps_unitaire": "0",
    "quantite_conso": "0",
    "designation": "''",
    "quantite_a_produire": "0",
    "quantite_produite": "0",
    "quantite_stock": "0",
    "poids_unitaire": "1000",
    "stock_min": "0",
    "consommable_lie": "''",
    "lien_achat": "''",
}


def _objet_sqlite(cursor, nom):
    return cursor.execute(
        "SELECT type FROM sqlite_master WHERE name = ?", (nom,)
    ).fetchone()


def _copier_anciennes_lignes(cursor, source, cible, pole):
    colonnes_source = [
        ligne[1] for ligne in cursor.execute(f'PRAGMA table_info("{source}")')
    ]
    colonnes_cible = [
        ligne[1] for ligne in cursor.execute(f'PRAGMA table_info("{cible}")')
    ]
    colonnes = [
        colonne for colonne in colonnes_source
        if colonne in colonnes_cible and colonne not in ("id", "type_production")
    ]
    if not colonnes:
        return

    colonnes_sql = ", ".join(f'"{colonne}"' for colonne in colonnes)
    placeholders = ", ".join("?" for _ in range(len(colonnes) + 1))
    lignes = cursor.execute(
        f'SELECT {colonnes_sql} FROM "{source}" ORDER BY id'
    ).fetchall()
    cursor.executemany(
        f'INSERT INTO "{cible}" (type_production, {colonnes_sql}) VALUES ({placeholders})',
        [(pole, *ligne) for ligne in lignes],
    )


def _migrer_anciennes_tables(cursor):
    for table, definition in TABLES_UNIFIEES.items():
        resine = ALIAS_TABLES[table]
        unifiee = f"{table}_unifiee"

        for nom in (table, resine):
            objet = _objet_sqlite(cursor, nom)
            if objet and objet[0] == "view":
                cursor.execute(f'DROP VIEW "{nom}"')

        objet_cible = _objet_sqlite(cursor, table)
        objet_unifie = _objet_sqlite(cursor, unifiee)
        objet_resine = _objet_sqlite(cursor, resine)

        if objet_cible and objet_cible[0] == "table":
            colonnes = [
                ligne[1] for ligne in cursor.execute(f'PRAGMA table_info("{table}")')
            ]
            if "type_production" in colonnes:
                if objet_resine and objet_resine[0] == "table":
                    _copier_anciennes_lignes(cursor, resine, table, POLES["resine"])
                    cursor.execute(f'DROP TABLE "{resine}"')
                continue

            temporaire = f"__fusion_{table}"
            cursor.execute(f'DROP TABLE IF EXISTS "{temporaire}"')
            cursor.execute(f'CREATE TABLE "{temporaire}" ({definition})')
            _copier_anciennes_lignes(cursor, table, temporaire, POLES["3D"])
            if objet_resine and objet_resine[0] == "table":
                _copier_anciennes_lignes(cursor, resine, temporaire, POLES["resine"])
                cursor.execute(f'DROP TABLE "{resine}"')
            cursor.execute(f'DROP TABLE "{table}"')
            cursor.execute(f'ALTER TABLE "{temporaire}" RENAME TO "{table}"')
        elif objet_unifie and objet_unifie[0] == "table":
            cursor.execute(f'ALTER TABLE "{unifiee}" RENAME TO "{table}"')
            if objet_resine and objet_resine[0] == "table":
                _copier_anciennes_lignes(cursor, resine, table, POLES["resine"])
                cursor.execute(f'DROP TABLE "{resine}"')
        else:
            cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({definition})')
            if objet_resine and objet_resine[0] == "table":
                _copier_anciennes_lignes(cursor, resine, table, POLES["resine"])
                cursor.execute(f'DROP TABLE "{resine}"')

    _unifier_parametres_references(cursor)


def _unifier_parametres_references(cursor):
    colonnes = [
        ligne[1] for ligne in cursor.execute('PRAGMA table_info("parametres_references")')
    ]
    if "nature" not in colonnes:
        temporaire = "__parametres_references_v2"
        cursor.execute(f'DROP TABLE IF EXISTS "{temporaire}"')
        cursor.execute(
            f'CREATE TABLE "{temporaire}" ({TABLES_UNIFIEES["parametres_references"]})'
        )
        lignes = cursor.execute(
            "SELECT type_production, prefix, nom FROM parametres_references ORDER BY id"
        ).fetchall()
        cursor.executemany(
            f'INSERT INTO "{temporaire}" (type_production, prefix, nom) VALUES (?, ?, ?)',
            lignes,
        )
        cursor.execute('DROP TABLE "parametres_references"')
        cursor.execute(
            f'ALTER TABLE "{temporaire}" RENAME TO "parametres_references"'
        )

    tables_reference = (
        ("zones_travail", "3D", "secteur", "prefixe"),
        ("categories_resines", "Résine", "categorie", "prefixe"),
        ("secteurs", "3D", "secteur", "code_3_lettres"),
        ("secteurs_resine", "Résine", "secteur", "code_3_lettres"),
    )
    for source, pole, nature, colonne_prefixe in tables_reference:
        objet = _objet_sqlite(cursor, source)
        if not objet or objet[0] != "table":
            continue
        lignes = cursor.execute(
            f'SELECT nom, "{colonne_prefixe}" FROM "{source}" ORDER BY id'
        ).fetchall()
        cursor.executemany(
            "INSERT OR REPLACE INTO parametres_references (type_production, nature, prefix, nom) VALUES (?, ?, ?, ?)",
            [(pole, nature, prefixe, nom) for nom, prefixe in lignes],
        )
        cursor.execute(f'DROP TABLE "{source}"')


def initialiser_base():
    conn = sqlite3.connect("atelier.db", timeout=30.0)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        _migrer_anciennes_tables(cursor)

        consommables_defaut = [
            ("Résine Standard Grey", "Résine 3D", 5.0, "Litre", 1.5),
            ("Résine Biocompatible", "Résine 3D", 2.0, "Litre", 1.0),
            ("Alcool Isopropylique (IPA)", "Nettoyage", 25.0, "Litre", 5.0),
            ("Film FEP (Rapidshape)", "Pièce détachée", 4.0, "Unité", 1.0),
            ("Sachets d'ensachage", "Emballage", 250.0, "Unité", 50.0),
        ]
        secteurs_defaut = [
            ("CDT", "Cellule de thermoformage"),
            ("CDD", "Cellule de découpe"),
            ("CDN", "Cellule de nettoyage / ensachage"),
            ("LMA", "Lavage manuel"),
            ("TRI", "Triosmile"),
            ("BAR", "Puce de suivi à intégrer - Baracoda"),
            ("FIN", "Finisher / Finition"),
            ("BAD", "Projet brosse à dents personnalisée"),
            ("PRW", "Prodways LD20 / D100"),
            ("RSH", "Rapidshape"),
            ("OUT", "Outilages"),
            ("THE", "Thermoformage"),
        ]

        for pole in POLES.values():
            cursor.execute(
                "SELECT COUNT(*) FROM consommables WHERE type_production = ?", (pole,)
            )
            if cursor.fetchone()[0] == 0:
                cursor.executemany(
                    "INSERT INTO consommables (type_production, nom, categorie, quantite_stock, unite, seuil_alerte) VALUES (?, ?, ?, ?, ?, ?)",
                    [(pole, *ligne) for ligne in consommables_defaut],
                )

            cursor.execute(
                "SELECT COUNT(*) FROM parametres_atelier WHERE type_production = ?", (pole,)
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO parametres_atelier (type_production, heure_debut, heure_fin_lancement) VALUES (?, '07:00', '17:30')",
                    (pole,),
                )

            cursor.executemany(
                "INSERT OR IGNORE INTO parametres_references (type_production, nature, prefix, nom) VALUES (?, 'parametre', ?, ?)",
                [(pole, *ligne) for ligne in secteurs_defaut],
            )

        cursor.execute(
            "SELECT COUNT(*) FROM parametres_references WHERE type_production = '3D' AND nature = 'secteur'"
        )
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO parametres_references (type_production, nature, prefix, nom) VALUES ('3D', 'secteur', ?, ?)",
                secteurs_defaut,
            )

        categories_resines = [
            ("Résine Modèle", "MOD"),
            ("Résine Guide Chirurgical", "GUI"),
            ("Résine Calcinable (Castable)", "CAL"),
            ("Résine Gouttière (Splint)", "SPL"),
            ("Résine Provisoire", "PRO"),
            ("Résine Porte-Empreinte", "POR"),
        ]
        cursor.execute(
            "SELECT COUNT(*) FROM parametres_references WHERE type_production = 'Résine' AND nature = 'categorie'"
        )
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO parametres_references (type_production, nature, prefix, nom) VALUES ('Résine', 'categorie', ?, ?)",
                [(prefixe, nom) for nom, prefixe in categories_resines],
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    initialiser_base()
    print("Base de données initialisée avec succès.")