# -*- coding: utf-8 -*-
"""
Routes pour le Projet 23 - Situation de la Trésorerie
"""
import io
from flask import Blueprint, render_template, request, jsonify
from logic.projet23 import extraire_solde_tresorerie, extraire_lignes_financement, save_synthese, get_latest_synthese
from logic.auth import is_authenticated, get_current_user

projet23_bp = Blueprint('projet23', __name__, url_prefix='/projet23')


@projet23_bp.route('/')
def index():
    """Page principale : Situation de la Trésorerie"""
    return render_template('projet23.html')


@projet23_bp.route('/api/synthese', methods=['GET'])
def api_get_synthese():
    """Récupère la dernière synthèse enregistrée (accessible à tous)."""
    try:
        data = get_latest_synthese()
        return jsonify({'success': True, 'solde': data['solde'], 'lignes': data['lignes']})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@projet23_bp.route('/api/synthese', methods=['POST'])
def api_save_synthese():
    """Enregistre la synthèse (utilisateur authentifié requis). Remplace la précédente."""
    if not is_authenticated():
        return jsonify({'success': False, 'error': 'Authentification requise.'}), 401
    try:
        payload = request.get_json() or {}
        solde = payload.get('solde')
        lignes = payload.get('lignes')
        if not solde or not lignes:
            return jsonify({'success': False, 'error': 'Données solde et lignes requises.'}), 400
        ok = save_synthese(solde, lignes, enregistre_par=get_current_user() or '')
        return jsonify({'success': ok})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@projet23_bp.route('/api/analyser/solde', methods=['POST'])
def api_analyser_solde():
    """Reçoit un fichier PDF (upload), l'analyse et retourne les données pour le graphique solde trésorerie."""
    try:
        fichier = request.files.get('fichier') or request.files.get('file')
        if not fichier or not fichier.filename or not fichier.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Veuillez envoyer un fichier PDF.'}), 400
        stream = io.BytesIO(fichier.read())
        result = extraire_solde_tresorerie(stream, filename=fichier.filename)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@projet23_bp.route('/api/analyser/lignes', methods=['POST'])
def api_analyser_lignes():
    """Reçoit un fichier PDF (upload), l'analyse et retourne les données pour le graphique lignes financement."""
    try:
        fichier = request.files.get('fichier') or request.files.get('file')
        if not fichier or not fichier.filename or not fichier.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Veuillez envoyer un fichier PDF.'}), 400
        stream = io.BytesIO(fichier.read())
        result = extraire_lignes_financement(stream, filename=fichier.filename)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
