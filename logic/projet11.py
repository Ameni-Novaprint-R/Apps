#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PROJET 11 - Gestion de la table WEB_TRAITEMENTS
Module pour gérer les traitements avec données provenant de plusieurs tables
"""

from datetime import datetime
from contextlib import contextmanager
from decimal import Decimal
import re
import pyodbc
# Utiliser la fonction de connexion de db.py qui fonctionne déjà
from db import get_db_cursor


def _to_int(value):
    """Convertit une valeur vers un entier sans lever d'exception."""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        return int(value)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def column_exists(cursor, table_name, column_name):
    """Vérifie si une colonne existe dans une table SQL Server."""
    try:
        cursor.execute("""
            SELECT COUNT(*) as col_exists
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ? AND COLUMN_NAME = ?
        """, (table_name, column_name))
        return cursor.fetchone().col_exists > 0
    except Exception:
        return False


_cloture_column_ensured = False
_description_column_ensured = False
_nom_fd_column_ensured = False
_chrono_affichage_en_pause_ensured = False
_chrono_affichage_snapshot_at_ensured = False
_controle_valide_columns_ensured = False
_compteur_mode_column_ensured = False
_compteur_lecture_column_ensured = False

_web_commande_qte_unitaire_ensured = False


def ensure_web_commande_qte_unitaire_table():
    """Crée/évolue WEB_COMMANDE_QTE_UNITAIRE (cache calcul quantité finale)."""
    global _web_commande_qte_unitaire_ensured
    if _web_commande_qte_unitaire_ensured:
        return
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS c
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='WEB_COMMANDE_QTE_UNITAIRE'
                """
            )
            if cursor.fetchone().c > 0:
                # Évolution schéma si table déjà présente
                if not column_exists(cursor, 'WEB_COMMANDE_QTE_UNITAIRE', 'NombreModeles'):
                    cursor.execute("ALTER TABLE dbo.WEB_COMMANDE_QTE_UNITAIRE ADD NombreModeles INT NULL")
                if not column_exists(cursor, 'WEB_COMMANDE_QTE_UNITAIRE', 'QteFinale'):
                    cursor.execute("ALTER TABLE dbo.WEB_COMMANDE_QTE_UNITAIRE ADD QteFinale DECIMAL(18, 3) NULL")
                cursor.connection.commit()
                _web_commande_qte_unitaire_ensured = True
                return
            cursor.execute(
                """
                CREATE TABLE dbo.WEB_COMMANDE_QTE_UNITAIRE (
                    ID INT NOT NULL PRIMARY KEY,
                    Numero NVARCHAR(50) NULL,
                    Reference NVARCHAR(255) NULL,
                    QteComm DECIMAL(18, 3) NULL,
                    NombrePose INT NULL,
                    NombreModeles INT NULL,
                    QteFinale DECIMAL(18, 3) NULL,
                    QteUnitaire DECIMAL(18, 3) NULL -- compat: ancienne colonne
                );
                """
            )
            cursor.connection.commit()
            _web_commande_qte_unitaire_ensured = True
            print("[projet11] Table WEB_COMMANDE_QTE_UNITAIRE créée.")
    except Exception as e:
        print(f"[projet11] ensure_web_commande_qte_unitaire_table: {e}")
    finally:
        _web_commande_qte_unitaire_ensured = True


def extract_nombre_pose(reference):
    """
    Extraction heuristique du nombre de poses depuis Reference.
    Exemples attendus: "PLANCHE 24 POSES", "planche 9 poses", "12 P".
    """
    if not reference:
        return None
    try:
        import re
        s = str(reference)
        # Chercher un entier suivi de "pose", "poses" ou "p" (P) même sans espaces (ex: "PLANCHE16POSES")
        # Ne pas exiger une frontière de mot avant le nombre (sinon "PLANCHE16..." ne matche pas).
        m = re.search(r"(?i)(?<!\d)(\d{1,3})\s*(?:poses?\b|p\b)", s)
        if not m:
            # Variante "PLANCHE16POSES" / "PLANCHE 16 POSES"
            m = re.search(r"(?i)planch(?:e)?\s*(\d{1,3})\s*poses?\b", s)
        if m:
            v = int(m.group(1))
            if 1 <= v <= 999:
                return v
        return None
    except Exception:
        return None


def get_commandes_qte_unitaires(limit=2000):
    """Retourne les commandes + poses + modèles + quantité finale calculée."""
    ensure_web_commande_qte_unitaire_table()
    lim = int(limit) if limit else 2000
    if lim <= 0:
        lim = 2000
    lim = min(lim, 10000)
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT TOP (?)
                C.ID,
                C.Numero,
                C.Reference,
                C.QteComm,
                C.ID_DEVIS,
                W.NombrePose AS NombrePoseSaved,
                W.NombreModeles AS NombreModelesSaved,
                DE.Modeles AS NombreModelesDevis
            FROM COMMANDES C
            LEFT JOIN WEB_COMMANDE_QTE_UNITAIRE W ON W.ID = C.ID
            LEFT JOIN (
                SELECT ID_DEVIS, MAX(Modeles) AS Modeles
                FROM DEV_ELEM
                GROUP BY ID_DEVIS
            ) DE ON DE.ID_DEVIS = C.ID_DEVIS
            WHERE C.Numero IS NOT NULL AND LTRIM(RTRIM(C.Numero)) <> ''
            ORDER BY C.ID DESC
            """,
            (lim,),
        )
        rows = []
        for r in cursor.fetchall():
            qte_comm = None
            try:
                qte_comm = float(r.QteComm) if r.QteComm is not None else None
            except Exception:
                qte_comm = None
            saved_pose = None
            try:
                saved_pose = int(r.NombrePoseSaved) if r.NombrePoseSaved is not None else None
            except Exception:
                saved_pose = None
            ref = (r.Reference or '').strip() if hasattr(r, "Reference") else ""
            extracted = extract_nombre_pose(ref)
            pose = saved_pose if saved_pose is not None else extracted
            if pose is None:
                pose = 1
            saved_modeles = None
            try:
                saved_modeles = int(r.NombreModelesSaved) if r.NombreModelesSaved is not None else None
            except Exception:
                saved_modeles = None
            devis_modeles = None
            try:
                devis_modeles = int(r.NombreModelesDevis) if r.NombreModelesDevis is not None else None
            except Exception:
                devis_modeles = None
            nb_modeles = saved_modeles if saved_modeles is not None else devis_modeles

            qte_finale = None
            if qte_comm is not None and pose is not None:
                try:
                    if nb_modeles is None:
                        qte_finale = qte_comm * float(pose)
                    else:
                        qte_finale = qte_comm * float(pose) * float(nb_modeles)
                except Exception:
                    qte_finale = None
            rows.append(
                {
                    "id": int(r.ID),
                    "numero": (r.Numero or "").strip(),
                    "reference": ref,
                    "qte_comm": qte_comm,
                    "nombre_pose": pose,
                    "nombre_pose_extrait": extracted,
                    "nombre_pose_source": "saved" if saved_pose is not None else ("extrait" if extracted is not None else "defaut"),
                    "nombre_modeles": nb_modeles,
                    "nombre_modeles_source": "saved" if saved_modeles is not None else ("devis" if devis_modeles is not None else "vide"),
                    "qte_finale": qte_finale,
                }
            )
        return rows


def upsert_commande_qte_unitaire(id_commande, numero, reference, qte_comm, nombre_pose, nombre_modeles):
    """Upsert WEB_COMMANDE_QTE_UNITAIRE (ID=COMMANDES.ID)."""
    ensure_web_commande_qte_unitaire_table()
    try:
        tid = int(id_commande)
    except Exception:
        return False, "ID commande invalide"
    try:
        pose = int(nombre_pose) if nombre_pose is not None and str(nombre_pose).strip() != "" else None
    except Exception:
        pose = None
    if pose is not None and pose <= 0:
        pose = None
    try:
        nb_modeles = int(nombre_modeles) if nombre_modeles is not None and str(nombre_modeles).strip() != "" else None
    except Exception:
        nb_modeles = None
    if nb_modeles is not None and nb_modeles <= 0:
        nb_modeles = None
    qte_finale = None
    try:
        qc = float(qte_comm) if qte_comm is not None and str(qte_comm).strip() != "" else None
    except Exception:
        qc = None
    if qc is not None and pose is not None:
        if nb_modeles is None:
            qte_finale = qc * float(pose)
        else:
            qte_finale = qc * float(pose) * float(nb_modeles)
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                MERGE dbo.WEB_COMMANDE_QTE_UNITAIRE AS T
                USING (SELECT ? AS ID) AS S
                ON T.ID = S.ID
                WHEN MATCHED THEN
                    UPDATE SET Numero = ?, Reference = ?, QteComm = ?, NombrePose = ?, NombreModeles = ?, QteFinale = ?, QteUnitaire = ?
                WHEN NOT MATCHED THEN
                    INSERT (ID, Numero, Reference, QteComm, NombrePose, NombreModeles, QteFinale, QteUnitaire)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    tid,
                    (numero or "")[:50],
                    (reference or "")[:255],
                    qc,
                    pose,
                    nb_modeles,
                    qte_finale,
                    qte_finale,
                    tid,
                    (numero or "")[:50],
                    (reference or "")[:255],
                    qc,
                    pose,
                    nb_modeles,
                    qte_finale,
                    qte_finale,
                ),
            )
            cursor.connection.commit()
            return True, None
    except Exception as e:
        return False, str(e)


def _ht_ap_remise_has_three_decimals(val):
    """True si la valeur HT conserve une 3e décimale significative (ex. base 1,234 TND)."""
    if val is None:
        return False
    try:
        d = Decimal(str(val))
    except Exception:
        return False
    return d != d.quantize(Decimal("0.01"))


def parse_filtre_numero_dossier_ecarts(q):
    """
    Filtre N° dossier :
    - intervalle : "202601-202603" ou "202601 à 202603"
      Bornes entièrement numériques et de même longueur : plage [de, fin] au sens
      préfixes prolongeables (ex. 202602-202603 → >= 202602 et < 202604, donc tout 202603… inclus).
    - sinon : préfixe (ex: "2025" -> LIKE '2025%')
    """
    s = (q or "").strip()
    if not s:
        return {"type": "none"}
    m = re.match(r"^\s*(\d+)\s*(?:-|à|to)\s*(\d+)\s*$", s, flags=re.IGNORECASE)
    if m:
        return {"type": "interval", "de": m.group(1), "a": m.group(2)}
    return {"type": "prefix", "prefix": s}


def get_suivi_ecarts_facturation_par_dossier(filtre_numero=None, limit=4000):
    """
    Suivi des écarts de facturation par dossier (COMMANDES + FACTURES_ELEM + FACTURES).

    Une ligne par couple (dossier, facture) : quantités et Px de vente HT (somme HtApRemise)
    sont limités à la facture affichée sur la ligne.

    Affiche les dossiers ayant au moins une ligne FACTURES_ELEM ou (si NumFact existe)
    un NumFact renseigné sans ligne d'élément (une ligne sans montant HT).
    """
    lim = int(limit) if limit else 4000
    if lim <= 0:
        lim = 4000
    lim = min(lim, 20000)

    filt = parse_filtre_numero_dossier_ecarts(filtre_numero)

    rows_out = []
    with get_db_cursor() as cursor:
        has_numfact = column_exists(cursor, "COMMANDES", "NumFact")
        has_ht_ap_remise = column_exists(cursor, "FACTURES_ELEM", "HtApRemise")
        if has_numfact:
            fact_where = (
                "(EXISTS (SELECT 1 FROM FACTURES_ELEM fe0 WHERE fe0.ID_COMMANDE = C.ID) "
                "OR (C.NumFact IS NOT NULL AND LTRIM(RTRIM(C.NumFact)) <> ''))"
            )
        else:
            fact_where = "EXISTS (SELECT 1 FROM FACTURES_ELEM fe0 WHERE fe0.ID_COMMANDE = C.ID)"

        num_expr = "LTRIM(RTRIM(CAST(C.Numero AS NVARCHAR(4000))))"
        where_sql = [fact_where, "C.Numero IS NOT NULL", f"{num_expr} <> ''"]
        params = []

        if filt.get("type") == "interval":
            de, a = filt["de"], filt["a"]

            if (
                re.fullmatch(r"\d+", de)
                and re.fullmatch(r"\d+", a)
                and len(de) == len(a)
            ):
                L = len(de)
                id_de, id_a = int(de), int(a)
                if id_de > id_a:
                    id_de, id_a = id_a, id_de
                de_s = str(id_de).zfill(L)
                a_excl = str(id_a + 1)
                where_sql.append(f"{num_expr} >= ? AND {num_expr} < ?")
                params.extend([de_s, a_excl])
            else:
                where_sql.append(f"{num_expr} >= ? AND {num_expr} <= ?")
                params.extend([de, a])
        elif filt.get("type") == "prefix":
            where_sql.append(f"{num_expr} LIKE ?")
            params.append(f"{filt['prefix']}%")

        where_clause = " AND ".join(where_sql)

        if has_ht_ap_remise:
            px_select = """ISNULL((
                    SELECT SUM(CAST(FEht.HtApRemise AS DECIMAL(18, 4)))
                    FROM FACTURES_ELEM FEht
                    WHERE FEht.ID_COMMANDE = C.ID AND FEht.ID_FACTURE = F.ID
                ), NULL) AS px_vente_ht"""
        else:
            px_select = "CAST(NULL AS DECIMAL(18, 4)) AS px_vente_ht"

        # Lignes : une par facture liée au dossier via FACTURES_ELEM
        sql_par_facture = f"""
            SELECT
                C.ID,
                C.Numero AS numero_dossier,
                ISNULL(NULLIF(LTRIM(RTRIM(S.RaiSocTri)), ''), '-') AS client,
                C.Reference AS reference,
                C.QteComm AS qte_comm,
                C.QteLiv AS qte_liv,
                ISNULL((
                    SELECT SUM(CAST(FE.QteFact AS DECIMAL(18, 4)))
                    FROM FACTURES_ELEM FE
                    WHERE FE.ID_COMMANDE = C.ID AND FE.ID_FACTURE = F.ID
                ), 0) AS qte_facturee,
                C.PrxVteReelExt AS prx_vte_reel_ext,
                C.TotalFact AS total_fact,
                CAST(F.Numero AS NVARCHAR(4000)) AS numeros_factures,
                {px_select}
            FROM COMMANDES C
            LEFT JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
            INNER JOIN (
                SELECT DISTINCT fe.ID_COMMANDE, fe.ID_FACTURE
                FROM FACTURES_ELEM fe
                WHERE fe.ID_FACTURE IS NOT NULL
            ) inv ON inv.ID_COMMANDE = C.ID
            INNER JOIN FACTURES F ON F.ID = inv.ID_FACTURE
            WHERE {where_clause}
        """

        if has_numfact:
            sql_numfact_seul = f"""
            SELECT
                C.ID,
                C.Numero AS numero_dossier,
                ISNULL(NULLIF(LTRIM(RTRIM(S.RaiSocTri)), ''), '-') AS client,
                C.Reference AS reference,
                C.QteComm AS qte_comm,
                C.QteLiv AS qte_liv,
                CAST(0 AS DECIMAL(18, 4)) AS qte_facturee,
                C.PrxVteReelExt AS prx_vte_reel_ext,
                C.TotalFact AS total_fact,
                NULLIF(LTRIM(RTRIM(C.NumFact)), '') AS numeros_factures,
                CAST(NULL AS DECIMAL(18, 4)) AS px_vente_ht
            FROM COMMANDES C
            LEFT JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
            WHERE {where_clause}
              AND NOT EXISTS (SELECT 1 FROM FACTURES_ELEM fe0 WHERE fe0.ID_COMMANDE = C.ID)
              AND C.NumFact IS NOT NULL AND LTRIM(RTRIM(C.NumFact)) <> ''
            """
            sql_union = f"""
            SELECT TOP (?)
                t.ID,
                t.numero_dossier,
                t.client,
                t.reference,
                t.qte_comm,
                t.qte_liv,
                t.qte_facturee,
                t.prx_vte_reel_ext,
                t.total_fact,
                t.numeros_factures,
                t.px_vente_ht
            FROM (
                {sql_par_facture}
                UNION ALL
                {sql_numfact_seul}
            ) t
            ORDER BY LTRIM(RTRIM(CAST(t.numero_dossier AS NVARCHAR(4000)))) DESC
            """
            params_full = tuple([lim] + list(params) + list(params))
        else:
            sql_union = f"""
            SELECT TOP (?)
                x.ID,
                x.numero_dossier,
                x.client,
                x.reference,
                x.qte_comm,
                x.qte_liv,
                x.qte_facturee,
                x.prx_vte_reel_ext,
                x.total_fact,
                x.numeros_factures,
                x.px_vente_ht
            FROM (
                {sql_par_facture}
            ) x
            ORDER BY LTRIM(RTRIM(CAST(x.numero_dossier AS NVARCHAR(4000)))) DESC
            """
            params_full = tuple([lim] + list(params))

        cursor.execute(sql_union, params_full)
        for r in cursor.fetchall():
            px_raw = getattr(r, "px_vente_ht", None)
            rows_out.append(
                {
                    "id": int(r.ID),
                    "numero_dossier": (r.numero_dossier or "").strip(),
                    "client": (r.client or "-").strip(),
                    "reference": (r.reference or "").strip() if r.reference else "",
                    "qte_comm": float(r.qte_comm) if r.qte_comm is not None else None,
                    "qte_liv": float(r.qte_liv) if r.qte_liv is not None else None,
                    "qte_facturee": float(r.qte_facturee) if r.qte_facturee is not None else 0.0,
                    "prx_vte_reel_ext": float(r.prx_vte_reel_ext) if r.prx_vte_reel_ext is not None else None,
                    "total_fact": float(r.total_fact) if r.total_fact is not None else None,
                    "numeros_factures": (r.numeros_factures or "").strip() if r.numeros_factures else "",
                    "px_vente_ht": float(px_raw) if px_raw is not None else None,
                }
            )
    return rows_out


def _get_liste_traitements_validation_action_id():
    """
    ID de l'action de validation contrôle sur la section « Liste des Traitements » (projet 11).
    L'intitulé d'action en base peut être « VALIDATION », « Validation », etc.
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 WA.ID
                FROM dbo.WEB_ACTIONS WA
                INNER JOIN dbo.WEB_SECTIONS WS ON WS.ID = WA.ID_Section
                INNER JOIN dbo.WEB_PROJETS WP ON WP.ID = WS.ID_Proj
                WHERE WP.NumProj = 11
                  AND (
                      LTRIM(RTRIM(WS.Nom)) = N'Liste des Traitements'
                      OR LOWER(LTRIM(RTRIM(WS.Nom))) LIKE N'%liste%traitement%'
                  )
                  AND LOWER(LTRIM(RTRIM(WA.Action))) LIKE N'%validation%'
                  AND (WA.archive = 0 OR WA.archive IS NULL)
                ORDER BY WA.ID
                """
            )
            row = cursor.fetchone()
            return getattr(row, "ID", None) if row else None
    except Exception as e:
        print(f"[projet11] _get_liste_traitements_validation_action_id: {e}")
        return None


def matricule_peut_valider_controle(matricule, is_super_user=False):
    """
    True si l'utilisateur peut valider ou dévalider le contrôle des données.
    Super-utilisateur : oui. Sinon : droit WEB_DROITS_ACCES sur l'action validation
    de la section Liste des Traitements (projet 11), via has_action_access.
    """
    if is_super_user:
        return True
    try:
        from logic.auth import has_action_access
    except Exception:
        return False
    aid = _get_liste_traitements_validation_action_id()
    if aid is None:
        return False
    return has_action_access(aid)


def ensure_controle_valide_columns():
    """Colonnes Contrôle validation (WEB_TRAITEMENTS)."""
    global _controle_valide_columns_ensured
    ensure_nom_fd_column()
    if _controle_valide_columns_ensured:
        return
    try:
        with get_db_cursor() as cursor:
            if not column_exists(cursor, 'WEB_TRAITEMENTS', 'ControleValide'):
                cursor.execute(
                    "ALTER TABLE dbo.WEB_TRAITEMENTS ADD ControleValide TINYINT NULL DEFAULT 0"
                )
            if not column_exists(cursor, 'WEB_TRAITEMENTS', 'ControleValideDte'):
                cursor.execute(
                    "ALTER TABLE dbo.WEB_TRAITEMENTS ADD ControleValideDte DATETIME2 NULL"
                )
            if not column_exists(cursor, 'WEB_TRAITEMENTS', 'ControleValideMatricule'):
                cursor.execute(
                    "ALTER TABLE dbo.WEB_TRAITEMENTS ADD ControleValideMatricule INT NULL"
                )
            cursor.connection.commit()
            print("[projet11] Colonnes contrôle validation vérifiées sur WEB_TRAITEMENTS.")
    except Exception as e:
        print(f"[projet11] ensure_controle_valide_columns: {e}")
    finally:
        _controle_valide_columns_ensured = True


_pause_table_ensured = False
_tps_pause_total_column_ensured = False


def pause_table_exists(cursor):
    """True si la table WEB_TRAITEMENTS_PAUSE existe."""
    try:
        cursor.execute(
            """
            SELECT COUNT(*) AS c FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_TRAITEMENTS_PAUSE'
            """
        )
        return cursor.fetchone().c > 0
    except Exception:
        return False


def ensure_web_traitements_pause_table():
    """Crée WEB_TRAITEMENTS_PAUSE (une ligne par épisode de pause : début, fin optionnelle)."""
    global _pause_table_ensured
    if _pause_table_ensured:
        return
    try:
        with get_db_cursor() as cursor:
            if pause_table_exists(cursor):
                _pause_table_ensured = True
                return
            cursor.execute(
                """
                CREATE TABLE dbo.WEB_TRAITEMENTS_PAUSE (
                    ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                    ID_Traitement INT NOT NULL,
                    DteDebPause DATETIME2 NOT NULL,
                    DteFinPause DATETIME2 NULL,
                    CONSTRAINT FK_WEB_TRAITEMENTS_PAUSE_TRAITEMENT
                        FOREIGN KEY (ID_Traitement) REFERENCES dbo.WEB_TRAITEMENTS(ID) ON DELETE CASCADE
                );
                CREATE INDEX IX_WEB_TRAITEMENTS_PAUSE_ID_Traitement
                    ON dbo.WEB_TRAITEMENTS_PAUSE (ID_Traitement);
                """
            )
            cursor.connection.commit()
            print("[projet11] Table WEB_TRAITEMENTS_PAUSE créée.")
    except Exception as e:
        print(f"[projet11] ensure_web_traitements_pause_table: {e}")
    finally:
        _pause_table_ensured = True


def ensure_tps_pause_total_column():
    """Colonne TpsPauseTotal (heures) sur WEB_TRAITEMENTS — somme des pauses au moment de la finalisation."""
    global _tps_pause_total_column_ensured
    ensure_nom_fd_column()
    if _tps_pause_total_column_ensured:
        return
    try:
        with get_db_cursor() as cursor:
            if column_exists(cursor, "WEB_TRAITEMENTS", "TpsPauseTotal"):
                _tps_pause_total_column_ensured = True
                return
            cursor.execute(
                "ALTER TABLE dbo.WEB_TRAITEMENTS ADD TpsPauseTotal FLOAT NULL"
            )
            cursor.connection.commit()
            print("[projet11] Colonne TpsPauseTotal ajoutée à WEB_TRAITEMENTS.")
    except Exception as e:
        print(f"[projet11] ensure_tps_pause_total_column: {e}")
    finally:
        _tps_pause_total_column_ensured = True


def _sum_pause_seconds_closed(cursor, traitement_id):
    """Somme des durées des pauses terminées (DteFinPause renseignée)."""
    if not pause_table_exists(cursor):
        return 0
    try:
        tid = int(traitement_id)
    except (TypeError, ValueError):
        return 0
    cursor.execute(
        """
        SELECT COALESCE(SUM(DATEDIFF(SECOND, DteDebPause, DteFinPause)), 0)
        FROM dbo.WEB_TRAITEMENTS_PAUSE
        WHERE ID_Traitement = ? AND DteFinPause IS NOT NULL
        """,
        (tid,),
    )
    row = cursor.fetchone()
    if not row:
        return 0
    return max(0, int(row[0] or 0))


def get_pause_seconds_total_display(cursor, traitement_id):
    """Pauses terminées + pause ouverte jusqu’à maintenant (affichage fiche en cours)."""
    closed = _sum_pause_seconds_closed(cursor, traitement_id)
    if not pause_table_exists(cursor):
        return closed
    try:
        tid = int(traitement_id)
    except (TypeError, ValueError):
        return closed
    cursor.execute(
        """
        SELECT TOP 1 DteDebPause FROM dbo.WEB_TRAITEMENTS_PAUSE
        WHERE ID_Traitement = ? AND DteFinPause IS NULL
        ORDER BY ID DESC
        """,
        (tid,),
    )
    r = cursor.fetchone()
    if not r or r[0] is None:
        return closed
    cursor.execute("SELECT DATEDIFF(SECOND, ?, GETDATE())", (r[0],))
    r2 = cursor.fetchone()
    extra = max(0, int(r2[0] or 0)) if r2 else 0
    return closed + extra


def finalize_open_pauses_traitement(cursor, traitement_id, dte_fin_dt):
    """Clôt toute pause ouverte avec DteFinPause = date de fin de production (enregistrement)."""
    if not pause_table_exists(cursor) or dte_fin_dt is None:
        return
    try:
        tid = int(traitement_id)
    except (TypeError, ValueError):
        return
    cursor.execute(
        """
        UPDATE dbo.WEB_TRAITEMENTS_PAUSE
        SET DteFinPause = ?
        WHERE ID_Traitement = ? AND DteFinPause IS NULL
        """,
        (dte_fin_dt, tid),
    )


def start_pause_production(traitement_id):
    """Démarre une pause : une ligne DteDebPause = GETDATE(), DteFinPause NULL."""
    ensure_web_traitements_pause_table()
    try:
        tid = int(traitement_id)
    except (TypeError, ValueError):
        return False, "ID de traitement invalide."
    if is_traitement_controle_valide(tid):
        return False, "Traitement validé au contrôle."
    try:
        with get_db_cursor() as cursor:
            if not pause_table_exists(cursor):
                return False, "Table pause indisponible."
            cursor.execute("SELECT DteFin FROM WEB_TRAITEMENTS WHERE ID = ?", (tid,))
            r = cursor.fetchone()
            if not r:
                return False, "Traitement introuvable."
            if r.DteFin is not None:
                return False, "Traitement déjà terminé."
            cursor.execute(
                """
                SELECT COUNT(*) FROM dbo.WEB_TRAITEMENTS_PAUSE
                WHERE ID_Traitement = ? AND DteFinPause IS NULL
                """,
                (tid,),
            )
            cnt_row = cursor.fetchone()
            if cnt_row and int(cnt_row[0] or 0) > 0:
                return False, "Une pause est déjà en cours."
            cursor.execute(
                """
                INSERT INTO dbo.WEB_TRAITEMENTS_PAUSE (ID_Traitement, DteDebPause, DteFinPause)
                VALUES (?, GETDATE(), NULL)
                """,
                (tid,),
            )
            cursor.connection.commit()
            return True, ""
    except Exception as e:
        print(f"[projet11] start_pause_production: {e}")
        return False, str(e)


def end_pause_production(traitement_id):
    """Termine la pause en cours (DteFinPause = GETDATE()). Idempotent si aucune pause ouverte."""
    ensure_web_traitements_pause_table()
    try:
        tid = int(traitement_id)
    except (TypeError, ValueError):
        return False, "ID de traitement invalide."
    if is_traitement_controle_valide(tid):
        return False, "Traitement validé au contrôle."
    try:
        with get_db_cursor() as cursor:
            if not pause_table_exists(cursor):
                return True, ""
            cursor.execute(
                """
                SELECT TOP 1 ID FROM dbo.WEB_TRAITEMENTS_PAUSE
                WHERE ID_Traitement = ? AND DteFinPause IS NULL
                ORDER BY ID DESC
                """,
                (tid,),
            )
            row = cursor.fetchone()
            if not row:
                return True, ""
            pause_id = row[0]
            cursor.execute(
                """
                UPDATE dbo.WEB_TRAITEMENTS_PAUSE
                SET DteFinPause = GETDATE()
                WHERE ID = ?
                """,
                (pause_id,),
            )
            cursor.connection.commit()
            return True, ""
    except Exception as e:
        print(f"[projet11] end_pause_production: {e}")
        return False, str(e)


def is_traitement_controle_valide(traitement_id):
    """True si la fiche est marquée validée au contrôle."""
    ensure_controle_valide_columns()
    try:
        tid = int(traitement_id)
    except (TypeError, ValueError):
        return False
    try:
        with get_db_cursor() as cursor:
            if not column_exists(cursor, 'WEB_TRAITEMENTS', 'ControleValide'):
                return False
            cursor.execute(
                "SELECT ControleValide FROM WEB_TRAITEMENTS WHERE ID = ?",
                (tid,),
            )
            row = cursor.fetchone()
            if not row:
                return False
            v = getattr(row, "ControleValide", 0)
            return v in (1, True)
    except Exception as e:
        print(f"[projet11] is_traitement_controle_valide: {e}")
        return False


def set_traitement_controle_valide(traitement_id, valide, matricule_validateur):
    """
    Valide ou dévalide le contrôle des données.
    La validation n'est autorisée que si DteFin est renseignée (fiche terminée).
    Retourne (success: bool, message: str).
    """
    ensure_controle_valide_columns()
    try:
        tid = int(traitement_id)
    except (TypeError, ValueError):
        return False, "ID de traitement invalide."
    valide = valide in (True, 1, "1", "true", "True")
    try:
        mv = int(matricule_validateur) if matricule_validateur is not None else None
    except (TypeError, ValueError):
        mv = None
    try:
        with get_db_cursor() as cursor:
            if not column_exists(cursor, "WEB_TRAITEMENTS", "ControleValide"):
                return False, "Colonnes de contrôle non disponibles."
            cursor.execute(
                "SELECT DteFin FROM WEB_TRAITEMENTS WHERE ID = ?",
                (tid,),
            )
            row = cursor.fetchone()
            if not row:
                return False, "Traitement introuvable."
            if valide and row.DteFin is None:
                return (
                    False,
                    "Seule une fiche terminée (date de fin renseignée) peut être validée au contrôle.",
                )
            if valide:
                cursor.execute(
                    """
                    UPDATE WEB_TRAITEMENTS
                    SET ControleValide = 1,
                        ControleValideDte = GETDATE(),
                        ControleValideMatricule = ?,
                        DateModification = GETDATE()
                    WHERE ID = ?
                    """,
                    (mv, tid),
                )
            else:
                cursor.execute(
                    """
                    UPDATE WEB_TRAITEMENTS
                    SET ControleValide = 0,
                        ControleValideDte = NULL,
                        ControleValideMatricule = NULL,
                        DateModification = GETDATE()
                    WHERE ID = ?
                    """,
                    (tid,),
                )
            cursor.connection.commit()
            if cursor.rowcount <= 0:
                return False, "Aucune ligne mise à jour."
            return True, ""
    except Exception as e:
        print(f"[projet11] set_traitement_controle_valide: {e}")
        return False, str(e)


def ensure_chrono_affichage_snapshot_at_column():
    """Horodatage UTC du dernier snapshot chrono en marche (pour ajouter le temps réel hors fiche à la reprise)."""
    global _chrono_affichage_snapshot_at_ensured
    ensure_temps_ecoule_affichage_en_pause_column()
    if _chrono_affichage_snapshot_at_ensured:
        return
    try:
        with get_db_cursor() as cursor:
            if column_exists(cursor, 'WEB_TRAITEMENTS', 'ChronoAffichageSnapshotAt'):
                _chrono_affichage_snapshot_at_ensured = True
                return
            cursor.execute(
                "ALTER TABLE dbo.WEB_TRAITEMENTS ADD ChronoAffichageSnapshotAt DATETIME2 NULL"
            )
            cursor.connection.commit()
            print("[projet11] Colonne ChronoAffichageSnapshotAt ajoutée à WEB_TRAITEMENTS.")
    except Exception as e:
        print(f"[projet11] ensure_chrono_affichage_snapshot_at_column: {e}")
    finally:
        _chrono_affichage_snapshot_at_ensured = True


def ensure_compteur_mode_column():
    """Colonne CompteurMode : 0=journalier (saisie directe), 1=cumulatif (diff lectures)."""
    global _compteur_mode_column_ensured
    if _compteur_mode_column_ensured:
        return
    try:
        with get_db_cursor() as cursor:
            if not column_exists(cursor, "WEB_TRAITEMENTS", "CompteurMode"):
                cursor.execute(
                    "ALTER TABLE dbo.WEB_TRAITEMENTS ADD CompteurMode TINYINT NULL DEFAULT 0"
                )
            cursor.connection.commit()
    except Exception as e:
        print(f"[projet11] ensure_compteur_mode_column: {e}")
    finally:
        _compteur_mode_column_ensured = True


def ensure_compteur_lecture_column():
    """Colonne CompteurLecture : lecture du compteur machine (entier)."""
    global _compteur_lecture_column_ensured
    if _compteur_lecture_column_ensured:
        return
    try:
        with get_db_cursor() as cursor:
            if not column_exists(cursor, "WEB_TRAITEMENTS", "CompteurLecture"):
                cursor.execute("ALTER TABLE dbo.WEB_TRAITEMENTS ADD CompteurLecture INT NULL")
            cursor.connection.commit()
    except Exception as e:
        print(f"[projet11] ensure_compteur_lecture_column: {e}")
    finally:
        _compteur_lecture_column_ensured = True


def get_last_compteur_lecture(numero_commande, nom_service, machine_reelle, exclude_id=None):
    """Dernière lecture compteur pour (dossier + service + machine réelle)."""
    ensure_compteur_lecture_column()
    try:
        numero = (numero_commande or "").strip()
        service = (nom_service or "").strip()
        machine = (machine_reelle or "").strip()
        if not numero or not service or not machine:
            return None
        with get_db_cursor() as cursor:
            if not column_exists(cursor, "WEB_TRAITEMENTS", "CompteurLecture"):
                return None
            exclude_sql = ""
            params = [numero, service, machine]
            if exclude_id:
                exclude_sql = " AND ID <> ?"
                params.append(int(exclude_id))
            cursor.execute(
                f"""
                SELECT TOP 1 CompteurLecture
                FROM WEB_TRAITEMENTS
                WHERE LTRIM(RTRIM(Numero_COMMANDES)) = ?
                  AND LTRIM(RTRIM(Nom_GP_SERVICES)) = ?
                  AND LTRIM(RTRIM(PostesReel)) = ?
                  AND CompteurLecture IS NOT NULL
                  {exclude_sql}
                ORDER BY DateCreation DESC, ID DESC
                """,
                tuple(params),
            )
            row = cursor.fetchone()
            if not row:
                return None
            v = getattr(row, "CompteurLecture", None)
            return int(v) if v is not None else None
    except Exception as e:
        print(f"[projet11] get_last_compteur_lecture: {e}")
        return None


def ensure_temps_ecoule_affichage_en_pause_column():
    """Colonne TempsEcouleAffichageEnPause : 1 = dernier snapshot en pause, 0 = en cours (chrono actif à la fermeture)."""
    global _chrono_affichage_en_pause_ensured
    ensure_cloture_column()
    if _chrono_affichage_en_pause_ensured:
        return
    try:
        with get_db_cursor() as cursor:
            if column_exists(cursor, 'WEB_TRAITEMENTS', 'TempsEcouleAffichageEnPause'):
                _chrono_affichage_en_pause_ensured = True
                return
            cursor.execute(
                "ALTER TABLE dbo.WEB_TRAITEMENTS ADD TempsEcouleAffichageEnPause TINYINT NULL"
            )
            cursor.connection.commit()
            print("[projet11] Colonne TempsEcouleAffichageEnPause ajoutée à WEB_TRAITEMENTS.")
    except Exception as e:
        print(f"[projet11] ensure_temps_ecoule_affichage_en_pause_column: {e}")
    finally:
        _chrono_affichage_en_pause_ensured = True


def ensure_description_column():
    """Vérifie si la colonne Description existe dans WEB_TRAITEMENTS ; si non, l'ajoute."""
    global _description_column_ensured
    if _description_column_ensured:
        return
    try:
        with get_db_cursor() as cursor:
            if column_exists(cursor, 'WEB_TRAITEMENTS', 'Description'):
                _description_column_ensured = True
                return
            cursor.execute("ALTER TABLE dbo.WEB_TRAITEMENTS ADD Description NVARCHAR(MAX) NULL")
            cursor.connection.commit()
            print("[projet11] Colonne Description ajoutée à WEB_TRAITEMENTS.")
    except Exception as e:
        print(f"[projet11] ensure_description_column: {e}")
    finally:
        _description_column_ensured = True


def ensure_cloture_column():
    """Vérifie si les colonnes Cloture et Description existent dans WEB_TRAITEMENTS ; si non, les ajoute."""
    global _cloture_column_ensured
    ensure_description_column()
    if _cloture_column_ensured:
        return
    try:
        with get_db_cursor() as cursor:
            if column_exists(cursor, 'WEB_TRAITEMENTS', 'Cloture'):
                _cloture_column_ensured = True
                return
            cursor.execute("ALTER TABLE dbo.WEB_TRAITEMENTS ADD Cloture TINYINT NULL DEFAULT 0")
            cursor.connection.commit()
            print("[projet11] Colonne Cloture ajoutée à WEB_TRAITEMENTS.")
    except Exception as e:
        print(f"[projet11] ensure_cloture_column: {e}")
    finally:
        _cloture_column_ensured = True


def ensure_nom_fd_column():
    """Vérifie si la colonne NOM_FD existe dans WEB_TRAITEMENTS ; si non, l'ajoute."""
    global _nom_fd_column_ensured
    ensure_cloture_column()
    if _nom_fd_column_ensured:
        return
    try:
        with get_db_cursor() as cursor:
            if column_exists(cursor, 'WEB_TRAITEMENTS', 'NOM_FD'):
                _nom_fd_column_ensured = True
                return
            cursor.execute("ALTER TABLE dbo.WEB_TRAITEMENTS ADD NOM_FD NVARCHAR(100) NULL")
            cursor.connection.commit()
            print("[projet11] Colonne NOM_FD ajoutée à WEB_TRAITEMENTS.")
    except Exception as e:
        print(f"[projet11] ensure_nom_fd_column: {e}")
    finally:
        _nom_fd_column_ensured = True


def _is_typo_service(cursor, service_name):
    """Retourne True si le service correspond au service Typo (GP_SERVICES.ID=5)."""
    if not service_name:
        return False
    try:
        cursor.execute("SELECT Nom FROM GP_SERVICES WHERE ID = 5")
        row = cursor.fetchone()
        nom_typo = (row.Nom or '').strip().lower() if row else ''
        return nom_typo != '' and (service_name or '').strip().lower() == nom_typo
    except Exception:
        return False


def _apply_nom_fd_tirages_delta(cursor, nom_fd, delta):
    """Applique un delta de tirages à WEB_FORMES_DECOUPE.TOTAL_TIRAGES pour une forme (tables dédiées Projet 24)."""
    nom_fd = (nom_fd or '').strip()
    if not nom_fd or not delta:
        return
    cursor.execute("""
        UPDATE WEB_FORMES_DECOUPE
        SET TOTAL_TIRAGES = CASE
            WHEN ISNULL(TOTAL_TIRAGES, 0) + ? < 0 THEN 0
            ELSE ISNULL(TOTAL_TIRAGES, 0) + ?
        END
        WHERE NOM = ?
    """, (int(delta), int(delta), nom_fd))


# ============================================================================
# SUIVI PRODUCTION - Synthèse dossiers x ordres
# ============================================================================

def get_suivi_production_data(client_filter='', dossier_filter='', poste_filter=''):
    """Retourne la matrice Dossier x Ordre pour la section Suivi Production.
    Chaque cellule contient : poste, temps (h), codindav (0=Non commencé, 1=En attente, 2=En cours, 3=Terminé).
    CodIndAv reflète WEB_TRAITEMENTS (DteDeb/DteFin) ; synchronisation faite par sync_codindav_*.
    """
    ensure_cloture_column()
    with get_db_cursor() as cursor:
        has_ordre = column_exists(cursor, 'GP_FICHES_TRAVAIL', 'Ordre')
        ordre_select = 'FT.Ordre AS ordre' if has_ordre else 'ROW_NUMBER() OVER (PARTITION BY FT.ID_COMMANDE ORDER BY FT.ID) AS ordre'
        
        has_cloture = column_exists(cursor, 'WEB_TRAITEMENTS', 'Cloture')
        wt_cols = 'TpsReel, PostesReel, DteFin, w.Cloture' if has_cloture else 'TpsReel, PostesReel, DteFin, CAST(0 AS INT) AS Cloture'
        # Prendre la DERNIÈRE fiche (par date début) pour livraisons partielles : si dernière non clôturée = en cours (bleu)
        wt_order = 'ORDER BY w.DteDeb DESC, w.DateCreation DESC'
        sql = f"""
            SELECT 
                C.Numero AS dossier,
                S.RaiSocTri AS client,
                {ordre_select},
                P.Nom AS poste_prev,
                ISNULL(FT.CodIndAv, 0) AS codindav_ft,
                FT.ID AS id_fiche,
                C.ID AS id_commande,
                FI.TpsPrevDev AS tps_prev,
                WT.TpsReel AS tps_reel,
                WT.PostesReel AS poste_reel,
                WT.DteFin AS dte_fin,
                ISNULL(WT.Cloture, 0) AS cloture
            FROM GP_FICHES_TRAVAIL FT
            INNER JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            LEFT JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
            LEFT JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            LEFT JOIN GP_FICHTRA_INT FI ON FI.ID_FICHTRA = FT.ID
            OUTER APPLY (
                SELECT TOP 1 {wt_cols}
                FROM WEB_TRAITEMENTS w
                WHERE w.ID_FICHE_TRAVAIL = FT.ID
                {wt_order}
            ) WT
            WHERE C.Termine = 0
        """
        params = []
        if client_filter:
            sql += " AND S.RaiSocTri LIKE ?"
            params.append(f"%{client_filter}%")
        if dossier_filter:
            sql += " AND C.Numero LIKE ?"
            params.append(f"%{dossier_filter}%")
        if poste_filter:
            sql += " AND P.Nom LIKE ?"
            params.append(f"%{poste_filter}%")
        sql += " ORDER BY C.Numero, " + ("FT.Ordre" if has_ordre else "FT.ID")
        
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        except Exception as e:
            if 'Ordre' in str(e) or 'invalid column' in str(e).lower() or 'nom de colonne' in str(e).lower():
                wt_cols_fb = 'TpsReel, PostesReel, DteFin, w.Cloture' if has_cloture else 'TpsReel, PostesReel, DteFin, CAST(0 AS INT) AS Cloture'
                wt_order_fb = 'ORDER BY w.DteDeb DESC, w.DateCreation DESC'
                sql_fallback = f"""
                    SELECT 
                        C.Numero AS dossier,
                        S.RaiSocTri AS client,
                        ROW_NUMBER() OVER (PARTITION BY FT.ID_COMMANDE ORDER BY FT.ID) AS ordre,
                        P.Nom AS poste_prev,
                        ISNULL(FT.CodIndAv, 0) AS codindav_ft,
                        FT.ID AS id_fiche,
                        C.ID AS id_commande,
                        FI.TpsPrevDev AS tps_prev,
                        WT.TpsReel AS tps_reel,
                        WT.PostesReel AS poste_reel,
                        WT.DteFin AS dte_fin,
                        ISNULL(WT.Cloture, 0) AS cloture
                    FROM GP_FICHES_TRAVAIL FT
                    INNER JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
                    LEFT JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
                    LEFT JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
                    LEFT JOIN GP_FICHTRA_INT FI ON FI.ID_FICHTRA = FT.ID
                    OUTER APPLY (
                        SELECT TOP 1 {wt_cols_fb}
                        FROM WEB_TRAITEMENTS w
                        WHERE w.ID_FICHE_TRAVAIL = FT.ID
                        {wt_order_fb}
                    ) WT
                    WHERE C.Termine = 0
                """
                add_clauses = []
                if client_filter:
                    add_clauses.append(" AND S.RaiSocTri LIKE ?")
                if dossier_filter:
                    add_clauses.append(" AND C.Numero LIKE ?")
                if poste_filter:
                    add_clauses.append(" AND P.Nom LIKE ?")
                sql_fallback += ''.join(add_clauses) + " ORDER BY C.Numero, FT.ID"
                cursor.execute(sql_fallback, params)
                rows = cursor.fetchall()
            else:
                raise
    
    dossiers = {}
    for r in rows:
        dossier = (r.dossier or '').strip()
        client = (r.client or '').strip()
        ordre = int(r.ordre) if r.ordre is not None else 0
        poste = (r.poste_reel or '').strip() or (getattr(r, 'poste_prev', None) or '').strip()
        codindav_ft = int(r.codindav_ft) if getattr(r, 'codindav_ft', None) is not None else 0
        cloture = int(getattr(r, 'cloture', 0) or 0)
        tps_reel = getattr(r, 'tps_reel', None)
        # Terminé (vert) = dernière fiche clôturée ; si dernière fiche non clôturée = en cours (bleu) même si ancienne clôturée
        if cloture:
            codindav = 3
        elif tps_reel is not None or getattr(r, 'poste_reel', None):
            codindav = 2
        else:
            codindav = codindav_ft
        tps = r.tps_reel if r.tps_reel is not None else r.tps_prev
        try:
            tps_h = round(float(tps), 1) if tps is not None else 0.0
        except (TypeError, ValueError):
            tps_h = 0.0
        
        if dossier not in dossiers:
            dossiers[dossier] = {'dossier': dossier, 'client': client, 'ordres': {}}
        dossiers[dossier]['ordres'][ordre] = {
            'poste': poste,
            'tps_h': tps_h,
            'codindav': codindav,
            'id_fiche': r.id_fiche
        }
    
    max_ordre = max((max(d['ordres'].keys()) for d in dossiers.values() if d['ordres']), default=0)
    lignes = []
    for dossier, data in sorted(dossiers.items()):
        ordres_list = []
        for k in range(1, max_ordre + 1):
            c = data['ordres'].get(k, {'poste': '', 'tps_h': 0.0, 'codindav': 0, 'id_fiche': None})
            ordres_list.append(c)
        lignes.append({
            'dossier': data['dossier'],
            'client': data['client'],
            'ordres': ordres_list
        })
    
    return {'lignes': lignes, 'nb_ordres': max_ordre}


def sync_codindav_for_fiche(id_fiche_travail, cursor):
    """
    Met à jour GP_FICHES_TRAVAIL.CodIndAv pour une fiche, à partir de WEB_TRAITEMENTS.
    - Traitement avec DteDeb + DteFin -> CodIndAv = 3 (Terminé)
    - Traitement avec DteDeb sans DteFin -> CodIndAv = 2 (En cours)
    - Pas de traitement: si ordre précédent terminé -> 1 (En attente), sinon 0 (Non commencé)
    """
    if not id_fiche_travail:
        return
    try:
        if not column_exists(cursor, 'GP_FICHES_TRAVAIL', 'Ordre'):
            return
        has_id_travail = column_exists(cursor, 'GP_FICHES_TRAVAIL', 'ID_TRAVAIL')
        if has_id_travail:
            cursor.execute("SELECT ID_COMMANDE, ID_TRAVAIL, Ordre FROM GP_FICHES_TRAVAIL WHERE ID = ?", (id_fiche_travail,))
        else:
            cursor.execute("SELECT ID_COMMANDE, Ordre FROM GP_FICHES_TRAVAIL WHERE ID = ?", (id_fiche_travail,))
        fiche = cursor.fetchone()
        if not fiche:
            return
        id_commande = fiche.ID_COMMANDE
        ordre = fiche.Ordre if fiche.Ordre is not None else 0
        id_travail = getattr(fiche, 'ID_TRAVAIL', None)
        
        has_cloture = column_exists(cursor, 'WEB_TRAITEMENTS', 'Cloture')
        cloture_col = ', Cloture' if has_cloture else ''
        cursor.execute(f"""
            SELECT TOP 1 DteDeb, DteFin{cloture_col}
            FROM WEB_TRAITEMENTS
            WHERE ID_FICHE_TRAVAIL = ?
            ORDER BY DateCreation DESC
        """, (id_fiche_travail,))
        wt = cursor.fetchone()
        if wt and wt.DteDeb:
            cloture_ok = has_cloture and getattr(wt, 'Cloture', 0) == 1
            cod = 3 if (wt.DteFin or cloture_ok) else 2
        else:
            prev_done = True
            if ordre > 1:
                # Uniquement Cloture=1 = étape définitivement terminée (DteFin seul peut avoir une 2e fiche)
                done_cond = "W.Cloture = 1" if has_cloture else "W.DteFin IS NOT NULL"
                if has_id_travail and id_travail is not None:
                    cursor.execute(f"""
                        SELECT FT.ID
                        FROM GP_FICHES_TRAVAIL FT
                        INNER JOIN WEB_TRAITEMENTS W ON W.ID_FICHE_TRAVAIL = FT.ID AND {done_cond}
                        WHERE FT.ID_COMMANDE = ? AND FT.ID_TRAVAIL = ? AND FT.Ordre = ?
                    """, (id_commande, id_travail, ordre - 1))
                else:
                    cursor.execute(f"""
                        SELECT FT.ID
                        FROM GP_FICHES_TRAVAIL FT
                        INNER JOIN WEB_TRAITEMENTS W ON W.ID_FICHE_TRAVAIL = FT.ID AND {done_cond}
                        WHERE FT.ID_COMMANDE = ? AND FT.Ordre = ?
                    """, (id_commande, ordre - 1))
                prev_done = cursor.fetchone() is not None
            cod = 1 if prev_done else 0
        cursor.execute("UPDATE GP_FICHES_TRAVAIL SET CodIndAv = ? WHERE ID = ?", (cod, id_fiche_travail))
        if cod == 3 and ordre:
            if has_id_travail and id_travail is not None:
                cursor.execute("""
                    SELECT ID FROM GP_FICHES_TRAVAIL
                    WHERE ID_COMMANDE = ? AND ID_TRAVAIL = ? AND Ordre = ?
                """, (id_commande, id_travail, ordre + 1))
            else:
                cursor.execute("""
                    SELECT ID FROM GP_FICHES_TRAVAIL
                    WHERE ID_COMMANDE = ? AND Ordre = ?
                """, (id_commande, ordre + 1))
            next_fiche = cursor.fetchone()
            if next_fiche:
                cursor.execute("UPDATE GP_FICHES_TRAVAIL SET CodIndAv = 1 WHERE ID = ?", (next_fiche.ID,))
    except Exception as e:
        print(f"[projet11] sync_codindav_for_fiche: {e}")


# ============================================================================
# FONCTIONS DE CONSULTATION
# ============================================================================

def get_numeros_commandes_disponibles():
    """
    Récupère tous les numéros de commandes ayant des fiches de travail
    Note: Une même fiche peut avoir plusieurs traitements (production par lots)
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT
                C.Numero,
                C.Reference,
                S.RaiSocTri,
                C.QteComm,
                C.ID
            FROM GP_FICHES_TRAVAIL FT
            INNER JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            LEFT JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
            WHERE C.Numero IS NOT NULL
            AND C.Numero != ''
            ORDER BY C.Numero DESC
        """)
        
        commandes = []
        for row in cursor.fetchall():
            commandes.append({
                "numero": (row.Numero or '').strip(),
                "reference": (row.Reference or '').strip(),
                "client": (row.RaiSocTri or '').strip(),
                "qte_commande": row.QteComm or 0,
                "id_commande": row.ID
            })
        
        return commandes


def get_fiches_by_numero_commande(numero_commande):
    """
    Récupère toutes les fiches de travail pour un numéro de commande spécifique
    Note: Une même fiche peut avoir plusieurs traitements (production par lots)
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                FT.ID as ID_FICHE_TRAVAIL,
                FT.ID_COMMANDE,
                FT.ID_POSTE,
                
                -- Informations COMMANDES
                C.ID as ID_COMMANDE,
                C.Numero as Numero_COMMANDES,
                C.Reference as Reference_COMMANDES,
                C.QteComm as QteComm_COMMANDES,
                C.ID_SOCIETE,
                
                -- Informations SOCIETES
                S.ID as ID_SOCIETE,
                S.RaiSocTri as RaiSocTri_SOCIETES,
                
                -- Informations GP_POSTES
                P.ID as ID_POSTE,
                P.Nom as Nom_GP_POSTES,
                P.ID_SERVICE,
                
                -- Informations GP_SERVICES
                SRV.ID as ID_SERVICE,
                SRV.Nom as Nom_GP_SERVICES
                
            FROM GP_FICHES_TRAVAIL FT
            INNER JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            LEFT JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
            LEFT JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            LEFT JOIN GP_SERVICES SRV ON SRV.ID = P.ID_SERVICE
            WHERE LTRIM(RTRIM(C.Numero)) = ?
            ORDER BY FT.ID DESC
        """, (numero_commande,))
        
        fiches = []
        for row in cursor.fetchall():
            fiches.append({
                "id_fiche_travail": row.ID_FICHE_TRAVAIL,
                "numero_commande": row.Numero_COMMANDES or '',
                "reference": row.Reference_COMMANDES or '',
                "client": row.RaiSocTri_SOCIETES or '',
                "poste": row.Nom_GP_POSTES or '',
                "service": row.Nom_GP_SERVICES or '',
                "qte_commande": row.QteComm_COMMANDES or 0
            })
        
        return fiches


def get_fiches_travail_disponibles():
    """
    Récupère toutes les fiches de travail avec leurs informations
    Note: Une même fiche peut avoir plusieurs traitements (production par lots)
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                FT.ID as ID_FICHE_TRAVAIL,
                FT.ID_COMMANDE,
                FT.ID_POSTE,
                
                -- Informations COMMANDES
                C.ID as ID_COMMANDE,
                C.Numero as Numero_COMMANDES,
                C.Reference as Reference_COMMANDES,
                C.QteComm as QteComm_COMMANDES,
                C.ID_SOCIETE,
                
                -- Informations SOCIETES
                S.ID as ID_SOCIETE,
                S.RaiSocTri as RaiSocTri_SOCIETES,
                
                -- Informations GP_POSTES
                P.ID as ID_POSTE,
                P.Nom as Nom_GP_POSTES,
                P.ID_SERVICE,
                
                -- Informations GP_SERVICES
                SRV.ID as ID_SERVICE,
                SRV.Nom as Nom_GP_SERVICES
                
            FROM GP_FICHES_TRAVAIL FT
            LEFT JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            LEFT JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
            LEFT JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            LEFT JOIN GP_SERVICES SRV ON SRV.ID = P.ID_SERVICE
            ORDER BY FT.ID DESC
        """)
        
        fiches = []
        for row in cursor.fetchall():
            fiches.append({
                "id_fiche_travail": row.ID_FICHE_TRAVAIL,
                "numero_commande": row.Numero_COMMANDES or '',
                "reference": row.Reference_COMMANDES or '',
                "client": row.RaiSocTri_SOCIETES or '',
                "poste": row.Nom_GP_POSTES or '',
                "service": row.Nom_GP_SERVICES or '',
                "qte_commande": row.QteComm_COMMANDES or 0
            })
        
        return fiches


def get_operateurs_disponibles():
    """Récupère la liste des opérateurs disponibles"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                Matricule,
                Nom,
                Prenom
            FROM personel
            WHERE Matricule IS NOT NULL
            ORDER BY Nom, Prenom
        """)
        
        operateurs = []
        for row in cursor.fetchall():
            operateurs.append({
                "matricule": row.Matricule,
                "nom": (row.Nom or '').strip(),
                "prenom": (row.Prenom or '').strip(),
                "nom_complet": f"{(row.Nom or '').strip()} {(row.Prenom or '').strip()}".strip()
            })
        
        return operateurs


def get_postes_disponibles():
    """Récupère la liste de tous les postes/machines disponibles depuis GP_POSTES"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                P.ID,
                P.Nom,
                P.ID_SERVICE,
                S.Nom as Nom_Service
            FROM GP_POSTES P
            LEFT JOIN GP_SERVICES S ON S.ID = P.ID_SERVICE
            WHERE P.Nom IS NOT NULL
            AND P.Nom != ''
            ORDER BY S.Nom, P.Nom
        """)
        
        postes = []
        for row in cursor.fetchall():
            postes.append({
                "id": row.ID,
                "nom": (row.Nom or '').strip(),
                "id_service": row.ID_SERVICE,
                "nom_service": (row.Nom_Service or '').strip(),
                "nom_complet": f"{(row.Nom_Service or '').strip()} - {(row.Nom or '').strip()}".strip()
            })
        
        return postes


def get_services_prevus_by_commande(numero_commande):
    """
    Récupère les SERVICES prévus pour une commande spécifique
    en se basant sur GP_FICHES_TRAVAIL
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT
                SRV.ID as ID_SERVICE,
                SRV.Nom as Nom_Service,
                COUNT(DISTINCT FT.ID) as Nb_Fiches
            FROM GP_FICHES_TRAVAIL FT
            INNER JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            INNER JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            INNER JOIN GP_SERVICES SRV ON SRV.ID = P.ID_SERVICE
            WHERE LTRIM(RTRIM(C.Numero)) = ?
            AND SRV.Nom IS NOT NULL
            GROUP BY SRV.ID, SRV.Nom
            ORDER BY SRV.Nom
        """, (numero_commande,))
        
        services = []
        for row in cursor.fetchall():
            services.append({
                "id_service": row.ID_SERVICE,
                "nom_service": row.Nom_Service,
                "nb_fiches": row.Nb_Fiches
            })
        
        return services


def get_postes_prevus_by_commande_service(numero_commande, nom_service):
    """
    Récupère les POSTES/MACHINES prévus pour une commande et un service spécifiques
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT
                FT.ID as ID_FICHE_TRAVAIL,
                P.ID as ID_POSTE,
                P.Nom as Nom_Poste,
                SRV.Nom as Nom_Service,
                C.Numero as Numero_COMMANDES,
                C.Reference as Reference_COMMANDES,
                C.QteComm as QteComm_COMMANDES,
                S.RaiSocTri as RaiSocTri_SOCIETES,
                FOP.OpPrevDev,
                FTI.TpsPrevDev
            FROM GP_FICHES_TRAVAIL FT
            INNER JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            LEFT JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
            INNER JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            INNER JOIN GP_SERVICES SRV ON SRV.ID = P.ID_SERVICE
            LEFT JOIN GP_FICHTRA_INT FTI ON FTI.ID_FICHTRA = FT.ID
            LEFT JOIN (
                SELECT 
                    ID_FICHE_TRAVAIL,
                    SUM(OpPrevDev) as OpPrevDev
                FROM GP_FICHES_OPERATIONS
                GROUP BY ID_FICHE_TRAVAIL
            ) FOP ON FOP.ID_FICHE_TRAVAIL = FT.ID
            WHERE LTRIM(RTRIM(C.Numero)) = ?
            AND SRV.Nom = ?
            ORDER BY P.Nom
        """, (numero_commande, nom_service))
        
        postes = []
        for row in cursor.fetchall():
            # Logique quantité prévue:
            # Si OpPrevDev existe et > 0, l'utiliser
            # Sinon, utiliser QteComm_COMMANDES (quantité commande)
            qte_prevue = row.OpPrevDev if (row.OpPrevDev and row.OpPrevDev > 0) else row.QteComm_COMMANDES
            
            postes.append({
                "id_fiche_travail": row.ID_FICHE_TRAVAIL,
                "id_poste": row.ID_POSTE,
                "nom_poste": row.Nom_Poste,
                "nom_service": row.Nom_Service,
                "numero_commandes": row.Numero_COMMANDES,
                "reference_commandes": row.Reference_COMMANDES,
                "qte_prevue": qte_prevue,
                "client": row.RaiSocTri_SOCIETES,
                "op_prev_dev": row.OpPrevDev or 0.000,
                "tps_prev_dev": row.TpsPrevDev or 0.000
            })
        
        return postes


def get_traitements_existants_service(numero_commande, nom_service):
    """
    Récupère les traitements déjà enregistrés pour une commande et un service
    pour éviter les doublons et suivre la production
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                WT.ID,
                WT.DteDeb,
                WT.DteFin,
                WT.NbOp,
                WT.NbPers,
                WT.PostesReel,
                WT.Nom_personel,
                WT.Prenom_personel,
                WT.Nom_GP_POSTES as PostePrevu,
                WT.PdtC,
                WT.PdtNNC,
                WT.PdtANC,
                DATEDIFF(MINUTE, WT.DteDeb, ISNULL(WT.DteFin, GETDATE())) as DureeMinutes
            FROM WEB_TRAITEMENTS WT
            WHERE LTRIM(RTRIM(WT.Numero_COMMANDES)) = ?
            AND WT.Nom_GP_SERVICES = ?
            ORDER BY WT.DteDeb DESC
        """, (numero_commande.strip(), nom_service))
        
        traitements = []
        for row in cursor.fetchall():
            duree_heures = row.DureeMinutes / 60.0 if row.DureeMinutes else 0.000
            
            traitements.append({
                "id": row.ID,
                "dte_deb": row.DteDeb.strftime('%Y-%m-%d %H:%M') if row.DteDeb else None,
                "dte_fin": row.DteFin.strftime('%Y-%m-%d %H:%M') if row.DteFin else None,
                "nb_op": _to_int(row.NbOp),
                "nb_pers": _to_int(row.NbPers),
                "postes_reel": row.PostesReel or row.PostePrevu or '',
                "operateur": f"{row.Nom_personel or ''} {row.Prenom_personel or ''}".strip(),
                "pdt_c": _to_int(row.PdtC),
                "pdt_nnc": _to_int(row.PdtNNC),
                "pdt_anc": _to_int(row.PdtANC),
                "duree_minutes": row.DureeMinutes or 0,
                "duree_heures": round(duree_heures, 3),
                "en_cours": row.DteFin is None
            })
        
        return traitements


def get_tous_services():
    """
    Récupère TOUS les services disponibles depuis GP_SERVICES
    Utilisé pour ajouter un service non prévu
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                ID,
                Nom
            FROM GP_SERVICES
            WHERE Nom IS NOT NULL
            AND Nom != ''
            ORDER BY Nom
        """)
        
        services = []
        for row in cursor.fetchall():
            services.append({
                "id_service": row.ID,
                "nom_service": (row.Nom or '').strip()
            })
        
        return services


def get_postes_by_service(nom_service):
    """
    Récupère TOUS les postes/machines d'un service spécifique depuis GP_POSTES
    Utilisé pour les services non prévus
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                P.ID,
                P.Nom
            FROM GP_POSTES P
            INNER JOIN GP_SERVICES S ON S.ID = P.ID_SERVICE
            WHERE S.Nom = ?
            AND P.Nom IS NOT NULL
            AND P.Nom != ''
            ORDER BY P.Nom
        """, (nom_service,))
        
        postes = []
        for row in cursor.fetchall():
            postes.append({
                "id": row.ID,
                "nom": (row.Nom or '').strip()
            })
        
        return postes



def get_traitements_existants_fiche(id_fiche_travail):
    """
    Récupère les traitements déjà existants pour une fiche de travail
    Utile pour savoir combien de sessions de production ont déjà été enregistrées
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                ID,
                DteDeb,
                DteFin,
                NbOp,
                PostesReel
            FROM WEB_TRAITEMENTS
            WHERE ID_FICHE_TRAVAIL = ?
            ORDER BY DteDeb DESC
        """, (id_fiche_travail,))
        
        traitements = []
        for row in cursor.fetchall():
            traitements.append({
                "id": row.ID,
                "dte_deb": row.DteDeb.strftime('%Y-%m-%d %H:%M') if row.DteDeb else None,
                "dte_fin": row.DteFin.strftime('%Y-%m-%d %H:%M') if row.DteFin else None,
                "nb_op": row.NbOp or 0,
                "postes_reel": row.PostesReel or ''
            })
        
        return traitements


def get_operations_by_fiche(id_fiche_travail):
    """
    Récupère les opérations liées à une fiche de travail
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                ID_FICHE_TRAVAIL,
                ID_OPERATION,
                OpPrevDev,
                TpsPrevDev
            FROM GP_FICHES_OPERATIONS
            WHERE ID_FICHE_TRAVAIL = ?
            ORDER BY ID_OPERATION
        """, (id_fiche_travail,))
        
        operations = []
        for row in cursor.fetchall():
            operations.append({
                "id_operation": row.ID_OPERATION,
                "op_prev_dev": row.OpPrevDev or 0.000,
                "tps_prev_dev": row.TpsPrevDev or 0.000
            })
        
        return operations


def get_fiche_encours_operateur(matricule, exclude_traitement_id=None):
    """
    Retourne un traitement en cours (DteFin IS NULL) pour cet opérateur, ou None.
    exclude_traitement_id : ID à exclure (fiche en cours de modification).
    """
    if not matricule:
        return None
    try:
        with get_db_cursor() as cursor:
            exclude_sql = " AND ID != ?" if exclude_traitement_id else ""
            params = [matricule]
            if exclude_traitement_id:
                params.append(exclude_traitement_id)
            cursor.execute("""
                SELECT ID, Numero_COMMANDES, Nom_GP_SERVICES, DteDeb
                FROM WEB_TRAITEMENTS
                WHERE Matricule_personel = ? AND DteFin IS NULL""" + exclude_sql,
                params)
            row = cursor.fetchone()
            if row:
                return {"id": row.ID, "numero": row.Numero_COMMANDES or "", "service": row.Nom_GP_SERVICES or "", "dte_deb": row.DteDeb}
            return None
    except Exception as e:
        print(f"[projet11] get_fiche_encours_operateur: {e}")
        return None


def get_fiche_encours_machine(postes_reel, exclude_traitement_id=None):
    """
    Retourne un traitement en cours (DteFin IS NULL) avec cette machine, ou None.
    exclude_traitement_id : ID à exclure.
    """
    if not postes_reel or not str(postes_reel).strip():
        return None
    try:
        with get_db_cursor() as cursor:
            exclude_sql = " AND ID != ?" if exclude_traitement_id else ""
            params = [postes_reel.strip()]
            if exclude_traitement_id:
                params.append(exclude_traitement_id)
            cursor.execute("""
                SELECT ID, Numero_COMMANDES, Nom_GP_SERVICES, DteDeb
                FROM WEB_TRAITEMENTS
                WHERE LTRIM(RTRIM(PostesReel)) = ? AND DteFin IS NULL""" + exclude_sql,
                params)
            row = cursor.fetchone()
            if row:
                return {"id": row.ID, "numero": row.Numero_COMMANDES or "", "service": row.Nom_GP_SERVICES or "", "dte_deb": row.DteDeb}
            return None
    except Exception as e:
        print(f"[projet11] get_fiche_encours_machine: {e}")
        return None


def get_traitement_by_fiche(id_fiche_travail):
    """
    Récupère le traitement existant pour une fiche de travail
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                ID,
                ID_FICHE_TRAVAIL
            FROM GP_TRAITEMENTS
            WHERE ID_FICHE_TRAVAIL = ?
        """, (id_fiche_travail,))
        
        row = cursor.fetchone()
        if row:
            return {
                "id": row.ID,
                "id_fiche_travail": row.ID_FICHE_TRAVAIL
            }
        return None


# ============================================================================
# FONCTIONS CRUD POUR WEB_TRAITEMENTS
# ============================================================================

def resolve_periode_filtre(periode='jour'):
    """
    Bornes de période pour la liste des traitements (filtre sur DteDeb).
    periodes : jour | semaine | mois | tous
    Retourne dict : periode, date_debut (date|None), date_fin (date|None), label
    """
    from datetime import date, timedelta

    periode = (periode or 'jour').strip().lower()
    if periode not in ('jour', 'semaine', 'mois', 'tous'):
        periode = 'jour'

    today = date.today()
    if periode == 'jour':
        return {
            'periode': periode,
            'date_debut': today,
            'date_fin': today,
            'label': "Aujourd'hui",
        }
    if periode == 'semaine':
        return {
            'periode': periode,
            'date_debut': today - timedelta(days=6),
            'date_fin': today,
            'label': '7 derniers jours',
        }
    if periode == 'mois':
        return {
            'periode': periode,
            'date_debut': today.replace(day=1),
            'date_fin': today,
            'label': 'Mois en cours',
        }
    return {
        'periode': 'tous',
        'date_debut': None,
        'date_fin': None,
        'label': 'Tous les traitements',
    }


def get_all_traitements(periode=None, date_debut=None, date_fin=None):
    """
    Récupère les traitements WEB_TRAITEMENTS.
    - periode : jour | semaine | mois | tous (filtre sur CAST(DteDeb AS DATE))
    - date_debut / date_fin : bornes explicites (prioritaires si fournies)
    Sans filtre (periode=None et dates None) : tous les traitements (compat API).
    """
    ensure_nom_fd_column()
    ensure_controle_valide_columns()

    if date_debut is None and date_fin is None and periode:
        bounds = resolve_periode_filtre(periode)
        date_debut = bounds['date_debut']
        date_fin = bounds['date_fin']

    with get_db_cursor() as cursor:
        cols_cloture = ', Cloture' if column_exists(cursor, 'WEB_TRAITEMENTS', 'Cloture') else ', CAST(0 AS TINYINT) AS Cloture'
        cols_desc = ', Description' if column_exists(cursor, 'WEB_TRAITEMENTS', 'Description') else ', CAST(NULL AS NVARCHAR(MAX)) AS Description'
        cols_nom_fd = ', NOM_FD' if column_exists(cursor, 'WEB_TRAITEMENTS', 'NOM_FD') else ", CAST(NULL AS NVARCHAR(100)) AS NOM_FD"
        has_cv = column_exists(cursor, 'WEB_TRAITEMENTS', 'ControleValide')
        cols_controle = (
            ', ControleValide, ControleValideDte, ControleValideMatricule'
            if has_cv
            else ', CAST(0 AS TINYINT) AS ControleValide, CAST(NULL AS DATETIME2) AS ControleValideDte, CAST(NULL AS INT) AS ControleValideMatricule'
        )

        where_parts = []
        params = []
        # Filtre période sur la date de début du traitement (métier)
        if date_debut is not None:
            where_parts.append("CAST(DteDeb AS DATE) >= ?")
            params.append(date_debut)
        if date_fin is not None:
            where_parts.append("CAST(DteDeb AS DATE) <= ?")
            params.append(date_fin)
        where_sql = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""

        cursor.execute(f"""
            SELECT 
                ID,
                ID_FICHE_TRAVAIL,
                ID_GP_TRAITEMENTS,
                DteDeb,
                DteFin,
                NbOp,
                NbPers,
                Numero_COMMANDES,
                Reference_COMMANDES,
                RaiSocTri_SOCIETES,
                Nom_GP_POSTES,
                Nom_GP_SERVICES,
                Nom_personel,
                Prenom_personel,
                PostesReel,
                PdtC,
                PdtNNC,
                PdtANC,
                TpsPrevDev_GP_FICHTRA_INT,
                TpsReel,
                DateCreation,
                DateModification
                {cols_cloture}
                {cols_desc}
                {cols_nom_fd}
                {cols_controle}
            FROM WEB_TRAITEMENTS
            {where_sql}
            ORDER BY DateCreation DESC
        """, tuple(params))
        
        traitements = []
        for row in cursor.fetchall():
            tps_prev = float(row.TpsPrevDev_GP_FICHTRA_INT) if row.TpsPrevDev_GP_FICHTRA_INT else None
            tps_reel = float(row.TpsReel) if row.TpsReel else None
            ecart = None
            if tps_prev is not None and tps_reel is not None:
                ecart = tps_reel - tps_prev
            
            traitements.append({
                "id": row.ID,
                "id_fiche_travail": row.ID_FICHE_TRAVAIL,
                "id_gp_traitements": row.ID_GP_TRAITEMENTS,
                "dte_deb": row.DteDeb.strftime('%Y-%m-%d %H:%M:%S') if row.DteDeb else None,
                "dte_fin": row.DteFin.strftime('%Y-%m-%d %H:%M:%S') if row.DteFin else None,
                "nb_op": _to_int(row.NbOp),
                "nb_pers": _to_int(row.NbPers),
                "numero_commande": row.Numero_COMMANDES or '',
                "reference": row.Reference_COMMANDES or '',
                "client": row.RaiSocTri_SOCIETES or '',
                "poste": row.Nom_GP_POSTES or '',
                "service": row.Nom_GP_SERVICES or '',
                "operateur": f"{row.Nom_personel or ''} {row.Prenom_personel or ''}".strip(),
                "postes_reel": row.PostesReel or '',
                "pdt_c": _to_int(row.PdtC),
                "pdt_nnc": _to_int(row.PdtNNC),
                "pdt_anc": _to_int(row.PdtANC),
                "tps_prev_dev": tps_prev,
                "tps_reel": tps_reel,
                "ecart_temps": ecart,
                "date_creation": row.DateCreation.strftime('%Y-%m-%d') if row.DateCreation else None,
                "date_modification": row.DateModification.strftime('%Y-%m-%d') if row.DateModification else None,
                "cloture": _to_int(getattr(row, 'Cloture', 0)),
                "description": getattr(row, 'Description', None) or '',
                "nom_fd": (getattr(row, 'NOM_FD', None) or '').strip(),
                "controle_valide": _to_int(getattr(row, "ControleValide", 0)),
                "controle_valide_dte": (
                    row.ControleValideDte.strftime("%Y-%m-%d %H:%M:%S")
                    if getattr(row, "ControleValideDte", None)
                    else None
                ),
                "controle_valide_matricule": getattr(
                    row, "ControleValideMatricule", None
                ),
            })
        
        return traitements


def get_pause_seconds_total_display_for_api(traitement_id):
    """Somme des secondes de pause (terminées + pause ouverte jusqu’à maintenant) pour une API."""
    ensure_web_traitements_pause_table()
    try:
        tid = int(traitement_id)
    except (TypeError, ValueError):
        return 0
    try:
        with get_db_cursor() as cursor:
            return get_pause_seconds_total_display(cursor, tid)
    except Exception as e:
        print(f"[projet11] get_pause_seconds_total_display_for_api: {e}")
        return 0


def get_traitement_by_id(traitement_id):
    """
    Récupère un traitement spécifique par son ID.
    Gère les deux noms de colonne pour le temps prévu (TpsPrevDev_GP_FICHTRA_INT ou TpsPrevDev_GP_FICHES_OPERATIONS).
    Retourne aussi Cloture pour afficher le bouton Déclôturer en fiche clôturée.
    """
    ensure_nom_fd_column()
    ensure_temps_ecoule_affichage_en_pause_column()
    ensure_chrono_affichage_snapshot_at_column()
    ensure_compteur_mode_column()
    ensure_compteur_lecture_column()
    ensure_controle_valide_columns()
    ensure_tps_pause_total_column()
    ensure_web_traitements_pause_table()
    with get_db_cursor() as cursor:
        has_cloture = column_exists(cursor, 'WEB_TRAITEMENTS', 'Cloture')
        has_description = column_exists(cursor, 'WEB_TRAITEMENTS', 'Description')
        has_nom_fd = column_exists(cursor, 'WEB_TRAITEMENTS', 'NOM_FD')
        has_chrono_en_pause = column_exists(cursor, 'WEB_TRAITEMENTS', 'TempsEcouleAffichageEnPause')
        has_chrono_snapshot_at = column_exists(cursor, 'WEB_TRAITEMENTS', 'ChronoAffichageSnapshotAt')
        has_compteur_mode = column_exists(cursor, 'WEB_TRAITEMENTS', 'CompteurMode')
        has_compteur_lecture = column_exists(cursor, 'WEB_TRAITEMENTS', 'CompteurLecture')
        has_controle = column_exists(cursor, 'WEB_TRAITEMENTS', 'ControleValide')
        has_tps_pause = column_exists(cursor, 'WEB_TRAITEMENTS', 'TpsPauseTotal')
        tps_pause_col = ', TpsPauseTotal' if has_tps_pause else ''
        chrono_en_pause_col = ', TempsEcouleAffichageEnPause' if has_chrono_en_pause else ''
        chrono_snapshot_at_col = ', ChronoAffichageSnapshotAt' if has_chrono_snapshot_at else ''
        compteur_mode_col = ', CompteurMode' if has_compteur_mode else ''
        compteur_lecture_col = ', CompteurLecture' if has_compteur_lecture else ''
        cloture_col = ', Cloture' if has_cloture else ''
        desc_col = ', Description' if has_description else ''
        nom_fd_col = ', NOM_FD' if has_nom_fd else ''
        controle_col = (
            ', ControleValide, ControleValideDte, ControleValideMatricule'
            if has_controle
            else ''
        )
        # Essayer d'abord avec la colonne renommée TpsPrevDev_GP_FICHTRA_INT
        try:
            cursor.execute("""
                SELECT 
                    ID,
                    ID_FICHE_TRAVAIL,
                    ID_GP_TRAITEMENTS,
                    DteDeb,
                    DteFin,
                    NbOp,
                    NbPers,
                    Numero_COMMANDES,
                    Reference_COMMANDES,
                    QteComm_COMMANDES,
                    RaiSocTri_SOCIETES,
                    Matricule_personel,
                    Nom_personel,
                    Prenom_personel,
                    Nom_GP_SERVICES,
                    Nom_GP_POSTES,
                    OpPrevDev_GP_FICHES_OPERATIONS,
                    TpsPrevDev_GP_FICHTRA_INT,
                    PdtC,
                    PdtNNC,
                    PdtANC,
                    TpsReel,
                    PostesReel,
                    DateCreation,
                    DateModification,
                    TempsEcouleAffichageSec
                    """ + chrono_en_pause_col + chrono_snapshot_at_col + compteur_mode_col + compteur_lecture_col + cloture_col + desc_col + nom_fd_col + controle_col + tps_pause_col + """
                FROM WEB_TRAITEMENTS
                WHERE ID = ?
            """, (traitement_id,))
        except Exception as e_col:
            err_msg = str(e_col).lower()
            if 'tpsprevdev_gp_fichtra_int' in err_msg or 'invalid column' in err_msg or 'nom de colonne' in err_msg:
                # Fallback: ancienne colonne TpsPrevDev_GP_FICHES_OPERATIONS
                try:
                    cursor.execute("""
                        SELECT 
                            ID,
                            ID_FICHE_TRAVAIL,
                            ID_GP_TRAITEMENTS,
                            DteDeb,
                            DteFin,
                            NbOp,
                            NbPers,
                            Numero_COMMANDES,
                            Reference_COMMANDES,
                            QteComm_COMMANDES,
                            RaiSocTri_SOCIETES,
                            Matricule_personel,
                            Nom_personel,
                            Prenom_personel,
                            Nom_GP_SERVICES,
                            Nom_GP_POSTES,
                            OpPrevDev_GP_FICHES_OPERATIONS,
                            TpsPrevDev_GP_FICHES_OPERATIONS,
                            PdtC,
                            PdtNNC,
                            PdtANC,
                            TpsReel,
                            PostesReel,
                            DateCreation,
                            DateModification,
                            TempsEcouleAffichageSec
                            """ + chrono_en_pause_col + chrono_snapshot_at_col + compteur_mode_col + compteur_lecture_col + cloture_col + desc_col + nom_fd_col + controle_col + tps_pause_col + """
                        FROM WEB_TRAITEMENTS
                        WHERE ID = ?
                    """, (traitement_id,))
                except Exception:
                    raise e_col
            else:
                raise
        
        row = cursor.fetchone()
        if not row:
            return None

        pause_sec_total = get_pause_seconds_total_display(cursor, traitement_id)
        tps_pause_stored = None
        if has_tps_pause and getattr(row, "TpsPauseTotal", None) is not None:
            try:
                tps_pause_stored = float(row.TpsPauseTotal)
            except (TypeError, ValueError):
                tps_pause_stored = None
        
        # Temps prévu: colonne renommée ou ancienne
        tps_prev = None
        if hasattr(row, 'TpsPrevDev_GP_FICHTRA_INT') and row.TpsPrevDev_GP_FICHTRA_INT is not None:
            tps_prev = float(row.TpsPrevDev_GP_FICHTRA_INT)
        elif hasattr(row, 'TpsPrevDev_GP_FICHES_OPERATIONS') and row.TpsPrevDev_GP_FICHES_OPERATIONS is not None:
            tps_prev = float(row.TpsPrevDev_GP_FICHES_OPERATIONS)
        tps_reel = float(row.TpsReel) if row.TpsReel else None
        ecart = None
        if tps_prev is not None and tps_reel is not None:
            ecart = tps_reel - tps_prev
        
        # Convertir les dates en chaînes pour JSON
        dte_deb_str = None
        if row.DteDeb:
            if isinstance(row.DteDeb, str):
                dte_deb_str = row.DteDeb
            else:
                dte_deb_str = row.DteDeb.isoformat() if hasattr(row.DteDeb, 'isoformat') else str(row.DteDeb)
        
        dte_fin_str = None
        if row.DteFin:
            if isinstance(row.DteFin, str):
                dte_fin_str = row.DteFin
            else:
                dte_fin_str = row.DteFin.isoformat() if hasattr(row.DteFin, 'isoformat') else str(row.DteFin)
        
        date_creation_str = None
        if row.DateCreation:
            if isinstance(row.DateCreation, str):
                date_creation_str = row.DateCreation
            else:
                date_creation_str = row.DateCreation.isoformat() if hasattr(row.DateCreation, 'isoformat') else str(row.DateCreation)
        
        date_modification_str = None
        if row.DateModification:
            if isinstance(row.DateModification, str):
                date_modification_str = row.DateModification
            else:
                date_modification_str = row.DateModification.isoformat() if hasattr(row.DateModification, 'isoformat') else str(row.DateModification)

        chrono_snap_str = None
        snap_val = getattr(row, 'ChronoAffichageSnapshotAt', None)
        if snap_val is not None:
            if isinstance(snap_val, str):
                chrono_snap_str = snap_val
            elif hasattr(snap_val, 'strftime'):
                chrono_snap_str = snap_val.strftime('%Y-%m-%dT%H:%M:%S')
                if getattr(snap_val, 'microsecond', 0):
                    chrono_snap_str += '.{:03d}'.format(snap_val.microsecond // 1000)
                chrono_snap_str += 'Z'

        # Horodatage serveur (UTC) pour corriger un éventuel décalage d'horloge côté poste
        server_utc_now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S') + 'Z'

        return {
            "id": row.ID,
            "id_fiche_travail": row.ID_FICHE_TRAVAIL,
            "id_gp_traitements": row.ID_GP_TRAITEMENTS,
            "dte_deb": dte_deb_str,
            "dte_fin": dte_fin_str,
            "nb_op": _to_int(row.NbOp),
            "nb_pers": _to_int(row.NbPers),
            "numero_commandes": row.Numero_COMMANDES,
            "reference_commandes": row.Reference_COMMANDES,
            "qte_comm_commandes": row.QteComm_COMMANDES,
            "raisoctri_societes": row.RaiSocTri_SOCIETES,
            "matricule_personel": row.Matricule_personel,
            "nom_personel": row.Nom_personel,
            "prenom_personel": row.Prenom_personel,
            "nom_gp_services": row.Nom_GP_SERVICES,
            "nom_gp_postes": row.Nom_GP_POSTES,
            "opprevdev_gp_fiches_operations": row.OpPrevDev_GP_FICHES_OPERATIONS,
            "tpsprevdev_gp_fichtra_int": getattr(row, 'TpsPrevDev_GP_FICHTRA_INT', None) or getattr(row, 'TpsPrevDev_GP_FICHES_OPERATIONS', None),
            "tps_prev_dev": tps_prev,
            "tps_reel": tps_reel,
            "pdt_c": _to_int(row.PdtC),
            "pdt_nnc": _to_int(row.PdtNNC),
            "pdt_anc": _to_int(row.PdtANC),
            "ecart_temps": ecart,
            "postes_reel": row.PostesReel,
            "date_creation": date_creation_str,
            "date_modification": date_modification_str,
            "temps_ecoule_affichage_sec": getattr(row, 'TempsEcouleAffichageSec', None),
            "temps_ecoule_affichage_en_pause": getattr(row, 'TempsEcouleAffichageEnPause', None),
            "chrono_affichage_snapshot_at": chrono_snap_str,
            "server_utc_now": server_utc_now,
            "compteur_mode": _to_int(getattr(row, "CompteurMode", 0)) if has_compteur_mode else 0,
            "compteur_lecture": getattr(row, "CompteurLecture", None) if has_compteur_lecture else None,
            "cloture": _to_int(getattr(row, 'Cloture', 0)),
            "description": getattr(row, 'Description', None) or '',
            "nom_fd": (getattr(row, 'NOM_FD', None) or '').strip(),
            "controle_valide": _to_int(getattr(row, "ControleValide", 0)) if has_controle else 0,
            "controle_valide_dte": (
                row.ControleValideDte.strftime("%Y-%m-%d %H:%M:%S")
                if has_controle and getattr(row, "ControleValideDte", None)
                else None
            ),
            "controle_valide_matricule": (
                getattr(row, "ControleValideMatricule", None) if has_controle else None
            ),
            "total_pause_sec": pause_sec_total,
            "tps_pause_total": tps_pause_stored,
        }


def create_traitement(data):
    """
    Crée un nouveau traitement dans WEB_TRAITEMENTS
    
    Args:
        data (dict): Dictionnaire contenant toutes les données du traitement
            - id_fiche_travail (int, requis): ID de la fiche de travail
            - dte_deb (datetime): Date de début
            - dte_fin (datetime): Date de fin
            - nb_op (int): Nombre d'opérations
            - nb_pers (int): Nombre de personnes
            - matricule_personel (int): Matricule de l'opérateur
            
    Returns:
        int: ID du traitement créé, ou None en cas d'erreur
    """
    ensure_nom_fd_column()
    ensure_compteur_mode_column()
    ensure_compteur_lecture_column()
    try:
        print(f"[DEBUG] Début create_traitement avec data: {data}")
        with get_db_cursor() as cursor:
            # Récupérer toutes les données des tables sources
            id_fiche_travail = data.get('id_fiche_travail')
            print(f"[DEBUG] id_fiche_travail: {id_fiche_travail}")

            # Quantités produites (conformes et non conformes)
            def _safe_int(value):
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return 0

            pdt_c = _safe_int(data.get('pdt_c'))
            pdt_nnc = _safe_int(data.get('pdt_nnc'))
            pdt_anc = _safe_int(data.get('pdt_anc'))
            nb_op = pdt_c + pdt_nnc + pdt_anc
            data['nb_op'] = nb_op
            nom_fd = (data.get('nom_fd') or '').strip() or None
            
            # SERVICE NON PRÉVU: Si id_fiche_travail est 0 ou NULL, c'est un service non prévu
            # On doit récupérer les informations directement depuis les données fournies
            if not id_fiche_travail or id_fiche_travail == 0:
                print("[INFO] Service non prévu détecté - Traitement sans fiche de travail")
                # Pour un service non prévu, on récupère les infos depuis le formulaire
                numero_commande = data.get('numero_commande')
                nom_service = data.get('nom_service')
                nom_poste_reel = data.get('postes_reel')
                
                if not numero_commande or not nom_service:
                    print("Erreur: Données insuffisantes pour service non prévu")
                    return None
                
                # Récupérer les infos de la commande seulement
                cursor.execute("""
                    SELECT 
                        C.ID,
                        C.Numero,
                        C.Reference,
                        C.QteComm,
                        C.ID_SOCIETE,
                        S.RaiSocTri
                    FROM COMMANDES C
                    LEFT JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
                    WHERE LTRIM(RTRIM(C.Numero)) = ?
                """, (numero_commande.strip(),))
                
                commande_data = cursor.fetchone()
                if not commande_data:
                    print(f"Erreur: Commande {numero_commande} non trouvée")
                    return None
                
                # Construire un objet fiche_data virtuel pour le service non prévu
                # Utiliser une classe simple pour simuler le résultat SQL
                class FicheDataVirtuelle:
                    def __init__(self, commande_data, nom_poste_reel, nom_service):
                        # Simuler les colonnes d'un résultat SQL par index
                        self.data = [
                            None,                    # [0] FT.ID (NULL pour service non prévu)
                            commande_data[0],        # [1] ID_COMMANDE
                            None,                    # [2] ID_POSTE (NULL)
                            commande_data[0],        # [3] C.ID
                            commande_data[4],        # [4] C.ID_SOCIETE
                            commande_data[1],        # [5] C.Numero
                            commande_data[2],        # [6] C.Reference
                            commande_data[3],        # [7] C.QteComm
                            commande_data[4],        # [8] S.ID
                            commande_data[5],        # [9] S.RaiSocTri
                            None,                    # [10] P.ID (NULL)
                            nom_poste_reel or '',    # [11] P.Nom (machine réelle)
                            None,                    # [12] P.ID_SERVICE (NULL)
                            None,                    # [13] SRV.ID (NULL)
                            nom_service or ''        # [14] SRV.Nom
                        ]
                    
                    def __getitem__(self, index):
                        return self.data[index]
                
                fiche_data = FicheDataVirtuelle(commande_data, nom_poste_reel, nom_service)
                operation_data = None  # Pas d'opérations pour service non prévu
                tps_prev_dev = None  # Pas de temps prévu pour service non prévu
                traitement_data = None  # Pas de traitement pour service non prévu
                
            else:
                # SERVICE PRÉVU: Récupérer les informations complètes depuis les tables sources
                cursor.execute("""
                    SELECT 
                        FT.ID,
                        FT.ID_COMMANDE,
                        FT.ID_POSTE,
                        
                        -- COMMANDES
                        C.ID,
                        C.ID_SOCIETE,
                        C.Numero,
                        C.Reference,
                        C.QteComm,
                        
                        -- SOCIETES
                        S.ID,
                        S.RaiSocTri,
                        
                        -- GP_POSTES
                        P.ID,
                        P.Nom,
                        P.ID_SERVICE,
                        
                        -- GP_SERVICES
                        SRV.ID,
                        SRV.Nom
                        
                    FROM GP_FICHES_TRAVAIL FT
                    LEFT JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
                    LEFT JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
                    LEFT JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
                    LEFT JOIN GP_SERVICES SRV ON SRV.ID = P.ID_SERVICE
                    WHERE FT.ID = ?
                """, (id_fiche_travail,))
                
                fiche_data = cursor.fetchone()
                if not fiche_data:
                    print(f"Erreur: Fiche de travail {id_fiche_travail} non trouvée")
                    return None
                
                # Récupérer les opérations (OpPrevDev depuis GP_FICHES_OPERATIONS)
                cursor.execute("""
                    SELECT TOP 1
                        ID_OPERATION,
                        OpPrevDev
                    FROM GP_FICHES_OPERATIONS
                    WHERE ID_FICHE_TRAVAIL = ?
                    ORDER BY ID_OPERATION
                """, (id_fiche_travail,))
                
                operation_data = cursor.fetchone()
                
                # Récupérer TpsPrevDev depuis GP_FICHTRA_INT
                cursor.execute("""
                    SELECT TpsPrevDev
                    FROM GP_FICHTRA_INT
                    WHERE ID_FICHTRA = ?
                """, (id_fiche_travail,))
                
                fichtra_data = cursor.fetchone()
                tps_prev_dev = fichtra_data.TpsPrevDev if fichtra_data and fichtra_data.TpsPrevDev else None
                
                # Récupérer le traitement
                cursor.execute("""
                    SELECT ID
                    FROM GP_TRAITEMENTS
                    WHERE ID_FICHE_TRAVAIL = ?
                """, (id_fiche_travail,))
                
                traitement_data = cursor.fetchone()
            
            # Récupérer les infos de l'opérateur
            matricule = data.get('matricule_personel')
            print(f"[DEBUG] matricule reçu: {matricule}, type: {type(matricule)}")
            nom_personel = None
            prenom_personel = None
            
            if matricule:
                cursor.execute("""
                    SELECT Nom, Prenom
                    FROM personel
                    WHERE Matricule = ?
                """, (matricule,))
                
                pers = cursor.fetchone()
                if pers:
                    nom_personel = pers.Nom
                    prenom_personel = pers.Prenom
                    print(f"[DEBUG] Opérateur trouvé: {nom_personel} {prenom_personel}")
                else:
                    print(f"[DEBUG] ATTENTION: Aucun opérateur trouvé pour matricule {matricule}")
            
            # Quantités produites (Nouvelle fiche de production) → colonnes PdtC, PdtNNC, PdtANC
            def _safe_int(value):
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return 0

            pdt_c = _safe_int(data.get('pdt_c'))
            pdt_nnc = _safe_int(data.get('pdt_nnc'))
            pdt_anc = _safe_int(data.get('pdt_anc'))
            nb_op = pdt_c + pdt_nnc + pdt_anc

            # Calculer TpsReel si DteDeb et DteFin sont présents
            tps_reel = None
            dte_deb = data.get('dte_deb')
            dte_fin = data.get('dte_fin')
            
            print(f"[DEBUG] dte_deb type: {type(dte_deb)}, value: {dte_deb}")
            print(f"[DEBUG] dte_fin type: {type(dte_fin)}, value: {dte_fin}")
            
            if dte_deb and dte_fin:
                try:
                    # Calculer la durée en heures
                    duree_secondes = (dte_fin - dte_deb).total_seconds()
                    tps_reel = duree_secondes / 3600.0  # Convertir en heures
                    print(f"[DEBUG] TpsReel calculé à la création: {tps_reel:.3f}h")
                except Exception as e:
                    print(f"[ERREUR] Calcul TpsReel échoué: {e}")
                    tps_reel = None
            
            # Insérer dans WEB_TRAITEMENTS (données métier + ID de traçabilité)
            print(f"[DEBUG] Données à insérer:")
            print(f"  - id_fiche_travail: {id_fiche_travail}")
            print(f"  - numero_commande: {fiche_data[5]}")
            print(f"  - nom_service: {fiche_data[14]}")
            print(f"  - nom_poste: {fiche_data[11]}")
            print(f"  - postes_reel: {data.get('postes_reel')}")
            
            try:
                # Pour les services non prévus, utiliser NULL au lieu de 0 pour ID_FICHE_TRAVAIL
                id_fiche_insert = None if (not id_fiche_travail or id_fiche_travail == 0) else id_fiche_travail
                
                cloture_val = 1 if data.get('cloture') in (1, '1', True) else 0
                has_cloture = column_exists(cursor, 'WEB_TRAITEMENTS', 'Cloture')
                has_description = column_exists(cursor, 'WEB_TRAITEMENTS', 'Description')
                has_nom_fd = column_exists(cursor, 'WEB_TRAITEMENTS', 'NOM_FD')
                has_compteur_mode = column_exists(cursor, 'WEB_TRAITEMENTS', 'CompteurMode')
                has_compteur_lecture = column_exists(cursor, 'WEB_TRAITEMENTS', 'CompteurLecture')

                compteur_mode_col = ', CompteurMode' if has_compteur_mode else ''
                compteur_mode_ph = ', ?' if has_compteur_mode else ''
                compteur_mode_params = (
                    (1 if data.get('compteur_mode') in (1, '1', True, 'cumulatif') else 0,)
                    if has_compteur_mode
                    else ()
                )

                compteur_lecture_col = ', CompteurLecture' if has_compteur_lecture else ''
                compteur_lecture_ph = ', ?' if has_compteur_lecture else ''
                cl = data.get('compteur_lecture')
                try:
                    cl_val = int(cl) if cl is not None and str(cl).strip() != '' else None
                except (TypeError, ValueError):
                    cl_val = None
                compteur_lecture_params = (cl_val,) if has_compteur_lecture else ()

                cloture_col = ', Cloture' if has_cloture else ''
                cloture_ph = ', ?' if has_cloture else ''
                cloture_params = (cloture_val,) if has_cloture else ()
                desc_col = ', Description' if has_description else ''
                desc_ph = ', ?' if has_description else ''
                desc_params = (data.get('description') or None,) if has_description else ()
                nom_fd_col = ', NOM_FD' if has_nom_fd else ''
                nom_fd_ph = ', ?' if has_nom_fd else ''
                nom_fd_params = (nom_fd,) if has_nom_fd else ()
                cursor.execute(f"""
                    INSERT INTO WEB_TRAITEMENTS (
                        ID_FICHE_TRAVAIL,
                        ID_GP_TRAITEMENTS,
                        DteDeb,
                        DteFin,
                        NbOp,
                        NbPers,
                        Numero_COMMANDES,
                        Reference_COMMANDES,
                        QteComm_COMMANDES,
                        RaiSocTri_SOCIETES,
                        Matricule_personel,
                        Nom_personel,
                        Prenom_personel,
                        Nom_GP_SERVICES,
                        Nom_GP_POSTES,
                        OpPrevDev_GP_FICHES_OPERATIONS,
                        TpsPrevDev_GP_FICHTRA_INT,
                        PostesReel,
                        PdtC,
                        PdtNNC,
                        PdtANC,
                        TpsReel{compteur_mode_col}{compteur_lecture_col}{cloture_col}{desc_col}{nom_fd_col}
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?{compteur_mode_ph}{compteur_lecture_ph}{cloture_ph}{desc_ph}{nom_fd_ph})
                """, (
                    id_fiche_insert,  # NULL pour service non prévu, ID valide sinon
                    traitement_data[0] if traitement_data else None,  # ID_GP_TRAITEMENTS (traçabilité)
                    data.get('dte_deb'),
                    data.get('dte_fin'),
                    nb_op,
                    data.get('nb_pers'),
                    # Données COMMANDES (sans ID)
                    fiche_data[5],  # Numero_COMMANDES
                    fiche_data[6],  # Reference_COMMANDES
                    fiche_data[7],  # QteComm_COMMANDES
                    # Données SOCIETES (sans ID)
                    fiche_data[9],  # RaiSocTri_SOCIETES
                    # Données personel
                    matricule,
                    nom_personel,
                    prenom_personel,
                    # Données GP_SERVICES (sans ID)
                    fiche_data[14],  # Nom_GP_SERVICES
                    # Données GP_POSTES (sans ID)
                    fiche_data[11],  # Nom_GP_POSTES
                    # Données GP_FICHES_OPERATIONS (sans ID_OPERATION)
                    operation_data[1] if operation_data else None,  # OpPrevDev
                    # Données GP_FICHTRA_INT
                    tps_prev_dev,  # TpsPrevDev depuis GP_FICHTRA_INT
                    # Poste réellement utilisé
                    data.get('postes_reel'),
                    pdt_c,
                    pdt_nnc,
                    pdt_anc,
                    # Temps réel calculé
                    tps_reel
                ) + compteur_mode_params + compteur_lecture_params + cloture_params + desc_params + nom_fd_params)
                
                print("[DEBUG] INSERT réussi")
                if id_fiche_insert:
                    sync_codindav_for_fiche(id_fiche_insert, cursor)
                if dte_fin and nom_fd and _is_typo_service(cursor, fiche_data[14]):
                    _apply_nom_fd_tirages_delta(cursor, nom_fd, nb_op)
                if nom_fd and data.get('dte_deb'):
                    from logic.projet24 import ensure_derniere_utilisation_columns, sync_forme_derniere_utilisation
                    ensure_derniere_utilisation_columns()
                    sync_forme_derniere_utilisation(cursor, nom_fd)
                cursor.connection.commit()
                print("[DEBUG] COMMIT réussi")
                
            except Exception as e:
                print(f"[ERREUR] INSERT ou COMMIT échoué: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # Récupérer l'ID inséré en cherchant le dernier enregistrement
            # (SCOPE_IDENTITY ne fonctionne pas avec les triggers actifs)
            # Utiliser une approche simplifiée : chercher le dernier ID par DateCreation
            print("[DEBUG] Recherche de l'ID inséré...")
            
            if id_fiche_travail and id_fiche_travail != 0:
                # Service prévu : recherche par fiche et opérateur
                cursor.execute("""
                    SELECT TOP 1 ID 
                    FROM WEB_TRAITEMENTS 
                    WHERE ID_FICHE_TRAVAIL = ? 
                    AND Matricule_personel = ?
                    AND DATEDIFF(SECOND, DteDeb, ?) BETWEEN -5 AND 5
                    ORDER BY DateCreation DESC
                """, (id_fiche_travail, matricule, data.get('dte_deb')))
            else:
                # Service non prévu : recherche simplifiée par le dernier créé
                # avec les mêmes caractéristiques de base
                cursor.execute("""
                    SELECT TOP 1 ID 
                    FROM WEB_TRAITEMENTS 
                    WHERE ID_FICHE_TRAVAIL IS NULL
                    AND Matricule_personel = ?
                    AND LTRIM(RTRIM(Numero_COMMANDES)) = ?
                    AND Nom_GP_SERVICES = ?
                    AND DATEDIFF(SECOND, DateCreation, GETDATE()) < 5
                    ORDER BY DateCreation DESC, ID DESC
                """, (matricule, data.get('numero_commande').strip() if data.get('numero_commande') else '', data.get('nom_service')))
            
            result = cursor.fetchone()
            print(f"[DEBUG] Résultat SELECT ID: {result}")
            
            if result and result[0]:
                traitement_id = int(result[0])
                print(f"[SUCCESS] Traitement {traitement_id} cree avec succes")
                return traitement_id
            else:
                print("[ERREUR] Impossible de recuperer l'ID du traitement insere")
                # Essayer une requête encore plus simple
                print("[DEBUG] Tentative de récupération alternative...")
                cursor.execute("""
                    SELECT TOP 1 ID, DateCreation, Numero_COMMANDES, Nom_GP_SERVICES
                    FROM WEB_TRAITEMENTS 
                    WHERE ID_FICHE_TRAVAIL IS NULL
                    AND Matricule_personel = ?
                    ORDER BY DateCreation DESC
                """, (matricule,))
                alt_result = cursor.fetchone()
                if alt_result:
                    print(f"[DEBUG] Dernier enregistrement trouve: ID={alt_result[0]}, Date={alt_result[1]}, Cmd={alt_result[2]}, Service={alt_result[3]}")
                    traitement_id = int(alt_result[0])
                    print(f"[SUCCESS] ID recupere via methode alternative: {traitement_id}")
                    return traitement_id
                else:
                    print("[ERREUR] Aucun enregistrement trouve meme avec requete simplifiee")
                    return None
            
    except Exception as e:
        print(f"Erreur lors de la création du traitement: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_traitement(traitement_id, data):
    """Met à jour un traitement existant.
    
    Args:
        traitement_id (int): ID du traitement à mettre à jour
        data (dict): Données à mettre à jour
        
    Returns:
        bool: True si succès, False sinon
    """
    ensure_nom_fd_column()
    ensure_compteur_mode_column()
    ensure_compteur_lecture_column()
    ensure_controle_valide_columns()
    try:
        with get_db_cursor() as cursor:
            from datetime import datetime

            if column_exists(cursor, "WEB_TRAITEMENTS", "ControleValide"):
                cursor.execute(
                    "SELECT ControleValide FROM WEB_TRAITEMENTS WHERE ID = ?",
                    (traitement_id,),
                )
                row_cv = cursor.fetchone()
                if row_cv and getattr(row_cv, "ControleValide", 0) in (1, True):
                    raise Exception(
                        "Traitement validé au contrôle : dévalider avant toute modification."
                    )

            def _safe_int(value):
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return 0

            # PdtC, PdtNNC, PdtANC : valeurs des champs de la fiche (si renseignés)
            pdt_c = _safe_int(data.get('pdt_c'))
            pdt_nnc = _safe_int(data.get('pdt_nnc'))
            pdt_anc = _safe_int(data.get('pdt_anc'))
            nom_fd_new = (data.get('nom_fd') or '').strip()

            def _parse_datetime_local(value):
                if not value:
                    return None
                if isinstance(value, datetime):
                    return value
                try:
                    date_str = str(value).replace('Z', '')
                    base = date_str.split('.')[0]
                    formats = [
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%dT%H:%M',
                        '%Y-%m-%d %H:%M'
                    ]
                    for fmt in formats:
                        try:
                            return datetime.strptime(base, fmt)
                        except ValueError:
                            continue
                    raise ValueError(f"Format de date non reconnu: {value}")
                except Exception as parse_error:
                    print(f"[WARN] Impossible de parser la date '{value}': {parse_error}")
                    return None

            dte_deb = _parse_datetime_local(data.get('dte_deb'))
            dte_fin = _parse_datetime_local(data.get('dte_fin'))

            nb_op = pdt_c + pdt_nnc + pdt_anc
            nb_pers = _safe_int(data.get('nb_pers'))

            if nb_op <= 0:
                print("[WARN] nb_op calculé <= 0, maintien de la valeur existante en base")
                nb_op = data.get('nb_op') or 0
            if nb_pers <= 0:
                nb_pers = 0

            # TpsReel net (heures) = (DteFin - DteDeb) - somme des pauses enregistrées (WEB_TRAITEMENTS_PAUSE).
            # TpsPauseTotal = somme des pauses en heures. Anciennes fiches : pas de lignes pause → net = brut.
            ensure_web_traitements_pause_table()
            ensure_tps_pause_total_column()
            tps_reel = None
            tps_pause_total_h = None
            if dte_deb and dte_fin:
                try:
                    finalize_open_pauses_traitement(cursor, traitement_id, dte_fin)
                    duree_secondes = int((dte_fin - dte_deb).total_seconds())
                    pause_sec = _sum_pause_seconds_closed(cursor, traitement_id)
                    net_sec = max(0, duree_secondes - pause_sec)
                    tps_reel = net_sec / 3600.0
                    tps_pause_total_h = pause_sec / 3600.0
                    print(
                        f"[DEBUG] TpsReel net={tps_reel:.3f}h (brut {duree_secondes}s, pauses {pause_sec}s)"
                    )
                except Exception as duree_error:
                    print(f"[WARN] Impossible de calculer TpsReel: {duree_error}")
                    tps_reel = None
                    tps_pause_total_h = None
            # Ne pas auto-remplir dte_fin quand le client envoie dte_fin null (fiche en cours)
            
            print(f"[DEBUG update_traitement] Mise à jour traitement {traitement_id}")
            print(f"[DEBUG update_traitement] Données: dte_deb={dte_deb}, dte_fin={dte_fin}, nb_op={nb_op}, pdt_c={pdt_c}, pdt_nnc={pdt_nnc}, pdt_anc={pdt_anc}")
            
            # Opérateur : si matricule_personel fourni, récupérer Nom/Prenom depuis personel
            matricule_op = data.get('matricule_personel')
            nom_op, prenom_op = '', ''
            if matricule_op is not None:
                try:
                    m = int(matricule_op)
                    cursor.execute("SELECT Nom, Prenom FROM personel WHERE Matricule = ?", (m,))
                    r = cursor.fetchone()
                    if r:
                        nom_op = (r.Nom or "").strip()
                        prenom_op = (r.Prenom or "").strip()
                except (TypeError, ValueError):
                    pass
            
            # Cloture : ne modifier QUE si explicitement fourni (bouton Clôturer envoie cloture=1).
            # Sinon (bouton Enregistrer en mode Modifier) : conserver la valeur existante.
            has_cloture = column_exists(cursor, 'WEB_TRAITEMENTS', 'Cloture')
            has_description = column_exists(cursor, 'WEB_TRAITEMENTS', 'Description')
            has_nom_fd = column_exists(cursor, 'WEB_TRAITEMENTS', 'NOM_FD')
            nom_fd_select = "ISNULL(NOM_FD, '') AS NOM_FD" if has_nom_fd else "CAST('' AS NVARCHAR(100)) AS NOM_FD"
            cursor.execute(f"""
                SELECT ISNULL(PdtC,0) AS PdtC, ISNULL(PdtNNC,0) AS PdtNNC, ISNULL(PdtANC,0) AS PdtANC,
                       Nom_GP_SERVICES, {nom_fd_select}, DteFin
                FROM WEB_TRAITEMENTS WHERE ID = ?
            """, (traitement_id,))
            old_row = cursor.fetchone()
            if not old_row:
                raise Exception(f"Le traitement {traitement_id} n'existe pas")
            old_total = _to_int(old_row.PdtC) + _to_int(old_row.PdtNNC) + _to_int(old_row.PdtANC)
            old_nom_fd = (getattr(old_row, 'NOM_FD', None) or '').strip()
            service_name = (old_row.Nom_GP_SERVICES or data.get('nom_service') or '').strip()
            update_cloture = has_cloture and ('cloture' in data)
            cloture_val = 1 if data.get('cloture') in (1, '1', True) else 0
            cloture_set = ', Cloture = ?' if update_cloture else ''
            cloture_param = (cloture_val,) if update_cloture else ()
            desc_set = ', Description = ?' if has_description else ''
            desc_param = (data.get('description') or None,) if has_description else ()
            nom_fd_set = ', NOM_FD = ?' if has_nom_fd else ''
            nom_fd_param = ((nom_fd_new or None),) if has_nom_fd else ()
            op_set = ', Matricule_personel = ?, Nom_personel = ?, Prenom_personel = ?' if matricule_op is not None else ''
            op_param = (matricule_op, nom_op, prenom_op) if matricule_op is not None else ()
            has_chrono_en_pause = column_exists(cursor, 'WEB_TRAITEMENTS', 'TempsEcouleAffichageEnPause')
            has_chrono_snapshot_at = column_exists(cursor, 'WEB_TRAITEMENTS', 'ChronoAffichageSnapshotAt')
            has_tps_pause = column_exists(cursor, 'WEB_TRAITEMENTS', 'TpsPauseTotal')
            has_compteur_mode = column_exists(cursor, 'WEB_TRAITEMENTS', 'CompteurMode')
            has_compteur_lecture = column_exists(cursor, 'WEB_TRAITEMENTS', 'CompteurLecture')
            tps_pause_fin_set = ', TpsPauseTotal = ?' if (has_tps_pause and dte_fin is not None) else ''
            chrono_clear_fin = ', TempsEcouleAffichageSec = NULL' + (
                ', TempsEcouleAffichageEnPause = NULL' if has_chrono_en_pause else ''
            ) + (', ChronoAffichageSnapshotAt = NULL' if has_chrono_snapshot_at else '')
            compteur_mode_set = ', CompteurMode = ?' if has_compteur_mode else ''
            compteur_lecture_set = ', CompteurLecture = ?' if has_compteur_lecture else ''
            sql_update = f"""
                UPDATE WEB_TRAITEMENTS
                SET 
                    DteDeb = ?,
                    DteFin = ?,
                    NbOp = ?,
                    PdtC = ?,
                    PdtNNC = ?,
                    PdtANC = ?,
                    NbPers = ?,
                    PostesReel = ?,
                    TpsReel = ?{op_set}{cloture_set}{desc_set}{nom_fd_set}{compteur_mode_set}{compteur_lecture_set},
                    DateModification = GETDATE()
                WHERE ID = ?
            """
            cmode = 1 if data.get('compteur_mode') in (1, '1', True, 'cumulatif') else 0
            clec = data.get('compteur_lecture')
            try:
                clec_val = int(clec) if clec is not None and str(clec).strip() != '' else None
            except (TypeError, ValueError):
                clec_val = None
            params = (
                dte_deb,
                dte_fin,
                nb_op,
                pdt_c,
                pdt_nnc,
                pdt_anc,
                nb_pers,
                data.get('postes_reel'),
                tps_reel
            ) + op_param + cloture_param + desc_param + nom_fd_param + (
                (cmode,) if has_compteur_mode else ()
            ) + (
                (clec_val,) if has_compteur_lecture else ()
            ) + (traitement_id,)
            try:
                if dte_fin is not None:
                    sql_fin = f"""
                        UPDATE WEB_TRAITEMENTS
                        SET DteDeb = ?, DteFin = ?, NbOp = ?, PdtC = ?, PdtNNC = ?, PdtANC = ?,
                            NbPers = ?, PostesReel = ?, TpsReel = ?{tps_pause_fin_set}{op_set}{cloture_set}{desc_set}{nom_fd_set}{compteur_mode_set}{compteur_lecture_set}{chrono_clear_fin},
                            DateModification = GETDATE()
                        WHERE ID = ?
                    """
                    params_fin = (
                        dte_deb,
                        dte_fin,
                        nb_op,
                        pdt_c,
                        pdt_nnc,
                        pdt_anc,
                        nb_pers,
                        data.get('postes_reel'),
                        tps_reel,
                    )
                    if has_tps_pause and dte_fin is not None:
                        params_fin += (tps_pause_total_h,)
                    params_fin += op_param + cloture_param + desc_param + nom_fd_param
                    if has_compteur_mode:
                        params_fin += (cmode,)
                    if has_compteur_lecture:
                        params_fin += (clec_val,)
                    params_fin += (traitement_id,)
                    cursor.execute(sql_fin, params_fin)
                else:
                    cursor.execute(sql_update, params)
            except Exception:
                cursor.execute(sql_update, params)
            
            rows_affected = cursor.rowcount
            print(f"[DEBUG update_traitement] UPDATE exécuté, lignes affectées: {rows_affected}")
            
            cursor.execute("SELECT ID_FICHE_TRAVAIL FROM WEB_TRAITEMENTS WHERE ID = ?", (traitement_id,))
            row_fiche = cursor.fetchone()
            if row_fiche and row_fiche.ID_FICHE_TRAVAIL:
                sync_codindav_for_fiche(row_fiche.ID_FICHE_TRAVAIL, cursor)
            if dte_fin and _is_typo_service(cursor, service_name):
                if old_nom_fd:
                    _apply_nom_fd_tirages_delta(cursor, old_nom_fd, -old_total)
                if nom_fd_new:
                    _apply_nom_fd_tirages_delta(cursor, nom_fd_new, nb_op)
            
            from logic.projet24 import ensure_derniere_utilisation_columns, sync_formes_derniere_utilisation_for_noms
            ensure_derniere_utilisation_columns()
            cursor.execute(
                "SELECT LTRIM(RTRIM(ISNULL(NOM_FD, ''))) AS NOM_FD FROM WEB_TRAITEMENTS WHERE ID = ?",
                (traitement_id,),
            )
            row_nd = cursor.fetchone()
            current_nom_fd = (getattr(row_nd, 'NOM_FD', None) or '').strip() if row_nd else ''
            sync_formes_derniere_utilisation_for_noms(cursor, old_nom_fd, current_nom_fd)
            
            if rows_affected == 0:
                # Vérifier si le traitement existe
                cursor.execute("SELECT ID FROM WEB_TRAITEMENTS WHERE ID = ?", (traitement_id,))
                exists = cursor.fetchone()
                if not exists:
                    print(f"[ERREUR update_traitement] Le traitement {traitement_id} n'existe pas")
                    raise Exception(f"Le traitement {traitement_id} n'existe pas")
                else:
                    print(f"[WARN update_traitement] Aucune ligne mise à jour pour traitement {traitement_id} - les données sont peut-être identiques")
            
            cursor.connection.commit()
            print(f"[OK] Traitement {traitement_id} mis à jour avec succès")
            return True
            
    except pyodbc.OperationalError as e:
        error_msg = str(e)
        print(f"[ERREUR update_traitement] Erreur de connexion DB: {error_msg}")
        from db import DB_CONFIG
        print(f"[ERREUR update_traitement] Serveur configuré: {DB_CONFIG.get('SERVER')}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Erreur de connexion à la base de données lors de la mise à jour: {error_msg}")
    except pyodbc.Error as e:
        error_msg = str(e)
        print(f"[ERREUR update_traitement] Erreur SQL: {error_msg}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Erreur SQL lors de la mise à jour: {error_msg}")
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"[ERREUR update_traitement] {error_type}: {error_msg}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Erreur lors de la mise à jour du traitement: {error_msg}")


def update_chrono_affichage(traitement_id, temps_ecoule_sec, en_pause=None):
    """
    Met à jour le temps affiché du chronomètre pour réouverture (Reprise / fermeture X).
    - en_pause True (défaut si omis) : affichage gelé comme en pause (comportement historique).
    - en_pause False : temps cumulé + ChronoAffichageSnapshotAt = GETUTCDATE() pour prolonger le chrono
      à la réouverture comme si la fiche n'avait pas été fermée.
    """
    ensure_temps_ecoule_affichage_en_pause_column()
    ensure_chrono_affichage_snapshot_at_column()
    if is_traitement_controle_valide(traitement_id):
        print("[projet11] update_chrono_affichage refusé : traitement validé au contrôle.")
        return False
    sec = max(0, int(temps_ecoule_sec))
    if en_pause is None:
        pause_val = 1
    else:
        pause_val = 1 if en_pause in (True, 1, '1', 'true', 'True') else 0
    try:
        with get_db_cursor() as cursor:
            has_pause_col = column_exists(cursor, 'WEB_TRAITEMENTS', 'TempsEcouleAffichageEnPause')
            has_snap_col = column_exists(cursor, 'WEB_TRAITEMENTS', 'ChronoAffichageSnapshotAt')
            if has_pause_col and has_snap_col:
                cursor.execute("""
                    UPDATE WEB_TRAITEMENTS
                    SET TempsEcouleAffichageSec = ?,
                        TempsEcouleAffichageEnPause = ?,
                        ChronoAffichageSnapshotAt = CASE WHEN ? = 0 THEN GETUTCDATE() ELSE NULL END,
                        DateModification = GETDATE()
                    WHERE ID = ? AND DteFin IS NULL
                """, (sec, pause_val, pause_val, traitement_id))
            elif has_pause_col:
                cursor.execute("""
                    UPDATE WEB_TRAITEMENTS
                    SET TempsEcouleAffichageSec = ?, TempsEcouleAffichageEnPause = ?, DateModification = GETDATE()
                    WHERE ID = ? AND DteFin IS NULL
                """, (sec, pause_val, traitement_id))
            else:
                cursor.execute("""
                    UPDATE WEB_TRAITEMENTS
                    SET TempsEcouleAffichageSec = ?, DateModification = GETDATE()
                    WHERE ID = ? AND DteFin IS NULL
                """, (sec, traitement_id))
            cursor.connection.commit()
            return True
    except Exception as e:
        if 'TempsEcouleAffichageSec' in str(e) or 'invalid column' in str(e).lower():
            return True
        print(f"Erreur update_chrono_affichage: {e}")
        return False


def update_operateur_traitement(traitement_id, matricule_personel):
    """
    Met à jour uniquement l'opérateur (Matricule_personel, Nom_personel, Prenom_personel)
    d'un traitement. Récupère Nom et Prenom depuis la table personel.
    """
    if is_traitement_controle_valide(traitement_id):
        return False
    if matricule_personel is None:
        return False
    try:
        matricule = int(matricule_personel)
    except (TypeError, ValueError):
        return False
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT Nom, Prenom FROM personel WHERE Matricule = ?",
                (matricule,)
            )
            row = cursor.fetchone()
            nom = (row.Nom or "").strip() if row else ""
            prenom = (row.Prenom or "").strip() if row else ""
            cursor.execute("""
                UPDATE WEB_TRAITEMENTS
                SET Matricule_personel = ?, Nom_personel = ?, Prenom_personel = ?, DateModification = GETDATE()
                WHERE ID = ?
            """, (matricule, nom, prenom, traitement_id))
            cursor.connection.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur update_operateur_traitement: {e}")
        return False


def update_cloture_traitement(traitement_id, cloture_val):
    """Met à jour uniquement la colonne Cloture (0 ou 1) d'un traitement."""
    if is_traitement_controle_valide(traitement_id):
        return False
    try:
        cloture = 1 if cloture_val in (1, '1', True) else 0
        with get_db_cursor() as cursor:
            if not column_exists(cursor, 'WEB_TRAITEMENTS', 'Cloture'):
                return False
            cursor.execute("""
                UPDATE WEB_TRAITEMENTS
                SET Cloture = ?, DateModification = GETDATE()
                WHERE ID = ?
            """, (cloture, traitement_id))
            cursor.connection.commit()
            if cursor.rowcount > 0:
                cursor.execute("SELECT ID_FICHE_TRAVAIL FROM WEB_TRAITEMENTS WHERE ID = ?", (traitement_id,))
                row_fiche = cursor.fetchone()
                if row_fiche and row_fiche.ID_FICHE_TRAVAIL:
                    sync_codindav_for_fiche(row_fiche.ID_FICHE_TRAVAIL, cursor)
                    cursor.connection.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur update_cloture_traitement: {e}")
        return False


# ============================================================================
# VERROUILLAGE FICHE OUVERTE (éviter double ouverture)
# Libération : à la fermeture (Annuler/X/Clôturer/Enregistrer), bouton Débloquer, ou task 23h59.
# ============================================================================
OUVERTURE_TIMEOUT_SEC = 300

_ouverture_table_ensured = False


def ensure_ouverture_table(cursor):
    """
    Crée la table WEB_TRAITEMENTS_OUVERTURE si elle n'existe pas.
    Si elle existe avec une mauvaise structure (ex. PK sur SessionId), on la recrée :
    PRIMARY KEY sur TraitementId uniquement = une ligne par fiche ouverte.
    """
    global _ouverture_table_ensured
    if _ouverture_table_ensured:
        return
    try:
        cursor.execute("SELECT 1 FROM sys.tables WHERE name = 'WEB_TRAITEMENTS_OUVERTURE'")
        table_exists = cursor.fetchone()
        if table_exists:
            # Vérifier que la PK est bien (TraitementId) seul
            cursor.execute("""
                SELECT kcu.COLUMN_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                    ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME AND tc.TABLE_NAME = kcu.TABLE_NAME
                WHERE tc.TABLE_NAME = 'WEB_TRAITEMENTS_OUVERTURE' AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                ORDER BY kcu.ORDINAL_POSITION
            """)
            pk_cols = [row.COLUMN_NAME for row in cursor.fetchall()]
            if pk_cols != ['TraitementId']:
                cursor.execute("DROP TABLE dbo.WEB_TRAITEMENTS_OUVERTURE")
                cursor.connection.commit()
                table_exists = None
        if not table_exists:
            cursor.execute("""
                CREATE TABLE dbo.WEB_TRAITEMENTS_OUVERTURE (
                    TraitementId INT NOT NULL PRIMARY KEY,
                    SessionId NVARCHAR(255) NOT NULL,
                    DateOuverture DATETIME NOT NULL DEFAULT GETDATE()
                )
            """)
            cursor.connection.commit()
        _ouverture_table_ensured = True
    except Exception as e:
        print(f"[projet11] ensure_ouverture_table: {e}")


def acquire_traitement_lock(traitement_id, session_id):
    """
    Acquiert le verrou pour une fiche.
    Une fiche (ID) ne peut être ouverte qu'à un seul endroit à la fois (tout utilisateur, tout PC).
    Pas de suppression par timeout ici : libération par fermeture, Débloquer, ou task 23h59.
    """
    if not session_id:
        return (False, "session_id manquant")
    try:
        with get_db_cursor() as cursor:
            ensure_ouverture_table(cursor)
            # Tenter d'insérer : si la fiche est déjà prise par quelqu'un, on aura une erreur de clé dupliquée
            try:
                cursor.execute("""
                    INSERT INTO WEB_TRAITEMENTS_OUVERTURE (TraitementId, SessionId, DateOuverture)
                    VALUES (?, ?, GETDATE())
                """, (traitement_id, session_id))
                cursor.connection.commit()
                return (True, None)
            except Exception as insert_err:
                cursor.connection.rollback()
                err_str = str(insert_err).lower()
                is_duplicate = (
                    getattr(insert_err, 'args', None) and len(insert_err.args) >= 1 and str(insert_err.args[0]) == '23000'
                ) or 'unique' in err_str or 'duplicate' in err_str or 'primary key' in err_str or 'violation' in err_str
                if not is_duplicate:
                    raise insert_err
            # Une ligne existe déjà : vérifier si c'est la même session
            cursor.execute("""
                SELECT SessionId FROM WEB_TRAITEMENTS_OUVERTURE WHERE TraitementId = ?
            """, (traitement_id,))
            row = cursor.fetchone()
            if not row:
                # Race : la ligne a été supprimée entre-temps, réessayer l'insert
                try:
                    cursor.execute("""
                        INSERT INTO WEB_TRAITEMENTS_OUVERTURE (TraitementId, SessionId, DateOuverture)
                        VALUES (?, ?, GETDATE())
                    """, (traitement_id, session_id))
                    cursor.connection.commit()
                    return (True, None)
                except Exception:
                    cursor.connection.rollback()
                return (False, "Cette fiche est déjà ouverte ailleurs. Veuillez attendre qu'elle soit fermée.")
            if row.SessionId == session_id:
                cursor.execute("""
                    UPDATE WEB_TRAITEMENTS_OUVERTURE
                    SET DateOuverture = GETDATE()
                    WHERE TraitementId = ? AND SessionId = ?
                """, (traitement_id, session_id))
                cursor.connection.commit()
                return (True, None)
            return (False, "Cette fiche est déjà ouverte ailleurs. Veuillez attendre qu'elle soit fermée.")
    except Exception as e:
        print(f"Erreur acquire_traitement_lock: {e}")
        return (False, "Erreur technique lors de l'ouverture de la fiche.")


def release_traitement_lock(traitement_id, session_id):
    """Libère le verrou à la fermeture d'une fiche. Supprime la ligne même si session_id diffère (nettoyage)."""
    try:
        with get_db_cursor() as cursor:
            ensure_ouverture_table(cursor)
            cursor.execute("""
                DELETE FROM WEB_TRAITEMENTS_OUVERTURE
                WHERE TraitementId = ? AND SessionId = ?
            """, (traitement_id, session_id))
            n = cursor.rowcount
            if n == 0 and session_id:
                # Fallback : supprimer par TraitementId seul (cas où session_id ne matche pas)
                cursor.execute("DELETE FROM WEB_TRAITEMENTS_OUVERTURE WHERE TraitementId = ?", (traitement_id,))
            cursor.connection.commit()
    except Exception as e:
        print(f"Erreur release_traitement_lock: {e}")


def nettoyage_verrous_ouverture():
    """Vide la table WEB_TRAITEMENTS_OUVERTURE (appelé par la task 23h59)."""
    try:
        with get_db_cursor() as cursor:
            ensure_ouverture_table(cursor)
            cursor.execute("DELETE FROM WEB_TRAITEMENTS_OUVERTURE")
            cursor.connection.commit()
            return True
    except Exception as e:
        print(f"Erreur nettoyage_verrous_ouverture: {e}")
        return False


def forcer_liberation_traitement(traitement_id):
    """Supprime la ligne de cette fiche dans WEB_TRAITEMENTS_OUVERTURE (bouton Débloquer)."""
    try:
        with get_db_cursor() as cursor:
            ensure_ouverture_table(cursor)
            cursor.execute("DELETE FROM WEB_TRAITEMENTS_OUVERTURE WHERE TraitementId = ?", (traitement_id,))
            cursor.connection.commit()
            return True
    except Exception as e:
        print(f"Erreur forcer_liberation_traitement: {e}")
        return False


def get_ids_verrouilles_ouverture():
    """Retourne la liste des TraitementId présents dans WEB_TRAITEMENTS_OUVERTURE."""
    try:
        with get_db_cursor() as cursor:
            ensure_ouverture_table(cursor)
            cursor.execute("SELECT TraitementId FROM WEB_TRAITEMENTS_OUVERTURE")
            return [row.TraitementId for row in cursor.fetchall()]
    except Exception as e:
        print(f"Erreur get_ids_verrouilles_ouverture: {e}")
        return []


def delete_traitement(traitement_id):
    """
    Supprime un traitement et ses verrous d'ouverture.
    Utilisé par le bouton Annuler de la nouvelle fiche de production.
    
    Args:
        traitement_id (int): ID du traitement à supprimer
        
    Returns:
        bool: True si succès, False sinon
    """
    if is_traitement_controle_valide(traitement_id):
        print("[projet11] delete_traitement refusé : traitement validé au contrôle.")
        return False
    try:
        with get_db_cursor() as cursor:
            nom_fd_del = ''
            if column_exists(cursor, 'WEB_TRAITEMENTS', 'NOM_FD'):
                cursor.execute(
                    "SELECT LTRIM(RTRIM(ISNULL(NOM_FD, ''))) AS NOM_FD FROM WEB_TRAITEMENTS WHERE ID = ?",
                    (traitement_id,),
                )
                row_nom = cursor.fetchone()
                nom_fd_del = (getattr(row_nom, 'NOM_FD', None) or '').strip() if row_nom else ''
            cursor.execute("DELETE FROM WEB_TRAITEMENTS_OUVERTURE WHERE TraitementId = ?", (traitement_id,))
            cursor.execute("SELECT ID_FICHE_TRAVAIL FROM WEB_TRAITEMENTS WHERE ID = ?", (traitement_id,))
            row_fiche = cursor.fetchone()
            id_fiche = row_fiche.ID_FICHE_TRAVAIL if row_fiche and row_fiche.ID_FICHE_TRAVAIL else None
            cursor.execute("DELETE FROM WEB_TRAITEMENTS WHERE ID = ?", (traitement_id,))
            if id_fiche:
                sync_codindav_for_fiche(id_fiche, cursor)
            if nom_fd_del:
                from logic.projet24 import ensure_derniere_utilisation_columns, sync_forme_derniere_utilisation
                ensure_derniere_utilisation_columns()
                sync_forme_derniere_utilisation(cursor, nom_fd_del)
            cursor.connection.commit()
            print(f"[OK] Traitement {traitement_id} supprimé avec succès")
            return True
            
    except Exception as e:
        print(f"Erreur lors de la suppression du traitement: {e}")
        return False


# ============================================================================
# FONCTIONS DE STATISTIQUES
# ============================================================================

def _stats_periode_sql(date_debut=None, date_fin=None, column="DteDeb"):
    """
    Clause SQL + paramètres pour filtrer WEB_TRAITEMENTS sur une période.
    Par défaut : date de début du traitement (DteDeb).
    """
    parts = []
    params = []
    if date_debut:
        parts.append(f" AND CAST({column} AS DATE) >= ?")
        params.append(date_debut)
    if date_fin:
        parts.append(f" AND CAST({column} AS DATE) <= ?")
        params.append(date_fin)
    return "".join(parts), params


def get_statistiques_traitements(date_debut=None, date_fin=None):
    """
    Récupère les statistiques globales des traitements (période optionnelle sur DteDeb).
    """
    periode_sql, periode_params = _stats_periode_sql(date_debut, date_fin)
    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT 
                COUNT(*) as total_traitements,
                SUM(NbOp) as total_operations,
                AVG(CAST(NbOp AS FLOAT)) as moyenne_operations,
                SUM(NbPers) as total_personnes,
                AVG(CAST(NbPers AS FLOAT)) as moyenne_personnes,
                COUNT(CASE WHEN DteFin IS NOT NULL THEN 1 END) as traitements_termines,
                COUNT(CASE WHEN DteFin IS NULL THEN 1 END) as traitements_en_cours
            FROM WEB_TRAITEMENTS
            WHERE 1=1
            {periode_sql}
            """,
            tuple(periode_params),
        )
        
        row = cursor.fetchone()
        if row:
            return {
                "total_traitements": row[0] or 0,
                "total_operations": row[1] or 0,
                "moyenne_operations": round(row[2] or 0, 3),
                "total_personnes": row[3] or 0,
                "moyenne_personnes": round(row[4] or 0, 3),
                "traitements_termines": row[5] or 0,
                "traitements_en_cours": row[6] or 0
            }
        
        return {}


def get_traitements_par_service(date_debut=None, date_fin=None):
    """
    Récupère les statistiques par service (période optionnelle sur DteDeb).
    """
    periode_sql, periode_params = _stats_periode_sql(date_debut, date_fin)
    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT 
                Nom_GP_SERVICES,
                COUNT(*) as nb_traitements,
                SUM(NbOp) as total_operations,
                AVG(CAST(NbOp AS FLOAT)) as moyenne_operations
            FROM WEB_TRAITEMENTS
            WHERE Nom_GP_SERVICES IS NOT NULL
            {periode_sql}
            GROUP BY Nom_GP_SERVICES
            ORDER BY nb_traitements DESC
            """,
            tuple(periode_params),
        )
        
        services = []
        for row in cursor.fetchall():
            services.append({
                "service": row[0],
                "nb_traitements": row[1] or 0,
                "total_operations": row[2] or 0,
                "moyenne_operations": round(row[3] or 0, 3)
            })
        
        return services


def get_traitements_par_machine(date_debut=None, date_fin=None):
    """
    Récupère les statistiques par machine (PostesReel), période optionnelle sur DteDeb.
    """
    periode_sql, periode_params = _stats_periode_sql(date_debut, date_fin)
    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT 
                ISNULL(NULLIF(LTRIM(RTRIM(PostesReel)), ''), 'Non renseigné') AS machine,
                COUNT(*) as nb_traitements,
                SUM(NbOp) as total_operations
            FROM WEB_TRAITEMENTS
            WHERE 1=1
            {periode_sql}
            GROUP BY ISNULL(NULLIF(LTRIM(RTRIM(PostesReel)), ''), 'Non renseigné')
            ORDER BY nb_traitements DESC
            """,
            tuple(periode_params),
        )
        machines = []
        for row in cursor.fetchall():
            machines.append({
                "machine": row.machine or "Non renseigné",
                "nb_traitements": row.nb_traitements or 0,
                "total_operations": row.total_operations or 0
            })
        return machines


def get_traitements_par_operateur(date_debut=None, date_fin=None):
    """
    Récupère les statistiques par opérateur (période optionnelle sur DteDeb).
    """
    periode_sql, periode_params = _stats_periode_sql(date_debut, date_fin)
    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT 
                Nom_personel,
                Prenom_personel,
                COUNT(*) as nb_traitements,
                SUM(NbOp) as total_operations
            FROM WEB_TRAITEMENTS
            WHERE Nom_personel IS NOT NULL
            {periode_sql}
            GROUP BY Nom_personel, Prenom_personel
            ORDER BY nb_traitements DESC
            """,
            tuple(periode_params),
        )
        
        operateurs = []
        for row in cursor.fetchall():
            operateurs.append({
                "operateur": f"{row[0] or ''} {row[1] or ''}".strip(),
                "nb_traitements": row[2] or 0,
                "total_operations": row[3] or 0
            })
        
        return operateurs


def get_cadence_par_machine(date_debut=None, date_fin=None):
    """
    Cadence par machine (PostesReel) pour une période donnée.
    Inclut le service (Nom_GP_SERVICES) pour permettre une comparaison homogène.
    Cadence = Somme(NbOp) / Somme(TpsReel) en opérations/heure.
    """
    sql = """
        SELECT 
            ISNULL(NULLIF(LTRIM(RTRIM(Nom_GP_SERVICES)), ''), 'Non renseigné') AS service,
            ISNULL(NULLIF(LTRIM(RTRIM(PostesReel)), ''), 'Non renseigné') AS machine,
            SUM(ISNULL(NbOp, 0)) AS total_operations,
            SUM(ISNULL(TpsReel, 0)) AS total_heures,
            COUNT(*) AS nb_traitements
        FROM WEB_TRAITEMENTS
        WHERE DteFin IS NOT NULL
          AND TpsReel IS NOT NULL
          AND TpsReel > 0
    """
    params = []
    if date_debut:
        sql += " AND CAST(DteFin AS DATE) >= ?"
        params.append(date_debut)
    if date_fin:
        sql += " AND CAST(DteFin AS DATE) <= ?"
        params.append(date_fin)
    sql += """
        GROUP BY ISNULL(NULLIF(LTRIM(RTRIM(Nom_GP_SERVICES)), ''), 'Non renseigné'),
                 ISNULL(NULLIF(LTRIM(RTRIM(PostesReel)), ''), 'Non renseigné')
        ORDER BY ISNULL(NULLIF(LTRIM(RTRIM(Nom_GP_SERVICES)), ''), 'Non renseigné'),
                 SUM(ISNULL(NbOp, 0)) / NULLIF(SUM(ISNULL(TpsReel, 0)), 0) DESC
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    result = []
    for row in rows:
        tps = float(row.total_heures) if row.total_heures else 0
        cadence = round((row.total_operations or 0) / tps, 2) if tps > 0 else 0
        result.append({
            "service": row.service or "Non renseigné",
            "machine": row.machine or "Non renseigné",
            "total_operations": row.total_operations or 0,
            "total_heures": round(tps, 2),
            "nb_traitements": row.nb_traitements or 0,
            "cadence": cadence
        })
    return result


def get_cadence_par_machine_par_service(date_debut=None, date_fin=None, top_n=10):
    """
    Cadence par machine regroupée par service.
    Pour chaque service, retourne les top_n machines avec la meilleure cadence.
    Permet de comparer les machines entre elles au sein d'un même service
    (ex: machines d'impression vs machines d'impression, machines de pliage vs machines de pliage).
    """
    flat = get_cadence_par_machine(date_debut=date_debut, date_fin=date_fin)
    by_service = {}
    for m in flat:
        svc = m["service"]
        if svc not in by_service:
            by_service[svc] = []
        by_service[svc].append(m)
    # Chaque service est déjà trié par cadence desc (dans get_cadence_par_machine on trie par service puis cadence)
    # mais le tri groupe par service d'abord - on a donc besoin de trier chaque liste par cadence
    result = []
    for service in sorted(by_service.keys()):
        machines = sorted(by_service[service], key=lambda x: x["cadence"], reverse=True)[:top_n]
        result.append({"service": service, "machines": machines})
    return result


def get_cadence_par_operateur(date_debut=None, date_fin=None):
    """
    Cadence par opérateur principal pour une période donnée.
    Cadence = Somme(NbOp) / Somme(TpsReel) en opérations/heure.
    Filtre sur DteFin (traitements terminés). TpsReel > 0 requis.
    """
    sql = """
        SELECT 
            ISNULL(LTRIM(RTRIM(Nom_personel)), '') AS nom,
            ISNULL(LTRIM(RTRIM(Prenom_personel)), '') AS prenom,
            SUM(ISNULL(NbOp, 0)) AS total_operations,
            SUM(ISNULL(TpsReel, 0)) AS total_heures,
            COUNT(*) AS nb_traitements
        FROM WEB_TRAITEMENTS
        WHERE DteFin IS NOT NULL
          AND TpsReel IS NOT NULL
          AND TpsReel > 0
    """
    params = []
    if date_debut:
        sql += " AND CAST(DteFin AS DATE) >= ?"
        params.append(date_debut)
    if date_fin:
        sql += " AND CAST(DteFin AS DATE) <= ?"
        params.append(date_fin)
    sql += """
        GROUP BY Nom_personel, Prenom_personel
        ORDER BY SUM(ISNULL(NbOp, 0)) / NULLIF(SUM(ISNULL(TpsReel, 0)), 0) DESC
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    result = []
    for row in rows:
        operateur = f"{row.nom or ''} {row.prenom or ''}".strip() or "Non renseigné"
        tps = float(row.total_heures) if row.total_heures else 0
        cadence = round((row.total_operations or 0) / tps, 2) if tps > 0 else 0
        result.append({
            "operateur": operateur,
            "total_operations": row.total_operations or 0,
            "total_heures": round(tps, 2),
            "nb_traitements": row.nb_traitements or 0,
            "cadence": cadence
        })
    return result


def get_cadence_pivot_machine_operateur(date_debut=None, date_fin=None):
    """
    Tableau croisé Machine x Opérateur.
    Cellule (machine, opérateur) :
    - cadence (op/h) = somme NbOp / somme TpsReel
    - nb_dossiers = COUNT(DISTINCT Numero_COMMANDES)
    - nb_operations = somme NbOp
    Filtre sur DteFin (traitements terminés). TpsReel > 0 requis.
    """
    sql = """
        SELECT
            ISNULL(NULLIF(LTRIM(RTRIM(Nom_GP_SERVICES)), ''), 'Non renseigné') AS service,
            ISNULL(NULLIF(LTRIM(RTRIM(PostesReel)), ''), 'Non renseigné') AS machine,
            ISNULL(LTRIM(RTRIM(Nom_personel)), '') AS nom,
            ISNULL(LTRIM(RTRIM(Prenom_personel)), '') AS prenom,
            COUNT(DISTINCT LTRIM(RTRIM(CAST(Numero_COMMANDES AS NVARCHAR(50))))) AS nb_dossiers,
            SUM(ISNULL(NbOp, 0)) AS total_operations,
            SUM(ISNULL(TpsReel, 0)) AS total_heures
        FROM WEB_TRAITEMENTS
        WHERE DteFin IS NOT NULL
          AND TpsReel IS NOT NULL
          AND TpsReel > 0
    """
    params = []
    if date_debut:
        sql += " AND CAST(DteFin AS DATE) >= ?"
        params.append(date_debut)
    if date_fin:
        sql += " AND CAST(DteFin AS DATE) <= ?"
        params.append(date_fin)
    sql += """
        GROUP BY
            ISNULL(NULLIF(LTRIM(RTRIM(Nom_GP_SERVICES)), ''), 'Non renseigné'),
            ISNULL(NULLIF(LTRIM(RTRIM(PostesReel)), ''), 'Non renseigné'),
            Nom_personel,
            Prenom_personel
        ORDER BY
            ISNULL(NULLIF(LTRIM(RTRIM(Nom_GP_SERVICES)), ''), 'Non renseigné'),
            ISNULL(NULLIF(LTRIM(RTRIM(PostesReel)), ''), 'Non renseigné'),
            Nom_personel,
            Prenom_personel
    """

    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    # Construire listes et matrice
    rows_keys = []  # (service, machine)
    ops_set = []
    cells = {}  # (service,machine) -> operateur -> stats

    def _op_label(nom, prenom):
        s = f"{nom or ''} {prenom or ''}".strip()
        return s or "Non renseigné"

    seen_sm = set()
    seen_o = set()
    for r in rows:
        svc = (r.service or "Non renseigné").strip() or "Non renseigné"
        m = (r.machine or "Non renseigné").strip() or "Non renseigné"
        sm = (svc, m)
        o = _op_label(r.nom, r.prenom)
        if sm not in seen_sm:
            seen_sm.add(sm)
            rows_keys.append(sm)
        if o not in seen_o:
            seen_o.add(o)
            ops_set.append(o)
        tps = float(r.total_heures) if r.total_heures else 0.0
        ops = int(r.total_operations or 0)
        cadence = round(ops / tps, 2) if tps > 0 else 0.0
        nb_dossiers = int(r.nb_dossiers or 0)
        if sm not in cells:
            cells[sm] = {}
        cells[sm][o] = {
            "cadence": cadence,
            "nb_dossiers": nb_dossiers,
            "nb_operations": ops,
            "total_heures": round(tps, 2),
        }

    # Tri stable pour affichage
    rows_sorted = sorted(rows_keys, key=lambda x: (x[0], x[1]))
    operateurs = sorted(ops_set)

    return {
        "rows": [{"service": s, "machine": m} for (s, m) in rows_sorted],
        "operateurs": operateurs,
        "cells": cells,
    }


def get_monthly_cadence_by_service_machine():
    """
    Retourne un dictionnaire des cadences mensuelles agrégées par (Service + Machine).
    Même grouping que get_cadence_par_machine() utilisé dans le Tableau de bord,
    pour que les valeurs de référence soient strictement identiques.

    Pour chaque (service, machine) et chaque mois calendaire (basé sur DteFin) :
        cadence = SUM(NbOp) / SUM(TpsReel)

    Format retourné :
        {
            ("OFFSET FEUILLES", "KBA105-6"): {
                (2026, 4): {"cadence": 2391.70, "ops": 690310, "heures": 288.63, "nb": 48},
                (2026, 3): {...},
                ...
            },
            ...
        }
    """
    sql = """
        SELECT 
            ISNULL(NULLIF(LTRIM(RTRIM(Nom_GP_SERVICES)), ''), 'Non renseigné') AS service,
            ISNULL(NULLIF(LTRIM(RTRIM(PostesReel)), ''), 'Non renseigné') AS machine,
            YEAR(DteFin) AS annee,
            MONTH(DteFin) AS mois,
            SUM(ISNULL(NbOp, 0)) AS total_operations,
            SUM(ISNULL(TpsReel, 0)) AS total_heures,
            COUNT(*) AS nb_traitements
        FROM WEB_TRAITEMENTS
        WHERE DteFin IS NOT NULL
          AND TpsReel IS NOT NULL
          AND TpsReel > 0
          AND PostesReel IS NOT NULL
          AND LTRIM(RTRIM(PostesReel)) <> ''
        GROUP BY ISNULL(NULLIF(LTRIM(RTRIM(Nom_GP_SERVICES)), ''), 'Non renseigné'),
                 ISNULL(NULLIF(LTRIM(RTRIM(PostesReel)), ''), 'Non renseigné'),
                 YEAR(DteFin), MONTH(DteFin)
    """
    result = {}
    try:
        with get_db_cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
        for row in rows:
            service = (row.service or 'Non renseigné').strip() or 'Non renseigné'
            machine = (row.machine or 'Non renseigné').strip() or 'Non renseigné'
            ops = float(row.total_operations or 0)
            heures = float(row.total_heures or 0)
            if heures <= 0 or ops <= 0:
                continue
            cadence = ops / heures
            if cadence <= 0:
                continue
            key_sm = (service, machine)
            if key_sm not in result:
                result[key_sm] = {}
            result[key_sm][(int(row.annee), int(row.mois))] = {
                "cadence": round(cadence, 2),
                "ops": ops,
                "heures": heures,
                "nb": int(row.nb_traitements or 0),
            }
    except Exception as e:
        print(f"[WARN] get_monthly_cadence_by_service_machine: {e}")
    return result


def _normalize_service_machine_key(service, machine):
    s = (str(service).strip() if service else '') or 'Non renseigné'
    m = (str(machine).strip() if machine else '') or 'Non renseigné'
    return (s, m)


def find_cadence_reference_for_row(monthly_cadences, service, machine, dte_deb_value, max_months_back=24):
    """
    Cherche la cadence moyenne de référence pour une fiche donnée.
    - service : valeur de Nom_GP_SERVICES de la fiche
    - machine : valeur de PostesReel de la fiche
    - dte_deb_value : DteDeb (chaîne 'YYYY-MM-DD HH:MM:SS' ou datetime)
    - On commence par le mois calendaire précédent (par rapport à DteDeb)
    - Si pas de données pour ce mois, on remonte d'un mois (jusqu'à max_months_back = 24)
    Retourne (cadence_ref, label_mois) ou (None, None) si rien trouvé.
    """
    from datetime import datetime as _dt
    if not machine or not dte_deb_value:
        return None, None

    key_sm = _normalize_service_machine_key(service, machine)
    if key_sm not in monthly_cadences:
        return None, None

    try:
        if isinstance(dte_deb_value, _dt):
            dt_obj = dte_deb_value
        else:
            s = str(dte_deb_value).replace('T', ' ').strip()
            dt_obj = _dt.strptime(s[:19], '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        try:
            dt_obj = _dt.strptime(str(dte_deb_value)[:10], '%Y-%m-%d')
        except (ValueError, TypeError):
            return None, None

    year = dt_obj.year
    month = dt_obj.month - 1
    if month < 1:
        month = 12
        year -= 1

    month_names_fr = [
        '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
    ]

    sm_data = monthly_cadences[key_sm]
    for _ in range(max_months_back):
        k = (year, month)
        if k in sm_data:
            data = sm_data[k]
            if data.get("cadence", 0) > 0:
                return data["cadence"], f"{month_names_fr[month]} {year}"
        month -= 1
        if month < 1:
            month = 12
            year -= 1

    return None, None


def enrich_traitements_cadence_comparison(traitements):
    """
    Enrichit chaque fiche de la liste avec :
    - cadence_actuelle (op/h, précision décimale)
    - cadence_reference (cadence moyenne de la même Service+Machine sur le mois calendaire
      précédent par rapport à DteDeb ; si pas de données, on remonte jusqu'à 24 mois).
      Le grouping (Service + Machine) est identique à celui du Tableau de bord
      → les valeurs sont strictement cohérentes.
    - cadence_reference_label (ex: "Avril 2026")
    - cadence_ecart_pct (écart relatif en %)
    - cadence_alert (True si écart <= -15%)
    Les fiches en cours (sans TpsReel) ou sans machine ne reçoivent pas de comparaison.
    """
    if not traitements:
        return traitements
    monthly_cadences = get_monthly_cadence_by_service_machine()
    for t in traitements:
        nb_op = t.get('nb_op') or 0
        tps_reel = t.get('tps_reel') or 0
        cadence_actuelle = None
        if tps_reel and tps_reel > 0 and nb_op:
            try:
                cadence_actuelle = float(nb_op) / float(tps_reel)
            except (TypeError, ValueError, ZeroDivisionError):
                cadence_actuelle = None

        cadence_ref = None
        label_ref = None
        ecart_pct = None
        if cadence_actuelle is not None and t.get('postes_reel') and t.get('dte_deb'):
            cadence_ref, label_ref = find_cadence_reference_for_row(
                monthly_cadences, t.get('service'), t['postes_reel'], t['dte_deb']
            )
            if cadence_ref and cadence_ref > 0:
                try:
                    ecart_pct = ((cadence_actuelle - cadence_ref) / cadence_ref) * 100.0
                except (TypeError, ValueError, ZeroDivisionError):
                    ecart_pct = None

        t['cadence_actuelle'] = round(cadence_actuelle, 2) if cadence_actuelle is not None else None
        t['cadence_reference'] = cadence_ref
        t['cadence_reference_label'] = label_ref
        t['cadence_ecart_pct'] = round(ecart_pct, 2) if ecart_pct is not None else None
        t['cadence_alert'] = bool(ecart_pct is not None and ecart_pct <= -15.0)
    return traitements


def get_tableau_comparatif_commandes(numero_filter=None):
    """
    Données pour le Tableau comparatif (prévu / réel par dossier).
    Retourne une liste de dossiers avec totaux et écarts (temps, coût, quantité).
    Uniquement les commandes non terminées (C.Termine = 0) avec au moins du temps réel.

    Temps réel = SUM(WEB_TRAITEMENTS.TpsReel) des traitements terminés (DteFin renseignée).
    Quantité réelle = SUM(GP_TRAITEMENTS.NbOp) ERP (inchangé).
    """
    def _f(v):
        if v is None:
            return 0.0
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    sql = """
        SELECT
            C.Numero AS numero,
            S.RaiSocTri AS client,
            FT.ID AS id_fiche,
            ISNULL(FT.CtPrevDev, 0) AS cout_prev,
            ISNULL(FT.CtReel, 0) AS cout_reel,
            ISNULL(FI.TpsPrevDev, 0) AS tps_prev,
            ISNULL((
                SELECT SUM(WT.TpsReel)
                FROM WEB_TRAITEMENTS WT
                WHERE LTRIM(RTRIM(WT.Numero_COMMANDES)) = LTRIM(RTRIM(C.Numero))
                  AND WT.DteFin IS NOT NULL
                  AND WT.TpsReel IS NOT NULL
                  AND WT.TpsReel > 0
            ), 0) AS tps_reel,
            (SELECT ISNULL(SUM(FO.OpPrevDev), 0) FROM GP_FICHES_OPERATIONS FO WHERE FO.ID_FICHE_TRAVAIL = FT.ID) AS nb_op_prev,
            (SELECT ISNULL(SUM(T.NbOp), 0) FROM GP_TRAITEMENTS T WHERE T.ID_FICHE_TRAVAIL = FT.ID) AS quantite_reelle
        FROM COMMANDES C
        INNER JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
        INNER JOIN GP_FICHES_TRAVAIL FT ON FT.ID_COMMANDE = C.ID
        LEFT JOIN GP_FICHTRA_INT FI ON FI.ID_FICHTRA = FT.ID
        WHERE C.Termine = 0
    """
    params = []
    if numero_filter and numero_filter.strip():
        sql += " AND C.Numero LIKE ?"
        params.append("%" + numero_filter.strip() + "%")
    sql += " ORDER BY C.Numero, FT.RefFiche"

    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    # Regroupement par numéro de commande
    # tps_reel est déjà au niveau dossier (sous-requête WEB_TRAITEMENTS) : ne pas le resommer par fiche
    by_numero = {}
    for row in rows:
        num = (row.numero or "").strip()
        if not num:
            continue
        if num not in by_numero:
            by_numero[num] = {
                "numero": num,
                "client": (row.client or "").strip(),
                "tps_prev": 0.0,
                "tps_reel": _f(row.tps_reel),
                "cout_prev": 0.0,
                "cout_reel": 0.0,
                "nb_op_prev": 0.0,
                "quantite_reelle": 0.0,
            }
        by_numero[num]["tps_prev"] += _f(row.tps_prev)
        by_numero[num]["cout_prev"] += _f(row.cout_prev)
        by_numero[num]["cout_reel"] += _f(row.cout_reel)
        by_numero[num]["nb_op_prev"] += _f(row.nb_op_prev)
        by_numero[num]["quantite_reelle"] += _f(row.quantite_reelle)

    # Écarts et filtre: uniquement dossiers avec temps réel > 0
    result = []
    for num, data in by_numero.items():
        if data["tps_reel"] == 0:
            continue
        data["tps_prev"] = round(data["tps_prev"], 2)
        data["tps_reel"] = round(data["tps_reel"], 2)
        data["cout_prev"] = round(data["cout_prev"], 2)
        data["cout_reel"] = round(data["cout_reel"], 2)
        data["nb_op_prev"] = round(data["nb_op_prev"], 2)
        data["quantite_reelle"] = round(data["quantite_reelle"], 2)
        data["ecart_tps"] = round(data["tps_reel"] - data["tps_prev"], 2)
        data["ecart_cout"] = round(data["cout_reel"] - data["cout_prev"], 2)
        data["ecart_quantite"] = round(data["quantite_reelle"] - data["nb_op_prev"], 2)
        result.append(data)

    result.sort(key=lambda x: x["numero"])
    return result


# ============================================================================
# RAPPORT MENSUEL KBA (données Projet 11)
# ============================================================================

MOIS_FR_RAPPORT = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def _shift_month(year, month, delta):
    """Retourne (année, mois) après décalage de delta mois."""
    m = month + delta
    y = year
    while m < 1:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return y, m


def _month_bounds(year, month):
    from calendar import monthrange
    from datetime import date
    last = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last)


def get_machines_pour_rapport_kba():
    """
    Liste des machines pour le rapport : postes GP_POSTES non archivés
    (Archive = FAUX), triés alphabétiquement.
    """
    names = []
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT LTRIM(RTRIM(Nom)) AS nom
            FROM GP_POSTES
            WHERE Nom IS NOT NULL
              AND LTRIM(RTRIM(Nom)) <> ''
              AND ISNULL(Archive, 0) = 0
            ORDER BY LTRIM(RTRIM(Nom))
        """)
        seen = set()
        for row in cursor.fetchall():
            n = (row.nom or "").strip()
            if n and n.lower() not in seen:
                seen.add(n.lower())
                names.append(n)
    return sorted(names, key=lambda x: x.lower())


def _fetch_rapport_kba_monthly_rows(machine, date_debut, date_fin):
    """Agrégats mensuels pour une machine sur une plage (filtre DteDeb)."""
    machine = (machine or "").strip()
    with get_db_cursor() as cursor:
        has_pdt_c = column_exists(cursor, "WEB_TRAITEMENTS", "PdtC")
        net_expr = "SUM(ISNULL(PdtC, 0))" if has_pdt_c else "SUM(ISNULL(NbOp, 0))"
        sql = f"""
        SELECT
            YEAR(DteDeb) AS annee,
            MONTH(DteDeb) AS mois,
            SUM(ISNULL(NbOp, 0)) AS total_operations,
            {net_expr} AS feuilles_net_sum,
            COUNT(*) AS nb_traitements,
            COUNT(DISTINCT CAST(DteDeb AS DATE)) AS jours_production,
            SUM(CASE WHEN DteFin IS NOT NULL AND TpsReel IS NOT NULL AND TpsReel > 0
                THEN ISNULL(NbOp, 0) ELSE 0 END) AS ops_cadence,
            SUM(CASE WHEN DteFin IS NOT NULL AND TpsReel IS NOT NULL AND TpsReel > 0
                THEN TpsReel ELSE 0 END) AS tps_cadence,
            SUM(ISNULL(TpsReel, 0)) AS total_heures,
            AVG(CAST(NbOp AS FLOAT)) AS tirage_moyen,
            MAX(CASE WHEN DteFin IS NOT NULL AND TpsReel IS NOT NULL AND TpsReel > 0
                THEN CAST(NbOp AS FLOAT) / TpsReel ELSE NULL END) AS cadence_max_traitement
        FROM WEB_TRAITEMENTS
        WHERE LTRIM(RTRIM(PostesReel)) = ?
          AND DteDeb IS NOT NULL
          AND CAST(DteDeb AS DATE) >= ?
          AND CAST(DteDeb AS DATE) <= ?
        GROUP BY YEAR(DteDeb), MONTH(DteDeb)
        """
        cursor.execute(sql, (machine, date_debut, date_fin))
        rows = cursor.fetchall()
    by_key = {}
    for row in rows:
        key = (int(row.annee), int(row.mois))
        tps = float(row.tps_cadence or 0)
        ops_c = float(row.ops_cadence or 0)
        cadence_moy = round(ops_c / tps, 0) if tps > 0 else 0
        cadence_max = round(float(row.cadence_max_traitement or 0), 0)
        total_h = float(row.total_heures or 0)
        nb_trait = int(row.nb_traitements or 0)
        jours_prod = int(getattr(row, "jours_production", 0) or 0)
        # Changement de travail : le 1er dossier d'une journée n'est pas un changement
        # => changements = dossiers - jours de production (>= 0)
        changements_total = max(nb_trait - jours_prod, 0)
        changements_moyen_jour = round(changements_total / jours_prod, 1) if jours_prod else 0
        by_key[key] = {
            "annee": key[0],
            "mois": key[1],
            "mois_label": MOIS_FR_RAPPORT[key[1] - 1],
            "total_operations": int(row.total_operations or 0),
            "nb_traitements": nb_trait,
            "jours_production": jours_prod,
            "changements_total": changements_total,
            "changements_moyen_jour": changements_moyen_jour,
            "total_heures": round(total_h, 1),
            "cadence_moyenne": int(cadence_moy),
            "cadence_max": int(cadence_max),
            "tirage_moyen": int(round(float(row.tirage_moyen or 0))),
            "feuilles_brut": int(row.total_operations or 0),
            "feuilles_net": int(getattr(row, "feuilles_net_sum", None) or row.total_operations or 0),
        }
    return by_key


def _fetch_compteur_rapport_kba(machine, year, month):
    """Compteur machine : delta du mois et cumul max (CompteurLecture)."""
    ensure_compteur_lecture_column()
    machine = (machine or "").strip()
    debut, fin = _month_bounds(year, month)
    result = {
        "delta_mois": None,
        "max_mois": None,
        "max_cumul": None,
        "disponible": False,
    }
    try:
        with get_db_cursor() as cursor:
            if not column_exists(cursor, "WEB_TRAITEMENTS", "CompteurLecture"):
                return result
            cursor.execute(
                """
                SELECT
                    MIN(CompteurLecture) AS min_lecture,
                    MAX(CompteurLecture) AS max_lecture
                FROM WEB_TRAITEMENTS
                WHERE LTRIM(RTRIM(PostesReel)) = ?
                  AND CompteurLecture IS NOT NULL
                  AND CAST(DteDeb AS DATE) >= ?
                  AND CAST(DteDeb AS DATE) <= ?
                """,
                (machine, debut, fin),
            )
            row = cursor.fetchone()
            if row and row.max_lecture is not None:
                result["disponible"] = True
                result["max_mois"] = int(row.max_lecture)
                if row.min_lecture is not None and int(row.max_lecture) >= int(row.min_lecture):
                    result["delta_mois"] = int(row.max_lecture) - int(row.min_lecture)
            cursor.execute(
                """
                SELECT MAX(CompteurLecture) AS max_cumul
                FROM WEB_TRAITEMENTS
                WHERE LTRIM(RTRIM(PostesReel)) = ?
                  AND CompteurLecture IS NOT NULL
                  AND CAST(DteDeb AS DATE) <= ?
                """,
                (machine, fin),
            )
            row2 = cursor.fetchone()
            if row2 and row2.max_cumul is not None:
                result["max_cumul"] = int(row2.max_cumul)
                result["disponible"] = True
    except Exception as e:
        print(f"[projet11] _fetch_compteur_rapport_kba: {e}")
    return result


def _fetch_rapport_kba_vitesse_repartition(machine, year, month):
    """
    Répartition KBA du temps d'impression du mois par tranche de cadence.

    Chaque traitement terminé avec TpsReel > 0 est classé selon :
        cadence = NbOp / TpsReel (feuilles/heure)
    Le pourcentage d'une tranche est :
        somme(TpsReel de la tranche) / somme(TpsReel éligible) * 100

    Une tranche sans temps retourne pct=None afin d'afficher « — % ».
    """
    machine = (machine or "").strip()
    debut, fin = _month_bounds(year, month)
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                SUM(CASE WHEN cadence < 8000
                    THEN TpsReel ELSE 0 END) AS tps_moins_8000,
                SUM(CASE WHEN cadence >= 8000 AND cadence < 12000
                    THEN TpsReel ELSE 0 END) AS tps_8000_12000,
                SUM(CASE WHEN cadence >= 12000 AND cadence <= 16000
                    THEN TpsReel ELSE 0 END) AS tps_12000_16000,
                SUM(CASE WHEN cadence > 16000
                    THEN TpsReel ELSE 0 END) AS tps_plus_16000,
                SUM(TpsReel) AS tps_total
            FROM (
                SELECT
                    CAST(ISNULL(NbOp, 0) AS FLOAT)
                        / NULLIF(CAST(TpsReel AS FLOAT), 0) AS cadence,
                    CAST(TpsReel AS FLOAT) AS TpsReel
                FROM WEB_TRAITEMENTS
                WHERE LTRIM(RTRIM(PostesReel)) = ?
                  AND DteDeb IS NOT NULL
                  AND CAST(DteDeb AS DATE) >= ?
                  AND CAST(DteDeb AS DATE) <= ?
                  AND DteFin IS NOT NULL
                  AND TpsReel IS NOT NULL
                  AND TpsReel > 0
            ) AS traitements_eligibles
            """,
            (machine, debut, fin),
        )
        row = cursor.fetchone()

    labels = [
        "< 8.000 f/h",
        "8.000 - 12.000 f/h",
        "12.000 - 16.000 f/h",
        "> 16.000 f/h",
    ]
    if not row:
        return [{"label": label, "pct": None, "heures": 0} for label in labels]

    total = float(row.tps_total or 0)
    temps = [
        float(row.tps_moins_8000 or 0),
        float(row.tps_8000_12000 or 0),
        float(row.tps_12000_16000 or 0),
        float(row.tps_plus_16000 or 0),
    ]
    return [
        {
            "label": label,
            "pct": round(tps / total * 100, 1) if total > 0 and tps > 0 else None,
            "heures": round(tps, 2),
        }
        for label, tps in zip(labels, temps)
    ]


def _fetch_rapport_kba_operateurs(machine, date_debut, date_fin):
    """
    Performance opérateurs sur une machine (6 mois).
    Cadence = Somme(NbOp) / Somme(TpsReel) — même formule que
    « Cadence par opérateur » du tableau de bord (traitements terminés, TpsReel > 0).
    Jobs = nombre de dossiers distincts (Numero_COMMANDES).
    Période alignée sur DteDeb (comme le reste du rapport KBA).
    """
    machine = (machine or "").strip()
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                ISNULL(LTRIM(RTRIM(Nom_personel)), '') AS nom,
                ISNULL(LTRIM(RTRIM(Prenom_personel)), '') AS prenom,
                YEAR(DteDeb) AS annee,
                MONTH(DteDeb) AS mois,
                SUM(CASE
                    WHEN DteFin IS NOT NULL AND TpsReel IS NOT NULL AND TpsReel > 0
                    THEN ISNULL(NbOp, 0) ELSE 0 END) AS ops_cadence,
                SUM(CASE
                    WHEN DteFin IS NOT NULL AND TpsReel IS NOT NULL AND TpsReel > 0
                    THEN TpsReel ELSE 0 END) AS tps_cadence,
                COUNT(DISTINCT NULLIF(LTRIM(RTRIM(CAST(Numero_COMMANDES AS NVARCHAR(50)))), '')) AS nb_jobs
            FROM WEB_TRAITEMENTS
            WHERE LTRIM(RTRIM(PostesReel)) = ?
              AND DteDeb IS NOT NULL
              AND CAST(DteDeb AS DATE) >= ?
              AND CAST(DteDeb AS DATE) <= ?
              AND (
                    (Nom_personel IS NOT NULL AND LTRIM(RTRIM(Nom_personel)) <> '')
                 OR (Prenom_personel IS NOT NULL AND LTRIM(RTRIM(Prenom_personel)) <> '')
              )
            GROUP BY
                ISNULL(LTRIM(RTRIM(Nom_personel)), ''),
                ISNULL(LTRIM(RTRIM(Prenom_personel)), ''),
                YEAR(DteDeb),
                MONTH(DteDeb)
            """,
            (machine, date_debut, date_fin),
        )
        rows = cursor.fetchall()

    by_op = {}
    for row in rows:
        nom = (row.nom or "").strip()
        prenom = (row.prenom or "").strip()
        label = f"{nom} {prenom}".strip() or "Non renseigné"
        key = (int(row.annee), int(row.mois))
        tps = float(row.tps_cadence or 0)
        ops = float(row.ops_cadence or 0)
        cadence = round(ops / tps, 0) if tps > 0 else 0
        jobs = int(row.nb_jobs or 0)
        entry = by_op.setdefault(label, {
            "operateur": label,
            "mois": {},
            "total_jobs": 0,
            "total_ops": 0.0,
            "total_tps": 0.0,
        })
        entry["mois"][key] = {
            "cadence": int(cadence),
            "nb_jobs": jobs,
        }
        entry["total_jobs"] += jobs
        entry["total_ops"] += ops
        entry["total_tps"] += tps

    operateurs = list(by_op.values())
    # Tri : volume d'activité (jobs) puis cadence globale
    def _sort_key(op):
        cad = (op["total_ops"] / op["total_tps"]) if op["total_tps"] > 0 else 0
        return (-op["total_jobs"], -cad, op["operateur"].lower())

    operateurs.sort(key=_sort_key)
    return operateurs


def get_rapport_kba_data(machine, year, month, nb_mois_historique=6):
    """
    Données pour le rapport mensuel type KBA à partir de WEB_TRAITEMENTS.
    Filtre sur DteDeb. Historique : nb_mois_historique mois se terminant au mois choisi.
    """
    machine = (machine or "").strip()
    if not machine:
        raise ValueError("Machine requise")
    year = int(year)
    month = int(month)
    if month < 1 or month > 12:
        raise ValueError("Mois invalide")

    start_y, start_m = _shift_month(year, month, -(nb_mois_historique - 1))
    range_debut, _ = _month_bounds(start_y, start_m)
    _, range_fin = _month_bounds(year, month)

    by_key = _fetch_rapport_kba_monthly_rows(machine, range_debut, range_fin)
    operateurs_performance = _fetch_rapport_kba_operateurs(machine, range_debut, range_fin)

    historique = []
    y, m = start_y, start_m
    for _ in range(nb_mois_historique):
        key = (y, m)
        entry = by_key.get(key, {
            "annee": y,
            "mois": m,
            "mois_label": MOIS_FR_RAPPORT[m - 1],
            "total_operations": 0,
            "nb_traitements": 0,
            "jours_production": 0,
            "changements_total": 0,
            "changements_moyen_jour": 0,
            "total_heures": 0,
            "cadence_moyenne": 0,
            "cadence_max": 0,
            "tirage_moyen": 0,
            "feuilles_brut": 0,
            "feuilles_net": 0,
        })
        # Compat : changements/jour basé sur la règle (dossiers - 1 par jour de production)
        entry["changements_par_jour"] = entry.get("changements_moyen_jour", 0)
        historique.append(entry)
        y, m = _shift_month(y, m, 1)

    # mois courant = dernier de l'historique
    mois_courant = historique[-1] if historique else {}
    compteur = _fetch_compteur_rapport_kba(machine, year, month)
    repartition_vitesses = _fetch_rapport_kba_vitesse_repartition(machine, year, month)
    historique_graph = list(reversed(historique))

    # Compteur feuilles brut/net : cumul du mois sélectionné (toutes les opérations)
    feuilles_brut_mois = int(mois_courant.get("feuilles_brut") or mois_courant.get("total_operations") or 0)
    feuilles_net_mois = int(mois_courant.get("feuilles_net") or mois_courant.get("total_operations") or 0)

    return {
        "machine": machine,
        "machine_type": "Moyen format",
        "machine_segment": "tous",
        "num_construction": None,
        "annee_machine": year,
        "annee": year,
        "mois": month,
        "mois_label": MOIS_FR_RAPPORT[month - 1],
        "titre_periode": f"{MOIS_FR_RAPPORT[month - 1]} {year}",
        "client": "Imprimerie Novaprint",
        "site": "TN",
        "mois_courant": mois_courant,
        "historique": historique,
        "historique_graph": historique_graph,
        "operateurs_performance": operateurs_performance,
        "compteur": compteur,
        "compteur_brut": feuilles_brut_mois,
        "compteur_net": feuilles_net_mois,
        "source": "Projet 11 — WEB_TRAITEMENTS (DteDeb)",
        "sections_telemetry": {
            "disponibilite_pct": None,
            "temps_veille_h": None,
            "temps_arret_h": None,
            "temps_impression_h": mois_courant.get("total_heures"),
            "temps_plaques_h": None,
            "temps_lavage_h": None,
            "vitesses": repartition_vitesses,
            "performance_score": None,
            "maintenance": None,
        },
    }

