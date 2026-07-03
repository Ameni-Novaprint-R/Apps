# -*- coding: utf-8 -*-
"""
Projet 27 – Crédit Leasing.
Suivi prévisionnel des échéances leasing et crédits bancaires à long terme.
"""
import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal

from db import get_db_cursor

NUM_PROJ = 27
JOURS_PRELEVEMENT = (5, 15, 25)
SEUIL_TOTAL_DEFAUT = Decimal('200000')

# Jours fériés fixes secteur bancaire (complément convention + projet 25)
FERIES_FIXES_BANQUE_EXTRA = [
    (1, 1),    # Jour de l'an
    (4, 9),    # Journée des martyrs
    (8, 13),   # Fête de la femme
    (10, 15),  # Fête de l'évacuation
]


def init_web_credit_tables():
    """Crée les tables et données de référence si absentes."""
    sql_blocks = [
        """IF OBJECT_ID('dbo.WEB_CREDIT_BANQUE', 'U') IS NULL
           CREATE TABLE dbo.WEB_CREDIT_BANQUE (
               ID INT IDENTITY(1,1) PRIMARY KEY, Code NVARCHAR(20) NULL,
               Libelle NVARCHAR(100) NOT NULL, Actif BIT NOT NULL DEFAULT 1,
               OrdreAffichage INT NULL, DateCreation DATETIME NOT NULL DEFAULT GETDATE(),
               DateModification DATETIME NULL)""",
        """IF OBJECT_ID('dbo.WEB_CREDIT_TYPE', 'U') IS NULL
           CREATE TABLE dbo.WEB_CREDIT_TYPE (
               ID INT IDENTITY(1,1) PRIMARY KEY, Code NVARCHAR(20) NOT NULL,
               Libelle NVARCHAR(50) NOT NULL, OrdreAffichage INT NULL,
               CONSTRAINT UQ_WEB_CREDIT_TYPE_Code UNIQUE (Code))""",
        """IF OBJECT_ID('dbo.WEB_CREDIT', 'U') IS NULL
           CREATE TABLE dbo.WEB_CREDIT (
               ID INT IDENTITY(1,1) PRIMARY KEY,
               ID_WEB_CREDIT_BANQUE INT NOT NULL, ID_WEB_CREDIT_TYPE INT NOT NULL,
               Libelle NVARCHAR(200) NOT NULL, ReferenceContrat NVARCHAR(50) NULL,
               JourPrelevement TINYINT NOT NULL, MontantMensuel DECIMAL(18,3) NOT NULL DEFAULT 0,
               DateDebut DATE NULL, DateFin DATE NULL, Actif BIT NOT NULL DEFAULT 1,
               OrdreAffichage INT NULL, Commentaire NVARCHAR(500) NULL,
               DateCreation DATETIME NOT NULL DEFAULT GETDATE(), DateModification DATETIME NULL,
               UtilisateurCreation NVARCHAR(50) NULL, UtilisateurModification NVARCHAR(50) NULL,
               CONSTRAINT FK_WEB_CREDIT_BANQUE FOREIGN KEY (ID_WEB_CREDIT_BANQUE)
                   REFERENCES dbo.WEB_CREDIT_BANQUE(ID),
               CONSTRAINT FK_WEB_CREDIT_TYPE FOREIGN KEY (ID_WEB_CREDIT_TYPE)
                   REFERENCES dbo.WEB_CREDIT_TYPE(ID),
               CONSTRAINT CK_WEB_CREDIT_Jour CHECK (JourPrelevement BETWEEN 1 AND 31),
               CONSTRAINT UQ_WEB_CREDIT_Banque_Ref UNIQUE (ID_WEB_CREDIT_BANQUE, ReferenceContrat))""",
        """IF OBJECT_ID('dbo.WEB_CREDIT_ECHEANCE', 'U') IS NULL
           CREATE TABLE dbo.WEB_CREDIT_ECHEANCE (
               ID INT IDENTITY(1,1) PRIMARY KEY, ID_WEB_CREDIT INT NOT NULL,
               Annee SMALLINT NOT NULL, Mois TINYINT NOT NULL,
               Montant DECIMAL(18,3) NOT NULL DEFAULT 0, DateEcheance DATE NULL,
               DateCreation DATETIME NOT NULL DEFAULT GETDATE(), DateModification DATETIME NULL,
               CONSTRAINT FK_WEB_CREDIT_ECHEANCE_CREDIT FOREIGN KEY (ID_WEB_CREDIT)
                   REFERENCES dbo.WEB_CREDIT(ID) ON DELETE CASCADE,
               CONSTRAINT CK_WEB_CREDIT_ECHEANCE_Mois CHECK (Mois BETWEEN 1 AND 12),
               CONSTRAINT UQ_WEB_CREDIT_ECHEANCE UNIQUE (ID_WEB_CREDIT, Annee, Mois))""",
        """IF OBJECT_ID('dbo.WEB_CREDIT_PARAM', 'U') IS NULL
           CREATE TABLE dbo.WEB_CREDIT_PARAM (
               Cle NVARCHAR(50) NOT NULL PRIMARY KEY, Valeur NVARCHAR(100) NOT NULL,
               Libelle NVARCHAR(200) NULL, DateModification DATETIME NULL)""",
    ]
    seeds = [
        ("IF NOT EXISTS (SELECT 1 FROM WEB_CREDIT_TYPE WHERE Code='LEASING') "
         "INSERT INTO WEB_CREDIT_TYPE (Code,Libelle,OrdreAffichage) VALUES ('LEASING',N'Crédit leasing',1)"),
        ("IF NOT EXISTS (SELECT 1 FROM WEB_CREDIT_TYPE WHERE Code='BANCAIRE') "
         "INSERT INTO WEB_CREDIT_TYPE (Code,Libelle,OrdreAffichage) VALUES ('BANCAIRE',N'Crédit bancaire',2)"),
        ("IF NOT EXISTS (SELECT 1 FROM WEB_CREDIT_BANQUE WHERE Code='BIAT') "
         "INSERT INTO WEB_CREDIT_BANQUE (Code,Libelle,OrdreAffichage) VALUES ('BIAT',N'BIAT',1)"),
        ("IF NOT EXISTS (SELECT 1 FROM WEB_CREDIT_BANQUE WHERE Code='UIB') "
         "INSERT INTO WEB_CREDIT_BANQUE (Code,Libelle,OrdreAffichage) VALUES ('UIB',N'UIB',2)"),
        ("IF NOT EXISTS (SELECT 1 FROM WEB_CREDIT_BANQUE WHERE Code='ZITOUNA') "
         "INSERT INTO WEB_CREDIT_BANQUE (Code,Libelle,OrdreAffichage) VALUES ('ZITOUNA',N'ZITOUNA',3)"),
        ("IF NOT EXISTS (SELECT 1 FROM WEB_CREDIT_BANQUE WHERE Code='WIFAK') "
         "INSERT INTO WEB_CREDIT_BANQUE (Code,Libelle,OrdreAffichage) VALUES ('WIFAK',N'WIFAK',4)"),
        ("IF NOT EXISTS (SELECT 1 FROM WEB_CREDIT_PARAM WHERE Cle='SEUIL_TOTAL_MENSUEL') "
         "INSERT INTO WEB_CREDIT_PARAM (Cle,Valeur,Libelle) "
         "VALUES ('SEUIL_TOTAL_MENSUEL','200000',N'Seuil total mensuel TND')"),
    ]
    with get_db_cursor() as cursor:
        for block in sql_blocks:
            cursor.execute(block)
        for seed in seeds:
            cursor.execute(seed)
        cursor.connection.commit()
    ensure_projet27_in_web_projets()
    ensure_projet27_sections()


def ensure_projet27_in_web_projets():
    try:
        with get_db_cursor() as cursor:
            cursor.execute('SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = ?', (NUM_PROJ,))
            if cursor.fetchone():
                return
            cursor.execute("""
                INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive)
                VALUES (?, N'Projet 27', N'Crédit Leasing', 0)
            """, (NUM_PROJ,))
            cursor.connection.commit()
            print('[Projet 27] WEB_PROJETS ajouté.')
    except Exception as e:
        print(f'[Projet 27] ensure_projet27_in_web_projets: {e}')


def ensure_projet27_sections():
    sections = ['Tableau de bord', 'Gestion des crédits', 'Nouveau crédit']
    try:
        with get_db_cursor() as cursor:
            cursor.execute('SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = ?', (NUM_PROJ,))
            row = cursor.fetchone()
            if not row:
                return
            id_proj = row[0]
            for nom in sections:
                cursor.execute(
                    'SELECT 1 FROM WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?',
                    (id_proj, nom),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        'INSERT INTO WEB_SECTIONS (ID_Proj, Nom, archive) VALUES (?, ?, 0)',
                        (id_proj, nom),
                    )
            cursor.connection.commit()
    except Exception as e:
        print(f'[Projet 27] ensure_projet27_sections: {e}')


def _parse_date(val):
    if not val:
        return None
    if isinstance(val, date):
        return val
    s = str(val).strip()[:10]
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _dec(val):
    if val is None:
        return Decimal('0')
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def _date_echeance(annee, mois, jour):
    jour = min(int(jour), calendar.monthrange(int(annee), int(mois))[1])
    return date(int(annee), int(mois), jour)


def _get_jours_feries_set(date_debut, date_fin):
    """Jours fériés tunisiens : base projet 25 (fixes + variables RH) + fixes banque."""
    try:
        from logic import projet25 as p25
        feries = p25.get_jours_feries_set(date_debut, date_fin)
    except Exception:
        feries = set()
    y1 = date_debut.year if isinstance(date_debut, date) else date.today().year
    y2 = date_fin.year if isinstance(date_fin, date) else y1
    for annee in range(y1, y2 + 1):
        for mois, jour in FERIES_FIXES_BANQUE_EXTRA:
            try:
                feries.add(date(annee, mois, jour))
            except ValueError:
                pass
    return feries


def _est_jour_non_ouvre(d, feries):
    return d.weekday() >= 5 or d in feries


def date_effective_prelevement(annee, mois, jour, feries=None):
    """
    Date à laquelle le prélèvement est considéré comme effectué.
    Report au prochain jour ouvré si week-end ou jour férié.
    """
    d = _date_echeance(annee, mois, jour)
    if feries is None:
        feries = _get_jours_feries_set(d, d + timedelta(days=14))
    while _est_jour_non_ouvre(d, feries):
        d += timedelta(days=1)
    return d


def _load_echeances_par_credits(credit_ids):
    if not credit_ids:
        return {}
    out = {cid: [] for cid in credit_ids}
    placeholders = ','.join('?' * len(credit_ids))
    with get_db_cursor() as cursor:
        cursor.execute(f"""
            SELECT ID_WEB_CREDIT, Annee, Mois, Montant
            FROM WEB_CREDIT_ECHEANCE
            WHERE ID_WEB_CREDIT IN ({placeholders})
            ORDER BY Annee, Mois
        """, credit_ids)
        for r in cursor.fetchall():
            out[r.ID_WEB_CREDIT].append({
                'annee': int(r.Annee),
                'mois': int(r.Mois),
                'montant': float(r.Montant or 0),
            })
    return out


def calcul_situation_credit(credit, echeances, ref_date=None, feries=None):
    """
    Montant restant à payer et date de la prochaine échéance effective.
    Simulation prévisionnelle (pas de relevé bancaire réel).
    """
    ref = ref_date or date.today()
    if isinstance(ref, datetime):
        ref = ref.date()

    date_fin = _parse_date(credit.get('date_fin'))
    if date_fin and ref > date_fin:
        return 0.0, None

    if not echeances:
        return 0.0, None

    jour = int(credit.get('jour_prelevement') or 0)
    annee_min = min(e['annee'] for e in echeances)
    annee_max = max(e['annee'] for e in echeances)
    if feries is None:
        feries = _get_jours_feries_set(
            date(annee_min, 1, 1),
            date(max(annee_max, ref.year) + 1, 12, 31),
        )

    restant = 0.0
    prochaine = None
    for ech in echeances:
        if ech['montant'] <= 0:
            continue
        eff = date_effective_prelevement(ech['annee'], ech['mois'], jour, feries)
        if eff > ref:
            restant += ech['montant']
            if prochaine is None or eff < prochaine:
                prochaine = eff

    return round(restant, 3), prochaine


def _enrich_credits_situation(credits, ref_date=None):
    if not credits:
        return credits
    ref = ref_date or date.today()
    ids = [c['id'] for c in credits]
    echeances_map = _load_echeances_par_credits(ids)

    annee_min = ref.year
    annee_max = ref.year
    for echs in echeances_map.values():
        for e in echs:
            annee_min = min(annee_min, e['annee'])
            annee_max = max(annee_max, e['annee'])
    feries = _get_jours_feries_set(
        date(annee_min, 1, 1),
        date(annee_max + 1, 12, 31),
    )

    for c in credits:
        restant, prochaine = calcul_situation_credit(
            c, echeances_map.get(c['id'], []), ref, feries,
        )
        c['montant_restant'] = restant
        c['prochaine_echeance'] = prochaine.isoformat() if prochaine else None
    return credits


def get_seuil_total():
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT Valeur FROM WEB_CREDIT_PARAM WHERE Cle = 'SEUIL_TOTAL_MENSUEL'"
        )
        row = cursor.fetchone()
        if row and row[0]:
            try:
                return _dec(row[0])
            except Exception:
                pass
    return SEUIL_TOTAL_DEFAUT


def set_seuil_total(valeur):
    v = _dec(valeur)
    with get_db_cursor() as cursor:
        cursor.execute("""
            IF EXISTS (SELECT 1 FROM WEB_CREDIT_PARAM WHERE Cle = 'SEUIL_TOTAL_MENSUEL')
                UPDATE WEB_CREDIT_PARAM SET Valeur = ?, DateModification = GETDATE()
                WHERE Cle = 'SEUIL_TOTAL_MENSUEL'
            ELSE
                INSERT INTO WEB_CREDIT_PARAM (Cle, Valeur, Libelle, DateModification)
                VALUES ('SEUIL_TOTAL_MENSUEL', ?, N'Seuil total mensuel TND', GETDATE())
        """, (str(v), str(v)))
        cursor.connection.commit()
    return float(v)


def list_banques(actif_only=True):
    with get_db_cursor() as cursor:
        q = """
            SELECT ID, Code, Libelle, Actif, OrdreAffichage
            FROM WEB_CREDIT_BANQUE
        """
        if actif_only:
            q += ' WHERE Actif = 1'
        q += ' ORDER BY COALESCE(OrdreAffichage, 999), Libelle'
        cursor.execute(q)
        return [
            {
                'id': r.ID,
                'code': r.Code,
                'libelle': r.Libelle,
                'actif': bool(r.Actif),
                'ordre': r.OrdreAffichage,
            }
            for r in cursor.fetchall()
        ]


def list_types():
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT ID, Code, Libelle, OrdreAffichage
            FROM WEB_CREDIT_TYPE ORDER BY COALESCE(OrdreAffichage, 999)
        """)
        return [
            {'id': r.ID, 'code': r.Code, 'libelle': r.Libelle, 'ordre': r.OrdreAffichage}
            for r in cursor.fetchall()
        ]


def _row_credit(r):
    return {
        'id': r.ID,
        'id_banque': r.ID_WEB_CREDIT_BANQUE,
        'banque': r.BanqueLibelle,
        'banque_code': r.BanqueCode,
        'id_type': r.ID_WEB_CREDIT_TYPE,
        'type_code': r.TypeCode,
        'type_libelle': r.TypeLibelle,
        'libelle': r.Libelle,
        'reference': r.ReferenceContrat,
        'jour_prelevement': r.JourPrelevement,
        'montant_mensuel': float(r.MontantMensuel or 0),
        'date_debut': r.DateDebut.isoformat() if r.DateDebut else None,
        'date_fin': r.DateFin.isoformat() if r.DateFin else None,
        'actif': bool(r.Actif),
        'ordre': r.OrdreAffichage,
        'commentaire': r.Commentaire,
    }


def list_credits(actif_only=False, type_code=None, id_banque=None):
    with get_db_cursor() as cursor:
        q = """
            SELECT c.ID, c.ID_WEB_CREDIT_BANQUE, c.ID_WEB_CREDIT_TYPE,
                   c.Libelle, c.ReferenceContrat, c.JourPrelevement, c.MontantMensuel,
                   c.DateDebut, c.DateFin, c.Actif, c.OrdreAffichage, c.Commentaire,
                   b.Libelle AS BanqueLibelle, b.Code AS BanqueCode,
                   t.Code AS TypeCode, t.Libelle AS TypeLibelle
            FROM WEB_CREDIT c
            INNER JOIN WEB_CREDIT_BANQUE b ON b.ID = c.ID_WEB_CREDIT_BANQUE
            INNER JOIN WEB_CREDIT_TYPE t ON t.ID = c.ID_WEB_CREDIT_TYPE
            WHERE 1=1
        """
        params = []
        if actif_only:
            q += ' AND c.Actif = 1'
        if type_code:
            q += ' AND t.Code = ?'
            params.append(type_code)
        if id_banque:
            q += ' AND c.ID_WEB_CREDIT_BANQUE = ?'
            params.append(id_banque)
        q += """
            ORDER BY t.OrdreAffichage, c.JourPrelevement,
                     COALESCE(c.OrdreAffichage, 999), c.Libelle
        """
        cursor.execute(q, params)
        credits = [_row_credit(r) for r in cursor.fetchall()]
    return _enrich_credits_situation(credits)


def get_credit(credit_id):
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT c.ID, c.ID_WEB_CREDIT_BANQUE, c.ID_WEB_CREDIT_TYPE,
                   c.Libelle, c.ReferenceContrat, c.JourPrelevement, c.MontantMensuel,
                   c.DateDebut, c.DateFin, c.Actif, c.OrdreAffichage, c.Commentaire,
                   b.Libelle AS BanqueLibelle, b.Code AS BanqueCode,
                   t.Code AS TypeCode, t.Libelle AS TypeLibelle
            FROM WEB_CREDIT c
            INNER JOIN WEB_CREDIT_BANQUE b ON b.ID = c.ID_WEB_CREDIT_BANQUE
            INNER JOIN WEB_CREDIT_TYPE t ON t.ID = c.ID_WEB_CREDIT_TYPE
            WHERE c.ID = ?
        """, (credit_id,))
        row = cursor.fetchone()
        if not row:
            return None
        credit = _row_credit(row)
        _enrich_credits_situation([credit])
        return credit


def _validate_credit_data(data, credit_id=None):
    libelle = (data.get('libelle') or '').strip()
    if not libelle:
        return 'Le libellé du crédit est requis.'
    id_banque = data.get('id_banque')
    id_type = data.get('id_type')
    if not id_banque:
        return 'La banque est requise.'
    if not id_type:
        return 'Le type de crédit est requis.'
    jour = data.get('jour_prelevement')
    try:
        jour = int(jour)
    except (TypeError, ValueError):
        return 'Le jour de prélèvement est invalide.'
    if jour not in JOURS_PRELEVEMENT:
        return f'Le jour de prélèvement doit être {", ".join(map(str, JOURS_PRELEVEMENT))}.'
    try:
        montant = float(data.get('montant_mensuel') or 0)
        if montant < 0:
            return 'Le montant mensuel ne peut pas être négatif.'
    except (TypeError, ValueError):
        return 'Le montant mensuel est invalide.'
    ref = (data.get('reference') or '').strip() or None
    if ref:
        with get_db_cursor() as cursor:
            q = """
                SELECT ID FROM WEB_CREDIT
                WHERE ID_WEB_CREDIT_BANQUE = ? AND ReferenceContrat = ?
            """
            params = [id_banque, ref]
            if credit_id:
                q += ' AND ID <> ?'
                params.append(credit_id)
            cursor.execute(q, params)
            if cursor.fetchone():
                return 'Cette référence existe déjà pour cette banque.'
    date_debut = _parse_date(data.get('date_debut'))
    date_fin = _parse_date(data.get('date_fin'))
    if date_debut and date_fin and date_fin < date_debut:
        return 'La date de fin doit être postérieure ou égale à la date de début.'
    return None


def create_credit(data, utilisateur=None):
    err = _validate_credit_data(data)
    if err:
        return None, err
    libelle = data['libelle'].strip()
    ref = (data.get('reference') or '').strip() or None
    montant = float(data.get('montant_mensuel') or 0)
    date_debut = _parse_date(data.get('date_debut'))
    date_fin = _parse_date(data.get('date_fin'))
    actif = 1 if data.get('actif', True) in (True, 1, '1', 'true') else 0
    ordre = data.get('ordre')
    commentaire = (data.get('commentaire') or '').strip() or None
    generer = data.get('generer_echeances', True) in (True, 1, '1', 'true')

    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO WEB_CREDIT (
                ID_WEB_CREDIT_BANQUE, ID_WEB_CREDIT_TYPE, Libelle, ReferenceContrat,
                JourPrelevement, MontantMensuel, DateDebut, DateFin, Actif,
                OrdreAffichage, Commentaire, UtilisateurCreation
            )
            OUTPUT INSERTED.ID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['id_banque'], data['id_type'], libelle, ref,
            int(data['jour_prelevement']), montant, date_debut, date_fin, actif,
            ordre, commentaire, utilisateur,
        ))
        new_id = cursor.fetchone()[0]
        cursor.connection.commit()

    if generer and date_debut and date_fin:
        generer_echeances(new_id, utilisateur=utilisateur)
    return get_credit(new_id), None


def update_credit(credit_id, data, utilisateur=None):
    existing = get_credit(credit_id)
    if not existing:
        return None, 'Crédit introuvable.'
    err = _validate_credit_data(data, credit_id=credit_id)
    if err:
        return None, err

    libelle = data['libelle'].strip()
    ref = (data.get('reference') or '').strip() or None
    montant = float(data.get('montant_mensuel') or 0)
    date_debut = _parse_date(data.get('date_debut'))
    date_fin = _parse_date(data.get('date_fin'))
    actif = 1 if data.get('actif', True) in (True, 1, '1', 'true') else 0
    ordre = data.get('ordre')
    commentaire = (data.get('commentaire') or '').strip() or None
    regen = data.get('regenerer_echeances', False) in (True, 1, '1', 'true')

    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE WEB_CREDIT SET
                ID_WEB_CREDIT_BANQUE = ?, ID_WEB_CREDIT_TYPE = ?, Libelle = ?,
                ReferenceContrat = ?, JourPrelevement = ?, MontantMensuel = ?,
                DateDebut = ?, DateFin = ?, Actif = ?, OrdreAffichage = ?,
                Commentaire = ?, DateModification = GETDATE(),
                UtilisateurModification = ?
            WHERE ID = ?
        """, (
            data['id_banque'], data['id_type'], libelle, ref,
            int(data['jour_prelevement']), montant, date_debut, date_fin, actif,
            ordre, commentaire, utilisateur, credit_id,
        ))
        cursor.connection.commit()

    if regen and date_debut and date_fin:
        generer_echeances(credit_id, utilisateur=utilisateur, remplacer=True)
    return get_credit(credit_id), None


def delete_credit(credit_id):
    """Supprime un crédit et ses échéances (CASCADE)."""
    existing = get_credit(credit_id)
    if not existing:
        return False, 'Crédit introuvable.'
    with get_db_cursor() as cursor:
        cursor.execute('DELETE FROM WEB_CREDIT WHERE ID = ?', (credit_id,))
        if cursor.rowcount == 0:
            return False, 'Crédit introuvable.'
        cursor.connection.commit()
    return True, None


def generer_echeances(credit_id, utilisateur=None, remplacer=False):
    """Génère les échéances mensuelles entre DateDebut et DateFin."""
    credit = get_credit(credit_id)
    if not credit:
        return 0, 'Crédit introuvable.'
    date_debut = _parse_date(credit.get('date_debut'))
    date_fin = _parse_date(credit.get('date_fin'))
    if not date_debut or not date_fin:
        return 0, 'Dates début et fin requises pour générer l''échéancier.'

    jour = int(credit['jour_prelevement'])
    montant = credit['montant_mensuel']
    y, m = date_debut.year, date_debut.month
    y_fin, m_fin = date_fin.year, date_fin.month
    rows = []
    while (y, m) <= (y_fin, m_fin):
        d = _date_echeance(y, m, jour)
        if d >= date_debut and d <= date_fin:
            rows.append((credit_id, y, m, montant, d))
        m += 1
        if m > 12:
            m = 1
            y += 1

    with get_db_cursor() as cursor:
        if remplacer:
            cursor.execute('DELETE FROM WEB_CREDIT_ECHEANCE WHERE ID_WEB_CREDIT = ?', (credit_id,))
        for credit_id, annee, mois, mt, d_echeance in rows:
            cursor.execute("""
                IF EXISTS (
                    SELECT 1 FROM WEB_CREDIT_ECHEANCE
                    WHERE ID_WEB_CREDIT = ? AND Annee = ? AND Mois = ?
                )
                    UPDATE WEB_CREDIT_ECHEANCE
                    SET Montant = ?, DateEcheance = ?, DateModification = GETDATE()
                    WHERE ID_WEB_CREDIT = ? AND Annee = ? AND Mois = ?
                ELSE
                    INSERT INTO WEB_CREDIT_ECHEANCE
                        (ID_WEB_CREDIT, Annee, Mois, Montant, DateEcheance)
                    VALUES (?, ?, ?, ?, ?)
            """, (
                credit_id, annee, mois, mt, d_echeance, credit_id, annee, mois,
                credit_id, annee, mois, mt, d_echeance,
            ))
        cursor.connection.commit()
    return len(rows), None


def get_annees_disponibles():
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT Annee FROM WEB_CREDIT_ECHEANCE
            UNION
            SELECT YEAR(DateDebut) FROM WEB_CREDIT WHERE DateDebut IS NOT NULL
            UNION
            SELECT YEAR(DateFin) FROM WEB_CREDIT WHERE DateFin IS NOT NULL
            ORDER BY 1 DESC
        """)
        years = [r[0] for r in cursor.fetchall() if r[0]]
    annee_courante = date.today().year
    if annee_courante not in years:
        years.append(annee_courante)
        years.sort(reverse=True)
    if not years:
        years = [annee_courante]
    return years


def _build_colonnes_tableau(credits):
    colonnes = []
    for c in credits:
        colonnes.append({
            'id': c['id'],
            'libelle': c['libelle'],
            'reference': c['reference'],
            'banque': c['banque'],
            'banque_code': c['banque_code'],
            'type_code': c['type_code'],
            'type_libelle': c['type_libelle'],
            'jour_prelevement': c['jour_prelevement'],
            'actif': c['actif'],
        })
    return colonnes


def _load_montants_annee(annee):
    montants = {}
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT ID_WEB_CREDIT, Mois, Montant
            FROM WEB_CREDIT_ECHEANCE WHERE Annee = ?
        """, (int(annee),))
        for r in cursor.fetchall():
            montants[(r.ID_WEB_CREDIT, r.Mois)] = float(r.Montant or 0)
    return montants


def _lignes_tableau_annee(annee, credits, montants, seuil, today):
    """Lignes mensuelles + total annuel pour une année."""
    annee = int(annee)
    mois_courant = today.month if today.year == annee else None
    lignes = []
    totaux_annuels_credit = {c['id']: 0.0 for c in credits}
    total_leasing_annuel = 0.0
    total_bancaire_annuel = 0.0
    total_global_annuel = 0.0

    for mois in range(1, 13):
        cellules = {}
        total_leasing = 0.0
        total_bancaire = 0.0
        for c in credits:
            if not c['actif']:
                continue
            val = montants.get((c['id'], mois), 0.0)
            if val:
                cellules[str(c['id'])] = val
                totaux_annuels_credit[c['id']] += val
                if c['type_code'] == 'LEASING':
                    total_leasing += val
                else:
                    total_bancaire += val
        total_global = total_leasing + total_bancaire
        total_leasing_annuel += total_leasing
        total_bancaire_annuel += total_bancaire
        total_global_annuel += total_global

        est_mois_courant = mois_courant == mois
        if total_global >= seuil:
            couleur_total = 'rouge'
        elif total_global > 0:
            couleur_total = 'vert'
        else:
            couleur_total = None

        lignes.append({
            'type_ligne': 'mois',
            'mois': mois,
            'annee': annee,
            'libelle': f'{mois:02d}/{annee}',
            'est_mois_courant': est_mois_courant,
            'cellules': cellules,
            'total_leasing': total_leasing,
            'total_bancaire': total_bancaire,
            'total_global': total_global,
            'couleur_total': couleur_total,
            'couleur_ligne': 'mois-courant' if est_mois_courant else None,
        })

    totaux_credit_cells = {
        str(c['id']): totaux_annuels_credit[c['id']] for c in credits
    }
    lignes.append({
        'type_ligne': 'total_annuel',
        'mois': None,
        'annee': annee,
        'libelle': f'Totaux {annee}',
        'est_mois_courant': False,
        'cellules': totaux_credit_cells,
        'total_leasing': total_leasing_annuel,
        'total_bancaire': total_bancaire_annuel,
        'total_global': total_global_annuel,
        'couleur_total': (
            'rouge' if total_global_annuel >= seuil
            else ('vert' if total_global_annuel > 0 else None)
        ),
        'couleur_ligne': None,
    })
    return lignes


def get_tableau(annee=None):
    """Construit la grille mensuelle type Excel. annee=None → toutes les années."""
    credits = list_credits(actif_only=False)
    seuil = float(get_seuil_total())
    today = date.today()
    colonnes = _build_colonnes_tableau(credits)

    groupes_jour = {}
    for jour in JOURS_PRELEVEMENT:
        groupes_jour[str(jour)] = {
            'jour': jour,
            'leasing': [col for col in colonnes if col['jour_prelevement'] == jour and col['type_code'] == 'LEASING'],
            'bancaire': [col for col in colonnes if col['jour_prelevement'] == jour and col['type_code'] == 'BANCAIRE'],
        }

    if annee is not None:
        annee = int(annee)
        montants = _load_montants_annee(annee)
        lignes = _lignes_tableau_annee(annee, credits, montants, seuil, today)
        mois_courant = today.month if today.year == annee else None
        return {
            'annee': annee,
            'toutes_annees': False,
            'annees': [annee],
            'seuil_total': seuil,
            'colonnes': colonnes,
            'groupes_jour': groupes_jour,
            'lignes': lignes,
            'mois_courant': mois_courant,
        }

    with get_db_cursor() as cursor:
        cursor.execute('SELECT DISTINCT Annee FROM WEB_CREDIT_ECHEANCE ORDER BY Annee')
        annees = [r[0] for r in cursor.fetchall() if r[0]]
    if not annees:
        annees = [today.year]

    lignes = []
    for y in annees:
        montants = _load_montants_annee(y)
        if not any(montants.values()):
            continue
        lignes.extend(_lignes_tableau_annee(y, credits, montants, seuil, today))

    return {
        'annee': None,
        'toutes_annees': True,
        'annees': annees,
        'seuil_total': seuil,
        'colonnes': colonnes,
        'groupes_jour': groupes_jour,
        'lignes': lignes,
        'mois_courant': today.month if today.year in annees else None,
    }


def format_montant_tnd(val):
    """Format 123456,789 (virgule décimale, 3 décimales)."""
    if val is None:
        return ''
    try:
        n = float(val)
    except (TypeError, ValueError):
        return ''
    s = f'{n:,.3f}'.replace(',', ' ').replace('.', ',').replace(' ', '.')
    # Fix: French/Tunisian - thousands with space or dot, decimal comma
    # Simpler approach:
    parts = f'{n:.3f}'.split('.')
    int_part = parts[0]
    # add thousands separator .
    rev = int_part[::-1]
    grouped = '.'.join(rev[i:i + 3] for i in range(0, len(rev), 3))[::-1]
    return f'{grouped},{parts[1]}'
