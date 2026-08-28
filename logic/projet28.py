# -*- coding: utf-8 -*-
"""
Projet 28 – Gestion des codes-barres matières premières.
Payload Code 128 :
  MP{ID_MVT}{SEQ3};{TYPE_MP};{CODE_FAM};{CODE_ART};{P|B}
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
import unicodedata

from db import get_db_cursor

NUM_PROJ = 28
CPTE_VAR_STK_MP = 'MAT. PREM'
TYPE_PIECE_ENTREE = 'C'  # provisoire – à valider avec dépôt (G = retour)

STATUTS = (
    'RECU',
    'EN_STOCK',
    'RESERVE',
    'PARTIEL',
    'SORTIE',
    'CONSOMME',
    'ANNULE',
)

STATUT_LABELS = {
    'RECU': 'Reçu',
    'EN_STOCK': 'En stock',
    'RESERVE': 'Réservé',
    'PARTIEL': 'En cours d\'utilisation',
    'SORTIE': 'Sortie',
    'CONSOMME': 'Consommé',
    'ANNULE': 'Annulé',
}

# Seed mapping payload ↔ GS_TYPES_ARTICLE (MAT. PREM)
TYPES_MP_SEED = [
    # CodePayload, Designation, ID_TYPE_ARTICLE
    ('PD', 'PAPIERS DIVERS', 0),
    ('PE', 'POCHETTE & ENVELOPPE', 14),
    ('CA', 'CARTON', 15),
    ('CO', 'COUCHE', 16),
    ('VE', 'VERGE', 17),
    ('OF', 'OFFSET', 18),
]


def _strip_accents(s):
    if s is None:
        return ''
    nk = unicodedata.normalize('NFKD', str(s))
    return ''.join(ch for ch in nk if not unicodedata.combining(ch))


def sanitize_segment(value, max_len=40):
    """Normalise un segment payload : ASCII, majuscules, sans ';' ni espaces."""
    s = _strip_accents(value).upper().strip()
    s = s.replace(';', '').replace(' ', '')
    s = re.sub(r'[^A-Z0-9._\-+]', '', s)
    return (s or '-')[:max_len]


def infer_mode_from_unite(unite):
    """
    Déduit P (palette/feuilles) ou B (bobine/kg) depuis l'unité ERP du mouvement.
    Retourne 'P', 'B' ou None si indéterminé.
    """
    u = _strip_accents(unite or '').strip().lower()
    if not u:
        return None
    if u in ('kg', 'kgs', 'kilo', 'kilos', 'kilogramme', 'kilogrammes') or u.startswith('kg'):
        return 'B'
    if 'bobine' in u or u in ('bob', 'bobines'):
        return 'B'
    if 'feuille' in u or u in ('fl', 'flles', 'sheet', 'sheets'):
        return 'P'
    if 'palette' in u or u in ('pal', 'pals'):
        return 'P'
    return None


def unite_stockage_from_mode(mode):
    return 'KG' if mode == 'B' else 'FEUILLE'


def resolve_mode(mode_demande, unite_erp):
    """
    Le mode métier suit l'unité du mouvement ERP quand elle est claire (Kg→B, Feuilles→P).
    Sinon on conserve le mode demandé (P/B).
    """
    inferred = infer_mode_from_unite(unite_erp)
    if inferred:
        return inferred, inferred
    mode = (mode_demande or '').upper().strip()
    if mode not in ('P', 'B'):
        return None, None
    return mode, None


def build_code_id(id_mvt, sequence, id_stock=None):
    """
    ID scannable :
    - avec mouvement : MP{ID_MVT}{SEQ3}
    - inventaire sans mvt : MPS{ID_STOCK}{SEQ3}
    """
    seq = int(sequence)
    if seq < 1 or seq > 999:
        raise ValueError('Séquence hors plage 001–999')
    if id_mvt is not None:
        return f'MP{int(id_mvt)}{seq:03d}'
    if id_stock is None:
        raise ValueError('ID_MVT ou ID_STOCK requis pour CodeId')
    return f'MPS{int(id_stock)}{seq:03d}'


def build_payload(id_mvt, sequence, type_code, code_famille, code_article, mode, id_stock=None):
    mode = (mode or '').upper().strip()
    if mode not in ('P', 'B'):
        raise ValueError("Mode invalide (P=palette, B=bobine)")
    code_id = build_code_id(id_mvt, sequence, id_stock=id_stock)
    parts = [
        code_id,
        sanitize_segment(type_code, 10),
        sanitize_segment(code_famille, 30),
        sanitize_segment(code_article, 40),
        mode,
    ]
    return ';'.join(parts)


def parse_payload(payload):
    """Parse un payload scanné. Retourne dict ou None."""
    raw = (payload or '').strip()
    if not raw:
        return None
    parts = raw.split(';')
    if len(parts) != 5:
        return None
    code_id, type_code, code_fam, code_art, mode = parts
    if mode not in ('P', 'B'):
        return None
    id_mvt = None
    id_stock = None
    if code_id.startswith('MPS'):
        body = code_id[3:]
        if len(body) < 4 or not body.isdigit():
            return None
        seq = int(body[-3:])
        id_stock = int(body[:-3])
    elif code_id.startswith('MP'):
        body = code_id[2:]
        if len(body) < 4 or not body.isdigit():
            return None
        seq = int(body[-3:])
        id_mvt = int(body[:-3])
    else:
        return None
    return {
        'payload': raw,
        'code_id': code_id,
        'id_mvt': id_mvt,
        'id_stock': id_stock,
        'sequence': seq,
        'type_code': type_code,
        'code_famille': code_fam,
        'code_article': code_art,
        'mode': mode,
    }


def init_web_cod_bar_tables():
    """Crée les tables applicatives et seed le référentiel types MP."""
    blocks = [
        """
        IF OBJECT_ID('dbo.WEB_COD_BAR_MP_TYPES', 'U') IS NULL
        CREATE TABLE dbo.WEB_COD_BAR_MP_TYPES (
            ID INT IDENTITY(1,1) PRIMARY KEY,
            Code NVARCHAR(10) NOT NULL,
            Designation NVARCHAR(50) NOT NULL,
            ID_TYPE_ARTICLE INT NOT NULL,
            Actif BIT NOT NULL CONSTRAINT DF_WEB_COD_BAR_MP_TYPES_Actif DEFAULT 1,
            OrdreAffichage INT NULL,
            DateCreation DATETIME NOT NULL CONSTRAINT DF_WEB_COD_BAR_MP_TYPES_DC DEFAULT GETDATE(),
            CONSTRAINT UQ_WEB_COD_BAR_MP_TYPES_Code UNIQUE (Code),
            CONSTRAINT UQ_WEB_COD_BAR_MP_TYPES_ID_TYPE UNIQUE (ID_TYPE_ARTICLE),
            CONSTRAINT FK_WEB_COD_BAR_MP_TYPES_GS
                FOREIGN KEY (ID_TYPE_ARTICLE) REFERENCES dbo.GS_TYPES_ARTICLE(ID)
        )
        """,
        """
        IF OBJECT_ID('dbo.WEB_COD_BAR_MP_UNITES', 'U') IS NULL
        CREATE TABLE dbo.WEB_COD_BAR_MP_UNITES (
            ID INT IDENTITY(1,1) PRIMARY KEY,
            ID_MVT INT NULL,
            ID_STOCK INT NULL,
            Origine NVARCHAR(20) NOT NULL CONSTRAINT DF_WEB_COD_BAR_MP_UNITES_Orig DEFAULT N'RECEPTION',
            QteInventaireRef DECIMAL(18,3) NULL,
            Sequence SMALLINT NOT NULL,
            CodeId NVARCHAR(40) NOT NULL,
            Payload NVARCHAR(120) NOT NULL,
            Mode CHAR(1) NOT NULL,
            ID_WEB_TYPE INT NOT NULL,
            CodeType NVARCHAR(10) NOT NULL,
            DesignationType NVARCHAR(50) NULL,
            CodeFamille NVARCHAR(50) NOT NULL,
            CodeArticle NVARCHAR(50) NOT NULL,
            DesignationArticle NVARCHAR(200) NULL,
            NumOrdrePiece INT NULL,
            QteInitiale DECIMAL(18,3) NOT NULL CONSTRAINT DF_WEB_COD_BAR_MP_UNITES_QI DEFAULT 0,
            QteRestante DECIMAL(18,3) NOT NULL CONSTRAINT DF_WEB_COD_BAR_MP_UNITES_QR DEFAULT 0,
            Unite NVARCHAR(20) NOT NULL,
            Dimensions NVARCHAR(100) NULL,
            Statut NVARCHAR(20) NOT NULL CONSTRAINT DF_WEB_COD_BAR_MP_UNITES_ST DEFAULT 'RECU',
            DateReception DATETIME NULL,
            DateCreation DATETIME NOT NULL CONSTRAINT DF_WEB_COD_BAR_MP_UNITES_DC DEFAULT GETDATE(),
            DateModification DATETIME NULL,
            UtilisateurCreation NVARCHAR(50) NULL,
            UtilisateurModification NVARCHAR(50) NULL,
            Commentaire NVARCHAR(500) NULL,
            CONSTRAINT UQ_WEB_COD_BAR_MP_UNITES_Payload UNIQUE (Payload),
            CONSTRAINT UQ_WEB_COD_BAR_MP_UNITES_CodeId UNIQUE (CodeId),
            CONSTRAINT CK_WEB_COD_BAR_MP_UNITES_Mode CHECK (Mode IN ('P','B')),
            CONSTRAINT CK_WEB_COD_BAR_MP_UNITES_Seq CHECK (Sequence BETWEEN 1 AND 999),
            CONSTRAINT CK_WEB_COD_BAR_MP_UNITES_Origine CHECK (Origine IN ('RECEPTION','INVENTAIRE')),
            CONSTRAINT CK_WEB_COD_BAR_MP_UNITES_Statut CHECK (
                Statut IN ('RECU','EN_STOCK','RESERVE','PARTIEL','SORTIE','CONSOMME','ANNULE')
            ),
            CONSTRAINT FK_WEB_COD_BAR_MP_UNITES_TYPE
                FOREIGN KEY (ID_WEB_TYPE) REFERENCES dbo.WEB_COD_BAR_MP_TYPES(ID)
        )
        """,
        """
        IF OBJECT_ID('dbo.WEB_COD_BAR_MP_SCANS', 'U') IS NULL
        CREATE TABLE dbo.WEB_COD_BAR_MP_SCANS (
            ID INT IDENTITY(1,1) PRIMARY KEY,
            ID_UNITE INT NULL,
            PayloadScanne NVARCHAR(120) NOT NULL,
            ActionScan NVARCHAR(40) NOT NULL CONSTRAINT DF_WEB_COD_BAR_MP_SCANS_ACT DEFAULT 'CONSULTATION',
            Utilisateur NVARCHAR(50) NULL,
            Matricule INT NULL,
            Lieu NVARCHAR(100) NULL,
            Detail NVARCHAR(500) NULL,
            DateScan DATETIME NOT NULL CONSTRAINT DF_WEB_COD_BAR_MP_SCANS_DS DEFAULT GETDATE(),
            CONSTRAINT FK_WEB_COD_BAR_MP_SCANS_UNITE
                FOREIGN KEY (ID_UNITE) REFERENCES dbo.WEB_COD_BAR_MP_UNITES(ID)
        )
        """,
    ]
    with get_db_cursor() as cursor:
        for block in blocks:
            cursor.execute(block)
        for ordre, (code, desig, id_type) in enumerate(TYPES_MP_SEED, start=1):
            cursor.execute(
                "SELECT 1 FROM dbo.WEB_COD_BAR_MP_TYPES WHERE Code = ?",
                (code,),
            )
            if not cursor.fetchone():
                cursor.execute(
                    """
                    INSERT INTO dbo.WEB_COD_BAR_MP_TYPES
                        (Code, Designation, ID_TYPE_ARTICLE, Actif, OrdreAffichage)
                    VALUES (?, ?, ?, 1, ?)
                    """,
                    (code, desig, id_type, ordre),
                )
        cursor.connection.commit()
    ensure_statut_partiel_constraint()
    ensure_inventaire_schema()
    ensure_inventaire_campagne_tables()
    ensure_projet28_in_web_projets()
    ensure_projet28_sections()
    try:
        accorder_projet28_matricules([234, 334])
    except Exception as e:
        print(f'[Projet 28] accorder matricules: {e}')


def code_campagne_trimestre(dt=None, annee=None, trimestre=None):
    """Code campagne trimestrielle : YYYY-Tn (ex. 2026-T3)."""
    if annee is not None and trimestre is not None:
        return f'{int(annee)}-T{int(trimestre)}'
    dt = dt or datetime.now()
    t = (dt.month - 1) // 3 + 1
    return f'{dt.year}-T{t}'


def _slug_campagne(txt, max_len=20):
    raw = unicodedata.normalize('NFKD', str(txt or ''))
    raw = ''.join(c for c in raw if not unicodedata.combining(c))
    raw = re.sub(r'[^A-Za-z0-9]+', '-', raw.upper()).strip('-')
    return (raw or 'EXC')[:max_len]


def ensure_inventaire_campagne_tables():
    """Tables campagnes + quantités inventoriées (trimestriel / exceptionnel)."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            IF OBJECT_ID('dbo.WEB_COD_BAR_MP_CAMPAGNES', 'U') IS NULL
            CREATE TABLE dbo.WEB_COD_BAR_MP_CAMPAGNES (
                ID INT IDENTITY(1,1) PRIMARY KEY,
                CodeCampagne NVARCHAR(40) NOT NULL,
                Libelle NVARCHAR(120) NULL,
                TypeCampagne NVARCHAR(20) NOT NULL
                    CONSTRAINT DF_WEB_COD_BAR_MP_CAMP_Type DEFAULT N'TRIMESTRIEL',
                Annee INT NULL,
                Trimestre TINYINT NULL,
                Actif BIT NOT NULL CONSTRAINT DF_WEB_COD_BAR_MP_CAMP_Actif DEFAULT 0,
                DateCreation DATETIME NOT NULL CONSTRAINT DF_WEB_COD_BAR_MP_CAMP_DC DEFAULT GETDATE(),
                DateCloture DATETIME NULL,
                CONSTRAINT UQ_WEB_COD_BAR_MP_CAMPAGNES_Code UNIQUE (CodeCampagne),
                CONSTRAINT CK_WEB_COD_BAR_MP_CAMP_Type
                    CHECK (TypeCampagne IN (N'TRIMESTRIEL', N'EXCEPTIONNEL')),
                CONSTRAINT CK_WEB_COD_BAR_MP_CAMP_Trim
                    CHECK (Trimestre IS NULL OR Trimestre BETWEEN 1 AND 4)
            )
        """)
        # Migration colonnes si table déjà créée sans typage
        cursor.execute("""
            IF COL_LENGTH('dbo.WEB_COD_BAR_MP_CAMPAGNES', 'TypeCampagne') IS NULL
                ALTER TABLE dbo.WEB_COD_BAR_MP_CAMPAGNES ADD TypeCampagne NVARCHAR(20) NOT NULL
                    CONSTRAINT DF_WEB_COD_BAR_MP_CAMP_Type DEFAULT N'TRIMESTRIEL'
        """)
        cursor.execute("""
            IF COL_LENGTH('dbo.WEB_COD_BAR_MP_CAMPAGNES', 'Annee') IS NULL
                ALTER TABLE dbo.WEB_COD_BAR_MP_CAMPAGNES ADD Annee INT NULL
        """)
        cursor.execute("""
            IF COL_LENGTH('dbo.WEB_COD_BAR_MP_CAMPAGNES', 'Trimestre') IS NULL
                ALTER TABLE dbo.WEB_COD_BAR_MP_CAMPAGNES ADD Trimestre TINYINT NULL
        """)
        # Élargir CodeCampagne si besoin (codes exceptionnels)
        cursor.execute("""
            IF EXISTS (
                SELECT 1 FROM sys.columns
                WHERE object_id = OBJECT_ID('dbo.WEB_COD_BAR_MP_CAMPAGNES')
                  AND name = 'CodeCampagne' AND max_length < 80
            )
                ALTER TABLE dbo.WEB_COD_BAR_MP_CAMPAGNES ALTER COLUMN CodeCampagne NVARCHAR(40) NOT NULL
        """)
        cursor.execute("""
            IF OBJECT_ID('dbo.WEB_COD_BAR_MP_INVENTAIRE', 'U') IS NULL
            CREATE TABLE dbo.WEB_COD_BAR_MP_INVENTAIRE (
                ID INT IDENTITY(1,1) PRIMARY KEY,
                CodeCampagne NVARCHAR(40) NOT NULL,
                ID_STOCK INT NOT NULL,
                QteInventoriee DECIMAL(18,3) NOT NULL,
                QteStockSnapshot DECIMAL(18,3) NULL,
                Utilisateur NVARCHAR(50) NULL,
                DateSaisie DATETIME NOT NULL CONSTRAINT DF_WEB_COD_BAR_MP_INV_DS DEFAULT GETDATE(),
                DateModification DATETIME NULL,
                CONSTRAINT UQ_WEB_COD_BAR_MP_INV_CAMP_STK UNIQUE (CodeCampagne, ID_STOCK)
            )
        """)
        cursor.execute("""
            IF EXISTS (
                SELECT 1 FROM sys.columns
                WHERE object_id = OBJECT_ID('dbo.WEB_COD_BAR_MP_INVENTAIRE')
                  AND name = 'CodeCampagne' AND max_length < 80
            )
                ALTER TABLE dbo.WEB_COD_BAR_MP_INVENTAIRE ALTER COLUMN CodeCampagne NVARCHAR(40) NOT NULL
        """)
        # Backfill Annee/Trimestre/Type pour anciennes campagnes YYYY-Tn
        cursor.execute("""
            UPDATE dbo.WEB_COD_BAR_MP_CAMPAGNES
            SET TypeCampagne = ISNULL(NULLIF(TypeCampagne, ''), N'TRIMESTRIEL'),
                Annee = CASE
                    WHEN Annee IS NULL AND CodeCampagne LIKE '[0-9][0-9][0-9][0-9]-T[1-4]'
                    THEN TRY_CAST(LEFT(CodeCampagne, 4) AS INT) ELSE Annee END,
                Trimestre = CASE
                    WHEN Trimestre IS NULL AND CodeCampagne LIKE '[0-9][0-9][0-9][0-9]-T[1-4]'
                    THEN TRY_CAST(RIGHT(CodeCampagne, 1) AS TINYINT) ELSE Trimestre END
            WHERE TypeCampagne IS NULL OR TypeCampagne = ''
               OR (CodeCampagne LIKE '[0-9][0-9][0-9][0-9]-T[1-4]' AND (Annee IS NULL OR Trimestre IS NULL))
        """)
        cursor.connection.commit()
    # Si aucune campagne active : créer le trimestre courant (sans forcer un basculement)
    if not get_campagne_active(create_if_missing=False):
        ensure_campagne_default()


def _serialize_campagne(r):
    if not r:
        return None
    out = dict(r)
    for k in ('DateCreation', 'DateCloture'):
        if out.get(k) and hasattr(out[k], 'isoformat'):
            out[k] = out[k].isoformat(sep=' ', timespec='seconds')
    typ = (out.get('TypeCampagne') or 'TRIMESTRIEL').upper()
    out['TypeCampagne'] = typ
    out['TypeCampagneLabel'] = 'Exceptionnel' if typ == 'EXCEPTIONNEL' else 'Trimestriel'
    out['Actif'] = bool(out.get('Actif'))
    return out


def ensure_campagne_default(dt=None):
    """Crée/active le trimestre courant uniquement s'il n'existe pas encore de campagne active."""
    dt = dt or datetime.now()
    annee, trimestre = dt.year, (dt.month - 1) // 3 + 1
    return creer_ou_activer_campagne(
        type_campagne='TRIMESTRIEL',
        annee=annee,
        trimestre=trimestre,
        activer=True,
    )


def get_campagne_active(create_if_missing=True):
    """Retourne la campagne active (ne bascule plus automatiquement de trimestre)."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT TOP 1 ID, CodeCampagne, Libelle, TypeCampagne, Annee, Trimestre,
                   Actif, DateCreation, DateCloture
            FROM dbo.WEB_COD_BAR_MP_CAMPAGNES
            WHERE Actif = 1
            ORDER BY DateCreation DESC, ID DESC
            """
        )
        r = _serialize_campagne(_row_to_dict(cursor, cursor.fetchone()))
    if r:
        return r
    if create_if_missing:
        return ensure_campagne_default()
    return None


def list_campagnes(limit=50):
    limit = max(1, min(int(limit or 50), 200))
    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT TOP ({limit})
                ID, CodeCampagne, Libelle, TypeCampagne, Annee, Trimestre,
                Actif, DateCreation, DateCloture,
                (SELECT COUNT(*) FROM dbo.WEB_COD_BAR_MP_INVENTAIRE I
                 WHERE I.CodeCampagne = C.CodeCampagne) AS NbSaisies
            FROM dbo.WEB_COD_BAR_MP_CAMPAGNES C
            ORDER BY Actif DESC, DateCreation DESC, ID DESC
            """
        )
        return [_serialize_campagne(_row_to_dict(cursor, row)) for row in cursor.fetchall()]


def activer_campagne(code_campagne):
    """Active une campagne existante (désactive les autres). Retourne (campagne, erreur)."""
    code = (code_campagne or '').strip()
    if not code:
        return None, 'Code campagne manquant.'
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT ID, CodeCampagne, Libelle, TypeCampagne, Annee, Trimestre,
                   Actif, DateCreation, DateCloture
            FROM dbo.WEB_COD_BAR_MP_CAMPAGNES WHERE CodeCampagne = ?
            """,
            (code,),
        )
        row = _row_to_dict(cursor, cursor.fetchone())
        if not row:
            return None, f'Campagne introuvable : {code}'
        cursor.execute(
            'UPDATE dbo.WEB_COD_BAR_MP_CAMPAGNES SET Actif = 0 WHERE Actif = 1 AND CodeCampagne <> ?',
            (code,),
        )
        cursor.execute(
            'UPDATE dbo.WEB_COD_BAR_MP_CAMPAGNES SET Actif = 1, DateCloture = NULL WHERE CodeCampagne = ?',
            (code,),
        )
        cursor.connection.commit()
        cursor.execute(
            """
            SELECT ID, CodeCampagne, Libelle, TypeCampagne, Annee, Trimestre,
                   Actif, DateCreation, DateCloture
            FROM dbo.WEB_COD_BAR_MP_CAMPAGNES WHERE CodeCampagne = ?
            """,
            (code,),
        )
        return _serialize_campagne(_row_to_dict(cursor, cursor.fetchone())), None


def creer_ou_activer_campagne(type_campagne='TRIMESTRIEL', annee=None, trimestre=None,
                              libelle=None, code_campagne=None, activer=True):
    """
    Crée (si besoin) puis optionnellement active une campagne.
    - TRIMESTRIEL : code YYYY-Tn
    - EXCEPTIONNEL : code YYYY-EXC-SLUG (ou code fourni)
    Retourne (campagne, erreur).
    """
    typ = (type_campagne or 'TRIMESTRIEL').strip().upper()
    if typ not in ('TRIMESTRIEL', 'EXCEPTIONNEL'):
        return None, 'Type campagne invalide (TRIMESTRIEL ou EXCEPTIONNEL).'

    now = datetime.now()
    annee = int(annee) if annee not in (None, '') else now.year

    if typ == 'TRIMESTRIEL':
        try:
            trimestre = int(trimestre) if trimestre not in (None, '') else ((now.month - 1) // 3 + 1)
        except (TypeError, ValueError):
            return None, 'Trimestre invalide (1 à 4).'
        if trimestre < 1 or trimestre > 4:
            return None, 'Trimestre invalide (1 à 4).'
        code = code_campagne_trimestre(annee=annee, trimestre=trimestre)
        libelle = (libelle or '').strip() or f'Inventaire trimestriel {annee} T{trimestre}'
    else:
        trimestre = None
        code = (code_campagne or '').strip().upper()
        if not code:
            slug = _slug_campagne(libelle or 'MISE-EN-PLACE', max_len=16)
            code = f'{annee}-EXC-{slug}'
        if len(code) > 40:
            return None, 'Code campagne trop long (max 40).'
        libelle = (libelle or '').strip() or f'Inventaire exceptionnel {annee}'

    with get_db_cursor() as cursor:
        cursor.execute(
            'SELECT ID FROM dbo.WEB_COD_BAR_MP_CAMPAGNES WHERE CodeCampagne = ?',
            (code,),
        )
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(
                """
                INSERT INTO dbo.WEB_COD_BAR_MP_CAMPAGNES
                    (CodeCampagne, Libelle, TypeCampagne, Annee, Trimestre, Actif)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (code, libelle, typ, annee, trimestre),
            )
        else:
            cursor.execute(
                """
                UPDATE dbo.WEB_COD_BAR_MP_CAMPAGNES
                SET Libelle = COALESCE(NULLIF(?, ''), Libelle),
                    TypeCampagne = ?,
                    Annee = ?,
                    Trimestre = ?
                WHERE CodeCampagne = ?
                """,
                (libelle, typ, annee, trimestre, code),
            )
        cursor.connection.commit()

    if activer:
        return activer_campagne(code)
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT ID, CodeCampagne, Libelle, TypeCampagne, Annee, Trimestre,
                   Actif, DateCreation, DateCloture
            FROM dbo.WEB_COD_BAR_MP_CAMPAGNES WHERE CodeCampagne = ?
            """,
            (code,),
        )
        return _serialize_campagne(_row_to_dict(cursor, cursor.fetchone())), None


def enregistrer_qte_inventoriee(id_stock, qte_inventoriee, utilisateur=None, code_campagne=None):
    """
    UPSERT qté inventoriée pour (campagne active, ID_STOCK).
    Retourne (dict, erreur).
    """
    try:
        id_stock = int(id_stock)
    except (TypeError, ValueError):
        return None, 'id_stock invalide'
    qte = _dec(qte_inventoriee)
    if qte <= 0:
        return None, 'Qté inventoriée doit être > 0.'

    camp = get_campagne_active()
    code = (code_campagne or (camp or {}).get('CodeCampagne') or '').strip()
    if not code:
        return None, 'Aucune campagne d’inventaire active.'

    ctx = get_article_contexte_stock(id_stock)
    if not ctx:
        return None, 'Stock MP introuvable.'
    qte_stock_snap = ctx.get('QteStock')

    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT ID FROM dbo.WEB_COD_BAR_MP_INVENTAIRE
            WHERE CodeCampagne = ? AND ID_STOCK = ?
            """,
            (code, id_stock),
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE dbo.WEB_COD_BAR_MP_INVENTAIRE
                SET QteInventoriee = ?,
                    QteStockSnapshot = ?,
                    Utilisateur = ?,
                    DateModification = GETDATE()
                WHERE CodeCampagne = ? AND ID_STOCK = ?
                """,
                (float(qte), qte_stock_snap, utilisateur, code, id_stock),
            )
            action = 'update'
            row_id = existing[0]
        else:
            cursor.execute(
                """
                INSERT INTO dbo.WEB_COD_BAR_MP_INVENTAIRE
                    (CodeCampagne, ID_STOCK, QteInventoriee, QteStockSnapshot, Utilisateur)
                OUTPUT INSERTED.ID
                VALUES (?, ?, ?, ?, ?)
                """,
                (code, id_stock, float(qte), qte_stock_snap, utilisateur),
            )
            row_id = cursor.fetchone()[0]
            action = 'insert'
        cursor.connection.commit()
        cursor.execute(
            """
            SELECT ID, CodeCampagne, ID_STOCK, QteInventoriee, QteStockSnapshot,
                   Utilisateur, DateSaisie, DateModification
            FROM dbo.WEB_COD_BAR_MP_INVENTAIRE WHERE ID = ?
            """,
            (row_id,),
        )
        row = _row_to_dict(cursor, cursor.fetchone())

    for k in ('QteInventoriee', 'QteStockSnapshot'):
        if row.get(k) is not None:
            row[k] = float(row[k])
    for k in ('DateSaisie', 'DateModification'):
        if row.get(k) and hasattr(row[k], 'isoformat'):
            row[k] = row[k].isoformat(sep=' ', timespec='seconds')
    row['action'] = action
    row['campagne'] = camp or {'CodeCampagne': code}
    return row, None


def ensure_inventaire_schema():
    """Colonnes inventaire initial + ID_MVT nullable + index uniques filtrés."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            IF COL_LENGTH('dbo.WEB_COD_BAR_MP_UNITES', 'ID_STOCK') IS NULL
                ALTER TABLE dbo.WEB_COD_BAR_MP_UNITES ADD ID_STOCK INT NULL
        """)
        cursor.execute("""
            IF COL_LENGTH('dbo.WEB_COD_BAR_MP_UNITES', 'Origine') IS NULL
                ALTER TABLE dbo.WEB_COD_BAR_MP_UNITES ADD Origine NVARCHAR(20) NOT NULL
                    CONSTRAINT DF_WEB_COD_BAR_MP_UNITES_Orig DEFAULT N'RECEPTION'
        """)
        cursor.execute("""
            IF COL_LENGTH('dbo.WEB_COD_BAR_MP_UNITES', 'QteInventaireRef') IS NULL
                ALTER TABLE dbo.WEB_COD_BAR_MP_UNITES ADD QteInventaireRef DECIMAL(18,3) NULL
        """)
        cursor.execute("""
            IF EXISTS (
                SELECT 1 FROM sys.check_constraints
                WHERE name = 'CK_WEB_COD_BAR_MP_UNITES_Origine'
                  AND parent_object_id = OBJECT_ID('dbo.WEB_COD_BAR_MP_UNITES')
            )
                ALTER TABLE dbo.WEB_COD_BAR_MP_UNITES DROP CONSTRAINT CK_WEB_COD_BAR_MP_UNITES_Origine
        """)
        cursor.execute("""
            ALTER TABLE dbo.WEB_COD_BAR_MP_UNITES ADD CONSTRAINT CK_WEB_COD_BAR_MP_UNITES_Origine
                CHECK (Origine IN ('RECEPTION','INVENTAIRE'))
        """)
        # Rendre ID_MVT nullable (unités inventaire sans mouvement ERP)
        cursor.execute("""
            IF EXISTS (
                SELECT 1 FROM sys.key_constraints
                WHERE name = 'UQ_WEB_COD_BAR_MP_UNITES_MVT_SEQ'
                  AND parent_object_id = OBJECT_ID('dbo.WEB_COD_BAR_MP_UNITES')
            )
                ALTER TABLE dbo.WEB_COD_BAR_MP_UNITES DROP CONSTRAINT UQ_WEB_COD_BAR_MP_UNITES_MVT_SEQ
        """)
        cursor.execute("""
            IF EXISTS (
                SELECT 1 FROM sys.columns
                WHERE object_id = OBJECT_ID('dbo.WEB_COD_BAR_MP_UNITES')
                  AND name = 'ID_MVT' AND is_nullable = 0
            )
                ALTER TABLE dbo.WEB_COD_BAR_MP_UNITES ALTER COLUMN ID_MVT INT NULL
        """)
        cursor.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM sys.indexes
                WHERE name = 'UQ_WEB_COD_BAR_MP_UNITES_MVT_SEQ_F'
                  AND object_id = OBJECT_ID('dbo.WEB_COD_BAR_MP_UNITES')
            )
                CREATE UNIQUE INDEX UQ_WEB_COD_BAR_MP_UNITES_MVT_SEQ_F
                ON dbo.WEB_COD_BAR_MP_UNITES (ID_MVT, Sequence)
                WHERE ID_MVT IS NOT NULL
        """)
        cursor.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM sys.indexes
                WHERE name = 'UQ_WEB_COD_BAR_MP_UNITES_STK_SEQ_F'
                  AND object_id = OBJECT_ID('dbo.WEB_COD_BAR_MP_UNITES')
            )
                CREATE UNIQUE INDEX UQ_WEB_COD_BAR_MP_UNITES_STK_SEQ_F
                ON dbo.WEB_COD_BAR_MP_UNITES (ID_STOCK, Sequence)
                WHERE ID_MVT IS NULL AND ID_STOCK IS NOT NULL
        """)
        cursor.connection.commit()


def ensure_statut_partiel_constraint():
    """Ajoute le statut PARTIEL (migration V1) et reclasse les conso partielles."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            IF EXISTS (
                SELECT 1 FROM sys.check_constraints
                WHERE name = 'CK_WEB_COD_BAR_MP_UNITES_Statut'
                  AND parent_object_id = OBJECT_ID('dbo.WEB_COD_BAR_MP_UNITES')
            )
            ALTER TABLE dbo.WEB_COD_BAR_MP_UNITES DROP CONSTRAINT CK_WEB_COD_BAR_MP_UNITES_Statut
        """)
        cursor.execute("""
            ALTER TABLE dbo.WEB_COD_BAR_MP_UNITES ADD CONSTRAINT CK_WEB_COD_BAR_MP_UNITES_Statut CHECK (
                Statut IN ('RECU','EN_STOCK','RESERVE','PARTIEL','SORTIE','CONSOMME','ANNULE')
            )
        """)
        # Ancien comportement : SORTIE = conso partielle → PARTIEL si reste > 0
        cursor.execute("""
            UPDATE dbo.WEB_COD_BAR_MP_UNITES
            SET Statut = 'PARTIEL',
                DateModification = GETDATE(),
                UtilisateurModification = ISNULL(UtilisateurModification, N'MIGRATION_PARTIEL')
            WHERE Statut = 'SORTIE' AND QteRestante > 0
        """)
        cursor.execute("""
            UPDATE dbo.WEB_COD_BAR_MP_UNITES
            SET Statut = 'CONSOMME',
                DateModification = GETDATE(),
                UtilisateurModification = ISNULL(UtilisateurModification, N'MIGRATION_PARTIEL')
            WHERE Statut = 'SORTIE' AND QteRestante <= 0
        """)
        cursor.connection.commit()


def ensure_projet28_in_web_projets():
    try:
        with get_db_cursor() as cursor:
            cursor.execute('SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = ?', (NUM_PROJ,))
            if cursor.fetchone():
                cursor.execute(
                    """
                    UPDATE dbo.WEB_PROJETS
                    SET CodeProj = N'Projet 28',
                        Nom = N'Gestion des codes-barres MP',
                        archive = 0
                    WHERE NumProj = ?
                    """,
                    (NUM_PROJ,),
                )
                cursor.connection.commit()
                return
            cursor.execute(
                """
                INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive)
                VALUES (?, N'Projet 28', N'Gestion des codes-barres MP', 0)
                """,
                (NUM_PROJ,),
            )
            cursor.connection.commit()
            print('[Projet 28] WEB_PROJETS ajouté.')
    except Exception as e:
        print(f'[Projet 28] ensure_projet28_in_web_projets: {e}')


def ensure_projet28_sections():
    try:
        with get_db_cursor() as cursor:
            cursor.execute('SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = ?', (NUM_PROJ,))
            row = cursor.fetchone()
            if not row:
                return
            id_proj = row[0]
            for nom in SECTIONS_P28:
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
        print(f'[Projet 28] ensure_projet28_sections: {e}')


SECTIONS_P28 = ['Mise en place', 'Génération', 'Unités', 'Scan', 'Étiquettes']
ACTION_P28 = 'CONSULTATION'
EPS_QTE = Decimal('0.001')


def ensure_projet28_actions():
    """Crée une action CONSULTATION par section (nécessaire pour WEB_DROITS_ACCES)."""
    ensure_projet28_in_web_projets()
    ensure_projet28_sections()
    action_ids = []
    with get_db_cursor() as cursor:
        cursor.execute(
            'SELECT ID, CodeProj FROM dbo.WEB_PROJETS WHERE NumProj = ?',
            (NUM_PROJ,),
        )
        proj = cursor.fetchone()
        if not proj:
            return []
        id_proj, code_proj = proj[0], proj[1] or 'Projet 28'
        for nom in SECTIONS_P28:
            cursor.execute(
                'SELECT ID FROM WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?',
                (id_proj, nom),
            )
            sec = cursor.fetchone()
            if not sec:
                print(f'[Projet 28] Section manquante: {nom}')
                continue
            id_section = sec[0]
            cursor.execute(
                'SELECT ID FROM WEB_ACTIONS WHERE ID_Section = ? AND Action = ?',
                (id_section, ACTION_P28),
            )
            row = cursor.fetchone()
            if row:
                action_ids.append(row[0])
                continue
            cursor.execute(
                """
                INSERT INTO WEB_ACTIONS (ID_Section, Action, archive, CodeProj, Nom_SECTIONS)
                VALUES (?, ?, 0, ?, ?)
                """,
                (id_section, ACTION_P28, code_proj, nom),
            )
            cursor.execute(
                'SELECT ID FROM WEB_ACTIONS WHERE ID_Section = ? AND Action = ?',
                (id_section, ACTION_P28),
            )
            action_ids.append(cursor.fetchone()[0])
        cursor.connection.commit()
    return action_ids


def accorder_projet28_matricules(matricules):
    """
    Accorde l'accès complet (toutes les sections) aux matricules donnés.
    Retourne un résumé {matricule: nb_droits_ajoutes}.
    """
    action_ids = ensure_projet28_actions()
    resume = {}
    with get_db_cursor() as cursor:
        for mat in matricules:
            mat = int(mat)
            cursor.execute(
                'SELECT Matricule, Nom, Prenom FROM personel WHERE Matricule = ?',
                (mat,),
            )
            emp = cursor.fetchone()
            if not emp:
                resume[mat] = {'ok': False, 'error': 'Matricule introuvable', 'ajoutes': 0}
                continue
            ajoutes = 0
            for aid in action_ids:
                cursor.execute(
                    'SELECT 1 FROM WEB_DROITS_ACCES WHERE Matricule = ? AND ID_Action = ?',
                    (mat, aid),
                )
                if cursor.fetchone():
                    continue
                cursor.execute(
                    'INSERT INTO WEB_DROITS_ACCES (Matricule, ID_Action, Autorise) VALUES (?, ?, 1)',
                    (mat, aid),
                )
                ajoutes += 1
            resume[mat] = {
                'ok': True,
                'nom': f'{emp[1] or ""} {emp[2] or ""}'.strip(),
                'ajoutes': ajoutes,
                'actions': len(action_ids),
            }
        cursor.connection.commit()
    return resume


def _dec(val, default='0'):
    if val is None or val == '':
        return Decimal(default)
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val).replace(',', '.'))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _row_to_dict(cursor, row):
    if not row:
        return None
    cols = [d[0] for d in cursor.description]
    return {cols[i]: row[i] for i in range(len(cols))}


def list_types_mp(actif_only=True):
    sql = """
        SELECT T.ID, T.Code, T.Designation, T.ID_TYPE_ARTICLE, T.Actif, T.OrdreAffichage,
               G.Code AS CodeERP, G.Designation AS DesignationERP, G.CpteVarStk
        FROM WEB_COD_BAR_MP_TYPES T
        LEFT JOIN GS_TYPES_ARTICLE G ON G.ID = T.ID_TYPE_ARTICLE
    """
    if actif_only:
        sql += ' WHERE T.Actif = 1'
    sql += ' ORDER BY T.OrdreAffichage, T.Code'
    with get_db_cursor() as cursor:
        cursor.execute(sql)
        return [_row_to_dict(cursor, r) for r in cursor.fetchall()]


def get_type_by_id_article(id_type_article):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT ID, Code, Designation, ID_TYPE_ARTICLE
            FROM WEB_COD_BAR_MP_TYPES
            WHERE ID_TYPE_ARTICLE = ? AND Actif = 1
            """,
            (id_type_article,),
        )
        return _row_to_dict(cursor, cursor.fetchone())


def _serialize_mouvement(r, for_json=True):
    if not r:
        return None
    out = dict(r)
    if out.get('Quantite') is not None:
        out['Quantite'] = float(out['Quantite'])
    if out.get('SumQteGeneree') is not None:
        out['SumQteGeneree'] = float(out['SumQteGeneree'])
    else:
        out['SumQteGeneree'] = 0.0
    # Codes ERP souvent paddés : trim pour affichage / payload
    for k in ('CodeArticle', 'CodeFamille', 'DesignationArticle', 'DesignationFamille',
              'DesignationTypeERP', 'DesignationType', 'Unite'):
        if isinstance(out.get(k), str):
            out[k] = out[k].strip()
    mode_suggere = infer_mode_from_unite(out.get('Unite'))
    out['ModeSuggere'] = mode_suggere
    out['ModeSuggereLabel'] = (
        'Bobine (kg)' if mode_suggere == 'B'
        else 'Palette (feuilles)' if mode_suggere == 'P'
        else None
    )
    if for_json and out.get('DatePiece'):
        out['DatePiece'] = out['DatePiece'].isoformat(sep=' ', timespec='seconds')
    return out


def search_mouvements_entree(q=None, num_ordre=None, limit=50, for_json=True):
    """Mouvements TypePiece=C, articles MAT. PREM, avec type mapping WEB."""
    limit = max(1, min(int(limit or 50), 200))
    clauses = [
        "M.TypePiece = ?",
        "T.CpteVarStk = ?",
        "MAP.ID IS NOT NULL",
    ]
    params = [TYPE_PIECE_ENTREE, CPTE_VAR_STK_MP]
    if num_ordre not in (None, ''):
        clauses.append('M.NumOrdrePiece = ?')
        params.append(int(num_ordre))
    if q:
        clauses.append(
            '(A.Code LIKE ? OR A.Designation LIKE ? OR F.Code LIKE ? OR CAST(M.ID AS VARCHAR(20)) LIKE ? '
            'OR CAST(M.NumOrdrePiece AS VARCHAR(20)) LIKE ?)'
        )
        like = f'%{q.strip()}%'
        params.extend([like, like, like, like, like])
    where = ' AND '.join(clauses)
    sql = f"""
        SELECT TOP ({limit})
            M.ID AS ID_MVT,
            M.NumOrdrePiece,
            M.DatePiece,
            M.Quantite,
            M.Unite,
            M.TypePiece,
            S.ID AS ID_STOCK,
            A.ID AS ID_ARTICLE,
            A.Code AS CodeArticle,
            A.Designation AS DesignationArticle,
            F.Code AS CodeFamille,
            F.Designation AS DesignationFamille,
            T.ID AS ID_TYPE_ARTICLE,
            T.Designation AS DesignationTypeERP,
            MAP.ID AS ID_WEB_TYPE,
            MAP.Code AS CodeType,
            MAP.Designation AS DesignationType,
            (SELECT COUNT(*) FROM WEB_COD_BAR_MP_UNITES U WHERE U.ID_MVT = M.ID AND U.Statut <> 'ANNULE') AS NbUnitesGenerees,
            (SELECT ISNULL(MAX(U.Sequence), 0) FROM WEB_COD_BAR_MP_UNITES U WHERE U.ID_MVT = M.ID) AS MaxSequence,
            (SELECT ISNULL(SUM(U.QteInitiale), 0) FROM WEB_COD_BAR_MP_UNITES U
             WHERE U.ID_MVT = M.ID AND U.Statut <> 'ANNULE') AS SumQteGeneree
        FROM GS_MVT_STOCKS M
        INNER JOIN GS_STOCKS S ON S.ID = M.ID_STOCK
        INNER JOIN GS_ARTICLES A ON A.ID = S.ID_ARTICLE
        INNER JOIN GS_FAMILLES F ON F.ID = A.ID_FAMILLE
        INNER JOIN GS_TYPES_ARTICLE T ON T.ID = F.ID_TYPE_ARTICLE
        LEFT JOIN WEB_COD_BAR_MP_TYPES MAP ON MAP.ID_TYPE_ARTICLE = T.ID AND MAP.Actif = 1
        WHERE {where}
        ORDER BY M.ID DESC
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        return [_serialize_mouvement(_row_to_dict(cursor, r), for_json=for_json)
                for r in cursor.fetchall()]


def get_mouvement_entree(id_mvt, for_json=False):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                M.ID AS ID_MVT, M.NumOrdrePiece, M.DatePiece, M.Quantite, M.Unite, M.TypePiece,
                S.ID AS ID_STOCK, A.ID AS ID_ARTICLE, A.Code AS CodeArticle,
                A.Designation AS DesignationArticle, F.Code AS CodeFamille,
                F.Designation AS DesignationFamille, T.ID AS ID_TYPE_ARTICLE,
                T.Designation AS DesignationTypeERP, MAP.ID AS ID_WEB_TYPE,
                MAP.Code AS CodeType, MAP.Designation AS DesignationType,
                (SELECT COUNT(*) FROM WEB_COD_BAR_MP_UNITES U WHERE U.ID_MVT = M.ID AND U.Statut <> 'ANNULE') AS NbUnitesGenerees,
                (SELECT ISNULL(MAX(U.Sequence), 0) FROM WEB_COD_BAR_MP_UNITES U WHERE U.ID_MVT = M.ID) AS MaxSequence,
                (SELECT ISNULL(SUM(U.QteInitiale), 0) FROM WEB_COD_BAR_MP_UNITES U
                 WHERE U.ID_MVT = M.ID AND U.Statut <> 'ANNULE') AS SumQteGeneree
            FROM GS_MVT_STOCKS M
            INNER JOIN GS_STOCKS S ON S.ID = M.ID_STOCK
            INNER JOIN GS_ARTICLES A ON A.ID = S.ID_ARTICLE
            INNER JOIN GS_FAMILLES F ON F.ID = A.ID_FAMILLE
            INNER JOIN GS_TYPES_ARTICLE T ON T.ID = F.ID_TYPE_ARTICLE
            LEFT JOIN WEB_COD_BAR_MP_TYPES MAP ON MAP.ID_TYPE_ARTICLE = T.ID AND MAP.Actif = 1
            WHERE M.ID = ? AND M.TypePiece = ? AND T.CpteVarStk = ?
            """,
            (id_mvt, TYPE_PIECE_ENTREE, CPTE_VAR_STK_MP),
        )
        return _serialize_mouvement(_row_to_dict(cursor, cursor.fetchone()), for_json=for_json)


def _qte_eq(a, b, epsilon=None):
    epsilon = EPS_QTE if epsilon is None else epsilon
    return abs(_dec(a) - _dec(b)) <= epsilon


def _qte_deja_generee_inventaire_stock(id_stock, cursor=None):
    """Somme déjà générée en inventaire sans ID_MVT pour un stock."""
    sql = """
        SELECT ISNULL(SUM(QteInitiale), 0)
        FROM WEB_COD_BAR_MP_UNITES
        WHERE ID_STOCK = ? AND ID_MVT IS NULL AND Origine = N'INVENTAIRE' AND Statut <> 'ANNULE'
    """
    if cursor is not None:
        cursor.execute(sql, (id_stock,))
        return _dec(cursor.fetchone()[0])
    with get_db_cursor() as c:
        c.execute(sql, (id_stock,))
        return _dec(c.fetchone()[0])


def get_article_contexte_stock(id_stock):
    """Contexte article / type WEB pour un ID_STOCK MP."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                S.ID AS ID_STOCK, S.QteStock,
                A.ID AS ID_ARTICLE, A.Code AS CodeArticle, A.Designation AS DesignationArticle,
                F.Code AS CodeFamille, F.Designation AS DesignationFamille,
                T.ID AS ID_TYPE_ARTICLE, T.Designation AS DesignationTypeERP,
                MAP.ID AS ID_WEB_TYPE, MAP.Code AS CodeType, MAP.Designation AS DesignationType
            FROM GS_STOCKS S
            INNER JOIN GS_ARTICLES A ON A.ID = S.ID_ARTICLE
            INNER JOIN GS_FAMILLES F ON F.ID = A.ID_FAMILLE
            INNER JOIN GS_TYPES_ARTICLE T ON T.ID = F.ID_TYPE_ARTICLE
            LEFT JOIN WEB_COD_BAR_MP_TYPES MAP ON MAP.ID_TYPE_ARTICLE = T.ID AND MAP.Actif = 1
            WHERE S.ID = ? AND T.CpteVarStk = ?
            """,
            (id_stock, CPTE_VAR_STK_MP),
        )
        r = _row_to_dict(cursor, cursor.fetchone())
    if not r:
        return None
    for k in ('CodeArticle', 'CodeFamille', 'DesignationArticle', 'DesignationFamille',
              'DesignationTypeERP', 'DesignationType'):
        if isinstance(r.get(k), str):
            r[k] = r[k].strip()
    if r.get('QteStock') is not None:
        r['QteStock'] = float(r['QteStock'])
    return r


def search_stocks_inventaire(q=None, limit=100, for_json=True):
    """
    Stocks MP avec QteStock > 0 + dernière entrée TypePiece=C.
    Couleurs / affichage ID MVT selon QteStockApres vs Quantite.
    Inclut la qté inventoriée saisie pour la campagne active.
    """
    limit = max(1, min(int(limit or 100), 300))
    camp = get_campagne_active()
    code_camp = (camp or {}).get('CodeCampagne') or code_campagne_trimestre()
    clauses = [
        "T.CpteVarStk = ?",
        "S.QteStock > 0",
        "MAP.ID IS NOT NULL",
    ]
    params = [CPTE_VAR_STK_MP]
    if q:
        like = f'%{q.strip()}%'
        clauses.append(
            '(A.Code LIKE ? OR A.Designation LIKE ? OR F.Code LIKE ? '
            'OR CAST(S.ID AS VARCHAR(20)) LIKE ? OR CAST(LAST_C.ID AS VARCHAR(20)) LIKE ? '
            'OR CAST(LAST_C.NumOrdrePiece AS VARCHAR(20)) LIKE ?)'
        )
        params.extend([like, like, like, like, like, like])
    where = ' AND '.join(clauses)
    sql = f"""
        SELECT TOP ({limit})
            S.ID AS ID_STOCK,
            S.QteStock,
            A.ID AS ID_ARTICLE,
            A.Code AS CodeArticle,
            A.Designation AS DesignationArticle,
            F.Code AS CodeFamille,
            F.Designation AS DesignationFamille,
            T.ID AS ID_TYPE_ARTICLE,
            T.Designation AS DesignationTypeERP,
            MAP.ID AS ID_WEB_TYPE,
            MAP.Code AS CodeType,
            MAP.Designation AS DesignationType,
            LAST_C.ID AS ID_MVT,
            LAST_C.NumOrdrePiece,
            LAST_C.DatePiece,
            LAST_C.Quantite AS QteMvt,
            LAST_C.QteStockApres,
            LAST_C.Unite AS UniteMvt,
            INV.QteInventoriee AS QteInventorieeSaisie,
            INV.DateModification AS DateInvModification,
            INV.DateSaisie AS DateInvSaisie,
            ? AS CodeCampagne,
            (SELECT ISNULL(SUM(U.QteInitiale), 0) FROM WEB_COD_BAR_MP_UNITES U
             WHERE U.ID_STOCK = S.ID AND U.Origine = N'INVENTAIRE' AND U.Statut <> 'ANNULE') AS SumQteInvGeneree,
            (SELECT COUNT(*) FROM WEB_COD_BAR_MP_UNITES U
             WHERE U.ID_STOCK = S.ID AND U.Origine = N'INVENTAIRE' AND U.Statut <> 'ANNULE') AS NbUnitesInv,
            (SELECT ISNULL(SUM(U.QteInitiale), 0) FROM WEB_COD_BAR_MP_UNITES U
             WHERE U.ID_MVT = LAST_C.ID AND U.Statut <> 'ANNULE') AS SumQteMvtGeneree,
            (SELECT ISNULL(MAX(U.Sequence), 0) FROM WEB_COD_BAR_MP_UNITES U
             WHERE U.ID_MVT = LAST_C.ID) AS MaxSequenceMvt,
            (SELECT ISNULL(MAX(U.Sequence), 0) FROM WEB_COD_BAR_MP_UNITES U
             WHERE U.ID_STOCK = S.ID AND U.ID_MVT IS NULL AND U.Origine = N'INVENTAIRE') AS MaxSequenceInv
        FROM GS_STOCKS S
        INNER JOIN GS_ARTICLES A ON A.ID = S.ID_ARTICLE
        INNER JOIN GS_FAMILLES F ON F.ID = A.ID_FAMILLE
        INNER JOIN GS_TYPES_ARTICLE T ON T.ID = F.ID_TYPE_ARTICLE
        LEFT JOIN WEB_COD_BAR_MP_TYPES MAP ON MAP.ID_TYPE_ARTICLE = T.ID AND MAP.Actif = 1
        LEFT JOIN WEB_COD_BAR_MP_INVENTAIRE INV
            ON INV.ID_STOCK = S.ID AND INV.CodeCampagne = ?
        OUTER APPLY (
            SELECT TOP 1 M.ID, M.NumOrdrePiece, M.DatePiece, M.Quantite, M.QteStockApres, M.Unite
            FROM GS_MVT_STOCKS M
            WHERE M.ID_STOCK = S.ID AND M.TypePiece = ?
            ORDER BY M.DatePiece DESC, M.ID DESC
        ) LAST_C
        WHERE {where}
        ORDER BY A.Code, S.ID
    """
    # Order of ? : CodeCampagne select, INV join, TypePiece OUTER APPLY, then WHERE params
    params_sql = [code_camp, code_camp, TYPE_PIECE_ENTREE] + params
    with get_db_cursor() as cursor:
        cursor.execute(sql, params_sql)
        rows = [_row_to_dict(cursor, r) for r in cursor.fetchall()]
    stocks = [_serialize_stock_inventaire(r, for_json=for_json) for r in rows]
    return {
        'campagne': camp,
        'stocks': stocks,
    }


def _serialize_stock_inventaire(r, for_json=True):
    if not r:
        return None
    out = dict(r)
    for k in ('QteStock', 'QteMvt', 'QteStockApres', 'SumQteInvGeneree', 'SumQteMvtGeneree',
              'QteInventorieeSaisie'):
        if out.get(k) is not None:
            out[k] = float(out[k])
    for k in ('CodeArticle', 'CodeFamille', 'DesignationArticle', 'DesignationFamille',
              'DesignationTypeERP', 'DesignationType', 'UniteMvt'):
        if isinstance(out.get(k), str):
            out[k] = out[k].strip()

    qte_stock = _dec(out.get('QteStock'))
    qte_mvt = out.get('QteMvt')
    qte_apres = out.get('QteStockApres')
    has_entree = out.get('ID_MVT') is not None

    out['HasEntreeC'] = has_entree
    # Affichage : qté déjà saisie pour la campagne, sinon défaut = QteStock
    if out.get('QteInventorieeSaisie') is not None:
        out['QteInventorieeDefaut'] = float(out['QteInventorieeSaisie'])
        out['InventaireSaisi'] = True
    else:
        out['QteInventorieeDefaut'] = float(qte_stock)
        out['InventaireSaisi'] = False

    # Affichage ID MVT / N° entrée
    show_ref = False
    row_class = ''
    info = None
    if not has_entree:
        row_class = 'orange'
        info = "Aucune entrée TypePiece = 'C' trouvée"
        out['ID_MVT_Affiche'] = '-'
        out['NumOrdrePieceAffiche'] = '-'
        out['SansIdMvt'] = True
        out['AvecIdMvt'] = False
    else:
        q_mvt = _dec(qte_mvt)
        q_ap = _dec(qte_apres)
        stock_diff_apres = not _qte_eq(qte_stock, q_ap)
        if q_ap < q_mvt - EPS_QTE:
            row_class = 'rouge'
            info = (
                f'Situation anormale : QteStockApres ({float(q_ap)}) < Quantite mvt ({float(q_mvt)}).'
            )
            show_ref = True
        elif q_ap > q_mvt + EPS_QTE:
            # Accepté : pas de rouge. Référence entrée non utilisable → « - »
            out['ID_MVT_Affiche'] = '-'
            out['NumOrdrePieceAffiche'] = '-'
            out['SansIdMvt'] = True
            out['AvecIdMvt'] = False
            info = (
                f'QteStockApres ({float(q_ap)}) > Quantite mvt ({float(q_mvt)}) : '
                f'reference entree non utilisable directement.'
            )
        else:
            # QteStockApres ≈ Quantite → référence utilisable (pas de rouge)
            show_ref = True
            if stock_diff_apres:
                info = (
                    f'QteStock ({float(qte_stock)}) different de QteStockApres ({float(q_ap)}).'
                )

        if show_ref:
            out['ID_MVT_Affiche'] = out['ID_MVT']
            out['NumOrdrePieceAffiche'] = (
                out['NumOrdrePiece'] if out.get('NumOrdrePiece') is not None else '-'
            )
            out['SansIdMvt'] = False
            out['AvecIdMvt'] = True

    out['RowClass'] = row_class
    out['InfoAlerte'] = info
    # Bleu (UI) : Qté stock ≠ qté inventoriée saisie
    out['PeutComparerStockInventaire'] = out.get('QteStock') is not None
    if out.get('AvecIdMvt'):
        out['SumQteDejaControl'] = float(out.get('SumQteMvtGeneree') or 0)
        out['MaxSequence'] = int(out.get('MaxSequenceMvt') or 0)
    else:
        out['SumQteDejaControl'] = float(out.get('SumQteInvGeneree') or 0)
        out['MaxSequence'] = int(out.get('MaxSequenceInv') or 0)

    unite = out.get('UniteMvt')
    mode_suggere = infer_mode_from_unite(unite)
    out['ModeSuggere'] = mode_suggere
    out['ModeSuggereLabel'] = (
        'Bobine (kg)' if mode_suggere == 'B'
        else 'Palette (feuilles)' if mode_suggere == 'P'
        else None
    )
    out['Unite'] = unite
    if for_json and out.get('DatePiece'):
        out['DatePiece'] = out['DatePiece'].isoformat(sep=' ', timespec='seconds')
    return out


def _quantites_coherentes_inventaire(qte_cible, qte_deja, qte_nouvelles, epsilon=None):
    epsilon = EPS_QTE if epsilon is None else epsilon
    qte_cible = _dec(qte_cible)
    qte_deja = _dec(qte_deja)
    qte_nouvelles = _dec(qte_nouvelles)
    total = qte_deja + qte_nouvelles
    if abs(total - qte_cible) <= epsilon:
        return True, None
    return False, (
        f'Quantités incohérentes par rapport à la qté inventoriée.\n'
        f'• Qté inventoriée : {float(qte_cible)}\n'
        f'• Déjà généré : {float(qte_deja)}\n'
        f'• Saisie actuelle : {float(qte_nouvelles)}\n'
        f'• Total (déjà + saisie) : {float(total)}\n'
        f'Le total doit être égal à la qté inventoriée.'
    )


def generer_unites_inventaire(id_stock, qte_inventoriee, lignes=None, mode=None,
                              id_mvt=None, utilisateur=None, mettre_en_stock=True):
    """
    Génération initiale depuis un stock MP.
    - Avec id_mvt : lie les unités au mouvement ERP, contrôle sur qté inventoriée.
    - Sans id_mvt : CodeId MPS{ID_STOCK}{SEQ}, ID_MVT NULL.
    """
    ctx = get_article_contexte_stock(id_stock)
    if not ctx:
        return None, 'Stock MP introuvable.'
    if not ctx.get('ID_WEB_TYPE') or not ctx.get('CodeType'):
        return None, 'Type article non mappé dans WEB_COD_BAR_MP_TYPES.'

    qte_inv = _dec(qte_inventoriee)
    if qte_inv <= 0:
        return None, 'Qté inventoriée doit être > 0.'

    mvt = None
    num_ordre = None
    unite_erp = None
    if id_mvt is not None:
        mvt = get_mouvement_entree(id_mvt)
        if not mvt:
            return None, "Mouvement d'entrée MP introuvable."
        if int(mvt.get('ID_STOCK') or 0) != int(id_stock):
            return None, 'Le mouvement ne correspond pas à ce stock.'
        num_ordre = mvt.get('NumOrdrePiece')
        unite_erp = mvt.get('Unite')
    else:
        # Sans mvt : tenter l'unité de la dernière entrée C si présente
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 Unite FROM GS_MVT_STOCKS
                WHERE ID_STOCK = ? AND TypePiece = ?
                ORDER BY DatePiece DESC, ID DESC
                """,
                (id_stock, TYPE_PIECE_ENTREE),
            )
            row = cursor.fetchone()
            if row and row[0]:
                unite_erp = str(row[0]).strip()

    mode, _ = resolve_mode(mode, unite_erp)
    if not mode:
        return None, 'Mode invalide (P ou B) et unité ERP non reconnue.'

    if not isinstance(lignes, (list, tuple)) or not lignes:
        return None, 'Liste des unités (quantités) vide ou invalide.'
    specs = []
    for idx, raw in enumerate(lignes, start=1):
        if not isinstance(raw, dict):
            return None, f'Ligne {idx} invalide.'
        qte = _dec(raw.get('qte'))
        if qte <= 0:
            return None, f'Quantité invalide à la ligne {idx} (doit être > 0).'
        dim = (raw.get('dimensions') or '').strip() or None
        specs.append({'qte': qte, 'dimensions': dim})

    nb = len(specs)
    if nb < 1 or nb > 999:
        return None, 'Nombre d’unités doit être entre 1 et 999.'

    qte_nouvelles = sum((s['qte'] for s in specs), Decimal('0'))
    if id_mvt is not None:
        qte_deja = _qte_deja_generee_mvt(id_mvt)
    else:
        qte_deja = _qte_deja_generee_inventaire_stock(id_stock)
    ok_qte, err_qte = _quantites_coherentes_inventaire(qte_inv, qte_deja, qte_nouvelles)
    if not ok_qte:
        return None, err_qte

    unite = unite_stockage_from_mode(mode)
    statut = 'EN_STOCK' if mettre_en_stock else 'RECU'
    id_mvt_val = int(id_mvt) if id_mvt is not None else None
    id_stock_val = int(id_stock)

    with get_db_cursor() as cursor:
        if id_mvt_val is not None:
            cursor.execute(
                'SELECT ISNULL(MAX(Sequence), 0) FROM WEB_COD_BAR_MP_UNITES WHERE ID_MVT = ?',
                (id_mvt_val,),
            )
        else:
            cursor.execute(
                """
                SELECT ISNULL(MAX(Sequence), 0) FROM WEB_COD_BAR_MP_UNITES
                WHERE ID_STOCK = ? AND ID_MVT IS NULL AND Origine = N'INVENTAIRE'
                """,
                (id_stock_val,),
            )
        max_seq = int(cursor.fetchone()[0] or 0)
        if max_seq + nb > 999:
            return None, f'Séquence dépasserait 999 (actuel max={max_seq}).'

        created = []
        for i, spec in enumerate(specs, start=1):
            seq = max_seq + i
            qte = spec['qte']
            dim = spec['dimensions']
            try:
                payload = build_payload(
                    id_mvt_val, seq, ctx['CodeType'], ctx['CodeFamille'],
                    ctx['CodeArticle'], mode, id_stock=id_stock_val if id_mvt_val is None else None,
                )
                code_id = build_code_id(
                    id_mvt_val, seq,
                    id_stock=id_stock_val if id_mvt_val is None else None,
                )
            except ValueError as e:
                cursor.connection.rollback()
                return None, str(e)
            cursor.execute(
                """
                INSERT INTO WEB_COD_BAR_MP_UNITES (
                    ID_MVT, ID_STOCK, Origine, QteInventaireRef, Sequence, CodeId, Payload, Mode,
                    ID_WEB_TYPE, CodeType, DesignationType, CodeFamille, CodeArticle,
                    DesignationArticle, NumOrdrePiece, QteInitiale, QteRestante, Unite, Dimensions,
                    Statut, DateReception, UtilisateurCreation, Commentaire
                )
                OUTPUT INSERTED.ID
                VALUES (?, ?, N'INVENTAIRE', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    id_mvt_val, id_stock_val, float(qte_inv), seq, code_id, payload, mode,
                    int(ctx['ID_WEB_TYPE']), ctx['CodeType'],
                    ctx.get('DesignationType') or ctx.get('DesignationTypeERP'),
                    (ctx.get('CodeFamille') or '').strip()[:50],
                    (ctx.get('CodeArticle') or '').strip()[:50],
                    ctx.get('DesignationArticle'),
                    num_ordre,
                    float(qte), float(qte), unite, dim, statut,
                    datetime.now(), utilisateur,
                    f'Inventaire initial stock={id_stock_val}',
                ),
            )
            new_id = cursor.fetchone()[0]
            created.append(new_id)
        cursor.connection.commit()

    unites = get_unites_by_ids(created)
    for u in unites:
        enregistrer_scan(
            u['Payload'],
            utilisateur=utilisateur,
            action='INVENTAIRE_INITIAL',
            detail=f'stock={id_stock_val}; qte_inv={float(qte_inv)}; id_mvt={id_mvt_val}',
        )
    return unites, None


def _qte_deja_generee_mvt(id_mvt, cursor=None):
    """Somme des QteInitiale déjà générées pour ce mouvement."""
    sql = """
        SELECT ISNULL(SUM(QteInitiale), 0)
        FROM WEB_COD_BAR_MP_UNITES
        WHERE ID_MVT = ? AND Statut <> 'ANNULE'
    """
    if cursor is not None:
        cursor.execute(sql, (id_mvt,))
        return _dec(cursor.fetchone()[0])
    with get_db_cursor() as c:
        c.execute(sql, (id_mvt,))
        return _dec(c.fetchone()[0])


def _quantites_coherentes(qte_mvt, qte_deja, qte_nouvelles, epsilon=Decimal('0.001')):
    """
    Vérifie que qte_deja + qte_nouvelles == qte_mvt (tolérance float).
    Retourne (ok, message_erreur).
    """
    qte_mvt = _dec(qte_mvt)
    qte_deja = _dec(qte_deja)
    qte_nouvelles = _dec(qte_nouvelles)
    total = qte_deja + qte_nouvelles
    if abs(total - qte_mvt) <= epsilon:
        return True, None
    unite_txt = ''
    return False, (
        f'Quantités incohérentes par rapport au mouvement de stock.\n'
        f'• Qté mvt : {float(qte_mvt)}\n'
        f'• Déjà généré : {float(qte_deja)}\n'
        f'• Saisie actuelle : {float(qte_nouvelles)}\n'
        f'• Total (déjà + saisie) : {float(total)}\n'
        f'Veuillez vérifier les quantités avant de générer les codes-barres '
        f'(le total doit être égal à la Qté mvt).'
    )


def generer_unites(id_mvt, nb_unites=None, mode=None, qte_par_unite=None, dimensions=None,
                   lignes=None, statut='RECU', utilisateur=None, mettre_en_stock=True):
    """
    Génère des codes-barres pour un mouvement d'entrée.
    Preferer `lignes` : liste de dicts {qte, dimensions?} — une qté par unité.
    Retourne (liste_unites, erreur).
    """
    mvt = get_mouvement_entree(id_mvt)
    if not mvt:
        return None, "Mouvement d'entrée MP introuvable (TypePiece=C, MAT. PREM)."
    if not mvt.get('ID_WEB_TYPE') or not mvt.get('CodeType'):
        return None, "Type article non mappé dans WEB_COD_BAR_MP_TYPES."

    mode, _mode_from_unite = resolve_mode(mode, mvt.get('Unite'))
    if not mode:
        return None, 'Mode invalide (P ou B) et unité ERP non reconnue.'

    # Normaliser les lignes (qté spécifique par unité)
    specs = []
    if lignes is not None:
        if not isinstance(lignes, (list, tuple)) or not lignes:
            return None, 'Liste des unités (quantités) vide ou invalide.'
        for idx, raw in enumerate(lignes, start=1):
            if not isinstance(raw, dict):
                return None, f'Ligne {idx} invalide.'
            qte = _dec(raw.get('qte'))
            if qte <= 0:
                return None, f'Quantité invalide à la ligne {idx} (doit être > 0).'
            dim = (raw.get('dimensions') or '').strip() or None
            specs.append({'qte': qte, 'dimensions': dim})
    else:
        # Compat ancienne API : même qté pour toutes
        try:
            nb = int(nb_unites)
        except (TypeError, ValueError):
            return None, 'Nombre d’unités invalide.'
        if nb < 1 or nb > 999:
            return None, 'Nombre d’unités doit être entre 1 et 999.'
        qte = _dec(qte_par_unite)
        if qte <= 0:
            return None, 'Quantité par unité doit être > 0.'
        dim = (dimensions or '').strip() or None if isinstance(dimensions, str) else dimensions
        specs = [{'qte': qte, 'dimensions': dim} for _ in range(nb)]

    nb = len(specs)
    if nb < 1 or nb > 999:
        return None, 'Nombre d’unités doit être entre 1 et 999.'

    qte_nouvelles = sum((s['qte'] for s in specs), Decimal('0'))
    qte_mvt = mvt.get('Quantite')
    if qte_mvt is None:
        return None, 'Qté mvt introuvable sur le mouvement.'
    qte_deja = _qte_deja_generee_mvt(id_mvt)
    ok_qte, err_qte = _quantites_coherentes(qte_mvt, qte_deja, qte_nouvelles)
    if not ok_qte:
        return None, err_qte

    unite = unite_stockage_from_mode(mode)
    statut = statut if statut in STATUTS else 'RECU'
    if mettre_en_stock and statut == 'RECU':
        statut = 'EN_STOCK'

    with get_db_cursor() as cursor:
        cursor.execute(
            'SELECT ISNULL(MAX(Sequence), 0) FROM WEB_COD_BAR_MP_UNITES WHERE ID_MVT = ?',
            (id_mvt,),
        )
        max_seq = int(cursor.fetchone()[0] or 0)
        if max_seq + nb > 999:
            return None, f'Séquence dépasserait 999 (actuel max={max_seq}).'

        created = []
        for i, spec in enumerate(specs, start=1):
            seq = max_seq + i
            qte = spec['qte']
            dim = spec['dimensions']
            try:
                payload = build_payload(
                    id_mvt, seq, mvt['CodeType'], mvt['CodeFamille'],
                    mvt['CodeArticle'], mode,
                )
                code_id = build_code_id(id_mvt, seq)
            except ValueError as e:
                cursor.connection.rollback()
                return None, str(e)
            cursor.execute(
                """
                INSERT INTO WEB_COD_BAR_MP_UNITES (
                    ID_MVT, ID_STOCK, Origine, Sequence, CodeId, Payload, Mode, ID_WEB_TYPE, CodeType,
                    DesignationType, CodeFamille, CodeArticle, DesignationArticle,
                    NumOrdrePiece, QteInitiale, QteRestante, Unite, Dimensions,
                    Statut, DateReception, UtilisateurCreation
                )
                OUTPUT INSERTED.ID
                VALUES (?, ?, N'RECEPTION', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(id_mvt),
                    mvt.get('ID_STOCK'),
                    seq, code_id, payload, mode,
                    int(mvt['ID_WEB_TYPE']), mvt['CodeType'],
                    mvt.get('DesignationType') or mvt.get('DesignationTypeERP'),
                    (mvt.get('CodeFamille') or '').strip()[:50],
                    (mvt.get('CodeArticle') or '').strip()[:50],
                    mvt.get('DesignationArticle'),
                    mvt.get('NumOrdrePiece'),
                    float(qte), float(qte), unite,
                    dim,
                    statut,
                    mvt.get('DatePiece') or datetime.now(),
                    utilisateur,
                ),
            )
            new_id = cursor.fetchone()[0]
            created.append(new_id)
        cursor.connection.commit()

    return get_unites_by_ids(created), None


def get_unites_by_ids(ids):
    if not ids:
        return []
    placeholders = ','.join('?' for _ in ids)
    sql = f"""
        SELECT U.*, T.Designation AS TypeLibelle
        FROM WEB_COD_BAR_MP_UNITES U
        LEFT JOIN WEB_COD_BAR_MP_TYPES T ON T.ID = U.ID_WEB_TYPE
        WHERE U.ID IN ({placeholders})
        ORDER BY U.ID_MVT, U.Sequence
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, list(ids))
        rows = [_row_to_dict(cursor, r) for r in cursor.fetchall()]
    return [_serialize_unite(r) for r in rows]


def _serialize_unite(r):
    if not r:
        return None
    out = dict(r)
    for k in ('QteInitiale', 'QteRestante'):
        if out.get(k) is not None:
            out[k] = float(out[k])
    for k in ('DateReception', 'DateCreation', 'DateModification'):
        if out.get(k):
            out[k] = out[k].isoformat(sep=' ', timespec='seconds')
    out['StatutLabel'] = STATUT_LABELS.get(out.get('Statut'), out.get('Statut'))
    out['ModeLabel'] = 'Palette' if out.get('Mode') == 'P' else 'Bobine' if out.get('Mode') == 'B' else out.get('Mode')
    out['NumOrdrePieceAffiche'] = (
        out['NumOrdrePiece'] if out.get('NumOrdrePiece') is not None else '-'
    )
    origine = (out.get('Origine') or 'RECEPTION').upper()
    out['Origine'] = origine
    out['OrigineLabel'] = 'Inventaire' if origine == 'INVENTAIRE' else 'Réception'
    if out.get('QteInventaireRef') is not None:
        out['QteInventaireRef'] = float(out['QteInventaireRef'])
    if out.get('ID_MVT') is None:
        out['ID_MVT_Affiche'] = '-'
    else:
        out['ID_MVT_Affiche'] = out['ID_MVT']
    return out


def list_unites(id_mvt=None, statut=None, q=None, limit=100):
    limit = max(1, min(int(limit or 100), 500))
    clauses = ['1=1']
    params = []
    if id_mvt:
        clauses.append('U.ID_MVT = ?')
        params.append(int(id_mvt))
    if statut:
        clauses.append('U.Statut = ?')
        params.append(statut)
    if q:
        like = f'%{q.strip()}%'
        clauses.append(
            '(U.Payload LIKE ? OR U.CodeId LIKE ? OR U.CodeArticle LIKE ? OR U.CodeFamille LIKE ? '
            'OR CAST(U.NumOrdrePiece AS VARCHAR(20)) LIKE ?)'
        )
        params.extend([like, like, like, like, like])
    where = ' AND '.join(clauses)
    sql = f"""
        SELECT TOP ({limit}) U.*, T.Designation AS TypeLibelle
        FROM WEB_COD_BAR_MP_UNITES U
        LEFT JOIN WEB_COD_BAR_MP_TYPES T ON T.ID = U.ID_WEB_TYPE
        WHERE {where}
        ORDER BY U.ID DESC
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        return [_serialize_unite(_row_to_dict(cursor, r)) for r in cursor.fetchall()]


def get_unite(unite_id=None, payload=None, code_id=None):
    clauses = []
    params = []
    if unite_id:
        clauses.append('U.ID = ?')
        params.append(int(unite_id))
    elif payload:
        clauses.append('U.Payload = ?')
        params.append(payload.strip())
    elif code_id:
        clauses.append('U.CodeId = ?')
        params.append(code_id.strip())
    else:
        return None
    sql = f"""
        SELECT U.*, T.Designation AS TypeLibelle
        FROM WEB_COD_BAR_MP_UNITES U
        LEFT JOIN WEB_COD_BAR_MP_TYPES T ON T.ID = U.ID_WEB_TYPE
        WHERE {' AND '.join(clauses)}
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        return _serialize_unite(_row_to_dict(cursor, cursor.fetchone()))


def enregistrer_scan(payload, utilisateur=None, matricule=None, lieu=None,
                     action='CONSULTATION', detail=None):
    parsed = parse_payload(payload)
    unite = get_unite(payload=payload.strip()) if payload else None
    if not unite and parsed:
        unite = get_unite(code_id=parsed['code_id'])
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO WEB_COD_BAR_MP_SCANS
                (ID_UNITE, PayloadScanne, ActionScan, Utilisateur, Matricule, Lieu, Detail)
            OUTPUT INSERTED.ID
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                unite['ID'] if unite else None,
                (payload or '').strip()[:120],
                (action or 'CONSULTATION')[:40],
                utilisateur,
                matricule,
                lieu,
                detail,
            ),
        )
        scan_id = cursor.fetchone()[0]
        cursor.connection.commit()
    return {
        'scan_id': scan_id,
        'unite': unite,
        'parsed': parsed,
        'ok': unite is not None,
    }


def _statut_selon_reste(reste, initiale):
    reste = _dec(reste)
    initiale = _dec(initiale)
    if reste <= 0:
        return 'CONSOMME'
    if reste >= initiale:
        return 'EN_STOCK'
    return 'PARTIEL'


def _parse_qte_detail(detail):
    """Extrait qte=… depuis Detail d'un scan CONSOMMATION / RETOUR."""
    if not detail:
        return None
    m = re.search(r'qte\s*=\s*([0-9]+(?:[.,][0-9]+)?)', str(detail), re.I)
    if not m:
        return None
    return _dec(m.group(1).replace(',', '.'))


def _parse_scan_conso_id(detail):
    if not detail:
        return None
    m = re.search(r'scan_conso_id\s*=\s*(\d+)', str(detail), re.I)
    return int(m.group(1)) if m else None


ACTION_LABELS = {
    'CONSULTATION': 'Consultation',
    'CONSOMMATION': 'Sortie',
    'ANNULATION_SORTIE': 'Annulation de sortie',
    'RETOUR_STOCK': 'Retour en stock',
    'INVENTAIRE_INITIAL': 'Inventaire initial',
}


def list_mouvements_unite(unite_id, include_consultations=False):
    """
    Historique des écritures de l'unité (sorties, annulations, retours).
    Les lignes CONSOMMATION déjà annulées restent visibles (annulee=True, pas de bouton).
    """
    with get_db_cursor() as cursor:
        annules = set()
        cursor.execute(
            """
            SELECT Detail FROM WEB_COD_BAR_MP_SCANS
            WHERE ID_UNITE = ? AND ActionScan = 'ANNULATION_SORTIE'
            """,
            (unite_id,),
        )
        for (detail,) in cursor.fetchall():
            sid = _parse_scan_conso_id(detail)
            if sid:
                annules.add(sid)

        cursor.execute(
            """
            SELECT ID, ActionScan, Detail, Utilisateur, Matricule, Lieu, DateScan
            FROM WEB_COD_BAR_MP_SCANS
            WHERE ID_UNITE = ?
            ORDER BY DateScan DESC, ID DESC
            """,
            (unite_id,),
        )
        rows = cursor.fetchall()

    mouvements = []
    for row in rows:
        scan_id, action, detail, user, matricule, lieu, date_scan = row
        action = (action or '').strip()
        if action == 'CONSULTATION' and not include_consultations:
            continue
        qte = _parse_qte_detail(detail)
        qte_signee = None
        if qte is not None:
            if action == 'CONSOMMATION':
                qte_signee = -float(qte)
            elif action in ('ANNULATION_SORTIE', 'RETOUR_STOCK'):
                qte_signee = float(qte)
        annulee = action == 'CONSOMMATION' and int(scan_id) in annules
        annulable = action == 'CONSOMMATION' and not annulee and qte is not None and qte > 0
        mouvements.append({
            'scan_id': int(scan_id),
            'action': action,
            'action_label': ACTION_LABELS.get(action, action),
            'qte': float(qte) if qte is not None else None,
            'qte_signee': qte_signee,
            'detail': detail,
            'utilisateur': user,
            'matricule': matricule,
            'lieu': lieu,
            'date_scan': date_scan.isoformat(sep=' ', timespec='seconds') if date_scan else None,
            'annulee': annulee,
            'annulable': annulable,
            'scan_conso_id_lie': _parse_scan_conso_id(detail) if action == 'ANNULATION_SORTIE' else None,
        })
    return mouvements


def get_derniere_consommation_annulable(unite_id):
    """Dernière CONSOMMATION non encore annulée (compat)."""
    for m in list_mouvements_unite(unite_id):
        if m.get('annulable'):
            return {
                'scan_id': m['scan_id'],
                'qte': m['qte'],
                'detail': m['detail'],
                'date_scan': m['date_scan'],
                'utilisateur': m['utilisateur'],
                'lieu': m['lieu'],
            }
    return None


def consommer_unite(unite_id, qte, utilisateur=None, lieu=None):
    """Consommation partielle ou totale. Retourne (unite, erreur)."""
    qte = _dec(qte)
    if qte <= 0:
        return None, 'Quantité invalide.'
    with get_db_cursor() as cursor:
        cursor.execute(
            'SELECT ID, QteRestante, QteInitiale, Statut, Payload FROM WEB_COD_BAR_MP_UNITES WHERE ID = ?',
            (unite_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None, 'Unité introuvable.'
        restante = _dec(row[1])
        initiale = _dec(row[2])
        statut = row[3]
        payload = row[4]
        if statut == 'ANNULE':
            return None, 'Unité annulée : consommation impossible.'
        if statut == 'CONSOMME' or restante <= 0:
            return None, 'Unité déjà consommée (reste = 0).'
        if qte > restante:
            return None, f'Quantité > reste ({float(restante)}).'
        new_reste = restante - qte
        new_statut = _statut_selon_reste(new_reste, initiale)
        cursor.execute(
            """
            UPDATE WEB_COD_BAR_MP_UNITES
            SET QteRestante = ?, Statut = ?, DateModification = GETDATE(),
                UtilisateurModification = ?
            WHERE ID = ?
            """,
            (float(new_reste), new_statut, utilisateur, unite_id),
        )
        cursor.connection.commit()
    unite = get_unite(unite_id=unite_id)
    enregistrer_scan(
        payload or unite['Payload'],
        utilisateur=utilisateur,
        lieu=lieu,
        action='CONSOMMATION',
        detail=f'qte={float(qte)}; reste={float(new_reste)}',
    )
    return unite, None


def annuler_sortie(unite_id, scan_conso_id, utilisateur=None, lieu=None):
    """
    Crée une écriture d'annulation pour une sortie précise (scan CONSOMMATION).
    Ne modifie / ne supprime pas la ligne de sortie d'origine.
    Retourne (unite, info, erreur).
    """
    try:
        scan_conso_id = int(scan_conso_id)
    except (TypeError, ValueError):
        return None, None, 'Identifiant de sortie invalide.'

    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT ID, ActionScan, Detail, DateScan
            FROM WEB_COD_BAR_MP_SCANS
            WHERE ID = ? AND ID_UNITE = ?
            """,
            (scan_conso_id, unite_id),
        )
        scan_row = cursor.fetchone()
        if not scan_row:
            return None, None, 'Sortie introuvable pour cette unité.'
        if (scan_row[1] or '').strip() != 'CONSOMMATION':
            return None, None, 'Seule une ligne de sortie peut être annulée.'
        qte = _parse_qte_detail(scan_row[2])
        if qte is None or qte <= 0:
            return None, None, 'Quantité de sortie illisible.'

        cursor.execute(
            """
            SELECT Detail FROM WEB_COD_BAR_MP_SCANS
            WHERE ID_UNITE = ? AND ActionScan = 'ANNULATION_SORTIE'
            """,
            (unite_id,),
        )
        for (detail,) in cursor.fetchall():
            if _parse_scan_conso_id(detail) == scan_conso_id:
                return None, None, 'Cette sortie a déjà une écriture d’annulation.'

        cursor.execute(
            'SELECT ID, QteRestante, QteInitiale, Statut, Payload FROM WEB_COD_BAR_MP_UNITES WHERE ID = ?',
            (unite_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None, None, 'Unité introuvable.'
        restante = _dec(row[1])
        initiale = _dec(row[2])
        statut = row[3]
        payload = row[4]
        if statut == 'ANNULE':
            return None, None, 'Unité annulée : opération impossible.'
        new_reste = restante + qte
        if new_reste > initiale:
            new_reste = initiale
        new_statut = _statut_selon_reste(new_reste, initiale)
        cursor.execute(
            """
            UPDATE WEB_COD_BAR_MP_UNITES
            SET QteRestante = ?, Statut = ?, DateModification = GETDATE(),
                UtilisateurModification = ?
            WHERE ID = ?
            """,
            (float(new_reste), new_statut, utilisateur, unite_id),
        )
        cursor.connection.commit()
        date_conso = scan_row[3]

    unite = get_unite(unite_id=unite_id)
    enregistrer_scan(
        payload or unite['Payload'],
        utilisateur=utilisateur,
        lieu=lieu,
        action='ANNULATION_SORTIE',
        detail=(
            f'scan_conso_id={scan_conso_id};qte={float(qte)};'
            f'reste={float(new_reste)}'
        ),
    )
    info = {
        'qte_annulee': float(qte),
        'scan_conso_id': scan_conso_id,
        'date_conso': date_conso.isoformat(sep=' ', timespec='seconds') if date_conso else None,
    }
    return unite, info, None


def annuler_derniere_sortie(unite_id, utilisateur=None, lieu=None):
    """Compat : annule la dernière sortie annulable via écriture d'annulation."""
    derniere = get_derniere_consommation_annulable(unite_id)
    if not derniere:
        return None, None, 'Aucune sortie annulable pour cette unité.'
    return annuler_sortie(
        unite_id, derniere['scan_id'], utilisateur=utilisateur, lieu=lieu,
    )


def retour_en_stock(unite_id, qte, utilisateur=None, lieu=None):
    """
    Réintègre une quantité (retour), plafonnée à QteInitiale.
    Retourne (unite, info, erreur).
    """
    qte = _dec(qte)
    if qte <= 0:
        return None, None, 'Quantité invalide.'
    with get_db_cursor() as cursor:
        cursor.execute(
            'SELECT ID, QteRestante, QteInitiale, Statut, Payload FROM WEB_COD_BAR_MP_UNITES WHERE ID = ?',
            (unite_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None, None, 'Unité introuvable.'
        restante = _dec(row[1])
        initiale = _dec(row[2])
        statut = row[3]
        payload = row[4]
        if statut == 'ANNULE':
            return None, None, 'Unité annulée : retour impossible.'
        max_retour = initiale - restante
        if max_retour <= 0:
            return None, None, 'Stock déjà au maximum (qté initiale).'
        if qte > max_retour:
            return None, None, (
                f'Retour trop élevé : max autorisé {float(max_retour)} '
                f'(reste {float(restante)} / initiale {float(initiale)}).'
            )
        new_reste = restante + qte
        new_statut = _statut_selon_reste(new_reste, initiale)
        cursor.execute(
            """
            UPDATE WEB_COD_BAR_MP_UNITES
            SET QteRestante = ?, Statut = ?, DateModification = GETDATE(),
                UtilisateurModification = ?
            WHERE ID = ?
            """,
            (float(new_reste), new_statut, utilisateur, unite_id),
        )
        cursor.connection.commit()
    unite = get_unite(unite_id=unite_id)
    enregistrer_scan(
        payload or unite['Payload'],
        utilisateur=utilisateur,
        lieu=lieu,
        action='RETOUR_STOCK',
        detail=f'qte={float(qte)}; reste={float(new_reste)}',
    )
    info = {
        'qte_retournee': float(qte),
        'max_retour': float(max_retour),
        'reste': float(new_reste),
    }
    return unite, info, None


def apercu_payload(id_mvt, sequence, mode):
    """Calcule un payload sans l’enregistrer (prévisualisation)."""
    mvt = get_mouvement_entree(id_mvt)
    if not mvt:
        return None, "Mouvement introuvable."
    if not mvt.get('CodeType'):
        return None, "Type non mappé."
    mode_ok, _ = resolve_mode(mode, mvt.get('Unite'))
    if not mode_ok:
        return None, 'Mode invalide (P ou B) et unité ERP non reconnue.'
    try:
        payload = build_payload(
            id_mvt, sequence, mvt['CodeType'], mvt['CodeFamille'],
            mvt['CodeArticle'], mode_ok,
        )
    except ValueError as e:
        return None, str(e)
    return {
        'payload': payload,
        'code_id': build_code_id(id_mvt, sequence),
        'mode': mode_ok,
        'mode_depuis_unite': infer_mode_from_unite(mvt.get('Unite')),
        'unite_erp': mvt.get('Unite'),
        'mouvement': mvt,
        'segments': parse_payload(payload),
    }, None


def corriger_mode_selon_unite_mvt(id_mvt):
    """
    Recalcule Mode / Unite / Payload des unités d'un mouvement
    selon l'unité ERP (ex. Kg → B). Retourne (nb_corriges, erreur).
    """
    mvt = get_mouvement_entree(id_mvt)
    if not mvt:
        return 0, "Mouvement introuvable."
    mode_cible = infer_mode_from_unite(mvt.get('Unite'))
    if not mode_cible:
        return 0, f"Unité ERP non reconnue ({mvt.get('Unite')})."
    unite = unite_stockage_from_mode(mode_cible)
    with get_db_cursor() as cursor:
        cursor.execute(
            'SELECT ID, Sequence, Mode, CodeType, CodeFamille, CodeArticle FROM WEB_COD_BAR_MP_UNITES WHERE ID_MVT = ?',
            (id_mvt,),
        )
        rows = cursor.fetchall()
        n = 0
        for row in rows:
            uid, seq, mode_actu, code_type, code_fam, code_art = row
            if (mode_actu or '').upper() == mode_cible:
                continue
            payload = build_payload(id_mvt, seq, code_type, code_fam, code_art, mode_cible)
            cursor.execute(
                """
                UPDATE WEB_COD_BAR_MP_UNITES
                SET Mode = ?, Unite = ?, Payload = ?, DateModification = GETDATE(),
                    UtilisateurModification = N'CORRECTION_MODE'
                WHERE ID = ?
                """,
                (mode_cible, unite, payload, uid),
            )
            n += 1
        cursor.connection.commit()
    return n, None
