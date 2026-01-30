#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script Python pour ajouter les colonnes CodeProj et Nom_SECTIONS à WEB_ACTIONS
dans la base novaprint_restored.

Ces colonnes affichent :
- CodeProj : la valeur de CodeProj de WEB_PROJETS (via WEB_SECTIONS)
- Nom_SECTIONS : la valeur de Nom de WEB_SECTIONS
"""

from db import get_db_cursor

def ajouter_colonnes_codeproj_nom_sections():
    """Ajoute les colonnes CodeProj et Nom_SECTIONS à WEB_ACTIONS"""
    
    print("=" * 70)
    print("AJOUT DES COLONNES CodeProj ET Nom_SECTIONS À WEB_ACTIONS")
    print("=" * 70)
    print()
    
    try:
        with get_db_cursor() as cursor:
            # Déterminer le nom de la table (WEB_ACTIONS ou WEB_DROITS_ACCES)
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME IN ('WEB_ACTIONS', 'WEB_DROITS_ACCES')
            """)
            table_row = cursor.fetchone()
            if not table_row:
                print("[ERREUR] Ni WEB_ACTIONS ni WEB_DROITS_ACCES n'existent.")
                return False
            
            table_name = table_row.TABLE_NAME
            print(f"[INFO] Table trouvée: {table_name}")
            print()
            
            # Étape 1: Ajouter la colonne CodeProj
            print("[1/2] Ajout de la colonne CodeProj...")
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ? AND COLUMN_NAME = 'CodeProj'
            """, (table_name,))
            
            if cursor.fetchone()[0] > 0:
                print("  ⚠ La colonne CodeProj existe déjà.")
            else:
                cursor.execute(f"ALTER TABLE dbo.{table_name} ADD CodeProj NVARCHAR(50) NULL")
                cursor.connection.commit()
                print("  ✓ Colonne CodeProj ajoutée.")
            
            print()
            
            # Étape 2: Ajouter la colonne Nom_SECTIONS
            print("[2/2] Ajout de la colonne Nom_SECTIONS...")
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ? AND COLUMN_NAME = 'Nom_SECTIONS'
            """, (table_name,))
            
            if cursor.fetchone()[0] > 0:
                print("  ⚠ La colonne Nom_SECTIONS existe déjà.")
            else:
                cursor.execute(f"ALTER TABLE dbo.{table_name} ADD Nom_SECTIONS NVARCHAR(200) NULL")
                cursor.connection.commit()
                print("  ✓ Colonne Nom_SECTIONS ajoutée.")
            
            print()
            
            # Étape 3: Mettre à jour les valeurs existantes
            print("[3/3] Mise à jour des valeurs existantes...")
            cursor.execute(f"""
                UPDATE dbo.{table_name}
                SET 
                    CodeProj = (
                        SELECT p.CodeProj
                        FROM dbo.WEB_SECTIONS s
                        INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                        WHERE s.ID = {table_name}.ID_Section
                    ),
                    Nom_SECTIONS = (
                        SELECT s.Nom
                        FROM dbo.WEB_SECTIONS s
                        WHERE s.ID = {table_name}.ID_Section
                    )
                WHERE ID_Section IS NOT NULL
            """)
            row_count = cursor.rowcount
            cursor.connection.commit()
            print(f"  ✓ {row_count} ligne(s) mise(s) à jour.")
            print()
            
            # Étape 4: Créer un trigger pour maintenir la synchronisation
            print("[4/4] Création du trigger de synchronisation...")
            
            # Supprimer le trigger s'il existe déjà
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sys.triggers 
                WHERE name = 'TRG_WEB_ACTIONS_UPDATE_CODE_NOM'
            """)
            if cursor.fetchone()[0] > 0:
                cursor.execute("DROP TRIGGER TRG_WEB_ACTIONS_UPDATE_CODE_NOM")
                cursor.connection.commit()
                print("  ⚠ Ancien trigger supprimé.")
            
            # Créer le trigger
            trigger_sql = f"""
                CREATE TRIGGER TRG_WEB_ACTIONS_UPDATE_CODE_NOM
                ON dbo.{table_name}
                AFTER INSERT, UPDATE
                AS
                BEGIN
                    SET NOCOUNT ON;
                    
                    UPDATE wa
                    SET 
                        CodeProj = (
                            SELECT p.CodeProj
                            FROM dbo.WEB_SECTIONS s
                            INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                            WHERE s.ID = wa.ID_Section
                        ),
                        Nom_SECTIONS = (
                            SELECT s.Nom
                            FROM dbo.WEB_SECTIONS s
                            WHERE s.ID = wa.ID_Section
                        )
                    FROM dbo.{table_name} wa
                    INNER JOIN inserted i ON i.ID = wa.ID
                    WHERE wa.ID_Section IS NOT NULL;
                END
            """
            cursor.execute(trigger_sql)
            cursor.connection.commit()
            print("  ✓ Trigger TRG_WEB_ACTIONS_UPDATE_CODE_NOM créé.")
            print()
            
            # Vérification
            print("=" * 70)
            print("VÉRIFICATION")
            print("=" * 70)
            print()
            
            print("Structure de la table:")
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """, (table_name,))
            
            for row in cursor.fetchall():
                length = f"({row.CHARACTER_MAXIMUM_LENGTH})" if row.CHARACTER_MAXIMUM_LENGTH else ""
                print(f"  - {row.COLUMN_NAME}: {row.DATA_TYPE}{length} ({row.IS_NULLABLE})")
            
            print()
            print("Exemple de données avec les nouvelles colonnes:")
            cursor.execute(f"""
                SELECT TOP 5
                    wa.ID,
                    wa.ID_Section,
                    wa.CodeProj,
                    wa.Nom_SECTIONS,
                    wa.Action,
                    wa.archive
                FROM dbo.{table_name} wa
                ORDER BY wa.ID
            """)
            
            for row in cursor.fetchall():
                print(f"  ID={row.ID}, ID_Section={row.ID_Section}, CodeProj={row.CodeProj}, Nom_SECTIONS={row.Nom_SECTIONS}, Action={row.Action}")
            
            print()
            print("=" * 70)
            print("MODIFICATIONS TERMINÉES AVEC SUCCÈS")
            print("=" * 70)
            print()
            print("Les colonnes CodeProj et Nom_SECTIONS ont été ajoutées et remplies.")
            print("Un trigger a été créé pour maintenir ces valeurs à jour automatiquement.")
            print()
            
            return True
            
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    ajouter_colonnes_codeproj_nom_sections()
