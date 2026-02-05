"""
Routes pour le Projet 22 - Gestion des employés et des ateliers
"""

from flask import Blueprint, render_template, request, jsonify
from logic.projet22 import (
    get_all_employes,
    get_employe_by_matricule,
    create_employe,
    update_employe,
    set_mot_de_passe,
    archiver_employe,
    verifier_mot_de_passe,
    get_matricules_disponibles,
    get_all_ateliers,
    get_atelier_by_id,
    create_atelier,
    update_atelier,
    delete_atelier,
    set_atelier_mdp,
    archive_atelier,
)

projet22_bp = Blueprint('projet22', __name__, url_prefix='/projet22')

@projet22_bp.route('/')
def index():
    """Page d'accueil : Gestion des Employés et des Ateliers (sections à afficher au clic)"""
    return render_template('projet22.html')

@projet22_bp.route('/api/employes', methods=['GET'])
def api_get_employes():
    """API pour récupérer tous les employés"""
    try:
        employes = get_all_employes()
        return jsonify({"success": True, "employes": employes})
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_get_employes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/employe/<int:matricule>', methods=['GET'])
def api_get_employe(matricule):
    """API pour récupérer un employé par son matricule"""
    try:
        employe = get_employe_by_matricule(matricule)
        if employe:
            return jsonify({"success": True, "employe": employe})
        return jsonify({"success": False, "error": "Employé non trouvé"}), 404
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_get_employe: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/create', methods=['POST'])
def api_create_employe():
    """API pour créer un nouvel employé"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "Aucune donnée reçue"}), 400
        
        print(f"[DEBUG] Données reçues: {data}")
        
        matricule = data.get('matricule')
        nom = data.get('nom')
        prenom = data.get('prenom')
        email = data.get('email')
        mdp = data.get('mdp')  # Optionnel
        
        # Validation
        if matricule is None:
            return jsonify({"success": False, "error": "Le matricule est requis"}), 400
        
        # Convertir le matricule en entier si c'est une chaîne
        try:
            matricule = int(matricule)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Le matricule doit être un nombre valide"}), 400
        
        if not nom or not nom.strip():
            return jsonify({"success": False, "error": "Le nom est requis"}), 400
        
        if not prenom or not prenom.strip():
            return jsonify({"success": False, "error": "Le prénom est requis"}), 400
        
        # Nettoyer les chaînes
        nom = nom.strip()
        prenom = prenom.strip()
        email = email.strip() if email else None
        mdp = mdp.strip() if mdp else None
        
        result = create_employe(matricule, nom, prenom, email, mdp)
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_create_employe: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500

@projet22_bp.route('/api/update/<int:matricule>', methods=['PUT'])
def api_update_employe(matricule):
    """API pour mettre à jour un employé"""
    try:
        data = request.get_json()
        
        nom = data.get('nom')
        prenom = data.get('prenom')
        email = data.get('email')
        
        result = update_employe(matricule, nom, prenom, email)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_update_employe: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/set-password/<int:matricule>', methods=['POST'])
def api_set_password(matricule):
    """API pour définir ou mettre à jour le mot de passe d'un employé"""
    try:
        data = request.get_json()
        new_mdp = data.get('mdp')
        old_mdp = data.get('oldPassword')  # Optionnel, requis seulement si l'employé a déjà un mot de passe
        
        if not new_mdp:
            return jsonify({"success": False, "error": "Le nouveau mot de passe est requis"}), 400
        
        if len(new_mdp) < 6:
            return jsonify({"success": False, "error": "Le mot de passe doit contenir au moins 6 caractères"}), 400
        
        result = set_mot_de_passe(matricule, new_mdp, old_mdp)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_set_password: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/archive/<int:matricule>', methods=['POST'])
def api_archive_employe(matricule):
    """API pour archiver ou désarchiver un employé"""
    try:
        data = request.get_json()
        archive = data.get('archive', True)
        
        result = archiver_employe(matricule, archive)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_archive_employe: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/verify-password', methods=['POST'])
def api_verify_password():
    """API pour vérifier un mot de passe"""
    try:
        data = request.get_json()
        matricule = data.get('matricule')
        mdp = data.get('mdp')
        
        if not matricule or not mdp:
            return jsonify({"success": False, "error": "Matricule et mot de passe requis"}), 400
        
        is_valid = verifier_mot_de_passe(matricule, mdp)
        
        return jsonify({"success": True, "valid": is_valid})
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_verify_password: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/matricules-disponibles', methods=['GET'])
def api_get_matricules_disponibles():
    """API pour récupérer les matricules disponibles"""
    try:
        limit = request.args.get('limit', 20, type=int)
        matricules = get_matricules_disponibles(limit)
        return jsonify({"success": True, "matricules": matricules})
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_get_matricules_disponibles: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# --- API Ateliers (WEB_ATELIER_ACCES) ---

@projet22_bp.route('/api/ateliers', methods=['GET'])
def api_get_ateliers():
    """API pour récupérer tous les ateliers"""
    try:
        ateliers = get_all_ateliers()
        return jsonify({"success": True, "ateliers": ateliers})
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_get_ateliers: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet22_bp.route('/api/atelier/<int:atelier_id>', methods=['GET'])
def api_get_atelier(atelier_id):
    """API pour récupérer un atelier par ID"""
    try:
        atelier = get_atelier_by_id(atelier_id)
        if atelier:
            return jsonify({"success": True, "atelier": atelier})
        return jsonify({"success": False, "error": "Atelier non trouvé"}), 404
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_get_atelier: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet22_bp.route('/api/atelier', methods=['POST'])
def api_create_atelier():
    """API pour créer un atelier"""
    try:
        data = request.get_json()
        nom = (data or {}).get('nom', '').strip()
        if not nom:
            return jsonify({"success": False, "error": "Le nom de l'atelier est requis"}), 400
        result = create_atelier(nom)
        if result["success"]:
            return jsonify(result), 201
        return jsonify(result), 400
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_create_atelier: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet22_bp.route('/api/atelier/<int:atelier_id>', methods=['PUT'])
def api_update_atelier(atelier_id):
    """API pour modifier un atelier"""
    try:
        data = request.get_json()
        nom = (data or {}).get('nom', '').strip()
        if not nom:
            return jsonify({"success": False, "error": "Le nom de l'atelier est requis"}), 400
        result = update_atelier(atelier_id, nom)
        if result["success"]:
            return jsonify(result)
        return jsonify(result), 400
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_update_atelier: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet22_bp.route('/api/atelier/<int:atelier_id>', methods=['DELETE'])
def api_delete_atelier(atelier_id):
    """API pour supprimer un atelier"""
    try:
        result = delete_atelier(atelier_id)
        if result["success"]:
            return jsonify(result)
        return jsonify(result), 400
    except Exception as e:
        print(f"[ERREUR API] Erreur dans api_delete_atelier: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet22_bp.route('/api/atelier/<int:atelier_id>/set-password', methods=['POST'])
def api_set_atelier_password(atelier_id):
    """API pour définir ou modifier le mot de passe d'un atelier"""
    try:
        data = request.get_json() or {}
        new_mdp = (data.get('mdp') or '').strip()
        old_mdp = (data.get('oldPassword') or '').strip() or None
        if not new_mdp:
            return jsonify({"success": False, "error": "Le nouveau mot de passe est requis"}), 400
        if len(new_mdp) < 6:
            return jsonify({"success": False, "error": "Le mot de passe doit contenir au moins 6 caractères"}), 400
        result = set_atelier_mdp(atelier_id, new_mdp, old_mdp)
        if result["success"]:
            return jsonify(result)
        return jsonify(result), 400
    except Exception as e:
        print(f"[ERREUR API] api_set_atelier_password: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet22_bp.route('/api/atelier/<int:atelier_id>/archive', methods=['POST'])
def api_archive_atelier(atelier_id):
    """API pour archiver ou désarchiver un atelier"""
    try:
        data = request.get_json() or {}
        archive = data.get('archive', True)
        result = archive_atelier(atelier_id, archive)
        if result["success"]:
            return jsonify(result)
        return jsonify(result), 400
    except Exception as e:
        print(f"[ERREUR API] api_archive_atelier: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
