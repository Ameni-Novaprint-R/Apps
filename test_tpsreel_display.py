"""
Script pour tester l'affichage de TpsReel dans le tableau de suivi des préventifs
"""
from db import get_db_cursor

def test_tpsreel_display():
    """Teste la récupération de TpsReel pour les préventifs"""
    try:
        with get_db_cursor() as cursor:
            print("=" * 60)
            print("TEST D'AFFICHAGE DE TpsReel")
            print("=" * 60)
            print()
            
            # Vérifier la ligne 53 de WEB_GMAO_REPARATION
            print("📋 Vérification de la ligne 53 de WEB_GMAO_REPARATION:")
            # Vérifier si TypeIN existe
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_GMAO_REPARATION'
                AND COLUMN_NAME = 'TypeIN'
            """)
            typein_exists = cursor.fetchone() is not None
            
            query = """
                SELECT 
                    ID,
                    ID_WEB_GMAO_PREVENTIVE,
                    TpsReel,
                    PostesReel,
                    DateCreation"""
            if typein_exists:
                query += ", TypeIN"
            query += """
                FROM WEB_GMAO_REPARATION
                WHERE ID = 53
            """
            
            cursor.execute(query)
            
            rep_row = cursor.fetchone()
            if rep_row:
                print(f"   ✅ Ligne trouvée:")
                print(f"      - ID: {rep_row.ID}")
                print(f"      - ID_WEB_GMAO_PREVENTIVE: {rep_row.ID_WEB_GMAO_PREVENTIVE}")
                print(f"      - TpsReel: {rep_row.TpsReel}")
                if typein_exists:
                    print(f"      - TypeIN: {rep_row.TypeIN}")
                print(f"      - PostesReel: {rep_row.PostesReel}")
                print(f"      - DateCreation: {rep_row.DateCreation}")
                print()
                
                if rep_row.ID_WEB_GMAO_PREVENTIVE:
                    preventive_id = rep_row.ID_WEB_GMAO_PREVENTIVE
                    
                    # Vérifier que le préventif existe
                    cursor.execute("""
                        SELECT ID, Reference, Tache, Nom_GP_POSTES
                        FROM WEB_GMAO_PREVENTIVE
                        WHERE ID = ?
                    """, (preventive_id,))
                    
                    preventive_row = cursor.fetchone()
                    if preventive_row:
                        print(f"   ✅ Préventif associé trouvé:")
                        print(f"      - ID: {preventive_row.ID}")
                        print(f"      - Référence: {preventive_row.Reference}")
                        print(f"      - Tâche: {preventive_row.Tache}")
                        print(f"      - Machine: {preventive_row.Nom_GP_POSTES}")
                        print()
                        
                        # Tester la requête utilisée par get_all_preventive_tasks
                        print("🔍 Test de la requête utilisée par get_all_preventive_tasks:")
                        cursor.execute("""
                            SELECT 
                                p.ID,
                                p.Reference,
                                p.Tache,
                                r.TpsReel
                            FROM WEB_GMAO_PREVENTIVE p
                            LEFT JOIN (
                                SELECT 
                                    ID_WEB_GMAO_PREVENTIVE,
                                    TpsReel,
                                    ROW_NUMBER() OVER (PARTITION BY ID_WEB_GMAO_PREVENTIVE ORDER BY DateCreation DESC) as rn
                                FROM WEB_GMAO_REPARATION
                                WHERE ID_WEB_GMAO_PREVENTIVE IS NOT NULL
                            ) r ON r.ID_WEB_GMAO_PREVENTIVE = p.ID AND r.rn = 1
                            WHERE p.ID = ?
                        """, (preventive_id,))
                        
                        test_row = cursor.fetchone()
                        if test_row:
                            print(f"   ✅ Résultat de la requête:")
                            print(f"      - Préventif ID: {test_row.ID}")
                            print(f"      - Référence: {test_row.Reference}")
                            print(f"      - TpsReel: {test_row.TpsReel}")
                            print()
                            
                            if test_row.TpsReel is not None:
                                heures = int(test_row.TpsReel)
                                minutes = round((test_row.TpsReel - heures) * 60)
                                print(f"   ✅ Formatage: {heures}h{minutes:02d}")
                            else:
                                print("   ⚠️ TpsReel est NULL dans la requête")
                        else:
                            print("   ❌ Aucun résultat trouvé pour ce préventif")
                    else:
                        print(f"   ❌ Le préventif ID {preventive_id} n'existe pas dans WEB_GMAO_PREVENTIVE")
                else:
                    print("   ⚠️ ID_WEB_GMAO_PREVENTIVE est NULL")
            else:
                print("   ❌ La ligne 53 n'existe pas dans WEB_GMAO_REPARATION")
            
            print()
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tpsreel_display()

