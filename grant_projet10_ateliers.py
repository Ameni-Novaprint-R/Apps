from db import get_db_connection


def main() -> None:
    """
    Donne les droits d'accès pour les ateliers 1 à 10
    sur les actions ID = 11 et ID = 14 dans WEB_DROITS_ACCES.

    - Utilise NomAtelier = 'Atelier1', 'Atelier2', ..., 'Atelier10'
    - Matricule = NULL
    - Autorise = 1 (True)
    - N'insère rien si la ligne existe déjà.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        actions = (11, 14)
        for i in range(1, 11):
            nom_atelier = f"Atelier{i}"
            for action_id in actions:
                # Vérifier si le droit existe déjà
                cur.execute(
                    """
                    SELECT ID
                    FROM WEB_DROITS_ACCES
                    WHERE ID_Action = ? AND NomAtelier = ? AND Matricule IS NULL
                    """,
                    (action_id, nom_atelier),
                )
                row = cur.fetchone()
                if row:
                    continue

                # Insérer le droit
                cur.execute(
                    """
                    INSERT INTO WEB_DROITS_ACCES (Matricule, ID_Action, Autorise, NomAtelier)
                    VALUES (?, ?, ?, ?)
                    """,
                    (None, action_id, True, nom_atelier),
                )

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()

