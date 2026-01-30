import pyodbc

target_conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=192.168.10.225;'
    'DATABASE=novaprint_restored;'
    'Trusted_Connection=yes;'
    'TrustServerCertificate=yes'
)

source_conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=SageSRV\\Graphisoft;'
    'DATABASE=Novaprint;'
    'UID=sa;'
    'PWD=Graphis0ft;'
    'TrustServerCertificate=yes'
)

target_cursor = target_conn.cursor()
source_cursor = source_conn.cursor()

# Trouver les colonnes de IDX_DEVIS1
target_cursor.execute("""
    SELECT c.name, ic.key_ordinal
    FROM sys.indexes i
    INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
    WHERE i.object_id = OBJECT_ID('DEVIS') AND i.name = 'IDX_DEVIS1'
    ORDER BY ic.key_ordinal
""")

idx_columns = [row[0] for row in target_cursor.fetchall()]
print(f"Colonnes de IDX_DEVIS1: {idx_columns}")

# Lire la ligne source ID=287636
source_cursor.execute("""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'DEVIS'
    ORDER BY ORDINAL_POSITION
""")
all_columns = [row[0] for row in source_cursor.fetchall()]

# Obtenir les valeurs de l'index pour la ligne source
source_cursor.execute(f"SELECT {', '.join([f'[{col}]' for col in idx_columns])} FROM DEVIS WHERE ID = 287636")
source_idx_values = source_cursor.fetchone()

print(f"\nValeurs de l'index pour ID=287636: {source_idx_values}")

# Trouver la ligne existante en cible avec ces valeurs d'index
where_parts = []
for col, val in zip(idx_columns, source_idx_values):
    if val is None:
        where_parts.append(f"[{col}] IS NULL")
    elif isinstance(val, str):
        escaped_val = val.replace("'", "''")
        where_parts.append(f"[{col}] = '{escaped_val}'")
    elif isinstance(val, bool):
        where_parts.append(f"[{col}] = {1 if val else 0}")
    else:
        where_parts.append(f"[{col}] = {val}")

where_clause = " AND ".join(where_parts)
target_cursor.execute(f"SELECT ID, {', '.join([f'[{col}]' for col in idx_columns])} FROM DEVIS WHERE {where_clause}")
existing_row = target_cursor.fetchone()

if existing_row:
    print(f"\nLigne existante en cible avec ces valeurs d'index:")
    print(f"  ID: {existing_row[0]}")
    print(f"  Valeurs index: {existing_row[1:]}")
    print(f"\nConflit detecte: La ligne ID={existing_row[0]} a les memes valeurs d'index que ID=287636")
else:
    print("\nAucune ligne existante trouvee avec ces valeurs d'index")

source_conn.close()
target_conn.close()
