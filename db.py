import pyodbc
from datetime import datetime
from contextlib import contextmanager

# ---------------------------
# CONFIGURATION SQL SERVER
# ---------------------------
# IMPORTANT: Toutes les opérations pointent vers le serveur réseau 192.168.10.225
# Aucune donnée ne doit être stockée sur la base locale du PC
# 
# NOTE CRITIQUE: Pour utiliser l'IP 192.168.10.225, il peut être nécessaire de:
# 1. Utiliser l'authentification SQL Server (UID/PWD) au lieu de Trusted_Connection
# 2. Ou configurer le serveur pour accepter les connexions depuis cette IP
#
# Si l'authentification Windows ne fonctionne pas avec l'IP, décommenter et remplir:
# "UID": "username_sql",
# "PWD": "password_sql",
# Et commenter "Trusted_Connection": "yes"
DB_CONFIG = {
    "SERVER": "192.168.10.225",  # Serveur reseau - Nom du serveur (requis pour Trusted_Connection) - TOUTES les operations CRUD pointent ici
    "DATABASE": "novaprint_restored",
    "Trusted_Connection": False,  # Utiliser True pour la logique robuste
    # Alternative si Trusted_Connection ne fonctionne pas:
    "username": "sa",
    "password": "bA8ALvct9QtX",

}

def get_db_connection():
    """
    Retourne une connexion à la base de données avec logique robuste.
    Essaie plusieurs drivers ODBC dans l'ordre : Driver 18, puis 17, puis SQL Server.
    """
    if DB_CONFIG.get("Trusted_Connection"):
        errors: list[tuple[str, Exception]] = []

        # IMPORTANT:
        # - Certaines configs SQL/SSL/SSPI échouent quand on se connecte via l'IP (certificat/SPN)
        # - On tente donc aussi via localhost / 127.0.0.1 (si l'app tourne sur le même serveur que SQL)
        servers_to_try = []
        for s in [DB_CONFIG.get("SERVER")]:
            if s and s not in servers_to_try:
                servers_to_try.append(s)

        for server in servers_to_try:
            # Essayer Driver 18 (recommandé) avec Encrypt=no + TrustServerCertificate
            try:
                conn_str = (
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                    f"SERVER={server};"
                    f"DATABASE={DB_CONFIG['DATABASE']};"
                    f"Trusted_Connection=yes;"
                    f"Encrypt=no;"
                    f"TrustServerCertificate=yes"
                )
                return pyodbc.connect(conn_str, timeout=5)
            except Exception as e:
                errors.append((f"SERVER={server} | ODBC Driver 18 (Encrypt=no, TrustServerCertificate=yes)", e))

            # Essayer Driver 17 avec Encrypt=no (pour éviter les problèmes SSL)
            try:
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={server};"
                    f"DATABASE={DB_CONFIG['DATABASE']};"
                    f"Trusted_Connection=yes;"
                    f"Encrypt=no"
                )
                return pyodbc.connect(conn_str, timeout=5)
            except Exception as e:
                errors.append((f"SERVER={server} | ODBC Driver 17 (Encrypt=no)", e))

            # Essayer Driver 17 avec TrustServerCertificate
            try:
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={server};"
                    f"DATABASE={DB_CONFIG['DATABASE']};"
                    f"Trusted_Connection=yes;"
                    f"TrustServerCertificate=yes"
                )
                return pyodbc.connect(conn_str, timeout=5)
            except Exception as e:
                errors.append((f"SERVER={server} | ODBC Driver 17 (TrustServerCertificate=yes)", e))

        details = " | ".join([f"{name}: {err}" for name, err in errors]) or "Aucun détail"
        raise Exception(f"Impossible de se connecter avec aucun driver ODBC. Détails: {details}")
    else:
        # Authentification SQL Server (si Trusted_Connection ne fonctionne pas)
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_CONFIG['SERVER']};"
            f"DATABASE={DB_CONFIG['DATABASE']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']}"
        )
        conn = pyodbc.connect(conn_str)
    return conn

def init_projet6_tables():
    """
    Initialise les tables du Projet 6 sur le serveur reseau
    IMPORTANT: Toutes les tables sont creees sur le serveur reseau 192.168.10.225
    Aucune table ne doit etre creee localement
    """
    with get_db_cursor() as cursor:
        # Verifier que la table n'existe pas avant de la creer (syntaxe SQL Server)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'VOYAGES')
            BEGIN
                CREATE TABLE VOYAGES (
                    ID INT IDENTITY(1,1) PRIMARY KEY,
                    DateVoyage DATE NOT NULL,
                    Destination NVARCHAR(255),
                    Camion NVARCHAR(255),
                    Chauffeur NVARCHAR(255)
                )
            END
        """)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'VOYAGE_LIGNES')
            BEGIN
                CREATE TABLE VOYAGE_LIGNES (
                    ID INT IDENTITY(1,1) PRIMARY KEY,
                    ID_VOYAGE INT,
                    Client NVARCHAR(255),
                    NumDossier NVARCHAR(255),
                    Quantite INT,
                    NbCarton INT,
                    NbPalette INT,
                    Termine BIT,
                    FOREIGN KEY (ID_VOYAGE) REFERENCES VOYAGES(ID)
                )
            END
        """)
        cursor.connection.commit()


@contextmanager
def get_db_cursor():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()
        conn.close()

# ---------------------------
# PROJET 1 – PLANNING & SUIVI DES DÉLAIS
# ---------------------------
def get_commandes():
    commandes = []
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT C.Numero, C.DteLivPrev, C.Reference, S.RaiSocTri AS Client
            FROM COMMANDES C
            LEFT JOIN SOCIETES S ON C.ID_SOCIETE = S.ID
            WHERE C.Termine = 0 AND C.EtatLiv = 0
        """)
        for row in cursor.fetchall():
            if row.DteLivPrev:  # Vérifier que la date n'est pas nulle
                commandes.append({
                    "id": row.Numero,
                    "title": row.Numero,
                    "start": row.DteLivPrev.strftime('%Y-%m-%d'),
                    "reference": row.Reference,
                    "client": row.Client
                })
    return commandes

def update_commande(numero, new_date, user=None):
    try:
        new_date_obj = datetime.strptime(new_date, '%Y-%m-%d')
        with get_db_cursor() as cursor:
            cursor.execute("SELECT DteLivPrev FROM COMMANDES WHERE Numero = ?", numero)
            row = cursor.fetchone()
            if not row:
                return False
            old_date = row.DteLivPrev
            cursor.execute("""
                UPDATE COMMANDES 
                SET DteLivPrev = ? 
                WHERE Numero = ?
            """, new_date_obj, numero)
            if user:
                cursor.execute("""
                    INSERT INTO HISTORIQUE_LIVRAISON 
                    (NumeroCommande, AncienneDate, NouvelleDate, ModifiePar)
                    VALUES (?, ?, ?, ?)
                """, numero, old_date, new_date_obj, user)
            cursor.connection.commit()
            return True
    except Exception as e:
        print(f"[Erreur MAJ planning] {e}")
        return False

def get_historique_commande(numero):
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT AncienneDate, NouvelleDate, ModifiePar, DateModification
            FROM HISTORIQUE_LIVRAISON
            WHERE NumeroCommande = ?
            ORDER BY DateModification DESC
        """, numero)
        rows = cursor.fetchall()
        return [
            {
                "ancienne": row.AncienneDate.strftime('%Y-%m-%d'),
                "nouvelle": row.NouvelleDate.strftime('%Y-%m-%d'),
                "user": row.ModifiePar,
                "modifie_le": row.DateModification.strftime('%Y-%m-%d %H:%M')
            }
            for row in rows
        ]

# ---------------------------
# SUIVI DES DÉLAIS ET PONCTUALITÉ
# ---------------------------
def get_commandes_avec_suivi():
    """Récupère les commandes avec informations de suivi des délais"""
    commandes = []
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                C.Numero, 
                C.DteLivPrev, 
                L.DteLiv AS DteLivReelle,
                C.Reference, 
                S.RaiSocTri AS Client,
                C.Termine,
                C.EtatLiv,
                CASE 
                    WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' THEN
                        CASE 
                            WHEN L.DteLiv > C.DteLivPrev THEN 'Livré en Retard'
                            WHEN L.DteLiv <= C.DteLivPrev THEN 'Livré à Temps'
                            ELSE 'Non Défini'
                        END
                    WHEN C.DteLivPrev < GETDATE() THEN 'En Retard'
                    ELSE 'En Cours'
                END AS StatutDelai,
                CASE 
                    WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' THEN
                        DATEDIFF(day, C.DteLivPrev, L.DteLiv)
                    WHEN C.DteLivPrev < GETDATE() THEN
                        DATEDIFF(day, C.DteLivPrev, GETDATE())
                    ELSE 0
                END AS EcartJours
            FROM COMMANDES C
            INNER JOIN SOCIETES S ON C.ID_SOCIETE = S.ID
            LEFT JOIN LIVRAISONS_CMDE L ON C.ID = L.ID_COMMANDE 
            WHERE C.DteLivPrev IS NOT NULL 
            AND C.DteLivPrev <> '9999-12-31 00:00:00.000' 
            AND C.DteLivPrev > '1900-01-01'
            ORDER BY C.DteLivPrev DESC
        """)
        for row in cursor.fetchall():
            commandes.append({
                "numero": row.Numero,
                "date_prevue": row.DteLivPrev.strftime('%Y-%m-%d') if row.DteLivPrev else None,
                "date_reelle": row.DteLivReelle.strftime('%Y-%m-%d') if row.DteLivReelle else None,
                "reference": row.Reference,
                "client": row.Client,
                "termine": bool(row.Termine),
                "etat_liv": row.EtatLiv,
                "statut_delai": row.StatutDelai,
                "ecart_jours": row.EcartJours
            })
    return commandes

def get_statistiques_performance():
    """Calcule les statistiques de performance de livraison"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_commandes,
                SUM(CASE 
                    WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' THEN 1 
                    ELSE 0 
                END) as commandes_livrees,
                SUM(CASE 
                    WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' AND L.DteLiv <= C.DteLivPrev THEN 1 
                    ELSE 0 
                END) as livrees_a_temps,
                SUM(CASE 
                    WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' AND L.DteLiv > C.DteLivPrev THEN 1 
                    ELSE 0 
                END) as livrees_en_retard,
                SUM(CASE 
                    WHEN (L.DteLiv IS NULL OR L.DteLiv = '9999-12-31 00:00:00.000' OR L.DteLiv <= '1900-01-01' OR L.DteLiv >= '2100-01-01') AND C.DteLivPrev < GETDATE() THEN 1 
                    ELSE 0 
                END) as en_retard,
                AVG(CASE 
                    WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' THEN DATEDIFF(day, C.DteLivPrev, L.DteLiv) 
                    ELSE NULL 
                END) as delai_moyen,
                AVG(CASE 
                    WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' AND L.DteLiv <= C.DteLivPrev THEN DATEDIFF(day, C.DteLivPrev, L.DteLiv) 
                    ELSE NULL 
                END) as delai_moyen_a_temps,
                AVG(CASE 
                    WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' AND L.DteLiv > C.DteLivPrev THEN DATEDIFF(day, C.DteLivPrev, L.DteLiv) 
                    ELSE NULL 
                END) as retard_moyen
            FROM COMMANDES C
            LEFT JOIN LIVRAISONS_CMDE L ON C.ID = L.ID_COMMANDE 
            WHERE C.DteLivPrev IS NOT NULL 
            AND C.DteLivPrev <> '9999-12-31 00:00:00.000' 
            AND C.DteLivPrev > '1900-01-01'
        """)
        row = cursor.fetchone()
        if row:
            total = row.total_commandes or 0
            livrees = row.commandes_livrees or 0
            a_temps = row.livrees_a_temps or 0
            en_retard = row.livrees_en_retard or 0
            en_retard_actuel = row.en_retard or 0
            
            taux_ponctualite = (a_temps / livrees * 100) if livrees > 0 else 0
            taux_livraison = (livrees / total * 100) if total > 0 else 0
            
            return {
                "total_commandes": total,
                "commandes_livrees": livrees,
                "livrees_a_temps": a_temps,
                "livrees_en_retard": en_retard,
                "en_retard_actuel": en_retard_actuel,
                "taux_ponctualite": round(taux_ponctualite, 2),
                "taux_livraison": round(taux_livraison, 2),
                "delai_moyen": round(row.delai_moyen or 0, 2),
                "delai_moyen_a_temps": round(row.delai_moyen_a_temps or 0, 2),
                "retard_moyen": round(row.retard_moyen or 0, 2)
            }
    return {}

def get_performance_par_client():
    """Calcule la performance par client"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                S.RaiSocTri AS Client,
                COUNT(*) as total_commandes,
                SUM(CASE 
                    WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' THEN 1 
                    ELSE 0 
                END) as commandes_livrees,
                SUM(CASE 
                    WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' AND L.DteLiv <= C.DteLivPrev THEN 1 
                    ELSE 0 
                END) as livrees_a_temps,
                AVG(CASE 
                    WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' THEN DATEDIFF(day, C.DteLivPrev, L.DteLiv) 
                    ELSE NULL 
                END) as delai_moyen
            FROM COMMANDES C
            INNER JOIN SOCIETES S ON C.ID_SOCIETE = S.ID
            LEFT JOIN LIVRAISONS_CMDE L ON C.ID = L.ID_COMMANDE 
            WHERE C.DteLivPrev IS NOT NULL 
            AND C.DteLivPrev <> '9999-12-31 00:00:00.000' 
            AND C.DteLivPrev > '1900-01-01'
            AND S.RaiSocTri IS NOT NULL
            GROUP BY S.RaiSocTri
            HAVING COUNT(*) >= 1
            ORDER BY COUNT(*) DESC
        """)
        clients = []
        for row in cursor.fetchall():
            total = row.total_commandes or 0
            livrees = row.commandes_livrees or 0
            a_temps = row.livrees_a_temps or 0
            taux_ponctualite = (a_temps / livrees * 100) if livrees > 0 else 0
            
            clients.append({
                "client": row.Client,
                "total_commandes": total,
                "commandes_livrees": livrees,
                "livrees_a_temps": a_temps,
                "taux_ponctualite": round(taux_ponctualite, 2),
                "delai_moyen": round(row.delai_moyen or 0, 2)
            })
        return clients

def get_alertes_retard():
    """Récupère les commandes en retard nécessitant une attention (sans date de livraison)"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                C.Numero,
                C.DteLivPrev,
                C.Reference,
                S.RaiSocTri AS Client,
                DATEDIFF(day, C.DteLivPrev, GETDATE()) as jours_retard
            FROM COMMANDES C
            INNER JOIN SOCIETES S ON C.ID_SOCIETE = S.ID
            LEFT JOIN LIVRAISONS_CMDE L ON C.ID = L.ID_COMMANDE 
            WHERE C.Termine = 0 
            AND C.DteLivPrev IS NOT NULL 
            AND C.DteLivPrev <> '9999-12-31 00:00:00.000' 
            AND C.DteLivPrev > '1900-01-01'
            AND C.DteLivPrev < GETDATE()
            AND L.DteLiv IS NULL
            ORDER BY C.DteLivPrev ASC
        """)
        alertes = []
        for row in cursor.fetchall():
            alertes.append({
                "numero": row.Numero,
                "date_prevue": row.DteLivPrev.strftime('%Y-%m-%d'),
                "reference": row.Reference,
                "client": row.Client,
                "jours_retard": row.jours_retard
            })
        return alertes


# ---------------------------
# PROJET 10 - CONTRÔLE QUALITÉ
# ---------------------------
def get_numeros_commandes_disponibles():
    """Récupère tous les numéros de commandes disponibles pour le contrôle qualité"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT Numero
            FROM COMMANDES
            WHERE Numero IS NOT NULL 
            AND Numero <> ''
            ORDER BY Numero
        """)
        numeros = []
        for row in cursor.fetchall():
            numeros.append(row.Numero.strip())
        return numeros

# ---------------------------
# CONTRÔLE QUALITÉ
# ---------------------------
def get_controles_qualite():
    """Récupère tous les contrôles qualité"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                id,
                date_controle,
                Numero_COMMANDES,
                operateur,
                machine_impression,
                operateur_machine_impression,
                machine_decoupe,
                operateur_machine_decoupe,
                rebus,
                validation_chef,
                date_creation
            FROM CONTROLES_QUALITE
            ORDER BY date_controle DESC, date_creation DESC
        """)
        controles = []
        for row in cursor.fetchall():
            controles.append({
                "id": row.id,
                "date_controle": row.date_controle,
                "Numero_COMMANDES": row.Numero_COMMANDES,
                "operateur": row.operateur,
                "machine_impression": row.machine_impression,
                "operateur_machine_impression": row.operateur_machine_impression,
                "machine_decoupe": row.machine_decoupe,
                "operateur_machine_decoupe": row.operateur_machine_decoupe,
                "rebus": row.rebus,
                "validation_chef": row.validation_chef,
                "date_creation": row.date_creation
            })
        return controles

def get_controle_qualite_by_id(controle_id):
    """Récupère un contrôle qualité par ID avec ses tolérances"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                id,
                date_controle,
                Numero_COMMANDES,
                operateur,
                machine_impression,
                operateur_machine_impression,
                machine_decoupe,
                operateur_machine_decoupe,
                rebus,
                validation_chef,
                date_creation
            FROM CONTROLES_QUALITE
            WHERE id = ?
        """, (controle_id,))
        
        controle = cursor.fetchone()
        if not controle:
            return None
            
        # Récupérer les tolérances
        cursor.execute("""
            SELECT 
                tolerance,
                quantite_conforme,
                quantite_non_conforme
            FROM TOLERANCES_CONTROLE
            WHERE controle_id = ?
            ORDER BY id
        """, (controle_id,))
        
        tolérances = []
        for row in cursor.fetchall():
            tolérances.append({
                "tolerance": row.tolerance,
                "quantite_conforme": row.quantite_conforme,
                "quantite_non_conforme": row.quantite_non_conforme
            })
        
        # Récupérer les détails des opérateurs depuis la table Employes si disponible
        operateur_machine_impression_details = []
        chef_details = {}
        
        try:
            if controle.operateur_machine_impression:
                # Parser les noms des opérateurs séparés par des virgules
                op_names = [name.strip() for name in controle.operateur_machine_impression.split(',')]
                for full_name in op_names:
                    if full_name:
                        # Essayer de récupérer les détails depuis la base
                        parts = full_name.split()
                        if len(parts) >= 2:
                            nom = parts[0]
                            prenom = ' '.join(parts[1:])
                            cursor.execute("""
                                SELECT TOP 1 Matricule, Nom, Prenom 
                                FROM Employes 
                                WHERE LTRIM(RTRIM(Nom)) = ? AND LTRIM(RTRIM(Prenom)) = ?
                            """, (nom, prenom))
                            emp = cursor.fetchone()
                            if emp:
                                operateur_machine_impression_details.append({
                                    'matricule': (emp.Matricule or '').strip(),
                                    'nom': (emp.Nom or '').strip(),
                                    'prenom': (emp.Prenom or '').strip()
                                })
            
            # Récupérer les détails du chef de section
            if controle.validation_chef:
                parts = controle.validation_chef.split()
                if len(parts) >= 2:
                    nom = parts[0]
                    prenom = ' '.join(parts[1:])
                    cursor.execute("""
                        SELECT TOP 1 Matricule, Nom, Prenom 
                        FROM Employes 
                        WHERE LTRIM(RTRIM(Nom)) = ? AND LTRIM(RTRIM(Prenom)) = ?
                    """, (nom, prenom))
                    emp = cursor.fetchone()
                    if emp:
                        chef_details = {
                            'chef_matricule': (emp.Matricule or '').strip(),
                            'chef_nom': (emp.Nom or '').strip(),
                            'chef_prenom': (emp.Prenom or '').strip()
                        }
        except Exception as e:
            # Si la table Employes n'existe pas ou autre erreur, on continue sans les détails
            print(f"Avertissement: Impossible de récupérer les détails des opérateurs depuis Employes: {e}")
        
        result = {
            "id": controle.id,
            "date_controle": controle.date_controle,
            "Numero_COMMANDES": controle.Numero_COMMANDES,
            "operateur": controle.operateur,
            "machine_impression": controle.machine_impression,
            "operateur_machine_impression": controle.operateur_machine_impression,
            "machine_decoupe": controle.machine_decoupe,
            "operateur_machine_decoupe": controle.operateur_machine_decoupe,
            "rebus": controle.rebus,
            "validation_chef": controle.validation_chef,
            "date_creation": controle.date_creation,
            "tolérances": tolérances
        }
        
        # Ajouter les détails des opérateurs machine impression si disponibles
        if operateur_machine_impression_details:
            result['operateur_machine_impression_matricules'] = [d['matricule'] for d in operateur_machine_impression_details]
            result['operateur_machine_impression_noms'] = [d['nom'] for d in operateur_machine_impression_details]
            result['operateur_machine_impression_prenoms'] = [d['prenom'] for d in operateur_machine_impression_details]
        
        # Ajouter les détails du chef de section si disponibles
        if chef_details:
            result.update(chef_details)
        
        return result

def get_controle_qualite_by_numero(numero_commande):
    """Récupère le contrôle qualité le plus récent par numéro de commande avec ses tolérances"""
    with get_db_cursor() as cursor:
        # Nettoyer le numéro de commande (enlever les espaces)
        numero_clean = numero_commande.strip() if numero_commande else ''
        
        cursor.execute("""
            SELECT TOP 1
                id,
                date_controle,
                Numero_COMMANDES,
                operateur,
                machine_impression,
                operateur_machine_impression,
                machine_decoupe,
                operateur_machine_decoupe,
                rebus,
                validation_chef,
                date_creation
            FROM CONTROLES_QUALITE
            WHERE LTRIM(RTRIM(Numero_COMMANDES)) = ?
            ORDER BY date_creation DESC
        """, (numero_clean,))
        
        controle = cursor.fetchone()
        if not controle:
            return None
            
        # Récupérer les tolérances
        cursor.execute("""
            SELECT 
                tolerance,
                quantite_conforme,
                quantite_non_conforme
            FROM TOLERANCES_CONTROLE
            WHERE controle_id = ?
            ORDER BY id
        """, (controle.id,))
        
        tolérances = []
        for row in cursor.fetchall():
            tolérances.append({
                "tolerance": row.tolerance,
                "quantite_conforme": row.quantite_conforme,
                "quantite_non_conforme": row.quantite_non_conforme
            })
        
        result = {
            "id": controle.id,
            "date_controle": controle.date_controle,
            "Numero_COMMANDES": controle.Numero_COMMANDES,
            "operateur": controle.operateur,
            "machine_impression": controle.machine_impression,
            "operateur_machine_impression": controle.operateur_machine_impression,
            "machine_decoupe": controle.machine_decoupe,
            "operateur_machine_decoupe": controle.operateur_machine_decoupe,
            "rebus": controle.rebus,
            "validation_chef": controle.validation_chef,
            "date_creation": controle.date_creation,
            "tolérances": tolérances
        }
        
        return result

def create_controle_qualite(data):
    """Crée un nouveau contrôle qualité"""
    try:
        with get_db_cursor() as cursor:
            # Insérer le contrôle qualité et récupérer l'ID directement
            print(f"DEBUG CREATE: Insertion contrôle avec data={data}")
            cursor.execute("""
                INSERT INTO CONTROLES_QUALITE (
                    date_controle, Numero_COMMANDES, operateur, machine_impression, operateur_machine_impression, 
                    machine_decoupe, operateur_machine_decoupe, rebus, validation_chef, date_creation
                )
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                data['date_controle'],
                data['Numero_COMMANDES'],
                data['operateur'],
                data.get('machine_impression', ''),
                data.get('operateur_machine_impression', ''),
                data.get('machine_decoupe', ''),
                data.get('operateur_machine_decoupe', ''),
                data.get('rebus', 0),
                data.get('validation_chef', ''),
            ))
            
            # Récupérer l'ID du contrôle créé
            controle_id = cursor.fetchone()[0]
            print(f"DEBUG CREATE: Contrôle créé avec ID={controle_id}")
            
            # Insérer les tolérances (accepte 'tolérances' ou 'tolerances')
            tolerances_list = data.get('tolérances') or data.get('tolerances') or []
            print(f"DEBUG CREATE: Insertion de {len(tolerances_list)} tolérances")
            if tolerances_list:
                for i, tolerance_data in enumerate(tolerances_list):
                    # Ne pas insérer de lignes vides
                    if (tolerance_data.get('tolerance', '').strip() or 
                        tolerance_data.get('quantite_conforme', 0) or 
                        tolerance_data.get('quantite_non_conforme', 0)):
                        print(f"DEBUG CREATE: Insertion tolérance {i+1}: {tolerance_data}")
                    cursor.execute("""
                        INSERT INTO TOLERANCES_CONTROLE (
                            controle_id, tolerance, quantite_conforme, quantite_non_conforme
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        controle_id,
                            tolerance_data.get('tolerance', ''),
                            tolerance_data.get('quantite_conforme', 0),
                            tolerance_data.get('quantite_non_conforme', 0)
                    ))
            
            # Valider la transaction
            cursor.commit()
            print(f"DEBUG CREATE: Transaction validée, retour ID={controle_id}")
            return controle_id
    except Exception as e:
        print(f"ERREUR lors de la création du contrôle qualité: {e}")
        import traceback
        traceback.print_exc()
        return None

def update_controle_qualite(controle_id, data):
    """Met à jour un contrôle qualité"""
    try:
        with get_db_cursor() as cursor:
            # Mettre à jour le contrôle qualité
            cursor.execute("""
                UPDATE CONTROLES_QUALITE SET
                    date_controle = ?,
                    Numero_COMMANDES = ?,
                    operateur = ?,
                    machine_impression = ?,
                    operateur_machine_impression = ?,
                    machine_decoupe = ?,
                    operateur_machine_decoupe = ?,
                    rebus = ?,
                    validation_chef = ?
                WHERE id = ?
            """, (
                data['date_controle'],
                data['Numero_COMMANDES'],
                data['operateur'],
                data.get('machine_impression', ''),
                data.get('operateur_machine_impression', ''),
                data.get('machine_decoupe', ''),
                data.get('operateur_machine_decoupe', ''),
                data.get('rebus', 0),
                data.get('validation_chef', ''),
                controle_id
            ))
            
            # Supprimer les anciennes tolérances
            cursor.execute("DELETE FROM TOLERANCES_CONTROLE WHERE controle_id = ?", (controle_id,))
            
            # Insérer les nouvelles tolérances (accepte 'tolérances' ou 'tolerances')
            tolerances_list = data.get('tolérances') or data.get('tolerances') or []
            if tolerances_list:
                for tolerance_data in tolerances_list:
                    # Ne pas insérer de lignes vides
                    if (tolerance_data.get('tolerance', '').strip() or 
                        tolerance_data.get('quantite_conforme', 0) or 
                        tolerance_data.get('quantite_non_conforme', 0)):
                        cursor.execute("""
                            INSERT INTO TOLERANCES_CONTROLE (
                            controle_id, tolerance, quantite_conforme, quantite_non_conforme
                            ) VALUES (?, ?, ?, ?)
                            """, (
                            controle_id,
                            tolerance_data.get('tolerance', ''),
                            tolerance_data.get('quantite_conforme', 0),
                            tolerance_data.get('quantite_non_conforme', 0)
                            ))
            # Valider la transaction
            cursor.connection.commit()
            
            return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour du contrôle qualité: {e}")
        return False

def get_statistiques_controle_qualite():
    """Récupère les statistiques globales de contrôle qualité"""
    with get_db_cursor() as cursor:
        # Statistiques globales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_controles,
                COUNT(CASE WHEN validation_chef IS NOT NULL AND validation_chef != '' THEN 1 END) as controles_valides,
                AVG(CAST(rebus AS FLOAT)) as rebus_moyen,
                SUM(rebus) as total_rebus
            FROM CONTROLES_QUALITE
        """)
        
        row = cursor.fetchone()
        stats = {
                "total_controles": row.total_controles or 0,
                "controles_valides": row.controles_valides or 0,
                "rebus_moyen": round(row.rebus_moyen or 0, 3),
                "total_rebus": row.total_rebus or 0
            }
        
        # Calculer taux de conformité et taux de rebus
        cursor.execute("""
            SELECT 
                SUM(T.quantite_conforme) as total_conforme,
                SUM(CASE 
                    WHEN rn = 1 THEN T.quantite_non_conforme 
                    ELSE 0 
                END) as total_non_conforme_final
            FROM TOLERANCES_CONTROLE T
            INNER JOIN (
                SELECT controle_id, id, 
                       ROW_NUMBER() OVER (PARTITION BY controle_id ORDER BY id DESC) as rn
                FROM TOLERANCES_CONTROLE
            ) LastRow ON T.id = LastRow.id
        """)
        
        row2 = cursor.fetchone()
        total_conforme = row2.total_conforme or 0
        total_non_conforme = row2.total_non_conforme_final or 0
        total_produit = total_conforme + total_non_conforme
        
        stats["total_conforme"] = total_conforme
        stats["total_non_conforme"] = total_non_conforme
        stats["total_produit"] = total_produit
        stats["taux_conformite"] = round((total_conforme / total_produit * 100) if total_produit > 0 else 0, 3)
        stats["taux_rebus"] = round((total_non_conforme / total_produit * 100) if total_produit > 0 else 0, 3)
        
        return stats

def get_performance_par_machine():
    """Récupère les statistiques de performance par machine d'impression"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            WITH DernieresLignes AS (
                SELECT 
                    T.controle_id,
                    T.quantite_conforme,
                    T.quantite_non_conforme,
                    ROW_NUMBER() OVER (PARTITION BY T.controle_id ORDER BY T.id DESC) as rn
                FROM TOLERANCES_CONTROLE T
            ),
            StatsParControle AS (
                SELECT 
                    C.id,
                    C.machine_impression,
                    SUM(T.quantite_conforme) as total_conforme,
                    MAX(CASE WHEN D.rn = 1 THEN D.quantite_non_conforme ELSE 0 END) as rebus
                FROM CONTROLES_QUALITE C
                LEFT JOIN TOLERANCES_CONTROLE T ON T.controle_id = C.id
                LEFT JOIN DernieresLignes D ON D.controle_id = C.id AND D.rn = 1
                WHERE C.machine_impression IS NOT NULL AND C.machine_impression != ''
                GROUP BY C.id, C.machine_impression
            )
            SELECT 
                machine_impression,
                COUNT(*) as nombre_controles,
                SUM(total_conforme) as total_conforme,
                SUM(rebus) as total_rebus,
                SUM(total_conforme + rebus) as total_produit,
                CASE 
                    WHEN SUM(total_conforme + rebus) > 0 
                    THEN ROUND(SUM(total_conforme) * 100.0 / SUM(total_conforme + rebus), 2)
                    ELSE 0 
                END as taux_conformite
            FROM StatsParControle
            GROUP BY machine_impression
            ORDER BY taux_conformite DESC
        """)
        
        machines = []
        for row in cursor.fetchall():
            machines.append({
                "machine": row.machine_impression,
                "nombre_controles": row.nombre_controles or 0,
                "total_conforme": row.total_conforme or 0,
                "total_rebus": row.total_rebus or 0,
                "total_produit": row.total_produit or 0,
                "taux_conformite": row.taux_conformite or 0
            })
        return machines

def get_evolution_qualite(jours=30):
    """Récupère l'évolution de la qualité sur les N derniers jours"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            WITH DernieresLignes AS (
                SELECT 
                    T.controle_id,
                    T.quantite_non_conforme,
                    ROW_NUMBER() OVER (PARTITION BY T.controle_id ORDER BY T.id DESC) as rn
                FROM TOLERANCES_CONTROLE T
            ),
            StatsParJour AS (
                SELECT 
                    CAST(C.date_controle AS DATE) as jour,
                    SUM(T.quantite_conforme) as total_conforme,
                    SUM(CASE WHEN D.rn = 1 THEN D.quantite_non_conforme ELSE 0 END) as total_rebus
                FROM CONTROLES_QUALITE C
                LEFT JOIN TOLERANCES_CONTROLE T ON T.controle_id = C.id
                LEFT JOIN DernieresLignes D ON D.controle_id = C.id
                WHERE C.date_controle >= DATEADD(day, -?, GETDATE())
                GROUP BY CAST(C.date_controle AS DATE)
            )
            SELECT 
                jour,
                total_conforme,
                total_rebus,
                (total_conforme + total_rebus) as total_produit,
                CASE 
                    WHEN (total_conforme + total_rebus) > 0 
                    THEN ROUND(total_conforme * 100.0 / (total_conforme + total_rebus), 2)
                    ELSE 0 
                END as taux_conformite
            FROM StatsParJour
            ORDER BY jour
        """, (jours,))
        
        evolution = []
        for row in cursor.fetchall():
            # Gérer le cas où jour est déjà une chaîne
            date_str = ''
            if row.jour:
                if isinstance(row.jour, str):
                    date_str = row.jour.split('T')[0] if 'T' in row.jour else row.jour
                else:
                    date_str = row.jour.strftime('%Y-%m-%d')
            
            evolution.append({
                "date": date_str,
                "total_conforme": row.total_conforme or 0,
                "total_rebus": row.total_rebus or 0,
                "total_produit": row.total_produit or 0,
                "taux_conformite": row.taux_conformite or 0
            })
        return evolution

def get_dossiers_probleme(seuil_rebus_pct=10):
    """Récupère les contrôles individuels avec un taux de rebus élevé"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            WITH DernieresLignes AS (
                SELECT 
                    T.controle_id,
                    T.quantite_non_conforme,
                    ROW_NUMBER() OVER (PARTITION BY T.controle_id ORDER BY T.id DESC) as rn
                FROM TOLERANCES_CONTROLE T
            ),
            StatsControle AS (
                SELECT 
                    C.id as controle_id,
                    C.Numero_COMMANDES,
                    C.date_controle,
                    C.operateur,
                    C.machine_impression,
                    SUM(T.quantite_conforme) as total_conforme,
                    MAX(CASE WHEN D.rn = 1 THEN D.quantite_non_conforme ELSE 0 END) as total_rebus
                FROM CONTROLES_QUALITE C
                LEFT JOIN TOLERANCES_CONTROLE T ON T.controle_id = C.id
                LEFT JOIN DernieresLignes D ON D.controle_id = C.id
                GROUP BY C.id, C.Numero_COMMANDES, C.date_controle, C.operateur, C.machine_impression
            )
            SELECT 
                controle_id,
                Numero_COMMANDES,
                date_controle,
                operateur,
                machine_impression,
                total_conforme,
                total_rebus,
                (total_conforme + total_rebus) as total_produit,
                CASE 
                    WHEN (total_conforme + total_rebus) > 0 
                    THEN ROUND(total_rebus * 100.0 / (total_conforme + total_rebus), 3)
                    ELSE 0 
                END as taux_rebus
            FROM StatsControle
            WHERE (total_conforme + total_rebus) > 0
              AND (total_rebus * 100.0 / (total_conforme + total_rebus)) >= ?
            ORDER BY taux_rebus DESC
        """, (seuil_rebus_pct,))
        
        dossiers = []
        for row in cursor.fetchall():
            # Gérer le cas où date_controle est déjà une chaîne
            date_str = ''
            if row.date_controle:
                if isinstance(row.date_controle, str):
                    date_str = row.date_controle.split('T')[0] if 'T' in row.date_controle else row.date_controle
                else:
                    date_str = row.date_controle.strftime('%Y-%m-%d')
            
            dossiers.append({
                "controle_id": row.controle_id,
                "Numero_COMMANDES": row.Numero_COMMANDES,
                "date": date_str,
                "operateur": row.operateur or '',
                "machine": row.machine_impression or '',
                "total_conforme": row.total_conforme or 0,
                "total_rebus": row.total_rebus or 0,
                "total_produit": row.total_produit or 0,
                "taux_rebus": row.taux_rebus or 0
            })
        return dossiers

def get_comparaison_periodes(date_debut1, date_fin1, date_debut2, date_fin2):
    """Compare les statistiques entre deux périodes"""
    with get_db_cursor() as cursor:
        # Statistiques pour la période 1
        cursor.execute("""
            WITH DernieresLignes AS (
                SELECT 
                    T.controle_id,
                    T.quantite_non_conforme,
                    ROW_NUMBER() OVER (PARTITION BY T.controle_id ORDER BY T.id DESC) as rn
                FROM TOLERANCES_CONTROLE T
            )
            SELECT 
                COUNT(DISTINCT C.id) as nombre_controles,
                SUM(T.quantite_conforme) as total_conforme,
                SUM(CASE WHEN D.rn = 1 THEN D.quantite_non_conforme ELSE 0 END) as total_rebus,
                SUM(T.quantite_conforme) + SUM(CASE WHEN D.rn = 1 THEN D.quantite_non_conforme ELSE 0 END) as total_produit
            FROM CONTROLES_QUALITE C
            LEFT JOIN TOLERANCES_CONTROLE T ON T.controle_id = C.id
            LEFT JOIN DernieresLignes D ON D.controle_id = C.id
            WHERE CAST(C.date_controle AS DATE) BETWEEN ? AND ?
        """, (date_debut1, date_fin1))
        
        row1 = cursor.fetchone()
        periode1 = {
            "nombre_controles": row1.nombre_controles or 0,
            "total_conforme": row1.total_conforme or 0,
            "total_rebus": row1.total_rebus or 0,
            "total_produit": row1.total_produit or 0
        }
        periode1["taux_conformite"] = round((periode1["total_conforme"] / periode1["total_produit"] * 100) if periode1["total_produit"] > 0 else 0, 3)
        periode1["taux_rebus"] = round((periode1["total_rebus"] / periode1["total_produit"] * 100) if periode1["total_produit"] > 0 else 0, 3)
        
        # Statistiques pour la période 2
        cursor.execute("""
            WITH DernieresLignes AS (
                SELECT 
                    T.controle_id,
                    T.quantite_non_conforme,
                    ROW_NUMBER() OVER (PARTITION BY T.controle_id ORDER BY T.id DESC) as rn
                FROM TOLERANCES_CONTROLE T
            )
            SELECT 
                COUNT(DISTINCT C.id) as nombre_controles,
                SUM(T.quantite_conforme) as total_conforme,
                SUM(CASE WHEN D.rn = 1 THEN D.quantite_non_conforme ELSE 0 END) as total_rebus,
                SUM(T.quantite_conforme) + SUM(CASE WHEN D.rn = 1 THEN D.quantite_non_conforme ELSE 0 END) as total_produit
            FROM CONTROLES_QUALITE C
            LEFT JOIN TOLERANCES_CONTROLE T ON T.controle_id = C.id
            LEFT JOIN DernieresLignes D ON D.controle_id = C.id
            WHERE CAST(C.date_controle AS DATE) BETWEEN ? AND ?
        """, (date_debut2, date_fin2))
        
        row2 = cursor.fetchone()
        periode2 = {
            "nombre_controles": row2.nombre_controles or 0,
            "total_conforme": row2.total_conforme or 0,
            "total_rebus": row2.total_rebus or 0,
            "total_produit": row2.total_produit or 0
        }
        periode2["taux_conformite"] = round((periode2["total_conforme"] / periode2["total_produit"] * 100) if periode2["total_produit"] > 0 else 0, 3)
        periode2["taux_rebus"] = round((periode2["total_rebus"] / periode2["total_produit"] * 100) if periode2["total_produit"] > 0 else 0, 3)
        
        return {
            "periode1": periode1,
            "periode2": periode2
        }

def get_machines_impression():
    """Récupère la liste des machines d'impression depuis GP_POSTES (centre de coût 6)"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT P.Nom, P.ID
            FROM GP_POSTES P
            WHERE P.ID_CENTRE_COUT = 6
              AND P.Nom IS NOT NULL 
              AND P.Nom != ''
            ORDER BY P.Nom
        """)
        machines = []
        for row in cursor.fetchall():
            machines.append({
                "nom": row.Nom,
                "id": row.ID
            })
        return machines

def get_comparaison_machines(machine1, machine2, jours=30):
    """Compare les statistiques entre deux machines sur une période donnée"""
    with get_db_cursor() as cursor:
        # Statistiques pour la machine 1
        cursor.execute("""
            WITH DernieresLignes AS (
                SELECT 
                    T.controle_id,
                    T.quantite_non_conforme,
                    ROW_NUMBER() OVER (PARTITION BY T.controle_id ORDER BY T.id DESC) as rn
                FROM TOLERANCES_CONTROLE T
            )
            SELECT 
                COUNT(DISTINCT C.id) as nombre_controles,
                SUM(T.quantite_conforme) as total_conforme,
                SUM(CASE WHEN D.rn = 1 THEN D.quantite_non_conforme ELSE 0 END) as total_rebus,
                SUM(T.quantite_conforme) + SUM(CASE WHEN D.rn = 1 THEN D.quantite_non_conforme ELSE 0 END) as total_produit
            FROM CONTROLES_QUALITE C
            LEFT JOIN TOLERANCES_CONTROLE T ON T.controle_id = C.id
            LEFT JOIN DernieresLignes D ON D.controle_id = C.id
            WHERE C.machine_impression = ?
              AND C.date_controle >= DATEADD(day, -?, GETDATE())
        """, (machine1, jours))
        
        row1 = cursor.fetchone()
        stats_machine1 = {
            "machine": machine1,
            "nombre_controles": row1.nombre_controles or 0,
            "total_conforme": row1.total_conforme or 0,
            "total_rebus": row1.total_rebus or 0,
            "total_produit": row1.total_produit or 0
        }
        stats_machine1["taux_conformite"] = round((stats_machine1["total_conforme"] / stats_machine1["total_produit"] * 100) if stats_machine1["total_produit"] > 0 else 0, 3)
        stats_machine1["taux_rebus"] = round((stats_machine1["total_rebus"] / stats_machine1["total_produit"] * 100) if stats_machine1["total_produit"] > 0 else 0, 3)
        
        # Statistiques pour la machine 2
        cursor.execute("""
            WITH DernieresLignes AS (
                SELECT 
                    T.controle_id,
                    T.quantite_non_conforme,
                    ROW_NUMBER() OVER (PARTITION BY T.controle_id ORDER BY T.id DESC) as rn
                FROM TOLERANCES_CONTROLE T
            )
            SELECT 
                COUNT(DISTINCT C.id) as nombre_controles,
                SUM(T.quantite_conforme) as total_conforme,
                SUM(CASE WHEN D.rn = 1 THEN D.quantite_non_conforme ELSE 0 END) as total_rebus,
                SUM(T.quantite_conforme) + SUM(CASE WHEN D.rn = 1 THEN D.quantite_non_conforme ELSE 0 END) as total_produit
            FROM CONTROLES_QUALITE C
            LEFT JOIN TOLERANCES_CONTROLE T ON T.controle_id = C.id
            LEFT JOIN DernieresLignes D ON D.controle_id = C.id
            WHERE C.machine_impression = ?
              AND C.date_controle >= DATEADD(day, -?, GETDATE())
        """, (machine2, jours))
        
        row2 = cursor.fetchone()
        stats_machine2 = {
            "machine": machine2,
            "nombre_controles": row2.nombre_controles or 0,
            "total_conforme": row2.total_conforme or 0,
            "total_rebus": row2.total_rebus or 0,
            "total_produit": row2.total_produit or 0
        }
        stats_machine2["taux_conformite"] = round((stats_machine2["total_conforme"] / stats_machine2["total_produit"] * 100) if stats_machine2["total_produit"] > 0 else 0, 3)
        stats_machine2["taux_rebus"] = round((stats_machine2["total_rebus"] / stats_machine2["total_produit"] * 100) if stats_machine2["total_produit"] > 0 else 0, 3)
        
        return {
            "machine1": stats_machine1,
            "machine2": stats_machine2
        }

def marquer_livraison_reelle(numero, date_livraison, user=None):
    """Marque une commande comme livrée avec la date réelle"""
    try:
        date_obj = datetime.strptime(date_livraison, '%Y-%m-%d')
        with get_db_cursor() as cursor:
            # Mettre à jour la commande
            cursor.execute("""
                UPDATE COMMANDES 
                SET DteLivReelle = ?, Termine = 1, EtatLiv = 1
                WHERE Numero = ?
            """, date_obj, numero)
            
            # Enregistrer dans l'historique si un utilisateur est fourni
            if user:
                cursor.execute("""
                    INSERT INTO HISTORIQUE_LIVRAISON 
                    (NumeroCommande, AncienneDate, NouvelleDate, ModifiePar, TypeModification)
                    VALUES (?, NULL, ?, ?, 'Livraison Réelle')
                """, numero, date_obj, user)
            
            cursor.connection.commit()
            return True
    except Exception as e:
        print(f"[Erreur marquage livraison] {e}")
        return False

# ---------------------------
# PROJET 2 – COMMANDES EN COURS
# ---------------------------
def get_commandes_en_cours():
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                C.Numero, 
                S.RaiSocTri, 
                C.Reference, 
                C.PourcentageReceptElem, 
                C.EtatPrepress, 
                C.EtatImpression, 
                C.EtatFaconnage, 
                C.EtatLiv,
                CASE WHEN MVT.TypePiece = 'D' THEN 'OK' ELSE 'En Attente' END AS SortiePapier
            FROM COMMANDES C
            LEFT JOIN SOCIETES S ON C.ID_SOCIETE = S.ID
            LEFT JOIN GS_MVT_STOCKS MVT ON LTRIM(RTRIM(C.Numero)) = LTRIM(RTRIM(MVT.NumDossier))
            LEFT JOIN GS_STOCKS ST ON ST.ID = MVT.ID_STOCK
            LEFT JOIN GS_ARTICLES A ON A.ID = ST.ID
            LEFT JOIN GS_FAMILLES F ON F.ID = A.ID_FAMILLE
            LEFT JOIN GS_TYPES_ARTICLE T ON T.ID = F.ID_TYPE_ARTICLE
            WHERE C.Termine = 0 AND T.Code IN ('P','B','O','D','V')
            ORDER BY C.Numero DESC
        """)
        return cursor.fetchall()

# ---------------------------
# PROJET 3 – SUIVI BAT
# ---------------------------
def get_commandes_bat():
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                C.ID, 
                C.Numero, 
                S.RaiSocTri AS RaisonSociale, 
                C.DteBat, 
                C.DteReceptElem, 
                C.EtatPrepress, 
                C.PourcentageReceptElem, 
                C.EtatLiv
            FROM COMMANDES C
            LEFT JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
            WHERE C.Termine = 0
        """)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results

def update_date_bat(id_commande, date_bat):
    try:
        date_obj = datetime.strptime(date_bat, "%Y-%m-%d")
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE COMMANDES 
                SET DteBat = ?
                WHERE ID = ?
            """, date_obj, id_commande)
            cursor.connection.commit()
            return True
    except Exception as e:
        print(f"[Erreur MAJ DteBat] {e}")
        return False

def update_reception_elem(id_commande):
    try:
        today = datetime.now().date()
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE COMMANDES
                SET DteReceptElem = ?
                WHERE ID = ?
            """, today, id_commande)
            cursor.connection.commit()
            return True
    except Exception as e:
        print(f"[Erreur MAJ réception] {e}")
        return False

def envoyer_bat(id_commande):
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE COMMANDES
                SET EtatPrepress = 1
                WHERE ID = ?
            """, id_commande)
            cursor.connection.commit()
            return True
    except Exception as e:
        print(f"[Erreur envoi BAT] {e}")
        return False

def get_contact_principal(id_societe):
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                P.ID AS ID_PERSONNE,
                P.Nom,
                P.Prenom,
                P.Telephone,
                P.Mobile,
                M.Mail,
                FCT.Fonction
            FROM SOCIETES_PERSONNES SP
            INNER JOIN PERSONNES P ON P.ID = SP.ID_PERSONNE
            LEFT JOIN (
                SELECT ID_PERSONNE, Mail
                FROM PERSONNES_MAIL
                WHERE ParDefaut = 1
            ) M ON M.ID_PERSONNE = P.ID
            LEFT JOIN (
                SELECT PF.ID_PERSONNE, FO.Nom AS Fonction, 
                       ROW_NUMBER() OVER (PARTITION BY PF.ID_PERSONNE ORDER BY PF.Ordre ASC) AS rn
                FROM PERSONNES_FONCTIONS PF
                INNER JOIN FONCTIONS FO ON FO.ID = PF.ID_FONCTION
            ) FCT ON FCT.ID_PERSONNE = P.ID AND FCT.rn = 1
            WHERE SP.ID_SOCIETE = ? AND SP.Principal = 1
        """, id_societe)

        row = cursor.fetchone()
        if row:
            return {
                "nom": row.Nom,
                "prenom": row.Prenom,
                "telephone": row.Telephone or row.Mobile,
                "email": row.Mail,
                "fonction": row.Fonction
            }
    return None

# ---------------------------
# PROJET 10 – Contrôle Qualité - Gestion des Opérateurs
# ---------------------------
def get_operateurs():
    """Récupère la liste des opérateurs disponibles (employés)"""
    with get_db_cursor() as cursor:
        operateurs: list[dict] = []
        # Utiliser la table [dbo].[personel]
        try:
            cursor.execute("""
                SELECT 
                    Matricule,
                    COALESCE(Nom, '') AS Nom,
                    COALESCE(Prenom, '') AS Prenom
                FROM [dbo].[personel]
                WHERE Matricule IS NOT NULL
                ORDER BY Nom, Prenom
            """)
            rows = cursor.fetchall()
            for row in rows:
                # Matricule peut être un INT, le convertir en string
                matricule_str = str(row.Matricule) if row.Matricule is not None else ''
                operateurs.append({
                    "id": None,
                    "matricule": matricule_str.strip(),
                    "nom": (row.Nom or '').strip(),
                    "prenom": (row.Prenom or '').strip(),
                    "nom_complet": f"{(row.Nom or '').strip()} {(row.Prenom or '').strip()}".strip(),
                    "telephone": None,
                    "email": None
                })
        except Exception as e:
            print(f"Erreur lors de la récupération des opérateurs depuis [dbo].[personel]: {e}")
            import traceback
            traceback.print_exc()

        # Dédupliquer par matricule si nécessaire et trier
        seen = set()
        unique_operateurs = []
        for op in operateurs:
            key = (op.get("matricule") or "").strip().lower()
            if key in seen:
                continue
            seen.add(key)
            unique_operateurs.append(op)

        # Tri alpha par Nom, Prénom si disponible, sinon par matricule
        unique_operateurs.sort(key=lambda o: (
            (o.get("nom") or "").lower(),
            (o.get("prenom") or "").lower(),
            (o.get("matricule") or "").lower()
        ))
        return unique_operateurs

# ---------------------------
# PROJET 4 – CRM – Création Prospect + Contact
# ---------------------------
def creer_prospect(raison_sociale, ville=None, pays=None, telephone=None, email=None, id_categorie=None):
    with get_db_cursor() as cursor:
        # 1. Insertion dans SOCIETES avec ID_CATEGORIE en plus
        cursor.execute("""
            INSERT INTO SOCIETES (
                ID_CATEGORIE,
                ID_DEVISE,
                RaiSocTri,
                Archive,
                DateCreation,
                Langue,
                Effectif,
                CA,
                Modele,
                DepotFichiers,
                ApprobationEnLigne,
                ExpediteurSocUtil
            )
            OUTPUT INSERTED.ID
            VALUES (?, ?, ?, 0, GETDATE(), ?, ?, ?, 0, 0, 0, 1)
        """, (
            id_categorie,
            'TND',
            raison_sociale,
            1036,  # Langue
            0,     # Effectif
            0      # Chiffre d'affaires
        ))
        id_societe = cursor.fetchone()[0]

        # 2. Insertion dans SOCIETES_ADRESSES
        cursor.execute("""
            INSERT INTO SOCIETES_ADRESSES (
                ID_SOCIETE, Nom, Adresse, Ville, CodePostal,
                ID_PAYS, Telephone, Fax, Mail,
                RefuseEMailling, AdrPostale, AdrPhysique,
                AdrFacturation, AdrLivraison
            )
            VALUES (?, ?, ?, ?, ?, 
                (SELECT TOP 1 ID FROM PAYS WHERE Nom = ?),
                ?, ?, ?, 
                0, 1, 1, 0, 1
            )
        """, (
            id_societe,
            raison_sociale,
            '',                 # Adresse vide mais requise
            ville or '',
            '',                 # CodePostal vide
            pays,
            telephone or '',
            '',                 # Fax vide
            email or ''
        ))

        # 3. Générer un numéro de compte unique
        cursor.execute("SELECT ISNULL(MAX(CAST(Compte AS INT)), 0) + 1 FROM SOCIETES_SOCUTIL")
        nouveau_compte = cursor.fetchone()[0]

        # 4. Insertion dans SOCIETES_SOCUTIL
        cursor.execute("""
            INSERT INTO SOCIETES_SOCUTIL (
                ID_SOCIETE, ID_SOCUTIL, Compte, Coefficient,
                ClientProspect, RegElemFact, ID_TARIF
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            id_societe,
            0,  # ID_SOCUTIL existant
            str(nouveau_compte).zfill(5),
            30,
            2,  # Prospect
            1,  # RegElemFact
            0   # ID_TARIF par défaut
        ))


        cursor.connection.commit()
        return id_societe

# ---------------------------
# PROJET WEB - WEB_S_DOS_ENCOURS
# ---------------------------
def get_web_s_dos_encours(search_numero=None):
    """
    Récupère les dossiers en cours depuis WEB_S_DOS_ENCOURS
    Si search_numero est fourni, recherche les dossiers dont le numéro contient cette valeur
    """
    with get_db_cursor() as cursor:
        # Vérifier quelles colonnes existent
        try:
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                AND COLUMN_NAME IN ('Nom_GP_SERVICES', 'PrixVenteUnitaire', 'QteComm_COMMANDES', 'PrixVenteTotal', 'CTEstimé', 'CoutTotal', 'CtRel')
            """)
            existing_cols = {row.COLUMN_NAME for row in cursor.fetchall()}
            avancement_exists = 'Nom_GP_SERVICES' in existing_cols
            prix_exists = 'PrixVenteUnitaire' in existing_cols
            quantite_exists = 'QteComm_COMMANDES' in existing_cols
            prix_total_exists = 'PrixVenteTotal' in existing_cols
            ct_estime_exists = 'CTEstimé' in existing_cols
            cout_total_exists = 'CoutTotal' in existing_cols
            ct_rel_exists = 'CtRel' in existing_cols
        except Exception as e:
            print(f"[WARNING] Erreur lors de la vérification des colonnes: {e}")
            avancement_exists = False
            prix_exists = False
            quantite_exists = False
            prix_total_exists = False
            ct_estime_exists = False
            cout_total_exists = False
            ct_rel_exists = False
        
        # Construire la liste des colonnes dynamiquement
        columns_list = ['ID', 'Numero_COMMANDES', 'RaiSocTri_SOCIETES', 'Reference_COMMANDES', 'Coef_COMMANDES']
        if avancement_exists:
            columns_list.append('Nom_GP_SERVICES')
        if prix_exists:
            columns_list.append('PrixVenteUnitaire')
        if quantite_exists:
            columns_list.append('QteComm_COMMANDES')
        if prix_total_exists:
            columns_list.append('PrixVenteTotal')
        if ct_estime_exists:
            columns_list.append('CTEstimé')
        if cout_total_exists:
            columns_list.append('CoutTotal')
        if ct_rel_exists:
            columns_list.append('CtRel')
        columns_list.extend(['DateCreation', 'DateModification'])
        
        select_cols = ', '.join(columns_list)
        print(f"[DEBUG] Colonnes SELECT: {select_cols}")
        
        if search_numero:
            cursor.execute(f"""
                SELECT {select_cols}
                FROM WEB_S_DOS_ENCOURS
                WHERE Numero_COMMANDES LIKE ?
                ORDER BY Numero_COMMANDES
            """, (f'%{search_numero}%',))
        else:
            cursor.execute(f"""
                SELECT {select_cols}
                FROM WEB_S_DOS_ENCOURS
                ORDER BY Numero_COMMANDES
            """)
        
        result = []
        for row in cursor.fetchall():
            # Convertir Decimal en float pour la sérialisation JSON
            marge_value = None
            if row.Coef_COMMANDES is not None:
                try:
                    marge_value = float(row.Coef_COMMANDES)
                except (ValueError, TypeError):
                    marge_value = None
            
            dossier = {
                "id": row.ID,
                "numero": row.Numero_COMMANDES,
                "client": row.RaiSocTri_SOCIETES,
                "reference": row.Reference_COMMANDES,
                "marge": marge_value,
                "date_creation": row.DateCreation.isoformat() if row.DateCreation else None,
                "date_modification": row.DateModification.isoformat() if row.DateModification else None
            }
            
            # Ajouter avancement seulement si la colonne existe
            if avancement_exists:
                dossier["avancement"] = row.Nom_GP_SERVICES if hasattr(row, 'Nom_GP_SERVICES') else None
            else:
                dossier["avancement"] = None
            
            # Ajouter prix_vente_unitaire seulement si la colonne existe
            if prix_exists:
                prix_value = row.PrixVenteUnitaire if hasattr(row, 'PrixVenteUnitaire') else None
                if prix_value is not None:
                    dossier["prix_vente_unitaire"] = float(round(prix_value, 3))
                else:
                    dossier["prix_vente_unitaire"] = None
            else:
                dossier["prix_vente_unitaire"] = None
            
            # Ajouter quantite seulement si la colonne existe
            if quantite_exists:
                quantite_value = row.QteComm_COMMANDES if hasattr(row, 'QteComm_COMMANDES') else None
                dossier["quantite"] = int(quantite_value) if quantite_value is not None else None
            else:
                dossier["quantite"] = None
            
            # Ajouter prix_vente_total seulement si la colonne existe
            if prix_total_exists:
                prix_total_value = row.PrixVenteTotal if hasattr(row, 'PrixVenteTotal') else None
                if prix_total_value is not None:
                    dossier["prix_vente_total"] = float(round(prix_total_value, 3))
                else:
                    dossier["prix_vente_total"] = None
            else:
                dossier["prix_vente_total"] = None
            
            # Ajouter ct_estime seulement si la colonne existe
            if ct_estime_exists:
                ct_estime_value = row.CTEstimé if hasattr(row, 'CTEstimé') else None
                if ct_estime_value is not None:
                    dossier["ct_estime"] = float(round(ct_estime_value, 3))
                else:
                    dossier["ct_estime"] = None
            else:
                dossier["ct_estime"] = None
            
            # Ajouter cout_total seulement si la colonne existe
            if cout_total_exists:
                cout_total_value = row.CoutTotal if hasattr(row, 'CoutTotal') else None
                if cout_total_value is not None:
                    dossier["cout_total"] = float(round(cout_total_value, 3))
                else:
                    dossier["cout_total"] = None
            else:
                dossier["cout_total"] = None
            
            # Ajouter ct_rel seulement si la colonne existe
            if ct_rel_exists:
                ct_rel_value = row.CtRel if hasattr(row, 'CtRel') else None
                if ct_rel_value is not None:
                    dossier["ct_rel"] = float(round(ct_rel_value, 3))
                    print(f"[DEBUG get_web_s_dos_encours] Dossier {dossier.get('numero', 'N/A')}: ct_rel récupéré = {dossier['ct_rel']}")
                else:
                    dossier["ct_rel"] = None
                    print(f"[DEBUG get_web_s_dos_encours] Dossier {dossier.get('numero', 'N/A')}: ct_rel est NULL dans la base")
            else:
                dossier["ct_rel"] = None
                print(f"[DEBUG get_web_s_dos_encours] Dossier {dossier.get('numero', 'N/A')}: Colonne CtRel n'existe pas")
            
            result.append(dossier)
        return result

def get_web_s_dos_encours_by_numero(numero):
    """
    Récupère un dossier en cours par son numéro
    """
    with get_db_cursor() as cursor:
        # Vérifier si la colonne Nom_GP_SERVICES existe
        try:
            cursor.execute("""
                SELECT COUNT(*) as col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' AND COLUMN_NAME = 'Nom_GP_SERVICES'
            """)
            avancement_exists = cursor.fetchone().col_exists > 0
        except Exception as e:
            print(f"[WARNING] Erreur lors de la vérification de la colonne Nom_GP_SERVICES: {e}")
            avancement_exists = False
        
        # Vérifier quelles colonnes existent
        try:
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                AND COLUMN_NAME IN ('Nom_GP_SERVICES', 'PrixVenteUnitaire', 'QteComm_COMMANDES', 'PrixVenteTotal', 'CTEstimé', 'CoutTotal', 'CtRel')
            """)
            existing_cols = {row.COLUMN_NAME for row in cursor.fetchall()}
            avancement_exists = 'Nom_GP_SERVICES' in existing_cols
            prix_exists = 'PrixVenteUnitaire' in existing_cols
            quantite_exists = 'QteComm_COMMANDES' in existing_cols
            prix_total_exists = 'PrixVenteTotal' in existing_cols
            ct_estime_exists = 'CTEstimé' in existing_cols
            cout_total_exists = 'CoutTotal' in existing_cols
            ct_rel_exists = 'CtRel' in existing_cols
        except Exception as e:
            print(f"[WARNING] Erreur lors de la vérification des colonnes: {e}")
            avancement_exists = False
            prix_exists = False
            quantite_exists = False
            prix_total_exists = False
            ct_estime_exists = False
            cout_total_exists = False
            ct_rel_exists = False
        
        # Construire la liste des colonnes dynamiquement
        columns_list = ['ID', 'Numero_COMMANDES', 'RaiSocTri_SOCIETES', 'Reference_COMMANDES', 'Coef_COMMANDES']
        if avancement_exists:
            columns_list.append('Nom_GP_SERVICES')
        if prix_exists:
            columns_list.append('PrixVenteUnitaire')
        if quantite_exists:
            columns_list.append('QteComm_COMMANDES')
        if prix_total_exists:
            columns_list.append('PrixVenteTotal')
        if ct_estime_exists:
            columns_list.append('CTEstimé')
        if cout_total_exists:
            columns_list.append('CoutTotal')
        if ct_rel_exists:
            columns_list.append('CtRel')
        columns_list.extend(['DateCreation', 'DateModification'])
        
        select_cols = ', '.join(columns_list)
        
        cursor.execute(f"""
            SELECT {select_cols}
            FROM WEB_S_DOS_ENCOURS
            WHERE LTRIM(RTRIM(Numero_COMMANDES)) = ?
        """, (numero.strip(),))
        
        row = cursor.fetchone()
        if row:
            # Convertir Decimal en float pour la sérialisation JSON
            marge_value = None
            if row.Coef_COMMANDES is not None:
                try:
                    marge_value = float(row.Coef_COMMANDES)
                except (ValueError, TypeError):
                    marge_value = None
            
            dossier = {
                "id": row.ID,
                "numero": row.Numero_COMMANDES,
                "client": row.RaiSocTri_SOCIETES,
                "reference": row.Reference_COMMANDES,
                "marge": marge_value,
                "date_creation": row.DateCreation.isoformat() if row.DateCreation else None,
                "date_modification": row.DateModification.isoformat() if row.DateModification else None
            }
            # Ajouter avancement seulement si la colonne existe
            if avancement_exists:
                dossier["avancement"] = row.Nom_GP_SERVICES if hasattr(row, 'Nom_GP_SERVICES') else None
            else:
                dossier["avancement"] = None
            
            # Ajouter prix_vente_unitaire seulement si la colonne existe
            if prix_exists:
                prix_value = row.PrixVenteUnitaire if hasattr(row, 'PrixVenteUnitaire') else None
                if prix_value is not None:
                    dossier["prix_vente_unitaire"] = float(round(prix_value, 3))
                else:
                    dossier["prix_vente_unitaire"] = None
            else:
                dossier["prix_vente_unitaire"] = None
            
            # Ajouter quantite seulement si la colonne existe
            if quantite_exists:
                quantite_value = row.QteComm_COMMANDES if hasattr(row, 'QteComm_COMMANDES') else None
                dossier["quantite"] = int(quantite_value) if quantite_value is not None else None
            else:
                dossier["quantite"] = None
            
            # Ajouter prix_vente_total seulement si la colonne existe
            if prix_total_exists:
                prix_total_value = row.PrixVenteTotal if hasattr(row, 'PrixVenteTotal') else None
                if prix_total_value is not None:
                    dossier["prix_vente_total"] = float(round(prix_total_value, 3))
                else:
                    dossier["prix_vente_total"] = None
            else:
                dossier["prix_vente_total"] = None
            
            # Ajouter ct_estime seulement si la colonne existe
            if ct_estime_exists:
                ct_estime_value = row.CTEstimé if hasattr(row, 'CTEstimé') else None
                if ct_estime_value is not None:
                    dossier["ct_estime"] = float(round(ct_estime_value, 3))
                else:
                    dossier["ct_estime"] = None
            else:
                dossier["ct_estime"] = None
            
            # Ajouter cout_total seulement si la colonne existe
            if cout_total_exists:
                cout_total_value = row.CoutTotal if hasattr(row, 'CoutTotal') else None
                if cout_total_value is not None:
                    dossier["cout_total"] = float(round(cout_total_value, 3))
                else:
                    dossier["cout_total"] = None
            else:
                dossier["cout_total"] = None
            
            # Ajouter ct_rel seulement si la colonne existe
            if ct_rel_exists:
                ct_rel_value = row.CtRel if hasattr(row, 'CtRel') else None
                if ct_rel_value is not None:
                    dossier["ct_rel"] = float(round(ct_rel_value, 3))
                else:
                    dossier["ct_rel"] = None
            else:
                dossier["ct_rel"] = None
            
            return dossier
        return None

def create_web_s_dos_encours(numero, client=None, reference=None, marge=None, avancement=None, quantite=None, prix_vente_total=None, ct_estime=None, cout_total=None, ct_rel=None):
    """
    Crée un nouveau dossier dans WEB_S_DOS_ENCOURS
    Les données peuvent être copiées depuis COMMANDES et SOCIETES si nécessaire
    quantite: QteComm_COMMANDES (INT) - valeur saisie par l'utilisateur
    prix_vente_total: PrixVenteTotal (DECIMAL) - valeur calculée dans l'application
    ct_estime: CTEstimé (DECIMAL) - valeur calculée dans l'application (Prix de Vente Total / (1 + Marge))
    cout_total: CoutTotal (DECIMAL) - valeur calculée dans l'application
    """
    with get_db_cursor() as cursor:
        # Récupérer les données depuis COMMANDES et SOCIETES (lecture seule)
        cursor.execute("""
            SELECT 
                C.Numero,
                S.RaiSocTri,
                C.Reference,
                C.QteComm,
                C.PrxVteReel,
                C.ID_DEVIS,
                DC.CoefInt AS MargeCoefInt
            FROM COMMANDES C
            LEFT JOIN SOCIETES S ON C.ID_SOCIETE = S.ID
            LEFT JOIN DEV_COUTS DC ON DC.ID_DEVIS = C.ID_DEVIS
            WHERE LTRIM(RTRIM(C.Numero)) = ?
        """, (numero.strip(),))
        
        row = cursor.fetchone()
        if row:
            # Utiliser les valeurs fournies en paramètre, ou celles de COMMANDES/DEV_COUTS si None
            client = client if client is not None else row.RaiSocTri
            reference = reference if reference is not None else row.Reference
            
            # Utiliser CoefInt depuis DEV_COUTS comme valeur par défaut pour la marge
            if marge is None:
                if hasattr(row, 'MargeCoefInt') and row.MargeCoefInt is not None:
                    try:
                        marge = round(float(row.MargeCoefInt), 3)
                    except (ValueError, TypeError):
                        marge = None
                else:
                    marge = None
            
            # Calculer PrixVenteUnitaire = PrxVteReel / QteComm (utiliser QteComm de COMMANDES pour le calcul du prix unitaire)
            prix_vente_unitaire = None
            if row.PrxVteReel is not None and row.QteComm is not None and row.QteComm > 0:
                prix_vente_unitaire = float(row.PrxVteReel) / float(row.QteComm)
                print(f"[DEBUG create_web_s_dos_encours] Prix unitaire calculé: {row.PrxVteReel} / {row.QteComm} = {prix_vente_unitaire}")
        
        # Vérifier quelles colonnes existent
        try:
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                AND COLUMN_NAME IN ('Nom_GP_SERVICES', 'PrixVenteUnitaire', 'QteComm_COMMANDES', 'PrixVenteTotal', 'CTEstimé', 'CoutTotal', 'CtRel')
            """)
            existing_cols = {row.COLUMN_NAME for row in cursor.fetchall()}
            avancement_exists = 'Nom_GP_SERVICES' in existing_cols
            prix_exists = 'PrixVenteUnitaire' in existing_cols
            quantite_exists = 'QteComm_COMMANDES' in existing_cols
            prix_total_exists = 'PrixVenteTotal' in existing_cols
            ct_estime_exists = 'CTEstimé' in existing_cols
            cout_total_exists = 'CoutTotal' in existing_cols
            ct_rel_exists = 'CtRel' in existing_cols
        except Exception as e:
            print(f"[WARNING] Erreur lors de la vérification des colonnes: {e}")
            avancement_exists = False
            prix_exists = False
            quantite_exists = False
            prix_total_exists = False
            ct_estime_exists = False
            cout_total_exists = False
            ct_rel_exists = False
        
        # Construire la requête INSERT dynamiquement selon les colonnes disponibles
        columns = ['Numero_COMMANDES', 'RaiSocTri_SOCIETES', 'Reference_COMMANDES', 'Coef_COMMANDES']
        values = [numero.strip(), client, reference, marge]
        placeholders = ['?'] * len(values)
        
        if avancement_exists:
            columns.append('Nom_GP_SERVICES')
            values.append(avancement)
            placeholders.append('?')
        
        if prix_exists:
            columns.append('PrixVenteUnitaire')
            values.append(prix_vente_unitaire)
            placeholders.append('?')
        
        if quantite_exists:
            columns.append('QteComm_COMMANDES')
            values.append(quantite)  # Valeur saisie par l'utilisateur
            placeholders.append('?')
        
        if prix_total_exists:
            columns.append('PrixVenteTotal')
            values.append(prix_vente_total)  # Valeur calculée dans l'application
            placeholders.append('?')
        
        if ct_estime_exists:
            columns.append('CTEstimé')
            values.append(ct_estime)  # Valeur calculée dans l'application
            placeholders.append('?')
        
        if cout_total_exists:
            columns.append('CoutTotal')
            values.append(cout_total)  # Valeur calculée dans l'application
            placeholders.append('?')
        
        if ct_rel_exists:
            columns.append('CtRel')
            # Enregistrer ct_rel même s'il est 0 (utiliser 0.0 au lieu de None)
            ct_rel_value = ct_rel if ct_rel is not None else 0.0
            values.append(ct_rel_value)  # Valeur calculée dans l'application: (CoutTotal / QteComm_COMMANDES) * Quantité
            placeholders.append('?')
            print("="*80)
            print(f"[CTREL DB DEBUG] Ajout de CtRel dans INSERT")
            print(f"[CTREL DB DEBUG] ct_rel_value = {ct_rel_value}")
            print(f"[CTREL DB DEBUG] ct_rel original = {ct_rel}")
            print(f"[CTREL DB DEBUG] Type ct_rel_value = {type(ct_rel_value)}")
            print("="*80)
            import sys
            sys.stdout.flush()
        else:
            print(f"[DEBUG create_web_s_dos_encours] [ATTENTION] Colonne CtRel n'existe pas, ne sera pas enregistre")
        
        print(f"[DEBUG create_web_s_dos_encours] Colonnes: {columns}")
        print(f"[DEBUG create_web_s_dos_encours] Valeurs: {values}")
        print(f"[DEBUG create_web_s_dos_encours] Types des valeurs: {[type(v).__name__ for v in values]}")
        
        try:
            cursor.execute(f"""
                INSERT INTO WEB_S_DOS_ENCOURS ({', '.join(columns)})
                OUTPUT INSERTED.ID
                VALUES ({', '.join(placeholders)})
            """, tuple(values))
            result = cursor.fetchone()
            dossier_id = result[0] if result else None
            
            # Vérifier que la valeur a bien été enregistrée
            if dossier_id and ct_rel_exists:
                cursor.execute("""
                    SELECT CtRel FROM WEB_S_DOS_ENCOURS WHERE ID = ?
                """, (dossier_id,))
                verification_row = cursor.fetchone()
                if verification_row:
                    ct_rel_saved = verification_row.CtRel if hasattr(verification_row, 'CtRel') else None
                    print("="*80)
                    print(f"[CTREL DB DEBUG] VERIFICATION APRES INSERT")
                    print(f"[CTREL DB DEBUG] CtRel enregistre dans la base = {ct_rel_saved}")
                    print("="*80)
                    import sys
                    sys.stdout.flush()
                else:
                    print(f"[DEBUG create_web_s_dos_encours] [ATTENTION] Impossible de verifier CtRel apres INSERT")
            
            cursor.connection.commit()
            return dossier_id
        except Exception as e:
            print(f"[DEBUG create_web_s_dos_encours] [ERREUR] ERREUR lors de l'INSERT: {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()
            raise

def update_web_s_dos_encours_avancement(id_dossier, avancement):
    """
    Met à jour uniquement l'avancement (Nom_GP_SERVICES) d'un dossier dans WEB_S_DOS_ENCOURS
    """
    with get_db_cursor() as cursor:
        # Vérifier si la colonne Nom_GP_SERVICES existe
        try:
            cursor.execute("""
                SELECT COUNT(*) as col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' AND COLUMN_NAME = 'Nom_GP_SERVICES'
            """)
            avancement_exists = cursor.fetchone().col_exists > 0
        except Exception as e:
            print(f"[WARNING] Erreur lors de la vérification de la colonne Nom_GP_SERVICES: {e}")
            return False
        
        if not avancement_exists:
            print("[WARNING] La colonne Nom_GP_SERVICES n'existe pas encore dans WEB_S_DOS_ENCOURS")
            return False
        
        cursor.execute("""
            UPDATE WEB_S_DOS_ENCOURS
            SET Nom_GP_SERVICES = ?,
                DateModification = GETDATE()
            WHERE ID = ?
        """, (avancement, id_dossier))
        cursor.connection.commit()
        return cursor.rowcount > 0

def update_web_s_dos_encours_quantite_prix_total(id_dossier, quantite, prix_vente_total, ct_estime=None, cout_total=None, ct_rel=None):
    """
    Met à jour la quantité (QteComm_COMMANDES), le prix de vente total (PrixVenteTotal), 
    le coût total estimé (CTEstimé), le coût total (CoutTotal) et le coût total réel (CtRel) d'un dossier dans WEB_S_DOS_ENCOURS
    quantite: QteComm_COMMANDES (INT) - valeur saisie par l'utilisateur
    prix_vente_total: PrixVenteTotal (DECIMAL) - valeur calculée dans l'application
    ct_estime: CTEstimé (DECIMAL) - valeur calculée dans l'application (Prix de Vente Total / (1 + Marge))
    cout_total: CoutTotal (DECIMAL) - valeur calculée dans l'application
    ct_rel: CtRel (DECIMAL) - valeur calculée dans l'application (CoutTotal / QteComm_COMMANDES) * Quantité
    """
    with get_db_cursor() as cursor:
        # Vérifier si les colonnes existent
        try:
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                AND COLUMN_NAME IN ('QteComm_COMMANDES', 'PrixVenteTotal', 'CTEstimé', 'CoutTotal', 'CtRel')
            """)
            existing_cols = {row.COLUMN_NAME for row in cursor.fetchall()}
            quantite_exists = 'QteComm_COMMANDES' in existing_cols
            prix_total_exists = 'PrixVenteTotal' in existing_cols
            ct_estime_exists = 'CTEstimé' in existing_cols
            cout_total_exists = 'CoutTotal' in existing_cols
            ct_rel_exists = 'CtRel' in existing_cols
        except Exception as e:
            print(f"[WARNING] Erreur lors de la vérification des colonnes: {e}")
            return False
        
        if not quantite_exists or not prix_total_exists:
            print("[WARNING] Les colonnes QteComm_COMMANDES ou PrixVenteTotal n'existent pas encore dans WEB_S_DOS_ENCOURS")
            return False
        
        # Construire la requête UPDATE dynamiquement
        update_parts = []
        values = []
        
        if quantite_exists:
            update_parts.append('QteComm_COMMANDES = ?')
            values.append(quantite)
        
        if prix_total_exists:
            update_parts.append('PrixVenteTotal = ?')
            values.append(prix_vente_total)
        
        if ct_estime_exists and ct_estime is not None:
            update_parts.append('CTEstimé = ?')
            values.append(ct_estime)
        
        if cout_total_exists and cout_total is not None:
            update_parts.append('CoutTotal = ?')
            values.append(cout_total)
        
        if ct_rel_exists and ct_rel is not None:
            update_parts.append('CtRel = ?')
            values.append(ct_rel)
        
        update_parts.append('DateModification = GETDATE()')
        values.append(id_dossier)
        
        cursor.execute(f"""
            UPDATE WEB_S_DOS_ENCOURS
            SET {', '.join(update_parts)}
            WHERE ID = ?
        """, tuple(values))
        cursor.connection.commit()
        return cursor.rowcount > 0

def get_services_by_numero_commande(numero_commande):
    """
    Récupère chaque occurrence individuelle des services liés à un dossier depuis GP_FICHES_TRAVAIL, GP_POSTES et GP_SERVICES
    avec leurs coûts CtPrevDev individuels (pas de regroupement)
    LECTURE SEULE - Ne modifie pas GP_FICHES_TRAVAIL, GP_POSTES ni GP_SERVICES
    Logique : COMMANDES → GP_FICHES_TRAVAIL → GP_POSTES → GP_SERVICES
    Retourne chaque ligne individuelle pour permettre de choisir quelles occurrences sont réalisées
    Ajoute également l'option "Matière première sortie" qui est toujours disponible
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                FT.ID AS ID_FICHE_TRAVAIL,
                S.Nom AS Nom_GP_SERVICES,
                FT.CtPrevDev AS CoutCtPrevDev,
                P.Nom AS Nom_Poste
            FROM GP_FICHES_TRAVAIL FT
            INNER JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            INNER JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            INNER JOIN GP_SERVICES S ON S.ID = P.ID_SERVICE
            WHERE LTRIM(RTRIM(C.Numero)) = ?
            AND S.Nom IS NOT NULL
            ORDER BY S.Nom, FT.ID
        """, (numero_commande.strip(),))
        
        rows = cursor.fetchall()
        print(f"[DEBUG get_services_by_numero_commande] Nombre de lignes retournées: {len(rows)} pour numéro: {numero_commande}")
        
        result = []
        for row in rows:
            if row.Nom_GP_SERVICES:
                # Debug: afficher les valeurs brutes
                print(f"[DEBUG] Service: {row.Nom_GP_SERVICES}, ID_FICHE: {row.ID_FICHE_TRAVAIL}, CtPrevDev brut: {row.CoutCtPrevDev}, Type: {type(row.CoutCtPrevDev)}")
                
                # Gérer les valeurs NULL et les convertir correctement
                if row.CoutCtPrevDev is None:
                    cout_value = 0.0
                else:
                    try:
                        cout_value = float(row.CoutCtPrevDev)
                    except (ValueError, TypeError):
                        print(f"[DEBUG] Erreur conversion pour {row.Nom_GP_SERVICES}: {row.CoutCtPrevDev}")
                        cout_value = 0.0
                
                print(f"[DEBUG] Service: {row.Nom_GP_SERVICES}, Cout converti: {cout_value}")
                
                # Créer un identifiant unique pour chaque occurrence
                service_id = f"{row.Nom_GP_SERVICES}_{row.ID_FICHE_TRAVAIL}"
                # S'assurer que toutes les valeurs sont sérialisables en JSON
                nom_poste_value = row.Nom_Poste if hasattr(row, 'Nom_Poste') and row.Nom_Poste is not None else None
                result.append({
                    "id": str(service_id),  # S'assurer que c'est une string
                    "id_fiche_travail": int(row.ID_FICHE_TRAVAIL) if row.ID_FICHE_TRAVAIL is not None else None,
                    "nom": str(row.Nom_GP_SERVICES),
                    "nom_poste": str(nom_poste_value) if nom_poste_value is not None else None,
                    "cout": float(round(cout_value, 3))  # S'assurer que c'est un float
                })
        
        # Ajouter l'option "Matière première sortie" qui est toujours disponible
        # Vérifier qu'elle n'existe pas déjà pour éviter les doublons
        matiere_premiere_sortie = "Matière première sortie"
        if not any(service["nom"] == matiere_premiere_sortie for service in result):
            result.append({
                "id": "matiere_premiere_sortie",
                "id_fiche_travail": None,
                "nom": str(matiere_premiere_sortie),
                "nom_poste": None,
                "cout": float(0.0)  # Sera rempli par AchatsMat dans le frontend
            })
        
        # Trier par nom puis par ID pour un affichage cohérent
        result.sort(key=lambda x: (x["nom"], x["id_fiche_travail"] or 0))
        
        return result

def delete_web_s_dos_encours(id_dossier):
    """
    Supprime un dossier de WEB_S_DOS_ENCOURS
    """
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM WEB_S_DOS_ENCOURS WHERE ID = ?", (id_dossier,))
        cursor.connection.commit()
        return cursor.rowcount > 0

def search_commandes_by_numero(search_numero):
    """
    Recherche dans COMMANDES par numéro (recherche de type "contient")
    LECTURE SEULE - Ne modifie pas COMMANDES
    Utilisé uniquement pour la sélection dans l'interface
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                C.Numero,
                S.RaiSocTri AS Client,
                C.Reference,
                C.QteComm,
                C.Coef
            FROM COMMANDES C
            LEFT JOIN SOCIETES S ON C.ID_SOCIETE = S.ID
            WHERE C.Numero LIKE ?
            ORDER BY C.Numero
        """, (f'%{search_numero}%',))
        
        result = []
        for row in cursor.fetchall():
            result.append({
                "numero": row.Numero,
                "client": row.Client,
                "reference": row.Reference,
                "quantite": row.QteComm,
                "marge": row.Coef
            })
        return result

def get_commande_by_numero(numero):
    """
    Récupère une commande par son numéro exact depuis COMMANDES
    La marge (CoefInt) est récupérée depuis DEV_COUTS au lieu de COMMANDES.Coef
    LECTURE SEULE - Ne modifie pas COMMANDES ni DEV_COUTS
    Liaison: DEV_COUTS.ID_DEVIS = COMMANDES.ID_DEVIS
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                C.Numero,
                S.RaiSocTri AS Client,
                C.Reference,
                C.QteComm,
                C.PrxVteReel,
                C.ID_DEVIS,
                DC.CoefInt AS MargeCoefInt
            FROM COMMANDES C
            LEFT JOIN SOCIETES S ON C.ID_SOCIETE = S.ID
            LEFT JOIN DEV_COUTS DC ON DC.ID_DEVIS = C.ID_DEVIS
            WHERE LTRIM(RTRIM(C.Numero)) = ?
        """, (numero.strip(),))
        
        row = cursor.fetchone()
        if row:
            # Calculer PrixVenteUnitaire = PrxVteReel / QteComm
            prix_vente_unitaire = None
            if row.PrxVteReel is not None and row.QteComm is not None and row.QteComm > 0:
                prix_vente_unitaire = round(float(row.PrxVteReel) / float(row.QteComm), 3)
            
            # Utiliser CoefInt depuis DEV_COUTS comme marge
            marge_value = None
            if hasattr(row, 'MargeCoefInt') and row.MargeCoefInt is not None:
                try:
                    marge_value = round(float(row.MargeCoefInt), 3)
                except (ValueError, TypeError):
                    marge_value = None
            
            return {
                "numero": row.Numero,
                "client": row.Client,
                "reference": row.Reference,
                "quantite": row.QteComm,
                "marge": marge_value,  # CoefInt depuis DEV_COUTS
                "prix_vente_unitaire": prix_vente_unitaire,
                "id_devis": row.ID_DEVIS if hasattr(row, 'ID_DEVIS') else None
            }
        return None

def get_achats_mat_by_numero_commande(numero_commande):
    """
    Récupère le coût matière première depuis GP_COUTS.CtPreDev pour un numéro de commande
    Liaison: GP_COUTS.ID_COMMANDE = COMMANDES.ID
    Condition: GP_COUTS.ID_CENTRE_COUT = 1
    LECTURE SEULE - Ne modifie pas GP_COUTS ni COMMANDES
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                GC.CtPreDev
            FROM COMMANDES C
            INNER JOIN GP_COUTS GC ON GC.ID_COMMANDE = C.ID
            WHERE LTRIM(RTRIM(C.Numero)) = ?
            AND GC.ID_CENTRE_COUT = 1
        """, (numero_commande.strip(),))
        
        row = cursor.fetchone()
        if row and row.CtPreDev is not None:
            # Convertir en float avec 3 décimales
            return round(float(row.CtPreDev), 3)
        return None

def get_achats_sstr_by_numero_commande(numero_commande):
    """
    Récupère AchatsSstr depuis DEV_COUTS pour un numéro de commande
    Liaison: DEV_COUTS.ID_DEVIS = COMMANDES.ID_DEVIS
    Condition: DEV_COUTS.ID_CENTRE_COUT = 5
    LECTURE SEULE - Ne modifie pas DEV_COUTS ni COMMANDES
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                DC.AchatsSstr
            FROM COMMANDES C
            INNER JOIN DEV_COUTS DC ON DC.ID_DEVIS = C.ID_DEVIS
            WHERE LTRIM(RTRIM(C.Numero)) = ?
            AND DC.ID_CENTRE_COUT = 5
        """, (numero_commande.strip(),))
        
        row = cursor.fetchone()
        if row and row.AchatsSstr is not None:
            # Convertir en float avec 3 décimales
            return round(float(row.AchatsSstr), 3)
        return None

def get_ct_prev_dev_sum_by_numero_commande(numero_commande):
    """
    Récupère la somme de CtPrevDev depuis GP_FICHES_TRAVAIL pour un numéro de commande
    Condition: GP_POSTES.ID_SERVICE = 1 ou 5
    Liaisons:
    - GP_POSTES.ID = GP_FICHES_TRAVAIL.ID_POSTE
    - GP_FICHES_TRAVAIL.ID_COMMANDE = COMMANDES.ID
    LECTURE SEULE - Ne modifie pas GP_FICHES_TRAVAIL, GP_POSTES ni COMMANDES
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                SUM(FT.CtPrevDev) AS SommeCtPrevDev
            FROM COMMANDES C
            INNER JOIN GP_FICHES_TRAVAIL FT ON FT.ID_COMMANDE = C.ID
            INNER JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            WHERE LTRIM(RTRIM(C.Numero)) = ?
            AND P.ID_SERVICE IN (1, 5)
            AND FT.CtPrevDev IS NOT NULL
        """, (numero_commande.strip(),))
        
        row = cursor.fetchone()
        if row and row.SommeCtPrevDev is not None:
            # Convertir en float avec 3 décimales
            return round(float(row.SommeCtPrevDev), 3)
        return None

def ajouter_contact(id_societe, nom, prenom, telephone, email, id_fonction=None, langue=1):
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO PERSONNES (Nom, Prenom, Telephone, Langue, Archive)
            VALUES (?, ?, ?, ?, 0)
        """, nom, prenom, telephone, langue)
        cursor.execute("SELECT SCOPE_IDENTITY()")
        id_personne = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO PERSONNES_MAIL (ID_PERSONNE, Mail, ParDefaut, RefuseEMailling)
            VALUES (?, ?, 1, 0)
        """, id_personne, email)

        cursor.execute("""
            INSERT INTO SOCIETES_PERSONNES (ID_SOCIETE, ID_PERSONNE, Principal, ApprobateurPage, EmetteurPage)
            VALUES (?, ?, 1, 0, 0)
        """, id_societe, id_personne)

        if id_fonction:
            cursor.execute("""
                INSERT INTO PERSONNES_FONCTIONS (ID_PERSONNE, ID_FONCTION, Ordre)
                VALUES (?, ?, 1)
            """, id_personne, id_fonction)

        cursor.connection.commit()
        return id_personne
# Fonction pour insérer un rapport dans VISITES_CLIENTS (type client retiré)
def enregistrer_visite(id_societe, raison_sociale, nature_visite, objet, origine, sujets, bilan, visiteur, cree_par):
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO VISITES_CLIENTS (
                ID_SOCIETE, RaisonSociale, DateVisite, NatureVisite,
                Objet, Origine, Sujets, Bilan, Visiteur, CreePar, CreeLe
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_societe,
            raison_sociale,
            datetime.today().date(),
            nature_visite,
            objet,
            origine,
            sujets,
            bilan,
            visiteur,
            cree_par,
            datetime.now()
        ))
        cursor.connection.commit()
        return True