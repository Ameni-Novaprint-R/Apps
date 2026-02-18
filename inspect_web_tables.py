from db import get_db_cursor

TABLES = ["WEB_PROJETS", "WEB_SECTIONS", "WEB_ACTIONS", "WEB_DROITS_ACCES"]


def print_schemas() -> None:
    for table in TABLES:
        print(f"==== {table} ====")
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    """
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                    """,
                    table,
                )
                rows = cur.fetchall()
        except Exception as e:  # pragma: no cover - diagnostic only
            print(f"Erreur pour {table}: {e}")
            print()
            continue

        if not rows:
            print("(aucune colonne trouvée)")
        else:
            for name, dtype, nullable in rows:
                print(f"{name}\t{dtype}\t{nullable}")
        print()


def print_projet10_data() -> None:
    print("""========================
DONNÉES EXISTANTES POUR PROJET 10
========================""")
    with get_db_cursor() as cur:
        # Vérifier que le projet 10 existe
        print("-- WEB_PROJETS (ID = 10) --")
        cur.execute(
            "SELECT ID, NumProj, CodeProj, Nom, archive FROM WEB_PROJETS WHERE ID = 10"
        )
        for row in cur.fetchall():
            print(row)
        print()

        # Sections du projet 10
        print("-- WEB_SECTIONS (ID_Proj = 10) --")
        cur.execute(
            "SELECT ID, ID_Proj, Nom, archive FROM WEB_SECTIONS WHERE ID_Proj = 10"
        )
        sections = cur.fetchall()
        for row in sections:
            print(row)
        print()

        # Actions liées à ces sections
        print("-- WEB_ACTIONS (pour les sections du projet 10) --")
        if sections:
            section_ids = [str(row.ID) for row in sections]
            in_clause = ",".join(section_ids)
            query = f"SELECT ID, ID_Section, Action, archive, CodeProj, Nom_SECTIONS FROM WEB_ACTIONS WHERE ID_Section IN ({in_clause})"
            cur.execute(query)
            for row in cur.fetchall():
                print(row)
        else:
            print("(aucune section pour le projet 10)")
        print()


def main() -> None:
    print_schemas()
    print_projet10_data()


if __name__ == "__main__":
    main()

