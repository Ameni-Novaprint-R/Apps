"""
Routes Flask pour le Projet 19 - Gestion des Dossiers en Cours
Toutes les opérations CRUD pointent vers WEB_S_DOS_ENCOURS sur le serveur réseau 192.168.10.225
COMMANDES et SOCIETES sont en lecture seule
"""
from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
import sys
from db import (
    search_commandes_by_numero,
    get_commande_by_numero,
    get_web_s_dos_encours,
    create_web_s_dos_encours,
    update_web_s_dos_encours_avancement,
    update_web_s_dos_encours_quantite_prix_total,
    get_services_by_numero_commande,
    delete_web_s_dos_encours,
    get_achats_mat_by_numero_commande,
    get_achats_sstr_by_numero_commande,
    get_ct_prev_dev_sum_by_numero_commande
)

projet19_bp = Blueprint('projet19', __name__, url_prefix='/projet19')

@projet19_bp.route('/')
def index():
    """Page principale du Projet 19"""
    return render_template('projet19.html')

@projet19_bp.route('/api/search-commandes', methods=['GET'])
def api_search_commandes():
    """
    Recherche dans COMMANDES par numéro (recherche type "contient")
    LECTURE SEULE - Ne modifie pas COMMANDES
    Utilisé uniquement pour la sélection dans l'interface
    """
    try:
        search_term = request.args.get('q', '').strip()
        
        if not search_term:
            return jsonify({"results": []})
        
        # Recherche dans COMMANDES (lecture seule)
        results = search_commandes_by_numero(search_term)
        
        return jsonify({
            "results": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@projet19_bp.route('/api/commande/<numero>', methods=['GET'])
def api_get_commande(numero):
    """
    Récupère les détails d'une commande depuis COMMANDES
    LECTURE SEULE - Ne modifie pas COMMANDES
    """
    try:
        commande = get_commande_by_numero(numero)
        
        if not commande:
            return jsonify({"error": "Commande non trouvée"}), 404
        
        return jsonify(commande)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@projet19_bp.route('/api/achats-mat/<numero>', methods=['GET'])
def api_get_achats_mat(numero):
    """
    Récupère AchatsMat depuis DEV_COUTS pour un numéro de commande
    Utilisé pour calculer le coût total quand avancement = "Matière première sortie"
    LECTURE SEULE - Ne modifie pas DEV_COUTS ni COMMANDES
    """
    try:
        print(f"[API] Début récupération AchatsMat pour {numero}")
        achats_mat = get_achats_mat_by_numero_commande(numero)
        print(f"[API] AchatsMat récupéré: {achats_mat}")
        
        if achats_mat is None:
            print(f"[API] AchatsMat non trouvé pour {numero}")
            return jsonify({
                "success": False,
                "achats_mat": None,
                "message": "AchatsMat non trouvé pour ce dossier"
            })
        
        print(f"[API] Retour de la réponse avec succès pour {numero}")
        return jsonify({
            "success": True,
            "achats_mat": achats_mat
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[API ERROR] Erreur lors de la récupération d'AchatsMat pour {numero}: {e}")
        print(f"[API ERROR] Traceback complet:")
        print(error_trace)
        return jsonify({
            "error": str(e),
            "traceback": error_trace
        }), 500

@projet19_bp.route('/api/postes/<numero>', methods=['GET'])
def api_get_postes(numero):
    """
    Récupère les services disponibles pour un numéro de dossier
    LECTURE SEULE - Ne modifie pas GP_FICHES_TRAVAIL, GP_POSTES ni GP_SERVICES
    Logique : COMMANDES → GP_FICHES_TRAVAIL → GP_POSTES → GP_SERVICES
    """
    try:
        print(f"[API] Récupération des services pour le dossier: {numero}")
        services = get_services_by_numero_commande(numero)
        print(f"[API] {len(services)} services trouvés pour {numero}")
        
        # Debug: afficher les coûts de chaque service
        print(f"[API DEBUG] Détails complets des {len(services)} services:")
        for idx, service in enumerate(services):
            print(f"[API DEBUG] #{idx+1} - nom='{service.get('nom')}', cout={service.get('cout')}, id={service.get('id')}, id_fiche={service.get('id_fiche_travail')}")
        
        # Vérifier si "Matière première sortie" est dans la liste
        noms_services = [s.get('nom', '') for s in services]
        has_matiere_premiere = 'Matière première sortie' in noms_services
        print(f"[API] Liste des services: {noms_services}")
        print(f"[API] 'Matière première sortie' présent: {has_matiere_premiere}")
        
        # Debug: vérifier le contenu complet avant jsonify
        import json
        if services:
            print(f"[API DEBUG] Contenu avant jsonify (premier service): {json.dumps(services[0], indent=2, ensure_ascii=False)}")
            print(f"[API DEBUG] Tous les champs du premier service: id={services[0].get('id')}, nom={services[0].get('nom')}, cout={services[0].get('cout')}, id_fiche={services[0].get('id_fiche_travail')}")
        
        # FORCER la sérialisation JSON pour s'assurer que tous les champs sont présents
        # Convertir explicitement en dict Python standard (pas de Row objects)
        services_dict = []
        for service in services:
            service_dict = {
                "id": str(service.get('id', '')),
                "nom": str(service.get('nom', '')),
                "cout": float(service.get('cout', 0.0)),
                "id_fiche_travail": int(service.get('id_fiche_travail')) if service.get('id_fiche_travail') is not None else None,
                "nom_poste": str(service.get('nom_poste')) if service.get('nom_poste') is not None else None
            }
            services_dict.append(service_dict)
        
        response_data = {
            "postes": services_dict  # Garde le nom "postes" pour compatibilité avec le frontend
        }
        
        print(f"[API DEBUG] Nombre de services dans response_data: {len(response_data['postes'])}")
        if response_data['postes']:
            print(f"[API DEBUG] Premier service dans response_data: {json.dumps(response_data['postes'][0], indent=2, ensure_ascii=False)}")
        
        return jsonify(response_data)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[API] Erreur lors de la récupération des services pour {numero}: {e}")
        print(error_trace)
        return jsonify({"error": str(e)}), 500

@projet19_bp.route('/api/cout-total-offset/<numero>', methods=['GET'])
def api_get_cout_total_offset(numero):
    """
    Récupère toutes les composantes nécessaires pour calculer le coût total
    quand avancement = "OFFSET FEUILLES"
    Composantes:
    1. Coût matière première (AchatsMat, ID_CENTRE_COUT = 1)
    2. AchatsSstr (ID_CENTRE_COUT = 5)
    3. Somme CtPrevDev (ID_SERVICE = 1 ou 5)
    LECTURE SEULE - Ne modifie aucune table
    """
    try:
        print(f"[API] Début récupération composantes coût total OFFSET FEUILLES pour {numero}")
        
        # 1. Coût matière première (AchatsMat, ID_CENTRE_COUT = 1)
        cout_matiere_premiere = get_achats_mat_by_numero_commande(numero)
        if cout_matiere_premiere is None:
            cout_matiere_premiere = 0.000
        
        # 2. AchatsSstr (ID_CENTRE_COUT = 5)
        achats_sstr = get_achats_sstr_by_numero_commande(numero)
        if achats_sstr is None:
            achats_sstr = 0.000
        
        # 3. Somme CtPrevDev (ID_SERVICE = 1 ou 5)
        ct_prev_dev_sum = get_ct_prev_dev_sum_by_numero_commande(numero)
        if ct_prev_dev_sum is None:
            ct_prev_dev_sum = 0.000
        
        # Calculer le coût total (somme des 3 composantes)
        cout_total = round(cout_matiere_premiere + achats_sstr + ct_prev_dev_sum, 3)
        
        print(f"[API] Composantes récupérées pour {numero}:")
        print(f"  - Coût matière première: {cout_matiere_premiere}")
        print(f"  - AchatsSstr: {achats_sstr}")
        print(f"  - Somme CtPrevDev: {ct_prev_dev_sum}")
        print(f"  - Coût total: {cout_total}")
        
        return jsonify({
            "success": True,
            "cout_matiere_premiere": cout_matiere_premiere,
            "achats_sstr": achats_sstr,
            "ct_prev_dev_sum": ct_prev_dev_sum,
            "cout_total": cout_total
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[API ERROR] Erreur lors de la récupération du coût total OFFSET FEUILLES pour {numero}: {e}")
        print(f"[API ERROR] Traceback complet:")
        print(error_trace)
        return jsonify({
            "error": str(e),
            "traceback": error_trace
        }), 500

@projet19_bp.route('/api/dossiers-suivi', methods=['GET'])
def api_get_dossiers_suivi():
    """
    Récupère tous les dossiers en suivi depuis WEB_S_DOS_ENCOURS
    """
    try:
        search_numero = request.args.get('search', '').strip()
        
        dossiers = get_web_s_dos_encours(search_numero if search_numero else None)
        
        # Debug: vérifier le premier dossier retourné
        if dossiers and len(dossiers) > 0:
            print(f"[API] Premier dossier retourné: {dossiers[0]}")
            # Vérifier spécifiquement ct_rel
            for dossier in dossiers:
                if dossier.get('numero') == '2025050176':
                    print(f"[API DEBUG] Dossier 2025050176 trouvé: ct_rel = {dossier.get('ct_rel')}")
        
        # Vérifier que tous les dossiers sont sérialisables en JSON
        try:
            # Tester la sérialisation avant de retourner
            import json
            json.dumps(dossiers, default=str)
        except Exception as json_err:
            print(f"[API ERROR] Erreur de sérialisation JSON: {json_err}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Erreur de sérialisation: {str(json_err)}"}), 500
        
        return jsonify({
            "dossiers": dossiers
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[API ERROR] Erreur dans api_get_dossiers_suivi: {e}")
        print(error_trace)
        # Retourner l'erreur avec plus de détails
        return jsonify({
            "error": str(e),
            "type": type(e).__name__,
            "traceback": error_trace
        }), 500

@projet19_bp.route('/api/create', methods=['POST'])
def api_create_dossier():
    """
    Crée un nouveau dossier dans WEB_S_DOS_ENCOURS
    Les données sont copiées depuis COMMANDES et SOCIETES mais enregistrées uniquement dans WEB_S_DOS_ENCOURS
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Aucune donnée fournie"}), 400
        
        numero = data.get('numero', '').strip()
        if not numero:
            return jsonify({"error": "Le numéro de dossier est requis"}), 400
        
        # Récupérer les données depuis COMMANDES et SOCIETES (lecture seule)
        commande = get_commande_by_numero(numero)
        
        if not commande:
            return jsonify({"error": "Commande non trouvée dans COMMANDES"}), 404
        
        # Récupérer l'avancement, la quantité, le prix de vente total, le coût total estimé et le coût total depuis les données envoyées
        avancement = data.get('avancement')
        quantite = data.get('quantite')  # QteComm_COMMANDES - valeur saisie par l'utilisateur
        prix_vente_total = data.get('prix_vente_total')  # PrixVenteTotal - valeur calculée dans l'application
        ct_estime = data.get('ct_estime')  # CTEstimé - valeur calculée dans l'application
        cout_total = data.get('cout_total')  # CoutTotal - valeur calculée dans l'application
        date_inventaire_str = (data.get('date_inventaire') or '').strip()
        prepress_override = data.get('prepress_override')
        
        # Convertir quantite en int si elle est fournie
        if quantite is not None:
            try:
                quantite = int(quantite)
                if quantite < 0:
                    return jsonify({"error": "La quantité ne peut pas être négative"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "La quantité doit être un nombre entier"}), 400
        
        # Convertir prix_vente_total en float si elle est fournie
        if prix_vente_total is not None:
            try:
                prix_vente_total = float(prix_vente_total)
            except (ValueError, TypeError):
                return jsonify({"error": "Le prix de vente total doit être un nombre"}), 400
        
        # Convertir ct_estime en float si elle est fournie
        if ct_estime is not None:
            try:
                ct_estime = round(float(ct_estime), 3)
            except (ValueError, TypeError):
                return jsonify({"error": "Le coût total estimé doit être un nombre"}), 400
        
        # Convertir cout_total en float si elle est fournie
        if cout_total is not None:
            try:
                cout_total = round(float(cout_total), 3)
            except (ValueError, TypeError):
                return jsonify({"error": "Le coût total doit être un nombre"}), 400
        
        if prepress_override is not None and prepress_override != "":
            try:
                prepress_override = round(float(prepress_override), 3)
            except (ValueError, TypeError):
                return jsonify({"error": "Le montant PRE-PRESS modifié doit être un nombre"}), 400
        else:
            prepress_override = None
        
        date_inventaire = None
        if date_inventaire_str:
            try:
                date_inventaire = datetime.strptime(date_inventaire_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "La date d'inventaire doit être au format YYYY-MM-DD"}), 400
        
        # Convertir ct_rel en float si elle est fournie (même si 0, on l'enregistre)
        ct_rel = data.get('ct_rel')  # CtRel - valeur calculée dans l'application: (CoutTotal / QteComm_COMMANDES) * Quantité
        
        # Logs très visibles pour ct_rel
        print("="*80)
        print(f"[CTREL DEBUG] ========== DEBUT TRAITEMENT CTREL ==========")
        print(f"[CTREL DEBUG] ct_rel reçu depuis JSON: {ct_rel}")
        print(f"[CTREL DEBUG] Type de ct_rel: {type(ct_rel)}")
        print(f"[CTREL DEBUG] Toutes les clés dans data: {list(data.keys())}")
        print(f"[CTREL DEBUG] Valeur brute de ct_rel: {repr(ct_rel)}")
        sys.stdout.flush()
        
        if ct_rel is not None:
            try:
                ct_rel = round(float(ct_rel), 3)
                print(f"[CTREL DEBUG] ct_rel converti en float: {ct_rel}")
                sys.stdout.flush()
            except (ValueError, TypeError) as e:
                print(f"[CTREL DEBUG] ERREUR conversion ct_rel: {e}")
                sys.stdout.flush()
                return jsonify({"error": "Le coût total réel doit être un nombre"}), 400
        else:
            # Si ct_rel n'est pas fourni, utiliser 0.0 au lieu de None pour toujours enregistrer une valeur
            ct_rel = 0.0
            print(f"[CTREL DEBUG] ct_rel est None, utilisation de 0.0 par défaut")
            sys.stdout.flush()
        
        # Créer le dossier dans WEB_S_DOS_ENCOURS
        print(f"[CTREL DEBUG] Création dossier avec ct_rel={ct_rel}")
        print(f"[CTREL DEBUG] ========== FIN TRAITEMENT CTREL ==========")
        print("="*80)
        sys.stdout.flush()
        dossier_id = create_web_s_dos_encours(
            numero=numero,
            client=commande.get('client'),
            reference=commande.get('reference'),
            marge=commande.get('marge'),
            avancement=avancement,
            quantite=quantite,
            prix_vente_total=prix_vente_total,
            ct_estime=ct_estime,
            cout_total=cout_total,
            ct_rel=ct_rel,
            date_inventaire=date_inventaire,
            prepress_prosetter_override=prepress_override
        )
        
        if dossier_id is None:
            return jsonify({"error": "Erreur lors de la création du dossier"}), 500
        
        return jsonify({
            "success": True,
            "message": "Dossier ajouté au suivi",
            "id": dossier_id
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERREUR] api_create_dossier: {e}")
        print(error_trace)
        return jsonify({
            "error": str(e),
            "traceback": error_trace
        }), 500

@projet19_bp.route('/api/update-avancement', methods=['POST'])
def api_update_avancement():
    """
    Met à jour uniquement l'avancement (Nom_GP_SERVICES) d'un dossier dans WEB_S_DOS_ENCOURS
    """
    try:
        data = request.get_json()
        
        dossier_id = data.get('id')
        avancement = data.get('avancement')  # Peut être None ou vide
        
        if not dossier_id:
            return jsonify({"error": "ID est requis"}), 400
        
        # Mise à jour uniquement dans WEB_S_DOS_ENCOURS
        success = update_web_s_dos_encours_avancement(dossier_id, avancement if avancement else None)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Avancement mis à jour"
            })
        else:
            return jsonify({"error": "Dossier non trouvé"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@projet19_bp.route('/api/update-quantite-prix-total', methods=['POST'])
def api_update_quantite_prix_total():
    """
    Met à jour la quantité (QteComm_COMMANDES), le prix de vente total (PrixVenteTotal), 
    le coût total estimé (CTEstimé) et le coût total (CoutTotal) d'un dossier dans WEB_S_DOS_ENCOURS
    """
    try:
        data = request.get_json()
        
        dossier_id = data.get('id')
        quantite = data.get('quantite')  # QteComm_COMMANDES - valeur saisie par l'utilisateur
        prix_vente_total = data.get('prix_vente_total')  # PrixVenteTotal - valeur calculée dans l'application
        ct_estime = data.get('ct_estime')  # CTEstimé - valeur calculée dans l'application
        cout_total = data.get('cout_total')  # CoutTotal - valeur calculée dans l'application
        ct_rel = data.get('ct_rel')  # CtRel - valeur calculée dans l'application: (CoutTotal / QteComm_COMMANDES) * Quantité
        prepress_override = data.get('prepress_override')
        
        if not dossier_id:
            return jsonify({"error": "ID est requis"}), 400
        
        # Valider la quantité
        if quantite is not None:
            try:
                quantite = int(quantite)
                if quantite < 0:
                    return jsonify({"error": "La quantité ne peut pas être négative"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "La quantité doit être un nombre entier"}), 400
        
        # Convertir prix_vente_total en float si fourni
        if prix_vente_total is not None:
            try:
                prix_vente_total = float(prix_vente_total)
            except (ValueError, TypeError):
                return jsonify({"error": "Le prix de vente total doit être un nombre"}), 400
        
        # Convertir ct_estime en float si fourni
        if ct_estime is not None:
            try:
                ct_estime = round(float(ct_estime), 3)
            except (ValueError, TypeError):
                return jsonify({"error": "Le coût total estimé doit être un nombre"}), 400
        
        # Convertir cout_total en float si fourni
        if cout_total is not None:
            try:
                cout_total = round(float(cout_total), 3)
            except (ValueError, TypeError):
                return jsonify({"error": "Le coût total doit être un nombre"}), 400
        
        # Convertir ct_rel en float si fourni
        if ct_rel is not None:
            try:
                ct_rel = round(float(ct_rel), 3)
            except (ValueError, TypeError):
                return jsonify({"error": "Le coût total réel doit être un nombre"}), 400
        
        if prepress_override is not None and prepress_override != "":
            try:
                prepress_override = round(float(prepress_override), 3)
            except (ValueError, TypeError):
                return jsonify({"error": "Le montant PRE-PRESS modifié doit être un nombre"}), 400
        else:
            prepress_override = None
        
        # Mise à jour uniquement dans WEB_S_DOS_ENCOURS
        success = update_web_s_dos_encours_quantite_prix_total(dossier_id, quantite, prix_vente_total, ct_estime, cout_total, ct_rel, prepress_override)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Quantité et prix de vente total mis à jour"
            })
        else:
            return jsonify({"error": "Dossier non trouvé ou colonnes inexistantes"}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@projet19_bp.route('/api/delete/<int:dossier_id>', methods=['DELETE'])
def api_delete_dossier(dossier_id):
    """
    Supprime un dossier de WEB_S_DOS_ENCOURS
    """
    try:
        success = delete_web_s_dos_encours(dossier_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Dossier supprimé"
            })
        else:
            return jsonify({"error": "Dossier non trouvé"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
