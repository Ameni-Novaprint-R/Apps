"""
Projet 22 - Gestion des droits d'accès
Fonctions pour administrer les droits (WEB_DROITS_ACCES) liés aux projets, sections et actions.
"""
from db import get_db_cursor


def get_projets_avec_sections(inclure_archives=False):
    """Retourne tous les projets (actifs ou tous) avec leurs sections et actions."""
    with get_db_cursor() as cursor:
        arch_clause = "" if inclure_archives else " WHERE WP.archive = 0"
        cursor.execute(f"""
            SELECT WP.ID, WP.NumProj, WP.CodeProj, WP.Nom, WP.archive
            FROM [dbo].[WEB_PROJETS] WP
            {arch_clause}
            ORDER BY WP.NumProj ASC
        """)
        projets = []
        for row in cursor.fetchall():
            proj = {
                "id": row.ID,
                "num": row.NumProj,
                "code": row.CodeProj or "",
                "nom": row.Nom or "",
            }
            sec_arch = "" if inclure_archives else " AND (WS.archive = 0 OR WS.archive IS NULL)"
            cursor.execute(f"""
                SELECT WS.ID, WS.Nom
                FROM [dbo].[WEB_SECTIONS] WS
                WHERE WS.ID_Proj = ? {sec_arch}
                ORDER BY WS.Nom
            """, (row.ID,))
            proj["sections"] = [
                {"id": s.ID, "nom": s.Nom or ""}
                for s in cursor.fetchall()
            ]
            for sec in proj["sections"]:
                act_arch = "" if inclure_archives else " AND (WA.archive = 0 OR WA.archive IS NULL)"
                cursor.execute(f"""
                    SELECT WA.ID, WA.Action
                    FROM [dbo].[WEB_ACTIONS] WA
                    WHERE WA.ID_Section = ? {act_arch}
                    ORDER BY WA.Action
                """, (sec["id"],))
                sec["actions"] = [
                    {"id": a.ID, "action": a.Action or ""}
                    for a in cursor.fetchall()
                ]
            projets.append(proj)
        return projets


def get_droits_accordes():
    """Retourne tous les droits accordés (Matricule ou NomAtelier + ID_Action)."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT WDA.ID, WDA.Matricule, WDA.NomAtelier, WDA.ID_Action, WDA.Autorise,
                   WA.Action as Nom_Action, WA.ID_Section,
                   WS.Nom as Nom_Section, WS.ID_Proj,
                   WP.NumProj, WP.Nom as Nom_Projet
            FROM [dbo].[WEB_DROITS_ACCES] WDA
            INNER JOIN [dbo].[WEB_ACTIONS] WA ON WA.ID = WDA.ID_Action
            INNER JOIN [dbo].[WEB_SECTIONS] WS ON WS.ID = WA.ID_Section
            INNER JOIN [dbo].[WEB_PROJETS] WP ON WP.ID = WS.ID_Proj
            WHERE WDA.Autorise = 1 OR WDA.Autorise IS NULL
            ORDER BY WP.NumProj, WS.Nom, WA.Action
        """)
        result = []
        for row in cursor.fetchall():
            cible = "matricule"
            cible_valeur = row.Matricule
            if cible_valeur is None and row.NomAtelier:
                cible = "atelier"
                cible_valeur = row.NomAtelier
            result.append({
                "id": row.ID,
                "cible": cible,
                "matricule": row.Matricule,
                "nom_atelier": row.NomAtelier,
                "cible_valeur": cible_valeur,
                "id_action": row.ID_Action,
                "nom_action": row.Nom_Action or "",
                "id_section": row.ID_Section,
                "nom_section": row.Nom_Section or "",
                "id_proj": row.ID_Proj,
                "num_proj": row.NumProj,
                "nom_projet": row.Nom_Projet or "",
            })
        return result


def ajouter_droit(cible_type, cible_valeur, id_action):
    """
    Ajoute un droit d'accès.
    cible_type: 'matricule' ou 'atelier'
    cible_valeur: matricule (int) ou nom atelier (str)
    id_action: ID de l'action dans WEB_ACTIONS
    """
    with get_db_cursor() as cursor:
        try:
            matricule = int(cible_valeur) if cible_type == "matricule" else None
            nom_atelier = str(cible_valeur).strip() if cible_type == "atelier" else None

            # Vérifier que l'action existe
            cursor.execute("SELECT ID FROM [dbo].[WEB_ACTIONS] WHERE ID = ?", (id_action,))
            if not cursor.fetchone():
                return {"success": False, "error": "Action introuvable"}

            # Vérifier unicité selon le type
            if cible_type == "matricule":
                cursor.execute(
                    "SELECT ID FROM [dbo].[WEB_DROITS_ACCES] WHERE Matricule = ? AND ID_Action = ?",
                    (matricule, id_action)
                )
                if cursor.fetchone():
                    return {"success": False, "error": "Droit déjà accordé pour ce matricule et cette action"}
            else:
                cursor.execute(
                    "SELECT ID FROM [dbo].[WEB_DROITS_ACCES] WHERE NomAtelier = ? AND ID_Action = ?",
                    (nom_atelier, id_action)
                )
                if cursor.fetchone():
                    return {"success": False, "error": f"Droit déjà accordé pour cet atelier et cette action"}

            cursor.execute(
                """INSERT INTO [dbo].[WEB_DROITS_ACCES] (Matricule, NomAtelier, ID_Action, Autorise)
                   VALUES (?, ?, ?, 1)""",
                (matricule, nom_atelier, id_action)
            )
            cursor.connection.commit()
            return {"success": True, "message": "Droit ajouté avec succès"}
        except Exception as e:
            cursor.connection.rollback()
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}


def supprimer_droit(droit_id):
    """Supprime un droit par son ID."""
    with get_db_cursor() as cursor:
        try:
            cursor.execute("DELETE FROM [dbo].[WEB_DROITS_ACCES] WHERE ID = ?", (droit_id,))
            if cursor.rowcount == 0:
                return {"success": False, "error": "Droit introuvable"}
            cursor.connection.commit()
            return {"success": True, "message": "Droit supprimé avec succès"}
        except Exception as e:
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}


def get_employes_pour_select():
    """Liste des employés (matricule, nom) pour le sélecteur."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT Matricule, Nom, Prenom
            FROM [dbo].[personel]
            WHERE archive = 0 OR archive IS NULL
            ORDER BY CAST(Matricule AS INT) ASC
        """)
        return [
            {"matricule": row.Matricule, "nom": f"{row.Nom or ''} {row.Prenom or ''}".strip() or str(row.Matricule)}
            for row in cursor.fetchall()
        ]


def get_ateliers_pour_select():
    """Liste des ateliers (id, nom) pour le sélecteur."""
    with get_db_cursor() as cursor:
        try:
            cursor.execute("""
                SELECT ID, Nom FROM [dbo].[WEB_ATELIER_ACCES]
                WHERE archive = 0 OR archive IS NULL
                ORDER BY ID
            """)
        except Exception:
            cursor.execute("SELECT ID, Nom FROM [dbo].[WEB_ATELIER_ACCES] ORDER BY ID")
        return [{"id": row.ID, "nom": row.Nom or ""} for row in cursor.fetchall()]


# --- CRUD Projets (WEB_PROJETS) ---

def get_projets_tous(inclure_archives=True):
    """Liste tous les projets, avec ou sans archivés."""
    with get_db_cursor() as cursor:
        if inclure_archives:
            cursor.execute(
                """SELECT ID, NumProj, CodeProj, Nom, archive
                   FROM [dbo].[WEB_PROJETS] ORDER BY NumProj ASC"""
            )
        else:
            cursor.execute(
                """SELECT ID, NumProj, CodeProj, Nom, archive
                   FROM [dbo].[WEB_PROJETS] WHERE archive = 0 ORDER BY NumProj ASC"""
            )
        return [
            {"id": r.ID, "num": r.NumProj, "code": r.CodeProj or "", "nom": r.Nom or "",
             "archive": bool(r.archive) if r.archive is not None else False}
            for r in cursor.fetchall()
        ]


def create_projet(num_proj, code_proj, nom, archive=0):
    with get_db_cursor() as cursor:
        try:
            cursor.execute(
                """INSERT INTO [dbo].[WEB_PROJETS] (NumProj, CodeProj, Nom, archive)
                   VALUES (?, ?, ?, ?)""",
                (num_proj, (code_proj or "").strip(), (nom or "").strip(), 1 if archive else 0)
            )
            cursor.connection.commit()
            return {"success": True, "message": "Projet créé"}
        except Exception as e:
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}


def update_projet(proj_id, num_proj=None, code_proj=None, nom=None, archive=None):
    with get_db_cursor() as cursor:
        try:
            updates, params = [], []
            if num_proj is not None:
                updates.append("NumProj = ?")
                params.append(num_proj)
            if code_proj is not None:
                updates.append("CodeProj = ?")
                params.append((code_proj or "").strip())
            if nom is not None:
                updates.append("Nom = ?")
                params.append((nom or "").strip())
            if archive is not None:
                updates.append("archive = ?")
                params.append(1 if archive else 0)
            if not updates:
                return {"success": False, "error": "Aucune donnée à mettre à jour"}
            params.append(proj_id)
            cursor.execute(
                f"UPDATE [dbo].[WEB_PROJETS] SET {', '.join(updates)} WHERE ID = ?",
                params
            )
            cursor.connection.commit()
            return {"success": True, "message": "Projet mis à jour"}
        except Exception as e:
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}


def archive_projet(proj_id, archive=True):
    return update_projet(proj_id, archive=archive)


# --- CRUD Sections (WEB_SECTIONS) ---

def get_sections_toutes(inclure_archives=True, id_proj=None):
    """Liste les sections, optionnellement filtrées par projet."""
    with get_db_cursor() as cursor:
        sql = """SELECT WS.ID, WS.ID_Proj, WS.Nom, WS.archive, WP.NumProj, WP.Nom as NomProj
                 FROM [dbo].[WEB_SECTIONS] WS
                 INNER JOIN [dbo].[WEB_PROJETS] WP ON WP.ID = WS.ID_Proj
                 WHERE 1=1"""
        params = []
        if id_proj is not None:
            sql += " AND WS.ID_Proj = ?"
            params.append(id_proj)
        if not inclure_archives:
            sql += " AND (WS.archive = 0 OR WS.archive IS NULL)"
        sql += " ORDER BY WP.NumProj, WS.Nom"
        cursor.execute(sql, params)
        return [
            {"id": r.ID, "id_proj": r.ID_Proj, "nom": r.Nom or "", "archive": bool(r.archive) if r.archive is not None else False,
             "num_proj": r.NumProj, "nom_proj": r.NomProj or ""}
            for r in cursor.fetchall()
        ]


def create_section(id_proj, nom, archive=0):
    with get_db_cursor() as cursor:
        try:
            cursor.execute(
                """INSERT INTO [dbo].[WEB_SECTIONS] (ID_Proj, Nom, archive)
                   VALUES (?, ?, ?)""",
                (id_proj, (nom or "").strip(), 1 if archive else 0)
            )
            cursor.connection.commit()
            return {"success": True, "message": "Section créée"}
        except Exception as e:
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}


def update_section(sec_id, id_proj=None, nom=None, archive=None):
    with get_db_cursor() as cursor:
        try:
            updates, params = [], []
            if id_proj is not None:
                updates.append("ID_Proj = ?")
                params.append(id_proj)
            if nom is not None:
                updates.append("Nom = ?")
                params.append((nom or "").strip())
            if archive is not None:
                updates.append("archive = ?")
                params.append(1 if archive else 0)
            if not updates:
                return {"success": False, "error": "Aucune donnée à mettre à jour"}
            params.append(sec_id)
            cursor.execute(
                f"UPDATE [dbo].[WEB_SECTIONS] SET {', '.join(updates)} WHERE ID = ?",
                params
            )
            cursor.connection.commit()
            return {"success": True, "message": "Section mise à jour"}
        except Exception as e:
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}


def archive_section(sec_id, archive=True):
    return update_section(sec_id, archive=archive)


# --- CRUD Actions (WEB_ACTIONS) ---

def get_actions_toutes(inclure_archives=True, id_section=None):
    """Liste les actions, optionnellement filtrées par section."""
    with get_db_cursor() as cursor:
        sql = """SELECT WA.ID, WA.ID_Section, WA.Action, WA.archive, WA.CodeProj, WA.Nom_SECTIONS,
                        WS.Nom as NomSection, WS.ID_Proj, WP.NumProj
                 FROM [dbo].[WEB_ACTIONS] WA
                 INNER JOIN [dbo].[WEB_SECTIONS] WS ON WS.ID = WA.ID_Section
                 INNER JOIN [dbo].[WEB_PROJETS] WP ON WP.ID = WS.ID_Proj
                 WHERE 1=1"""
        params = []
        if id_section is not None:
            sql += " AND WA.ID_Section = ?"
            params.append(id_section)
        if not inclure_archives:
            sql += " AND (WA.archive = 0 OR WA.archive IS NULL)"
        sql += " ORDER BY WP.NumProj, WS.Nom, WA.Action"
        cursor.execute(sql, params)
        return [
            {"id": r.ID, "id_section": r.ID_Section, "action": r.Action or "", "archive": bool(r.archive) if r.archive is not None else False,
             "code_proj": r.CodeProj or "", "nom_sections": r.Nom_SECTIONS or "",
             "nom_section": r.NomSection or "", "id_proj": r.ID_Proj, "num_proj": r.NumProj}
            for r in cursor.fetchall()
        ]


def create_action(id_section, action, archive=0, code_proj=None, nom_sections=None):
    with get_db_cursor() as cursor:
        try:
            act = (action or "").strip()
            code = (code_proj or "").strip() or None
            nom_sec = (nom_sections or "").strip() or None
            cursor.execute(
                """INSERT INTO [dbo].[WEB_ACTIONS] (ID_Section, Action, archive, CodeProj, Nom_SECTIONS)
                   VALUES (?, ?, ?, ?, ?)""",
                (id_section, act, 1 if archive else 0, code, nom_sec)
            )
            cursor.connection.commit()
            return {"success": True, "message": "Action créée"}
        except Exception as e:
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}


def update_action(act_id, id_section=None, action=None, archive=None, code_proj=None, nom_sections=None):
    with get_db_cursor() as cursor:
        try:
            updates, params = [], []
            if id_section is not None:
                updates.append("ID_Section = ?")
                params.append(id_section)
            if action is not None:
                updates.append("Action = ?")
                params.append((action or "").strip())
            if archive is not None:
                updates.append("archive = ?")
                params.append(1 if archive else 0)
            if code_proj is not None:
                updates.append("CodeProj = ?")
                params.append((code_proj or "").strip() or None)
            if nom_sections is not None:
                updates.append("Nom_SECTIONS = ?")
                params.append((nom_sections or "").strip() or None)
            if not updates:
                return {"success": False, "error": "Aucune donnée à mettre à jour"}
            params.append(act_id)
            cursor.execute(
                f"UPDATE [dbo].[WEB_ACTIONS] SET {', '.join(updates)} WHERE ID = ?",
                params
            )
            cursor.connection.commit()
            return {"success": True, "message": "Action mise à jour"}
        except Exception as e:
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}


def archive_action(act_id, archive=True):
    return update_action(act_id, archive=archive)
