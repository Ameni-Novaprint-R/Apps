"""
Script pour ajouter la colonne MDP à la table personel si elle n'existe pas
"""
from db import get_db_cursor

try:
    with get_db_cursor() as cursor:
        print("Verification de la colonne MDP dans la table personel...")
        
        # Vérifier si la colonne existe
        cursor.execute("""
            SELECT COUNT(*) as col_exists
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' 
            AND TABLE_NAME = 'personel' 
            AND COLUMN_NAME = 'MDP'
        """)
        result = cursor.fetchone()
        
        if result and result.col_exists > 0:
            print("  [OK] La colonne MDP existe deja dans la table personel")
            
            # Vérifier le type de données
            cursor.execute("""
                SELECT DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo' 
                AND TABLE_NAME = 'personel' 
                AND COLUMN_NAME = 'MDP'
            """)
            col_info = cursor.fetchone()
            print(f"  Type: {col_info.DATA_TYPE}")
            print(f"  Longueur max: {col_info.CHARACTER_MAXIMUM_LENGTH}")
            print(f"  Nullable: {col_info.IS_NULLABLE}")
        else:
            print("  Ajout de la colonne MDP...")
            cursor.execute("""
                ALTER TABLE [dbo].[personel]
                ADD [MDP] NVARCHAR(255) NULL
            """)
            cursor.connection.commit()
            print("  [OK] Colonne MDP ajoutee avec succes!")
            print("  Type: NVARCHAR(255) NULL")
            print("  Note: Les mots de passe seront stockes en hachage bcrypt (60 caracteres)")
        
        print("\nVerification terminee.")
        
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()
