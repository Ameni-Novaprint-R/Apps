"""
Script pour vérifier la structure de la table WEB_ACTIONS
"""
from db import get_db_cursor

try:
    with get_db_cursor() as cursor:
        # Vérifier les colonnes de WEB_ACTIONS
        print("Colonnes de la table WEB_ACTIONS:")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_ACTIONS'
            ORDER BY ORDINAL_POSITION
        """)
        
        colonnes = cursor.fetchall()
        for col in colonnes:
            print(f"  - {col.COLUMN_NAME}: {col.DATA_TYPE} (Nullable: {col.IS_NULLABLE}, Default: {col.COLUMN_DEFAULT})")
        
        print("\nDonnées de l'action ID = 1:")
        cursor.execute("SELECT * FROM WEB_ACTIONS WHERE ID = 1")
        action = cursor.fetchone()
        if action:
            print(f"  {action}")
        else:
            print("  Aucune action trouvée avec ID = 1")
        
        print("\nToutes les actions:")
        cursor.execute("SELECT TOP 5 * FROM WEB_ACTIONS ORDER BY ID")
        actions = cursor.fetchall()
        for act in actions:
            print(f"  {act}")
            
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()
