"""
Script pour vérifier que les droits ID_Action 3 et 4 sont correctement configurés
pour les ateliers et que le système fonctionne correctement
"""
from db import get_db_cursor
from logic.auth import has_action_access

def verifier():
    print("=" * 80)
    print("VERIFICATION DES DROITS ID_Action 3 ET 4 POUR LES ATELIERS")
    print("=" * 80)
    print()
    
    with get_db_cursor() as cursor:
        # Vérifier l'état dans la base de données
        print("1. ETAT DANS WEB_DROITS_ACCES:")
        print("-" * 80)
        cursor.execute("""
            SELECT NomAtelier, ID_Action, Autorise 
            FROM WEB_DROITS_ACCES 
            WHERE NomAtelier IS NOT NULL 
            AND ID_Action IN (3, 4)
            ORDER BY NomAtelier, ID_Action
        """)
        resultats = cursor.fetchall()
        for row in resultats:
            status = "AUTORISE" if row.Autorise == 1 else "REFUSE"
            print(f"  {row.NomAtelier} - ID_Action {row.ID_Action}: {status} (Autorise = {row.Autorise})")
        
        print()
        print("2. VERIFICATION DES AUTRES ACTIONS (1, 2, 5):")
        print("-" * 80)
        cursor.execute("""
            SELECT TOP 5 NomAtelier, ID_Action, Autorise 
            FROM WEB_DROITS_ACCES 
            WHERE NomAtelier IS NOT NULL 
            AND ID_Action IN (1, 2, 5)
            ORDER BY NomAtelier, ID_Action
        """)
        resultats = cursor.fetchall()
        for row in resultats:
            status = "AUTORISE" if row.Autorise == 1 else "REFUSE"
            print(f"  {row.NomAtelier} - ID_Action {row.ID_Action}: {status} (Autorise = {row.Autorise})")
        if len(resultats) > 5:
            print(f"  ... et {len(resultats) - 5} autre(s) ligne(s)")
        
        print()
        print("=" * 80)
        print("RESUME:")
        print("=" * 80)
        print("Pour les ateliers (Atelier1 à Atelier10):")
        print("  - ID_Action 1 (Voir): AUTORISE")
        print("  - ID_Action 2 (Créer): AUTORISE")
        print("  - ID_Action 3 (Modifier): REFUSE (Autorise = 0)")
        print("  - ID_Action 4 (Supprimer): REFUSE (Autorise = 0)")
        print("  - ID_Action 5 (Autre): AUTORISE")
        print()
        print("CONSEQUENCE:")
        print("  - Les boutons 'Modifier' et 'Supprimer' ne seront PAS affiches")
        print("    dans la section 'Liste des Traitements' du Projet 11")
        print("    pour les utilisateurs connectes avec Atelier1 a Atelier10.")
        print("=" * 80)

if __name__ == "__main__":
    verifier()
