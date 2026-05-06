# -*- coding: utf-8 -*-
"""
Logique métier Projet 24 – Formes de Découpe.
Tables dédiées : WEB_FORMES_DECOUPE, WEB_FORMES_COUTS (isolées de toute synchro externe).
"""
from db import get_db_cursor

TABLE_FORMES = "dbo.WEB_FORMES_DECOUPE"
TABLE_COUTS = "dbo.WEB_FORMES_COUTS"


def _row_to_forme(row):
    """Convertit une ligne SQL en dict pour une forme."""
    if not row:
        return None
    return {
        'id': getattr(row, 'ID', None),
        'type_forme': getattr(row, 'TYPE_FORME', None),
        'type_produit': getattr(row, 'TYPE_PRODUIT', None),
        'nom': getattr(row, 'NOM', None),
        'dimension': getattr(row, 'DIMENSION', None),
        'format_fini': getattr(row, 'FORMAT_FINI', None),
        'sens_fibre': getattr(row, 'SENS_FIBRE', None),
        'fichier_source': getattr(row, 'FICHIER_SOURCE', None),
        'nombre_pose': getattr(row, 'NOMBRE_POSE', 1) or 1,
        'total_tirages': getattr(row, 'TOTAL_TIRAGES', 0) or 0,
        'cout_initial': float(getattr(row, 'COUT_INITIAL', 0) or 0),
        'cout_amelioration': float(getattr(row, 'COUT_AMELIORATION', 0) or 0),
        'etat': getattr(row, 'ETAT', 'EN_COMMANDE') or 'EN_COMMANDE',
        'description': getattr(row, 'DESCRIPTION', None),
        'date_creation': getattr(row, 'DATE_CREATION', None),
        'createur': getattr(row, 'CREATEUR', None),
    }


def get_all_formes():
    """Liste toutes les formes. Affiche toutes les lignes (pas de filtre STATUT) pour inclure les données existantes."""
    with get_db_cursor() as cursor:
        try:
            # Requête complète si la colonne STATUT existe
            cursor.execute("""
                SELECT ID, TYPE_FORME, TYPE_PRODUIT, NOM, DIMENSION, FORMAT_FINI, SENS_FIBRE,
                       FICHIER_SOURCE, NOMBRE_POSE, TOTAL_TIRAGES, COUT_INITIAL, COUT_AMELIORATION,
                       ETAT, DESCRIPTION, DATE_CREATION, CREATEUR
                FROM WEB_FORMES_DECOUPE
                ORDER BY COALESCE(DATE_CREATION, CAST(ID AS DATETIME)) DESC, ID DESC
            """)
        except Exception:
            # Fallback si colonnes DESCRIPTION ou DATE_CREATION absentes
            cursor.execute("""
                SELECT ID, TYPE_FORME, TYPE_PRODUIT, NOM, DIMENSION, FORMAT_FINI, SENS_FIBRE,
                       FICHIER_SOURCE, NOMBRE_POSE, TOTAL_TIRAGES, COUT_INITIAL, COUT_AMELIORATION,
                       ETAT, DATE_CREATION, CREATEUR
                FROM WEB_FORMES_DECOUPE
                ORDER BY ID DESC
            """)
        return [_row_to_forme(r) for r in cursor.fetchall()]


def get_forme_by_id(forme_id):
    """Retourne une forme par ID."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT ID, TYPE_FORME, TYPE_PRODUIT, NOM, DIMENSION, FORMAT_FINI, SENS_FIBRE,
                   FICHIER_SOURCE, NOMBRE_POSE, TOTAL_TIRAGES, COUT_INITIAL, COUT_AMELIORATION,
                   ETAT, DESCRIPTION, DATE_CREATION, CREATEUR
            FROM WEB_FORMES_DECOUPE WHERE ID = ?
        """, (forme_id,))
        return _row_to_forme(cursor.fetchone())


def get_forme_by_nom(nom):
    """Retourne une forme par NOM."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT ID, TYPE_FORME, TYPE_PRODUIT, NOM, DIMENSION, FORMAT_FINI, SENS_FIBRE,
                   FICHIER_SOURCE, NOMBRE_POSE, TOTAL_TIRAGES, COUT_INITIAL, COUT_AMELIORATION,
                   ETAT, DESCRIPTION, DATE_CREATION, CREATEUR
            FROM WEB_FORMES_DECOUPE WHERE NOM = ?
        """, (nom,))
        return _row_to_forme(cursor.fetchone())


def get_next_numero_for_type(prefix):
    """Retourne le prochain numéro séquentiel pour le préfixe (ex: VAR26 -> 001, 002...)."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT MAX(TRY_CAST(SUBSTRING(NOM, LEN(?) + 1, 10) AS INT))
            FROM WEB_FORMES_DECOUPE
            WHERE NOM LIKE ? AND LEN(NOM) >= LEN(?) + 3
        """, (prefix, prefix + '%', prefix))
        row = cursor.fetchone()
        val = row[0] if row and row[0] is not None else 0
        return val + 1


def _ensure_unique_nom_index():
    """Assure une contrainte d'unicité sur WEB_FORMES_DECOUPE.NOM (SQL Server)."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM sys.indexes
                WHERE name = 'UX_WEB_FORMES_DECOUPE_NOM' AND object_id = OBJECT_ID('dbo.WEB_FORMES_DECOUPE')
            )
            BEGIN
                CREATE UNIQUE INDEX UX_WEB_FORMES_DECOUPE_NOM ON dbo.WEB_FORMES_DECOUPE (NOM);
            END
        """)
        cursor.connection.commit()


def create_forme(data, createur='System'):
    """Crée une forme. Le NOM est toujours auto-généré (pas de saisie manuelle)."""
    _ensure_unique_nom_index()
    nom = ''  # plus de saisie manuelle
    type_forme = (data.get('type_forme') or '').strip().upper()[:10]
    type_produit = (data.get('type_produit') or '').strip()[:50]
    dimension = (data.get('dimension') or '').strip()[:100] or None
    format_fini = (data.get('format_fini') or '').strip()[:50] or None
    sens_fibre = (data.get('sens_fibre') or '').strip()[:20] or None
    description = data.get('description')
    if description:
        description = str(description).strip()[:8000]
    nombre_pose = data.get('nombre_pose')
    try:
        nombre_pose = int(nombre_pose) if nombre_pose is not None else 1
    except (ValueError, TypeError):
        nombre_pose = 1
    cout_initial = data.get('cout_initial')
    try:
        cout_initial = float(cout_initial) if cout_initial not in (None, '') else 0
    except (ValueError, TypeError):
        cout_initial = 0
    fichier_source = (data.get('fichier_source') or '').strip()[:255] or None

    if not type_forme:
        return None, "Type forme requis"
    if not type_produit:
        return None, "Type produit requis"

    with get_db_cursor() as cursor:
        # Génération auto atomique : verrou sur la plage de noms du préfixe
        an = "26"
        prefix = type_forme + an
        etat = 'EN_COMMANDE'
        tries = 0
        while True:
            tries += 1
            if tries > 25:
                return None, "Impossible de générer un identifiant unique (conflit). Réessayez."
            try:
                cursor.execute("BEGIN TRAN")
                # Verrouille la plage des lignes concernées pendant le calcul du max + insert
                cursor.execute("""
                    SELECT MAX(TRY_CAST(SUBSTRING(NOM, LEN(?) + 1, 10) AS INT))
                    FROM WEB_FORMES_DECOUPE WITH (UPDLOCK, HOLDLOCK)
                    WHERE NOM LIKE ? AND LEN(NOM) >= LEN(?) + 3
                """, (prefix, prefix + '%', prefix))
                row = cursor.fetchone()
                val = row[0] if row and row[0] is not None else 0
                next_num = int(val) + 1
                nom = f"{prefix}{next_num:03d}"
                cursor.execute("""
                    INSERT INTO WEB_FORMES_DECOUPE
                    (TYPE_FORME, TYPE_PRODUIT, NOM, DIMENSION, FORMAT_FINI, SENS_FIBRE, FICHIER_SOURCE,
                     NOMBRE_POSE, TOTAL_TIRAGES, COUT_INITIAL, COUT_AMELIORATION, ETAT, DESCRIPTION, CREATEUR)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 0, ?, ?, ?)
                """, (type_forme, type_produit, nom, dimension, format_fini, sens_fibre, fichier_source,
                      nombre_pose, cout_initial, etat, description, createur))
                cursor.execute("COMMIT TRAN")
                cursor.connection.commit()
                break
            except Exception:
                try:
                    cursor.execute("ROLLBACK TRAN")
                except Exception:
                    pass
                # collision / course : on retente
                continue
        cursor.execute("SELECT ID FROM WEB_FORMES_DECOUPE WHERE NOM = ?", (nom,))
        row = cursor.fetchone()
        return get_forme_by_id(row.ID), None


def update_forme_by_nom(nom, data, fichier_source=None):
    """Met à jour une forme par NOM. data contient les champs à mettre à jour."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT ID FROM WEB_FORMES_DECOUPE WHERE NOM = ?", (nom,))
        row = cursor.fetchone()
        if not row:
            return False, "Forme introuvable"
        forme_id = row.ID

    updates = []
    params = []
    for key, col in [
        ('type_forme', 'TYPE_FORME'), ('type_produit', 'TYPE_PRODUIT'),
        ('dimension', 'DIMENSION'), ('format_fini', 'FORMAT_FINI'), ('sens_fibre', 'SENS_FIBRE'),
        ('nombre_pose', 'NOMBRE_POSE'), ('cout_initial', 'COUT_INITIAL'), ('description', 'DESCRIPTION'),
    ]:
        if key in data:
            val = data[key]
            if key == 'nombre_pose':
                try:
                    val = int(val) if val not in (None, '') else 1
                except (ValueError, TypeError):
                    val = 1
            elif key == 'cout_initial':
                try:
                    val = float(val) if val not in (None, '') else 0
                except (ValueError, TypeError):
                    val = 0
            else:
                val = (val or '').strip() if isinstance(val, str) else val
                if col in ('TYPE_FORME', 'SENS_FIBRE') and val:
                    val = val[:10] if col == 'TYPE_FORME' else val[:20]
                elif col == 'TYPE_PRODUIT' and val:
                    val = val[:50]
                elif col in ('DIMENSION', 'FORMAT_FINI') and val:
                    val = val[:100] if col == 'DIMENSION' else val[:50]
            updates.append(f"{col} = ?")
            params.append(val)
    if fichier_source is not None:
        updates.append("FICHIER_SOURCE = ?")
        params.append((fichier_source or '').strip()[:255])
    if not updates:
        return True, None
    params.append(nom)
    with get_db_cursor() as cursor:
        cursor.execute(
            "UPDATE WEB_FORMES_DECOUPE SET " + ", ".join(updates) + " WHERE NOM = ?",
            params
        )
        cursor.connection.commit()
    return True, None


def delete_forme_by_nom(nom):
    """Suppression réelle : supprime les coûts puis la forme."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT ID FROM WEB_FORMES_DECOUPE WHERE NOM = ?", (nom,))
        row = cursor.fetchone()
        if not row:
            return False, "Forme introuvable"
        cursor.execute("DELETE FROM WEB_FORMES_COUTS WHERE ID_FORME = ?", (row.ID,))
        cursor.execute("DELETE FROM WEB_FORMES_DECOUPE WHERE NOM = ?", (nom,))
        cursor.connection.commit()
    return True, None


def add_tirages(nom, nombre_tirages, createur='System'):
    """Incrémente TOTAL_TIRAGES pour la forme."""
    try:
        n = int(nombre_tirages)
        if n <= 0:
            return False, "Nombre de tirages invalide"
    except (ValueError, TypeError):
        return False, "Nombre de tirages invalide"
    with get_db_cursor() as cursor:
        cursor.execute(
            "UPDATE WEB_FORMES_DECOUPE SET TOTAL_TIRAGES = TOTAL_TIRAGES + ? WHERE NOM = ?",
            (n, nom)
        )
        if cursor.rowcount == 0:
            return False, "Forme introuvable"
        cursor.connection.commit()
    return True, None


def get_couts_by_nom(nom):
    """Liste les coûts d'amélioration pour une forme (par NOM)."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT FC.ID, FC.MONTANT, FC.DESCRIPTION, FC.DATE_AJOUT, FC.CREATEUR
            FROM WEB_FORMES_COUTS FC
            INNER JOIN WEB_FORMES_DECOUPE FD ON FD.ID = FC.ID_FORME
            WHERE FD.NOM = ?
            ORDER BY FC.DATE_AJOUT DESC
        """, (nom,))
        return [
            {
                'id': r.ID,
                'montant': float(r.MONTANT),
                'description': getattr(r, 'DESCRIPTION', None),
                'date_ajout': r.DATE_AJOUT,
                'createur': getattr(r, 'CREATEUR', None),
            }
            for r in cursor.fetchall()
        ]


def add_cout(nom, montant, description, createur='System'):
    """Ajoute une ligne de coût d'amélioration et met à jour COUT_AMELIORATION."""
    try:
        m = float(montant)
    except (ValueError, TypeError):
        return False, "Montant invalide"
    with get_db_cursor() as cursor:
        cursor.execute("SELECT ID FROM WEB_FORMES_DECOUPE WHERE NOM = ?", (nom,))
        row = cursor.fetchone()
        if not row:
            return False, "Forme introuvable"
        id_forme = row.ID
        cursor.execute("""
            INSERT INTO WEB_FORMES_COUTS (ID_FORME, MONTANT, DESCRIPTION, CREATEUR) VALUES (?, ?, ?, ?)
        """, (id_forme, m, (description or '').strip()[:8000], createur))
        cursor.execute(
            "UPDATE WEB_FORMES_DECOUPE SET COUT_AMELIORATION = COUT_AMELIORATION + ? WHERE ID = ?",
            (m, id_forme)
        )
        cursor.connection.commit()
    return True, None


def set_etat(nom, etat):
    """Met à jour l'état : EN_COMMANDE, PRETE, EN_MODIFICATION."""
    allowed = ('EN_COMMANDE', 'PRETE', 'EN_MODIFICATION')
    if etat not in allowed:
        return False, "État invalide"
    with get_db_cursor() as cursor:
        cursor.execute("UPDATE WEB_FORMES_DECOUPE SET ETAT = ? WHERE NOM = ?", (etat, nom))
        if cursor.rowcount == 0:
            return False, "Forme introuvable"
        cursor.connection.commit()
    return True, None


def get_dashboard_stats():
    """Retourne les stats pour le tableau de bord. Inclut toutes les formes (pas de filtre STATUT) comme la liste."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) AS total, ISNULL(SUM(ISNULL(COUT_INITIAL, 0) + ISNULL(COUT_AMELIORATION, 0)), 0) AS cout_total
            FROM WEB_FORMES_DECOUPE
        """)
        r = cursor.fetchone()
        total_formes = r.total or 0
        cout_total = float(r.cout_total or 0)

        cursor.execute("""
            SELECT TYPE_FORME, COUNT(*) AS nb
            FROM WEB_FORMES_DECOUPE
            GROUP BY TYPE_FORME ORDER BY nb DESC
        """)
        by_type = [{'type_forme': row.TYPE_FORME or 'N/A', 'nb': row.nb} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT ETAT, COUNT(*) AS nb
            FROM WEB_FORMES_DECOUPE
            GROUP BY ETAT ORDER BY nb DESC
        """)
        by_etat = [{'etat': row.ETAT or 'N/A', 'nb': row.nb} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT TOP 5 NOM, ISNULL(TOTAL_TIRAGES, 0) AS TOTAL_TIRAGES
            FROM WEB_FORMES_DECOUPE
            ORDER BY ISNULL(TOTAL_TIRAGES, 0) DESC
        """)
        top5_plus = [{'nom': row.NOM or '', 'total_tirages': row.TOTAL_TIRAGES or 0} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT TOP 5 NOM, ISNULL(TOTAL_TIRAGES, 0) AS TOTAL_TIRAGES
            FROM WEB_FORMES_DECOUPE
            ORDER BY ISNULL(TOTAL_TIRAGES, 0) ASC
        """)
        top5_moins = [{'nom': row.NOM or '', 'total_tirages': row.TOTAL_TIRAGES or 0} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT TYPE_FORME, ISNULL(SUM(ISNULL(TOTAL_TIRAGES, 0)), 0) AS tirages
            FROM WEB_FORMES_DECOUPE
            GROUP BY TYPE_FORME ORDER BY tirages DESC
        """)
        tirages_par_type = [{'type_forme': row.TYPE_FORME or 'N/A', 'tirages': row.tirages} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT TYPE_PRODUIT, COUNT(*) AS nb
            FROM WEB_FORMES_DECOUPE
            GROUP BY TYPE_PRODUIT ORDER BY nb DESC
        """)
        by_type_produit = [{'type_produit': row.TYPE_PRODUIT or 'N/A', 'nb': row.nb} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT ISNULL(SUM(ISNULL(TOTAL_TIRAGES, 0)), 0) AS total_tirages
            FROM WEB_FORMES_DECOUPE
        """)
        row = cursor.fetchone()
        total_tirages = int(row.total_tirages or 0)

    return {
        'total_formes': total_formes,
        'cout_total': cout_total,
        'total_tirages': total_tirages,
        'by_type': by_type,
        'by_etat': by_etat,
        'by_type_produit': by_type_produit,
        'top5_plus': top5_plus,
        'top5_moins': top5_moins,
        'tirages_par_type': tirages_par_type,
    }


def generate_identifiant(type_forme):
    """Suggère un identifiant pour un type (ex: VAR -> VAR26001)."""
    type_forme = (type_forme or '').strip().upper()[:10]
    if not type_forme:
        return None
    an = "26"
    next_num = get_next_numero_for_type(type_forme + an)
    return f"{type_forme}{an}{next_num:03d}"
