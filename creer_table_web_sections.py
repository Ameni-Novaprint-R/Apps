#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour créer la table WEB_SECTIONS dans la base novaprint_restored.

Objectif : Définir les sections fonctionnelles de chaque projet, en vue de la
           gestion des accès par utilisateur (étape ultérieure).

Colonnes :
- ID      : clé primaire technique, auto-incrémentée
- ID_Proj : clé étrangère vers WEB_PROJETS(ID). Une section appartient à un
            seul projet.
- Nom     : nom de la section affiché à l'utilisateur
- archive : 0 par défaut (actif), 1 si la section est désactivée

Une section appartient obligatoirement à un seul projet.
UNIQUE (ID_Proj, Nom) : évite deux sections de même nom dans un même projet.
La table est créée puis des sections initiales peuvent être insérées
(idempotent : pas de doublons).

Utilise la configuration de db.py (serveur 192.168.10.225, base novaprint_restored).
"""

from db import get_db_cursor


SECTIONS_INITIALES_PAR_NUMPROJ = {
    # Projet 11 - Gestion des Traitements
    11: [
        "Nouvelle fiche de production",
        "Liste des Traitements",
        "Statistiques",
    ],
}


def creer_table_web_sections():
    """Crée la table WEB_SECTIONS (vide). La table WEB_PROJETS doit exister."""

    print("=" * 70)
    print("Création de la table WEB_SECTIONS")
    print("=" * 70)
    print()

    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_SECTIONS'
            """)
            table_exists = cursor.fetchone()[0] > 0

            if not table_exists:
                print("[INFO] Création de la table WEB_SECTIONS...")
                cursor.execute("""
                    CREATE TABLE dbo.WEB_SECTIONS (
                        ID      INT IDENTITY(1,1) NOT NULL,
                        ID_Proj INT NOT NULL,
                        Nom     NVARCHAR(200) NOT NULL,
                        archive TINYINT NOT NULL DEFAULT 0,
                        CONSTRAINT PK_WEB_SECTIONS PRIMARY KEY (ID),
                        CONSTRAINT FK_WEB_SECTIONS_ID_Proj FOREIGN KEY (ID_Proj)
                            REFERENCES dbo.WEB_PROJETS(ID) ON DELETE NO ACTION,
                        CONSTRAINT UQ_WEB_SECTIONS_ID_Proj_Nom UNIQUE (ID_Proj, Nom)
                    )
                """)
                cursor.connection.commit()
                print("[OK] Table WEB_SECTIONS créée.")
            else:
                print("[INFO] La table WEB_SECTIONS existe déjà.")
                cursor.execute("""
                    SELECT COUNT(*) FROM sys.foreign_keys
                    WHERE name = 'FK_WEB_SECTIONS_ID_Proj'
                """)
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        ALTER TABLE dbo.WEB_SECTIONS ADD CONSTRAINT FK_WEB_SECTIONS_ID_Proj
                        FOREIGN KEY (ID_Proj) REFERENCES dbo.WEB_PROJETS(ID) ON DELETE NO ACTION
                    """)
                    cursor.connection.commit()
                    print("[OK] Contrainte FK_WEB_SECTIONS_ID_Proj ajoutée.")
                cursor.execute("""
                    SELECT COUNT(*) FROM sys.key_constraints
                    WHERE name = 'UQ_WEB_SECTIONS_ID_Proj_Nom' AND parent_object_id = OBJECT_ID('dbo.WEB_SECTIONS')
                """)
                if cursor.fetchone()[0] == 0:
                    cursor.execute("ALTER TABLE dbo.WEB_SECTIONS ADD CONSTRAINT UQ_WEB_SECTIONS_ID_Proj_Nom UNIQUE (ID_Proj, Nom)")
                    cursor.connection.commit()
                    print("[OK] Contrainte UQ_WEB_SECTIONS_ID_Proj_Nom ajoutée.")

            # Insérer les sections initiales (idempotent)
            total_inserted = 0
            for numproj, sections in SECTIONS_INITIALES_PAR_NUMPROJ.items():
                cursor.execute("SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = ?", (numproj,))
                proj_row = cursor.fetchone()
                if not proj_row:
                    print(f"[WARN] Projet NumProj={numproj} introuvable dans WEB_PROJETS. Sections non insérées.")
                    continue
                id_proj = proj_row.ID

                for nom in sections:
                    cursor.execute(
                        """
                        INSERT INTO dbo.WEB_SECTIONS (ID_Proj, Nom, archive)
                        SELECT ?, ?, 0
                        WHERE NOT EXISTS (
                            SELECT 1 FROM dbo.WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?
                        )
                        """,
                        (id_proj, nom, id_proj, nom),
                    )
                    if cursor.rowcount and cursor.rowcount > 0:
                        total_inserted += 1

            if total_inserted > 0:
                cursor.connection.commit()
                print(f"[OK] {total_inserted} section(s) initiale(s) insérée(s) dans WEB_SECTIONS.")

            print()
            print("[STRUCTURE] Colonnes de WEB_SECTIONS :")
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH,
                       IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_SECTIONS'
                ORDER BY ORDINAL_POSITION
            """)
            for row in cursor.fetchall():
                lon = f"({row.CHARACTER_MAXIMUM_LENGTH})" if row.CHARACTER_MAXIMUM_LENGTH else ""
                defaut = f" DEFAULT {row.COLUMN_DEFAULT}" if row.COLUMN_DEFAULT else ""
                print(f"   - {row.COLUMN_NAME}: {row.DATA_TYPE}{lon} {row.IS_NULLABLE}{defaut}")

            cursor.execute("SELECT COUNT(*) FROM dbo.WEB_SECTIONS")
            total = cursor.fetchone()[0]
            print()
            print(f"[OK] Total : {total} section(s) dans WEB_SECTIONS.")
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
    creer_table_web_sections()
