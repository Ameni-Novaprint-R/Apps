import pyodbc

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=SageSRV\\Graphisoft;DATABASE=Novaprint;UID=sa;PWD=Graphis0ft')
cursor = conn.cursor()
cursor.execute("""
    SELECT COLUMN_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + QUOTENAME(CONSTRAINT_NAME)), 'IsPrimaryKey') = 1
    AND TABLE_NAME = 'COMMANDES'
    ORDER BY ORDINAL_POSITION
""")
print("Cles primaires COMMANDES:", [r[0] for r in cursor.fetchall()])
conn.close()
