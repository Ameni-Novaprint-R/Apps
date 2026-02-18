"""
Script pour ajouter dans WEB_DROITS_ACCES les droits du matricule 397
pour les ID_Action: 2, 3, 4, 6, 7, 8
"""
from db import get_db_cursor

MATRICULE = 397
ID_ACTIONS = [2, 3, 4, 6, 7, 8]
AUTORISE = 1

def inserer_droits_matricule_397():
    try:
        with get_db_cursor() as cursor:
            # Verifier que le matricule 397 existe dans personel
            cursor.execute(
                "SELECT Matricule, Nom, Prenom FROM personel WHERE Matricule = ?",
                (MATRICULE,),
            )
            emp = cursor.fetchone()
            if not emp:
                print(f"[ERREUR] Le matricule {MATRICULE} n'existe pas dans la table personel.")
                return False
            print(f"[OK] Matricule {MATRICULE} trouve: {emp.Nom} {emp.Prenom}")

            # Verifier que les ID_Action existent dans WEB_ACTIONS
            placeholders = ",".join(["?" for _ in ID_ACTIONS])
            cursor.execute(
                f"SELECT ID, Action, ID_Section FROM WEB_ACTIONS WHERE ID IN ({placeholders})",
                ID_ACTIONS,
            )
            actions = {row.ID: row for row in cursor.fetchall()}
            manquants = [id_a for id_a in ID_ACTIONS if id_a not in actions]
            if manquants:
                print(f"[ERREUR] Les ID_Action suivants n'existent pas dans WEB_ACTIONS: {manquants}")
                return False
            print(f"[OK] Toutes les actions (ID 2,3,4,6,7,8) existent dans WEB_ACTIONS")

            # Verifier les lignes deja presentes pour eviter doublon (contrainte unique)
            cursor.execute(
                """SELECT ID_Action FROM WEB_DROITS_ACCES
                   WHERE Matricule = ? AND ID_Action IN (?,?,?,?,?,?)""",
                (MATRICULE,) + tuple(ID_ACTIONS),
            )
            deja_presents = [row.ID_Action for row in cursor.fetchall()]
            a_inserer = [id_a for id_a in ID_ACTIONS if id_a not in deja_presents]

            if not a_inserer:
                print(f"[INFO] Le matricule {MATRICULE} a deja tous les droits (ID_Action 2,3,4,6,7,8). Rien a inserer.")
                return True

            # Inserer les nouveaux enregistrements
            for id_action in a_inserer:
                cursor.execute(
                    """INSERT INTO WEB_DROITS_ACCES (Matricule, ID_Action, Autorise)
                       VALUES (?, ?, ?)""",
                    (MATRICULE, id_action, AUTORISE),
                )
            cursor.connection.commit()
            print(f"[SUCCES] {len(a_inserer)} ligne(s) inseree(s): Matricule {MATRICULE}, ID_Action {a_inserer}")
            if deja_presents:
                print(f"[INFO] Deja presents (ignores): ID_Action {deja_presents}")
            return True
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("INSERTION WEB_DROITS_ACCES - Matricule 397, ID_Action 2,3,4,6,7,8")
    print("=" * 60)
    ok = inserer_droits_matricule_397()
    print("=" * 60)
    raise SystemExit(0 if ok else 1)
