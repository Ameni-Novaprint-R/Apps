#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Routes Flask pour le Projet 11 - Gestion des traitements (WEB_TRAITEMENTS)
"""

from flask import Blueprint, render_template, request, jsonify, Response, flash
from logic import projet11
from logic.auth import get_user_sections, has_section_access, has_action_access, is_super_user
from datetime import datetime

# Créer le blueprint
projet11_bp = Blueprint('projet11', __name__)


@projet11_bp.route('/projet11/test-connexion')
def test_connexion():
    """Route de test pour vérifier la connexion à la base de données"""
    try:
        from db import DB_CONFIG, get_db_cursor
        
        result = {
            "status": "success",
            "config": {
                "server": DB_CONFIG.get("SERVER"),
                "database": DB_CONFIG.get("DATABASE"),
                "auth_method": "Windows (Trusted_Connection)" if DB_CONFIG.get("Trusted_Connection") else "SQL Server"
            },
            "connection_test": None,
            "server_info": None,
            "error": None
        }
        
        # Tester la connexion
        with get_db_cursor() as cursor:
            # Test 1: Vérifier la connexion de base
            cursor.execute("SELECT 1 AS test")
            test_row = cursor.fetchone()
            result["connection_test"] = "OK" if test_row and test_row.test == 1 else "FAILED"
            
            # Test 2: Récupérer les informations du serveur
            cursor.execute("SELECT @@SERVERNAME AS ServerName, DB_NAME() AS DatabaseName, @@VERSION AS Version")
            server_row = cursor.fetchone()
            if server_row:
                result["server_info"] = {
                    "server_name": server_row.ServerName,
                    "database_name": server_row.DatabaseName,
                    "version": server_row.Version.split('\n')[0] if server_row.Version else "N/A"
                }
            
            # Test 3: Compter les tables disponibles
            cursor.execute("""
                SELECT COUNT(*) AS table_count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
            """)
            table_row = cursor.fetchone()
            result["table_count"] = table_row.table_count if table_row else 0
            
            # Test 4: Vérifier si les tables nécessaires existent
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME IN ('GP_FICHES_TRAVAIL', 'COMMANDES', 'personel', 'GP_POSTES', 'GP_SERVICES')
                AND TABLE_TYPE = 'BASE TABLE'
            """)
            required_tables = [row.TABLE_NAME for row in cursor.fetchall()]
            result["required_tables_found"] = required_tables
            result["required_tables_missing"] = [
                t for t in ['GP_FICHES_TRAVAIL', 'COMMANDES', 'personel', 'GP_POSTES', 'GP_SERVICES'] 
                if t not in required_tables
            ]
        
        return jsonify(result), 200
        
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        result = {
            "status": "error",
            "config": {
                "server": DB_CONFIG.get("SERVER") if 'DB_CONFIG' in locals() else "N/A",
                "database": DB_CONFIG.get("DATABASE") if 'DB_CONFIG' in locals() else "N/A",
                "driver": DB_CONFIG.get("DRIVER") if 'DB_CONFIG' in locals() else "N/A",
                "auth_method": "Windows (Trusted_Connection)" if DB_CONFIG.get("Trusted_Connection") == "yes" else "SQL Server" if 'DB_CONFIG' in locals() else "N/A"
            },
            "connection_test": "FAILED",
            "error": {
                "type": error_type,
                "message": error_msg
            },
            "troubleshooting": {
                "check_dns": "Vérifiez que SRV-KBA1 est résolu: ping SRV-KBA1 ou nslookup SRV-KBA1",
                "check_server": "Vérifiez que le serveur SQL Server est démarré et accessible",
                "check_auth": "Si Trusted_Connection ne fonctionne pas, essayez l'authentification SQL Server (UID/PWD)"
            }
        }
        
        import traceback
        result["traceback"] = traceback.format_exc()
        
        return jsonify(result), 500


@projet11_bp.route('/projet11')
def index():
    """Page principale du projet 11 - affiche uniquement les sections autorisées"""
    try:
        from db import get_db_cursor
        
        # Récupérer les sections autorisées pour le Projet 11 (NumProj = 11)
        authorized_sections = get_user_sections(11)
        
        # Créer un dictionnaire pour faciliter la vérification dans le template
        sections_dict = {s['id']: s['nom'] for s in authorized_sections}
        
        # Créer un set des IDs des sections autorisées pour vérification rapide
        authorized_section_ids = {s['id'] for s in authorized_sections}
        
        # Récupérer tous les IDs des sections du Projet 11 pour faire le mapping nom -> ID
        all_sections_map = {}  # {nom_lower: id}
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT WS.ID, WS.Nom
                    FROM WEB_SECTIONS WS
                    INNER JOIN WEB_PROJETS WP ON WP.ID = WS.ID_Proj
                    WHERE WP.NumProj = 11
                """)
                for row in cursor.fetchall():
                    all_sections_map[row.Nom.lower()] = row.ID
        except Exception as e:
            print(f"Erreur lors de la récupération des IDs de sections: {e}")
        
        # Déterminer quelles sections afficher basé sur les sections autorisées
        show_nouvelle_fiche = False
        show_liste_traitements = False
        show_statistiques = False
        
        if is_super_user():
            # Super-utilisateur : toutes les sections
            show_nouvelle_fiche = True
            show_liste_traitements = True
            show_statistiques = True
        else:
            # Vérifier chaque section autorisée par son nom pour déterminer quelle carte afficher
            for section in authorized_sections:
                section_nom_lower = section['nom'].lower()
                section_id = section['id']
                
                # Section "Nouvelle fiche de production" - vérifier par nom ET par ID si disponible
                if (section_id in authorized_section_ids and 
                    ('nouvelle' in section_nom_lower or 
                     ('fiche' in section_nom_lower and 'production' in section_nom_lower) or
                     section_id == all_sections_map.get('nouvelle fiche de production', -1))):
                    show_nouvelle_fiche = True
                
                # Section "Liste des Traitements"
                if (section_id in authorized_section_ids and 
                    (('liste' in section_nom_lower and 'traitements' in section_nom_lower) or
                     section_id == all_sections_map.get('liste des traitements', -1))):
                    show_liste_traitements = True
                
                # Section "Statistiques"
                if (section_id in authorized_section_ids and 
                    (('statistiques' in section_nom_lower or 'stats' in section_nom_lower) or
                     section_id == all_sections_map.get('statistiques', -1))):
                    show_statistiques = True
        
        return render_template('projet11.html',
                             authorized_sections=sections_dict,
                             show_nouvelle_fiche=show_nouvelle_fiche,
                             show_liste_traitements=show_liste_traitements,
                             show_statistiques=show_statistiques)
    except Exception as e:
        print(f"Erreur dans projet11.index: {e}")
        import traceback
        traceback.print_exc()
        # En cas d'erreur, afficher toutes les sections pour éviter de casser l'interface
        return render_template('projet11.html',
                             authorized_sections={},
                             show_nouvelle_fiche=True,
                             show_liste_traitements=True,
                             show_statistiques=True)


@projet11_bp.route('/projet11/traitements')
def liste_traitements():
    """Page de liste des traitements - vérifie l'accès à la section"""
    try:
        from db import get_db_cursor
        from logic.auth import has_section_access, is_super_user
        
        # Récupérer l'ID de la section "Liste des Traitements" du Projet 11
        section_id = None
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT WS.ID
                    FROM WEB_SECTIONS WS
                    INNER JOIN WEB_PROJETS WP ON WP.ID = WS.ID_Proj
                    WHERE WP.NumProj = 11
                    AND (WS.Nom LIKE '%liste%' OR WS.Nom LIKE '%traitements%')
                """)
                row = cursor.fetchone()
                if row:
                    section_id = row.ID
        except Exception as e:
            print(f"Erreur lors de la récupération de l'ID de section: {e}")
        
        # Vérifier l'accès à la section
        if section_id and not is_super_user() and not has_section_access(section_id):
            from flask import flash, redirect, url_for
            flash("Vous n'avez pas accès à cette section.", "error")
            return redirect(url_for('projet11.index'))
        
        traitements = projet11.get_all_traitements()
        from flask import make_response
        resp = make_response(render_template('projet11_liste.html', traitements=traitements))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp
    except Exception as e:
        print(f"Erreur dans liste_traitements: {e}")
        import traceback
        traceback.print_exc()
        from flask import flash, redirect, url_for
        flash(f"Erreur lors du chargement de la liste: {str(e)}", "error")
        return redirect(url_for('projet11.index'))


@projet11_bp.route('/projet11/nouveau')
def nouveau_traitement():
    """Page de création d'un nouveau traitement ou modification d'un traitement existant - vérifie l'accès à la section"""
    try:
        from flask import request
        from db import get_db_cursor
        from logic.auth import has_section_access, is_super_user
        
        # Vérifier si on est en mode embed
        is_embed = request.args.get('embed') == '1'
        
        # Récupérer l'ID du traitement à modifier (si présent)
        traitement_id = request.args.get('id') or request.args.get('traitement_id')
        traitement_data = None
        
        if traitement_id:
            try:
                traitement_id_int = int(traitement_id)
                traitement_data = projet11.get_traitement_by_id(traitement_id_int)
                if not traitement_data:
                    # Garder l'ID pour afficher un message clair côté client
                    print(f"[WARNING] Traitement ID {traitement_id_int} non trouvé (supprimé ou inexistant)")
            except (ValueError, TypeError) as e:
                traitement_id = None  # ID invalide, créer un nouveau
                print(f"[WARNING] ID de traitement invalide: {e}")
            except Exception as e_db:
                # Erreur BDD (ex: colonne renommée non déployée) -> garder l'ID, pas de données
                print(f"[WARNING] Erreur lors de la récupération du traitement {traitement_id}: {e_db}")
                import traceback
                traceback.print_exc()
                traitement_data = None
        
        # Récupérer l'ID de la section "Nouvelle fiche de production" du Projet 11
        section_id = None
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT WS.ID
                    FROM WEB_SECTIONS WS
                    INNER JOIN WEB_PROJETS WP ON WP.ID = WS.ID_Proj
                    WHERE WP.NumProj = 11
                    AND (WS.Nom LIKE '%nouvelle%' OR WS.Nom LIKE '%fiche%' OR WS.Nom LIKE '%production%')
                """)
                row = cursor.fetchone()
                if row:
                    section_id = row.ID
        except Exception as e:
            print(f"Erreur lors de la récupération de l'ID de section: {e}")
        
        # Vérifier l'accès à la section (seulement si section_id trouvé)
        if section_id:
            try:
                if not is_super_user() and not has_section_access(section_id):
                    from flask import flash, redirect, url_for
                    # En mode embed, afficher un message d'erreur dans la page plutôt que rediriger
                    if is_embed:
                        return render_template('projet11_nouveau.html', 
                                             commandes=[], 
                                             operateurs=[], 
                                             postes=[],
                                             traitement_data=None,
                                             traitement_id=None,
                                             error_message="Vous n'avez pas accès à cette section.")
                    flash("Vous n'avez pas accès à cette section.", "error")
                    return redirect(url_for('projet11.index'))
            except Exception as e:
                print(f"Erreur lors de la vérification d'accès à la section: {e}")
                import traceback
                traceback.print_exc()
                # En cas d'erreur de vérification, continuer quand même en mode embed pour éviter NS_BINDING_ABORTED
                if is_embed:
                    pass  # Continuer le chargement même si la vérification échoue
                else:
                    from flask import flash, redirect, url_for
                    flash("Erreur lors de la vérification des droits d'accès.", "error")
                    return redirect(url_for('projet11.index'))
        
        commandes = projet11.get_numeros_commandes_disponibles()
        operateurs = projet11.get_operateurs_disponibles()
        postes = projet11.get_postes_disponibles()
        
        # Debug: afficher les données passées au template
        traitement_introuvable_message = None
        if traitement_data:
            print(f"[DEBUG] Données du traitement passées au template: ID={traitement_data.get('id')}, Numéro commande={traitement_data.get('numero_commandes')}")
        elif traitement_id:
            print(f"[DEBUG] Aucune donnée de traitement passée au template (traitement_id={traitement_id} introuvable)")
            traitement_introuvable_message = f"Traitement (ID: {traitement_id}) introuvable. Il a peut-être été supprimé."
        else:
            print(f"[DEBUG] Aucune donnée de traitement passée au template (pas d'ID)")
        
        return render_template('projet11_nouveau.html', 
                             commandes=commandes, 
                             operateurs=operateurs, 
                             postes=postes,
                             traitement_data=traitement_data,
                             traitement_id=traitement_id,
                             traitement_introuvable_message=traitement_introuvable_message)
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"[ERREUR] Erreur dans nouveau_traitement: {error_type}: {error_msg}")
        import traceback
        traceback.print_exc()
        
        # Message d'erreur plus convivial pour l'utilisateur
        if "Impossible de se connecter" in error_msg or "SQL Server n'existe pas" in error_msg:
            user_message = "Erreur de connexion à la base de données. Le serveur SQL Server n'est pas accessible. Veuillez contacter l'administrateur système."
        else:
            user_message = f"Erreur lors du chargement des données: {error_msg}"
        
        # Retourner le template avec des listes vides pour éviter une erreur 500
        return render_template('projet11_nouveau.html', 
                             commandes=[], 
                             operateurs=[], 
                             postes=[],
                             error_message=user_message)


@projet11_bp.route('/projet11/fiche/<int:id_fiche>')
def details_fiche():
    """Récupère les détails d'une fiche de travail (AJAX)"""
    id_fiche = request.args.get('id_fiche', type=int)
    
    if not id_fiche:
        return jsonify({"error": "ID de fiche requis"}), 400
    
    operations = projet11.get_operations_by_fiche(id_fiche)
    traitement = projet11.get_traitement_by_fiche(id_fiche)
    
    return jsonify({
        "operations": operations,
        "traitement": traitement
    })


@projet11_bp.route('/projet11/api/traitements', methods=['GET'])
def api_get_traitements():
    """API pour récupérer tous les traitements"""
    traitements = projet11.get_all_traitements()
    return jsonify(traitements)


@projet11_bp.route('/projet11/api/traitements/<int:traitement_id>', methods=['GET'])
def api_get_traitement(traitement_id):
    """API pour récupérer un traitement spécifique"""
    traitement = projet11.get_traitement_by_id(traitement_id)
    
    if not traitement:
        return jsonify({"error": "Traitement non trouvé"}), 404
    
    return jsonify(traitement)


@projet11_bp.route('/projet11/api/traitements', methods=['POST'])
def api_create_traitement():
    """API pour créer un nouveau traitement"""
    try:
        data = request.get_json()
        print(f"[DEBUG API] Données reçues: {data}")

        def _safe_int(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        data['pdt_c'] = _safe_int(data.get('pdt_c'))
        data['pdt_nnc'] = _safe_int(data.get('pdt_nnc'))
        data['pdt_anc'] = _safe_int(data.get('pdt_anc'))
        data['nb_op'] = data['pdt_c'] + data['pdt_nnc'] + data['pdt_anc']

        if data['nb_op'] <= 0:
            return jsonify({"error": "Veuillez saisir au moins une quantité produite"}), 400
        data['nb_op'] = data['pdt_c'] + data['pdt_nnc'] + data['pdt_anc']
        
        # Valider les données requises
        # CORRECTION: Accepter id_fiche_travail = 0 pour les services non prévus
        if data.get('id_fiche_travail') is None:
            print("[ERREUR API] ID de fiche de travail manquant")
            return jsonify({"error": "ID de fiche de travail requis"}), 400
        
        # Pour les services non prévus (id_fiche_travail = 0), vérifier les données supplémentaires
        if data.get('id_fiche_travail') == 0:
            print("[INFO API] Service non prévu détecté")
            if not data.get('numero_commande') or not data.get('nom_service'):
                print(f"[ERREUR API] Données manquantes - numero_commande: {data.get('numero_commande')}, nom_service: {data.get('nom_service')}")
                return jsonify({"error": "Pour un service non prévu, le numéro de commande et le nom du service sont requis"}), 400
        
        if data['nb_op'] <= 0:
            print("[ERREUR API] Aucune quantité produite fournie")
            return jsonify({"error": "Veuillez saisir au moins une quantité produite"}), 400

        # Convertir les dates si nécessaire
        # CORRECTION: Gérer l'heure locale du navigateur (sans conversion UTC)
        if data.get('dte_deb'):
            try:
                # Format local: 2025-10-20T14:30:00 (sans Z, donc heure locale)
                if 'T' in data['dte_deb']:
                    # Enlever le Z s'il existe (ancien format)
                    date_str = data['dte_deb'].replace('Z', '')
                    # Parser le format ISO local
                    if '.' in date_str:
                        # Avec millisecondes: 2025-10-20T14:30:00.123
                        data['dte_deb'] = datetime.strptime(date_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    else:
                        # Sans millisecondes: 2025-10-20T14:30:00
                        data['dte_deb'] = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                else:
                    data['dte_deb'] = datetime.strptime(data['dte_deb'], '%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError) as e:
                print(f"Erreur parsing dte_deb: {e}")
        
        if data.get('dte_fin'):
            try:
                # Format local: 2025-10-20T14:30:00 (sans Z, donc heure locale)
                if 'T' in data['dte_fin']:
                    # Enlever le Z s'il existe (ancien format)
                    date_str = data['dte_fin'].replace('Z', '')
                    # Parser le format ISO local
                    if '.' in date_str:
                        # Avec millisecondes: 2025-10-20T14:30:00.123
                        data['dte_fin'] = datetime.strptime(date_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    else:
                        # Sans millisecondes: 2025-10-20T14:30:00
                        data['dte_fin'] = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                else:
                    data['dte_fin'] = datetime.strptime(data['dte_fin'], '%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError) as e:
                print(f"Erreur parsing dte_fin: {e}")
        
        # Créer le traitement
        print("[INFO API] Appel à create_traitement()")
        traitement_id = projet11.create_traitement(data)
        
        if traitement_id:
            print(f"[SUCCESS API] Traitement créé avec ID: {traitement_id}")
            return jsonify({
                "success": True,
                "id": traitement_id,
                "message": "Traitement créé avec succès"
            }), 201
        else:
            print("[ERREUR API] create_traitement() a retourné None")
            return jsonify({"error": "Erreur lors de la création du traitement - Vérifiez les logs serveur"}), 500
            
    except Exception as e:
        print(f"[EXCEPTION API] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500


@projet11_bp.route('/projet11/api/traitements/start', methods=['POST'])
def api_start_traitement():
    """API pour démarrer un traitement (chronomètre)"""
    try:
        data = request.get_json() or {}

        def _safe_int(value, default=0):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        # Normaliser les champs numériques
        data['pdt_c'] = _safe_int(data.get('pdt_c'))
        data['pdt_nnc'] = _safe_int(data.get('pdt_nnc'))
        data['pdt_anc'] = _safe_int(data.get('pdt_anc'))
        data['nb_pers'] = max(1, _safe_int(data.get('nb_pers'), 1))

        # Matricule opérateur (peut être None si non fourni)
        matricule = data.get('matricule_personel')
        try:
            data['matricule_personel'] = int(matricule) if matricule is not None else None
        except (TypeError, ValueError):
            data['matricule_personel'] = None

        # ID fiche travail (0 pour service non prévu)
        id_fiche_raw = data.get('id_fiche_travail')
        try:
            data['id_fiche_travail'] = int(id_fiche_raw) if id_fiche_raw is not None else None
        except (TypeError, ValueError):
            data['id_fiche_travail'] = None

        if data.get('id_fiche_travail') is None:
            return jsonify({"error": "ID de fiche de travail requis"}), 400

        # Services non prévus : s'assurer d'avoir les informations minimales
        if data['id_fiche_travail'] == 0:
            if not data.get('numero_commande') or not data.get('nom_service'):
                return jsonify({"error": "Pour un service non prévu, le numéro de commande et le nom du service sont requis"}), 400

        # Conversion de la date de début (locale)
        if data.get('dte_deb'):
            try:
                date_str = data['dte_deb'].replace('Z', '')
                if 'T' in date_str:
                    if '.' in date_str:
                        data['dte_deb'] = datetime.strptime(date_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    else:
                        data['dte_deb'] = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                else:
                    data['dte_deb'] = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError) as e:
                print(f"[ERREUR API START] Parse dte_deb: {e}")
                data['dte_deb'] = datetime.now()
        else:
            data['dte_deb'] = datetime.now()

        data['dte_fin'] = None  # Chronomètre en cours

        traitement_id = projet11.create_traitement(data)
        if traitement_id:
            return jsonify({
                "success": True,
                "id": traitement_id,
                "message": "Traitement démarré"
            }), 201

        return jsonify({"error": "Impossible de démarrer le traitement"}), 500

    except Exception as e:
        print(f"[EXCEPTION API START] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500


@projet11_bp.route('/projet11/api/traitements/<int:traitement_id>', methods=['PUT'])
def api_update_traitement(traitement_id):
    """API pour mettre à jour un traitement - Vérifie ID_Action 3 dans WEB_DROITS_ACCES"""
    from logic.auth import has_action_access, is_super_user
    
    # Vérifier si c'est une finalisation d'un traitement en cours (créé récemment sans dte_fin)
    # Dans ce cas, le droit SAISIE suffit (pas besoin de MODIFICATION)
    traitement_existant = projet11.get_traitement_by_id(traitement_id)
    is_finalisation = False
    
    if traitement_existant:
        # Si le traitement existe et n'a pas encore de date de fin, c'est une finalisation
        # d'un traitement qu'on vient de créer (via /start)
        if not traitement_existant.get('dte_fin'):
            is_finalisation = True
    
    # Vérification des droits :
    # - Si c'est une finalisation d'un traitement en cours : droit SAISIE suffit
    # - Si c'est une modification d'un traitement existant terminé : droit MODIFICATION requis
    if not is_super_user():
        if is_finalisation:
            # Pour finaliser un traitement qu'on vient de créer, le droit SAISIE suffit
            if not has_action_access(1):  # ID_Action 1 = SAISIE
                flash("Vous n'avez pas l'autorisation de saisir des traitements.", "error")
                return jsonify({"error": "Accès refusé : vous n'avez pas l'autorisation de saisir des traitements"}), 403
        else:
            # Pour modifier un traitement existant terminé, le droit MODIFICATION est requis
            if not has_action_access(3):  # ID_Action 3 = MODIFICATION
                flash("Vous n'avez pas l'autorisation de modifier les traitements.", "error")
                return jsonify({"error": "Accès refusé : vous n'avez pas l'autorisation de modifier les traitements"}), 403
    
    try:
        data = request.get_json()

        def _safe_int(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        data['pdt_c'] = _safe_int(data.get('pdt_c'))
        data['pdt_nnc'] = _safe_int(data.get('pdt_nnc'))
        data['pdt_anc'] = _safe_int(data.get('pdt_anc'))
        
        # Convertir les dates si nécessaire
        # CORRECTION: Gérer l'heure locale du navigateur (sans conversion UTC)
        if data.get('dte_deb'):
            try:
                if 'T' in data['dte_deb']:
                    date_str = data['dte_deb'].replace('Z', '')
                    if '.' in date_str:
                        data['dte_deb'] = datetime.strptime(date_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    else:
                        data['dte_deb'] = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                else:
                    data['dte_deb'] = datetime.strptime(data['dte_deb'], '%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError) as e:
                print(f"Erreur parsing dte_deb: {e}")
        
        if data.get('dte_fin'):
            try:
                if 'T' in data['dte_fin']:
                    date_str = data['dte_fin'].replace('Z', '')
                    if '.' in date_str:
                        data['dte_fin'] = datetime.strptime(date_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    else:
                        data['dte_fin'] = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                else:
                    data['dte_fin'] = datetime.strptime(data['dte_fin'], '%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError) as e:
                print(f"Erreur parsing dte_fin: {e}")
        
        # Mettre à jour le traitement
        print(f"[DEBUG API UPDATE] Mise à jour du traitement {traitement_id} avec données: {data}")
        success = projet11.update_traitement(traitement_id, data)
        
        if success:
            print(f"[SUCCESS API UPDATE] Traitement {traitement_id} mis à jour avec succès")
            return jsonify({
                "success": True,
                "message": "Traitement mis à jour avec succès"
            })
        else:
            print(f"[ERREUR API UPDATE] update_traitement() a retourné False pour traitement {traitement_id}")
            return jsonify({"error": "Erreur lors de la mise à jour du traitement - Vérifiez les logs serveur"}), 500
            
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"[EXCEPTION API UPDATE] {error_type}: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur lors de la mise à jour: {error_msg}"}), 500


@projet11_bp.route('/projet11/api/traitements/<int:traitement_id>', methods=['DELETE'])
def api_delete_traitement(traitement_id):
    """API pour supprimer un traitement - Vérifie ID_Action 4 dans WEB_DROITS_ACCES"""
    from logic.auth import has_action_access, is_super_user
    
    # Vérification stricte : l'ID_Action 4 (SUPPRESSION) doit être présent dans WEB_DROITS_ACCES
    if not is_super_user() and not has_action_access(4):
        flash("Vous n'avez pas l'autorisation de supprimer les traitements.", "error")
        return jsonify({"error": "Accès refusé : vous n'avez pas l'autorisation de supprimer les traitements"}), 403
    
    try:
        success = projet11.delete_traitement(traitement_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Traitement supprimé avec succès"
            })
        else:
            return jsonify({"error": "Erreur lors de la suppression"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@projet11_bp.route('/projet11/statistiques')
def statistiques():
    """Page de statistiques des traitements - vérifie l'accès à la section"""
    try:
        from db import get_db_cursor
        from logic.auth import has_section_access, is_super_user
        
        # Récupérer l'ID de la section "Statistiques" du Projet 11
        section_id = None
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT WS.ID
                    FROM WEB_SECTIONS WS
                    INNER JOIN WEB_PROJETS WP ON WP.ID = WS.ID_Proj
                    WHERE WP.NumProj = 11
                    AND (WS.Nom LIKE '%statistiques%' OR WS.Nom LIKE '%stats%')
                """)
                row = cursor.fetchone()
                if row:
                    section_id = row.ID
        except Exception as e:
            print(f"Erreur lors de la récupération de l'ID de section: {e}")
        
        # Vérifier l'accès à la section
        if section_id and not is_super_user() and not has_section_access(section_id):
            from flask import flash, redirect, url_for
            flash("Vous n'avez pas accès à cette section.", "error")
            return redirect(url_for('projet11.index'))
        
        stats = projet11.get_statistiques_traitements()
        stats_services = projet11.get_traitements_par_service()
        stats_operateurs = projet11.get_traitements_par_operateur()
        
        return render_template(
            'projet11_stats.html',
            stats=stats,
            stats_services=stats_services,
            stats_operateurs=stats_operateurs
        )
    except Exception as e:
        print(f"Erreur dans statistiques: {e}")
        import traceback
        traceback.print_exc()
        from flask import flash, redirect, url_for
        flash(f"Erreur lors du chargement des statistiques: {str(e)}", "error")
        return redirect(url_for('projet11.index'))


@projet11_bp.route('/projet11/api/statistiques', methods=['GET'])
def api_statistiques():
    """API pour récupérer les statistiques"""
    stats = projet11.get_statistiques_traitements()
    stats_services = projet11.get_traitements_par_service()
    stats_operateurs = projet11.get_traitements_par_operateur()
    
    return jsonify({
        "global": stats,
        "par_service": stats_services,
        "par_operateur": stats_operateurs
    })


@projet11_bp.route('/projet11/statistiques/export-excel')
def export_statistiques_excel():
    """Export des statistiques au format Excel - Vérifie ID_Action 6 dans WEB_DROITS_ACCES"""
    # Vérification stricte : l'ID_Action 6 (EXPORT_EXCEL) doit être présent dans WEB_DROITS_ACCES
    if not is_super_user() and not has_action_access(6):
        from flask import flash, redirect, url_for
        flash("Vous n'avez pas accès à cette action (Export Excel).", "error")
        return redirect(url_for('projet11.statistiques'))
    try:
        import pandas as pd
        from io import BytesIO
        
        stats = projet11.get_statistiques_traitements()
        stats_services = projet11.get_traitements_par_service()
        stats_operateurs = projet11.get_traitements_par_operateur()
        
        # Créer un fichier Excel avec plusieurs feuilles
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Feuille 1: Statistiques globales
            df_global = pd.DataFrame([{
                'Total traitements': stats.get('total_traitements', 0),
                'Traitements terminés': stats.get('traitements_termines', 0),
                'Traitements en cours': stats.get('traitements_en_cours', 0),
                'Total opérations': stats.get('total_operations', 0),
                'Moyenne opérations': stats.get('moyenne_operations', 0),
                'Total personnes': stats.get('total_personnes', 0),
                'Moyenne personnes': stats.get('moyenne_personnes', 0),
            }])
            df_global.to_excel(writer, sheet_name='Statistiques globales', index=False)
            
            # Feuille 2: Statistiques par service
            if stats_services:
                df_services = pd.DataFrame(stats_services)
                df_services.to_excel(writer, sheet_name='Par service', index=False)
            else:
                pd.DataFrame({'Service': [], 'Nb traitements': [], 'Total opérations': [], 'Moyenne opérations': []}).to_excel(
                    writer, sheet_name='Par service', index=False)
            
            # Feuille 3: Statistiques par opérateur
            if stats_operateurs:
                df_operateurs = pd.DataFrame(stats_operateurs)
                df_operateurs.to_excel(writer, sheet_name='Par opérateur', index=False)
            else:
                pd.DataFrame({'Opérateur': [], 'Nb traitements': [], 'Total opérations': []}).to_excel(
                    writer, sheet_name='Par opérateur', index=False)
        
        output.seek(0)
        filename = f"statistiques_projet11_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except ImportError:
        return jsonify({"error": "pandas et openpyxl sont requis pour l'export Excel"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@projet11_bp.route('/projet11/admin/renommer-colonne-tpsprevdev', methods=['GET', 'POST'])
def admin_renommer_colonne_tpsprevdev():
    """Route temporaire pour renommer la colonne TpsPrevDev_GP_FICHES_OPERATIONS en TpsPrevDev_GP_FICHTRA_INT"""
    from flask import jsonify
    from db import get_db_cursor
    
    try:
        with get_db_cursor() as cursor:
            # 1. Vérifier si la colonne existe avant de la renommer
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'WEB_TRAITEMENTS' 
                AND COLUMN_NAME = 'TpsPrevDev_GP_FICHES_OPERATIONS'
            """)
            
            colonne_existe = cursor.fetchone()
            
            if colonne_existe:
                # 2. Vérifier si la nouvelle colonne existe déjà
                cursor.execute("""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'WEB_TRAITEMENTS' 
                    AND COLUMN_NAME = 'TpsPrevDev_GP_FICHTRA_INT'
                """)
                
                nouvelle_colonne_existe = cursor.fetchone()
                
                if nouvelle_colonne_existe:
                    return jsonify({
                        'success': False,
                        'message': 'La colonne TpsPrevDev_GP_FICHTRA_INT existe déjà. Le renommage a peut-être déjà été effectué.',
                        'action': 'none'
                    })
                
                # 3. Renommer la colonne
                cursor.execute("""
                    EXEC sp_rename 
                        'WEB_TRAITEMENTS.TpsPrevDev_GP_FICHES_OPERATIONS', 
                        'TpsPrevDev_GP_FICHTRA_INT', 
                        'COLUMN'
                """)
                cursor.commit()
                
                # 4. Vérifier la structure après modification
                cursor.execute("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'WEB_TRAITEMENTS'
                    AND COLUMN_NAME LIKE '%TpsPrevDev%'
                    ORDER BY COLUMN_NAME
                """)
                
                colonnes = cursor.fetchall()
                colonnes_list = [{'name': c.COLUMN_NAME, 'type': c.DATA_TYPE, 'nullable': c.IS_NULLABLE} for c in colonnes]
                
                # 5. Compter les enregistrements
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(TpsPrevDev_GP_FICHTRA_INT) as avec_valeur
                    FROM WEB_TRAITEMENTS
                """)
                
                stats = cursor.fetchone()
                
                return jsonify({
                    'success': True,
                    'message': 'Colonne renommée avec succès de TpsPrevDev_GP_FICHES_OPERATIONS en TpsPrevDev_GP_FICHTRA_INT',
                    'action': 'renamed',
                    'colonnes': colonnes_list,
                    'statistiques': {
                        'total': stats.total,
                        'avec_valeur': stats.avec_valeur
                    }
                })
            else:
                # Vérifier si la nouvelle colonne existe déjà
                cursor.execute("""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'WEB_TRAITEMENTS' 
                    AND COLUMN_NAME = 'TpsPrevDev_GP_FICHTRA_INT'
                """)
                
                nouvelle_colonne_existe = cursor.fetchone()
                
                if nouvelle_colonne_existe:
                    return jsonify({
                        'success': True,
                        'message': 'La colonne TpsPrevDev_GP_FICHTRA_INT existe déjà. Le renommage a déjà été effectué.',
                        'action': 'already_exists'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Aucune des deux colonnes n\'existe. Vérifiez la structure de la table WEB_TRAITEMENTS.',
                        'action': 'none_found'
                    })
                    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return jsonify({
            'success': False,
            'message': f'Erreur lors du renommage: {str(e)}',
            'error': error_trace
        }), 500


@projet11_bp.route('/projet11/statistiques/export-pdf')
def export_statistiques_pdf():
    """Export des statistiques au format PDF - Vérifie ID_Action 7 dans WEB_DROITS_ACCES"""
    # Vérification stricte : l'ID_Action 7 (EXPORT_PDF) doit être présent dans WEB_DROITS_ACCES
    if not is_super_user() and not has_action_access(7):
        from flask import flash, redirect, url_for
        flash("Vous n'avez pas accès à cette action (Export PDF).", "error")
        return redirect(url_for('projet11.statistiques'))
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from io import BytesIO
        
        stats = projet11.get_statistiques_traitements()
        stats_services = projet11.get_traitements_par_service()
        stats_operateurs = projet11.get_traitements_par_operateur()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=1  # Centré
        )
        story.append(Paragraph("Statistiques - Projet 11", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Statistiques globales
        story.append(Paragraph("Statistiques Globales", styles['Heading2']))
        data_global = [
            ['Indicateur', 'Valeur'],
            ['Total traitements', str(stats.get('total_traitements', 0))],
            ['Traitements terminés', str(stats.get('traitements_termines', 0))],
            ['Traitements en cours', str(stats.get('traitements_en_cours', 0))],
            ['Total opérations', str(stats.get('total_operations', 0))],
            ['Moyenne opérations', f"{stats.get('moyenne_operations', 0):.3f}"],
            ['Total personnes', str(stats.get('total_personnes', 0))],
            ['Moyenne personnes', f"{stats.get('moyenne_personnes', 0):.3f}"],
        ]
        table_global = Table(data_global, colWidths=[3*inch, 2*inch])
        table_global.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table_global)
        story.append(Spacer(1, 0.3*inch))
        
        # Statistiques par service
        if stats_services:
            story.append(Paragraph("Statistiques par Service", styles['Heading2']))
            data_services = [['Service', 'Nb traitements', 'Total opérations', 'Moyenne opérations']]
            for s in stats_services:
                data_services.append([
                    s.get('service', ''),
                    str(s.get('nb_traitements', 0)),
                    str(s.get('total_operations', 0)),
                    f"{s.get('moyenne_operations', 0):.3f}"
                ])
            table_services = Table(data_services, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            table_services.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table_services)
            story.append(Spacer(1, 0.3*inch))
        
        # Statistiques par opérateur
        if stats_operateurs:
            story.append(Paragraph("Statistiques par Opérateur", styles['Heading2']))
            data_operateurs = [['Opérateur', 'Nb traitements', 'Total opérations']]
            for o in stats_operateurs:
                data_operateurs.append([
                    o.get('operateur', 'Non renseigné'),
                    str(o.get('nb_traitements', 0)),
                    str(o.get('total_operations', 0))
                ])
            table_operateurs = Table(data_operateurs, colWidths=[3*inch, 2*inch, 2*inch])
            table_operateurs.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table_operateurs)
        
        # Date de génération
        story.append(Spacer(1, 0.3*inch))
        date_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        story.append(Paragraph(f"<i>Généré le {date_str}</i>", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        filename = f"statistiques_projet11_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except ImportError:
        return jsonify({"error": "reportlab est requis pour l'export PDF"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@projet11_bp.route('/projet11/api/fiches-disponibles', methods=['GET'])
def api_fiches_disponibles():
    """API pour récupérer les fiches de travail disponibles"""
    fiches = projet11.get_fiches_travail_disponibles()
    return jsonify(fiches)


@projet11_bp.route('/projet11/api/operateurs', methods=['GET'])
def api_operateurs():
    """API pour récupérer la liste des opérateurs"""
    operateurs = projet11.get_operateurs_disponibles()
    return jsonify(operateurs)


@projet11_bp.route('/projet11/api/numeros-commandes', methods=['GET'])
def api_numeros_commandes():
    """API pour récupérer les numéros de commandes disponibles"""
    commandes = projet11.get_numeros_commandes_disponibles()
    return jsonify(commandes)


@projet11_bp.route('/projet11/api/fiches-by-commande/<numero_commande>', methods=['GET'])
def api_fiches_by_commande(numero_commande):
    """API pour récupérer les fiches de travail d'une commande spécifique"""
    fiches = projet11.get_fiches_by_numero_commande(numero_commande)
    return jsonify(fiches)


@projet11_bp.route('/projet11/api/postes', methods=['GET'])
def api_postes():
    """API pour récupérer la liste des postes/machines disponibles"""
    postes = projet11.get_postes_disponibles()
    return jsonify(postes)


@projet11_bp.route('/projet11/api/traitements-fiche/<int:id_fiche_travail>', methods=['GET'])
def api_traitements_fiche(id_fiche_travail):
    """API pour récupérer les traitements existants d'une fiche de travail"""
    traitements = projet11.get_traitements_existants_fiche(id_fiche_travail)
    return jsonify(traitements)


@projet11_bp.route('/projet11/api/services-prevus/<numero_commande>', methods=['GET'])
def api_services_prevus(numero_commande):
    """API pour récupérer les services prévus pour une commande"""
    services = projet11.get_services_prevus_by_commande(numero_commande)
    return jsonify(services)


@projet11_bp.route('/projet11/api/postes-prevus/<numero_commande>/<nom_service>', methods=['GET'])
def api_postes_prevus(numero_commande, nom_service):
    """API pour récupérer les postes prévus pour une commande et un service"""
    postes = projet11.get_postes_prevus_by_commande_service(numero_commande, nom_service)
    return jsonify(postes)


@projet11_bp.route('/projet11/api/traitements-service/<numero_commande>/<nom_service>', methods=['GET'])
def api_traitements_service(numero_commande, nom_service):
    """API pour récupérer les traitements existants pour une commande et un service"""
    traitements = projet11.get_traitements_existants_service(numero_commande, nom_service)
    return jsonify(traitements)


@projet11_bp.route('/projet11/api/services-tous', methods=['GET'])
def api_services_tous():
    """API pour récupérer TOUS les services disponibles depuis GP_SERVICES"""
    services = projet11.get_tous_services()
    return jsonify(services)


@projet11_bp.route('/projet11/api/postes-tous-service/<nom_service>', methods=['GET'])
def api_postes_tous_service(nom_service):
    """API pour récupérer TOUS les postes d'un service spécifique"""
    postes = projet11.get_postes_by_service(nom_service)
    return jsonify(postes)


@projet11_bp.route('/projet11/traitements/export-excel')
def export_traitements_excel():
    """Export du tableau des traitements au format Excel - Vérifie ID_Action 6 dans WEB_DROITS_ACCES"""
    # Vérification stricte : l'ID_Action 6 (EXPORT_EXCEL) doit être présent dans WEB_DROITS_ACCES
    if not is_super_user() and not has_action_access(6):
        from flask import flash, redirect, url_for
        flash("Vous n'avez pas accès à cette action (Export Excel).", "error")
        return redirect(url_for('projet11.liste_traitements'))
    try:
        import pandas as pd
        from io import BytesIO
        
        # Récupérer tous les traitements
        traitements = projet11.get_all_traitements()
        
        if not traitements:
            return jsonify({"error": "Aucun traitement à exporter"}), 404
        
        # Créer un DataFrame avec toutes les colonnes du tableau
        data = []
        for t in traitements:
            data.append({
                'ID': t.get('id', ''),
                'Date Début': t.get('dte_deb', ''),
                'Date Fin': t.get('dte_fin', ''),
                'N° Commande': t.get('numero_commande', ''),
                'Référence': t.get('reference', ''),
                'Client': t.get('client', ''),
                'Service': t.get('service', ''),
                'Poste Prévu': t.get('poste', ''),
                'Machine Réelle': t.get('postes_reel', ''),
                'Opérateur': t.get('operateur', ''),
                'Nb Op.': t.get('nb_op', 0),
                'Nb Pers.': t.get('nb_pers', 0),
                'Tps Prévu': f"{t.get('tps_prev_dev', 0):.2f}" if t.get('tps_prev_dev') else '',
                'Tps Réel': f"{t.get('tps_reel', 0):.2f}" if t.get('tps_reel') else '',
                'Écart': f"{t.get('ecart_temps', 0):.2f}" if t.get('ecart_temps') is not None else '',
                'Pdt C': t.get('pdt_c', 0),
                'Pdt NNC': t.get('pdt_nnc', 0),
                'Pdt ANC': t.get('pdt_anc', 0),
                'Statut': 'Terminé' if t.get('dte_fin') else 'En cours',
                'Date Création': t.get('date_creation', ''),
                'Date Modification': t.get('date_modification', '')
            })
        
        df = pd.DataFrame(data)
        
        # Créer le fichier Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Traitements', index=False)
            
            # Ajuster la largeur des colonnes
            worksheet = writer.sheets['Traitements']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.column_dimensions[chr(65 + idx) if idx < 26 else 'A' + chr(65 + idx - 26)].width = min(max_length + 2, 50)
        
        output.seek(0)
        filename = f"traitements_projet11_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except ImportError:
        return jsonify({"error": "pandas et openpyxl sont requis pour l'export Excel"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@projet11_bp.route('/projet11/traitements/export-pdf')
def export_traitements_pdf():
    """Export du tableau des traitements au format PDF - Vérifie ID_Action 7 dans WEB_DROITS_ACCES"""
    # Vérification stricte : l'ID_Action 7 (EXPORT_PDF) doit être présent dans WEB_DROITS_ACCES
    if not is_super_user() and not has_action_access(7):
        from flask import flash, redirect, url_for
        flash("Vous n'avez pas accès à cette action (Export PDF).", "error")
        return redirect(url_for('projet11.liste_traitements'))
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from io import BytesIO
        import textwrap
        
        # Récupérer tous les traitements
        traitements = projet11.get_all_traitements()
        
        if not traitements:
            return jsonify({"error": "Aucun traitement à exporter"}), 404
        
        buffer = BytesIO()
        # Utiliser le format paysage pour avoir plus d'espace horizontal
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        story = []
        styles = getSampleStyleSheet()
        
        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=20,
            alignment=1  # Centré
        )
        story.append(Paragraph("Liste des Traitements - Projet 11", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Style pour les cellules normales
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=7,
            leading=8,
            alignment=0,  # LEFT
        )
        
        # Style spécifique pour la colonne Référence avec retour à la ligne forcé
        # Largeur de la colonne Référence (sera utilisée pour calculer le nombre de caractères par ligne)
        reference_col_width_pts = 1.5 * inch  # Largeur en points (1 inch = 72 points) - ajustée à 1.5 inch pour tenir dans la page
        reference_style = ParagraphStyle(
            'ReferenceStyle',
            parent=styles['Normal'],
            fontSize=7,
            leading=8,
            alignment=0,  # LEFT
            wordWrap='LTR',  # Retour à la ligne pour texte latin
            leftIndent=0,
            rightIndent=0
        )
        
        # Fonction pour créer un Paragraph avec retour à la ligne automatique pour la référence
        def create_reference_paragraph(text, style, max_width_pts):
            """Crée un Paragraph avec retour à la ligne automatique basé sur la largeur"""
            if not text:
                return Paragraph('', style)
            # Échapper les caractères HTML
            text_escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Estimer le nombre de caractères par ligne de manière plus conservatrice
            # Avec padding de 8 points de chaque côté, largeur disponible = max_width_pts - 16
            # Pour fontSize 7, on utilise ~5 pts par caractère (plus conservateur pour éviter le débordement)
            available_width = max_width_pts - 16  # Soustraire les paddings
            chars_per_line = int(available_width / 5.0)  # ~5 pts par caractère pour fontSize 7 (conservateur)
            chars_per_line = max(chars_per_line, 15)  # Minimum 15 caractères par ligne pour éviter trop de lignes
            chars_per_line = min(chars_per_line, 40)  # Maximum 40 caractères pour éviter les lignes trop longues
            # Utiliser textwrap pour diviser le texte en lignes
            # break_long_words=True force la division même des mots très longs
            wrapped_lines = textwrap.wrap(text, width=chars_per_line, break_long_words=True, break_on_hyphens=True)
            # Joindre les lignes avec <br/> pour forcer le retour à la ligne dans le PDF
            if wrapped_lines:
                text_with_breaks = '<br/>'.join(wrapped_lines)
            else:
                text_with_breaks = text_escaped
            return Paragraph(text_with_breaks, style)
        
        # Style pour les en-têtes
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            alignment=0,
            textColor=colors.whitesmoke
        )
        
        # Préparer les données du tableau (colonnes principales)
        # Utiliser Paragraph pour permettre le retour à la ligne dans les cellules
        data = [[
            Paragraph('ID', header_style),
            Paragraph('Date Début', header_style),
            Paragraph('Date Fin', header_style),
            Paragraph('N° Commande', header_style),
            Paragraph('Référence', header_style),
            Paragraph('Client', header_style),
            Paragraph('Service', header_style),
            Paragraph('Poste', header_style),
            Paragraph('Opérateur', header_style),
            Paragraph('Nb Op.', header_style),
            Paragraph('Nb Pers.', header_style),
            Paragraph('Tps Prévu', header_style),
            Paragraph('Tps Réel', header_style),
            Paragraph('Statut', header_style)
        ]]
        
        for t in traitements:
            dte_deb = t.get('dte_deb', '')[:16] if t.get('dte_deb') else ''
            dte_fin = t.get('dte_fin', '')[:16] if t.get('dte_fin') else ''
            tps_prev = f"{t.get('tps_prev_dev', 0):.2f}" if t.get('tps_prev_dev') else ''
            tps_reel = f"{t.get('tps_reel', 0):.2f}" if t.get('tps_reel') else ''
            statut = 'Terminé' if t.get('dte_fin') else 'En cours'
            
            # Pour la colonne Référence, utiliser la fonction qui force le retour à la ligne
            reference_text = t.get('reference', '') or ''
            reference_para = create_reference_paragraph(reference_text, reference_style, reference_col_width_pts)
            # Modification pour forcer le rechargement Flask
            
            data.append([
                Paragraph(str(t.get('id', '')), cell_style),
                Paragraph(dte_deb, cell_style),
                Paragraph(dte_fin, cell_style),
                Paragraph(t.get('numero_commande', ''), cell_style),
                reference_para,  # Référence avec retour à la ligne automatique
                Paragraph(t.get('client', '')[:30], cell_style),  # Limiter un peu pour équilibrer
                Paragraph(t.get('service', '')[:20], cell_style),
                Paragraph(t.get('poste', '')[:20], cell_style),
                Paragraph(t.get('operateur', '')[:25], cell_style),
                Paragraph(str(t.get('nb_op', 0)), cell_style),
                Paragraph(str(t.get('nb_pers', 0)), cell_style),
                Paragraph(tps_prev, cell_style),
                Paragraph(tps_reel, cell_style),
                Paragraph(statut, cell_style)
            ])
        
        # Créer le tableau avec largeurs ajustées
        # Total doit être <= 11.69 inch (largeur page paysage A4)
        # ID : 0.9 inch (suffisant pour afficher les IDs)
        # Statut : 1.1 inch (suffisant pour "Terminé" ou "En cours")
        # Référence : 1.5 inch (fonctionne bien avec retour à la ligne)
        # Total: 0.9+0.9+0.9+0.8+1.5+0.9+0.8+0.7+0.9+0.5+0.5+0.6+0.6+1.1 = 11.7 inch
        table = Table(data, colWidths=[
            0.9*inch,  # ID - ajusté pour tenir dans la page
            0.9*inch,  # Date Début - réduit
            0.9*inch,  # Date Fin - réduit
            0.8*inch,  # N° Commande - réduit
            1.5*inch,  # Référence - réduit mais toujours fonctionnel avec retour à la ligne
            0.9*inch,  # Client - réduit
            0.8*inch,  # Service - réduit
            0.7*inch,  # Poste - réduit
            0.9*inch,  # Opérateur - réduit
            0.5*inch,  # Nb Op.
            0.5*inch,  # Nb Pers.
            0.6*inch,  # Tps Prévu - réduit
            0.6*inch,  # Tps Réel - réduit
            1.1*inch   # Statut - ajusté pour tenir dans la page
        ])
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (9, 0), (10, -1), 'CENTER'),  # Nb Op., Nb Pers.
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),  # Réduit le padding gauche pour plus d'espace
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),  # Réduit le padding droit pour plus d'espace
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # TOP pour permettre l'expansion verticale avec retour à la ligne
        ]))
        
        story.append(table)
        
        # Date de génération
        story.append(Spacer(1, 0.2*inch))
        date_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        story.append(Paragraph(f"<i>Généré le {date_str} - {len(traitements)} traitement(s)</i>", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        filename = f"traitements_projet11_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except ImportError:
        return jsonify({"error": "reportlab est requis pour l'export PDF"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@projet11_bp.route('/projet11/admin/corriger-ids-specifiques')
def corriger_ids_specifiques():
    """Route pour corriger les IDs spécifiques dans WEB_DROITS_ACCES"""
    from db import get_db_cursor
    
    try:
        with get_db_cursor() as cursor:
            corrections = [
                (6, 2, "EXPORT_EXCEL"),
                (7, 2, "EXPORT_PDF"),
                (8, 3, "CONSULTATION")
            ]
            
            results = []
            etat_final = []
            
            # Vérifier l'état actuel
            for id_record, id_section, action in corrections:
                cursor.execute("SELECT ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                row = cursor.fetchone()
                if row:
                    results.append(f"ID {id_record} avant: ID_Section={row.ID_Section}, Action={row.Action}, archive={row.archive}")
                else:
                    results.append(f"ID {id_record} n'existe pas")
            
            # Effectuer les corrections
            for id_record, id_section, action in corrections:
                cursor.execute("SELECT ID FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                if cursor.fetchone():
                    cursor.execute("""
                        UPDATE dbo.WEB_DROITS_ACCES 
                        SET ID_Section = ?, Action = ?, archive = 0
                        WHERE ID = ?
                    """, (id_section, action, id_record))
                    if cursor.rowcount > 0:
                        results.append(f"✓ ID {id_record} corrigé: ID_Section={id_section}, Action={action}")
                else:
                    cursor.execute("""
                        INSERT INTO dbo.WEB_DROITS_ACCES (ID, ID_Section, Action, archive)
                        VALUES (?, ?, ?, 0)
                    """, (id_record, id_section, action))
                    results.append(f"+ ID {id_record} créé: ID_Section={id_section}, Action={action}")
            
            cursor.connection.commit()
            
            # Vérifier l'état final
            for id_record, id_section, action in corrections:
                cursor.execute("SELECT ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                row = cursor.fetchone()
                if row:
                    etat_final.append({
                        "id": id_record,
                        "id_section": row.ID_Section,
                        "action": row.Action,
                        "archive": row.archive
                    })
            
            return jsonify({
                "success": True,
                "results": results,
                "etat_final": etat_final,
                "message": "Corrections appliquées avec succès"
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet11_bp.route('/projet11/admin/modifier-actions-droits')
def modifier_actions_droits():
    """Route pour corriger les actions dans WEB_DROITS_ACCES selon la configuration attendue"""
    from db import get_db_cursor
    
    try:
        with get_db_cursor() as cursor:
            # Récupérer l'ID du Projet 11
            cursor.execute("SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = 11")
            proj_row = cursor.fetchone()
            if not proj_row:
                return jsonify({"success": False, "error": "Projet 11 introuvable"}), 404
            
            id_proj = proj_row.ID
            
            # Configuration attendue
            CONFIG_ATTENDUE = {
                "Nouvelle fiche de production": ["SAISIE"],
                "Liste des Traitements": ["CONSULTATION", "MODIFICATION", "SUPPRESSION", "SAISIE", "EXPORT_EXCEL", "EXPORT_PDF"],
                "Statistiques": ["CONSULTATION"]
            }
            
            results = []
            
            # Pour chaque section
            for nom_section, actions_attendues in CONFIG_ATTENDUE.items():
                cursor.execute("SELECT ID FROM dbo.WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?", (id_proj, nom_section))
                section_row = cursor.fetchone()
                
                if not section_row:
                    results.append(f"Section '{nom_section}' introuvable")
                    continue
                
                id_section = section_row.ID
                
                # Récupérer les actions actuelles
                cursor.execute("SELECT Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID_Section = ?", (id_section,))
                actions_actuelles = {row.Action: row.archive for row in cursor.fetchall()}
                
                # Archiver les actions non attendues
                for action_actuelle, archive_status in actions_actuelles.items():
                    if action_actuelle not in actions_attendues and archive_status == 0:
                        cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET archive = 1 WHERE ID_Section = ? AND Action = ? AND archive = 0", 
                                     (id_section, action_actuelle))
                        if cursor.rowcount > 0:
                            results.append(f"Archivé: {nom_section} | {action_actuelle}")
                
                # Ajouter/Réactiver les actions attendues
                for action in actions_attendues:
                    if action in actions_actuelles:
                        if actions_actuelles[action] == 1:
                            cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET archive = 0 WHERE ID_Section = ? AND Action = ? AND archive = 1", 
                                         (id_section, action))
                            if cursor.rowcount > 0:
                                results.append(f"Réactivé: {nom_section} | {action}")
                    else:
                        # Vérifier si l'action existe déjà avec cette combinaison avant d'insérer
                        cursor.execute("SELECT ID FROM dbo.WEB_DROITS_ACCES WHERE ID_Section = ? AND Action = ?", 
                                     (id_section, action))
                        existing = cursor.fetchone()
                        if not existing:
                            cursor.execute("INSERT INTO dbo.WEB_DROITS_ACCES (ID_Section, Action, archive) VALUES (?, ?, 0)", 
                                         (id_section, action))
                            if cursor.rowcount > 0:
                                results.append(f"Ajouté: {nom_section} | {action}")
                        else:
                            # L'action existe déjà - juste s'assurer qu'elle n'est pas archivée
                            cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET archive = 0 WHERE ID_Section = ? AND Action = ?", 
                                         (id_section, action))
                            results.append(f"(déjà présent) {nom_section} | {action}")
            
            # CORRECTION DES IDs SPÉCIFIQUES
            # IMPORTANT: La colonne [ID] est une colonne IDENTITY -> on ne peut pas faire UPDATE ID = ...
            # Pour forcer des IDs précis (6,7,8), on supprime les doublons puis on ré-insère en utilisant IDENTITY_INSERT.
            corrections_ids = [
                (6, 2, "EXPORT_EXCEL"),
                (7, 2, "EXPORT_PDF"),
                (8, 3, "CONSULTATION")
            ]
            
            results_ids = []
            cursor.execute("SET IDENTITY_INSERT dbo.WEB_DROITS_ACCES ON")
            try:
                for id_record, id_section, action in corrections_ids:
                    # 1) Supprimer toute ligne existante avec la même combinaison (ID_Section, Action) mais un ID différent
                    cursor.execute(
                        "DELETE FROM dbo.WEB_DROITS_ACCES WHERE ID_Section = ? AND Action = ? AND ID <> ?",
                        (id_section, action, id_record),
                    )
                    if cursor.rowcount and cursor.rowcount > 0:
                        results_ids.append(
                            f"Supprimé {cursor.rowcount} doublon(s) pour (ID_Section={id_section}, Action={action})"
                        )

                    # 2) Supprimer la ligne portant déjà cet ID (si elle existe, même avec mauvaises valeurs)
                    cursor.execute("DELETE FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                    if cursor.rowcount and cursor.rowcount > 0:
                        results_ids.append(f"Supprimé l'ancien ID {id_record}")

                    # 3) Ré-insérer la ligne avec l'ID imposé
                    cursor.execute(
                        "INSERT INTO dbo.WEB_DROITS_ACCES (ID, ID_Section, Action, archive) VALUES (?, ?, ?, 0)",
                        (id_record, id_section, action),
                    )
                    results_ids.append(f"✓ ID {id_record} forcé: ID_Section={id_section}, Action={action}")
            finally:
                cursor.execute("SET IDENTITY_INSERT dbo.WEB_DROITS_ACCES OFF")
            
            cursor.connection.commit()
            
            # Vérifier l'état final des IDs spécifiques
            etat_ids = []
            for id_record, id_section, action in corrections_ids:
                cursor.execute("SELECT ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                row = cursor.fetchone()
                if row:
                    etat_ids.append({
                        "id": id_record,
                        "id_section": row.ID_Section,
                        "action": row.Action,
                        "archive": row.archive
                    })
            
            # Récupérer l'état final
            cursor.execute("""
                SELECT s.Nom AS Section, da.Action
                FROM dbo.WEB_DROITS_ACCES da
                INNER JOIN dbo.WEB_SECTIONS s ON s.ID = da.ID_Section
                INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                WHERE p.NumProj = 11 AND da.archive = 0
                ORDER BY s.Nom, da.Action
            """)
            actions_finales = [{"section": row.Section, "action": row.Action} for row in cursor.fetchall()]
            
            return jsonify({
                "success": True,
                "results": results,
                "results_ids": results_ids,
                "actions_finales": actions_finales,
                "actions_actives": actions_finales,  # Alias pour compatibilité
                "etat_ids": etat_ids,
                "message": "Actions corrigées avec succès"
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet11_bp.route('/projet11/admin/corriger-ids-v2')
def corriger_ids_v2():
    """Route V2 pour corriger les IDs en utilisant uniquement UPDATE - jamais INSERT"""
    print("Route corriger-ids-v2 appelée - VERSION UPDATE UNIQUEMENT")
    from db import get_db_cursor
    
    try:
        with get_db_cursor() as cursor:
            corrections = [
                (6, 2, "EXPORT_EXCEL"),
                (7, 2, "EXPORT_PDF"),
                (8, 3, "CONSULTATION")
            ]
            
            results = []
            etat_final = []
            
            for id_record, id_section, action in corrections:
                # Chercher l'enregistrement avec cette combinaison ID_Section + Action
                cursor.execute("SELECT ID, ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID_Section = ? AND Action = ?", 
                             (id_section, action))
                row_existing = cursor.fetchone()
                
                # Chercher l'enregistrement avec cet ID
                cursor.execute("SELECT ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                row_by_id = cursor.fetchone()
                
                if row_existing and row_existing.ID == id_record:
                    # Déjà correct
                    if row_existing.archive != 0:
                        cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET archive = 0 WHERE ID = ?", (id_record,))
                        results.append(f"✓ ID {id_record} réactivé")
                    else:
                        results.append(f"(déjà correct) ID {id_record}")
                elif row_existing and row_existing.ID != id_record:
                    # La combinaison existe avec un autre ID - mettre à jour cet ID
                    old_id = row_existing.ID
                    # Si l'ID cible existe avec des valeurs incorrectes, le supprimer
                    if row_by_id:
                        cursor.execute("DELETE FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                        results.append(f"Supprimé ID {id_record} avec valeurs incorrectes")
                    # Mettre à jour l'ID de l'enregistrement existant
                    cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET ID = ?, archive = 0 WHERE ID = ?", 
                                 (id_record, old_id))
                    results.append(f"✓ ID {old_id} → ID {id_record}: ID_Section={id_section}, Action={action}")
                elif row_by_id:
                    # L'ID existe mais avec des valeurs incorrectes - mettre à jour
                    cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET ID_Section = ?, Action = ?, archive = 0 WHERE ID = ?", 
                                 (id_section, action, id_record))
                    results.append(f"✓ ID {id_record} corrigé: ID_Section={id_section}, Action={action}")
                else:
                    # Aucun enregistrement trouvé - créer (seulement si vraiment nécessaire)
                    cursor.execute("INSERT INTO dbo.WEB_DROITS_ACCES (ID, ID_Section, Action, archive) VALUES (?, ?, ?, 0)", 
                                 (id_record, id_section, action))
                    results.append(f"+ ID {id_record} créé: ID_Section={id_section}, Action={action}")
            
            cursor.connection.commit()
            
            # Vérifier l'état final
            for id_record, id_section, action in corrections:
                cursor.execute("SELECT ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                row = cursor.fetchone()
                if row:
                    etat_final.append({
                        "id": id_record,
                        "id_section": row.ID_Section,
                        "action": row.Action,
                        "archive": row.archive
                    })
            
            return jsonify({
                "success": True,
                "results": results,
                "etat_final": etat_final,
                "message": "Corrections des IDs appliquées avec succès"
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet11_bp.route('/projet11/admin/corriger-ids-direct')
def corriger_ids_direct():
    """Route simple pour corriger directement les IDs spécifiques via SQL"""
    print("Route corriger-ids-direct appelée - VERSION CORRIGEE")
    from db import get_db_cursor
    
    try:
        with get_db_cursor() as cursor:
            # Corrections directes
            corrections = [
                (6, 2, "EXPORT_EXCEL"),
                (7, 2, "EXPORT_PDF"),
                (8, 3, "CONSULTATION")
            ]
            
            results = []
            etat_final = []
            
            for id_record, id_section, action in corrections:
                # Étape 1: Vérifier si un enregistrement avec cette combinaison ID_Section + Action existe déjà
                cursor.execute("SELECT ID, ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID_Section = ? AND Action = ?", 
                             (id_section, action))
                row_by_combo = cursor.fetchone()
                
                # Étape 2: Vérifier si l'enregistrement avec cet ID existe
                cursor.execute("SELECT ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                row_by_id = cursor.fetchone()
                
                if row_by_combo and row_by_combo.ID == id_record:
                    # La combinaison existe déjà avec le bon ID - vérifier archive
                    if row_by_combo.archive != 0:
                        cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET archive = 0 WHERE ID = ?", (id_record,))
                        results.append(f"✓ ID {id_record} réactivé: ID_Section={id_section}, Action={action}")
                    else:
                        results.append(f"(déjà correct) ID {id_record}: ID_Section={id_section}, Action={action}")
                elif row_by_combo and row_by_combo.ID != id_record:
                    # La combinaison existe avec un AUTRE ID - mettre à jour cet ID vers le bon
                    old_id = row_by_combo.ID
                    # Si l'ID cible existe avec des valeurs différentes, le supprimer d'abord
                    if row_by_id and (row_by_id.ID_Section != id_section or row_by_id.Action != action):
                        cursor.execute("DELETE FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                        results.append(f"Supprimé ID {id_record} avec valeurs incorrectes")
                    # Mettre à jour l'ID de l'enregistrement existant vers le bon ID
                    cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET ID = ?, archive = 0 WHERE ID = ?", 
                                 (id_record, old_id))
                    if cursor.rowcount > 0:
                        results.append(f"✓ ID {old_id} modifié vers ID {id_record}: ID_Section={id_section}, Action={action}")
                elif row_by_id:
                    # L'ID existe mais la combinaison n'existe pas encore - mettre à jour les valeurs
                    cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET ID_Section = ?, Action = ?, archive = 0 WHERE ID = ?", 
                                 (id_section, action, id_record))
                    if cursor.rowcount > 0:
                        results.append(f"✓ ID {id_record} corrigé: ID_Section={id_section}, Action={action}")
                else:
                    # Ni l'ID ni la combinaison n'existent - créer un nouvel enregistrement
                    cursor.execute("INSERT INTO dbo.WEB_DROITS_ACCES (ID, ID_Section, Action, archive) VALUES (?, ?, ?, 0)", 
                                 (id_record, id_section, action))
                    results.append(f"+ ID {id_record} créé: ID_Section={id_section}, Action={action}")
            
            cursor.connection.commit()
            
            # Vérifier l'état final
            for id_record, id_section, action in corrections:
                cursor.execute("SELECT ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                row = cursor.fetchone()
                if row:
                    etat_final.append({
                        "id": id_record,
                        "id_section": row.ID_Section,
                        "action": row.Action,
                        "archive": row.archive
                    })
            
            return jsonify({
                "success": True,
                "results": results,
                "etat_final": etat_final,
                "message": "Corrections des IDs appliquées avec succès"
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet11_bp.route('/projet11/admin/corriger-ids-specifiques-seulement')
def corriger_ids_specifiques_seulement():
    """Route pour corriger uniquement les IDs spécifiques dans WEB_DROITS_ACCES"""
    from db import get_db_cursor
    
    try:
        with get_db_cursor() as cursor:
            corrections_ids = [
                (6, 2, "EXPORT_EXCEL"),
                (7, 2, "EXPORT_PDF"),
                (8, 3, "CONSULTATION")
            ]
            
            results = []
            etat_final = []
            
            # Vérifier l'état actuel
            for id_record, id_section, action in corrections_ids:
                cursor.execute("SELECT ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                row = cursor.fetchone()
                if row:
                    results.append(f"ID {id_record} avant: ID_Section={row.ID_Section}, Action={row.Action}, archive={row.archive}")
                else:
                    results.append(f"ID {id_record} n'existe pas")
            
            # Effectuer les corrections
            for id_record, id_section, action in corrections_ids:
                cursor.execute("SELECT ID FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                if cursor.fetchone():
                    cursor.execute("""
                        UPDATE dbo.WEB_DROITS_ACCES 
                        SET ID_Section = ?, Action = ?, archive = 0
                        WHERE ID = ?
                    """, (id_section, action, id_record))
                    if cursor.rowcount > 0:
                        results.append(f"✓ ID {id_record} corrigé: ID_Section={id_section}, Action={action}")
                else:
                    cursor.execute("""
                        INSERT INTO dbo.WEB_DROITS_ACCES (ID, ID_Section, Action, archive)
                        VALUES (?, ?, ?, 0)
                    """, (id_record, id_section, action))
                    results.append(f"+ ID {id_record} créé: ID_Section={id_section}, Action={action}")
            
            cursor.connection.commit()
            
            # Vérifier l'état final
            for id_record, id_section, action in corrections_ids:
                cursor.execute("SELECT ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                row = cursor.fetchone()
                if row:
                    etat_final.append({
                        "id": id_record,
                        "id_section": row.ID_Section,
                        "action": row.Action,
                        "archive": row.archive
                    })
            
            return jsonify({
                "success": True,
                "results": results,
                "etat_final": etat_final,
                "message": "Corrections des IDs appliquées avec succès"
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet11_bp.route('/projet11/admin/corriger-actions-droits')
def corriger_actions_droits():
    """Route pour corriger les actions dans WEB_DROITS_ACCES selon la configuration attendue"""
    from db import get_db_cursor
    
    try:
        with get_db_cursor() as cursor:
            # Récupérer l'ID du Projet 11
            cursor.execute("SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = 11")
            proj_row = cursor.fetchone()
            if not proj_row:
                return jsonify({"success": False, "error": "Projet 11 introuvable"}), 404
            
            id_proj = proj_row.ID
            
            # Configuration attendue
            CONFIG_ATTENDUE = {
                "Nouvelle fiche de production": ["SAISIE"],
                "Liste des Traitements": ["CONSULTATION", "MODIFICATION", "SUPPRESSION", "SAISIE", "EXPORT_EXCEL", "EXPORT_PDF"],
                "Statistiques": ["CONSULTATION"]
            }
            
            results = []
            actions_finales = []
            
            # Pour chaque section
            for nom_section, actions_attendues in CONFIG_ATTENDUE.items():
                cursor.execute("SELECT ID FROM dbo.WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?", (id_proj, nom_section))
                section_row = cursor.fetchone()
                
                if not section_row:
                    results.append(f"Section '{nom_section}' introuvable")
                    continue
                
                id_section = section_row.ID
                
                # Récupérer les actions actuelles
                cursor.execute("SELECT Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID_Section = ?", (id_section,))
                actions_actuelles = {row.Action: row.archive for row in cursor.fetchall()}
                
                # Archiver les actions non attendues
                for action_actuelle, archive_status in actions_actuelles.items():
                    if action_actuelle not in actions_attendues and archive_status == 0:
                        cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET archive = 1 WHERE ID_Section = ? AND Action = ? AND archive = 0", 
                                     (id_section, action_actuelle))
                        if cursor.rowcount > 0:
                            results.append(f"Archivé: {nom_section} | {action_actuelle}")
                
                # Ajouter/Réactiver les actions attendues
                for action in actions_attendues:
                    if action in actions_actuelles:
                        if actions_actuelles[action] == 1:
                            cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET archive = 0 WHERE ID_Section = ? AND Action = ? AND archive = 1", 
                                         (id_section, action))
                            if cursor.rowcount > 0:
                                results.append(f"Réactivé: {nom_section} | {action}")
                    else:
                        cursor.execute("INSERT INTO dbo.WEB_DROITS_ACCES (ID_Section, Action, archive) VALUES (?, ?, 0)", 
                                     (id_section, action))
                        if cursor.rowcount > 0:
                            results.append(f"Ajouté: {nom_section} | {action}")
            
            cursor.connection.commit()
            
            # Récupérer l'état final
            cursor.execute("""
                SELECT s.Nom AS Section, da.Action
                FROM dbo.WEB_DROITS_ACCES da
                INNER JOIN dbo.WEB_SECTIONS s ON s.ID = da.ID_Section
                INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                WHERE p.NumProj = 11 AND da.archive = 0
                ORDER BY s.Nom, da.Action
            """)
            actions_finales = [{"section": row.Section, "action": row.Action} for row in cursor.fetchall()]
            
            return jsonify({
                "success": True,
                "results": results,
                "actions_finales": actions_finales,
                "message": "Actions corrigées avec succès"
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet11_bp.route('/projet11/corriger-droits')
def corriger_droits_simple():
    """Route simple pour corriger les actions dans WEB_DROITS_ACCES"""
    return corriger_actions_droits()


@projet11_bp.route('/projet11/admin/corriger-ids-sql-direct')
def corriger_ids_sql_direct():
    """Route qui exécute directement le SQL pour corriger les IDs"""
    from db import get_db_cursor
    
    try:
        with get_db_cursor() as cursor:
            results = []
            
            # Correction ID 6: EXPORT_EXCEL, ID_Section=2
            cursor.execute("SELECT ID FROM dbo.WEB_DROITS_ACCES WHERE ID_Section = 2 AND Action = 'EXPORT_EXCEL'")
            row6 = cursor.fetchone()
            if row6 and row6.ID != 6:
                cursor.execute("DELETE FROM dbo.WEB_DROITS_ACCES WHERE ID = 6")
                cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET ID = 6, archive = 0 WHERE ID = ?", (row6.ID,))
                results.append(f"✓ ID {row6.ID} → ID 6: EXPORT_EXCEL, ID_Section=2")
            elif row6 and row6.ID == 6:
                cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET archive = 0 WHERE ID = 6")
                results.append("✓ ID 6 déjà correct")
            else:
                cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET ID_Section = 2, Action = 'EXPORT_EXCEL', archive = 0 WHERE ID = 6")
                if cursor.rowcount > 0:
                    results.append("✓ ID 6 corrigé")
            
            # Correction ID 7: EXPORT_PDF, ID_Section=2
            cursor.execute("SELECT ID FROM dbo.WEB_DROITS_ACCES WHERE ID_Section = 2 AND Action = 'EXPORT_PDF'")
            row7 = cursor.fetchone()
            if row7 and row7.ID != 7:
                cursor.execute("DELETE FROM dbo.WEB_DROITS_ACCES WHERE ID = 7")
                cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET ID = 7, archive = 0 WHERE ID = ?", (row7.ID,))
                results.append(f"✓ ID {row7.ID} → ID 7: EXPORT_PDF, ID_Section=2")
            elif row7 and row7.ID == 7:
                cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET archive = 0 WHERE ID = 7")
                results.append("✓ ID 7 déjà correct")
            else:
                cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET ID_Section = 2, Action = 'EXPORT_PDF', archive = 0 WHERE ID = 7")
                if cursor.rowcount > 0:
                    results.append("✓ ID 7 corrigé")
            
            # Correction ID 8: CONSULTATION, ID_Section=3
            cursor.execute("SELECT ID FROM dbo.WEB_DROITS_ACCES WHERE ID_Section = 3 AND Action = 'CONSULTATION'")
            row8 = cursor.fetchone()
            if row8 and row8.ID != 8:
                cursor.execute("DELETE FROM dbo.WEB_DROITS_ACCES WHERE ID = 8")
                cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET ID = 8, archive = 0 WHERE ID = ?", (row8.ID,))
                results.append(f"✓ ID {row8.ID} → ID 8: CONSULTATION, ID_Section=3")
            elif row8 and row8.ID == 8:
                cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET archive = 0 WHERE ID = 8")
                results.append("✓ ID 8 déjà correct")
            else:
                cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET ID_Section = 3, Action = 'CONSULTATION', archive = 0 WHERE ID = 8")
                if cursor.rowcount > 0:
                    results.append("✓ ID 8 corrigé")
            
            cursor.connection.commit()
            
            # Vérifier l'état final
            etat_final = []
            for id_record in [6, 7, 8]:
                cursor.execute("SELECT ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                row = cursor.fetchone()
                if row:
                    etat_final.append({
                        "id": id_record,
                        "id_section": row.ID_Section,
                        "action": row.Action,
                        "archive": row.archive
                    })
            
            return jsonify({
                "success": True,
                "results": results,
                "etat_final": etat_final,
                "message": "Corrections des IDs appliquées avec succès"
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet11_bp.route('/projet11/admin/corriger-ids-droits')
def corriger_ids_droits():
    """Route pour corriger les IDs spécifiques dans WEB_DROITS_ACCES"""
    from db import get_db_cursor
    
    try:
        with get_db_cursor() as cursor:
            corrections = [
                (6, 2, "EXPORT_EXCEL"),
                (7, 2, "EXPORT_PDF"),
                (8, 3, "CONSULTATION")
            ]
            
            results = []
            etat_final = []
            
            # Vérifier l'état actuel
            for id_record, id_section, action in corrections:
                cursor.execute("SELECT ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                row = cursor.fetchone()
                if row:
                    results.append(f"ID {id_record} avant: ID_Section={row.ID_Section}, Action={row.Action}, archive={row.archive}")
                else:
                    results.append(f"ID {id_record} n'existe pas")
            
            # Effectuer les corrections
            for id_record, id_section, action in corrections:
                cursor.execute("SELECT ID FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                if cursor.fetchone():
                    cursor.execute("""
                        UPDATE dbo.WEB_DROITS_ACCES 
                        SET ID_Section = ?, Action = ?, archive = 0
                        WHERE ID = ?
                    """, (id_section, action, id_record))
                    if cursor.rowcount > 0:
                        results.append(f"✓ ID {id_record} corrigé: ID_Section={id_section}, Action={action}")
                else:
                    cursor.execute("""
                        INSERT INTO dbo.WEB_DROITS_ACCES (ID, ID_Section, Action, archive)
                        VALUES (?, ?, ?, 0)
                    """, (id_record, id_section, action))
                    results.append(f"+ ID {id_record} créé: ID_Section={id_section}, Action={action}")
            
            cursor.connection.commit()
            
            # Vérifier l'état final
            for id_record, id_section, action in corrections:
                cursor.execute("SELECT ID_Section, Action, archive FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                row = cursor.fetchone()
                if row:
                    etat_final.append({
                        "id": id_record,
                        "id_section": row.ID_Section,
                        "action": row.Action,
                        "archive": row.archive
                    })
            
            return jsonify({
                "success": True,
                "results": results,
                "etat_final": etat_final,
                "message": "Corrections appliquées avec succès"
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# 