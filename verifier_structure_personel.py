"""
Script pour vérifier la structure actuelle de la table personel
"""
from db import get_db_cursor

def verifier_structure():
    with get_db_cursor() as cursor:
        print("=" * 80)
        print("STRUCTURE DE LA TABLE personel")
        print("=" * 80)
        print()
        
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                CASE 
                    WHEN COLUMNPROPERTY(OBJECT_ID('dbo.personel'), COLUMN_NAME, 'IsIdentity') = 1 
                    THEN 'OUI' 
                    ELSE 'NON' 
                END AS IS_IDENTITY
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'personel'
            ORDER BY ORDINAL_POSITION
        """)
        
        columns = cursor.fetchall()
        print("Colonnes :")
        for col in columns:
            identity = " (IDENTITY)" if col.IS_IDENTITY == "OUI" else ""
            nullable = "NULL" if col.IS_NULLABLE == "YES" else "NOT NULL"
            length = f"({col.CHARACTER_MAXIMUM_LENGTH})" if col.CHARACTER_MAXIMUM_LENGTH else ""
            default = f" DEFAULT {col.COLUMN_DEFAULT}" if col.COLUMN_DEFAULT else ""
            print(f"  - {col.COLUMN_NAME}: {col.DATA_TYPE}{length} {nullable}{identity}{default}")
        
        print()
        print("=" * 80)
        print("ÉCHANTILLON DES DONNÉES (10 premières lignes)")
        print("=" * 80)
        cursor.execute("SELECT TOP 10 Matricule, Nom, Prenom, Adresse_mail, archive FROM personel ORDER BY Matricule")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Matricule: {row.Matricule}, Nom: {row.Nom or '(NULL)'}, Prenom: {row.Prenom or '(NULL)'}, Adresse_mail: {row.Adresse_mail or '(NULL)'}, archive: {row.archive}")

if __name__ == "__main__":
    verifier_structure()
