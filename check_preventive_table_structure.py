"""
Script pour vérifier la structure réelle de la table WEB_GMAO_PREVENTIVE
"""
from db import get_db_cursor

with get_db_cursor() as cursor:
    print("Structure de la table WEB_GMAO_PREVENTIVE:")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'WEB_GMAO_PREVENTIVE'
        ORDER BY ORDINAL_POSITION
    """)
    
    columns = cursor.fetchall()
    for col in columns:
        length = f"({col.CHARACTER_MAXIMUM_LENGTH})" if col.CHARACTER_MAXIMUM_LENGTH else ""
        nullable = "NULL" if col.IS_NULLABLE == "YES" else "NOT NULL"
        print(f"{col.COLUMN_NAME:<30} {col.DATA_TYPE}{length:<15} {nullable}")
    
    print()
    print("Colonnes de dates trouvees:")
    date_columns = [col.COLUMN_NAME for col in columns if 'DATE' in col.COLUMN_NAME.upper() or 'DTE' in col.COLUMN_NAME.upper()]
    for col_name in date_columns:
        print(f"  - {col_name}")













