"""
Script Python pour ajouter la colonne ID_WEB_GMAO_PREVENTIVE dans WEB_GMAO_REPARATION
"""
from db import get_db_cursor

def add_id_web_gmao_preventive_column():
    """Ajoute la colonne ID_WEB_GMAO_PREVENTIVE dans WEB_GMAO_REPARATION"""
    try:
        with get_db_cursor() as cursor:
            # Vérifier si la colonne existe déjà
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_GMAO_REPARATION'
                AND COLUMN_NAME = 'ID_WEB_GMAO_PREVENTIVE'
            """)
            
            if cursor.fetchone():
                print("⚠️ La colonne ID_WEB_GMAO_PREVENTIVE existe déjà.")
                return True
            
            print("=" * 60)
            print("AJOUT DE LA COLONNE ID_WEB_GMAO_PREVENTIVE")
            print("=" * 60)
            print()
            
            # Ajouter la colonne
            print("📝 Ajout de la colonne ID_WEB_GMAO_PREVENTIVE...")
            cursor.execute("""
                ALTER TABLE WEB_GMAO_REPARATION
                ADD ID_WEB_GMAO_PREVENTIVE INT NULL
            """)
            cursor.connection.commit()
            print("✅ Colonne ajoutée avec succès!")
            print()
            
            # Vérifier si la table WEB_GMAO_PREVENTIVE existe
            cursor.execute("""
                SELECT COUNT(*) as table_exists
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = 'WEB_GMAO_PREVENTIVE'
            """)
            preventive_table_exists = cursor.fetchone().table_exists > 0
            
            if not preventive_table_exists:
                print("⚠️ La table WEB_GMAO_PREVENTIVE n'existe pas.")
                print("   La contrainte de clé étrangère ne peut pas être créée.")
                return True
            
            # Vérifier si la contrainte existe déjà
            cursor.execute("""
                SELECT name
                FROM sys.foreign_keys
                WHERE name = 'FK_WEB_GMAO_REPARATION_WEB_GMAO_PREVENTIVE'
            """)
            
            if cursor.fetchone():
                print("⚠️ La contrainte de clé étrangère existe déjà.")
            else:
                # Ajouter la contrainte de clé étrangère
                print("📝 Ajout de la contrainte de clé étrangère...")
                cursor.execute("""
                    ALTER TABLE WEB_GMAO_REPARATION
                    ADD CONSTRAINT FK_WEB_GMAO_REPARATION_WEB_GMAO_PREVENTIVE 
                        FOREIGN KEY (ID_WEB_GMAO_PREVENTIVE) 
                        REFERENCES WEB_GMAO_PREVENTIVE(ID) 
                        ON DELETE SET NULL
                """)
                cursor.connection.commit()
                print("✅ Contrainte de clé étrangère ajoutée avec succès!")
                print()
            
            # Créer un index pour améliorer les performances
            cursor.execute("""
                SELECT name
                FROM sys.indexes
                WHERE name = 'IX_WEB_GMAO_REPARATION_ID_WEB_GMAO_PREVENTIVE'
            """)
            
            if cursor.fetchone():
                print("⚠️ L'index existe déjà.")
            else:
                print("📝 Création de l'index...")
                cursor.execute("""
                    CREATE NONCLUSTERED INDEX IX_WEB_GMAO_REPARATION_ID_WEB_GMAO_PREVENTIVE 
                    ON WEB_GMAO_REPARATION(ID_WEB_GMAO_PREVENTIVE)
                """)
                cursor.connection.commit()
                print("✅ Index créé avec succès!")
                print()
            
            # Afficher les statistiques
            cursor.execute("""
                SELECT 
                    COUNT(*) as TotalReparations,
                    COUNT(ID_WEB_GMAO_PREVENTIVE) as AvecPreventive,
                    COUNT(*) - COUNT(ID_WEB_GMAO_PREVENTIVE) as SansPreventive
                FROM WEB_GMAO_REPARATION
            """)
            
            stats = cursor.fetchone()
            print("📊 Statistiques après ajout:")
            print(f"   - Total des réparations: {stats.TotalReparations}")
            print(f"   - Avec ID_WEB_GMAO_PREVENTIVE renseigné: {stats.AvecPreventive}")
            print(f"   - Sans ID_WEB_GMAO_PREVENTIVE: {stats.SansPreventive}")
            print()
            
            print("=" * 60)
            print("✅ Opération terminée avec succès!")
            print("=" * 60)
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la colonne : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    add_id_web_gmao_preventive_column()














