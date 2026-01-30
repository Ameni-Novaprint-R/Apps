import pyodbc

source_conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=SageSRV\\Graphisoft;'
    'DATABASE=Novaprint;'
    'UID=sa;'
    'PWD=Graphis0ft;'
    'TrustServerCertificate=yes'
)

target_conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=192.168.10.225;'
    'DATABASE=novaprint_restored;'
    'Trusted_Connection=yes;'
    'TrustServerCertificate=yes'
)

source_cursor = source_conn.cursor()
target_cursor = target_conn.cursor()

# Obtenir toutes les colonnes de DEV_AFF (sauf ID_DEVIS pour la comparaison)
source_cursor.execute("""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'DEV_AFF' AND COLUMN_NAME != 'ID_DEVIS'
    ORDER BY ORDINAL_POSITION
""")
non_id_columns = [row[0] for row in source_cursor.fetchall()]

# Lire les lignes depuis la source
source_cursor.execute(f"SELECT {', '.join([f'[{col}]' for col in non_id_columns])} FROM DEV_AFF WHERE ID_DEVIS = 287615")
source_row_287615 = source_cursor.fetchone()

source_cursor.execute(f"SELECT {', '.join([f'[{col}]' for col in non_id_columns])} FROM DEV_AFF WHERE ID_DEVIS = 287636")
source_row_287636 = source_cursor.fetchone()

# Lire les lignes depuis la cible
target_cursor.execute(f"SELECT {', '.join([f'[{col}]' for col in non_id_columns])} FROM DEV_AFF WHERE ID_DEVIS = 287615")
target_row_287615 = target_cursor.fetchone()

target_cursor.execute(f"SELECT {', '.join([f'[{col}]' for col in non_id_columns])} FROM DEV_AFF WHERE ID_DEVIS = 287636")
target_row_287636 = target_cursor.fetchone()

print("Comparaison des lignes DEV_AFF:")
print("="*80)

if source_row_287615 and target_row_287615:
    # Comparer source 287615 vs cible 287615
    differences_615 = []
    for i, col in enumerate(non_id_columns):
        if source_row_287615[i] != target_row_287615[i]:
            differences_615.append(col)
    
    print(f"\nSource ID_DEVIS=287615 vs Cible ID_DEVIS=287615:")
    print(f"  Differences: {len(differences_615)}")
    if differences_615:
        print(f"  Colonnes differentes: {', '.join(differences_615[:5])}")

if source_row_287636 and target_row_287636:
    # Comparer source 287636 vs cible 287636
    differences_636 = []
    for i, col in enumerate(non_id_columns):
        if source_row_287636[i] != target_row_287636[i]:
            differences_636.append(col)
    
    print(f"\nSource ID_DEVIS=287636 vs Cible ID_DEVIS=287636:")
    print(f"  Differences: {len(differences_636)}")
    if differences_636:
        print(f"  Colonnes differentes: {', '.join(differences_636[:5])}")

# Comparer les deux lignes source entre elles
if source_row_287615 and source_row_287636:
    differences_source = []
    for i, col in enumerate(non_id_columns):
        if source_row_287615[i] != source_row_287636[i]:
            differences_source.append(col)
    
    print(f"\nSource ID_DEVIS=287615 vs Source ID_DEVIS=287636:")
    print(f"  Differences: {len(differences_source)}")
    if differences_source:
        print(f"  Colonnes differentes: {', '.join(differences_source[:5])}")
    else:
        print("  ✅ Les deux lignes source sont IDENTIQUES")
        print("  Conclusion: Les deux IDs (287615 et 287636) correspondent a la meme ligne DEVIS")
        print("  Action recommandee: Supprimer la ligne avec ID_DEVIS=287615 en cible")

source_conn.close()
target_conn.close()
