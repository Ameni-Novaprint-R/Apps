#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour créer la table WEB_PROJETS dans la base novaprint_restored.

Objectif : Gérer la liste des projets affichés sur la page d'accueil du portail
           et préparer la limitation des accès par utilisateur (liaison avec
           personel et tables à créer ultérieurement).

Colonnes :
- ID        : clé primaire technique, auto-incrémentée
- NumProj   : numéro métier du projet (1–22). Projet 13 = placeholder (archive=1), ID=NumProj.
- CodeProj  : code du projet, partie avant « – » (ex : Projet 1, Projet 11)
- Nom       : nom affiché à l'utilisateur, partie après « – » (ex : Planning, Gestion des Traitements)
- archive   : 0 par défaut (actif), 1 si le projet est désactivé

Contraintes UNIQUE sur NumProj et CodeProj : un projet ne peut exister qu'une seule fois.

Utilise la configuration de db.py (serveur 192.168.10.225, base novaprint_restored).
"""

from db import get_db_cursor

# Données initiales : CodeProj = avant « – », Nom = après « – ». Projet 13 = placeholder (archive=1).
PROJETS_INITIAUX = [
    (1,  'Projet 1',  'Planning', 0),
    (2,  'Projet 2',  'Gestion de commandes', 0),
    (3,  'Projet 3',  'Suivi BAT / Prépresse', 0),
    (4,  'Projet 4',  'Rapport de visite client', 0),
    (5,  'Projet 5',  'Planing production', 0),
    (6,  'Projet 6',  'Programme de voyage', 0),
    (7,  'Projet 7',  'Importation Factures STEG', 0),
    (8,  'Projet 8',  'Stats Devis/Commandes', 0),
    (9,  'Projet 9',  'Suivi Performance Livraison', 0),
    (10, 'Projet 10', 'Contrôle Qualité', 0),
    (11, 'Projet 11', 'Gestion des Traitements', 0),
    (12, 'Projet 12', 'Registre NC & Réclamations Clients', 0),
    (13, 'Projet 13',  'À venir', 1),  # placeholder, à traiter en étape suivante
    (14, 'Projet 14', 'Registre de suivi des déchets', 0),
    (15, 'Projet 15', 'Corrélation Déchets/CA', 0),
    (16, 'Projet 16', 'GMAO (Gestion de la Maintenance)', 0),
    (17, 'Projet 17', 'Fusion de fichiers HTML', 0),
    (18, 'Projet 18', 'Agenda Semainier 2026', 0),
    (19, 'Projet 19', 'Gestion des Dossiers en Cours', 0),
    (20, 'Projet 20', 'Analyse des Dossiers', 0),
    (21, 'Projet 21', 'Mise à jour Base de Données', 0),
    (22, 'Projet 22', 'Gestion des Employés', 0),
]


def creer_table_web_projets():
    """Crée la table WEB_PROJETS et insère les projets initiaux si la table est vide."""

    print("=" * 70)
    print("Création de la table WEB_PROJETS")
    print("=" * 70)
    print()

    try:
        with get_db_cursor() as cursor:
            # Vérifier si la table existe
            cursor.execute("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = 'WEB_PROJETS'
            """)
            table_exists = cursor.fetchone()[0] > 0

            if not table_exists:
                print("[INFO] Création de la table WEB_PROJETS...")
                cursor.execute("""
                    CREATE TABLE dbo.WEB_PROJETS (
                        ID        INT IDENTITY(1,1) NOT NULL,
                        NumProj   INT NOT NULL,
                        CodeProj  NVARCHAR(50) NOT NULL,
                        Nom       NVARCHAR(200) NOT NULL,
                        archive   TINYINT NOT NULL DEFAULT 0,
                        CONSTRAINT PK_WEB_PROJETS PRIMARY KEY (ID),
                        CONSTRAINT UQ_WEB_PROJETS_NumProj  UNIQUE (NumProj),
                        CONSTRAINT UQ_WEB_PROJETS_CodeProj UNIQUE (CodeProj)
                    )
                """)
                cursor.connection.commit()
                print("[OK] Table WEB_PROJETS créée.")
            else:
                print("[INFO] La table WEB_PROJETS existe déjà.")
                # Ajouter UQ sur NumProj si elle manque (table créée avant cette évolution)
                cursor.execute("""
                    SELECT COUNT(*) FROM sys.key_constraints
                    WHERE name = 'UQ_WEB_PROJETS_NumProj' AND parent_object_id = OBJECT_ID('dbo.WEB_PROJETS')
                """)
                if cursor.fetchone()[0] == 0:
                    cursor.execute("ALTER TABLE dbo.WEB_PROJETS ADD CONSTRAINT UQ_WEB_PROJETS_NumProj UNIQUE (NumProj)")
                    cursor.connection.commit()
                    print("[OK] Contrainte UQ_WEB_PROJETS_NumProj ajoutée.")

            # Insérer les projets initiaux uniquement si la table est vide
            cursor.execute("SELECT COUNT(*) FROM dbo.WEB_PROJETS")
            nb = cursor.fetchone()[0]

            if nb == 0:
                print("[INFO] Insertion des projets initiaux...")
                for num_proj, code_proj, nom, archive in PROJETS_INITIAUX:
                    cursor.execute("""
                        INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive)
                        VALUES (?, ?, ?, ?)
                    """, (num_proj, code_proj, nom, archive))
                cursor.connection.commit()
                print(f"[OK] {len(PROJETS_INITIAUX)} projets insérés (Projet 13 = placeholder archive=1, ID=NumProj).")
            else:
                cursor.execute("SELECT COUNT(*) FROM dbo.WEB_PROJETS WHERE NumProj = 13")
                has_13 = cursor.fetchone()[0] > 0
                if nb == 21 and not has_13:
                    print("[INFO] 21 lignes sans Projet 13 : TRUNCATE et ré-insertion des 22 projets pour aligner ID=NumProj.")
                    cursor.execute("TRUNCATE TABLE dbo.WEB_PROJETS")
                    cursor.connection.commit()
                    for num_proj, code_proj, nom, archive in PROJETS_INITIAUX:
                        cursor.execute("""
                            INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive) VALUES (?, ?, ?, ?)
                        """, (num_proj, code_proj, nom, archive))
                    cursor.connection.commit()
                    print(f"[OK] 22 projets réinsérés. ID=NumProj (Projet 13 = placeholder archive=1).")
                else:
                    print(f"[INFO] La table contient déjà {nb} projet(s). Mise à jour CodeProj et Nom.")
                    for num_proj, code_proj, nom, _ in PROJETS_INITIAUX:
                        cursor.execute("""
                            UPDATE dbo.WEB_PROJETS SET CodeProj = ?, Nom = ? WHERE NumProj = ?
                        """, (code_proj, nom, num_proj))
                    cursor.connection.commit()
                    print(f"[OK] CodeProj et Nom mis à jour pour {len(PROJETS_INITIAUX)} projet(s).")

            # Afficher la structure et un résumé
            print()
            print("[STRUCTURE] Colonnes de WEB_PROJETS :")
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH,
                       IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_PROJETS'
                ORDER BY ORDINAL_POSITION
            """)
            for row in cursor.fetchall():
                lon = f"({row.CHARACTER_MAXIMUM_LENGTH})" if row.CHARACTER_MAXIMUM_LENGTH else ""
                defaut = f" DEFAULT {row.COLUMN_DEFAULT}" if row.COLUMN_DEFAULT else ""
                print(f"   - {row.COLUMN_NAME}: {row.DATA_TYPE}{lon} {row.IS_NULLABLE}{defaut}")

            cursor.execute("SELECT COUNT(*) FROM dbo.WEB_PROJETS")
            total = cursor.fetchone()[0]
            print()
            print(f"[OK] Total : {total} projet(s) dans WEB_PROJETS.")
            print("=" * 70)

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        try:
            cursor.connection.rollback()
        except Exception:
            pass
        return False

    return True


if __name__ == "__main__":
    creer_table_web_projets()
