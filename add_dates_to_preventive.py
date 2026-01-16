"""
Script pour ajouter les colonnes DtePrev et DteReal à la table WEB_GMAO_PREVENTIVE
"""

from db import get_db_cursor

def add_dates_to_preventive():
    """Ajoute les colonnes DtePrev et DteReal à la table WEB_GMAO_PREVENTIVE"""
    
    try:
        with get_db_cursor() as cursor:
            # Vérifier si les colonnes existent déjà
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'WEB_GMAO_PREVENTIVE' 
                AND COLUMN_NAME IN ('DtePrev', 'DteReal')
            """)
            
            existing_columns = [row.COLUMN_NAME for row in cursor.fetchall()]
            
            print("📝 Ajout des colonnes de dates...")
            
            # Ajouter DtePrev si elle n'existe pas
            if 'DtePrev' not in existing_columns:
                cursor.execute("ALTER TABLE dbo.WEB_GMAO_PREVENTIVE ADD DtePrev DATETIME NULL")
                print("✅ Colonne DtePrev ajoutée")
            else:
                print("⚠️ La colonne DtePrev existe déjà")
            
            # Ajouter DteReal si elle n'existe pas
            if 'DteReal' not in existing_columns:
                cursor.execute("ALTER TABLE dbo.WEB_GMAO_PREVENTIVE ADD DteReal DATETIME NULL")
                print("✅ Colonne DteReal ajoutée")
            else:
                print("⚠️ La colonne DteReal existe déjà")
            
            cursor.connection.commit()
            
            # Créer les index
            print("\n📝 Création des index...")
            indexes = [
                ("IX_WEB_GMAO_PREVENTIVE_DtePrev", "DtePrev"),
                ("IX_WEB_GMAO_PREVENTIVE_DteReal", "DteReal")
            ]
            
            for index_name, column in indexes:
                try:
                    cursor.execute(f"""
                        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = '{index_name}')
                        CREATE NONCLUSTERED INDEX {index_name} 
                        ON dbo.WEB_GMAO_PREVENTIVE({column})
                    """)
                    print(f"✅ Index {index_name} créé")
                except Exception as e:
                    print(f"⚠️ Erreur lors de la création de l'index {index_name}: {e}")
            
            cursor.connection.commit()
            
            print("\n✅ Extension de la table WEB_GMAO_PREVENTIVE terminée!")
            print("\n📌 Nouvelles colonnes ajoutées:")
            print("   - DtePrev : Date prévue de la maintenance préventive")
            print("   - DteReal : Date de réalisation effective de la maintenance préventive")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout des colonnes: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    add_dates_to_preventive()

















