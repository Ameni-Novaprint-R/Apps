import pyodbc

source_conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=SageSRV\\Graphisoft;DATABASE=Novaprint;UID=sa;PWD=Graphis0ft')
target_conn = pyodbc.connect('DRIVER={SQL Server};SERVER=192.168.10.225;DATABASE=novaprint_restored;Trusted_Connection=yes')

source_cursor = source_conn.cursor()
target_cursor = target_conn.cursor()

# IDs dans source
source_cursor.execute("SELECT ID FROM COMMANDES ORDER BY ID")
source_ids = set(r[0] for r in source_cursor.fetchall())
print(f"Source: {len(source_ids)} IDs, min={min(source_ids)}, max={max(source_ids)}")

# IDs dans cible
target_cursor.execute("SELECT ID FROM COMMANDES ORDER BY ID")
target_ids = set(r[0] for r in target_cursor.fetchall())
print(f"Cible: {len(target_ids)} IDs, min={min(target_ids)}, max={max(target_ids)}")

# Difference
missing = source_ids - target_ids
print(f"Manquants: {len(missing)} IDs")
if missing:
    missing_list = sorted(list(missing))[:10]
    print(f"Premiers IDs manquants: {missing_list}")

source_conn.close()
target_conn.close()
