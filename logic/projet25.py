# -*- coding: utf-8 -*-
"""
Projet 25 – Gestion des congés et autorisations de sortie.
"""
import os
from datetime import datetime, date, time, timedelta

from db import get_db_cursor
from logic.projet25_email import send_email

# Matricule RH (CHAARI ISLEM)
MATRICULE_RH = 366
# E-mails fixes RH (notifications nouvelles demandes de congé) — séparés par des virgules
_EMAIL_RH_DEFAULT = 'grh@novaprint.tn,ameni.compta@novaprint.tn'
EMAILS_RH_NOTIF = [
    a.strip()
    for a in (os.environ.get('PROJET25_EMAIL_RH') or _EMAIL_RH_DEFAULT).split(',')
    if a.strip()
]
NUM_PROJ = 25
DELAI_MIN_HEURES = 24
UPLOAD_SUBDIR = 'uploads_projet25'

STATUTS = ('EN_ATTENTE', 'VALIDE', 'REFUSE', 'ANNULE')

# Jours fériés fixes (récurrents chaque année) : (mois, jour, libellé, code)
FERIES_FIXES = [
    (12, 17, 'Fête de la révolution', 'REVOLUTION_17_DEC'),
    (3, 20, "Fête de l'indépendance", 'INDEPENDANCE_20_MARS'),
    (5, 1, 'Fête du travail', 'TRAVAIL_1_MAI'),
    (7, 25, 'Fête de la république', 'REPUBLIQUE_25_JUIL'),
]

# Jours fériés variables (dates selon observation du croissant – saisie annuelle par la RH)
FERIES_VARIABLES_TYPES = [
    ('MOULED', 'Le Mouled (Mouloud)', 1),
    ('AID_FITER', 'Aid El Fitr', 2),
    ('AID_IDHA', 'Aid El Idha', 2),
    ('NOUVEL_AN_HEGIRE', "Jour de l'an Hégirien", 1),
]


def init_web_conge_tables():
    """Crée les tables si absentes (équivalent script SQL)."""
    sql_blocks = [
        """IF OBJECT_ID('dbo.WEB_CONGE_TYPE', 'U') IS NULL
           CREATE TABLE dbo.WEB_CONGE_TYPE (
               ID INT IDENTITY(1,1) PRIMARY KEY, Code NVARCHAR(50) NOT NULL UNIQUE,
               Libelle NVARCHAR(120) NOT NULL, Archive BIT NOT NULL DEFAULT 0)""",
        """IF OBJECT_ID('dbo.WEB_CONGE_JOUR_FERIE', 'U') IS NULL
           CREATE TABLE dbo.WEB_CONGE_JOUR_FERIE (
               ID INT IDENTITY(1,1) PRIMARY KEY, DateFerie DATE NOT NULL UNIQUE,
               Libelle NVARCHAR(200) NULL, Archive BIT NOT NULL DEFAULT 0)""",
        """IF OBJECT_ID('dbo.WEB_CONGE_SOLDE', 'U') IS NULL
           CREATE TABLE dbo.WEB_CONGE_SOLDE (
               ID INT IDENTITY(1,1) PRIMARY KEY, Matricule INT NOT NULL, Annee INT NOT NULL,
               SoldeJours DECIMAL(6,2) NOT NULL DEFAULT 0, ConsommeJours DECIMAL(6,2) NOT NULL DEFAULT 0,
               CONSTRAINT UQ_WEB_CONGE_SOLDE UNIQUE (Matricule, Annee))""",
        """IF OBJECT_ID('dbo.WEB_CONGE_VALIDATEUR_LIEN', 'U') IS NULL
           CREATE TABLE dbo.WEB_CONGE_VALIDATEUR_LIEN (
               ID INT IDENTITY(1,1) PRIMARY KEY, MatriculeValidateur INT NOT NULL,
               MatriculeEmploye INT NOT NULL, EmailNotification NVARCHAR(255) NULL,
               EstInterim BIT NOT NULL DEFAULT 0, Archive BIT NOT NULL DEFAULT 0,
               CONSTRAINT UQ_WEB_CONGE_VAL_EMP UNIQUE (MatriculeValidateur, MatriculeEmploye))""",
        """IF OBJECT_ID('dbo.WEB_CONGE_STAFF_ADMIN', 'U') IS NULL
           CREATE TABLE dbo.WEB_CONGE_STAFF_ADMIN (Matricule INT NOT NULL PRIMARY KEY)""",
        """IF OBJECT_ID('dbo.WEB_CONGE_RH', 'U') IS NULL
           CREATE TABLE dbo.WEB_CONGE_RH (
               Matricule INT NOT NULL PRIMARY KEY,
               Actif BIT NOT NULL DEFAULT 1,
               DateAjout DATETIME NOT NULL DEFAULT GETDATE())""",
        """IF OBJECT_ID('dbo.WEB_CONGE_DEMANDE', 'U') IS NULL
           CREATE TABLE dbo.WEB_CONGE_DEMANDE (
               ID INT IDENTITY(1,1) PRIMARY KEY, TypeDemande NVARCHAR(20) NOT NULL,
               MatriculeDemandeur INT NOT NULL, MatriculeSaisiePar INT NULL,
               Statut NVARCHAR(20) NOT NULL DEFAULT N'EN_ATTENTE',
               ID_TypeConge INT NULL, DateDebut DATE NULL, DateFin DATE NULL,
               DemiJournee NVARCHAR(10) NULL, NbJoursOuvres DECIMAL(6,2) NULL,
               Commentaire NVARCHAR(500) NULL, FichierJoint NVARCHAR(500) NULL,
               DateSortie DATE NULL, HeureDepart TIME NULL, HeureRetour TIME NULL,
               DureeMinutes INT NULL, MotifSortie NVARCHAR(500) NULL,
               MatriculeValidateur INT NULL, DateValidation DATETIME NULL,
               CommentaireRefus NVARCHAR(500) NULL, EstRetroactive BIT NOT NULL DEFAULT 0,
               MatriculeInterim INT NULL,
               DateCreation DATETIME NOT NULL DEFAULT GETDATE(),
               DateModification DATETIME NULL)""",
        """IF OBJECT_ID('dbo.WEB_CONGE_NOTIFICATION', 'U') IS NULL
           CREATE TABLE dbo.WEB_CONGE_NOTIFICATION (
               ID INT IDENTITY(1,1) PRIMARY KEY, MatriculeDest INT NOT NULL,
               TypeNotif NVARCHAR(50) NOT NULL, Message NVARCHAR(500) NOT NULL,
               ID_Demande INT NULL, Lu BIT NOT NULL DEFAULT 0,
               DateCreation DATETIME NOT NULL DEFAULT GETDATE())""",
    ]
    with get_db_cursor() as cursor:
        for block in sql_blocks:
            cursor.execute(block)
        cursor.connection.commit()
    sync_official_conge_types()
    migrate_feries_columns()
    ensure_default_rh()
    try:
        from logic.projet25_solde import init_solde_fiche_tables
        init_solde_fiche_tables()
    except Exception as e:
        print(f'[Projet25] init solde fiche: {e}')


# Types de congés officiels (entreprise)
OFFICIAL_CONGE_TYPES = [
    ('ANNUEL', 'Congé annuel'),
    ('MARIAGE', 'Mariage'),
    ('DECES', 'Décès'),
    ('MATERNITE', 'Maternité'),
    ('PATERNITE', 'Paternité'),
    ('RECUPERATION', 'Récupération'),
    ('CIRCONCISION', 'Circoncision'),
]


def sync_official_conge_types():
    """Met à jour les libellés actifs et archive les types hors liste officielle."""
    codes = [c for c, _ in OFFICIAL_CONGE_TYPES]
    with get_db_cursor() as cursor:
        for code, lib in OFFICIAL_CONGE_TYPES:
            cursor.execute("SELECT ID FROM WEB_CONGE_TYPE WHERE Code = ?", (code,))
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE WEB_CONGE_TYPE SET Libelle = ?, Archive = 0 WHERE Code = ?",
                    (lib, code),
                )
            else:
                cursor.execute(
                    "INSERT INTO WEB_CONGE_TYPE (Code, Libelle, Archive) VALUES (?, ?, 0)",
                    (code, lib),
                )
        placeholders = ','.join(['?'] * len(codes))
        cursor.execute(
            f"UPDATE WEB_CONGE_TYPE SET Archive = 1 WHERE Code NOT IN ({placeholders})",
            codes,
        )
        cursor.connection.commit()


def ensure_projet25_in_web_projets():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = ?", (NUM_PROJ,))
            if cursor.fetchone():
                return
            cursor.execute("""
                INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive)
                VALUES (?, 'Projet 25', N'Gestion des congés et autorisations de sortie', 0)
            """, (NUM_PROJ,))
            cursor.connection.commit()
            print('[Projet 25] WEB_PROJETS ajouté.')
    except Exception as e:
        print(f'[Projet 25] ensure_projet25_in_web_projets: {e}')


def _int_mat(m):
    if m is None:
        return None
    try:
        return int(m)
    except (TypeError, ValueError):
        return None


def get_rh_matricules_actifs():
    """Matricules ayant le rôle RH (table WEB_CONGE_RH)."""
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT Matricule FROM WEB_CONGE_RH WHERE Actif = 1"
        )
        return [_int_mat(r.Matricule) for r in cursor.fetchall() if _int_mat(r.Matricule) is not None]


def ensure_default_rh():
    """Garantit au moins le matricule RH historique (366) dans la table."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT 1 FROM WEB_CONGE_RH WHERE Matricule = ?", (MATRICULE_RH,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO WEB_CONGE_RH (Matricule, Actif) VALUES (?, 1)",
                (MATRICULE_RH,),
            )
        else:
            cursor.execute(
                "UPDATE WEB_CONGE_RH SET Actif = 1 WHERE Matricule = ?",
                (MATRICULE_RH,),
            )
        cursor.connection.commit()


def is_rh(matricule, is_super=False):
    if is_super:
        return True
    m = _int_mat(matricule)
    if m is None:
        return False
    return m in get_rh_matricules_actifs()


def get_person(matricule):
    m = _int_mat(matricule)
    if m is None:
        return None
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT Matricule, Nom, Prenom, Adresse_mail FROM personel WHERE Matricule = ? AND (archive = 0 OR archive IS NULL)",
            (m,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'matricule': row.Matricule,
            'nom': (row.Nom or '').strip(),
            'prenom': (row.Prenom or '').strip(),
            'email': (row.Adresse_mail or '').strip() if row.Adresse_mail else '',
            'label': f"{row.Nom or ''} {row.Prenom or ''}".strip(),
        }


def list_personel_actifs(q=''):
    with get_db_cursor() as cursor:
        if q:
            like = f'%{q}%'
            cursor.execute("""
                SELECT Matricule, Nom, Prenom, Adresse_mail
                FROM personel
                WHERE (archive = 0 OR archive IS NULL)
                  AND (CAST(Matricule AS NVARCHAR(20)) LIKE ? OR Nom LIKE ? OR Prenom LIKE ?)
                ORDER BY Nom, Prenom
            """, (like, like, like))
        else:
            cursor.execute("""
                SELECT Matricule, Nom, Prenom, Adresse_mail
                FROM personel
                WHERE (archive = 0 OR archive IS NULL)
                ORDER BY Nom, Prenom
            """)
        return [
            {
                'matricule': r.Matricule,
                'nom': r.Nom or '',
                'prenom': r.Prenom or '',
                'email': r.Adresse_mail or '',
                'label': f"{r.Nom or ''} {r.Prenom or ''}".strip(),
            }
            for r in cursor.fetchall()
        ]


def is_staff_administratif(matricule):
    m = _int_mat(matricule)
    if m is None:
        return False
    with get_db_cursor() as cursor:
        cursor.execute("SELECT 1 FROM WEB_CONGE_STAFF_ADMIN WHERE Matricule = ?", (m,))
        return cursor.fetchone() is not None


def migrate_feries_columns():
    """Ajoute CodeFerie et Annee pour les fériés variables (dates islamiques)."""
    alters = [
        "IF COL_LENGTH('dbo.WEB_CONGE_JOUR_FERIE', 'CodeFerie') IS NULL "
        "ALTER TABLE dbo.WEB_CONGE_JOUR_FERIE ADD CodeFerie NVARCHAR(50) NULL",
        "IF COL_LENGTH('dbo.WEB_CONGE_JOUR_FERIE', 'Annee') IS NULL "
        "ALTER TABLE dbo.WEB_CONGE_JOUR_FERIE ADD Annee INT NULL",
        "IF COL_LENGTH('dbo.WEB_CONGE_JOUR_FERIE', 'TypeFerie') IS NULL "
        "ALTER TABLE dbo.WEB_CONGE_JOUR_FERIE ADD TypeFerie NVARCHAR(20) NOT NULL DEFAULT 'VARIABLE'",
    ]
    with get_db_cursor() as cursor:
        for sql in alters:
            try:
                cursor.execute(sql)
            except Exception as e:
                print(f'[Projet25] migrate_feries: {e}')
        cursor.connection.commit()


def _feries_fixes_dates_pour_annee(annee):
    """Dates calendaires des 4 fériés fixes pour une année."""
    out = []
    for mois, jour, libelle, code in FERIES_FIXES:
        try:
            out.append((date(annee, mois, jour), libelle, code))
        except ValueError:
            pass
    return out


def get_jours_feries_set(date_debut=None, date_fin=None):
    """
    Ensemble des dates fériées : fixes (récurrents) + variables (saisies en base).
    """
    s = set()
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DateFerie FROM WEB_CONGE_JOUR_FERIE
            WHERE Archive = 0 AND DateFerie IS NOT NULL
        """)
        for r in cursor.fetchall():
            d = r.DateFerie.date() if hasattr(r.DateFerie, 'date') else r.DateFerie
            s.add(d)

    if date_debut and date_fin:
        if isinstance(date_debut, str):
            date_debut = datetime.strptime(date_debut[:10], '%Y-%m-%d').date()
        if isinstance(date_fin, str):
            date_fin = datetime.strptime(date_fin[:10], '%Y-%m-%d').date()
        y1, y2 = date_debut.year, date_fin.year
    else:
        t = date.today()
        y1, y2 = t.year - 1, t.year + 2

    for annee in range(y1, y2 + 1):
        for d, _lib, _code in _feries_fixes_dates_pour_annee(annee):
            s.add(d)
    return s


def compter_jours_ouvres(date_debut, date_fin, demi_journee=None):
    """Compte les jours ouvrés entre deux dates (excl. sam/dim et fériés). Demi-journée = 0.5 si une seule date."""
    if not date_debut or not date_fin:
        return 0.0
    if isinstance(date_debut, str):
        date_debut = datetime.strptime(date_debut[:10], '%Y-%m-%d').date()
    if isinstance(date_fin, str):
        date_fin = datetime.strptime(date_fin[:10], '%Y-%m-%d').date()
    feries = get_jours_feries_set(date_debut, date_fin)
    if date_debut > date_fin:
        return 0.0
    if date_debut == date_fin and demi_journee in ('MATIN', 'APRES_MIDI'):
        wd = date_debut.weekday()
        if wd >= 5 or date_debut in feries:
            return 0.0
        return 0.5
    n = 0.0
    d = date_debut
    while d <= date_fin:
        if d.weekday() < 5 and d not in feries:
            n += 1.0
        d += timedelta(days=1)
    return n


def get_validateur_for_employe(matricule_employe):
    m = _int_mat(matricule_employe)
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT TOP 1 MatriculeValidateur, EmailNotification
            FROM WEB_CONGE_VALIDATEUR_LIEN
            WHERE MatriculeEmploye = ? AND Archive = 0 AND EstInterim = 0
            ORDER BY ID
        """, (m,))
        row = cursor.fetchone()
        if row:
            return row.MatriculeValidateur, row.EmailNotification
    return None, None


def get_subordonnes_matricules(matricule_validateur):
    m = _int_mat(matricule_validateur)
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT MatriculeEmploye FROM WEB_CONGE_VALIDATEUR_LIEN
            WHERE MatriculeValidateur = ? AND Archive = 0
        """, (m,))
        return [_int_mat(r.MatriculeEmploye) for r in cursor.fetchall()]


def user_can_see_demande(matricule_viewer, demande, is_super=False):
    """Droit de lecture sur une demande."""
    v = _int_mat(matricule_viewer)
    dem = _int_mat(demande.get('matricule_demandeur'))
    if v == dem:
        return True
    if is_rh(v, is_super):
        return True
    if is_super:
        return True
    subs = get_subordonnes_matricules(v)
    if dem in subs:
        return True
    val = _int_mat(demande.get('matricule_validateur'))
    if v == val:
        return True
    return False


def get_solde(matricule, annee=None):
    m = _int_mat(matricule)
    if annee is None:
        annee = date.today().year
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT SoldeJours, ConsommeJours FROM WEB_CONGE_SOLDE WHERE Matricule = ? AND Annee = ?",
            (m, annee),
        )
        row = cursor.fetchone()
        if not row:
            return {'annee': annee, 'solde': 0.0, 'consomme': 0.0, 'restant': 0.0}
        solde = float(row.SoldeJours or 0)
        cons = float(row.ConsommeJours or 0)
        return {'annee': annee, 'solde': solde, 'consomme': cons, 'restant': max(0, solde - cons)}


def _chevauchement_conge(matricule, d1, d2, exclude_id=None):
    with get_db_cursor() as cursor:
        sql = """
            SELECT ID FROM WEB_CONGE_DEMANDE
            WHERE TypeDemande = 'CONGE' AND MatriculeDemandeur = ?
            AND Statut IN ('EN_ATTENTE', 'VALIDE')
            AND DateDebut IS NOT NULL AND DateFin IS NOT NULL
            AND DateDebut <= ? AND DateFin >= ?
        """
        params = [matricule, d2, d1]
        if exclude_id:
            sql += " AND ID <> ?"
            params.append(exclude_id)
        cursor.execute(sql, params)
        return cursor.fetchone() is not None


def _conge_valide_sur_date(matricule, d):
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT ID FROM WEB_CONGE_DEMANDE
            WHERE TypeDemande = 'CONGE' AND MatriculeDemandeur = ? AND Statut = 'VALIDE'
            AND DateDebut <= ? AND DateFin >= ?
        """, (matricule, d, d))
        return cursor.fetchone() is not None


def _row_to_demande(row):
    def fmt_date(x):
        if x is None:
            return None
        return x.strftime('%Y-%m-%d') if hasattr(x, 'strftime') else str(x)[:10]

    def fmt_time(x):
        if x is None:
            return None
        if hasattr(x, 'strftime'):
            return x.strftime('%H:%M')
        return str(x)[:5]

    def fmt_dt(x):
        if x is None:
            return None
        return x.strftime('%Y-%m-%d %H:%M') if hasattr(x, 'strftime') else str(x)

    return {
        'id': row.ID,
        'type_demande': row.TypeDemande,
        'matricule_demandeur': row.MatriculeDemandeur,
        'matricule_saisie_par': row.MatriculeSaisiePar,
        'statut': row.Statut,
        'id_type_conge': row.ID_TypeConge,
        'date_debut': fmt_date(row.DateDebut),
        'date_fin': fmt_date(row.DateFin),
        'demi_journee': row.DemiJournee,
        'nb_jours_ouvres': float(row.NbJoursOuvres) if row.NbJoursOuvres is not None else None,
        'commentaire': row.Commentaire,
        'fichier_joint': row.FichierJoint,
        'date_sortie': fmt_date(row.DateSortie),
        'heure_depart': fmt_time(row.HeureDepart),
        'heure_retour': fmt_time(row.HeureRetour),
        'duree_minutes': row.DureeMinutes,
        'motif_sortie': row.MotifSortie,
        'matricule_validateur': row.MatriculeValidateur,
        'date_validation': fmt_dt(row.DateValidation),
        'commentaire_refus': row.CommentaireRefus,
        'est_retroactive': bool(row.EstRetroactive),
        'matricule_interim': row.MatriculeInterim,
        'date_creation': fmt_dt(row.DateCreation),
        'date_modification': fmt_dt(row.DateModification),
    }


def list_demandes(filtre=None, matricule_viewer=None, scope='mes', is_super=False):
    """
    scope: mes | equipe | toutes | a_valider
    """
    filtre = filtre or {}
    v = _int_mat(matricule_viewer)
    clauses = []
    params = []

    if scope == 'mes':
        clauses.append('D.MatriculeDemandeur = ?')
        params.append(v)
    elif scope == 'equipe':
        subs = get_subordonnes_matricules(v)
        if not subs and not is_rh(v, is_super):
            return []
        if is_rh(v, is_super) or is_super:
            pass
        else:
            placeholders = ','.join(['?'] * len(subs))
            clauses.append(f'D.MatriculeDemandeur IN ({placeholders})')
            params.extend(subs)
    elif scope == 'a_valider':
        subs = get_subordonnes_matricules(v)
        if is_rh(v, is_super) or is_super:
            clauses.append("D.Statut = 'EN_ATTENTE'")
        elif subs:
            placeholders = ','.join(['?'] * len(subs))
            clauses.append(f"D.Statut = 'EN_ATTENTE' AND D.MatriculeDemandeur IN ({placeholders})")
            params.extend(subs)
        else:
            return []
    elif scope == 'toutes':
        if not (is_rh(v, is_super) or is_super):
            return []

    if filtre.get('type_demande'):
        clauses.append('D.TypeDemande = ?')
        params.append(filtre['type_demande'])
    if filtre.get('statut'):
        clauses.append('D.Statut = ?')
        params.append(filtre['statut'])

    where = ' AND '.join(clauses) if clauses else '1=1'
    sql = f"""
        SELECT D.*, T.Libelle AS TypeCongeLibelle,
               P.Nom AS NomDemandeur, P.Prenom AS PrenomDemandeur
        FROM WEB_CONGE_DEMANDE D
        LEFT JOIN WEB_CONGE_TYPE T ON T.ID = D.ID_TypeConge
        LEFT JOIN personel P ON P.Matricule = D.MatriculeDemandeur
        WHERE {where}
        ORDER BY D.DateCreation DESC
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        out = []
        for row in cursor.fetchall():
            d = _row_to_demande(row)
            d['type_conge_libelle'] = getattr(row, 'TypeCongeLibelle', None)
            d['demandeur_label'] = f"{row.NomDemandeur or ''} {row.PrenomDemandeur or ''}".strip()
            if scope != 'toutes' and scope != 'a_valider':
                if not user_can_see_demande(v, d, is_super):
                    continue
            out.append(d)
        return out


def get_demande(demande_id):
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT D.*, T.Libelle AS TypeCongeLibelle
            FROM WEB_CONGE_DEMANDE D
            LEFT JOIN WEB_CONGE_TYPE T ON T.ID = D.ID_TypeConge
            WHERE D.ID = ?
        """, (demande_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = _row_to_demande(row)
        d['type_conge_libelle'] = getattr(row, 'TypeCongeLibelle', None)
        p = get_person(d['matricule_demandeur'])
        d['demandeur_label'] = p['label'] if p else str(d['matricule_demandeur'])
        return d


def creer_notification(matricule_dest, type_notif, message, id_demande=None):
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO WEB_CONGE_NOTIFICATION (MatriculeDest, TypeNotif, Message, ID_Demande)
            VALUES (?, ?, ?, ?)
        """, (_int_mat(matricule_dest), type_notif, message[:500], id_demande))
        cursor.connection.commit()


def _ajouter_email_dest(emails, addr):
    a = (addr or '').strip()
    if a and a.lower() not in {e.lower() for e in emails}:
        emails.append(a)


def _corps_email_nouvelle_demande(d):
    label = d.get('demandeur_label', str(d.get('matricule_demandeur')))
    if d['type_demande'] == 'CONGE':
        typ = d.get('type_conge_libelle') or 'Congé'
        periode = f"{d.get('date_debut') or '—'} → {d.get('date_fin') or '—'}"
        jours = d.get('nb_jours_ouvres')
        jours_txt = f"{jours} j. ouvrés" if jours is not None else '—'
        detail = (
            f"<p><strong>Collaborateur :</strong> {label}</p>"
            f"<p><strong>Type :</strong> {typ}</p>"
            f"<p><strong>Période :</strong> {periode}</p>"
            f"<p><strong>Durée :</strong> {jours_txt}</p>"
        )
        if d.get('commentaire'):
            detail += f"<p><strong>Commentaire :</strong> {d['commentaire']}</p>"
        msg = f"Nouvelle demande de congé – {label} (en attente)"
    else:
        typ = 'autorisation de sortie'
        detail = (
            f"<p><strong>Collaborateur :</strong> {label}</p>"
            f"<p><strong>Date :</strong> {d.get('date_sortie') or '—'}</p>"
            f"<p><strong>Horaires :</strong> {d.get('heure_depart') or '—'} – {d.get('heure_retour') or '—'}</p>"
        )
        if d.get('motif_sortie'):
            detail += f"<p><strong>Motif :</strong> {d['motif_sortie']}</p>"
        msg = f"Nouvelle demande de {typ} – {label} (en attente)"
    html = detail + "<p>Connectez-vous au <strong>Projet 25</strong> pour traiter la demande.</p>"
    return msg, html


def notifier_demande_nouvelle(demande_id):
    d = get_demande(demande_id)
    if not d:
        return
    dem = d['matricule_demandeur']
    val, email_val = get_validateur_for_employe(dem)
    msg, html = _corps_email_nouvelle_demande(d)
    label = d.get('demandeur_label', str(dem))
    destinataires = []
    if val:
        destinataires.append(val)
        creer_notification(val, 'NOUVELLE_DEMANDE', msg, demande_id)
    emails = []
    _ajouter_email_dest(emails, email_val)
    p_val = get_person(val) if val else None
    if p_val:
        _ajouter_email_dest(emails, p_val.get('email'))
    for m_rh in get_rh_matricules_actifs():
        if m_rh and m_rh != val:
            creer_notification(m_rh, 'NOUVELLE_DEMANDE', msg, demande_id)
        p_rh = get_person(m_rh)
        if p_rh:
            _ajouter_email_dest(emails, p_rh.get('email'))
    if d['type_demande'] == 'CONGE':
        for addr in EMAILS_RH_NOTIF:
            _ajouter_email_dest(emails, addr)
    send_email(
        emails,
        f"[Congés] Nouvelle demande – {label}",
        html,
        msg,
    )
    # Intérim : notifier si congé validé sur la période
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT L.MatriculeValidateur
            FROM WEB_CONGE_VALIDATEUR_LIEN L
            WHERE L.EstInterim = 1 AND L.Archive = 0
              AND L.MatriculeEmploye IN (
                SELECT MatriculeValidateur FROM WEB_CONGE_VALIDATEUR_LIEN
                WHERE MatriculeEmploye = ? AND Archive = 0
              )
        """, (val or dem,))
        for r in cursor.fetchall():
            creer_notification(r.MatriculeValidateur, 'INFO_INTERIM', msg, demande_id)


def notifier_statut_demande(demande_id, nouveau_statut):
    d = get_demande(demande_id)
    if not d:
        return
    dem = d['matricule_demandeur']
    typ = 'congé' if d['type_demande'] == 'CONGE' else 'sortie'
    msg = f"Votre demande de {typ} est maintenant : {nouveau_statut}"
    creer_notification(dem, 'STATUT_DEMANDE', msg, demande_id)
    p = get_person(dem)
    if p and p.get('email'):
        send_email(p['email'], f"[Congés] Demande {nouveau_statut}", f"<p>{msg}</p>", msg)


def creer_demande_conge(data, matricule_connecte, is_rh_user=False, is_super=False):
    saisie = _int_mat(matricule_connecte)
    rh_ok = is_rh_user or is_super
    if rh_ok:
        dem = _int_mat(data.get('matricule_demandeur') or matricule_connecte)
    else:
        dem = saisie
        autre = _int_mat(data.get('matricule_demandeur'))
        if autre is not None and autre != saisie:
            return None, "Vous ne pouvez saisir une demande que pour vous-même."

    d1 = data.get('date_debut')
    d2 = data.get('date_fin')
    id_type = data.get('id_type_conge')
    demi = data.get('demi_journee') or None
    retro = bool(data.get('est_retroactive'))

    if not id_type or not d1 or not d2:
        return None, "Type de congé et dates obligatoires."

    if demi and not is_staff_administratif(dem):
        return None, "Demi-journée réservée au staff administratif."

    d1o = datetime.strptime(d1[:10], '%Y-%m-%d').date()
    d2o = datetime.strptime(d2[:10], '%Y-%m-%d').date()
    now = datetime.now()
    if d1o < now.date() and not (is_rh_user or is_super):
        return None, "Date de début dans le passé : réservé à la RH."

    debut_dt = datetime.combine(d1o, time.min)
    if debut_dt > now and (debut_dt - now).total_seconds() < DELAI_MIN_HEURES * 3600:
        if not (is_rh_user or is_super):
            return None, f"Délai minimum de {DELAI_MIN_HEURES} h avant le début non respecté."

    if _chevauchement_conge(dem, d1o, d2o):
        return None, "Chevauchement avec une autre demande de congé."

    nb = compter_jours_ouvres(d1o, d2o, demi)
    if id_type and _type_est_annual(id_type):
        solde_info = _solde_conge_annuel(dem, d1o.year)
        if nb > solde_info['restant']:
            return None, f"Solde insuffisant ({solde_info['restant']:.1f} j restants)."

    val, _ = get_validateur_for_employe(dem)
    fichier = data.get('fichier_joint')

    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO WEB_CONGE_DEMANDE (
                TypeDemande, MatriculeDemandeur, MatriculeSaisiePar, Statut,
                ID_TypeConge, DateDebut, DateFin, DemiJournee, NbJoursOuvres,
                Commentaire, FichierJoint, EstRetroactive, MatriculeValidateur
            )
            OUTPUT INSERTED.ID
            VALUES ('CONGE', ?, ?, 'EN_ATTENTE', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dem, saisie, id_type, d1o, d2o, demi, nb,
            data.get('commentaire'), fichier, 1 if retro else 0, val,
        ))
        row = cursor.fetchone()
        new_id = int(row[0]) if row and row[0] is not None else None
        if new_id is None:
            return None, "Erreur lors de l'enregistrement de la demande."
        cursor.connection.commit()
    try:
        notifier_demande_nouvelle(new_id)
    except Exception as e:
        print(f'[Projet25] notifier_demande_nouvelle: {e}')
    return get_demande(new_id), None


def _type_est_annual(id_type):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT Code FROM WEB_CONGE_TYPE WHERE ID = ?", (id_type,))
        row = cursor.fetchone()
        return row and row.Code in ('ANNUEL', 'RECUPERATION')


def _solde_conge_annuel(matricule, annee=None):
    """Solde congé annuel via fiche importée (Projet 25 soldes détaillés)."""
    from logic.projet25_solde import get_solde_demande_conge
    return get_solde_demande_conge(matricule, annee)


def _sync_solde_fiche_apres_demande(demande):
    if demande.get('type_demande') != 'CONGE' or not _type_est_annual(demande.get('id_type_conge')):
        return
    from logic.projet25_solde import sync_p25_conges_to_mensuel
    annee = date.today().year
    if demande.get('date_debut'):
        annee = int(str(demande['date_debut'])[:4])
    sync_p25_conges_to_mensuel(demande['matricule_demandeur'], annee)


def creer_demande_sortie(data, matricule_connecte, is_rh_user=False, is_super=False):
    saisie = _int_mat(matricule_connecte)
    rh_ok = is_rh_user or is_super
    if rh_ok:
        dem = _int_mat(data.get('matricule_demandeur') or matricule_connecte)
    else:
        dem = saisie
        autre = _int_mat(data.get('matricule_demandeur'))
        if autre is not None and autre != saisie:
            return None, "Vous ne pouvez saisir une demande que pour vous-même."

    ds = data.get('date_sortie')
    hd = data.get('heure_depart')
    hr = data.get('heure_retour')
    motif = (data.get('motif_sortie') or '').strip()
    if not ds or not hd or not motif:
        return None, "Date, heure de départ et motif obligatoires."

    if len(ds) < 10 or not ds[:10].replace('-', '').isdigit():
        return None, "Date de sortie invalide."
    try:
        dso = datetime.strptime(ds[:10], '%Y-%m-%d').date()
    except ValueError:
        return None, "Date de sortie invalide (format attendu : AAAA-MM-JJ)."
    annee = dso.year
    if annee < 1900 or annee > 2100:
        return None, "Année invalide (4 chiffres entre 1900 et 2100)."
    aujourd = date.today()
    if dso < aujourd and not (is_rh_user or is_super):
        return None, "La date de sortie ne peut pas être antérieure à aujourd'hui."
    if _conge_valide_sur_date(dem, dso):
        return None, "Impossible : congé validé sur cette date."

    duree = data.get('duree_minutes')
    try:
        duree = int(duree) if duree is not None and duree != '' else None
    except (TypeError, ValueError):
        duree = None
    if (not duree or duree <= 0) and hd and hr:
        duree = _calc_duree_minutes(hd, hr)
    if (not duree or duree <= 0) and data.get('temps_reel') and hd:
        h = _hhmm_vers_heures_decimales(data.get('temps_reel'))
        if h > 0:
            duree = int(round(h * 60))
    if not duree or duree <= 0:
        return None, "Indiquez l'heure de retour ou le temps réel (durée > 0)."

    val, _ = get_validateur_for_employe(dem)
    t_dep = datetime.strptime(hd[:5], '%H:%M').time()
    t_ret = datetime.strptime(hr[:5], '%H:%M').time() if hr else None

    if dem is None:
        return None, "Matricule employé introuvable (session déconnectée ?)."

    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO WEB_CONGE_DEMANDE (
                TypeDemande, MatriculeDemandeur, MatriculeSaisiePar, Statut,
                DateSortie, HeureDepart, HeureRetour, DureeMinutes, MotifSortie,
                MatriculeValidateur
            )
            OUTPUT INSERTED.ID
            VALUES ('SORTIE', ?, ?, 'EN_ATTENTE', ?, ?, ?, ?, ?, ?)
        """, (dem, saisie, dso, t_dep, t_ret, int(duree), motif, val))
        row = cursor.fetchone()
        new_id = int(row[0]) if row and row[0] is not None else None
        if new_id is None:
            return None, "Erreur lors de l'enregistrement de la demande."
        cursor.connection.commit()
    try:
        notifier_demande_nouvelle(new_id)
    except Exception as e:
        print(f'[Projet25] notifier_demande_nouvelle: {e}')
    return get_demande(new_id), None


def _calc_duree_minutes(hd, hr):
    t1 = datetime.strptime(str(hd)[:5], '%H:%M')
    t2 = datetime.strptime(str(hr)[:5], '%H:%M')
    delta = (t2 - t1).total_seconds() / 60
    return int(delta) if delta > 0 else 0


def _hhmm_vers_heures_decimales(tps):
    if not tps:
        return 0.0
    s = str(tps).strip()
    if ':' not in s:
        return 0.0
    parts = s.split(':')
    try:
        return int(parts[0]) + int(parts[1]) / 60.0
    except (ValueError, IndexError):
        return 0.0


def annuler_demande(demande_id, matricule_connecte, is_super=False):
    d = get_demande(demande_id)
    if not d:
        return None, "Demande introuvable."
    if d['statut'] != 'EN_ATTENTE':
        return None, "Annulation possible uniquement en attente."
    if _int_mat(d['matricule_demandeur']) != _int_mat(matricule_connecte):
        return None, "Non autorisé."
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE WEB_CONGE_DEMANDE SET Statut = 'ANNULE', DateModification = GETDATE()
            WHERE ID = ?
        """, (demande_id,))
        cursor.connection.commit()
    notifier_statut_demande(demande_id, 'ANNULE')
    return get_demande(demande_id), None


def valider_demande(demande_id, matricule_connecte, is_super=False):
    return _changer_statut(demande_id, matricule_connecte, 'VALIDE', None, is_super)


def refuser_demande(demande_id, matricule_connecte, commentaire_refus, is_super=False):
    if not (commentaire_refus or '').strip():
        return None, "Commentaire de refus obligatoire."
    return _changer_statut(demande_id, matricule_connecte, 'REFUSE', commentaire_refus.strip(), is_super)


def devalider_demande(demande_id, matricule_connecte, is_super=False):
    d = get_demande(demande_id)
    if not d or d['statut'] != 'VALIDE':
        return None, "Seules les demandes validées peuvent être dévalidées."
    m = _int_mat(matricule_connecte)
    if not (_can_validate(m, d, is_super)):
        return None, "Non autorisé."
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE WEB_CONGE_DEMANDE SET Statut = 'EN_ATTENTE',
                DateValidation = NULL, MatriculeValidateur = NULL, DateModification = GETDATE()
            WHERE ID = ?
        """, (demande_id,))
        cursor.connection.commit()
    if d['type_demande'] == 'CONGE':
        _sync_solde_fiche_apres_demande(d)
    notifier_statut_demande(demande_id, 'EN_ATTENTE')
    return get_demande(demande_id), None


def _can_validate(matricule, demande, is_super=False):
    if is_super or is_rh(matricule, False):
        return True
    dem = _int_mat(demande['matricule_demandeur'])
    subs = get_subordonnes_matricules(matricule)
    return dem in subs


def _changer_statut(demande_id, matricule_connecte, statut, commentaire_refus, is_super=False):
    d = get_demande(demande_id)
    if not d:
        return None, "Demande introuvable."
    if d['statut'] != 'EN_ATTENTE':
        return None, "Demande déjà traitée."
    m = _int_mat(matricule_connecte)
    if not _can_validate(m, d, is_super):
        return None, "Non autorisé à valider cette demande."

    with get_db_cursor() as cursor:
        if statut == 'VALIDE' and d['type_demande'] == 'CONGE':
            err = _incrementer_solde_check(cursor, d)
            if err:
                return None, err
        cursor.execute("""
            UPDATE WEB_CONGE_DEMANDE SET Statut = ?, MatriculeValidateur = ?,
                DateValidation = GETDATE(), CommentaireRefus = ?, DateModification = GETDATE()
            WHERE ID = ?
        """, (statut, m, commentaire_refus if statut == 'REFUSE' else None, demande_id))
        cursor.connection.commit()
    if statut == 'VALIDE' and d['type_demande'] == 'CONGE':
        _sync_solde_fiche_apres_demande(d)
    notifier_statut_demande(demande_id, statut)
    return get_demande(demande_id), None


def _incrementer_solde_check(cursor, demande):
    if not _type_est_annual(demande.get('id_type_conge')):
        return None
    nb = float(demande.get('nb_jours_ouvres') or 0)
    annee = date.today().year
    if demande.get('date_debut'):
        annee = int(str(demande['date_debut'])[:4])
    solde_info = _solde_conge_annuel(demande['matricule_demandeur'], annee)
    if nb > solde_info['restant']:
        return f"Solde insuffisant ({solde_info['restant']:.1f} j restants)."
    return None


def get_notifications(matricule, non_lues_seulement=False):
    m = _int_mat(matricule)
    with get_db_cursor() as cursor:
        sql = """
            SELECT ID, TypeNotif, Message, ID_Demande, Lu, DateCreation
            FROM WEB_CONGE_NOTIFICATION WHERE MatriculeDest = ?
        """
        if non_lues_seulement:
            sql += " AND Lu = 0"
        sql += " ORDER BY DateCreation DESC"
        cursor.execute(sql, (m,))
        return [
            {
                'id': r.ID,
                'type': r.TypeNotif,
                'message': r.Message,
                'id_demande': r.ID_Demande,
                'lu': bool(r.Lu),
                'date': r.DateCreation.strftime('%Y-%m-%d %H:%M') if r.DateCreation else '',
            }
            for r in cursor.fetchall()
        ]


def marquer_notifications_lues(matricule, ids=None):
    m = _int_mat(matricule)
    with get_db_cursor() as cursor:
        if ids:
            placeholders = ','.join(['?'] * len(ids))
            cursor.execute(
                f"UPDATE WEB_CONGE_NOTIFICATION SET Lu = 1 WHERE MatriculeDest = ? AND ID IN ({placeholders})",
                [m] + list(ids),
            )
        else:
            cursor.execute(
                "UPDATE WEB_CONGE_NOTIFICATION SET Lu = 1 WHERE MatriculeDest = ?",
                (m,),
            )
        cursor.connection.commit()


def stats_tableau_bord():
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT Statut, TypeDemande, COUNT(*) AS Nb
            FROM WEB_CONGE_DEMANDE
            GROUP BY Statut, TypeDemande
        """)
        par_statut = [{'statut': r.Statut, 'type': r.TypeDemande, 'nb': r.Nb} for r in cursor.fetchall()]
        cursor.execute("""
            SELECT COUNT(*) AS Nb FROM WEB_CONGE_DEMANDE WHERE Statut = 'EN_ATTENTE'
        """)
        attente = cursor.fetchone().Nb
        return {'par_statut': par_statut, 'en_attente': attente}


# --- Validateurs / fériés / soldes / types ---

def list_types_conge():
    order_codes = [c for c, _ in OFFICIAL_CONGE_TYPES]
    with get_db_cursor() as cursor:
        cursor.execute("SELECT ID, Code, Libelle FROM WEB_CONGE_TYPE WHERE Archive = 0")
        rows = {r.Code: {'id': r.ID, 'code': r.Code, 'libelle': r.Libelle} for r in cursor.fetchall()}
    return [rows[c] for c in order_codes if c in rows]


def list_rh_utilisateurs():
    rh_set = set(get_rh_matricules_actifs())
    out = []
    for m in sorted(rh_set):
        p = get_person(m)
        out.append({
            'matricule': m,
            'label': p['label'] if p else str(m),
        })
    return out


def add_rh_matricule(matricule):
    m = _int_mat(matricule)
    if m is None:
        return False, "Matricule invalide."
    if not get_person(m):
        return False, "Collaborateur introuvable."
    with get_db_cursor() as cursor:
        cursor.execute("SELECT 1 FROM WEB_CONGE_RH WHERE Matricule = ?", (m,))
        if cursor.fetchone():
            cursor.execute("UPDATE WEB_CONGE_RH SET Actif = 1 WHERE Matricule = ?", (m,))
        else:
            cursor.execute("INSERT INTO WEB_CONGE_RH (Matricule, Actif) VALUES (?, 1)", (m,))
        cursor.connection.commit()
    return True, None


def remove_rh_matricule(matricule):
    m = _int_mat(matricule)
    if m is None:
        return False, "Matricule invalide."
    actifs = get_rh_matricules_actifs()
    if len(actifs) <= 1 and m in actifs:
        return False, "Impossible de retirer le dernier responsable RH."
    with get_db_cursor() as cursor:
        cursor.execute("UPDATE WEB_CONGE_RH SET Actif = 0 WHERE Matricule = ?", (m,))
        cursor.connection.commit()
    return True, None


def list_validateurs_liens():
    rh_set = set(get_rh_matricules_actifs())
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT L.ID, L.MatriculeValidateur, L.MatriculeEmploye, L.EmailNotification, L.EstInterim,
                   V.Nom AS VNom, V.Prenom AS VPrenom, E.Nom AS ENom, E.Prenom AS EPrenom
            FROM WEB_CONGE_VALIDATEUR_LIEN L
            LEFT JOIN personel V ON V.Matricule = L.MatriculeValidateur
            LEFT JOIN personel E ON E.Matricule = L.MatriculeEmploye
            WHERE L.Archive = 0
            ORDER BY V.Nom, E.Nom
        """)
        return [
            {
                'id': r.ID,
                'matricule_validateur': r.MatriculeValidateur,
                'matricule_employe': r.MatriculeEmploye,
                'email': r.EmailNotification or '',
                'est_interim': bool(r.EstInterim),
                'est_rh_validateur': _int_mat(r.MatriculeValidateur) in rh_set,
                'est_rh_collaborateur': _int_mat(r.MatriculeEmploye) in rh_set,
                'validateur_label': f"{r.VNom or ''} {r.VPrenom or ''}".strip(),
                'collaborateur_label': f"{r.ENom or ''} {r.EPrenom or ''}".strip(),
                'employe_label': f"{r.ENom or ''} {r.EPrenom or ''}".strip(),
            }
            for r in cursor.fetchall()
        ]


def save_validateur_lien(data):
    vid = _int_mat(data.get('matricule_validateur'))
    eid = _int_mat(data.get('matricule_employe'))
    email = (data.get('email') or '').strip() or None
    interim = 1 if data.get('est_interim') else 0
    lid = data.get('id')
    with get_db_cursor() as cursor:
        if lid:
            cursor.execute("""
                UPDATE WEB_CONGE_VALIDATEUR_LIEN SET MatriculeValidateur=?, MatriculeEmploye=?,
                    EmailNotification=?, EstInterim=? WHERE ID=?
            """, (vid, eid, email, interim, lid))
        else:
            cursor.execute("""
                INSERT INTO WEB_CONGE_VALIDATEUR_LIEN (MatriculeValidateur, MatriculeEmploye, EmailNotification, EstInterim)
                VALUES (?, ?, ?, ?)
            """, (vid, eid, email, interim))
        cursor.connection.commit()
    return True, None


def delete_validateur_lien(lid):
    with get_db_cursor() as cursor:
        cursor.execute("UPDATE WEB_CONGE_VALIDATEUR_LIEN SET Archive = 1 WHERE ID = ?", (lid,))
        cursor.connection.commit()


def get_feries_config(annee=None):
    """Configuration complète fériés pour l'écran RH."""
    if annee is None:
        annee = date.today().year
    annee = int(annee)

    fixes = [
        {'mois': m, 'jour': j, 'libelle': lib, 'code': code}
        for m, j, lib, code in FERIES_FIXES
    ]
    types_variables = [
        {'code': c, 'libelle': lib, 'nb_jours': nb}
        for c, lib, nb in FERIES_VARIABLES_TYPES
    ]
    dates_fixes = [
        {'date': d.strftime('%Y-%m-%d'), 'libelle': lib, 'code': code, 'type': 'FIXE'}
        for d, lib, code in _feries_fixes_dates_pour_annee(annee)
    ]

    dates_variables = []
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT ID, DateFerie, Libelle, CodeFerie, Annee
            FROM WEB_CONGE_JOUR_FERIE
            WHERE Archive = 0 AND DateFerie IS NOT NULL
              AND (Annee = ? OR Annee IS NULL AND YEAR(DateFerie) = ?)
            ORDER BY DateFerie
        """, (annee, annee))
        for r in cursor.fetchall():
            dates_variables.append({
                'id': r.ID,
                'date': r.DateFerie.strftime('%Y-%m-%d'),
                'libelle': r.Libelle or '',
                'code': r.CodeFerie or '',
                'annee': r.Annee or annee,
                'type': 'VARIABLE',
            })

    return {
        'annee': annee,
        'feries_fixes': fixes,
        'types_variables': types_variables,
        'dates_fixes_annee': dates_fixes,
        'dates_variables': dates_variables,
        'note_variables': (
            "Les fêtes islamiques (Mouled, Aïd El Fitr, Aïd El Idha, Nouvel An Hégirien) "
            "dépendent de l'observation du croissant validée par le Mufti de la République. "
            "Saisissez la date de début officielle pour chaque fête et l'année concernée."
        ),
    }


def list_jours_feries(annee=None):
    """Liste plate (compatibilité) : fixes calculés + variables en base."""
    cfg = get_feries_config(annee)
    rows = list(cfg['dates_fixes_annee'])
    for v in cfg['dates_variables']:
        rows.append({
            'id': v['id'],
            'date': v['date'],
            'libelle': v['libelle'],
            'code': v.get('code'),
            'type': v['type'],
        })
    return rows


def save_ferie_variable(code, annee, date_debut):
    """
    Enregistre les jours d'une fête variable (ex. Aid El Fitr = 2 jours consécutifs).
    date_debut : première date (YYYY-MM-DD).
    """
    annee = int(annee)
    code = (code or '').strip().upper()
    type_info = next((t for t in FERIES_VARIABLES_TYPES if t[0] == code), None)
    if not type_info:
        return False, 'Type de fête inconnu.'
    nb_jours = type_info[2]
    libelle_base = type_info[1]

    if isinstance(date_debut, str):
        d0 = datetime.strptime(date_debut[:10], '%Y-%m-%d').date()
    else:
        d0 = date_debut

    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE WEB_CONGE_JOUR_FERIE SET Archive = 1
            WHERE CodeFerie = ? AND Annee = ? AND Archive = 0
        """, (code, annee))

        for i in range(nb_jours):
            d = d0 + timedelta(days=i)
            lib = libelle_base if nb_jours == 1 else f"{libelle_base} (jour {i + 1}/{nb_jours})"
            cursor.execute(
                "SELECT ID FROM WEB_CONGE_JOUR_FERIE WHERE DateFerie = ?",
                (d,),
            )
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE WEB_CONGE_JOUR_FERIE SET Libelle=?, CodeFerie=?, Annee=?,
                        TypeFerie='VARIABLE', Archive=0 WHERE DateFerie=?
                """, (lib, code, annee, d))
            else:
                cursor.execute("""
                    INSERT INTO WEB_CONGE_JOUR_FERIE (DateFerie, Libelle, CodeFerie, Annee, TypeFerie, Archive)
                    VALUES (?, ?, ?, ?, 'VARIABLE', 0)
                """, (d, lib, code, annee))
        cursor.connection.commit()
    return True, None


def delete_ferie_variable(code, annee):
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE WEB_CONGE_JOUR_FERIE SET Archive = 1
            WHERE CodeFerie = ? AND Annee = ?
        """, (code, int(annee)))
        cursor.connection.commit()


def save_jour_ferie(data):
    """Ajout manuel d'un jour férié ponctuel (optionnel)."""
    with get_db_cursor() as cursor:
        if data.get('id'):
            cursor.execute(
                "UPDATE WEB_CONGE_JOUR_FERIE SET DateFerie=?, Libelle=?, Annee=?, TypeFerie='VARIABLE' WHERE ID=?",
                (data['date'], data.get('libelle'), data.get('annee'), data['id']),
            )
        else:
            d = data['date']
            an = data.get('annee') or int(str(d)[:4])
            cursor.execute("""
                INSERT INTO WEB_CONGE_JOUR_FERIE (DateFerie, Libelle, Annee, TypeFerie, Archive)
                VALUES (?, ?, ?, 'VARIABLE', 0)
            """, (d, data.get('libelle'), an))
        cursor.connection.commit()


def delete_jour_ferie(fid):
    with get_db_cursor() as cursor:
        cursor.execute("UPDATE WEB_CONGE_JOUR_FERIE SET Archive = 1 WHERE ID = ?", (fid,))
        cursor.connection.commit()


def list_soldes(annee=None):
    if annee is None:
        annee = date.today().year
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT S.Matricule, S.SoldeJours, S.ConsommeJours, P.Nom, P.Prenom
            FROM WEB_CONGE_SOLDE S
            LEFT JOIN personel P ON P.Matricule = S.Matricule
            WHERE S.Annee = ?
            ORDER BY P.Nom
        """, (annee,))
        return [
            {
                'matricule': r.Matricule,
                'solde': float(r.SoldeJours),
                'consomme': float(r.ConsommeJours),
                'restant': max(0, float(r.SoldeJours) - float(r.ConsommeJours)),
                'label': f"{r.Nom or ''} {r.Prenom or ''}".strip(),
            }
            for r in cursor.fetchall()
        ]


def save_solde(matricule, annee, solde_jours):
    m = _int_mat(matricule)
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT ID FROM WEB_CONGE_SOLDE WHERE Matricule = ? AND Annee = ?",
            (m, annee),
        )
        if cursor.fetchone():
            cursor.execute(
                "UPDATE WEB_CONGE_SOLDE SET SoldeJours = ? WHERE Matricule = ? AND Annee = ?",
                (solde_jours, m, annee),
            )
        else:
            cursor.execute(
                "INSERT INTO WEB_CONGE_SOLDE (Matricule, Annee, SoldeJours, ConsommeJours) VALUES (?, ?, ?, 0)",
                (m, annee, solde_jours),
            )
        cursor.connection.commit()


def list_staff_admin():
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT S.Matricule, P.Nom, P.Prenom FROM WEB_CONGE_STAFF_ADMIN S
            LEFT JOIN personel P ON P.Matricule = S.Matricule
        """)
        return [{'matricule': r.Matricule, 'label': f"{r.Nom or ''} {r.Prenom or ''}".strip()} for r in cursor.fetchall()]


def toggle_staff_admin(matricule, add=True):
    m = _int_mat(matricule)
    with get_db_cursor() as cursor:
        if add:
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM WEB_CONGE_STAFF_ADMIN WHERE Matricule=?) INSERT INTO WEB_CONGE_STAFF_ADMIN (Matricule) VALUES (?)",
                (m, m),
            )
        else:
            cursor.execute("DELETE FROM WEB_CONGE_STAFF_ADMIN WHERE Matricule = ?", (m,))
        cursor.connection.commit()


def upload_dir():
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, UPLOAD_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


def get_calendrier_absences(date_debut, date_fin):
    """
    Absences (congés + sorties) EN_ATTENTE / VALIDE + jours fériés
    pour une plage [date_debut, date_fin].
    """
    if isinstance(date_debut, str):
        d1 = datetime.strptime(date_debut[:10], '%Y-%m-%d').date()
    else:
        d1 = date_debut
    if isinstance(date_fin, str):
        d2 = datetime.strptime(date_fin[:10], '%Y-%m-%d').date()
    else:
        d2 = date_fin
    if d2 < d1:
        d1, d2 = d2, d1

    absences = []
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT D.ID, D.TypeDemande, D.MatriculeDemandeur, D.Statut,
                   D.DateDebut, D.DateFin, D.DemiJournee,
                   D.DateSortie, D.HeureDepart, D.HeureRetour,
                   T.Libelle AS TypeCongeLibelle,
                   P.Nom, P.Prenom
            FROM WEB_CONGE_DEMANDE D
            LEFT JOIN WEB_CONGE_TYPE T ON T.ID = D.ID_TypeConge
            LEFT JOIN personel P ON P.Matricule = D.MatriculeDemandeur
            WHERE D.Statut IN ('EN_ATTENTE', 'VALIDE')
              AND (
                (D.TypeDemande = 'CONGE' AND D.DateDebut IS NOT NULL AND D.DateFin IS NOT NULL
                 AND D.DateDebut <= ? AND D.DateFin >= ?)
                OR
                (D.TypeDemande = 'SORTIE' AND D.DateSortie IS NOT NULL
                 AND D.DateSortie >= ? AND D.DateSortie <= ?)
              )
            ORDER BY P.Nom, P.Prenom, D.ID
        """, (d2, d1, d1, d2))
        for r in cursor.fetchall():
            label = f"{(r.Nom or '').strip()} {(r.Prenom or '').strip()}".strip() or str(r.MatriculeDemandeur)
            heure_dep = r.HeureDepart.strftime('%H:%M') if r.HeureDepart and hasattr(r.HeureDepart, 'strftime') else (
                str(r.HeureDepart)[:5] if r.HeureDepart else None
            )
            heure_ret = r.HeureRetour.strftime('%H:%M') if r.HeureRetour and hasattr(r.HeureRetour, 'strftime') else (
                str(r.HeureRetour)[:5] if r.HeureRetour else None
            )
            absences.append({
                'id': r.ID,
                'type_demande': r.TypeDemande,
                'matricule': r.MatriculeDemandeur,
                'label': label,
                'statut': r.Statut,
                'type_libelle': r.TypeCongeLibelle if r.TypeDemande == 'CONGE' else 'Autorisation de sortie',
                'date_debut': r.DateDebut.strftime('%Y-%m-%d') if r.DateDebut else None,
                'date_fin': r.DateFin.strftime('%Y-%m-%d') if r.DateFin else None,
                'date_sortie': r.DateSortie.strftime('%Y-%m-%d') if r.DateSortie else None,
                'demi_journee': r.DemiJournee,
                'heure_depart': heure_dep,
                'heure_retour': heure_ret,
            })

    annees = set(range(d1.year, d2.year + 1))
    feries = []
    seen_f = set()
    for an in annees:
        for f in list_jours_feries(an):
            fd = f.get('date')
            if not fd:
                continue
            if isinstance(fd, date):
                fd_s = fd.strftime('%Y-%m-%d')
                fd_d = fd
            else:
                fd_s = str(fd)[:10]
                try:
                    fd_d = datetime.strptime(fd_s, '%Y-%m-%d').date()
                except ValueError:
                    continue
            if d1 <= fd_d <= d2 and fd_s not in seen_f:
                seen_f.add(fd_s)
                feries.append({
                    'date': fd_s,
                    'libelle': f.get('libelle') or 'Jour férié',
                })

    return {
        'debut': d1.strftime('%Y-%m-%d'),
        'fin': d2.strftime('%Y-%m-%d'),
        'absences': absences,
        'feries': feries,
    }
