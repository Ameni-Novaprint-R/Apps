from db import get_db_connection


def get_or_create_section(cur, id_proj: int, nom: str) -> int:
    cur.execute(
        "SELECT ID FROM WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?",
        (id_proj, nom),
    )
    row = cur.fetchone()
    if row:
        return row.ID

    cur.execute(
        "INSERT INTO WEB_SECTIONS (ID_Proj, Nom, archive) VALUES (?, ?, 0)",
        (id_proj, nom),
    )
    # Récupérer l'ID créé
    cur.execute(
        "SELECT ID FROM WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?",
        (id_proj, nom),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Impossible de retrouver la section créée: {nom}")
    return row.ID


def get_or_create_action(
    cur, id_section: int, action: str, code_proj: str, nom_section: str
) -> int:
    cur.execute(
        "SELECT ID FROM WEB_ACTIONS WHERE ID_Section = ? AND Action = ?",
        (id_section, action),
    )
    row = cur.fetchone()
    if row:
        return row.ID

    cur.execute(
        """
        INSERT INTO WEB_ACTIONS (ID_Section, Action, archive, CodeProj, Nom_SECTIONS)
        VALUES (?, ?, 0, ?, ?)
        """,
        (id_section, action, code_proj, nom_section),
    )
    cur.execute(
        "SELECT ID FROM WEB_ACTIONS WHERE ID_Section = ? AND Action = ?",
        (id_section, action),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Impossible de retrouver l'action créée: {action}")
    return row.ID


def main() -> None:
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        id_proj = 10
        code_proj = "Projet 10"

        # 1) Sections du projet 10
        nom_section_liste = "Liste des contrôles"
        nom_section_nouveau = "Nouveau contrôle"
        nom_section_stats = "Statistiques"

        id_section_liste = get_or_create_section(cur, id_proj, nom_section_liste)
        id_section_nouveau = get_or_create_section(cur, id_proj, nom_section_nouveau)
        id_section_stats = get_or_create_section(cur, id_proj, nom_section_stats)

        print("Sections créées / existantes pour Projet 10 :")
        print(f"  ID {id_section_liste} -> {nom_section_liste}")
        print(f"  ID {id_section_nouveau} -> {nom_section_nouveau}")
        print(f"  ID {id_section_stats} -> {nom_section_stats}")
        print()

        # 2) Actions par section
        actions = {}

        # Liste des contrôles : Consultation, Modification, Suppression
        actions["LISTE_CONTROLES"] = {
            "section_id": id_section_liste,
            "nom_section": nom_section_liste,
            "actions": ["CONSULTATION", "MODIFICATION", "SUPPRESSION"],
        }

        # Nouveau contrôle : Saisie
        actions["NOUVEAU_CONTROLE"] = {
            "section_id": id_section_nouveau,
            "nom_section": nom_section_nouveau,
            "actions": ["SAISIE"],
        }

        # Statistiques : Consultation
        actions["STATISTIQUES"] = {
            "section_id": id_section_stats,
            "nom_section": nom_section_stats,
            "actions": ["CONSULTATION"],
        }

        action_ids: dict[str, dict[str, int]] = {}

        for key, cfg in actions.items():
            section_id = cfg["section_id"]
            nom_section = cfg["nom_section"]
            action_ids[key] = {}
            for act in cfg["actions"]:
                aid = get_or_create_action(cur, section_id, act, code_proj, nom_section)
                action_ids[key][act] = aid

        conn.commit()

        print("Actions créées / existantes pour Projet 10 :")
        for key, mapping in action_ids.items():
            print(f"  Section logique {key}:")
            for act, aid in mapping.items():
                print(f"    - {act}: ID_Action = {aid}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()

