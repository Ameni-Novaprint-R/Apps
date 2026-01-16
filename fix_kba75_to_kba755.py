"""
Script pour corriger les valeurs "KBA 75" en "KBA755" dans WEB_GMAO_PREVENTIVE
"""
from db import get_db_cursor

def fix_kba75_to_kba755():
    """Remplace 'KBA 75' par 'KBA755' dans la colonne Nom_GP_POSTES"""
    try:
        with get_db_cursor() as cursor:
            # Compter les lignes concernées avant la mise à jour
            cursor.execute("""
                SELECT COUNT(*) as NombreLignes
                FROM WEB_GMAO_PREVENTIVE
                WHERE Nom_GP_POSTES = 'KBA 75'
            """)
            result = cursor.fetchone()
            nombre_avant = result.NombreLignes if result else 0
            
            print(f"📊 Nombre de lignes à corriger : {nombre_avant}")
            
            if nombre_avant == 0:
                print("✅ Aucune ligne à corriger. La valeur 'KBA 75' n'existe pas dans la table.")
                return True
            
            # Effectuer la mise à jour
            print("📝 Mise à jour en cours...")
            cursor.execute("""
                UPDATE WEB_GMAO_PREVENTIVE
                SET Nom_GP_POSTES = 'KBA755'
                WHERE Nom_GP_POSTES = 'KBA 75'
            """)
            
            rows_affected = cursor.rowcount
            cursor.connection.commit()
            
            print(f"✅ {rows_affected} ligne(s) mise(s) à jour avec succès!")
            
            # Vérifier qu'il ne reste plus de "KBA 75"
            cursor.execute("""
                SELECT COUNT(*) as NombreRestant
                FROM WEB_GMAO_PREVENTIVE
                WHERE Nom_GP_POSTES = 'KBA 75'
            """)
            result = cursor.fetchone()
            nombre_restant = result.NombreRestant if result else 0
            
            if nombre_restant == 0:
                print("✅ Vérification : Aucune ligne avec 'KBA 75' restante.")
            else:
                print(f"⚠️ Attention : Il reste {nombre_restant} ligne(s) avec 'KBA 75'.")
            
            # Afficher un échantillon des lignes corrigées
            cursor.execute("""
                SELECT TOP 10 
                    ID,
                    Nom_GP_POSTES,
                    Reference,
                    Tache
                FROM WEB_GMAO_PREVENTIVE
                WHERE Nom_GP_POSTES = 'KBA755'
            """)
            
            rows = cursor.fetchall()
            if rows:
                print("\n📋 Échantillon des lignes corrigées :")
                for row in rows:
                    print(f"   ID: {row.ID}, Machine: {row.Nom_GP_POSTES}, Référence: {row.Reference or 'N/A'}, Tâche: {row.Tache or 'N/A'}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la correction : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Correction de KBA 75 en KBA755 dans WEB_GMAO_PREVENTIVE")
    print("=" * 60)
    print()
    
    success = fix_kba75_to_kba755()
    
    print()
    print("=" * 60)
    if success:
        print("✅ Correction terminée avec succès!")
    else:
        print("❌ Correction échouée!")
    print("=" * 60)














