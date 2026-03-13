# -*- coding: utf-8 -*-
"""
Ajoute les matricules 386, 71 et 134 à WEB_DROITS_ACCES pour l'action 32 (projet 23).
"""
from db import get_db_cursor

ID_ACTION = 32
MATRICULES = [386, 71, 134]
AUTORISE = 1


def main():
    print("=" * 60)
    print("Ajout droits Projet 23 - Matricules 386, 71, 134 (Action 32)")
    print("=" * 60)
    try:
        with get_db_cursor() as cursor:
            for mat in MATRICULES:
                cursor.execute(
                    """SELECT 1 FROM WEB_DROITS_ACCES
                       WHERE Matricule = ? AND ID_Action = ?""",
                    (mat, ID_ACTION),
                )
                if cursor.fetchone():
                    print(f"   [OK] Matricule {mat} a déjà l'action {ID_ACTION}.")
                    continue
                cursor.execute(
                    """INSERT INTO WEB_DROITS_ACCES (Matricule, ID_Action, Autorise)
                       VALUES (?, ?, ?)""",
                    (mat, ID_ACTION, AUTORISE),
                )
                print(f"   [OK] Matricule {mat} -> Action {ID_ACTION} ajouté.")
            cursor.connection.commit()
        print("\nTerminé.")
        return True
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ok = main()
    raise SystemExit(0 if ok else 1)
