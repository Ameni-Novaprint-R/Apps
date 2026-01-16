"""
Script pour vérifier et ajouter la colonne TypeIN dans WEB_GMAO_REPARATION
"""
from db import get_db_cursor

def verify_and_add_typein():
    """Vérifie et ajoute la colonne TypeIN si nécessaire"""
    try:
        with get_db_cursor() as cursor:
            print("=" * 60)
            print("VÉRIFICATION DE LA COLONNE TypeIN")
            print("=" * 60)
            print()
            
            # Vérifier si la colonne existe
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_GMAO_REPARATION'
                AND COLUMN_NAME = 'TypeIN'
            """)
            
            column_info = cursor.fetchone()
            
            if column_info:
                print("✅ La colonne TypeIN existe dans WEB_GMAO_REPARATION")
                print(f"   - Type de données: {column_info.DATA_TYPE}")
                print(f"   - Nullable: {column_info.IS_NULLABLE}")
                print(f"   - Valeur par défaut: {column_info.COLUMN_DEFAULT or 'Aucune'}")
                print()
            else:
                print("❌ La colonne TypeIN N'EXISTE PAS dans WEB_GMAO_REPARATION")
                print("📝 Ajout de la colonne TypeIN...")
                
                # Ajouter la colonne
                cursor.execute("""
                    ALTER TABLE WEB_GMAO_REPARATION
                    ADD TypeIN CHAR(1) NULL CHECK (TypeIN IN ('R','P'))
                """)
                cursor.connection.commit()
                print("✅ Colonne TypeIN ajoutée avec succès!")
                print()
                
                # Mettre à jour les données existantes
                print("📝 Mise à jour des données existantes...")
                
                # Les réparations liées à une demande (ID_WEB_GMAO_Dem_In IS NOT NULL) = 'R'
                cursor.execute("""
                    UPDATE WEB_GMAO_REPARATION
                    SET TypeIN = 'R'
                    WHERE ID_WEB_GMAO_Dem_In IS NOT NULL
                    AND TypeIN IS NULL
                """)
                count_r = cursor.rowcount
                
                # Les réparations avec ID_WEB_GMAO_PREVENTIVE renseigné = 'P'
                cursor.execute("""
                    UPDATE WEB_GMAO_REPARATION
                    SET TypeIN = 'P'
                    WHERE ID_WEB_GMAO_PREVENTIVE IS NOT NULL
                    AND TypeIN IS NULL
                """)
                count_p = cursor.rowcount
                
                # Les réparations directes (ID_WEB_GMAO_Dem_In IS NULL et ID_WEB_GMAO_PREVENTIVE IS NULL) = 'R' par défaut
                cursor.execute("""
                    UPDATE WEB_GMAO_REPARATION
                    SET TypeIN = 'R'
                    WHERE ID_WEB_GMAO_Dem_In IS NULL
                    AND ID_WEB_GMAO_PREVENTIVE IS NULL
                    AND TypeIN IS NULL
                """)
                count_default = cursor.rowcount
                
                cursor.connection.commit()
                print(f"   ✅ {count_r} réparation(s) mise(s) à jour avec TypeIN = 'R' (liées à une demande)")
                print(f"   ✅ {count_p} réparation(s) mise(s) à jour avec TypeIN = 'P' (interventions préventives)")
                print(f"   ✅ {count_default} réparation(s) mise(s) à jour avec TypeIN = 'R' (par défaut)")
                print()
            
            # Statistiques
            print("📊 Statistiques des données:")
            cursor.execute("""
                SELECT 
                    COUNT(*) as Total,
                    SUM(CASE WHEN TypeIN = 'R' THEN 1 ELSE 0 END) as TypeR,
                    SUM(CASE WHEN TypeIN = 'P' THEN 1 ELSE 0 END) as TypeP,
                    SUM(CASE WHEN TypeIN IS NULL THEN 1 ELSE 0 END) as TypeNull
                FROM WEB_GMAO_REPARATION
            """)
            
            stats = cursor.fetchone()
            print(f"   - Total des réparations: {stats.Total}")
            print(f"   - TypeIN = 'R' (Réparation): {stats.TypeR}")
            print(f"   - TypeIN = 'P' (Préventive): {stats.TypeP}")
            print(f"   - TypeIN = NULL: {stats.TypeNull}")
            print()
            
            # Vérifier les réparations avec ID_WEB_GMAO_PREVENTIVE mais TypeIN != 'P'
            cursor.execute("""
                SELECT COUNT(*) as Count
                FROM WEB_GMAO_REPARATION
                WHERE ID_WEB_GMAO_PREVENTIVE IS NOT NULL
                AND TypeIN != 'P'
            """)
            
            incorrect = cursor.fetchone()
            if incorrect and incorrect.Count > 0:
                print(f"⚠️ {incorrect.Count} réparation(s) avec ID_WEB_GMAO_PREVENTIVE mais TypeIN != 'P'")
                print("   Correction en cours...")
                cursor.execute("""
                    UPDATE WEB_GMAO_REPARATION
                    SET TypeIN = 'P'
                    WHERE ID_WEB_GMAO_PREVENTIVE IS NOT NULL
                    AND TypeIN != 'P'
                """)
                cursor.connection.commit()
                print("   ✅ Corrections appliquées")
                print()
            
            print("=" * 60)
            print("✅ Vérification terminée!")
            print("=" * 60)
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_and_add_typein()














