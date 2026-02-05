"""
Script pour vérifier les résultats de la migration
"""
from db import get_db_cursor

def verifier():
    with get_db_cursor() as cursor:
        print("=" * 80)
        print("VERIFICATION DE LA MIGRATION")
        print("=" * 80)
        print()
        
        # Nombre total d'employés
        cursor.execute("SELECT COUNT(*) as total FROM personel")
        total = cursor.fetchone().total
        print(f"Nombre total d'employes dans personel: {total}")
        
        # Nombre d'employés actifs (archive = 0)
        cursor.execute("SELECT COUNT(*) as actifs FROM personel WHERE archive = 0")
        actifs = cursor.fetchone().actifs
        print(f"Nombre d'employes actifs (archive = 0): {actifs}")
        
        # Nombre d'employés archivés (archive = 1)
        cursor.execute("SELECT COUNT(*) as archives FROM personel WHERE archive = 1")
        archives = cursor.fetchone().archives
        print(f"Nombre d'employes archives (archive = 1): {archives}")
        
        # Vérifier le matricule 321
        cursor.execute("SELECT Matricule, Nom, Prenom, archive FROM personel WHERE Matricule = 321")
        row = cursor.fetchone()
        if row:
            print(f"\nMatricule 321: {row.Nom} {row.Prenom}, archive = {row.archive}")
            if row.archive == 0:
                print("  [OK] Matricule 321 reste actif")
            else:
                print("  [ERREUR] Matricule 321 devrait etre actif!")
        else:
            print("\n  [ATTENTION] Matricule 321 non trouve")
        
        # Afficher quelques employés archivés
        print("\nEmployes archives (5 premiers):")
        cursor.execute("SELECT TOP 5 Matricule, Nom, Prenom FROM personel WHERE archive = 1 ORDER BY Matricule")
        for row in cursor.fetchall():
            print(f"  Matricule {row.Matricule}: {row.Nom} {row.Prenom}")
        
        # Vérifier les nouveaux employés ajoutés
        print("\nNouveaux employes ajoutes (matricules >= 390):")
        cursor.execute("SELECT Matricule, Nom, Prenom, Adresse_mail, archive FROM personel WHERE Matricule >= 390 ORDER BY Matricule")
        for row in cursor.fetchall():
            mail = row.Adresse_mail if row.Adresse_mail else "NULL"
            print(f"  Matricule {row.Matricule}: {row.Nom} {row.Prenom}, Email: {mail}, archive: {row.archive}")
        
        # Vérifier quelques exemples de séparation Nom/Prenom
        print("\nExemples de separation Nom/Prenom:")
        cursor.execute("""
            SELECT Matricule, Nom, Prenom FROM personel 
            WHERE Matricule IN (22, 167, 268, 365, 13)
            ORDER BY Matricule
        """)
        for row in cursor.fetchall():
            print(f"  Matricule {row.Matricule}: Nom='{row.Nom}', Prenom='{row.Prenom}'")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    verifier()
