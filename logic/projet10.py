from flask import Blueprint, jsonify, render_template, request
from db import (
    get_controles_qualite, 
    get_controle_qualite_by_id,
    create_controle_qualite,
    update_controle_qualite,
    delete_controle_qualite,
    get_statistiques_controle_qualite,
    get_performance_par_machine,
    get_evolution_qualite,
    get_dossiers_probleme,
    get_numeros_commandes_disponibles,
    get_operateurs,
    get_comparaison_periodes,
    get_comparaison_machines,
    get_machines_impression,
    get_traitement_data_for_controle
)

# Déclaration du blueprint
bp = Blueprint("projet10", __name__, url_prefix="/projet10")

@bp.route("/")
def index():
    """Page principale du contrôle qualité"""
    return render_template("projet10.html")

# ---------------------------
# PAGE STATS SEPAREE
# ---------------------------
@bp.route("/stat")
def stats_page():
    """Page dédiée d'affichage des statistiques (hors onglets)."""
    return render_template("projet10stat.html")

# ---------------------------
# API CONTRÔLE QUALITÉ
# ---------------------------
@bp.route("/api/controles")
def api_controles():
    """API pour récupérer tous les contrôles qualité"""
    return jsonify(get_controles_qualite())

@bp.route("/api/controle/<int:controle_id>")
def api_controle(controle_id):
    """API pour récupérer un contrôle qualité par ID"""
    controle = get_controle_qualite_by_id(controle_id)
    if controle:
        return jsonify(controle)
    return jsonify({"error": "Contrôle non trouvé"}), 404

# ---------------------------
# PAGE FICHE D'EDITION DETAILLEE
# ---------------------------
@bp.route("/fiche/<int:controle_id>")
def fiche_controle(controle_id: int):
    """Affiche une page dédiée de fiche avec tableau éditable des tolérances."""
    return render_template("projet10_fiche.html", controle_id=controle_id)

@bp.route("/api/numeros-commandes")
def api_numeros_commandes():
    """API pour récupérer les numéros de commandes disponibles"""
    return jsonify(get_numeros_commandes_disponibles())

@bp.route("/api/statistiques")
def api_statistiques():
    """API pour récupérer les statistiques globales de contrôle qualité"""
    return jsonify(get_statistiques_controle_qualite())

@bp.route("/api/statistiques/machines")
def api_statistiques_machines():
    """API pour récupérer les statistiques par machine"""
    return jsonify(get_performance_par_machine())

@bp.route("/api/statistiques/evolution")
def api_statistiques_evolution():
    """API pour récupérer l'évolution de la qualité sur 30 jours"""
    jours = request.args.get('jours', 30, type=int)
    return jsonify(get_evolution_qualite(jours))

@bp.route("/api/statistiques/dossiers-probleme")
def api_statistiques_dossiers_probleme():
    """API pour récupérer les dossiers avec rebus élevé"""
    seuil = request.args.get('seuil', 5, type=float)
    return jsonify(get_dossiers_probleme(seuil))

@bp.route("/api/operateurs")
def api_operateurs():
    """API pour récupérer la liste des opérateurs disponibles"""
    try:
        operateurs = get_operateurs()
        return jsonify(operateurs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/api/controle", methods=["POST"])
def api_create_controle():
    """API pour créer un nouveau contrôle qualité"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Données manquantes"}), 400
        
        # Validation des champs obligatoires
        required_fields = ['date_controle', 'Numero_COMMANDES', 'operateur']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Champ obligatoire manquant: {field}"}), 400
        
        controle_id = create_controle_qualite(data)
        
        if controle_id:
            return jsonify({"status": "success", "id": controle_id}), 201
        else:
            return jsonify({"error": "Erreur lors de la création - la fonction a retourné None"}), 500
    except Exception as e:
        print(f"ERREUR API CREATE CONTROLE: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@bp.route("/api/controle/<int:controle_id>", methods=["PUT"])
def api_update_controle(controle_id):
    """API pour mettre à jour un contrôle qualité"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Données manquantes"}), 400
        
        success = update_controle_qualite(controle_id, data)
        
        if success:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"error": "Erreur lors de la mise à jour - la fonction a retourné False"}), 500
    except Exception as e:
        print(f"ERREUR API UPDATE CONTROLE: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@bp.route("/api/controle/<int:controle_id>", methods=["DELETE"])
def api_delete_controle(controle_id):
    """API pour supprimer un contrôle qualité"""
    try:
        success = delete_controle_qualite(controle_id)
        if success:
            return jsonify({"status": "success", "message": "Contrôle supprimé avec succès"}), 200
        else:
            return jsonify({"error": "Contrôle non trouvé"}), 404
    except Exception as e:
        print(f"ERREUR API DELETE CONTROLE: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@bp.route("/api/statistiques/comparaison-periodes")
def api_comparaison_periodes():
    """API pour comparer deux périodes"""
    date_debut1 = request.args.get('date_debut1', type=str)
    date_fin1 = request.args.get('date_fin1', type=str)
    date_debut2 = request.args.get('date_debut2', type=str)
    date_fin2 = request.args.get('date_fin2', type=str)
    
    if not all([date_debut1, date_fin1, date_debut2, date_fin2]):
        return jsonify({"error": "Toutes les dates sont requises"}), 400
    
    return jsonify(get_comparaison_periodes(date_debut1, date_fin1, date_debut2, date_fin2))

@bp.route("/api/statistiques/comparaison-machines")
def api_comparaison_machines():
    """API pour comparer deux machines"""
    machine1 = request.args.get('machine1', type=str)
    machine2 = request.args.get('machine2', type=str)
    jours = request.args.get('jours', 30, type=int)
    
    if not machine1 or not machine2:
        return jsonify({"error": "Les deux machines sont requises"}), 400
    
    return jsonify(get_comparaison_machines(machine1, machine2, jours))

@bp.route("/api/machines-disponibles")
def api_machines_disponibles():
    """API pour récupérer la liste des machines d'impression depuis GP_POSTES (centre de coût 6)"""
    try:
        machines = get_machines_impression()
        # Retourner seulement les noms pour la compatibilité avec le frontend
        noms_machines = [m["nom"] for m in machines]
        return jsonify(noms_machines)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/api/traitement-data/<numero_commande>")
def api_traitement_data(numero_commande):
    """API pour récupérer les données de WEB_TRAITEMENTS pour pré-remplir le formulaire"""
    try:
        data = get_traitement_data_for_controle(numero_commande)
        if data:
            return jsonify(data)
        else:
            return jsonify({"machine_impression": None, "operateurs": []})
    except Exception as e:
        print(f"Erreur lors de la récupération des données traitement: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500