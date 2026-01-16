"""
Script pour vérifier toutes les réparations avec ID_WEB_GMAO_PREVENTIVE renseigné
"""
from db import get_db_cursor

def check_preventive_reparations():
    """Vérifie toutes les réparations avec ID_WEB_GMAO_PREVENTIVE"""
    try:
        with get_db_cursor() as cursor:
            print("=" * 60)
            print("VÉRIFICATION DES RÉPARATIONS AVEC ID_WEB_GMAO_PREVENTIVE")
            print("=" * 60)
            print()
            
            # Récupérer toutes les réparations avec ID_WEB_GMAO_PREVENTIVE non NULL
            cursor.execute("""
                SELECT 
                    r.ID,
                    r.ID_WEB_GMAO_PREVENTIVE,
                    r.TpsReel,
                    r.PostesReel,
                    r.DateCreation,
                    p.Reference,
                    p.Tache,
                    p.Nom_GP_POSTES
                FROM WEB_GMAO_REPARATION r
                LEFT JOIN WEB_GMAO_PREVENTIVE p ON p.ID = r.ID_WEB_GMAO_PREVENTIVE
                WHERE r.ID_WEB_GMAO_PREVENTIVE IS NOT NULL
                ORDER BY r.ID
            """)
            
            rows = cursor.fetchall()
            
            if rows:
                print(f"📊 {len(rows)} réparation(s) avec ID_WEB_GMAO_PREVENTIVE renseigné:")
                print()
                for row in rows:
                    print(f"   Réparation ID {row.ID}:")
                    print(f"      - ID_WEB_GMAO_PREVENTIVE: {row.ID_WEB_GMAO_PREVENTIVE}")
                    print(f"      - TpsReel: {row.TpsReel}")
                    print(f"      - PostesReel: {row.PostesReel}")
                    print(f"      - DateCreation: {row.DateCreation}")
                    if row.Reference or row.Tache:
                        print(f"      - Préventif: {row.Reference or 'N/A'} - {row.Tache or 'N/A'}")
                        print(f"      - Machine préventif: {row.Nom_GP_POSTES or 'N/A'}")
                    else:
                        print(f"      - ⚠️ Préventif ID {row.ID_WEB_GMAO_PREVENTIVE} n'existe pas!")
                    print()
            else:
                print("⚠️ Aucune réparation avec ID_WEB_GMAO_PREVENTIVE renseigné trouvée")
                print()
            
            # Vérifier spécifiquement la ligne 53
            print("📋 Vérification spécifique de la ligne 53:")
            cursor.execute("""
                SELECT 
                    ID,
                    ID_WEB_GMAO_PREVENTIVE,
                    TpsReel,
                    PostesReel
                FROM WEB_GMAO_REPARATION
                WHERE ID = 53
            """)
            
            row53 = cursor.fetchone()
            if row53:
                print(f"   - ID: {row53.ID}")
                print(f"   - ID_WEB_GMAO_PREVENTIVE: {row53.ID_WEB_GMAO_PREVENTIVE}")
                print(f"   - TpsReel: {row53.TpsReel}")
                print(f"   - PostesReel: {row53.PostesReel}")
                
                if row53.ID_WEB_GMAO_PREVENTIVE:
                    print(f"   ✅ ID_WEB_GMAO_PREVENTIVE est renseigné: {row53.ID_WEB_GMAO_PREVENTIVE}")
                else:
                    print(f"   ⚠️ ID_WEB_GMAO_PREVENTIVE est NULL - il faut le renseigner!")
            else:
                print("   ❌ La ligne 53 n'existe pas")
            
            print()
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_preventive_reparations()














