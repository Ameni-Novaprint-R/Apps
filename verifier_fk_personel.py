"""Script pour vérifier les contraintes de clé étrangère vers personel"""

from db import get_db_cursor

with get_db_cursor() as cursor:
    cursor.execute("""
        SELECT 
            fk.name AS fk_name,
            OBJECT_NAME(fk.parent_object_id) AS parent_table,
            COL_NAME(fc.parent_object_id, fc.parent_column_id) AS parent_column,
            COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS referenced_column
        FROM sys.foreign_keys fk
        INNER JOIN sys.foreign_key_columns fc ON fk.object_id = fc.constraint_object_id
        WHERE fk.referenced_object_id = OBJECT_ID('dbo.personel')
    """)
    
    fks = cursor.fetchall()
    print(f"Contraintes FK vers personel: {len(fks)}")
    print("")
    
    for fk in fks:
        print(f"  - {fk.fk_name}")
        print(f"    Table: {fk.parent_table}")
        print(f"    Colonne: {fk.parent_column} -> personel.{fk.referenced_column}")
        print("")
