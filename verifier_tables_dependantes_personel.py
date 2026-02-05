"""
Script pour identifier toutes les tables qui référencent personel.Matricule comme FK
"""
from db import get_db_cursor

def trouver_tables_dependantes():
    """Trouve toutes les tables avec FK vers personel.Matricule"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                OBJECT_SCHEMA_NAME(f.parent_object_id) AS SchemaName,
                OBJECT_NAME(f.parent_object_id) AS TableName,
                COL_NAME(fc.parent_object_id, fc.parent_column_id) AS ColumnName,
                f.name AS ForeignKeyName,
                OBJECT_SCHEMA_NAME(f.referenced_object_id) AS ReferencedSchemaName,
                OBJECT_NAME(f.referenced_object_id) AS ReferencedTableName,
                COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS ReferencedColumnName,
                f.delete_referential_action_desc AS DeleteAction,
                f.update_referential_action_desc AS UpdateAction
            FROM sys.foreign_keys AS f
            INNER JOIN sys.foreign_key_columns AS fc 
                ON f.object_id = fc.constraint_object_id
            WHERE OBJECT_SCHEMA_NAME(f.referenced_object_id) = 'dbo'
                AND OBJECT_NAME(f.referenced_object_id) = 'personel'
                AND COL_NAME(fc.referenced_object_id, fc.referenced_column_id) = 'Matricule'
            ORDER BY OBJECT_NAME(f.parent_object_id), COL_NAME(fc.parent_object_id, fc.parent_column_id)
        """)
        tables = cursor.fetchall()
        return tables

if __name__ == "__main__":
    print("=" * 80)
    print("RECHERCHE DES TABLES DÉPENDANTES DE personel.Matricule")
    print("=" * 80)
    print()
    try:
        tables = trouver_tables_dependantes()
        if not tables:
            print("Aucune table dépendante trouvée.")
        else:
            print(f"Nombre de tables dépendantes trouvées : {len(tables)}\n")
            for t in tables:
                print(f"Table : {t.TableName}")
                print(f"  Colonne FK : {t.ColumnName}")
                print(f"  Contrainte FK : {t.ForeignKeyName}")
                print(f"  Action DELETE : {t.DeleteAction}")
                print(f"  Action UPDATE : {t.UpdateAction}")
                print()
        print("=" * 80)
    except Exception as e:
        print(f"Erreur : {e}")
        import traceback
        traceback.print_exc()
