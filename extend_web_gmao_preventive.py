"""
Script pour étendre la table WEB_GMAO_PREVENTIVE avec les colonnes du planning
"""

from db import get_db_cursor

def extend_web_gmao_preventive():
    """Ajoute les colonnes nécessaires pour le planning de maintenance préventive"""
    
    try:
        with get_db_cursor() as cursor:
            # Vérifier si les colonnes existent déjà
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'WEB_GMAO_PREVENTIVE' 
                AND COLUMN_NAME = 'Reference'
            """)
            
            if cursor.fetchone():
                print("⚠️ Les colonnes existent déjà.")
                return False
            
            print("📝 Ajout des colonnes au planning de maintenance préventive...")
            
            # Ajouter les colonnes
            columns_to_add = [
                ("Reference", "VARCHAR(50) NULL", "Référence de la tâche"),
                ("Tache", "NVARCHAR(500) NULL", "Description de la tâche"),
                ("Periodicite", "VARCHAR(50) NULL CHECK (Periodicite IN ('Quotidienne', 'Hebdomadaire', 'Mensuelle', 'Trimestrielle', 'Semestrielle', 'Annuelle'))", "Périodicité"),
                ("Duree", "VARCHAR(20) NULL", "Durée estimée"),
                ("RoleRequis", "VARCHAR(50) NULL", "Rôle requis"),
                ("SpecificationsObservations", "NTEXT NULL", "Spécifications et observations"),
                ("OrdreAffichage", "INT NULL", "Ordre d'affichage"),
                ("DateDerniereExecution", "DATETIME NULL", "Date de dernière exécution"),
                ("DateProchaineExecution", "DATETIME NULL", "Date de prochaine exécution")
            ]
            
            for col_name, col_def, description in columns_to_add:
                try:
                    cursor.execute(f"ALTER TABLE dbo.WEB_GMAO_PREVENTIVE ADD {col_name} {col_def}")
                    print(f"✅ Colonne {col_name} ajoutée ({description})")
                except Exception as e:
                    print(f"⚠️ Erreur lors de l'ajout de {col_name}: {e}")
            
            cursor.connection.commit()
            
            # Créer les index
            print("\n📝 Création des index...")
            indexes = [
                ("IX_WEB_GMAO_PREVENTIVE_Periodicite", "Periodicite"),
                ("IX_WEB_GMAO_PREVENTIVE_Reference", "Reference"),
                ("IX_WEB_GMAO_PREVENTIVE_Nom_GP_POSTES_Periodicite", "Nom_GP_POSTES, Periodicite")
            ]
            
            for index_name, columns in indexes:
                try:
                    cursor.execute(f"""
                        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = '{index_name}')
                        CREATE NONCLUSTERED INDEX {index_name} 
                        ON dbo.WEB_GMAO_PREVENTIVE({columns})
                    """)
                    print(f"✅ Index {index_name} créé")
                except Exception as e:
                    print(f"⚠️ Erreur lors de la création de l'index {index_name}: {e}")
            
            cursor.connection.commit()
            
            print("\n✅ Extension de la table WEB_GMAO_PREVENTIVE terminée!")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de l'extension de la table: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    extend_web_gmao_preventive()

















