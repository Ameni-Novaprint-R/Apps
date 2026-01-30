"""
Script pour vérifier les colonnes mdp et MDP dans la table personel
"""
from db import get_db_cursor

try:
    with get_db_cursor() as cursor:
        print("=" * 80)
        print("VERIFICATION DES COLONNES MDP")
        print("=" * 80)
        
        # Vérifier toutes les colonnes de personel
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'personel'
            AND COLUMN_NAME LIKE '%mdp%' OR COLUMN_NAME LIKE '%MDP%'
            ORDER BY COLUMN_NAME
        """)
        
        colonnes = cursor.fetchall()
        print("\nColonnes trouvees contenant 'mdp' ou 'MDP':")
        for col in colonnes:
            print(f"  - {col.COLUMN_NAME}: {col.DATA_TYPE} (Nullable: {col.IS_NULLABLE})")
        
        # Vérifier le matricule 321 avec les deux colonnes
        print("\n" + "=" * 80)
        print("VERIFICATION MATRICULE 321")
        print("=" * 80)
        
        cursor.execute("""
            SELECT Matricule, Nom, Prenom, mdp, MDP
            FROM personel
            WHERE Matricule = 321
        """)
        
        employee = cursor.fetchone()
        if employee:
            print(f"Matricule: {employee.Matricule}")
            print(f"Nom: {employee.Nom}")
            print(f"Prenom: {employee.Prenom}")
            
            # Vérifier mdp (minuscule)
            mdp_min = None
            if hasattr(employee, 'mdp'):
                mdp_min = employee.mdp
            elif 'mdp' in employee.__dict__:
                mdp_min = employee.__dict__['mdp']
            
            # Vérifier MDP (majuscule)
            mdp_maj = None
            if hasattr(employee, 'MDP'):
                mdp_maj = employee.MDP
            elif 'MDP' in employee.__dict__:
                mdp_maj = employee.__dict__['MDP']
            
            print(f"\nColonne 'mdp' (minuscule):")
            if mdp_min:
                print(f"  [OK] Valeur trouvee: {mdp_min[:30]}... (longueur: {len(str(mdp_min))})")
            else:
                print(f"  [VIDE] NULL ou non trouvee")
            
            print(f"\nColonne 'MDP' (majuscule):")
            if mdp_maj:
                print(f"  [OK] Valeur trouvee: {mdp_maj[:30]}... (longueur: {len(str(mdp_maj))})")
            else:
                print(f"  [VIDE] NULL ou non trouvee")
            
            # Essayer de récupérer directement avec les noms de colonnes
            print("\n" + "=" * 80)
            print("TEST DIRECT DES COLONNES")
            print("=" * 80)
            
            try:
                cursor.execute("SELECT mdp FROM personel WHERE Matricule = 321")
                row_mdp = cursor.fetchone()
                if row_mdp:
                    print(f"Colonne 'mdp' (direct): {row_mdp[0][:30] if row_mdp[0] else 'NULL'}...")
            except Exception as e:
                print(f"Erreur lecture colonne 'mdp': {e}")
            
            try:
                cursor.execute("SELECT MDP FROM personel WHERE Matricule = 321")
                row_MDP = cursor.fetchone()
                if row_MDP:
                    print(f"Colonne 'MDP' (direct): {row_MDP[0][:30] if row_MDP[0] else 'NULL'}...")
            except Exception as e:
                print(f"Erreur lecture colonne 'MDP': {e}")
        
        print("\n" + "=" * 80)
            
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()
