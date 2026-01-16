"""
Routes Flask pour le Projet 20 - Analyse et affichage des données de dossier
"""
from flask import Blueprint, render_template, request, jsonify
from logic.projet20 import search_numeros_dossier, get_dossier_data

projet20_bp = Blueprint('projet20', __name__, url_prefix='/projet20')

@projet20_bp.route('/')
def index():
    """Page principale du Projet 20"""
    return render_template('projet20.html')

@projet20_bp.route('/api/search-numeros', methods=['GET'])
def api_search_numeros():
    """
    API pour la recherche autocomplete des numéros de dossier
    """
    try:
        search_term = request.args.get('q', '').strip()
        
        if not search_term:
            return jsonify({"results": []})
        
        numeros = search_numeros_dossier(search_term)
        
        # Format pour Select2 ou autocomplete simple
        results = [{"id": num, "text": num} for num in numeros[:50]]  # Limiter à 50 résultats
        
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@projet20_bp.route('/api/dossier/<numero>', methods=['GET'])
def api_get_dossier(numero):
    """
    API pour récupérer toutes les données d'un dossier
    """
    try:
        data = get_dossier_data(numero)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
