#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PROJET 11 - Gestion de la table WEB_TRAITEMENTS
Module pour gérer les traitements avec données provenant de plusieurs tables
"""

from datetime import datetime
from contextlib import contextmanager
from decimal import Decimal
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

def get_all_traitements():
    """
    Récupère tous les traitements enregistrés dans WEB_TRAITEMENTS
    """
    with get_db_cursor() as cursor:
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
            FROM WEB_TRAITEMENTS
            ORDER BY DateCreation DESC
        """)
        
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
                "date_modification": row.DateModification.strftime('%Y-%m-%d') if row.DateModification else None
            })
        
        return traitements


def get_traitement_by_id(traitement_id):
    """
    Récupère un traitement spécifique par son ID.
    Gère les deux noms de colonne pour le temps prévu (TpsPrevDev_GP_FICHTRA_INT ou TpsPrevDev_GP_FICHES_OPERATIONS).
    """
    with get_db_cursor() as cursor:
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
                    DateModification
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
                            DateModification
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
            "date_modification": date_modification_str
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
                
                cursor.execute("""
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
                        TpsReel
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ))
                
                print("[DEBUG] INSERT réussi")
                cursor.commit()
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
    """
    Met à jour un traitement existant
    
    Args:
        traitement_id (int): ID du traitement à mettre à jour
        data (dict): Données à mettre à jour
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        with get_db_cursor() as cursor:
            from datetime import datetime

            def _safe_int(value):
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return 0

            # PdtC, PdtNNC, PdtANC : valeurs des champs de la fiche (si renseignés)
            pdt_c = _safe_int(data.get('pdt_c'))
            pdt_nnc = _safe_int(data.get('pdt_nnc'))
            pdt_anc = _safe_int(data.get('pdt_anc'))

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

            # TpsReel : calculer seulement si les deux dates sont fournies (fiche terminée).
            # Si dte_fin est None (fiche en cours, ex. fermeture par le X), garder DteFin = NULL et TpsReel = None.
            tps_reel = None
            if dte_deb and dte_fin:
                try:
                    duree_secondes = (dte_fin - dte_deb).total_seconds()
                    tps_reel = duree_secondes / 3600.0  # Convertir en heures
                    print(f"[DEBUG] TpsReel calculé: {tps_reel:.3f}h")
                except Exception as duree_error:
                    print(f"[WARN] Impossible de calculer TpsReel: {duree_error}")
                    tps_reel = None
            # Ne pas auto-remplir dte_fin quand le client envoie dte_fin null (fiche en cours)
            
            print(f"[DEBUG update_traitement] Mise à jour traitement {traitement_id}")
            print(f"[DEBUG update_traitement] Données: dte_deb={dte_deb}, dte_fin={dte_fin}, nb_op={nb_op}, pdt_c={pdt_c}, pdt_nnc={pdt_nnc}, pdt_anc={pdt_anc}")
            
            cursor.execute("""
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
                    TpsReel = ?,
                    DateModification = GETDATE()
                WHERE ID = ?
            """, (
                dte_deb,
                dte_fin,
                nb_op,
                pdt_c,
                pdt_nnc,
                pdt_anc,
                nb_pers,
                data.get('postes_reel'),
                tps_reel,
                traitement_id
            ))
            
            rows_affected = cursor.rowcount
            print(f"[DEBUG update_traitement] UPDATE exécuté, lignes affectées: {rows_affected}")
            
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


def delete_traitement(traitement_id):
    """
    Supprime un traitement
    
    Args:
        traitement_id (int): ID du traitement à supprimer
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM WEB_TRAITEMENTS WHERE ID = ?", (traitement_id,))
            cursor.connection.commit()
            print(f"[OK] Traitement {traitement_id} supprimé avec succès")
            return True
            
    except Exception as e:
        print(f"Erreur lors de la suppression du traitement: {e}")
        return False


# ============================================================================
# FONCTIONS DE STATISTIQUES
# ============================================================================

def get_statistiques_traitements():
    """
    Récupère les statistiques globales des traitements
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_traitements,
                SUM(NbOp) as total_operations,
                AVG(CAST(NbOp AS FLOAT)) as moyenne_operations,
                SUM(NbPers) as total_personnes,
                AVG(CAST(NbPers AS FLOAT)) as moyenne_personnes,
                COUNT(CASE WHEN DteFin IS NOT NULL THEN 1 END) as traitements_termines,
                COUNT(CASE WHEN DteFin IS NULL THEN 1 END) as traitements_en_cours
            FROM WEB_TRAITEMENTS
        """)
        
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


def get_traitements_par_service():
    """
    Récupère les statistiques par service
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                Nom_GP_SERVICES,
                COUNT(*) as nb_traitements,
                SUM(NbOp) as total_operations,
                AVG(CAST(NbOp AS FLOAT)) as moyenne_operations
            FROM WEB_TRAITEMENTS
            WHERE Nom_GP_SERVICES IS NOT NULL
            GROUP BY Nom_GP_SERVICES
            ORDER BY nb_traitements DESC
        """)
        
        services = []
        for row in cursor.fetchall():
            services.append({
                "service": row[0],
                "nb_traitements": row[1] or 0,
                "total_operations": row[2] or 0,
                "moyenne_operations": round(row[3] or 0, 3)
            })
        
        return services


def get_traitements_par_operateur():
    """
    Récupère les statistiques par opérateur
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                Nom_personel,
                Prenom_personel,
                COUNT(*) as nb_traitements,
                SUM(NbOp) as total_operations
            FROM WEB_TRAITEMENTS
            WHERE Nom_personel IS NOT NULL
            GROUP BY Nom_personel, Prenom_personel
            ORDER BY nb_traitements DESC
        """)
        
        operateurs = []
        for row in cursor.fetchall():
            operateurs.append({
                "operateur": f"{row[0] or ''} {row[1] or ''}".strip(),
                "nb_traitements": row[2] or 0,
                "total_operations": row[3] or 0
            })
        
        return operateurs

