"""
Test de la requête complète pour vérifier l'affichage de TpsReel
"""
from logic.projet16 import get_all_preventive_tasks

def test_preventive_query():
    """Teste la fonction get_all_preventive_tasks"""
    try:
        print("=" * 60)
        print("TEST DE LA REQUÊTE POUR LES PRÉVENTIFS")
        print("=" * 60)
        print()
        
        # Récupérer toutes les tâches préventives
        tasks = get_all_preventive_tasks()
        
        print(f"📊 {len(tasks)} tâche(s) préventive(s) récupérée(s)")
        print()
        
        # Chercher le préventif ID 476 (celui associé à la réparation ID 54)
        preventive_476 = [t for t in tasks if t.get('id') == 476]
        
        if preventive_476:
            task = preventive_476[0]
            print(f"✅ Préventif ID 476 trouvé:")
            print(f"   - Référence: {task.get('reference', 'N/A')}")
            print(f"   - Tâche: {task.get('tache', 'N/A')}")
            print(f"   - Machine: {task.get('nom_gp_postes', 'N/A')}")
            print(f"   - TpsReel: {task.get('tps_reel', 'N/A')}")
            
            if task.get('tps_reel') is not None:
                tps_reel = task.get('tps_reel')
                heures = int(tps_reel)
                minutes = round((tps_reel - heures) * 60)
                print(f"   ✅ Formatage: {heures}h{minutes:02d}")
            else:
                print(f"   ⚠️ TpsReel est NULL")
            print()
        else:
            print("❌ Préventif ID 476 non trouvé dans les résultats")
            print()
        
        # Afficher tous les préventifs qui ont un tps_reel
        tasks_with_tpsreel = [t for t in tasks if t.get('tps_reel') is not None]
        
        if tasks_with_tpsreel:
            print(f"📋 {len(tasks_with_tpsreel)} préventif(s) avec TpsReel:")
            for task in tasks_with_tpsreel[:5]:  # Afficher les 5 premiers
                tps_reel = task.get('tps_reel')
                heures = int(tps_reel)
                minutes = round((tps_reel - heures) * 60)
                print(f"   - ID {task.get('id')}: {task.get('reference', 'N/A')} - TpsReel: {heures}h{minutes:02d}")
        else:
            print("⚠️ Aucun préventif avec TpsReel trouvé")
        
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_preventive_query()














