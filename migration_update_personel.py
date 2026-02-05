"""
Migration pour mettre à jour la table personel selon la liste fournie.

Règles :
1. Matricule reste INT (pas de padding avec zéros)
2. Pour BEN/BEL : préfixe + mot suivant = Nom, reste = Prenom
   Ex: "BEL MABROROUK ABDELMAJID" → Nom="BEL MABROROUK", Prenom="ABDELMAJID"
3. Email et mdp = NULL pour nouveaux employés
4. Archiver (archive=1) les employés absents de la liste (sauf matricules 321 et 179)
5. Supprimer les lignes dans WEB_DROITS_ACCES pour les employés archivés
6. Matricules 321 et 179 restent toujours actifs (archive=0) et inchangés (super-utilisateurs)
"""

from db import get_db_cursor

# Liste des employés à partir de l'image fournie
# Format: (Matricule, NomPrenom)
EMPLOYES_LISTE = [
    (13, "SALLEM SOFIENE"),
    (22, "BEL MABROUK ABDELMAJID"),
    (32, "DAMMAK AKRAM"),
    (44, "HAMMAMI ZOUHAIR"),
    (49, "SAHRAOUI HALIMA"),
    (71, "MILADI HOUYEM"),
    (72, "HENTATI BASMA"),
    (77, "BACCOUCHE MOHAMED ANIS"),
    (104, "YENGUI SAMEH"),
    (122, "RMIDA MOHAMED"),
    (134, "TRIGUI AHMED"),
    (135, "ZQUARI MOHAMED"),
    (140, "KDHIR ABDENNACEUR"),
    (143, "CHAABOUNI AMINA"),
    (144, "MSELMI NAJET"),
    (145, "CHTOUROU MOHAMED AL"),
    (148, "SOUDANI NEJI"),
    (167, "BEN AMOR MOHAMED"),
    (179, "YAICHE MOHAMED ANOUAR"),
    (181, "BEN YAZID IKHLAS"),
    (185, "GRIQUI SAMEH"),
    (191, "BAATI AMAL"),
    (197, "CHARFEDDINE MOEZ"),
    (220, "CHAYEB HOUDA"),
    (223, "OULED IMAA HABIBA"),
    (225, "OUDERNI NAFISSA"),
    (227, "CHAMTOURI REBAH"),
    (231, "MILADI HASSEN"),
    (234, "DABBECH ABDERRAHMEN"),
    (240, "RANNEN HABIB"),
    (250, "BEN AMOR AYMEN"),
    (254, "SOUISSI NEDER"),
    (266, "BACCOUCHE SANA"),
    (267, "CHRITI AHLEM"),
    (268, "BEN HMIDA MOKHLES"),
    (269, "NAHALI TARAK"),
    (270, "GARGOURI SAHAR"),
    (275, "IBN RACHED SAMIHA"),
    (278, "MBAREK MOHAMED"),
    (280, "MBAREK AIDA"),
    (281, "MASMOUDI LATIFA"),
    (285, "BEN IMAA HAZAR"),
    (297, "REBAI NIZAR"),
    (302, "SOUISSI HOUSSEM"),
    (307, "MOALLA REFKA"),
    (309, "TRARELSI DALINDA"),
    (310, "LOUSSAIER RAMI"),
    (311, "MLIK FIRAS"),
    (312, "BOUGHANMI HAJER"),
    (327, "MSEKNI CHEDI"),
    (332, "AKROUT RIM"),
    (334, "SAHNOUN IMEN"),
    (343, "ISKANDER KETATA"),
    (347, "HECHMI FOUED"),
    (350, "JAWA ANIS"),
    (353, "CHAABEN FARIDA"),
    (354, "AMEL HAMDI"),
    (357, "KHEDHRI SALWA"),
    (358, "CHAABANE FAIMA"),
    (361, "ZOUHA GHRAB"),
    (362, "CHRIHA FATMA"),
    (364, "SFAXI HSAN"),
    (365, "BEN SALAH MAKRAM"),
    (366, "CHAARI ISLEM"),
    (367, "ACHOURI KHAOULA"),
    (368, "NOUIR SOULEF"),
    (371, "SELLIMI BASMA"),  # Corrigé de 03/1
    (378, "ABBES MARIEM"),
    (379, "YAAKOUBI KHOULOUD"),
    (381, "BOUHLEL RAYEN"),
    (382, "SOUISSI MOHAMED"),
    (386, "BOUHLEL SAFA"),
    (390, "ABDELHEDI AMENI"),
    (391, "DAROUICHE MELEK"),
    (392, "LOUSSAIF MANEL"),
    (393, "GABSI SAHAR"),
    (394, "SQUISSI IBRAHIM"),
    (395, "NOUIR KARIM"),
]


def separer_nom_prenom(nom_prenom_complet):
    """
    Sépare Nom et Prenom selon les règles :
    - Pour BEN/BEL : préfixe + mot suivant = Nom, reste = Prenom
    - Sinon : premier mot = Nom, reste = Prenom
    """
    if not nom_prenom_complet or not nom_prenom_complet.strip():
        return "", ""
    
    mots = nom_prenom_complet.strip().split()
    if not mots:
        return "", ""
    
    # Vérifier si commence par BEN ou BEL
    if mots[0].upper() in ["BEN", "BEL"]:
        if len(mots) >= 2:
            # BEN/BEL + mot suivant = Nom
            nom = f"{mots[0]} {mots[1]}"
            prenom = " ".join(mots[2:]) if len(mots) > 2 else ""
            return nom, prenom
        else:
            # Juste BEN ou BEL
            return mots[0], ""
    else:
        # Premier mot = Nom, reste = Prenom
        nom = mots[0]
        prenom = " ".join(mots[1:]) if len(mots) > 1 else ""
        return nom, prenom


def run():
    if not EMPLOYES_LISTE:
        print("ERREUR: La liste EMPLOYES_LISTE est vide.")
        print("Veuillez remplir cette liste avec les données de l'image.")
        return
    
    print("=" * 80)
    print("MIGRATION: Mise à jour de la table personel")
    print("=" * 80)
    print()
    
    # Créer un dictionnaire pour faciliter la recherche
    employes_dict = {}
    for matricule, nom_prenom in EMPLOYES_LISTE:
        nom, prenom = separer_nom_prenom(nom_prenom)
        employes_dict[matricule] = {"nom": nom, "prenom": prenom}
    
    print(f"Nombre d'employés dans la liste : {len(employes_dict)}")
    print(f"Matricules dans la liste : {sorted(employes_dict.keys())}")
    print()
    
    with get_db_cursor() as cursor:
        try:
            # 1. Récupérer tous les employés actuels
            cursor.execute("SELECT Matricule, Nom, Prenom, archive FROM personel")
            employes_actuels = {row.Matricule: row for row in cursor.fetchall()}
            print(f"Nombre d'employés dans la table : {len(employes_actuels)}")
            
            # 2. Identifier les actions à effectuer
            a_mettre_a_jour = []
            a_ajouter = []
            a_archiver = []
            
            for matricule in employes_dict.keys():
                if matricule in employes_actuels:
                    # Vérifier si mise à jour nécessaire
                    emp_actuel = employes_actuels[matricule]
                    emp_nouveau = employes_dict[matricule]
                    if (emp_actuel.Nom != emp_nouveau["nom"] or 
                        emp_actuel.Prenom != emp_nouveau["prenom"]):
                        a_mettre_a_jour.append((matricule, emp_nouveau))
                else:
                    a_ajouter.append((matricule, employes_dict[matricule]))
            
            # Matricules spéciaux (super-utilisateurs) qui ne doivent jamais être archivés
            SUPER_USER_MATRICULES = [321, 179]
            
            for matricule in employes_actuels.keys():
                if matricule not in employes_dict and matricule not in SUPER_USER_MATRICULES:
                    a_archiver.append(matricule)
            
            print(f"\nActions à effectuer :")
            print(f"  - À mettre à jour : {len(a_mettre_a_jour)}")
            if a_mettre_a_jour:
                for matricule, emp in a_mettre_a_jour[:5]:  # Afficher les 5 premiers
                    print(f"      • Matricule {matricule}: {emp['nom']} {emp['prenom']}")
                if len(a_mettre_a_jour) > 5:
                    print(f"      ... et {len(a_mettre_a_jour) - 5} autre(s)")
            print(f"  - À ajouter : {len(a_ajouter)}")
            if a_ajouter:
                for matricule, emp in a_ajouter[:5]:  # Afficher les 5 premiers
                    print(f"      • Matricule {matricule}: {emp['nom']} {emp['prenom']}")
                if len(a_ajouter) > 5:
                    print(f"      ... et {len(a_ajouter) - 5} autre(s)")
            print(f"  - À archiver : {len(a_archiver)}")
            if a_archiver:
                print(f"      Matricules: {', '.join(str(m) for m in sorted(a_archiver)[:10])}")
                if len(a_archiver) > 10:
                    print(f"      ... et {len(a_archiver) - 10} autre(s)")
            print()
            
            # Demander confirmation (optionnel, peut être commenté pour exécution automatique)
            # reponse = input("Voulez-vous continuer ? (o/n): ")
            # if reponse.lower() != 'o':
            #     print("Migration annulée.")
            #     return
            
            # 3. Mettre à jour les employés existants
            if a_mettre_a_jour:
                print("Mise à jour des employés existants...")
                for matricule, emp in a_mettre_a_jour:
                    cursor.execute("""
                        UPDATE personel 
                        SET Nom = ?, Prenom = ?
                        WHERE Matricule = ?
                    """, (emp["nom"], emp["prenom"], matricule))
                    print(f"  [OK] Matricule {matricule}: {emp['nom']} {emp['prenom']}")
                cursor.connection.commit()
                print("  [OK] Mises à jour effectuées")
            
            # 4. Ajouter les nouveaux employés
            if a_ajouter:
                print("\nAjout des nouveaux employés...")
                for matricule, emp in a_ajouter:
                    cursor.execute("""
                        INSERT INTO personel (Matricule, Nom, Prenom, Adresse_mail, mdp, archive)
                        VALUES (?, ?, ?, NULL, NULL, 0)
                    """, (matricule, emp["nom"], emp["prenom"]))
                    print(f"  [OK] Matricule {matricule}: {emp['nom']} {emp['prenom']}")
                cursor.connection.commit()
                print("  [OK] Ajouts effectués")
            
            # 5. Archiver les employés absents (sauf 321)
            if a_archiver:
                print("\nArchivage des employés absents de la liste...")
                for matricule in a_archiver:
                    cursor.execute("""
                        UPDATE personel 
                        SET archive = 1
                        WHERE Matricule = ?
                    """, (matricule,))
                    print(f"  [OK] Matricule {matricule} archive")
                cursor.connection.commit()
                print("  [OK] Archivages effectués")
                
                # 6. Supprimer les lignes dans WEB_DROITS_ACCES pour les employés archivés
                print("\nSuppression des lignes dans WEB_DROITS_ACCES pour les employés archivés...")
                if a_archiver:
                    placeholders = ",".join("?" * len(a_archiver))
                    cursor.execute(f"""
                        DELETE FROM WEB_DROITS_ACCES
                        WHERE Matricule IN ({placeholders})
                    """, tuple(a_archiver))
                    deleted_count = cursor.rowcount
                    cursor.connection.commit()
                    print(f"  [OK] {deleted_count} ligne(s) supprimee(s) dans WEB_DROITS_ACCES")
                else:
                    print("  [INFO] Aucun employe a archiver, aucune suppression necessaire")
            
            # 7. Vérifier que les matricules spéciaux (321 et 179) restent actifs
            SUPER_USER_MATRICULES = [321, 179]
            for super_mat in SUPER_USER_MATRICULES:
                cursor.execute("SELECT archive FROM personel WHERE Matricule = ?", (super_mat,))
                row = cursor.fetchone()
                if row:
                    if row.archive != 0:
                        cursor.execute("UPDATE personel SET archive = 0 WHERE Matricule = ?", (super_mat,))
                        cursor.connection.commit()
                        print(f"\n  [OK] Matricule {super_mat} force a archive = 0")
                    else:
                        print(f"\n  [OK] Matricule {super_mat} reste actif (archive = 0)")
                else:
                    print(f"\n  [ATTENTION] Matricule {super_mat} non trouve dans la table")
            
            print("\n" + "=" * 80)
            print("MIGRATION TERMINÉE AVEC SUCCÈS!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\nERREUR lors de la migration : {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()


if __name__ == "__main__":
    run()
