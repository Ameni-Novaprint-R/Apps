"""Vérifier la structure de WEB_GMAO"""

from db import get_db_cursor

with get_db_cursor() as cursor:
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'WEB_GMAO'
        ORDER BY COLUMN_NAME
    """)
    
    print("Colonnes de WEB_GMAO:")
    for row in cursor.fetchall():
        print(f"  - {row.COLUMN_NAME}")
