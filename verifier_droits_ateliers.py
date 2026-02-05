"""
Script pour vérifier les droits actuels des ateliers dans WEB_DROITS_ACCES
"""
from db import get_db_cursor

def verifier():
    with get_db_cursor() as cursor:
        print("=" * 80)
        print("VERIFICATION DES DROITS DES ATELIERS")
        print("=" * 80)
        print()
        
        # Récupérer tous les ateliers
        cursor.execute("SELECT DISTINCT NomAtelier FROM WEB_DROITS_ACCES WHERE NomAtelier IS NOT NULL ORDER BY NomAtelier")
        ateliers = [row.NomAtelier for row in cursor.fetchall()]
        print(f"Ateliers trouves: {ateliers}")
        print()
        
        # Pour chaque atelier, afficher les droits
        for atelier in ateliers:
            print(f"Atelier: {atelier}")
            cursor.execute("""
                SELECT ID_Action, Autorise 
                FROM WEB_DROITS_ACCES 
                WHERE NomAtelier = ? 
                ORDER BY ID_Action
            """, (atelier,))
            droits = cursor.fetchall()
            for droit in droits:
                status = "AUTORISE" if droit.Autorise == 1 else "REFUSE"
                print(f"  ID_Action {droit.ID_Action}: {status} (Autorise = {droit.Autorise})")
            print()
        
        # Vérifier spécifiquement les ID_Action 3 et 4
        print("=" * 80)
        print("ETAT ACTUEL DES ID_Action 3 ET 4 POUR LES ATELIERS:")
        print("=" * 80)
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
            print(f"{row.NomAtelier} - ID_Action {row.ID_Action}: {status} (Autorise = {row.Autorise})")
        
        print()
        print("=" * 80)

if __name__ == "__main__":
    verifier()
