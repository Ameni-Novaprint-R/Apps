"""
Script pour ajouter dans WEB_DROITS_ACCES les droits des matricules 32, 268 et 167
pour les ID_Action: 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15
"""
from db import get_db_cursor

MATRICULES = [32, 268, 167]
ID_ACTIONS = [1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15]
AUTORISE = 1

def inserer_droits():
    try:
        with get_db_cursor() as cursor:
            # Verifier que les matricules existent dans personel
            placeholders_mat = ",".join(["?" for _ in MATRICULES])
            cursor.execute(
                f"SELECT Matricule, Nom, Prenom FROM personel WHERE Matricule IN ({placeholders_mat})",
                MATRICULES,
            )
            employes = {row.Matricule: row for row in cursor.fetchall()}
            manquants = [m for m in MATRICULES if m not in employes]
            if manquants:
                print(f"[ERREUR] Matricules introuvables dans personel: {manquants}")
                return False
            for m in MATRICULES:
                e = employes[m]
                print(f"[OK] Matricule {m}: {e.Nom} {e.Prenom}")

            # Verifier que les ID_Action existent dans WEB_ACTIONS
            placeholders_act = ",".join(["?" for _ in ID_ACTIONS])
            cursor.execute(
                f"SELECT ID FROM WEB_ACTIONS WHERE ID IN ({placeholders_act})",
                ID_ACTIONS,
            )
            ids_actions = {row.ID for row in cursor.fetchall()}
            manquants_act = [a for a in ID_ACTIONS if a not in ids_actions]
            if manquants_act:
                print(f"[ERREUR] ID_Action introuvables dans WEB_ACTIONS: {manquants_act}")
                return False
            print(f"[OK] Toutes les actions {ID_ACTIONS} existent dans WEB_ACTIONS")

            # Pour chaque matricule, inserer les droits manquants
            total_inseres = 0
            for matricule in MATRICULES:
                cursor.execute(
                    """SELECT ID_Action FROM WEB_DROITS_ACCES
                       WHERE Matricule = ? AND ID_Action IN ({})""".format(placeholders_act),
                    (matricule,) + tuple(ID_ACTIONS),
                )
                deja_presents = {row.ID_Action for row in cursor.fetchall()}
                a_inserer = [a for a in ID_ACTIONS if a not in deja_presents]
                for id_action in a_inserer:
                    cursor.execute(
                        """INSERT INTO WEB_DROITS_ACCES (Matricule, ID_Action, Autorise)
                           VALUES (?, ?, ?)""",
                        (matricule, id_action, AUTORISE),
                    )
                    total_inseres += 1
                if a_inserer:
                    print(f"[OK] Matricule {matricule}: {len(a_inserer)} droit(s) ajoute(s) (ID_Action {a_inserer})")
                if deja_presents:
                    print(f"[INFO] Matricule {matricule}: deja presents (ignores): ID_Action {sorted(deja_presents)}")

            cursor.connection.commit()
            print(f"[SUCCES] Total: {total_inseres} ligne(s) inseree(s)")
            return True
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("INSERTION WEB_DROITS_ACCES")
    print("Matricules: 32, 268, 167")
    print("ID_Action: 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15")
    print("=" * 60)
    ok = inserer_droits()
    print("=" * 60)
    raise SystemExit(0 if ok else 1)
