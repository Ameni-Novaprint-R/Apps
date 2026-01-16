"""
Script pour vérifier la colonne ID_WEB_GMAO_PREVENTIVE dans WEB_GMAO_REPARATION
"""
from db import get_db_cursor

def verify_id_web_gmao_preventive():
    """Vérifie que la colonne ID_WEB_GMAO_PREVENTIVE existe et fonctionne correctement"""
    try:
        with get_db_cursor() as cursor:
            # 1. Vérifier si la colonne existe
            print("=" * 60)
            print("VÉRIFICATION DE LA COLONNE ID_WEB_GMAO_PREVENTIVE")
            print("=" * 60)
            print()
            
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_GMAO_REPARATION'
                AND COLUMN_NAME = 'ID_WEB_GMAO_PREVENTIVE'
            """)
            
            column_info = cursor.fetchone()
            
            if column_info:
                print("✅ La colonne ID_WEB_GMAO_PREVENTIVE existe dans WEB_GMAO_REPARATION")
                print(f"   - Type de données: {column_info.DATA_TYPE}")
                print(f"   - Nullable: {column_info.IS_NULLABLE}")
                print()
            else:
                print("❌ La colonne ID_WEB_GMAO_PREVENTIVE N'EXISTE PAS dans WEB_GMAO_REPARATION")
                print("   Vous devez exécuter le script: add_id_web_gmao_preventive_to_reparation.sql")
                return False
            
            # 2. Vérifier la contrainte de clé étrangère
            print("📋 Vérification de la contrainte de clé étrangère...")
            cursor.execute("""
                SELECT 
                    fk.name AS FK_Name,
                    OBJECT_NAME(fk.parent_object_id) AS Table_Name,
                    COL_NAME(fc.parent_object_id, fc.parent_column_id) AS Column_Name,
                    OBJECT_NAME(fk.referenced_object_id) AS Referenced_Table,
                    COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS Referenced_Column
                FROM sys.foreign_keys AS fk
                INNER JOIN sys.foreign_key_columns AS fc
                    ON fk.object_id = fc.constraint_object_id
                WHERE OBJECT_NAME(fk.parent_object_id) = 'WEB_GMAO_REPARATION'
                AND COL_NAME(fc.parent_object_id, fc.parent_column_id) = 'ID_WEB_GMAO_PREVENTIVE'
            """)
            
            fk_info = cursor.fetchone()
            
            if fk_info:
                print("✅ Contrainte de clé étrangère trouvée:")
                print(f"   - Nom: {fk_info.FK_Name}")
                print(f"   - Table référencée: {fk_info.Referenced_Table}")
                print(f"   - Colonne référencée: {fk_info.Referenced_Column}")
                print()
            else:
                print("⚠️ Aucune contrainte de clé étrangère trouvée")
                print()
            
            # 3. Vérifier les données existantes
            print("📊 Statistiques des données:")
            cursor.execute("""
                SELECT 
                    COUNT(*) as TotalReparations,
                    COUNT(ID_WEB_GMAO_PREVENTIVE) as AvecPreventive,
                    COUNT(*) - COUNT(ID_WEB_GMAO_PREVENTIVE) as SansPreventive
                FROM WEB_GMAO_REPARATION
            """)
            
            stats = cursor.fetchone()
            print(f"   - Total des réparations: {stats.TotalReparations}")
            print(f"   - Avec ID_WEB_GMAO_PREVENTIVE renseigné: {stats.AvecPreventive}")
            print(f"   - Sans ID_WEB_GMAO_PREVENTIVE: {stats.SansPreventive}")
            print()
            
            # 4. Vérifier les valeurs et leur validité
            if stats.AvecPreventive > 0:
                print("🔍 Vérification de la validité des références...")
                cursor.execute("""
                    SELECT 
                        r.ID as ReparationID,
                        r.ID_WEB_GMAO_PREVENTIVE,
                        r.TypeIN,
                        p.ID as PreventiveExists,
                        p.Reference,
                        p.Tache
                    FROM WEB_GMAO_REPARATION r
                    LEFT JOIN WEB_GMAO_PREVENTIVE p ON p.ID = r.ID_WEB_GMAO_PREVENTIVE
                    WHERE r.ID_WEB_GMAO_PREVENTIVE IS NOT NULL
                """)
                
                rows = cursor.fetchall()
                valid_count = 0
                invalid_count = 0
                
                for row in rows:
                    if row.PreventiveExists:
                        valid_count += 1
                    else:
                        invalid_count += 1
                        print(f"   ⚠️ Réparation ID {row.ReparationID} référence un préventif inexistant (ID: {row.ID_WEB_GMAO_PREVENTIVE})")
                
                print(f"   ✅ Références valides: {valid_count}")
                if invalid_count > 0:
                    print(f"   ❌ Références invalides: {invalid_count}")
                print()
            
            # 5. Afficher quelques exemples
            print("📋 Exemples de réparations avec préventif associé:")
            # Vérifier si TypeIN existe
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_GMAO_REPARATION'
                AND COLUMN_NAME = 'TypeIN'
            """)
            typein_exists = cursor.fetchone() is not None
            
            query = """
                SELECT TOP 5
                    r.ID as ReparationID,
                    r.ID_WEB_GMAO_PREVENTIVE,
                    r.PostesReel,
                    p.Reference,
                    p.Tache,
                    p.Nom_GP_POSTES"""
            if typein_exists:
                query += ", r.TypeIN"
            query += """
                FROM WEB_GMAO_REPARATION r
                INNER JOIN WEB_GMAO_PREVENTIVE p ON p.ID = r.ID_WEB_GMAO_PREVENTIVE
                WHERE r.ID_WEB_GMAO_PREVENTIVE IS NOT NULL
                ORDER BY r.DateCreation DESC
            """
            
            cursor.execute(query)
            
            examples = cursor.fetchall()
            if examples:
                for ex in examples:
                    type_info = f" (Type: {ex.TypeIN})" if typein_exists and hasattr(ex, 'TypeIN') else ""
                    print(f"   - Réparation ID {ex.ReparationID}{type_info}")
                    print(f"     → Préventif ID {ex.ID_WEB_GMAO_PREVENTIVE}: {ex.Reference or 'N/A'} - {ex.Tache or 'N/A'}")
                    print(f"     → Machine: {ex.PostesReel or 'N/A'} / {ex.Nom_GP_POSTES or 'N/A'}")
                    print()
            else:
                print("   Aucune réparation avec préventif associé trouvée")
                print()
            
            # 6. Vérifier les réparations de type préventif sans ID_WEB_GMAO_PREVENTIVE
            if typein_exists:
                print("🔍 Vérification des réparations de type préventif sans ID_WEB_GMAO_PREVENTIVE...")
                cursor.execute("""
                    SELECT COUNT(*) as Count
                    FROM WEB_GMAO_REPARATION
                    WHERE TypeIN = 'P'
                    AND ID_WEB_GMAO_PREVENTIVE IS NULL
                """)
                
                missing_preventive = cursor.fetchone()
                if missing_preventive and missing_preventive.Count > 0:
                    print(f"   ⚠️ {missing_preventive.Count} réparation(s) de type préventif sans ID_WEB_GMAO_PREVENTIVE")
                    print("   Ces réparations devraient être associées à un préventif")
                else:
                    print("   ✅ Toutes les réparations de type préventif ont un ID_WEB_GMAO_PREVENTIVE")
                print()
            
            print("=" * 60)
            print("✅ Vérification terminée!")
            print("=" * 60)
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_id_web_gmao_preventive()

