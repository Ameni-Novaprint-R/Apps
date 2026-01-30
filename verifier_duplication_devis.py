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

# Obtenir toutes les colonnes (sauf ID)
source_cursor.execute("""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'DEVIS' AND COLUMN_NAME != 'ID'
    ORDER BY ORDINAL_POSITION
""")
non_id_columns = [row[0] for row in source_cursor.fetchall()]

# Lire les deux lignes
source_cursor.execute(f"SELECT {', '.join([f'[{col}]' for col in non_id_columns])} FROM DEVIS WHERE ID = 287636")
source_row = source_cursor.fetchone()

target_cursor.execute(f"SELECT {', '.join([f'[{col}]' for col in non_id_columns])} FROM DEVIS WHERE ID = 287615")
target_row = target_cursor.fetchone()

if source_row and target_row:
    # Comparer les lignes
    differences = []
    for i, col in enumerate(non_id_columns):
        source_val = source_row[i]
        target_val = target_row[i]
        
        # Comparaison en tenant compte des types
        if source_val != target_val:
            # Vérifier si c'est juste une différence de type (ex: 0 vs False)
            if (source_val == 0 and target_val == False) or (source_val == False and target_val == 0):
                continue
            if (source_val == 1 and target_val == True) or (source_val == True and target_val == 1):
                continue
            
            differences.append({
                'column': col,
                'source': source_val,
                'target': target_val
            })
    
    print(f"Comparaison ID=287636 (source) vs ID=287615 (cible):")
    print(f"Nombre de colonnes comparees: {len(non_id_columns)}")
    print(f"Nombre de differences: {len(differences)}")
    
    if len(differences) == 0:
        print("\n✅ Les lignes sont IDENTIQUES (sauf ID)")
        print("   Conclusion: ID=287615 correspond deja a ID=287636")
        print("   Action: Aucune insertion necessaire")
    else:
        print(f"\n⚠️ Les lignes sont DIFFERENTES ({len(differences)} differences)")
        print("\nPremieres differences:")
        for diff in differences[:10]:
            print(f"  {diff['column']}: source={diff['source']}, target={diff['target']}")
        
        if len(differences) > 10:
            print(f"  ... et {len(differences) - 10} autres differences")
else:
    print("Erreur: Impossible de lire une ou les deux lignes")

source_conn.close()
target_conn.close()
