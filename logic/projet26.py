# -*- coding: utf-8 -*-
"""
Projet 26 – Gestion des formations.
"""
from datetime import datetime, date, timedelta

from db import get_db_cursor
from logic import projet25 as p25
from logic.projet25_email import send_email

NUM_PROJ = 26
STATUTS_DEMANDE = ('EN_ATTENTE', 'VALIDE', 'REFUSE', 'ANNULE')
TYPES_FORMATION = ('INTRA', 'INTER', 'EN_LIGNE')
TYPE_EVAL = ('CHAUD', 'FROID')
JUGEMENTS = ('EFFICACE', 'NON_EFFICACE_REFAIRE', 'NON_EFFICACE_MODIFIER')
MOIS_EVAL_FROID_ADMIN = 6
MOIS_EVAL_FROID_PROD = 3
JOURS_RAPPEL_AVANT_FROID = 1


def _int_mat(m):
    return p25._int_mat(m)


def is_rh(matricule, is_super=False):
    return p25.is_rh(matricule, is_super)


def get_person(matricule):
    return p25.get_person(matricule)


def list_personel_actifs(q=''):
    return p25.list_personel_actifs(q)


def is_staff_administratif(matricule):
    return p25.is_staff_administratif(matricule)


def get_validateur_for_employe(matricule_employe):
    return p25.get_validateur_for_employe(matricule_employe)


def init_web_formation_tables():
    sql_blocks = [
        """IF OBJECT_ID('dbo.WEB_FORMATION_DEMANDE', 'U') IS NULL
           CREATE TABLE dbo.WEB_FORMATION_DEMANDE (
               ID INT IDENTITY(1,1) PRIMARY KEY,
               DateDemande DATE NOT NULL,
               MatriculeManager INT NOT NULL,
               MatriculeSaisiePar INT NULL,
               Theme NVARCHAR(300) NOT NULL,
               TypeFormation NVARCHAR(20) NOT NULL,
               OrganismeFormateurPropose NVARCHAR(500) NULL,
               OrganismePropose NVARCHAR(300) NULL,
               FormateurPropose NVARCHAR(300) NULL,
               DateDebutSouhaitee DATE NULL,
               DateFinSouhaitee DATE NULL,
               Objectif1 NVARCHAR(500) NULL,
               Objectif2 NVARCHAR(500) NULL,
               Objectif3 NVARCHAR(500) NULL,
               Statut NVARCHAR(20) NOT NULL DEFAULT N'EN_ATTENTE',
               MatriculeValidateurRH INT NULL,
               DateValidationRH DATETIME NULL,
               CommentaireRefus NVARCHAR(500) NULL,
               DateCreation DATETIME NOT NULL DEFAULT GETDATE(),
               DateModification DATETIME NULL
           )""",
        """IF OBJECT_ID('dbo.WEB_FORMATION_DEMANDE_BENEFICIAIRE', 'U') IS NULL
           CREATE TABLE dbo.WEB_FORMATION_DEMANDE_BENEFICIAIRE (
               ID INT IDENTITY(1,1) PRIMARY KEY,
               ID_Demande INT NOT NULL,
               Matricule INT NOT NULL,
               CONSTRAINT UQ_WEB_FORM_DEM_BEN UNIQUE (ID_Demande, Matricule)
           )""",
        """IF OBJECT_ID('dbo.WEB_FORMATION', 'U') IS NULL
           CREATE TABLE dbo.WEB_FORMATION (
               ID INT IDENTITY(1,1) PRIMARY KEY,
               ID_Demande INT NOT NULL,
               NumeroFormation NVARCHAR(20) NOT NULL,
               Annee INT NOT NULL,
               SeqAnnee INT NOT NULL,
               Theme NVARCHAR(300) NOT NULL,
               Formateur NVARCHAR(300) NULL,
               Objectif1 NVARCHAR(500) NULL,
               Objectif2 NVARCHAR(500) NULL,
               Objectif3 NVARCHAR(500) NULL,
               DateDebut DATE NOT NULL,
               DateFin DATE NOT NULL,
               DateCreation DATETIME NOT NULL DEFAULT GETDATE(),
               CONSTRAINT UQ_WEB_FORMATION_NUM UNIQUE (NumeroFormation)
           )""",
        """IF OBJECT_ID('dbo.WEB_FORMATION_EVAL_ADMIN', 'U') IS NULL
           CREATE TABLE dbo.WEB_FORMATION_EVAL_ADMIN (
               ID INT IDENTITY(1,1) PRIMARY KEY,
               ID_Formation INT NOT NULL,
               MatriculeParticipant INT NOT NULL,
               TypeEval NVARCHAR(10) NOT NULL,
               MatriculeSaisiePar INT NULL,
               NoteDuree TINYINT NULL,
               NoteHoraires TINYINT NULL,
               NoteOrganisation TINYINT NULL,
               NoteLocalEquip TINYINT NULL,
               NotePedagogie TINYINT NULL,
               NoteObj1 TINYINT NULL,
               NoteObj2 TINYINT NULL,
               NoteObj3 TINYINT NULL,
               NoteN1 DECIMAL(8,2) NULL,
               AttentesBesoins NVARCHAR(MAX) NULL,
               Propositions NVARCHAR(MAX) NULL,
               NoteColdObj1 TINYINT NULL,
               NoteColdObj2 TINYINT NULL,
               NoteColdObj3 TINYINT NULL,
               NoteN2 DECIMAL(8,2) NULL,
               NoteFinaleN DECIMAL(8,2) NULL,
               Jugement NVARCHAR(40) NULL,
               NouvelleFormationSuggestee NVARCHAR(MAX) NULL,
               DateSaisie DATETIME NULL,
               DateModification DATETIME NULL,
               CONSTRAINT UQ_WEB_FORM_EVAL_ADM UNIQUE (ID_Formation, MatriculeParticipant, TypeEval)
           )""",
        """IF OBJECT_ID('dbo.WEB_FORMATION_NOTIFICATION', 'U') IS NULL
           CREATE TABLE dbo.WEB_FORMATION_NOTIFICATION (
               ID INT IDENTITY(1,1) PRIMARY KEY,
               MatriculeDest INT NOT NULL,
               TypeNotif NVARCHAR(50) NOT NULL,
               Message NVARCHAR(500) NOT NULL,
               ID_Formation INT NULL,
               ID_Demande INT NULL,
               Lu BIT NOT NULL DEFAULT 0,
               EmailEnvoye BIT NOT NULL DEFAULT 0,
               DateCreation DATETIME NOT NULL DEFAULT GETDATE()
           )""",
        """IF OBJECT_ID('dbo.WEB_FORMATION_RAPPEL_FROID', 'U') IS NULL
           CREATE TABLE dbo.WEB_FORMATION_RAPPEL_FROID (
               ID INT IDENTITY(1,1) PRIMARY KEY,
               ID_Formation INT NOT NULL,
               MatriculeParticipant INT NOT NULL,
               ProfilEval NVARCHAR(20) NOT NULL DEFAULT 'ADMIN',
               DateEvalFroid DATE NOT NULL,
               RappelEnvoye BIT NOT NULL DEFAULT 0,
               DateRappelEnvoye DATETIME NULL,
               CONSTRAINT UQ_WEB_FORM_RAPPEL UNIQUE (ID_Formation, MatriculeParticipant, ProfilEval)
           )""",
    ]
    with get_db_cursor() as cursor:
        for block in sql_blocks:
            cursor.execute(block)
        try:
            cursor.execute("""
                IF COL_LENGTH('dbo.WEB_FORMATION', 'Formateur') IS NOT NULL
                   AND COL_LENGTH('dbo.WEB_FORMATION', 'Formateur') < 1000
                ALTER TABLE dbo.WEB_FORMATION ALTER COLUMN Formateur NVARCHAR(1000) NULL
            """)
        except Exception as e:
            print(f'[Projet 26] migrate Formateur: {e}')
        for mig in (
            "IF COL_LENGTH('dbo.WEB_FORMATION_DEMANDE', 'OrganismePropose') IS NULL "
            "ALTER TABLE dbo.WEB_FORMATION_DEMANDE ADD OrganismePropose NVARCHAR(300) NULL",
            "IF COL_LENGTH('dbo.WEB_FORMATION_DEMANDE', 'OrganismePropose') IS NOT NULL "
            "AND COL_LENGTH('dbo.WEB_FORMATION_DEMANDE', 'FormateurPropose') IS NULL "
            "ALTER TABLE dbo.WEB_FORMATION_DEMANDE ADD FormateurPropose NVARCHAR(300) NULL",
        ):
            try:
                cursor.execute(mig)
            except Exception as e:
                print(f'[Projet 26] migrate demande colonnes: {e}')
        cursor.connection.commit()


def _parse_formateurs_list(data):
    """Retourne la liste des noms de formateurs (au moins un) ou (None, message d'erreur)."""
    raw_list = data.get('formateurs')
    names = []
    if isinstance(raw_list, list):
        for item in raw_list:
            if isinstance(item, dict):
                n = (item.get('nom') or item.get('name') or '').strip()
            else:
                n = str(item or '').strip()
            if n and n not in names:
                names.append(n)
    if not names:
        raw = (data.get('formateur') or '').strip()
        if raw:
            for part in raw.replace(';', ',').split(','):
                n = part.strip()
                if n and n not in names:
                    names.append(n)
    if not names:
        return None, 'Au moins un formateur est obligatoire.'
    joined = ' ; '.join(names)
    if len(joined) > 1000:
        return None, 'Liste des formateurs trop longue (max 1000 caractères).'
    return joined, None


def ensure_projet26_in_web_projets():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = ?", (NUM_PROJ,))
            if cursor.fetchone():
                return
            cursor.execute("""
                INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive)
                VALUES (?, 'Projet 26', N'Gestion des formations', 0)
            """, (NUM_PROJ,))
            cursor.connection.commit()
            print('[Projet 26] WEB_PROJETS ajouté.')
    except Exception as e:
        print(f'[Projet 26] ensure_projet26_in_web_projets: {e}')


def _parse_date(val):
    if not val:
        return None
    if isinstance(val, date):
        return val
    s = str(val).strip()[:10]
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None


def format_periode(date_debut, date_fin):
    d1 = _parse_date(date_debut)
    d2 = _parse_date(date_fin)
    if not d1:
        return ''
    if not d2 or d1 == d2:
        return d1.strftime('%d/%m/%Y')
    return f"du {d1.strftime('%d/%m/%Y')} au {d2.strftime('%d/%m/%Y')}"


def _calc_n1_admin(notes):
    vals = [n for n in notes if n is not None]
    if len(vals) != 8:
        return None
    return round(float(sum(vals)), 2)


def _calc_n2_admin(n1, n2, n3):
    if n1 is None or n2 is None or n3 is None:
        return None
    return round(float(n1 * 4 + n2 * 4 + n3 * 4), 2)


def _calc_n_finale(n1, n2):
    if n1 is None or n2 is None:
        return None
    return round((float(n1) + float(n2)) / 100.0, 2)


def _jugement_from_n(n_finale):
    if n_finale is None:
        return None
    # N = (N1+N2)/100 → score sur 100 = N×100 = N1+N2
    score = float(n_finale) * 100
    if score > 70:
        return 'EFFICACE'
    if score >= 50:
        return 'NON_EFFICACE_REFAIRE'
    return 'NON_EFFICACE_MODIFIER'


def _jugement_label(code):
    return {
        'EFFICACE': 'Efficace',
        'NON_EFFICACE_REFAIRE': 'Non efficace à refaire',
        'NON_EFFICACE_MODIFIER': 'Non efficace à modifier',
    }.get(code, code or '')


def _type_formation_label(code):
    return {
        'INTRA': 'Intra-entreprise',
        'INTER': 'Inter-entreprise',
        'EN_LIGNE': 'En ligne',
    }.get(code, code or '')


def _statut_label(statut):
    return {
        'EN_ATTENTE': 'En attente',
        'VALIDE': 'Validée',
        'REFUSE': 'Refusée',
        'ANNULE': 'Annulée',
    }.get(statut, statut or '')


def _row_demande_beneficiaires(cursor, demande_id):
    cursor.execute("""
        SELECT B.Matricule, P.Nom, P.Prenom
        FROM WEB_FORMATION_DEMANDE_BENEFICIAIRE B
        LEFT JOIN personel P ON P.Matricule = B.Matricule
        WHERE B.ID_Demande = ?
        ORDER BY P.Nom, P.Prenom
    """, (demande_id,))
    out = []
    for r in cursor.fetchall():
        label = f"{r.Nom or ''} {r.Prenom or ''}".strip()
        out.append({
            'matricule': r.Matricule,
            'nom': r.Nom or '',
            'prenom': r.Prenom or '',
            'label': label or str(r.Matricule),
        })
    return out


def _demande_organisme_formateur_from_row(row):
    org = (getattr(row, 'OrganismePropose', None) or '').strip()
    frm = (getattr(row, 'FormateurPropose', None) or '').strip()
    if not org and not frm:
        legacy = (getattr(row, 'OrganismeFormateurPropose', None) or '').strip()
        if legacy:
            org = legacy
    if getattr(row, 'Statut', None) == 'VALIDE':
        ff = (getattr(row, 'FormationFormateur', None) or '').strip()
        if ff:
            frm = ff
    return org, frm


def _serialize_demande(row, beneficiaires=None):
    mgr = get_person(row.MatriculeManager)
    val = get_person(row.MatriculeValidateurRH) if row.MatriculeValidateurRH else None
    d1 = row.DateDebutSouhaitee
    d2 = row.DateFinSouhaitee
    if d1 and not d2:
        d2 = d1
    org, frm = _demande_organisme_formateur_from_row(row)
    return {
        'id': row.ID,
        'date_demande': row.DateDemande.isoformat() if row.DateDemande else None,
        'matricule_manager': row.MatriculeManager,
        'manager_label': mgr['label'] if mgr else str(row.MatriculeManager),
        'theme': row.Theme or '',
        'type_formation': row.TypeFormation,
        'type_formation_label': _type_formation_label(row.TypeFormation),
        'organisme_propose': org,
        'formateur_propose': frm,
        'organisme_formateur_propose': ' ; '.join(p for p in (org, frm) if p),
        'date_debut_souhaitee': d1.isoformat() if d1 else None,
        'date_fin_souhaitee': d2.isoformat() if d2 else None,
        'periode_souhaitee': format_periode(d1, d2),
        'objectif1': row.Objectif1 or '',
        'objectif2': row.Objectif2 or '',
        'objectif3': row.Objectif3 or '',
        'statut': row.Statut,
        'statut_label': _statut_label(row.Statut),
        'matricule_validateur_rh': row.MatriculeValidateurRH,
        'validateur_rh_label': val['label'] if val else '',
        'date_validation_rh': row.DateValidationRH.isoformat() if row.DateValidationRH else None,
        'commentaire_refus': row.CommentaireRefus or '',
        'beneficiaires': beneficiaires or [],
        'date_creation': row.DateCreation.isoformat() if row.DateCreation else None,
        'numero_formation': (getattr(row, 'FormationNumero', None) or getattr(row, 'NumeroFormation', None) or '') or '',
    }


def _can_see_all(matricule, is_super=False):
    return is_super or is_rh(matricule, is_super)


def _demande_visible_for(matricule, demande_id, is_super=False):
    if _can_see_all(matricule, is_super):
        return True
    m = _int_mat(matricule)
    if m is None:
        return False
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 1 FROM WEB_FORMATION_DEMANDE D
            WHERE D.ID = ? AND (
                D.MatriculeManager = ?
                OR EXISTS (
                    SELECT 1 FROM WEB_FORMATION_DEMANDE_BENEFICIAIRE B
                    WHERE B.ID_Demande = D.ID AND B.Matricule = ?
                )
            )
        """, (demande_id, m, m))
        return cursor.fetchone() is not None


def _can_edit_demande(matricule, demande_id, is_super=False):
    d = get_demande(demande_id)
    if not d:
        return False
    statut = d['statut']
    if statut == 'REFUSE':
        return False
    if _can_see_all(matricule, is_super):
        return statut in ('EN_ATTENTE', 'VALIDE')
    if statut == 'EN_ATTENTE':
        return _int_mat(matricule) == d['matricule_manager']
    return False


def list_demandes(matricule_connecte, is_super=False, statut=None):
    clauses = ['1=1']
    params = []
    if statut:
        clauses.append('D.Statut = ?')
        params.append(statut)
    if not _can_see_all(matricule_connecte, is_super):
        m = _int_mat(matricule_connecte)
        clauses.append('(D.MatriculeManager = ? OR EXISTS (SELECT 1 FROM WEB_FORMATION_DEMANDE_BENEFICIAIRE B WHERE B.ID_Demande = D.ID AND B.Matricule = ?))')
        params.extend([m, m])
    sql = f"""
        SELECT D.*, F.NumeroFormation AS FormationNumero, F.Formateur AS FormationFormateur
        FROM WEB_FORMATION_DEMANDE D
        LEFT JOIN WEB_FORMATION F ON F.ID_Demande = D.ID
        WHERE {' AND '.join(clauses)}
        ORDER BY D.DateCreation DESC
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        out = []
        for row in rows:
            bens = _row_demande_beneficiaires(cursor, row.ID)
            out.append(_serialize_demande(row, bens))
        return out


def get_demande(demande_id):
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT D.*, F.NumeroFormation AS FormationNumero, F.Formateur AS FormationFormateur
            FROM WEB_FORMATION_DEMANDE D
            LEFT JOIN WEB_FORMATION F ON F.ID_Demande = D.ID
            WHERE D.ID = ?
        """, (demande_id,))
        row = cursor.fetchone()
        if not row:
            return None
        bens = _row_demande_beneficiaires(cursor, row.ID)
        return _serialize_demande(row, bens)


def list_personel_pour_demande(matricule_connecte=None, is_super=False):
    """Tous les collaborateurs actifs — le manager peut choisir hors équipe."""
    return list_personel_actifs('')


def get_equipe_manager_matricules(matricule_connecte, is_super=False):
    """Matricules de l'équipe du manager (indication visuelle uniquement)."""
    if is_super or is_rh(matricule_connecte, is_super):
        return []
    return p25.get_subordonnes_matricules(matricule_connecte) or []


# Alias conservé pour compatibilité
def list_equipe_pour_demande(matricule_connecte, is_super=False):
    return list_personel_pour_demande(matricule_connecte, is_super)


def create_demande(data, matricule_connecte, is_super=False):
    m_saisie = _int_mat(matricule_connecte)
    if m_saisie is None:
        return None, 'Matricule connecté invalide.'
    if _can_see_all(matricule_connecte, is_super):
        manager_mat = _int_mat(data.get('matricule_manager'))
        if not manager_mat:
            return None, 'Responsable demandeur obligatoire.'
        if not get_person(manager_mat):
            return None, 'Responsable demandeur introuvable.'
    else:
        manager_mat = m_saisie
    theme = (data.get('theme') or '').strip()
    if not theme:
        return None, 'Thème obligatoire.'
    type_f = (data.get('type_formation') or '').strip().upper()
    if type_f not in TYPES_FORMATION:
        return None, 'Type de formation invalide.'
    beneficiaires = data.get('beneficiaires') or []
    mats = []
    for b in beneficiaires:
        bm = _int_mat(b.get('matricule') if isinstance(b, dict) else b)
        if bm and bm not in mats:
            mats.append(bm)
    if not mats:
        return None, 'Au moins un bénéficiaire est requis.'
    d1 = _parse_date(data.get('date_debut_souhaitee'))
    d2 = _parse_date(data.get('date_fin_souhaitee'))
    un_jour = bool(data.get('un_seul_jour'))
    if un_jour:
        if not d1:
            return None, 'Date souhaitée obligatoire.'
        d2 = d1
    else:
        if not d1 or not d2:
            return None, 'Période souhaitée : date début et fin obligatoires.'
        if d2 < d1:
            return None, 'La date de fin doit être >= date de début.'
    obj1 = (data.get('objectif1') or '').strip()
    obj2 = (data.get('objectif2') or '').strip()
    obj3 = (data.get('objectif3') or '').strip()
    if not (obj1 and obj2 and obj3):
        return None, 'Les 3 objectifs sont obligatoires.'
    organisme_propose = (data.get('organisme_propose') or '').strip() or None
    formateur_propose = (data.get('formateur_propose') or '').strip() or None
    if not organisme_propose and not formateur_propose:
        legacy = (data.get('organisme_formateur_propose') or '').strip()
        if legacy:
            organisme_propose = legacy
    combined_legacy = ' ; '.join(p for p in (organisme_propose, formateur_propose) if p) or None
    date_demande = _parse_date(data.get('date_demande')) or date.today()
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO WEB_FORMATION_DEMANDE (
                DateDemande, MatriculeManager, MatriculeSaisiePar, Theme, TypeFormation,
                OrganismeFormateurPropose, OrganismePropose, FormateurPropose,
                DateDebutSouhaitee, DateFinSouhaitee,
                Objectif1, Objectif2, Objectif3, Statut
            )
            OUTPUT INSERTED.ID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'EN_ATTENTE')
        """, (
            date_demande, manager_mat, m_saisie, theme, type_f,
            combined_legacy, organisme_propose, formateur_propose,
            d1, d2, obj1, obj2, obj3,
        ))
        row = cursor.fetchone()
        new_id = int(row[0]) if row and row[0] is not None else None
        if new_id is None:
            return None, "Erreur lors de l'enregistrement de la demande."
        for bm in mats:
            cursor.execute(
                'INSERT INTO WEB_FORMATION_DEMANDE_BENEFICIAIRE (ID_Demande, Matricule) VALUES (?, ?)',
                (new_id, bm),
            )
        cursor.connection.commit()
    try:
        _notifier_rh_nouvelle_demande(new_id)
        _notifier_beneficiaires_demande(new_id)
    except Exception as e:
        print(f'[Projet26] notifications demande {new_id}: {e}')
    return get_demande(new_id), None


def update_demande(demande_id, data, matricule_connecte, is_super=False):
    if not _can_edit_demande(matricule_connecte, demande_id, is_super):
        return None, 'Modification non autorisée ou demande non modifiable.'
    d_cur = get_demande(demande_id)
    if not d_cur:
        return None, 'Demande introuvable.'
    statut = d_cur['statut']
    m_saisie = _int_mat(matricule_connecte)
    if m_saisie is None:
        return None, 'Matricule connecté invalide.'
    if _can_see_all(matricule_connecte, is_super):
        manager_mat = _int_mat(data.get('matricule_manager'))
        if not manager_mat:
            return None, 'Responsable demandeur obligatoire.'
        if not get_person(manager_mat):
            return None, 'Responsable demandeur introuvable.'
    else:
        manager_mat = d_cur['matricule_manager'] if d_cur else m_saisie
    theme = (data.get('theme') or '').strip()
    if not theme:
        return None, 'Thème obligatoire.'
    type_f = (data.get('type_formation') or '').strip().upper()
    if type_f not in TYPES_FORMATION:
        return None, 'Type de formation invalide.'
    beneficiaires = data.get('beneficiaires') or []
    mats = []
    for b in beneficiaires:
        bm = _int_mat(b.get('matricule') if isinstance(b, dict) else b)
        if bm and bm not in mats:
            mats.append(bm)
    if not mats:
        return None, 'Au moins un bénéficiaire est requis.'
    d1 = _parse_date(data.get('date_debut_souhaitee'))
    d2 = _parse_date(data.get('date_fin_souhaitee'))
    un_jour = bool(data.get('un_seul_jour'))
    if un_jour:
        if not d1:
            return None, 'Date souhaitée obligatoire.'
        d2 = d1
    else:
        if not d1 or not d2:
            return None, 'Période souhaitée : date début et fin obligatoires.'
        if d2 < d1:
            return None, 'La date de fin doit être >= date de début.'
    obj1 = (data.get('objectif1') or '').strip()
    obj2 = (data.get('objectif2') or '').strip()
    obj3 = (data.get('objectif3') or '').strip()
    if not (obj1 and obj2 and obj3):
        return None, 'Les 3 objectifs sont obligatoires.'
    organisme_propose = (data.get('organisme_propose') or '').strip() or None
    formateur_propose = (data.get('formateur_propose') or '').strip() or None
    if not organisme_propose and not formateur_propose:
        legacy = (data.get('organisme_formateur_propose') or '').strip()
        if legacy:
            organisme_propose = legacy
    combined_legacy = ' ; '.join(p for p in (organisme_propose, formateur_propose) if p) or None
    date_demande = _parse_date(data.get('date_demande'))
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE WEB_FORMATION_DEMANDE SET
                DateDemande = COALESCE(?, DateDemande),
                MatriculeManager = ?, Theme = ?, TypeFormation = ?,
                OrganismeFormateurPropose = ?, OrganismePropose = ?, FormateurPropose = ?,
                DateDebutSouhaitee = ?, DateFinSouhaitee = ?,
                Objectif1 = ?, Objectif2 = ?, Objectif3 = ?,
                DateModification = GETDATE()
            WHERE ID = ?
        """, (
            date_demande, manager_mat, theme, type_f,
            combined_legacy, organisme_propose, formateur_propose,
            d1, d2, obj1, obj2, obj3, demande_id,
        ))
        if cursor.rowcount == 0:
            return None, 'Demande introuvable.'
        cursor.execute(
            'DELETE FROM WEB_FORMATION_DEMANDE_BENEFICIAIRE WHERE ID_Demande = ?',
            (demande_id,),
        )
        for bm in mats:
            cursor.execute(
                'INSERT INTO WEB_FORMATION_DEMANDE_BENEFICIAIRE (ID_Demande, Matricule) VALUES (?, ?)',
                (demande_id, bm),
            )
        if statut == 'VALIDE':
            cursor.execute('SELECT ID FROM WEB_FORMATION WHERE ID_Demande = ?', (demande_id,))
            frow = cursor.fetchone()
            if frow:
                formation_id = int(frow.ID)
                cursor.execute("""
                    UPDATE WEB_FORMATION SET
                        Theme = ?, Objectif1 = ?, Objectif2 = ?, Objectif3 = ?,
                        DateDebut = ?, DateFin = ?, Formateur = ?
                    WHERE ID_Demande = ?
                """, (
                    theme, obj1, obj2, obj3, d1, d2, formateur_propose, demande_id,
                ))
                cursor.connection.commit()
                _planifier_rappels_froid(formation_id)
                return get_demande(demande_id), None
        cursor.connection.commit()
    return get_demande(demande_id), None


def _notifier_rh_nouvelle_demande(demande_id):
    d = get_demande(demande_id)
    if not d:
        return
    msg = f"Nouvelle demande de formation : {d['theme']} ({d['manager_label']})"
    emails = []
    for mat in p25.get_rh_matricules_actifs():
        _insert_notification(mat, 'NOUVELLE_DEMANDE', msg, id_demande=demande_id)
        p = get_person(mat)
        if p and p.get('email'):
            emails.append(p['email'])
    if emails:
        send_email(
            emails,
            '[Formations] Nouvelle demande à valider',
            f'<p>{msg}</p><p>Bénéficiaires : {", ".join(b["label"] for b in d["beneficiaires"])}</p>',
            msg,
        )


def _notifier_beneficiaires_demande(demande_id):
    d = get_demande(demande_id)
    if not d:
        return
    msg = f"Vous êtes inscrit(e) à une demande de formation : {d['theme']}"
    for b in d['beneficiaires']:
        _insert_notification(b['matricule'], 'DEMANDE_EQUIPE', msg, id_demande=demande_id)
        p = get_person(b['matricule'])
        if p and p.get('email'):
            send_email(
                p['email'],
                '[Formations] Demande de formation – votre équipe',
                f'<p>{msg}</p><p>Période souhaitée : {d["periode_souhaitee"]}</p>',
                msg,
            )


def _insert_notification(matricule_dest, type_notif, message, id_formation=None, id_demande=None):
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO WEB_FORMATION_NOTIFICATION (MatriculeDest, TypeNotif, Message, ID_Formation, ID_Demande)
            VALUES (?, ?, ?, ?, ?)
        """, (matricule_dest, type_notif, message[:500], id_formation, id_demande))
        cursor.connection.commit()


def valider_demande_rh(demande_id, data, matricule_connecte, is_super=False):
    if not is_rh(matricule_connecte, is_super):
        return None, 'Seule la RH peut valider.'
    d = get_demande(demande_id)
    if not d:
        return None, 'Demande introuvable.'
    if d['statut'] != 'EN_ATTENTE':
        return None, 'Demande déjà traitée.'
    formateur, err_f = _parse_formateurs_list(data)
    if err_f:
        return None, err_f
    d1 = _parse_date(data.get('date_debut'))
    d2 = _parse_date(data.get('date_fin'))
    un_jour = bool(data.get('un_seul_jour'))
    if un_jour:
        if not d1:
            return None, 'Date de formation obligatoire.'
        d2 = d1
    else:
        if not d1 or not d2:
            return None, 'Dates début et fin de formation obligatoires.'
        if d2 < d1:
            return None, 'Date fin >= date début.'
    theme = (data.get('theme') or d['theme']).strip()
    type_f = (data.get('type_formation') or d['type_formation'] or '').strip().upper()
    if type_f not in TYPES_FORMATION:
        return None, 'Type de formation invalide.'
    obj1 = (data.get('objectif1') or d['objectif1']).strip()
    obj2 = (data.get('objectif2') or d['objectif2']).strip()
    obj3 = (data.get('objectif3') or d['objectif3']).strip()
    beneficiaires = data.get('beneficiaires')
    if beneficiaires is not None:
        mats = []
        for b in beneficiaires:
            bm = _int_mat(b.get('matricule') if isinstance(b, dict) else b)
            if bm and bm not in mats:
                mats.append(bm)
    else:
        mats = [b['matricule'] for b in d.get('beneficiaires') or []]
    if not mats:
        return None, 'Au moins un bénéficiaire est requis pour la formation.'
    m = _int_mat(matricule_connecte)
    annee = d2.year
    with get_db_cursor() as cursor:
        cursor.execute(
            'SELECT ISNULL(MAX(SeqAnnee), 0) AS M FROM WEB_FORMATION WHERE Annee = ?',
            (annee,),
        )
        seq = int(cursor.fetchone().M) + 1
        numero = f'{seq:02d}{annee}'
        cursor.execute("""
            UPDATE WEB_FORMATION_DEMANDE
            SET Statut = 'VALIDE', MatriculeValidateurRH = ?, DateValidationRH = GETDATE(),
                Theme = ?, TypeFormation = ?, Objectif1 = ?, Objectif2 = ?, Objectif3 = ?,
                DateDebutSouhaitee = ?, DateFinSouhaitee = ?,
                DateModification = GETDATE()
            WHERE ID = ?
        """, (m, theme, type_f, obj1, obj2, obj3, d1, d2, demande_id))
        cursor.execute(
            'DELETE FROM WEB_FORMATION_DEMANDE_BENEFICIAIRE WHERE ID_Demande = ?',
            (demande_id,),
        )
        for bm in mats:
            cursor.execute(
                'INSERT INTO WEB_FORMATION_DEMANDE_BENEFICIAIRE (ID_Demande, Matricule) VALUES (?, ?)',
                (demande_id, bm),
            )
        cursor.execute("""
            INSERT INTO WEB_FORMATION (
                ID_Demande, NumeroFormation, Annee, SeqAnnee, Theme, Formateur,
                Objectif1, Objectif2, Objectif3, DateDebut, DateFin
            )
            OUTPUT INSERTED.ID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (demande_id, numero, annee, seq, theme, formateur, obj1, obj2, obj3, d1, d2))
        row = cursor.fetchone()
        formation_id = int(row[0]) if row and row[0] is not None else None
        if formation_id is None:
            return None, "Erreur lors de la création de la formation."
        cursor.connection.commit()
    _planifier_rappels_froid(formation_id)
    _notifier_manager_demande_statut(demande_id, 'VALIDE', numero)
    return get_formation(formation_id), None


def refuser_demande_rh(demande_id, commentaire, matricule_connecte, is_super=False):
    if not is_rh(matricule_connecte, is_super):
        return None, 'Seule la RH peut refuser.'
    if not (commentaire or '').strip():
        return None, 'Commentaire de refus obligatoire.'
    d = get_demande(demande_id)
    if not d or d['statut'] != 'EN_ATTENTE':
        return None, 'Demande introuvable ou déjà traitée.'
    m = _int_mat(matricule_connecte)
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE WEB_FORMATION_DEMANDE
            SET Statut = 'REFUSE', MatriculeValidateurRH = ?, DateValidationRH = GETDATE(),
                CommentaireRefus = ?, DateModification = GETDATE()
            WHERE ID = ?
        """, (m, commentaire.strip(), demande_id))
        cursor.connection.commit()
    _notifier_manager_demande_statut(demande_id, 'REFUSE')
    return get_demande(demande_id), None


def _notifier_manager_demande_statut(demande_id, statut, numero=None):
    d = get_demande(demande_id)
    if not d:
        return
    if statut == 'VALIDE':
        msg = f"Demande validée – formation n° {numero} créée : {d['theme']}"
    else:
        msg = f"Demande refusée : {d['theme']}"
    _insert_notification(d['matricule_manager'], f'DEMANDE_{statut}', msg, id_demande=demande_id)
    p = get_person(d['matricule_manager'])
    if p and p.get('email'):
        send_email(p['email'], f'[Formations] Demande {statut.lower()}', f'<p>{msg}</p>', msg)


def _serialize_formation(row, cursor=None):
    d = None
    beneficiaires = []
    if cursor:
        cursor.execute('SELECT ID_Demande FROM WEB_FORMATION WHERE ID = ?', (row.ID,))
        id_dem = row.ID_Demande
        beneficiaires = _row_demande_beneficiaires(cursor, id_dem)
    return {
        'id': row.ID,
        'id_demande': row.ID_Demande,
        'numero_formation': row.NumeroFormation,
        'theme': row.Theme or '',
        'formateur': row.Formateur or '',
        'objectif1': row.Objectif1 or '',
        'objectif2': row.Objectif2 or '',
        'objectif3': row.Objectif3 or '',
        'date_debut': row.DateDebut.isoformat() if row.DateDebut else None,
        'date_fin': row.DateFin.isoformat() if row.DateFin else None,
        'periode': format_periode(row.DateDebut, row.DateFin),
        'date_eval_chaud': row.DateFin.isoformat() if row.DateFin else None,
        'date_eval_froid_admin': _date_eval_froid(row.DateFin, MOIS_EVAL_FROID_ADMIN),
        'beneficiaires': beneficiaires,
        'date_creation': row.DateCreation.isoformat() if row.DateCreation else None,
    }


def _date_eval_froid(date_fin, mois):
    df = _parse_date(date_fin)
    if not df:
        return None
    month = df.month + mois
    year = df.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    day = min(df.day, 28)
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return date(year, month, 28).isoformat()


def get_formation(formation_id):
    with get_db_cursor() as cursor:
        cursor.execute('SELECT * FROM WEB_FORMATION WHERE ID = ?', (formation_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return _serialize_formation(row, cursor)


def list_formations(matricule_connecte, is_super=False):
    if _can_see_all(matricule_connecte, is_super):
        sql = 'SELECT * FROM WEB_FORMATION ORDER BY DateCreation DESC'
        params = []
    else:
        m = _int_mat(matricule_connecte)
        sql = """
            SELECT F.* FROM WEB_FORMATION F
            INNER JOIN WEB_FORMATION_DEMANDE D ON D.ID = F.ID_Demande
            WHERE D.MatriculeManager = ?
               OR EXISTS (
                   SELECT 1 FROM WEB_FORMATION_DEMANDE_BENEFICIAIRE B
                   WHERE B.ID_Demande = D.ID AND B.Matricule = ?
               )
            ORDER BY F.DateCreation DESC
        """
        params = [m, m]
    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        return [_serialize_formation(r, cursor) for r in cursor.fetchall()]


def _planifier_rappels_froid(formation_id):
    f = get_formation(formation_id)
    if not f:
        return
    date_froid = _parse_date(f['date_eval_froid_admin'])
    if not date_froid:
        return
    with get_db_cursor() as cursor:
        for b in f['beneficiaires']:
            if not is_staff_administratif(b['matricule']):
                continue
            cursor.execute("""
                SELECT 1 FROM WEB_FORMATION_RAPPEL_FROID
                WHERE ID_Formation = ? AND MatriculeParticipant = ? AND ProfilEval = 'ADMIN'
            """, (formation_id, b['matricule']))
            if cursor.fetchone():
                continue
            cursor.execute("""
                INSERT INTO WEB_FORMATION_RAPPEL_FROID (
                    ID_Formation, MatriculeParticipant, ProfilEval, DateEvalFroid
                ) VALUES (?, ?, 'ADMIN', ?)
            """, (formation_id, b['matricule'], date_froid))
        cursor.connection.commit()


def process_rappels_eval_froid():
    """Notification RH J-1 avant évaluation à froid (admin)."""
    demain = date.today() + timedelta(days=JOURS_RAPPEL_AVANT_FROID)
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT R.*, F.NumeroFormation, F.Theme
            FROM WEB_FORMATION_RAPPEL_FROID R
            INNER JOIN WEB_FORMATION F ON F.ID = R.ID_Formation
            WHERE R.ProfilEval = 'ADMIN' AND R.RappelEnvoye = 0 AND R.DateEvalFroid = ?
        """, (demain,))
        rows = cursor.fetchall()
        if not rows:
            return
        rh_mats = p25.get_rh_matricules_actifs()
        emails = []
        for mat in rh_mats:
            p = get_person(mat)
            if p and p.get('email'):
                emails.append(p['email'])
        for row in rows:
            part = get_person(row.MatriculeParticipant)
            plabel = part['label'] if part else str(row.MatriculeParticipant)
            msg = (
                f"Évaluation à froid (admin) demain pour {plabel} – "
                f"formation {row.NumeroFormation} ({row.Theme})"
            )
            for mat in rh_mats:
                _insert_notification(mat, 'RAPPEL_EVAL_FROID', msg, id_formation=row.ID_Formation)
            cursor.execute("""
                UPDATE WEB_FORMATION_RAPPEL_FROID
                SET RappelEnvoye = 1, DateRappelEnvoye = GETDATE()
                WHERE ID = ?
            """, (row.ID,))
        cursor.connection.commit()
        if emails and rows:
            body_lines = []
            for row in rows:
                part = get_person(row.MatriculeParticipant)
                plabel = part['label'] if part else str(row.MatriculeParticipant)
                body_lines.append(
                    f"<li>{plabel} – {row.NumeroFormation} – {row.Theme} – "
                    f"date froid : {row.DateEvalFroid}</li>"
                )
            send_email(
                emails,
                '[Formations] Rappel évaluations à froid (demain)',
                '<p>Évaluations à froid prévues demain :</p><ul>' + ''.join(body_lines) + '</ul>',
                'Rappel évaluations à froid demain',
            )


def list_notifications(matricule, lu=None):
    m = _int_mat(matricule)
    clauses = ['MatriculeDest = ?']
    params = [m]
    if lu is not None:
        clauses.append('Lu = ?')
        params.append(1 if lu else 0)
    with get_db_cursor() as cursor:
        cursor.execute(f"""
            SELECT TOP 50 * FROM WEB_FORMATION_NOTIFICATION
            WHERE {' AND '.join(clauses)}
            ORDER BY DateCreation DESC
        """, params)
        return [{
            'id': r.ID,
            'type': r.TypeNotif,
            'message': r.Message,
            'id_formation': r.ID_Formation,
            'id_demande': r.ID_Demande,
            'lu': bool(r.Lu),
            'date_creation': r.DateCreation.isoformat() if r.DateCreation else None,
        } for r in cursor.fetchall()]


def marquer_notifications_lues(matricule):
    m = _int_mat(matricule)
    with get_db_cursor() as cursor:
        cursor.execute(
            'UPDATE WEB_FORMATION_NOTIFICATION SET Lu = 1 WHERE MatriculeDest = ? AND Lu = 0',
            (m,),
        )
        cursor.connection.commit()


def _serialize_eval(row):
    part = get_person(row.MatriculeParticipant)
    return {
        'id': row.ID,
        'id_formation': row.ID_Formation,
        'matricule_participant': row.MatriculeParticipant,
        'participant_label': part['label'] if part else str(row.MatriculeParticipant),
        'type_eval': row.TypeEval,
        'note_duree': row.NoteDuree,
        'note_horaires': row.NoteHoraires,
        'note_organisation': row.NoteOrganisation,
        'note_local_equip': row.NoteLocalEquip,
        'note_pedagogie': row.NotePedagogie,
        'note_obj1': row.NoteObj1,
        'note_obj2': row.NoteObj2,
        'note_obj3': row.NoteObj3,
        'note_n1': float(row.NoteN1) if row.NoteN1 is not None else None,
        'attentes_besoins': row.AttentesBesoins or '',
        'propositions': row.Propositions or '',
        'note_cold_obj1': row.NoteColdObj1,
        'note_cold_obj2': row.NoteColdObj2,
        'note_cold_obj3': row.NoteColdObj3,
        'note_n2': float(row.NoteN2) if row.NoteN2 is not None else None,
        'note_finale_n': float(row.NoteFinaleN) if row.NoteFinaleN is not None else None,
        'jugement': row.Jugement,
        'jugement_label': _jugement_label(row.Jugement),
        'nouvelle_formation_suggestee': row.NouvelleFormationSuggestee or '',
        'date_saisie': row.DateSaisie.isoformat() if row.DateSaisie else None,
    }


def list_evaluations_admin(matricule_connecte, is_super=False, id_formation=None):
    """Une ligne par formation + participant (éval. chaud et froid regroupées)."""
    clauses = ['1=1']
    params = []
    if id_formation:
        clauses.append('E.ID_Formation = ?')
        params.append(id_formation)
    if not _can_see_all(matricule_connecte, is_super):
        m = _int_mat(matricule_connecte)
        clauses.append('''(
            E.MatriculeParticipant = ?
            OR EXISTS (
                SELECT 1 FROM WEB_FORMATION F2
                INNER JOIN WEB_FORMATION_DEMANDE D ON D.ID = F2.ID_Demande
                WHERE F2.ID = E.ID_Formation AND D.MatriculeManager = ?
            )
            OR EXISTS (
                SELECT 1 FROM WEB_FORMATION F2
                INNER JOIN WEB_FORMATION_DEMANDE_BENEFICIAIRE B ON B.ID_Demande = F2.ID_Demande
                WHERE F2.ID = E.ID_Formation AND B.Matricule = ?
                  AND E.TypeEval = 'FROID'
                  AND EXISTS (
                      SELECT 1 FROM WEB_CONGE_VALIDATEUR_LIEN V
                      WHERE V.MatriculeValidateur = ? AND V.MatriculeEmploye = E.MatriculeParticipant
                  )
            )
        )''')
        params.extend([m, m, m, m])
    sql = f"""
        SELECT P.ID_Formation, P.MatriculeParticipant,
               F.NumeroFormation, F.Theme,
               CH.NoteN1, CH.DateSaisie AS DateChaud,
               FR.NoteN2, FR.NoteFinaleN, FR.Jugement, FR.DateSaisie AS DateFroid
        FROM (
            SELECT DISTINCT E.ID_Formation, E.MatriculeParticipant
            FROM WEB_FORMATION_EVAL_ADMIN E
            WHERE {' AND '.join(clauses)}
        ) P
        INNER JOIN WEB_FORMATION F ON F.ID = P.ID_Formation
        LEFT JOIN WEB_FORMATION_EVAL_ADMIN CH
            ON CH.ID_Formation = P.ID_Formation
           AND CH.MatriculeParticipant = P.MatriculeParticipant
           AND CH.TypeEval = 'CHAUD'
        LEFT JOIN WEB_FORMATION_EVAL_ADMIN FR
            ON FR.ID_Formation = P.ID_Formation
           AND FR.MatriculeParticipant = P.MatriculeParticipant
           AND FR.TypeEval = 'FROID'
        ORDER BY COALESCE(FR.DateSaisie, CH.DateSaisie) DESC, P.ID_Formation DESC
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        out = []
        for row in cursor.fetchall():
            part = get_person(row.MatriculeParticipant)
            n1 = float(row.NoteN1) if row.NoteN1 is not None else None
            n2 = float(row.NoteN2) if row.NoteN2 is not None else None
            n_finale = float(row.NoteFinaleN) if row.NoteFinaleN is not None else None
            if n_finale is None and n1 is not None and n2 is not None:
                n_finale = _calc_n_finale(n1, n2)
            out.append({
                'id_formation': row.ID_Formation,
                'matricule_participant': row.MatriculeParticipant,
                'participant_label': part['label'] if part else str(row.MatriculeParticipant),
                'numero_formation': row.NumeroFormation,
                'theme': row.Theme or '',
                'note_n1': n1,
                'note_n2': n2,
                'note_finale_n': n_finale,
                'jugement': row.Jugement,
                'jugement_label': _jugement_label(row.Jugement),
                'date_chaud': row.DateChaud.isoformat() if row.DateChaud else None,
                'date_froid': row.DateFroid.isoformat() if row.DateFroid else None,
                'has_chaud': row.DateChaud is not None or row.NoteN1 is not None,
                'has_froid': row.DateFroid is not None or row.NoteN2 is not None,
            })
        return out


def get_eval_admin(eval_id):
    with get_db_cursor() as cursor:
        cursor.execute('SELECT * FROM WEB_FORMATION_EVAL_ADMIN WHERE ID = ?', (eval_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return _serialize_eval(row)


def get_evals_participant(id_formation, matricule_participant):
    """Retourne les évaluations chaud/froid d'un participant pour une formation."""
    fid = int(id_formation)
    part = _int_mat(matricule_participant)
    chaud = froid = None
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM WEB_FORMATION_EVAL_ADMIN
            WHERE ID_Formation = ? AND MatriculeParticipant = ?
        """, (fid, part))
        for row in cursor.fetchall():
            if row.TypeEval == 'CHAUD':
                chaud = _serialize_eval(row)
            elif row.TypeEval == 'FROID':
                froid = _serialize_eval(row)
    n1 = chaud.get('note_n1') if chaud else None
    n2 = froid.get('note_n2') if froid else None
    n_finale = froid.get('note_finale_n') if froid else None
    if n_finale is None and n1 is not None and n2 is not None:
        n_finale = _calc_n_finale(n1, n2)
    return {
        'chaud': chaud,
        'froid': froid,
        'note_n1': n1,
        'note_n2': n2,
        'note_finale_n': n_finale,
    }


def _can_saisir_eval_chaud(matricule, formation_id, participant_mat, is_super=False):
    if _can_see_all(matricule, is_super):
        return True
    return _int_mat(matricule) == _int_mat(participant_mat)


def _can_saisir_eval_froid(matricule, participant_mat, is_super=False):
    if _can_see_all(matricule, is_super):
        return True
    m = _int_mat(matricule)
    val, _ = get_validateur_for_employe(participant_mat)
    return val == m


def save_eval_admin_chaud(data, matricule_connecte, is_super=False):
    fid = data.get('id_formation')
    part = _int_mat(data.get('matricule_participant'))
    if not fid or not part:
        return None, 'Formation et participant obligatoires.'
    f = get_formation(fid)
    if not f:
        return None, 'Formation introuvable.'
    if part not in [b['matricule'] for b in f['beneficiaires']]:
        return None, 'Participant non inscrit à cette formation.'
    if not _can_saisir_eval_chaud(matricule_connecte, fid, part, is_super):
        return None, 'Non autorisé à saisir cette évaluation.'
    notes = [
        _int_note(data.get('note_duree')),
        _int_note(data.get('note_horaires')),
        _int_note(data.get('note_organisation')),
        _int_note(data.get('note_local_equip')),
        _int_note(data.get('note_pedagogie')),
        _int_note(data.get('note_obj1')),
        _int_note(data.get('note_obj2')),
        _int_note(data.get('note_obj3')),
    ]
    if any(n is None for n in notes):
        return None, 'Les 8 notes (1 à 5) sont obligatoires.'
    n1 = _calc_n1_admin(notes)
    m = _int_mat(matricule_connecte)
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT ID FROM WEB_FORMATION_EVAL_ADMIN
            WHERE ID_Formation = ? AND MatriculeParticipant = ? AND TypeEval = 'CHAUD'
        """, (fid, part))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE WEB_FORMATION_EVAL_ADMIN SET
                    MatriculeSaisiePar = ?, NoteDuree = ?, NoteHoraires = ?, NoteOrganisation = ?,
                    NoteLocalEquip = ?, NotePedagogie = ?, NoteObj1 = ?, NoteObj2 = ?, NoteObj3 = ?,
                    NoteN1 = ?, AttentesBesoins = ?, Propositions = ?,
                    DateModification = GETDATE(), DateSaisie = GETDATE()
                WHERE ID = ?
            """, (
                m, *notes, n1,
                (data.get('attentes_besoins') or '').strip() or None,
                (data.get('propositions') or '').strip() or None,
                existing.ID,
            ))
            eid = existing.ID
        else:
            cursor.execute("""
                INSERT INTO WEB_FORMATION_EVAL_ADMIN (
                    ID_Formation, MatriculeParticipant, TypeEval, MatriculeSaisiePar,
                    NoteDuree, NoteHoraires, NoteOrganisation, NoteLocalEquip, NotePedagogie,
                    NoteObj1, NoteObj2, NoteObj3, NoteN1, AttentesBesoins, Propositions, DateSaisie
                )
                OUTPUT INSERTED.ID
                VALUES (?, ?, 'CHAUD', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (fid, part, m, *notes, n1,
                  (data.get('attentes_besoins') or '').strip() or None,
                  (data.get('propositions') or '').strip() or None))
            row = cursor.fetchone()
            eid = int(row[0]) if row and row[0] is not None else None
            if eid is None:
                return None, "Erreur lors de l'enregistrement de l'évaluation."
        cursor.connection.commit()
    return get_eval_admin(eid), None


def save_eval_admin_froid(data, matricule_connecte, is_super=False):
    fid = data.get('id_formation')
    part = _int_mat(data.get('matricule_participant'))
    if not fid or not part:
        return None, 'Formation et participant obligatoires.'
    if not _can_saisir_eval_froid(matricule_connecte, part, is_super):
        return None, 'Seul le supérieur hiérarchique ou la RH peut saisir l’évaluation à froid.'
    nc1 = _int_note(data.get('note_cold_obj1'))
    nc2 = _int_note(data.get('note_cold_obj2'))
    nc3 = _int_note(data.get('note_cold_obj3'))
    if any(n is None for n in (nc1, nc2, nc3)):
        return None, 'Les 3 notes à froid sont obligatoires.'
    n2 = _calc_n2_admin(nc1, nc2, nc3)
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT NoteN1 FROM WEB_FORMATION_EVAL_ADMIN
            WHERE ID_Formation = ? AND MatriculeParticipant = ? AND TypeEval = 'CHAUD'
        """, (fid, part))
        chaud = cursor.fetchone()
        n1moy = float(chaud.NoteN1) if chaud and chaud.NoteN1 is not None else None
        n_finale = _calc_n_finale(n1moy, n2)
        jugement = _jugement_from_n(n_finale)
        m = _int_mat(matricule_connecte)
        cursor.execute("""
            SELECT ID FROM WEB_FORMATION_EVAL_ADMIN
            WHERE ID_Formation = ? AND MatriculeParticipant = ? AND TypeEval = 'FROID'
        """, (fid, part))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE WEB_FORMATION_EVAL_ADMIN SET
                    MatriculeSaisiePar = ?, NoteColdObj1 = ?, NoteColdObj2 = ?, NoteColdObj3 = ?,
                    NoteN2 = ?, NoteFinaleN = ?, Jugement = ?, NouvelleFormationSuggestee = ?,
                    DateModification = GETDATE(), DateSaisie = GETDATE()
                WHERE ID = ?
            """, (
                m, nc1, nc2, nc3, n2, n_finale, jugement,
                (data.get('nouvelle_formation_suggestee') or '').strip() or None,
                existing.ID,
            ))
            eid = existing.ID
        else:
            cursor.execute("""
                INSERT INTO WEB_FORMATION_EVAL_ADMIN (
                    ID_Formation, MatriculeParticipant, TypeEval, MatriculeSaisiePar,
                    NoteColdObj1, NoteColdObj2, NoteColdObj3, NoteN2, NoteFinaleN,
                    Jugement, NouvelleFormationSuggestee, DateSaisie
                )
                OUTPUT INSERTED.ID
                VALUES (?, ?, 'FROID', ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                fid, part, m, nc1, nc2, nc3, n2, n_finale, jugement,
                (data.get('nouvelle_formation_suggestee') or '').strip() or None,
            ))
            row = cursor.fetchone()
            eid = int(row[0]) if row and row[0] is not None else None
            if eid is None:
                return None, "Erreur lors de l'enregistrement de l'évaluation à froid."
        cursor.connection.commit()
    return get_eval_admin(eid), None


def _int_note(v):
    try:
        n = int(v)
        return n if 1 <= n <= 5 else None
    except (TypeError, ValueError):
        return None


def formations_pour_eval_admin(matricule_connecte, is_super=False):
    """Formations éligibles au formulaire d'évaluation (tous bénéficiaires inscrits)."""
    formations = list_formations(matricule_connecte, is_super)
    out = []
    for f in formations:
        beneficiaires = f.get('beneficiaires') or []
        if not beneficiaires:
            continue
        admins = [b for b in beneficiaires if is_staff_administratif(b['matricule'])]
        # Staff admin en priorité ; sinon tous les bénéficiaires de la formation
        participants = admins if admins else beneficiaires
        item = dict(f)
        item['participants_admin'] = participants
        out.append(item)
    return out
