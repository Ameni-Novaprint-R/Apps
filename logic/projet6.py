from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from db import get_db_cursor
from datetime import datetime, timedelta, date
from contextlib import contextmanager
from logic.auth import (
    login_required,
    has_project_access,
    get_user_sections,
    is_super_user,
)
try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False
    pdfkit = None



projet6_bp = Blueprint('projet6', __name__)

PROJET6_SECTION_KEYS = {
    'Nouveau voyage': 'nouveau_voyage',
    'Liste des voyages': 'liste_voyages',
    'Gestion des véhicules': 'gestion_vehicules',
}

VIDANGE_INTERVALLE_KM = 10000
VIDANGE_ALERTE_KM = 1000
VIDANGE_INTERVALLE_HEURES = 200
VIDANGE_ALERTE_HEURES = 30
VISITE_ALERTE_JOURS = 7
MODE_VIDANGE_KM = 'KM'
MODE_VIDANGE_HEURES = 'HEURES'


def ensure_projet6_vidange_schema(cur):
    """Schéma véhicules : modes km/heures, visite, historique vidanges."""
    cur.execute("""
        IF COL_LENGTH('dbo.WEB_CAMIONS', 'KmActuel') IS NULL
            ALTER TABLE dbo.WEB_CAMIONS ADD KmActuel INT NULL
    """)
    cur.execute("""
        IF COL_LENGTH('dbo.WEB_CAMIONS', 'HeuresActuelles') IS NULL
            ALTER TABLE dbo.WEB_CAMIONS ADD HeuresActuelles INT NULL
    """)
    cur.execute("""
        IF COL_LENGTH('dbo.WEB_CAMIONS', 'ModeSuiviVidange') IS NULL
            ALTER TABLE dbo.WEB_CAMIONS ADD ModeSuiviVidange NVARCHAR(10) NULL
    """)
    cur.execute("""
        UPDATE WEB_CAMIONS
        SET ModeSuiviVidange = 'KM'
        WHERE ModeSuiviVidange IS NULL OR LTRIM(RTRIM(ModeSuiviVidange)) = ''
    """)
    cur.execute("""
        IF COL_LENGTH('dbo.WEB_CAMIONS', 'DateProchaineVisiteTechnique') IS NULL
            ALTER TABLE dbo.WEB_CAMIONS ADD DateProchaineVisiteTechnique DATE NULL
    """)
    for col in (
        'DateDebutAssurance',
        'DateFinAssurance',
        'DatePaiementTaxe',
        'PaiementTaxe',
    ):
        cur.execute(f"""
            IF COL_LENGTH('dbo.WEB_CAMIONS', '{col}') IS NOT NULL
                ALTER TABLE dbo.WEB_CAMIONS DROP COLUMN {col}
        """)
    cur.execute("""
        IF OBJECT_ID('dbo.WEB_CAMION_VIDANGES', 'U') IS NULL
        CREATE TABLE dbo.WEB_CAMION_VIDANGES (
            ID INT IDENTITY(1,1) PRIMARY KEY,
            ID_Camion INT NOT NULL,
            DateVidange DATE NOT NULL,
            Km INT NULL,
            Heures INT NULL,
            Remarque NVARCHAR(500) NULL,
            CreeLe DATETIME NOT NULL DEFAULT GETDATE(),
            CONSTRAINT FK_WEB_CAMION_VIDANGES_CAMION
                FOREIGN KEY (ID_Camion) REFERENCES dbo.WEB_CAMIONS(ID)
        )
    """)
    cur.execute("""
        IF COL_LENGTH('dbo.WEB_CAMION_VIDANGES', 'Heures') IS NULL
            ALTER TABLE dbo.WEB_CAMION_VIDANGES ADD Heures INT NULL
    """)
    # Km peut être NULL pour les engins suivis aux heures
    cur.execute("""
        IF EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'WEB_CAMION_VIDANGES' AND COLUMN_NAME = 'Km' AND IS_NULLABLE = 'NO'
        )
        BEGIN
            ALTER TABLE dbo.WEB_CAMION_VIDANGES ALTER COLUMN Km INT NULL
        END
    """)


def ensure_projet6_voyage_lignes_schema(cur):
    """Colonnes lignes de voyage (Article modifiable, prérempli depuis la commande)."""
    cur.execute("""
        IF COL_LENGTH('dbo.WEB_VOYAGE_LIGNES', 'Article') IS NULL
            ALTER TABLE dbo.WEB_VOYAGE_LIGNES ADD Article NVARCHAR(500) NULL
    """)


def ensure_projet6_notification_schema(cur):
    """Notifications vidange / visite technique (style Facebook : Lu + suppression)."""
    cur.execute("""
        IF OBJECT_ID('dbo.WEB_PROJET6_NOTIFICATION', 'U') IS NULL
        CREATE TABLE dbo.WEB_PROJET6_NOTIFICATION (
            ID INT IDENTITY(1,1) PRIMARY KEY,
            MatriculeDest NVARCHAR(50) NOT NULL,
            TypeNotif NVARCHAR(50) NOT NULL,
            Message NVARCHAR(500) NOT NULL,
            ID_Camion INT NULL,
            CleUnique NVARCHAR(160) NOT NULL,
            Lu BIT NOT NULL DEFAULT 0,
            Supprime BIT NOT NULL DEFAULT 0,
            DateCreation DATETIME NOT NULL DEFAULT GETDATE()
        )
    """)
    cur.execute("""
        IF NOT EXISTS (
            SELECT 1 FROM sys.indexes
            WHERE name = 'UQ_WEB_PROJET6_NOTIFICATION_CLE'
              AND object_id = OBJECT_ID('dbo.WEB_PROJET6_NOTIFICATION')
        )
        CREATE UNIQUE INDEX UQ_WEB_PROJET6_NOTIFICATION_CLE
            ON dbo.WEB_PROJET6_NOTIFICATION (MatriculeDest, CleUnique)
    """)


def _matricule_notif():
    mat = session.get('matricule')
    if mat is None or mat == '':
        return None
    return str(mat).strip()


def _insert_notif_if_new(cur, matricule, type_notif, message, id_camion, cle_unique):
    cur.execute("""
        SELECT 1 FROM WEB_PROJET6_NOTIFICATION
        WHERE MatriculeDest = ? AND CleUnique = ?
    """, (matricule, cle_unique))
    if cur.fetchone():
        return
    cur.execute("""
        INSERT INTO WEB_PROJET6_NOTIFICATION
            (MatriculeDest, TypeNotif, Message, ID_Camion, CleUnique, Lu, Supprime)
        VALUES (?, ?, ?, ?, ?, 0, 0)
    """, (matricule, type_notif, message[:500], id_camion, cle_unique))


def sync_projet6_notifications(cur, matricule=None):
    """Crée les notifs vidange/visite pour l'utilisateur (sans recréer si déjà existante/supprimée)."""
    mat = matricule if matricule is not None else _matricule_notif()
    if not mat:
        return
    ensure_projet6_notification_schema(cur)
    camions = fetch_camions_suivi(cur)
    for c in camions:
        immat = c.get('immatriculation') or '?'
        lib = f"{immat}"
        if c.get('marque') or c.get('modele'):
            lib = f"{immat} ({(c.get('marque') or '').strip()} {(c.get('modele') or '').strip()})".strip()

        st_v = c.get('statut_visite')
        if st_v in ('bientot', 'retard'):
            d = c.get('date_prochaine_visite')
            d_str = d.isoformat() if d else 'nr'
            d_aff = d.strftime('%d/%m/%Y') if d else '?'
            if st_v == 'retard':
                typ = 'VISITE_RETARD'
                msg = f"Visite technique dépassée — {lib}, prévue le {d_aff}."
            else:
                typ = 'VISITE_BIENTOT'
                msg = f"Visite technique bientôt — {lib}, prévue le {d_aff}."
            cle = f"VISITE:{c['id']}:{d_str}:{st_v}"
            _insert_notif_if_new(cur, mat, typ, msg, c['id'], cle)

        st_vd = c.get('statut_vidange')
        if st_vd in ('bientot', 'retard'):
            prochain = c.get('compteur_prochain')
            actuel = c.get('compteur_actuel')
            unite = c.get('unite_vidange') or 'km'
            restant = None
            if prochain is not None and actuel is not None:
                try:
                    restant = int(prochain) - int(actuel)
                except (TypeError, ValueError):
                    restant = None
            # Inclure compteur actuel / reste : un nouvel enregistrement (ex. 30h → 10h) crée une nouvelle notif
            cle = f"VIDANGE:{c['id']}:{actuel}:{prochain}:{restant}:{st_vd}"
            if st_vd == 'retard':
                typ = 'VIDANGE_RETARD'
                msg = f"Vidange dépassée — {lib}."
                if restant is not None:
                    msg = f"Vidange dépassée — {lib} (dépassement {abs(restant)} {unite})."
            else:
                typ = 'VIDANGE_BIENTOT'
                msg = f"Vidange bientôt — {lib}."
                if restant is not None:
                    msg = f"Vidange bientôt — {lib} (reste {restant} {unite})."
            _insert_notif_if_new(cur, mat, typ, msg, c['id'], cle)


def get_projet6_notifications(matricule=None, non_lues_seulement=False):
    mat = matricule if matricule is not None else _matricule_notif()
    if not mat:
        return []
    with get_db_cursor() as cur:
        ensure_projet6_notification_schema(cur)
        sync_projet6_notifications(cur, mat)
        cur.connection.commit()
        sql = """
            SELECT ID, TypeNotif, Message, ID_Camion, Lu, DateCreation
            FROM WEB_PROJET6_NOTIFICATION
            WHERE MatriculeDest = ? AND ISNULL(Supprime, 0) = 0
        """
        params = [mat]
        if non_lues_seulement:
            sql += " AND ISNULL(Lu, 0) = 0"
        sql += " ORDER BY DateCreation DESC, ID DESC"
        cur.execute(sql, params)
        rows = cur.fetchall()
    result = []
    for r in rows:
        dc = r[5]
        if hasattr(dc, 'strftime'):
            date_aff = dc.strftime('%d/%m/%Y %H:%M')
        else:
            date_aff = str(dc or '')
        result.append({
            'id': r[0],
            'type': r[1],
            'message': r[2],
            'id_camion': r[3],
            'lu': bool(r[4]),
            'date': date_aff,
        })
    return result


def marquer_projet6_notifications_lues(matricule=None, ids=None):
    mat = matricule if matricule is not None else _matricule_notif()
    if not mat:
        return
    with get_db_cursor() as cur:
        ensure_projet6_notification_schema(cur)
        if ids:
            ids = [int(i) for i in ids if str(i).isdigit() or isinstance(i, int)]
            if not ids:
                return
            placeholders = ','.join('?' for _ in ids)
            cur.execute(
                f"""UPDATE WEB_PROJET6_NOTIFICATION SET Lu = 1
                    WHERE MatriculeDest = ? AND ID IN ({placeholders}) AND ISNULL(Supprime, 0) = 0""",
                [mat] + ids,
            )
        else:
            cur.execute("""
                UPDATE WEB_PROJET6_NOTIFICATION SET Lu = 1
                WHERE MatriculeDest = ? AND ISNULL(Supprime, 0) = 0 AND ISNULL(Lu, 0) = 0
            """, (mat,))
        cur.connection.commit()


def supprimer_projet6_notification(notif_id, matricule=None):
    mat = matricule if matricule is not None else _matricule_notif()
    if not mat:
        return False
    with get_db_cursor() as cur:
        ensure_projet6_notification_schema(cur)
        cur.execute("""
            UPDATE WEB_PROJET6_NOTIFICATION SET Supprime = 1, Lu = 1
            WHERE ID = ? AND MatriculeDest = ?
        """, (notif_id, mat))
        cur.connection.commit()
        return cur.rowcount > 0


def _normalize_mode_vidange(value):
    mode = (value or MODE_VIDANGE_KM).strip().upper()
    if mode in ('H', 'HEURE', 'HEURES', 'HOUR', 'HOURS'):
        return MODE_VIDANGE_HEURES
    return MODE_VIDANGE_KM


def _parse_int_or_none(raw):
    raw = (raw or '').strip()
    if raw.isdigit():
        return int(raw)
    return None


def _statut_visite_prochaine(date_prochaine, today=None):
    """ok | bientot (<=7 j) | retard (dépassée) | nr."""
    if today is None:
        today = datetime.today().date()
    d = _coerce_camion_date(date_prochaine)
    if d is None:
        return 'nr'
    if d < today:
        return 'retard'
    if d <= today + timedelta(days=VISITE_ALERTE_JOURS):
        return 'bientot'
    return 'ok'


def _format_date_input(value):
    d = _coerce_camion_date(value)
    return d.isoformat() if d else ''


def _statut_vidange_compteur(actuel, derniere, intervalle, alerte):
    if actuel is None or derniere is None:
        return 'nr'
    try:
        actuel = int(actuel)
        derniere = int(derniere)
    except (TypeError, ValueError):
        return 'nr'
    restant = (derniere + intervalle) - actuel
    if restant <= 0:
        return 'retard'
    if restant <= alerte:
        return 'bientot'
    return 'ok'


def _build_camion_suivi_row(row):
    """Construit un dict véhicule + infos visite / vidange pour le tableau."""
    mode = _normalize_mode_vidange(getattr(row, 'ModeSuiviVidange', None))
    date_vidange = _coerce_camion_date(row.DateDerniereVidange)
    km_derniere = row.KmDerniereVidange
    heures_derniere = getattr(row, 'HeuresDerniereVidange', None)
    km_actuel = row.KmActuel
    heures_actuelles = getattr(row, 'HeuresActuelles', None)

    if mode == MODE_VIDANGE_HEURES:
        unite = 'h'
        compteur_actuel = heures_actuelles
        compteur_vidange = heures_derniere
        intervalle = VIDANGE_INTERVALLE_HEURES
        alerte = VIDANGE_ALERTE_HEURES
    else:
        unite = 'km'
        compteur_actuel = km_actuel
        compteur_vidange = km_derniere
        intervalle = VIDANGE_INTERVALLE_KM
        alerte = VIDANGE_ALERTE_KM

    compteur_prochain = (
        int(compteur_vidange) + intervalle
        if compteur_vidange is not None else None
    )
    statut = _statut_vidange_compteur(compteur_actuel, compteur_vidange, intervalle, alerte)

    date_derniere_visite = _coerce_camion_date(row.DateVisiteTechnique)
    date_prochaine_visite = _coerce_camion_date(getattr(row, 'DateProchaineVisiteTechnique', None))
    return {
        'id': row.ID,
        'immatriculation': row.Immatriculation,
        'marque': row.Marque,
        'modele': row.Modele,
        'date_achat': _coerce_camion_date(row.DateAchat),
        'date_derniere_visite': date_derniere_visite,
        'date_prochaine_visite': date_prochaine_visite,
        'statut_visite': _statut_visite_prochaine(date_prochaine_visite),
        'observations': row.Observations,
        'mode_suivi_vidange': mode,
        'unite_vidange': unite,
        'km_actuel': km_actuel,
        'heures_actuelles': heures_actuelles,
        'compteur_actuel': compteur_actuel,
        'date_derniere_vidange': date_vidange,
        'km_derniere_vidange': km_derniere,
        'heures_derniere_vidange': heures_derniere,
        'compteur_vidange': compteur_vidange,
        'compteur_prochain': compteur_prochain,
        'intervalle_vidange': intervalle,
        'statut_vidange': statut,
    }


def get_projet6_allowed_sections():
    if is_super_user():
        return list(PROJET6_SECTION_KEYS.values())
    raw = get_user_sections(6)
    allowed = []
    for s in raw:
        nom = (s.get('nom') or s.get('Nom') or '').strip()
        key = PROJET6_SECTION_KEYS.get(nom)
        if not key and nom:
            nl = nom.lower()
            if 'nouveau' in nl and 'voyage' in nl:
                key = 'nouveau_voyage'
            elif 'liste' in nl and 'voyage' in nl:
                key = 'liste_voyages'
            elif 'vehicul' in nl or 'véhicul' in nl:
                key = 'gestion_vehicules'
        if key and key not in allowed:
            allowed.append(key)
    return allowed


def _period_range_voyages(periode):
    """Retourne (date_debut, date_fin) ou (None, None) pour tout l'historique."""
    today = date.today()
    periode = (periode or 'semaine').strip().lower()
    if periode == 'mois':
        start = today.replace(day=1)
        if today.month == 12:
            end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        return start, end
    if periode in ('historique', 'tous', 'all'):
        return None, None
    # semaine en cours (lundi → dimanche)
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start, end


def fetch_voyages(cur, numero='', periode='semaine'):
    query = """
        SELECT ID, NumeroVoyage, DateVoyage, Destination, Camion, Chauffeur
        FROM WEB_VOYAGES
        WHERE 1=1
    """
    params = []
    if numero:
        query += " AND NumeroVoyage LIKE ?"
        params.append(f"%{numero}%")
    start, end = _period_range_voyages(periode)
    if start is not None and end is not None:
        query += " AND DateVoyage >= ? AND DateVoyage <= ?"
        params.extend([start, end])
    query += " ORDER BY DateVoyage DESC, ID DESC"
    cur.execute(query, params)
    return cur.fetchall()


def render_projet6(section=None, open_section=None, **kwargs):
    allowed = get_projet6_allowed_sections()
    kwargs.setdefault('voyages', [])
    kwargs.setdefault('search_numero', '')
    kwargs.setdefault('search_periode', 'semaine')
    kwargs.setdefault('camions', [])
    kwargs.setdefault('camions_suivi', [])
    kwargs.setdefault('today', datetime.today().date())
    kwargs.setdefault('timedelta', timedelta)
    kwargs.setdefault('vidange_intervalle_km', VIDANGE_INTERVALLE_KM)
    kwargs.setdefault('vidange_intervalle_heures', VIDANGE_INTERVALLE_HEURES)
    kwargs.update(
        section=section,
        open_section=open_section,
        allowed_sections=allowed,
        is_super=is_super_user(),
    )
    return render_template('projet6.html', **kwargs)


@projet6_bp.route('/projet6', methods=['GET'])
@login_required
def programme_voyage():
    if not has_project_access(6) and not is_super_user():
        flash("Vous n'avez pas accès à ce projet.", "error")
        return redirect(url_for('index'))

    numero = (request.args.get('numero') or '').strip()
    periode = (request.args.get('periode') or 'semaine').strip().lower()
    if periode not in ('semaine', 'mois', 'historique'):
        periode = 'semaine'
    open_section = (request.args.get('section') or '').strip() or None

    with get_db_cursor() as cur:
        ensure_projet6_vidange_schema(cur)
        ensure_projet6_voyage_lignes_schema(cur)
        ensure_projet6_notification_schema(cur)
        sync_projet6_notifications(cur)
        cur.connection.commit()
        cur.execute("SELECT * FROM WEB_CAMIONS ORDER BY Immatriculation")
        camions = cur.fetchall()
        voyages = fetch_voyages(cur, numero=numero, periode=periode)
        camions_suivi = fetch_camions_suivi(cur)

    return render_projet6(
        camions=camions,
        camions_suivi=camions_suivi,
        voyages=voyages,
        search_numero=numero,
        search_periode=periode,
        open_section=open_section,
    )

@projet6_bp.route('/projet6/save', methods=['POST'])
@login_required
def save_programme():
    if not has_project_access(6) and not is_super_user():
        flash("Vous n'avez pas accès à ce projet.", "error")
        return redirect(url_for('index'))

    with get_db_cursor() as cur:
        ensure_projet6_voyage_lignes_schema(cur)
        date_voyage = request.form.get('date')
        destination = request.form.get('destination')
        camion = request.form.get('camion')
        chauffeur = request.form.get('chauffeur')

        lignes = []
        index = 0
        while True:
            client = (request.form.get(f'client_{index}') or '').strip()
            num_dossier = (request.form.get(f'num_dossier_{index}') or '').strip()
            article = request.form.get(f'article_{index}')
            quantite = request.form.get(f'quantite_{index}')
            pieces_par_carton = request.form.get(f'pieces_par_carton_{index}')
            cartons_par_palette = request.form.get(f'cartons_par_palette_{index}')
            nb_carton = request.form.get(f'nb_carton_{index}')
            nb_palette = request.form.get(f'nb_palette_{index}')
            termine = request.form.get(f'termine_{index}') == 'on'

            if not client and not num_dossier:
                break

            lignes.append({
                'Client': client,
                'NumDossier': num_dossier,
                'Article': article,
                'Quantite': quantite,
                'PiecesParCarton': pieces_par_carton,
                'CartonsParPalette': cartons_par_palette,
                'NbCarton': nb_carton,
                'NbPalette': nb_palette,
                'Termine': termine
            })
            index += 1

        try:
            # Numéro métier séquentiel (ex. 251) — plus de trigger/défaut en base
            cur.execute("""
                SELECT ISNULL(MAX(TRY_CAST(NumeroVoyage AS INT)), 0) + 1
                FROM WEB_VOYAGES WITH (UPDLOCK, HOLDLOCK)
            """)
            numero_voyage = str(cur.fetchone()[0])

            cur.execute("""
                INSERT INTO WEB_VOYAGES (DateVoyage, Destination, Camion, Chauffeur, NumeroVoyage)
                OUTPUT INSERTED.ID, INSERTED.NumeroVoyage
                VALUES (?, ?, ?, ?, ?)
            """, (date_voyage, destination, camion, chauffeur, numero_voyage))
            result = cur.fetchone()
            if not result:
                raise RuntimeError("Impossible de récupérer l'ID du voyage après insertion.")
            id_voyage = result[0]
            numero_voyage = result[1] or numero_voyage

            for ligne in lignes:
                cur.execute("""
                    INSERT INTO WEB_VOYAGE_LIGNES (
                        ID_VOYAGE, Client, NumDossier, Article, Quantite,
                        PiecesParCarton, CartonsParPalette, NbCarton,
                        NbPalette, Termine
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (id_voyage, ligne['Client'], ligne['NumDossier'], ligne['Article'], ligne['Quantite'],
                      ligne['PiecesParCarton'], ligne['CartonsParPalette'],
                      ligne['NbCarton'], ligne['NbPalette'], ligne['Termine']))

                if ligne['Termine']:
                    cur.execute("""
                        UPDATE COMMANDES
                        SET Termine = 1
                        WHERE LTRIM(RTRIM(CAST(Numero AS NVARCHAR(100)))) = ?
                    """, (ligne['NumDossier'],))

            cur.connection.commit()
            flash(f"Voyage n° {numero_voyage} enregistré avec succès.", "success")
            # PRG : évite la duplication au rafraîchissement ; formulaire vide
            return redirect(url_for('projet6.programme_voyage', section='nouveau_voyage'))

        except Exception as e:
            cur.connection.rollback()
            flash(f"Erreur lors de l'enregistrement : {e}", "danger")
            return redirect(url_for('projet6.programme_voyage', section='nouveau_voyage'))


@projet6_bp.route('/api/commandes')
def api_commandes():
    try:
        q = (request.args.get('q') or '').strip()
        if not q:
            return jsonify([])
        with get_db_cursor() as cur:
            like = f"%{q}%"
            # Exclure si COMMANDES.Termine=1 OU une ligne voyage Termine=1 (comparaison normalisée)
            cur.execute("""
                SELECT c.Numero, s.RaiSocTri as Client, c.QteComm, c.Reference
                FROM COMMANDES c
                LEFT JOIN SOCIETES s ON c.ID_SOCIETE = s.ID
                WHERE (
                    LTRIM(RTRIM(CAST(c.Numero AS NVARCHAR(100)))) COLLATE Latin1_General_CI_AI LIKE ?
                    OR ISNULL(s.RaiSocTri, '') COLLATE Latin1_General_CI_AI LIKE ?
                    OR ISNULL(c.Reference, '') COLLATE Latin1_General_CI_AI LIKE ?
                )
                AND ISNULL(c.Termine, 0) = 0
                AND NOT EXISTS (
                    SELECT 1
                    FROM WEB_VOYAGE_LIGNES vl
                    WHERE ISNULL(vl.Termine, 0) = 1
                      AND LTRIM(RTRIM(ISNULL(vl.NumDossier, '')))
                          = LTRIM(RTRIM(CAST(c.Numero AS NVARCHAR(100))))
                )
                ORDER BY c.Numero DESC
                OFFSET 0 ROWS FETCH NEXT 25 ROWS ONLY
            """, (like, like, like))

            rows = cur.fetchall()
            resultats = [
                {
                    "Numero": (str(row[0]).strip() if row[0] is not None else ""),
                    "Client": row[1],
                    "QteComm": row[2],
                    "Reference": row[3],
                }
                for row in rows
            ]
            return jsonify(resultats)
    except Exception as e:
        print("❌ Erreur dans /api/commandes :", e)
        return jsonify([]), 500


@projet6_bp.route('/projet6/api/notifications')
@login_required
def api_projet6_notifications():
    if not has_project_access(6) and not is_super_user():
        return jsonify({'error': 'Accès refusé'}), 403
    non_lues = request.args.get('non_lues') == '1'
    return jsonify(get_projet6_notifications(non_lues_seulement=non_lues))


@projet6_bp.route('/projet6/api/notifications/lire', methods=['POST'])
@login_required
def api_projet6_notifications_lire():
    if not has_project_access(6) and not is_super_user():
        return jsonify({'error': 'Accès refusé'}), 403
    data = request.get_json(silent=True) or {}
    marquer_projet6_notifications_lues(ids=data.get('ids'))
    return jsonify({'ok': True})


@projet6_bp.route('/projet6/api/notifications/<int:notif_id>/supprimer', methods=['POST'])
@login_required
def api_projet6_notification_supprimer(notif_id):
    if not has_project_access(6) and not is_super_user():
        return jsonify({'error': 'Accès refusé'}), 403
    ok = supprimer_projet6_notification(notif_id)
    if not ok:
        return jsonify({'error': 'Notification introuvable'}), 404
    return jsonify({'ok': True})


@projet6_bp.route('/projet6/voyages', methods=['GET'])
@login_required
def list_voyages():
    """Redirige vers la section Liste des voyages sur la page projet 6."""
    if not has_project_access(6) and not is_super_user():
        flash("Vous n'avez pas accès à ce projet.", "error")
        return redirect(url_for('index'))
    args = {'section': 'liste_voyages'}
    numero = (request.args.get('numero') or '').strip()
    periode = (request.args.get('periode') or 'semaine').strip().lower()
    if periode not in ('semaine', 'mois', 'historique'):
        periode = 'semaine'
    if numero:
        args['numero'] = numero
    args['periode'] = periode
    return redirect(url_for('projet6.programme_voyage', **args))


@projet6_bp.route('/projet6/voyage/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_voyage(id):
    if not has_project_access(6) and not is_super_user():
        flash("Vous n'avez pas accès à ce projet.", "error")
        return redirect(url_for('index'))

    with get_db_cursor() as cur:
        cur.execute("SELECT NumeroVoyage FROM WEB_VOYAGES WHERE ID = ?", (id,))
        row = cur.fetchone()
        if not row:
            flash("Voyage introuvable.", "danger")
            return redirect(url_for('projet6.programme_voyage', section='liste_voyages'))
        numero = row[0]
        try:
            cur.execute("DELETE FROM WEB_VOYAGE_LIGNES WHERE ID_VOYAGE = ?", (id,))
            cur.execute("DELETE FROM WEB_VOYAGES WHERE ID = ?", (id,))
            cur.connection.commit()
            flash(f"Voyage {numero} supprimé avec succès.", "success")
        except Exception as e:
            cur.connection.rollback()
            flash(f"Impossible de supprimer le voyage : {e}", "danger")

    return redirect(url_for('projet6.programme_voyage', section='liste_voyages'))


@projet6_bp.route('/projet6/edit/<int:id>', methods=['GET', 'POST'])
def edit_voyage(id):
    with get_db_cursor() as cur:
        ensure_projet6_voyage_lignes_schema(cur)
        if request.method == 'GET':
            cur.execute("SELECT ID, NumeroVoyage, DateVoyage, Destination, Camion, Chauffeur FROM WEB_VOYAGES WHERE ID = ?", (id,))
            voyage = cur.fetchone()
            if not voyage:
                flash("Voyage introuvable", "danger")
                return redirect(url_for('projet6.list_voyages'))

            cur.execute("""
                SELECT ID_LIGNE, Client, NumDossier, Article, Quantite, PiecesParCarton, CartonsParPalette, NbCarton, NbPalette, Termine
                FROM WEB_VOYAGE_LIGNES WHERE ID_VOYAGE = ? ORDER BY ID_LIGNE
            """, (id,))
            lignes = cur.fetchall()

            cur.execute("SELECT * FROM WEB_CAMIONS")
            camions = cur.fetchall()

            return render_template('edit_voyage.html', voyage=voyage, lignes=lignes, camions=camions)

        else:
            date_voyage = request.form.get('date')
            destination = request.form.get('destination')
            camion = request.form.get('camion')
            chauffeur = request.form.get('chauffeur')

            try:
                cur.execute("""
                    UPDATE WEB_VOYAGES SET DateVoyage=?, Destination=?, Camion=?, Chauffeur=? WHERE ID=?
                """, (date_voyage, destination, camion, chauffeur, id))

                cur.execute("DELETE FROM WEB_VOYAGE_LIGNES WHERE ID_VOYAGE = ?", (id,))

                nb_lignes = int(request.form.get('nb_lignes'))
                for index in range(nb_lignes):
                    client = (request.form.get(f'client_{index}') or '').strip()
                    num_dossier = (request.form.get(f'num_dossier_{index}') or '').strip()
                    article = request.form.get(f'article_{index}')
                    quantite = request.form.get(f'quantite_{index}')
                    pieces_par_carton = request.form.get(f'pieces_par_carton_{index}')
                    cartons_par_palette = request.form.get(f'cartons_par_palette_{index}')
                    nb_carton = request.form.get(f'nb_carton_{index}')
                    nb_palette = request.form.get(f'nb_palette_{index}')
                    termine = request.form.get(f'termine_{index}') == 'on'

                    cur.execute("""
                        INSERT INTO WEB_VOYAGE_LIGNES (ID_VOYAGE, Client, NumDossier, Article, Quantite,
                            PiecesParCarton, CartonsParPalette, NbCarton, NbPalette, Termine)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (id, client, num_dossier, article, quantite, pieces_par_carton, cartons_par_palette, nb_carton, nb_palette, termine))

                    if termine and num_dossier:
                        cur.execute("""
                            UPDATE COMMANDES
                            SET Termine = 1
                            WHERE LTRIM(RTRIM(CAST(Numero AS NVARCHAR(100)))) = ?
                        """, (num_dossier,))

                cur.connection.commit()
                flash("Voyage mis à jour avec succès.", "success")
                return redirect(url_for('projet6.programme_voyage', section='liste_voyages'))

            except Exception as e:
                cur.connection.rollback()
                flash(f"Erreur de mise à jour : {e}", "danger")
                return redirect(url_for('projet6.edit_voyage', id=id))

def get_camions(cur):
    cur.execute("SELECT * FROM WEB_CAMIONS")
    return cur.fetchall()


def fetch_camions_suivi(cur):
    ensure_projet6_vidange_schema(cur)
    cur.execute("""
        SELECT
            c.ID,
            c.Immatriculation,
            c.Marque,
            c.Modele,
            c.DateAchat,
            c.DateVisiteTechnique,
            c.DateProchaineVisiteTechnique,
            c.Observations,
            c.KmActuel,
            c.HeuresActuelles,
            c.ModeSuiviVidange,
            v.DateVidange AS DateDerniereVidange,
            v.Km AS KmDerniereVidange,
            v.Heures AS HeuresDerniereVidange
        FROM WEB_CAMIONS c
        OUTER APPLY (
            SELECT TOP 1 DateVidange, Km, Heures
            FROM WEB_CAMION_VIDANGES
            WHERE ID_Camion = c.ID
            ORDER BY DateVidange DESC, ID DESC
        ) v
        ORDER BY c.Immatriculation
    """)
    return [_build_camion_suivi_row(row) for row in cur.fetchall()]


def fetch_vidanges(cur, id_camion, limit=20):
    limit = max(1, min(int(limit), 100))
    cur.execute(f"""
        SELECT TOP {limit} ID, DateVidange, Km, Heures, Remarque, CreeLe
        FROM WEB_CAMION_VIDANGES
        WHERE ID_Camion = ?
        ORDER BY DateVidange DESC, ID DESC
    """, (id_camion,))
    rows = []
    for r in cur.fetchall():
        rows.append({
            'id': r.ID,
            'date': _coerce_camion_date(r.DateVidange),
            'km': r.Km,
            'heures': getattr(r, 'Heures', None),
            'remarque': r.Remarque or '',
            'cree_le': r.CreeLe,
        })
    return rows


def _coerce_camion_date(value):
    """Normalise les champs date SQL pour le template (comparaisons en date)."""
    from datetime import date as date_cls
    if value is None:
        return None
    if isinstance(value, datetime):
        value = value.date()
    elif isinstance(value, date_cls):
        pass
    elif isinstance(value, str):
        try:
            value = datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    else:
        return None
    # Dates sentinelles / placeholders SQL (ex. 1900-01-01)
    if value.year <= 1900:
        return None
    return value

@projet6_bp.route('/projet6/ajouter-camion', methods=['GET', 'POST'])
@login_required
def ajouter_camion():
    if not has_project_access(6) and not is_super_user():
        flash("Vous n'avez pas accès à ce projet.", "error")
        return redirect(url_for('index'))

    with get_db_cursor() as cur:
        ensure_projet6_vidange_schema(cur)
        cur.connection.commit()
        if request.method == 'POST':
            immat = request.form.get('immat')
            marque = request.form.get('marque')
            modele = request.form.get('modele')
            date_achat = request.form.get('date_achat') or None
            mode = _normalize_mode_vidange(request.form.get('mode_suivi_vidange'))
            try:
                cur.execute("""
                    INSERT INTO WEB_CAMIONS (Immatriculation, Marque, Modele, DateAchat, ModeSuiviVidange)
                    VALUES (?, ?, ?, ?, ?)
                """, (immat, marque, modele, date_achat, mode))
                cur.connection.commit()
                flash("Camion ajouté avec succès", "success")
                return redirect(url_for('projet6.programme_voyage', section='gestion_vehicules'))
            except Exception as e:
                cur.connection.rollback()
                flash(f"Erreur : {e}", "danger")

        return render_template(
            'ajouter_camion.html',
            vidange_intervalle_km=VIDANGE_INTERVALLE_KM,
            vidange_intervalle_heures=VIDANGE_INTERVALLE_HEURES,
        )


@projet6_bp.route('/projet6/camions', methods=['GET'])
@login_required
def liste_camions():
    return redirect(url_for('projet6.programme_voyage', section='gestion_vehicules'))

@projet6_bp.route('/projet6/camion/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_camion(id):
    if not has_project_access(6) and not is_super_user():
        flash("Vous n'avez pas accès à ce projet.", "error")
        return redirect(url_for('index'))

    with get_db_cursor() as cur:
        ensure_projet6_vidange_schema(cur)
        cur.connection.commit()

        cur.execute("""
            SELECT ID, Immatriculation, Marque, Modele, DateAchat,
                   DateVisiteTechnique, DateProchaineVisiteTechnique,
                   Observations, KmActuel, HeuresActuelles, ModeSuiviVidange
            FROM WEB_CAMIONS WHERE ID = ?
        """, (id,))
        row = cur.fetchone()
        if not row:
            flash("Véhicule introuvable.", "danger")
            return redirect(url_for('projet6.programme_voyage', section='gestion_vehicules'))

        mode = _normalize_mode_vidange(row.ModeSuiviVidange)

        if request.method == 'POST':
            visite_derniere = request.form.get('date_derniere_visite') or None
            visite_prochaine = request.form.get('date_prochaine_visite') or None
            observations = request.form.get('observations')
            km_actuel = _parse_int_or_none(request.form.get('km_actuel'))
            heures_actuelles = _parse_int_or_none(request.form.get('heures_actuelles'))

            try:
                if mode == MODE_VIDANGE_HEURES:
                    cur.execute("""
                        UPDATE WEB_CAMIONS
                        SET DateVisiteTechnique = ?, DateProchaineVisiteTechnique = ?,
                            Observations = ?, HeuresActuelles = ?
                        WHERE ID = ?
                    """, (visite_derniere, visite_prochaine, observations, heures_actuelles, id))
                else:
                    cur.execute("""
                        UPDATE WEB_CAMIONS
                        SET DateVisiteTechnique = ?, DateProchaineVisiteTechnique = ?,
                            Observations = ?, KmActuel = ?
                        WHERE ID = ?
                    """, (visite_derniere, visite_prochaine, observations, km_actuel, id))
                cur.connection.commit()
                flash("Camion mis à jour avec succès", "success")
                return redirect(url_for('projet6.programme_voyage', section='gestion_vehicules'))
            except Exception as e:
                cur.connection.rollback()
                flash(f"Erreur : {e}", "danger")

        camion = {
            'id': row.ID,
            'immatriculation': row.Immatriculation,
            'marque': row.Marque,
            'modele': row.Modele,
            'date_achat': _format_date_input(row.DateAchat),
            'date_derniere_visite': _format_date_input(row.DateVisiteTechnique),
            'date_prochaine_visite': _format_date_input(row.DateProchaineVisiteTechnique),
            'observations': row.Observations or '',
            'km_actuel': row.KmActuel,
            'heures_actuelles': row.HeuresActuelles,
            'mode_suivi_vidange': mode,
        }
        vidanges = fetch_vidanges(cur, id)
        derniere = vidanges[0] if vidanges else None
        if mode == MODE_VIDANGE_HEURES:
            unite = 'h'
            intervalle = VIDANGE_INTERVALLE_HEURES
            compteur_prochain = (
                int(derniere['heures']) + intervalle
                if derniere and derniere.get('heures') is not None else None
            )
            compteur_actuel_prefill = camion['heures_actuelles']
        else:
            unite = 'km'
            intervalle = VIDANGE_INTERVALLE_KM
            compteur_prochain = (
                int(derniere['km']) + intervalle
                if derniere and derniere.get('km') is not None else None
            )
            compteur_actuel_prefill = camion['km_actuel']

    return render_template(
        'edit_camion.html',
        camion=camion,
        vidanges=vidanges,
        mode_suivi_vidange=mode,
        unite_vidange=unite,
        intervalle_vidange=intervalle,
        compteur_prochain=compteur_prochain,
        compteur_actuel_prefill=compteur_actuel_prefill,
        vidange_intervalle_km=VIDANGE_INTERVALLE_KM,
        vidange_intervalle_heures=VIDANGE_INTERVALLE_HEURES,
        today=_format_date_input(datetime.today().date()),
    )


@projet6_bp.route('/projet6/camion/<int:id>/vidange', methods=['POST'])
@login_required
def enregistrer_vidange(id):
    if not has_project_access(6) and not is_super_user():
        flash("Vous n'avez pas accès à ce projet.", "error")
        return redirect(url_for('index'))

    date_vidange = (request.form.get('date_vidange') or '').strip()
    compteur_raw = (request.form.get('compteur_vidange') or '').strip()
    remarque = (request.form.get('remarque_vidange') or '').strip() or None

    if not date_vidange or not compteur_raw.isdigit():
        flash("Date et compteur de vidange obligatoires.", "danger")
        return redirect(url_for('projet6.edit_camion', id=id))

    compteur = int(compteur_raw)

    with get_db_cursor() as cur:
        ensure_projet6_vidange_schema(cur)
        cur.execute("""
            SELECT ID, KmActuel, HeuresActuelles, ModeSuiviVidange
            FROM WEB_CAMIONS WHERE ID = ?
        """, (id,))
        row = cur.fetchone()
        if not row:
            flash("Véhicule introuvable.", "danger")
            return redirect(url_for('projet6.programme_voyage', section='gestion_vehicules'))

        mode = _normalize_mode_vidange(row.ModeSuiviVidange)
        try:
            if mode == MODE_VIDANGE_HEURES:
                cur.execute("""
                    INSERT INTO WEB_CAMION_VIDANGES (ID_Camion, DateVidange, Km, Heures, Remarque)
                    VALUES (?, ?, NULL, ?, ?)
                """, (id, date_vidange, compteur, remarque))
                cur.execute("""
                    UPDATE WEB_CAMIONS
                    SET HeuresActuelles = CASE
                        WHEN HeuresActuelles IS NULL OR HeuresActuelles < ? THEN ?
                        ELSE HeuresActuelles
                    END
                    WHERE ID = ?
                """, (compteur, compteur, id))
                flash(f"Vidange enregistrée ({compteur} h).", "success")
            else:
                cur.execute("""
                    INSERT INTO WEB_CAMION_VIDANGES (ID_Camion, DateVidange, Km, Heures, Remarque)
                    VALUES (?, ?, ?, NULL, ?)
                """, (id, date_vidange, compteur, remarque))
                cur.execute("""
                    UPDATE WEB_CAMIONS
                    SET KmActuel = CASE
                        WHEN KmActuel IS NULL OR KmActuel < ? THEN ?
                        ELSE KmActuel
                    END
                    WHERE ID = ?
                """, (compteur, compteur, id))
                flash(f"Vidange enregistrée ({compteur} km).", "success")
            cur.connection.commit()
        except Exception as e:
            cur.connection.rollback()
            flash(f"Impossible d'enregistrer la vidange : {e}", "danger")

    return redirect(url_for('projet6.edit_camion', id=id))


@projet6_bp.route('/projet6/camion/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_camion(id):
    if not has_project_access(6) and not is_super_user():
        flash("Vous n'avez pas accès à ce projet.", "error")
        return redirect(url_for('index'))

    with get_db_cursor() as cur:
        ensure_projet6_vidange_schema(cur)
        cur.execute("SELECT Immatriculation FROM WEB_CAMIONS WHERE ID = ?", (id,))
        row = cur.fetchone()
        if not row:
            flash("Véhicule introuvable.", "danger")
            return redirect(url_for('projet6.programme_voyage', section='gestion_vehicules'))
        immat = row[0]
        try:
            cur.execute("DELETE FROM WEB_CAMION_VIDANGES WHERE ID_Camion = ?", (id,))
            cur.execute("DELETE FROM WEB_CAMIONS WHERE ID = ?", (id,))
            cur.connection.commit()
            flash(f"Véhicule {immat} supprimé avec succès.", "success")
        except Exception as e:
            cur.connection.rollback()
            flash(f"Impossible de supprimer : {e}", "danger")

    return redirect(url_for('projet6.programme_voyage', section='gestion_vehicules'))


@projet6_bp.route('/api/camions', methods=['GET'])
def api_camions():
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT Immatriculation, Marque, Modele
            FROM WEB_CAMIONS
            ORDER BY Immatriculation
        """)
        rows = cur.fetchall()
    return jsonify([
        {"immat": r[0], "marque": r[1], "modele": r[2]} for r in rows
    ])
from flask import make_response, render_template



if PDFKIT_AVAILABLE:
    try:
        config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    except Exception:
        config = None
else:
    config = None

@projet6_bp.route('/projet6/pdf/<int:id>')
def export_pdf(id):
    if not PDFKIT_AVAILABLE or config is None:
        flash("Export PDF non disponible : pdfkit n'est pas installé ou wkhtmltopdf n'est pas configuré.", "danger")
        return redirect(url_for('projet6.programme_voyage'))
    with get_db_cursor() as cur:
        ensure_projet6_voyage_lignes_schema(cur)
        cur.execute("SELECT NumeroVoyage, DateVoyage, Destination, Camion, Chauffeur FROM WEB_VOYAGES WHERE ID = ?", (id,))
        voyage_data = cur.fetchone()

        if not voyage_data:
            flash("Voyage introuvable.", "danger")
            return redirect(url_for('projet6.programme_voyage'))

        voyage = {
            "NumeroVoyage": voyage_data[0],
            "DateVoyage": voyage_data[1],
            "Destination": voyage_data[2],
            "Camion": voyage_data[3],
            "Chauffeur": voyage_data[4]
        }

        cur.execute("""
            SELECT Client, NumDossier, Article, Quantite, PiecesParCarton,
                   CartonsParPalette, NbCarton, NbPalette, Termine
            FROM WEB_VOYAGE_LIGNES
            WHERE ID_VOYAGE = ?
        """, (id,))
        lignes_data = cur.fetchall()

        lignes = [{
            "Client": ligne[0],
            "NumDossier": ligne[1],
            "Article": ligne[2],
            "Quantite": ligne[3],
            "PiecesParCarton": ligne[4],
            "CartonsParPalette": ligne[5],
            "NbCarton": ligne[6],
            "NbPalette": ligne[7],
            "Termine": bool(ligne[8])
        } for ligne in lignes_data]

    rendered = render_template("programme_pdf.html", voyage=voyage, lignes=lignes)
    options = {'enable-local-file-access': None, 'quiet': ''}
    pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=programme_voyage_{voyage['NumeroVoyage']}.pdf"
    return response
