# -*- coding: utf-8 -*-
"""
Projet 29 – Suivi des connexions.
Présence = au moins un onglet encore ouvert (heartbeat + fermeture d'onglet).
"""
from datetime import datetime

from db import get_db_cursor

NUM_PROJ = 29
NOM_PROJ = 'Suivi des connexions'
CODE_PROJ = 'Projet 29'

# Délai après pagehide avant de retirer l'onglet (évite de couper l'historique au changement de page).
CLOSING_SECONDS = 20
# Filet de sécurité si l'onglet crash / le réseau coupe (timers d'onglet masqué ~1 min).
STALE_SECONDS = 120
HISTORY_DAYS = 7
_tables_ready = False

PAGE_LABELS = {
    '/': 'Accueil',
    '/auth/login': 'Connexion',
    '/auth/logout': 'Déconnexion',
    '/projet1': 'Planning',
    '/projet2': 'Commandes',
    '/projet3': 'Suivi BAT',
    '/projet4': 'Rapport de Visite',
    '/projet5': 'Planning Production',
    '/projet6': 'Transport & Logistique',
    '/import_facture': 'Factures STEG',
    '/projet7': 'Factures STEG',
    '/projet8': 'Stats',
    '/projet9': 'Performance',
    '/projet10': 'Qualité',
    '/projet11': 'Traitements',
    '/projet12': 'NC & Réclamations',
    '/projet13': 'Suivi Production',
    '/projet14': 'Déchets',
    '/projet15': 'Corrélation',
    '/projet16': 'GMAO',
    '/projet17': 'Fusion HTML',
    '/projet18': 'Agenda 2026',
    '/projet19': 'Dossiers en Cours',
    '/projet20': 'Analyse Dossiers',
    '/projet21': 'Sync BDD',
    '/projet22': 'Employés et Ateliers',
    '/projet23': 'Trésorerie',
    '/projet24': 'Formes de Découpe',
    '/projet25': 'Congés et autorisations',
    '/projet26': 'Gestion des formations',
    '/projet27': 'Crédit Leasing',
    '/projet28': 'Codes-barres MP',
    '/projet29': 'Suivi des connexions',
}


def ensure_projet29_in_web_projets():
    try:
        with get_db_cursor() as cursor:
            cursor.execute('SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = ?', (NUM_PROJ,))
            if cursor.fetchone():
                return
            cursor.execute(
                """
                INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive)
                VALUES (?, ?, ?, 0)
                """,
                (NUM_PROJ, CODE_PROJ, NOM_PROJ),
            )
            cursor.connection.commit()
            print('[Projet 29] WEB_PROJETS ajouté.')
    except Exception as e:
        print(f'[Projet 29] ensure_projet29_in_web_projets: {e}')


def init_presence_tables():
    global _tables_ready
    if _tables_ready:
        return
    with get_db_cursor() as cursor:
        cursor.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_PRESENCE_ONGLETS'
            )
            BEGIN
                CREATE TABLE dbo.WEB_PRESENCE_ONGLETS (
                    ID            INT IDENTITY(1,1) NOT NULL,
                    UserKey       NVARCHAR(40)  NOT NULL,
                    Matricule     INT           NULL,
                    AtelierId     INT           NULL,
                    Nom           NVARCHAR(200) NOT NULL,
                    TypeUser      NVARCHAR(20)  NOT NULL,
                    TabId         NVARCHAR(64)  NOT NULL,
                    ConnectedAt   DATETIME2(0)  NOT NULL,
                    LastSeen      DATETIME2(0)  NOT NULL,
                    Closing       TINYINT       NOT NULL CONSTRAINT DF_WEB_PRESENCE_Closing DEFAULT 0,
                    PagePath      NVARCHAR(500) NULL,
                    PageLabel     NVARCHAR(200) NULL,
                    Ip            NVARCHAR(45)  NULL,
                    UserAgent     NVARCHAR(500) NULL,
                    HistoId       INT           NULL,
                    CONSTRAINT PK_WEB_PRESENCE_ONGLETS PRIMARY KEY (ID),
                    CONSTRAINT UQ_WEB_PRESENCE_TabId UNIQUE (TabId)
                );
                CREATE INDEX IX_WEB_PRESENCE_UserKey ON dbo.WEB_PRESENCE_ONGLETS (UserKey);
                CREATE INDEX IX_WEB_PRESENCE_LastSeen ON dbo.WEB_PRESENCE_ONGLETS (LastSeen);
            END
        """)
        cursor.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_CONNEXIONS_HISTO'
            )
            BEGIN
                CREATE TABLE dbo.WEB_CONNEXIONS_HISTO (
                    ID              INT IDENTITY(1,1) NOT NULL,
                    UserKey         NVARCHAR(40)  NOT NULL,
                    Matricule       INT           NULL,
                    AtelierId       INT           NULL,
                    Nom             NVARCHAR(200) NOT NULL,
                    TypeUser        NVARCHAR(20)  NOT NULL,
                    ConnectedAt     DATETIME2(0)  NOT NULL,
                    DisconnectedAt  DATETIME2(0)  NULL,
                    LastPage        NVARCHAR(200) NULL,
                    Ip              NVARCHAR(45)  NULL,
                    UserAgent       NVARCHAR(500) NULL,
                    NbOngletsMax    INT           NOT NULL CONSTRAINT DF_WEB_CONN_NbOnglets DEFAULT 1,
                    CONSTRAINT PK_WEB_CONNEXIONS_HISTO PRIMARY KEY (ID)
                );
                CREATE INDEX IX_WEB_CONN_UserKey ON dbo.WEB_CONNEXIONS_HISTO (UserKey, DisconnectedAt);
                CREATE INDEX IX_WEB_CONN_ConnectedAt ON dbo.WEB_CONNEXIONS_HISTO (ConnectedAt);
            END
        """)
        cursor.connection.commit()
    _tables_ready = True


def _dt_iso(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%dT%H:%M:%S')
    return str(val)


def parse_user_agent(ua):
    ua = ua or ''
    if 'Edg/' in ua:
        browser = 'Edge'
    elif 'OPR/' in ua or 'Opera' in ua:
        browser = 'Opera'
    elif 'Chrome/' in ua:
        browser = 'Chrome'
    elif 'Firefox/' in ua:
        browser = 'Firefox'
    elif 'Safari/' in ua:
        browser = 'Safari'
    else:
        browser = 'Navigateur'
    if 'Windows' in ua:
        os_name = 'Windows'
    elif 'Android' in ua:
        os_name = 'Android'
    elif 'iPhone' in ua or 'iPad' in ua:
        os_name = 'iOS'
    elif 'Mac OS' in ua:
        os_name = 'macOS'
    elif 'Linux' in ua:
        os_name = 'Linux'
    else:
        os_name = ''
    return f'{browser} / {os_name}' if os_name else browser


def page_label_from_path(path, title=None):
    path = (path or '/').strip() or '/'
    if '?' in path:
        path = path.split('?', 1)[0]
    if path != '/':
        path = path.rstrip('/') or '/'
    if path in PAGE_LABELS:
        return PAGE_LABELS[path]
    if path.startswith('/accueil/'):
        return 'Catégorie accueil'
    parts = [p for p in path.split('/') if p]
    if parts:
        prefix = '/' + parts[0]
        if prefix in PAGE_LABELS:
            return PAGE_LABELS[prefix]
        if parts[0].startswith('projet') and parts[0][6:].isdigit():
            return PAGE_LABELS.get('/' + parts[0], parts[0])
    title = (title or '').strip()
    if title and 'Portail Novaprint' not in title:
        return title.split('–')[0].split('-')[0].strip() or path
    return path


def identity_from_session(flask_session):
    is_atelier = bool(
        flask_session.get('is_atelier')
        or flask_session.get('atelier_id') is not None
        or (flask_session.get('atelier_nom') and flask_session.get('matricule') is None)
    )
    if is_atelier:
        atelier_id = flask_session.get('atelier_id')
        nom = (
            flask_session.get('atelier_nom')
            or flask_session.get('nom')
            or 'Atelier'
        )
        nom = str(nom).strip() or 'Atelier'
        if atelier_id is not None:
            user_key = f'a:{atelier_id}'
        else:
            user_key = f'an:{nom.lower()}'
        return {
            'user_key': user_key[:40],
            'matricule': None,
            'atelier_id': atelier_id,
            'nom': nom[:200],
            'type_user': 'atelier',
        }
    matricule = flask_session.get('matricule')
    nom = (flask_session.get('nom') or '').strip() or f'Matricule {matricule}'
    return {
        'user_key': f'm:{matricule}'[:40],
        'matricule': matricule,
        'atelier_id': None,
        'nom': nom[:200],
        'type_user': 'employe',
    }


def _open_or_get_histo(cursor, ident, ip, ua_label, page_label):
    cursor.execute(
        """
        SELECT TOP 1 ID FROM dbo.WEB_CONNEXIONS_HISTO
        WHERE UserKey = ? AND DisconnectedAt IS NULL
        ORDER BY ConnectedAt DESC
        """,
        (ident['user_key'],),
    )
    row = cursor.fetchone()
    if row:
        histo_id = row[0]
        cursor.execute(
            """
            UPDATE dbo.WEB_CONNEXIONS_HISTO
            SET Nom = ?, LastPage = ?, Ip = ?, UserAgent = ?
            WHERE ID = ?
            """,
            (ident['nom'], page_label, ip, ua_label, histo_id),
        )
        return histo_id
    cursor.execute(
        """
        INSERT INTO dbo.WEB_CONNEXIONS_HISTO
            (UserKey, Matricule, AtelierId, Nom, TypeUser, ConnectedAt, LastPage, Ip, UserAgent, NbOngletsMax)
        VALUES (?, ?, ?, ?, ?, SYSDATETIME(), ?, ?, ?, 1)
        """,
        (
            ident['user_key'],
            ident['matricule'],
            ident['atelier_id'],
            ident['nom'],
            ident['type_user'],
            page_label,
            ip,
            ua_label,
        ),
    )
    cursor.execute('SELECT CAST(SCOPE_IDENTITY() AS INT)')
    return cursor.fetchone()[0]


def _refresh_onglets_max(cursor, user_key, histo_id):
    cursor.execute(
        'SELECT COUNT(*) FROM dbo.WEB_PRESENCE_ONGLETS WHERE UserKey = ?',
        (user_key,),
    )
    n = cursor.fetchone()[0] or 1
    cursor.execute(
        """
        UPDATE dbo.WEB_CONNEXIONS_HISTO
        SET NbOngletsMax = CASE WHEN NbOngletsMax < ? THEN ? ELSE NbOngletsMax END
        WHERE ID = ?
        """,
        (n, n, histo_id),
    )


def cleanup_presence(cursor=None):
    """Retire les onglets fermés / inactifs et clôture l'historique associé."""

    def _run(cur):
        cur.execute(
            """
            DELETE FROM dbo.WEB_PRESENCE_ONGLETS
            WHERE (Closing = 1 AND LastSeen < DATEADD(SECOND, ?, SYSDATETIME()))
               OR LastSeen < DATEADD(SECOND, ?, SYSDATETIME())
            """,
            (-CLOSING_SECONDS, -STALE_SECONDS),
        )
        cur.execute(
            """
            UPDATE h
            SET DisconnectedAt = SYSDATETIME()
            FROM dbo.WEB_CONNEXIONS_HISTO h
            WHERE h.DisconnectedAt IS NULL
              AND NOT EXISTS (
                  SELECT 1 FROM dbo.WEB_PRESENCE_ONGLETS p
                  WHERE p.UserKey = h.UserKey
              )
            """
        )
        cur.execute(
            """
            DELETE FROM dbo.WEB_CONNEXIONS_HISTO
            WHERE DisconnectedAt IS NOT NULL
              AND DisconnectedAt < DATEADD(DAY, ?, SYSDATETIME())
            """,
            (-HISTORY_DAYS,),
        )

    if cursor is not None:
        _run(cursor)
        return
    with get_db_cursor() as cur:
        _run(cur)
        cur.connection.commit()


def heartbeat(ident, tab_id, page_path, page_title, ip, user_agent):
    tab_id = (tab_id or '').strip()[:64]
    if not tab_id:
        return {'ok': False, 'error': 'tab_id manquant'}
    page_path = (page_path or '/').strip()
    if page_path.startswith('http://') or page_path.startswith('https://'):
        from urllib.parse import urlparse
        parsed = urlparse(page_path)
        page_path = (parsed.path or '/') + (('?' + parsed.query) if parsed.query else '')
    page_path = page_path[:500]
    page_label = page_label_from_path(page_path, page_title)[:200]
    ua_label = parse_user_agent(user_agent)[:500]
    ip = (ip or '')[:45]
    init_presence_tables()
    with get_db_cursor() as cursor:
        cleanup_presence(cursor)
        histo_id = _open_or_get_histo(cursor, ident, ip, ua_label, page_label)
        cursor.execute(
            'SELECT ID FROM dbo.WEB_PRESENCE_ONGLETS WHERE TabId = ?',
            (tab_id,),
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE dbo.WEB_PRESENCE_ONGLETS
                SET UserKey = ?, Matricule = ?, AtelierId = ?, Nom = ?, TypeUser = ?,
                    LastSeen = SYSDATETIME(), Closing = 0,
                    PagePath = ?, PageLabel = ?, Ip = ?, UserAgent = ?, HistoId = ?
                WHERE TabId = ?
                """,
                (
                    ident['user_key'], ident['matricule'], ident['atelier_id'],
                    ident['nom'], ident['type_user'],
                    page_path, page_label, ip, ua_label, histo_id, tab_id,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO dbo.WEB_PRESENCE_ONGLETS
                    (UserKey, Matricule, AtelierId, Nom, TypeUser, TabId,
                     ConnectedAt, LastSeen, Closing, PagePath, PageLabel, Ip, UserAgent, HistoId)
                VALUES (?, ?, ?, ?, ?, ?, SYSDATETIME(), SYSDATETIME(), 0, ?, ?, ?, ?, ?)
                """,
                (
                    ident['user_key'], ident['matricule'], ident['atelier_id'],
                    ident['nom'], ident['type_user'], tab_id,
                    page_path, page_label, ip, ua_label, histo_id,
                ),
            )
        _refresh_onglets_max(cursor, ident['user_key'], histo_id)
        cursor.connection.commit()
    return {'ok': True}


def mark_tab_closing(tab_id, ident=None):
    tab_id = (tab_id or '').strip()[:64]
    if not tab_id:
        return {'ok': False}
    init_presence_tables()
    with get_db_cursor() as cursor:
        if ident:
            cursor.execute(
                """
                UPDATE dbo.WEB_PRESENCE_ONGLETS
                SET Closing = 1, LastSeen = SYSDATETIME()
                WHERE TabId = ? AND UserKey = ?
                """,
                (tab_id, ident['user_key']),
            )
        else:
            cursor.execute(
                """
                UPDATE dbo.WEB_PRESENCE_ONGLETS
                SET Closing = 1, LastSeen = SYSDATETIME()
                WHERE TabId = ?
                """,
                (tab_id,),
            )
        cursor.connection.commit()
    return {'ok': True}


def list_connected():
    init_presence_tables()
    with get_db_cursor() as cursor:
        cleanup_presence(cursor)
        cursor.connection.commit()
        cursor.execute(
            """
            SELECT
                UserKey, Matricule, AtelierId, Nom, TypeUser,
                MIN(ConnectedAt) AS ConnectedAt,
                MAX(LastSeen) AS LastSeen,
                COUNT(*) AS NbOnglets
            FROM dbo.WEB_PRESENCE_ONGLETS
            GROUP BY UserKey, Matricule, AtelierId, Nom, TypeUser
            ORDER BY MAX(LastSeen) DESC
            """
        )
        groups = cursor.fetchall()
        result = []
        for g in groups:
            cursor.execute(
                """
                SELECT TOP 1 PageLabel, PagePath, Ip, UserAgent
                FROM dbo.WEB_PRESENCE_ONGLETS
                WHERE UserKey = ?
                ORDER BY LastSeen DESC
                """,
                (g.UserKey,),
            )
            detail = cursor.fetchone()
            result.append({
                'user_key': g.UserKey,
                'matricule': g.Matricule,
                'atelier_id': g.AtelierId,
                'nom': g.Nom,
                'type_user': g.TypeUser,
                'connected_at': _dt_iso(g.ConnectedAt),
                'last_seen': _dt_iso(g.LastSeen),
                'nb_onglets': int(g.NbOnglets or 1),
                'page': (detail.PageLabel if detail else None) or '',
                'page_path': (detail.PagePath if detail else None) or '',
                'ip': (detail.Ip if detail else None) or '',
                'navigateur': (detail.UserAgent if detail else None) or '',
            })
        return result


def list_history(limit=300):
    init_presence_tables()
    with get_db_cursor() as cursor:
        cleanup_presence(cursor)
        cursor.connection.commit()
        limit = max(1, min(int(limit or 300), 500))
        cursor.execute(
            f"""
            SELECT TOP ({limit})
                ID, UserKey, Matricule, AtelierId, Nom, TypeUser,
                ConnectedAt, DisconnectedAt, LastPage, Ip, UserAgent, NbOngletsMax
            FROM dbo.WEB_CONNEXIONS_HISTO
            WHERE ConnectedAt >= DATEADD(DAY, ?, SYSDATETIME())
            ORDER BY ConnectedAt DESC
            """,
            (-HISTORY_DAYS,),
        )
        rows = []
        for r in cursor.fetchall():
            debut = r.ConnectedAt
            fin = r.DisconnectedAt
            duree_s = None
            if debut:
                end = fin or datetime.now()
                try:
                    if getattr(debut, 'tzinfo', None) and getattr(end, 'tzinfo', None) is None:
                        end = end.replace(tzinfo=debut.tzinfo)
                    elif getattr(end, 'tzinfo', None) and getattr(debut, 'tzinfo', None) is None:
                        debut = debut.replace(tzinfo=end.tzinfo)
                    duree_s = max(0, int((end - debut).total_seconds()))
                except Exception:
                    duree_s = None
            rows.append({
                'id': r.ID,
                'matricule': r.Matricule,
                'atelier_id': r.AtelierId,
                'nom': r.Nom,
                'type_user': r.TypeUser,
                'connected_at': _dt_iso(r.ConnectedAt),
                'disconnected_at': _dt_iso(r.DisconnectedAt),
                'en_cours': r.DisconnectedAt is None,
                'duree_secondes': duree_s,
                'page': r.LastPage or '',
                'ip': r.Ip or '',
                'navigateur': r.UserAgent or '',
                'nb_onglets_max': int(r.NbOngletsMax or 1),
            })
        return rows
