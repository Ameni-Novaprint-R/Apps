"""Script de migration: renommer TpsReel en TpsTotal dans WEB_GMAO_REPARATION."""
from db import get_db_cursor

with get_db_cursor() as cursor:
    # Recuperer la definition de la colonne calculee TpsReel
    cursor.execute("""
        SELECT c.name, c.definition
        FROM sys.computed_columns c
        JOIN sys.tables t ON c.object_id = t.object_id
        WHERE t.name = 'WEB_GMAO_REPARATION' AND c.name = 'TpsReel'
    """)
    row = cursor.fetchone()
    if row:
        col_name, definition = row[0], row[1]
        print("Colonne calculee TpsReel trouvee. Definition:", definition[:200] if definition else "(vide)")
        # Supprimer la colonne calculee et recreer sous le nom TpsTotal
        cursor.execute("ALTER TABLE WEB_GMAO_REPARATION DROP COLUMN TpsReel")
        cursor.execute(f"ALTER TABLE WEB_GMAO_REPARATION ADD TpsTotal AS ({definition})")
        cursor.connection.commit()
        print("OK: Colonne TpsReel (calculee) remplacee par TpsTotal.")
    else:
        # Colonne ordinaire
        cursor.execute("""
            SELECT COUNT(*) as n FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'WEB_GMAO_REPARATION' AND COLUMN_NAME = 'TpsReel'
        """)
        if cursor.fetchone().n > 0:
            cursor.execute("EXEC sp_rename 'WEB_GMAO_REPARATION.TpsReel', 'TpsTotal', 'COLUMN'")
            cursor.connection.commit()
            print("OK: Colonne TpsReel renommee en TpsTotal.")
        else:
            cursor.execute("""
                SELECT COUNT(*) as n FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_GMAO_REPARATION' AND COLUMN_NAME = 'TpsTotal'
            """)
            if cursor.fetchone().n > 0:
                print("OK: La colonne TpsTotal existe deja.")
            else:
                print("ATTENTION: Colonne non trouvee.")
