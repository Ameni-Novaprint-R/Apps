"""
Script pour insérer les droits d'accès des employés au projet 11
Section: Nouvelle fiche de production
Action: ID_Action = 1
"""
import sys
from db import get_db_cursor

# Liste des matricules autorisés pour la nouvelle fiche de production du projet 11
MATRICULES_AUTORISES = [
    13, 22, 32, 44, 77, 104, 122, 144, 145, 167, 181, 185, 194, 197,
    220, 223, 225, 227, 231, 240, 250, 254, 268, 270, 275, 278, 280,
    285, 302, 306, 310, 311, 312, 321, 327, 343, 345, 347, 350, 353,
    354, 357, 358, 361, 362, 364, 365, 371, 379, 380, 381, 382, 383
]

ID_ACTION = 1  # ID de l'action "Nouvelle fiche de production" du projet 11
AUTORISE = 1   # 1 = autorisé

def inserer_droits_acces():
    """
    Insère les droits d'accès pour les employés autorisés
    """
    try:
        with get_db_cursor() as cursor:
            print("=" * 80)
            print("INSERTION DES DROITS D'ACCES - PROJET 11")
            print("Section: Nouvelle fiche de production")
            print("=" * 80)
            print()
            
            # ÉTAPE 1: Vérifier que ID_Action = 1 existe dans WEB_ACTIONS
            print("ETAPE 1: Verification de l'action ID_Action = 1...")
            cursor.execute("""
                SELECT ID, ID_Section, Action, CodeProj, Nom_SECTIONS
                FROM WEB_ACTIONS
                WHERE ID = ?
            """, (ID_ACTION,))
            
            action = cursor.fetchone()
            if not action:
                print(f"ERREUR: L'action avec ID = {ID_ACTION} n'existe pas dans WEB_ACTIONS!")
                return False
            
            print(f"  [OK] Action trouvee:")
            print(f"    - ID: {action.ID}")
            print(f"    - Action: {action.Action}")
            print(f"    - ID_Section: {action.ID_Section}")
            print(f"    - CodeProj: {action.CodeProj}")
            print(f"    - Nom_SECTIONS: {action.Nom_SECTIONS}")
            
            # Vérifier si c'est bien lié au projet 11
            if action.CodeProj and '11' in str(action.CodeProj):
                print("  [OK] Cette action est bien associee au projet 11")
            elif action.Nom_SECTIONS and 'Nouvelle fiche de production' in action.Nom_SECTIONS:
                print("  [OK] Cette action correspond bien a 'Nouvelle fiche de production'")
            else:
                print("  [ATTENTION] Verification de l'association au projet 11...")
                force = len(sys.argv) > 1 and sys.argv[1] in ['--force', '--yes', '-y']
                if not force:
                    try:
                        confirmation = input("Voulez-vous continuer quand meme? (oui/non): ")
                        if confirmation.lower() not in ['oui', 'o', 'yes', 'y']:
                            return False
                    except EOFError:
                        print("Operation annulee (pas d'entree interactive).")
                        return False
            
            print()
            
            # ÉTAPE 2: Vérifier que tous les matricules existent dans personel
            print(f"ETAPE 2: Verification des {len(MATRICULES_AUTORISES)} matricules dans la table personel...")
            cursor.execute("""
                SELECT Matricule, Nom, Prenom
                FROM personel
                WHERE Matricule IN ({})
                ORDER BY Matricule
            """.format(','.join(['?' for _ in MATRICULES_AUTORISES])), MATRICULES_AUTORISES)
            
            matricules_trouves = cursor.fetchall()
            matricules_trouves_set = {m.Matricule for m in matricules_trouves}
            matricules_manquants = [m for m in MATRICULES_AUTORISES if m not in matricules_trouves_set]
            
            print(f"  Matricules trouves: {len(matricules_trouves)}/{len(MATRICULES_AUTORISES)}")
            
            if matricules_manquants:
                print(f"  [ERREUR] Matricules non trouves dans personel: {matricules_manquants}")
                force = len(sys.argv) > 1 and sys.argv[1] in ['--force', '--yes', '-y']
                if not force:
                    try:
                        confirmation = input("Voulez-vous continuer avec seulement les matricules valides? (oui/non): ")
                        if confirmation.lower() not in ['oui', 'o', 'yes', 'y']:
                            return False
                    except EOFError:
                        print("Operation annulee (pas d'entree interactive).")
                        return False
                matricules_a_inserer = [m for m in MATRICULES_AUTORISES if m in matricules_trouves_set]
            else:
                matricules_a_inserer = MATRICULES_AUTORISES
                print("  [OK] Tous les matricules existent dans la table personel")
            
            print()
            
            # ÉTAPE 3: Vérifier les doublons existants
            print(f"ETAPE 3: Verification des enregistrements existants...")
            cursor.execute("""
                SELECT Matricule, ID_Action, Autorise
                FROM WEB_DROITS_ACCES
                WHERE Matricule IN ({}) AND ID_Action = ?
            """.format(','.join(['?' for _ in matricules_a_inserer])), 
            matricules_a_inserer + [ID_ACTION])
            
            enregistrements_existants = cursor.fetchall()
            
            if enregistrements_existants:
                print(f"  [ATTENTION] {len(enregistrements_existants)} enregistrement(s) existant(s) trouve(s):")
                for enr in enregistrements_existants:
                    # Récupérer le nom de l'employé
                    cursor.execute("""
                        SELECT Nom, Prenom FROM personel WHERE Matricule = ?
                    """, (enr.Matricule,))
                    emp = cursor.fetchone()
                    nom_emp = f"{emp.Nom} {emp.Prenom}" if emp else "N/A"
                    print(f"    - Matricule {enr.Matricule} ({nom_emp}): ID_Action={enr.ID_Action}, Autorise={enr.Autorise}")
                
                print()
                print("Options:")
                print("  1. Mettre a jour les enregistrements existants (changer Autorise a 1)")
                print("  2. Ignorer les enregistrements existants (ne rien faire)")
                print("  3. Annuler l'operation")
                force = len(sys.argv) > 1 and sys.argv[1] in ['--force', '--yes', '-y']
                if force:
                    choix = '1'  # Par défaut, mettre à jour en mode force
                    print("Mode non-interactif: choix automatique = 1 (Mettre a jour)")
                else:
                    try:
                        choix = input("Votre choix (1/2/3): ")
                    except EOFError:
                        print("Operation annulee (pas d'entree interactive).")
                        return False
                
                if choix == '3':
                    print("Operation annulee.")
                    return False
                elif choix == '1':
                    # Mettre à jour les enregistrements existants
                    matricules_a_mettre_a_jour = [e.Matricule for e in enregistrements_existants]
                    matricules_a_inserer = [m for m in matricules_a_inserer if m not in matricules_a_mettre_a_jour]
                    
                    print(f"\nMise a jour de {len(matricules_a_mettre_a_jour)} enregistrement(s)...")
                    for matricule in matricules_a_mettre_a_jour:
                        cursor.execute("""
                            UPDATE WEB_DROITS_ACCES
                            SET Autorise = ?
                            WHERE Matricule = ? AND ID_Action = ?
                        """, (AUTORISE, matricule, ID_ACTION))
                    print(f"  [OK] {len(matricules_a_mettre_a_jour)} enregistrement(s) mis(e) a jour")
                elif choix == '2':
                    # Ignorer les enregistrements existants
                    matricules_a_inserer = [m for m in matricules_a_inserer if m not in [e.Matricule for e in enregistrements_existants]]
                    print(f"  Les enregistrements existants seront ignores")
            else:
                print("  [OK] Aucun enregistrement existant trouve")
            
            print()
            
            # ÉTAPE 4: Insérer les nouveaux enregistrements
            if not matricules_a_inserer:
                print("Aucun nouvel enregistrement a inserer.")
                return True
            
            print(f"ETAPE 4: Insertion de {len(matricules_a_inserer)} nouvel(le)(s) enregistrement(s)...")
            
            # Afficher un aperçu
            print("\nApercu des enregistrements a inserer:")
            for i, matricule in enumerate(matricules_a_inserer[:10], 1):
                cursor.execute("SELECT Nom, Prenom FROM personel WHERE Matricule = ?", (matricule,))
                emp = cursor.fetchone()
                nom_emp = f"{emp.Nom} {emp.Prenom}" if emp else "N/A"
                print(f"  {i}. Matricule {matricule} ({nom_emp}) -> ID_Action={ID_ACTION}, Autorise={AUTORISE}")
            
            if len(matricules_a_inserer) > 10:
                print(f"  ... et {len(matricules_a_inserer) - 10} autre(s)")
            
            print()
            # Vérifier si l'argument --force est passé
            force = len(sys.argv) > 1 and sys.argv[1] in ['--force', '--yes', '-y']
            
            if not force:
                try:
                    confirmation = input("Confirmer l'insertion? (oui/non): ")
                    if confirmation.lower() not in ['oui', 'o', 'yes', 'y']:
                        print("Operation annulee.")
                        return False
                except EOFError:
                    # Si pas d'entrée interactive disponible, utiliser --force
                    print("Pas d'entree interactive disponible.")
                    print("Utilisez: python inserer_droits_acces_projet11.py --force")
                    return False
            else:
                print("Mode non-interactif active (--force)")
            
            # Insérer les données
            insertions_reussies = 0
            insertions_echouees = []
            
            for matricule in matricules_a_inserer:
                try:
                    cursor.execute("""
                        INSERT INTO WEB_DROITS_ACCES (Matricule, ID_Action, Autorise)
                        VALUES (?, ?, ?)
                    """, (matricule, ID_ACTION, AUTORISE))
                    insertions_reussies += 1
                except Exception as e:
                    insertions_echouees.append((matricule, str(e)))
                    print(f"  [ERREUR] Echec insertion matricule {matricule}: {e}")
            
            cursor.connection.commit()
            
            print()
            print("=" * 80)
            print("RESULTAT DE L'OPERATION")
            print("=" * 80)
            print(f"Insertions reussies: {insertions_reussies}/{len(matricules_a_inserer)}")
            
            if insertions_echouees:
                print(f"\nInsertions echouees: {len(insertions_echouees)}")
                for matricule, erreur in insertions_echouees:
                    print(f"  - Matricule {matricule}: {erreur}")
            
            if len(enregistrements_existants) > 0 and choix == '1':
                print(f"\nMises a jour reussies: {len(matricules_a_mettre_a_jour)}")
            
            print("=" * 80)
            
            return insertions_reussies > 0 or (len(enregistrements_existants) > 0 and choix == '1')
            
    except Exception as e:
        print(f"\nERREUR lors de l'insertion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("INSERTION DES DROITS D'ACCES")
    print("Projet 11 - Nouvelle fiche de production")
    print("Base de donnees: novaprint_restored")
    print("Serveur: 192.168.10.225")
    print("=" * 80)
    print()
    
    success = inserer_droits_acces()
    
    if success:
        print("\n[OK] Operation terminee avec succes!")
        sys.exit(0)
    else:
        print("\n[ERREUR] Operation echouee ou annulee!")
        sys.exit(1)
