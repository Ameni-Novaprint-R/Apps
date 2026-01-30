import pyodbc

target_conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=192.168.10.225;'
    'DATABASE=novaprint_restored;'
    'Trusted_Connection=yes;'
    'TrustServerCertificate=yes'
)

cursor = target_conn.cursor()

# Vérifier la structure de DEV_AFF
cursor.execute("""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_NAME = 'DEV_AFF' AND CONSTRAINT_NAME LIKE 'PK%'
    ORDER BY ORDINAL_POSITION
""")
pk_columns = [row[0] for row in cursor.fetchall()]
print(f"Clé primaire DEV_AFF: {pk_columns}")

# Vérifier les lignes avec ID_DEVIS = 287615 ou 287636
cursor.execute("""
    SELECT ID_DEVIS, COUNT(*) as nb
    FROM DEV_AFF
    WHERE ID_DEVIS IN (287615, 287636)
    GROUP BY ID_DEVIS
""")
print("\nLignes dans DEV_AFF:")
for row in cursor.fetchall():
    print(f"  ID_DEVIS={row[0]}: {row[1]} lignes")

# Si ID_DEVIS fait partie de la PK, vérifier les conflits
if 'ID_DEVIS' in pk_columns:
    print("\nID_DEVIS fait partie de la PK")
    # Lire les lignes complètes
    cursor.execute(f"""
        SELECT {', '.join([f'[{col}]' for col in pk_columns])}
        FROM DEV_AFF
        WHERE ID_DEVIS IN (287615, 287636)
    """)
    rows = cursor.fetchall()
    print(f"\nLignes detaillees ({len(rows)} lignes):")
    for row in rows:
        print(f"  {dict(zip(pk_columns, row))}")
else:
    print("\nID_DEVIS ne fait pas partie de la PK")
    # Vérifier s'il y a des lignes avec ID_DEVIS=287636 qui auraient le même PK que celles avec 287615
    cursor.execute("""
        SELECT COUNT(*)
        FROM DEV_AFF d1
        INNER JOIN DEV_AFF d2 ON d1.ID_DEVIS = 287615 AND d2.ID_DEVIS = 287636
        WHERE 1=1
    """)
    # Construire la condition de comparaison pour toutes les colonnes PK sauf ID_DEVIS
    other_pk_cols = [col for col in pk_columns if col != 'ID_DEVIS']
    if other_pk_cols:
        join_conditions = []
        for col in other_pk_cols:
            join_conditions.append(f"d1.[{col}] = d2.[{col}]")
        join_clause = " AND ".join(join_conditions)
        
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM DEV_AFF d1
            INNER JOIN DEV_AFF d2 ON d1.ID_DEVIS = 287615 AND d2.ID_DEVIS = 287636
            WHERE {join_clause}
        """)
        conflict_count = cursor.fetchone()[0]
        print(f"\nConflits potentiels (meme PK sauf ID_DEVIS): {conflict_count}")

target_conn.close()
