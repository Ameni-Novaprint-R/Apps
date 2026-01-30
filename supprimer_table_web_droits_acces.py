"""
Script pour supprimer complètement la table [WEB_DROITS_ACCES] 
de la base de données novaprint_restored sur le serveur 192.168.10.225
"""
import sys
from db import get_db_cursor

def supprimer_table_web_droits_acces():
    """
    Supprime complètement la table [WEB_DROITS_ACCES] en :
    1. Supprimant toutes les contraintes de clé étrangère qui référencent cette table
    2. Supprimant toutes les contraintes de la table (PK, FK, UNIQUE, CHECK, DEFAULT)
    3. Supprimant la table elle-même
    """
    table_name = "[WEB_DROITS_ACCES]"
    
    try:
        with get_db_cursor() as cursor:
            # Vérifier si la table existe
            cursor.execute("""
                SELECT COUNT(*) as table_exists
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_DROITS_ACCES'
            """)
            result = cursor.fetchone()
            
            if not result or result.table_exists == 0:
                print(f"La table {table_name} n'existe pas dans la base de données.")
                return True
            
            print(f"Suppression de la table {table_name}...")
            
            # 1. Supprimer toutes les contraintes de clé étrangère qui référencent cette table
            print("Étape 1: Recherche des contraintes de clé étrangère référençant cette table...")
            cursor.execute("""
                SELECT 
                    fk.name AS FK_Name,
                    OBJECT_SCHEMA_NAME(fk.parent_object_id) AS Parent_Schema,
                    OBJECT_NAME(fk.parent_object_id) AS Parent_Table
                FROM sys.foreign_keys AS fk
                INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
                INNER JOIN sys.tables AS t ON fkc.referenced_object_id = t.object_id
                WHERE t.name = 'WEB_DROITS_ACCES'
            """)
            
            foreign_keys = cursor.fetchall()
            for fk in foreign_keys:
                fk_name = fk.FK_Name
                parent_table = fk.Parent_Table
                print(f"  - Suppression de la contrainte FK '{fk_name}' dans la table '{parent_table}'...")
                try:
                    cursor.execute(f"ALTER TABLE [{parent_table}] DROP CONSTRAINT [{fk_name}]")
                    print(f"    [OK] Contrainte '{fk_name}' supprimee avec succes")
                except Exception as e:
                    print(f"    [ERREUR] Erreur lors de la suppression de '{fk_name}': {e}")
            
            # 2. Supprimer toutes les contraintes de la table elle-même
            print(f"\nÉtape 2: Recherche des contraintes de la table {table_name}...")
            
            # Récupérer toutes les contraintes (PK, FK, UNIQUE, CHECK, DEFAULT)
            cursor.execute("""
                SELECT 
                    CONSTRAINT_NAME,
                    CONSTRAINT_TYPE
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = 'dbo' 
                AND TABLE_NAME = 'WEB_DROITS_ACCES'
            """)
            
            constraints = cursor.fetchall()
            for constraint in constraints:
                constraint_name = constraint.CONSTRAINT_NAME
                constraint_type = constraint.CONSTRAINT_TYPE
                print(f"  - Suppression de la contrainte '{constraint_name}' (type: {constraint_type})...")
                try:
                    if constraint_type == 'FOREIGN KEY':
                        cursor.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT [{constraint_name}]")
                    elif constraint_type == 'PRIMARY KEY':
                        cursor.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT [{constraint_name}]")
                    elif constraint_type == 'UNIQUE':
                        cursor.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT [{constraint_name}]")
                    elif constraint_type == 'CHECK':
                        cursor.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT [{constraint_name}]")
                    print(f"    [OK] Contrainte '{constraint_name}' supprimee avec succes")
                except Exception as e:
                    print(f"    [ERREUR] Erreur lors de la suppression de '{constraint_name}': {e}")
            
            # Supprimer les contraintes DEFAULT (elles ne sont pas dans TABLE_CONSTRAINTS)
            cursor.execute("""
                SELECT 
                    dc.name AS DefaultConstraintName,
                    c.name AS ColumnName
                FROM sys.default_constraints dc
                INNER JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
                INNER JOIN sys.tables t ON dc.parent_object_id = t.object_id
                WHERE t.name = 'WEB_DROITS_ACCES'
            """)
            
            default_constraints = cursor.fetchall()
            for dc in default_constraints:
                constraint_name = dc.DefaultConstraintName
                column_name = dc.ColumnName
                print(f"  - Suppression de la contrainte DEFAULT '{constraint_name}' sur la colonne '{column_name}'...")
                try:
                    cursor.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT [{constraint_name}]")
                    print(f"    [OK] Contrainte DEFAULT '{constraint_name}' supprimee avec succes")
                except Exception as e:
                    print(f"    [ERREUR] Erreur lors de la suppression de '{constraint_name}': {e}")
            
            # 3. Supprimer les index non-clustered (sauf ceux liés aux contraintes PK/UNIQUE déjà supprimés)
            print(f"\nÉtape 3: Recherche des index de la table {table_name}...")
            cursor.execute("""
                SELECT 
                    i.name AS IndexName,
                    i.type_desc AS IndexType
                FROM sys.indexes i
                INNER JOIN sys.tables t ON i.object_id = t.object_id
                WHERE t.name = 'WEB_DROITS_ACCES'
                AND i.name IS NOT NULL
                AND i.is_primary_key = 0
                AND i.is_unique_constraint = 0
            """)
            
            indexes = cursor.fetchall()
            for idx in indexes:
                index_name = idx.IndexName
                index_type = idx.IndexType
                print(f"  - Suppression de l'index '{index_name}' (type: {index_type})...")
                try:
                    cursor.execute(f"DROP INDEX [{index_name}] ON {table_name}")
                    print(f"    [OK] Index '{index_name}' supprime avec succes")
                except Exception as e:
                    print(f"    [ERREUR] Erreur lors de la suppression de '{index_name}': {e}")
            
            # Valider toutes les modifications avant de supprimer la table
            cursor.connection.commit()
            print(f"\nÉtape 4: Suppression de la table {table_name}...")
            
            # 4. Supprimer la table elle-même
            cursor.execute(f"DROP TABLE {table_name}")
            cursor.connection.commit()
            
            print(f"[OK] La table {table_name} a ete supprimee avec succes!")
            return True
            
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la suppression de la table {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("SUPPRESSION DE LA TABLE [WEB_DROITS_ACCES]")
    print("Base de données: novaprint_restored")
    print("Serveur: 192.168.10.225")
    print("=" * 80)
    print()
    
    # Vérifier si l'argument --force ou --yes est passé
    force = len(sys.argv) > 1 and sys.argv[1] in ['--force', '--yes', '-y']
    
    if not force:
        # Demander confirmation seulement si pas en mode force
        try:
            confirmation = input("Êtes-vous sûr de vouloir supprimer complètement la table [WEB_DROITS_ACCES]? (oui/non): ")
            if confirmation.lower() not in ['oui', 'o', 'yes', 'y']:
                print("Opération annulée.")
                sys.exit(0)
        except EOFError:
            # Si pas d'entrée interactive disponible, demander via argument
            print("ERREUR: Pas d'entrée interactive disponible.")
            print("Utilisez: python supprimer_table_web_droits_acces.py --force")
            sys.exit(1)
    
    print()
    success = supprimer_table_web_droits_acces()
    
    if success:
        print("\n" + "=" * 80)
        print("OPÉRATION TERMINÉE AVEC SUCCÈS")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("OPÉRATION ÉCHOUÉE")
        print("=" * 80)
        sys.exit(1)
