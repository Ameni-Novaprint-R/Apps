"""
Script de test pour vérifier l'affichage de la maintenance préventive
"""

from db import get_db_cursor
from logic.projet16 import get_all_preventive_tasks

def test_preventive_display():
    """Teste l'affichage des tâches de maintenance préventive"""
    
    print("=" * 60)
    print("TEST D'AFFICHAGE DE LA MAINTENANCE PRÉVENTIVE")
    print("=" * 60)
    
    # Vérifier la structure de la table
    print("\n1. Vérification de la structure de la table...")
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_GMAO_PREVENTIVE'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns = cursor.fetchall()
            print(f"   ✅ Table WEB_GMAO_PREVENTIVE existe avec {len(columns)} colonnes:")
            for col in columns:
                nullable = "NULL" if col.IS_NULLABLE == "YES" else "NOT NULL"
                print(f"      - {col.COLUMN_NAME}: {col.DATA_TYPE} ({nullable})")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Compter les tâches
    print("\n2. Vérification du nombre de tâches...")
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM WEB_GMAO_PREVENTIVE")
            count = cursor.fetchone().count
            print(f"   📊 Nombre de tâches dans la base: {count}")
            
            if count == 0:
                print("   ⚠️  Aucune tâche trouvée. Vous devez importer les données depuis Excel.")
                print("   💡 Utilisez: python import_preventive_excel.py <fichier_excel> \"KBA 75\"")
                return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Tester la fonction get_all_preventive_tasks
    print("\n3. Test de la fonction get_all_preventive_tasks()...")
    try:
        tasks = get_all_preventive_tasks()
        print(f"   ✅ Fonction exécutée avec succès")
        print(f"   📋 {len(tasks)} tâches récupérées")
        
        if len(tasks) > 0:
            print("\n   📝 Aperçu de la première tâche:")
            first_task = tasks[0]
            for key, value in first_task.items():
                print(f"      - {key}: {value}")
            
            # Tester le filtre par machine
            if tasks:
                machine_name = tasks[0].get('nom_gp_postes')
                if machine_name:
                    print(f"\n4. Test du filtre par machine ({machine_name})...")
                    filtered_tasks = get_all_preventive_tasks(machine_name=machine_name)
                    print(f"   ✅ Filtre fonctionne: {len(filtered_tasks)} tâches pour {machine_name}")
        
        # Afficher un résumé par périodicité
        print("\n5. Résumé par périodicité:")
        periodicites = {}
        for task in tasks:
            periodicite = task.get('periodicite') or 'Non spécifiée'
            periodicites[periodicite] = periodicites.get(periodicite, 0) + 1
        
        for periodicite, count in sorted(periodicites.items()):
            print(f"   - {periodicite}: {count} tâche(s)")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✅ TESTS TERMINÉS AVEC SUCCÈS")
    print("=" * 60)
    print("\n💡 Pour tester l'affichage dans le navigateur:")
    print("   1. Assurez-vous que le serveur Flask est démarré")
    print("   2. Accédez à http://localhost:5000/projet16/")
    print("   3. Cliquez sur 'Maintenance Préventive'")
    print("   4. Le tableau devrait s'afficher avec toutes les tâches")
    
    return True

if __name__ == "__main__":
    test_preventive_display()

















