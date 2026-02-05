from flask import Blueprint, jsonify, render_template, request, session
from db import (
    get_commandes, update_commande, get_historique_commande,
    get_commandes_avec_suivi, get_alertes_retard,
    get_statistiques_performance, get_performance_par_client,
    marquer_livraison_reelle
)

# ✅ Déclaration du blueprint
bp = Blueprint("projet1", __name__, url_prefix="/projet1")

@bp.route("/")
def index():
    return render_template("projet1.html")

@bp.route("/api/commandes")
def api_commandes():
    return jsonify(get_commandes())

@bp.route("/update_commande", methods=["POST"])
def api_update_commande():
    data = request.get_json()
    numero = data.get("id")
    new_date = data.get("start")
    
    # Récupérer l'utilisateur depuis la session
    user = None
    if session.get("matricule"):
        user = f"Matricule_{session.get('matricule')}"
    elif session.get("atelier_nom"):
        user = session.get("atelier_nom")
    elif session.get("nom"):
        user = session.get("nom")
    else:
        user = "System"

    if numero and new_date:
        success = update_commande(numero, new_date, user)
        if success:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error", "message": "Échec de la mise à jour"}), 500
    return jsonify({"status": "error", "message": "Données invalides"}), 400


@bp.route("/api/historique/<numero>")
def historique_commande(numero):
    data = get_historique_commande(numero)
    return jsonify(data)

@bp.route("/api/commandes-avec-suivi")
def api_commandes_avec_suivi():
    """Retourne les commandes avec informations de suivi des délais"""
    return jsonify(get_commandes_avec_suivi())

@bp.route("/api/alertes-retard")
def api_alertes_retard():
    """Retourne les alertes de retard (commandes en retard sans date de livraison)"""
    return jsonify(get_alertes_retard())

@bp.route("/api/statistiques-performance")
def api_statistiques_performance():
    """Retourne les statistiques de performance globales"""
    return jsonify(get_statistiques_performance())

@bp.route("/api/performance-par-client")
def api_performance_par_client():
    """Retourne les statistiques de performance par client"""
    try:
        data = get_performance_par_client()
        # S'assurer que c'est toujours une liste
        if not isinstance(data, list):
            return jsonify([]), 200
        return jsonify(data)
    except Exception as e:
        print(f"[Erreur performance-par-client] {e}")
        import traceback
        traceback.print_exc()
        return jsonify([]), 500

@bp.route("/api/marquer-livraison", methods=["POST"])
def api_marquer_livraison():
    """Marque une commande comme livrée avec la date réelle"""
    data = request.get_json()
    numero = data.get("numero")
    date_livraison = data.get("date_livraison")
    
    # Récupérer l'utilisateur depuis la session
    user = None
    if session.get("matricule"):
        user = f"Matricule_{session.get('matricule')}"
    elif session.get("atelier_nom"):
        user = session.get("atelier_nom")
    elif session.get("nom"):
        user = session.get("nom")
    elif data.get("user"):
        user = data.get("user")
    else:
        user = "System"
    
    if numero and date_livraison:
        success = marquer_livraison_reelle(numero, date_livraison, user)
        if success:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error", "message": "Échec du marquage de livraison"}), 500
    return jsonify({"status": "error", "message": "Données invalides"}), 400
