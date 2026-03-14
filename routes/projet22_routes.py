"""
Routes pour le Projet 22 - Gestion des employés et des ateliers
"""

from flask import Blueprint, render_template, request, jsonify
from logic.auth import is_super_user
from logic.projet22_droits import (
    get_projets_avec_sections,
    get_droits_accordes,
    ajouter_droit,
    supprimer_droit,
    get_employes_pour_select,
    get_ateliers_pour_select,
    get_projets_tous,
    create_projet,
    update_projet,
    archive_projet,
    get_sections_toutes,
    create_section,
    update_section,
    archive_section,
    get_actions_toutes,
    create_action,
    update_action,
    archive_action,
)
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


# --- API Gestion des droits d'accès (réservé aux super-utilisateurs) ---

def _droits_require_super():
    if not is_super_user():
        return jsonify({"success": False, "error": "Accès réservé aux super-utilisateurs"}), 403
    return None

# Projets (admin)
@projet22_bp.route('/api/droits/projets-admin', methods=['GET'])
def api_droits_projets_admin():
    err = _droits_require_super()
    if err: return err
    try:
        inclure = request.args.get('archives', '1') == '1'
        projets = get_projets_tous(inclure_archives=inclure)
        return jsonify({"success": True, "projets": projets})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/droits/projet', methods=['POST'])
def api_droits_projet_create():
    err = _droits_require_super()
    if err: return err
    try:
        d = request.get_json() or {}
        num = d.get('num_proj')
        code = d.get('code_proj', '')
        nom = d.get('nom', '')
        archive = d.get('archive', False)
        if num is None:
            return jsonify({"success": False, "error": "num_proj requis"}), 400
        num = int(num)
        result = create_projet(num, code, nom, archive)
        return jsonify(result) if result["success"] else (jsonify(result), 400)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "num_proj invalide"}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/droits/projet/<int:proj_id>', methods=['PUT'])
def api_droits_projet_update(proj_id):
    err = _droits_require_super()
    if err: return err
    try:
        d = request.get_json() or {}
        updates = {}
        if 'num_proj' in d: updates['num_proj'] = int(d['num_proj'])
        if 'code_proj' in d: updates['code_proj'] = d['code_proj']
        if 'nom' in d: updates['nom'] = d['nom']
        if 'archive' in d: updates['archive'] = bool(d['archive'])
        result = update_projet(proj_id, **updates)
        return jsonify(result) if result["success"] else (jsonify(result), 400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/droits/projet/<int:proj_id>/archive', methods=['POST'])
def api_droits_projet_archive(proj_id):
    err = _droits_require_super()
    if err: return err
    try:
        archive = (request.get_json() or {}).get('archive', True)
        result = archive_projet(proj_id, archive=archive)
        return jsonify(result) if result["success"] else (jsonify(result), 400)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Sections (admin)
@projet22_bp.route('/api/droits/sections', methods=['GET'])
def api_droits_sections():
    err = _droits_require_super()
    if err: return err
    try:
        id_proj = request.args.get('id_proj', type=int)
        inclure = request.args.get('archives', '1') == '1'
        sections = get_sections_toutes(inclure_archives=inclure, id_proj=id_proj)
        return jsonify({"success": True, "sections": sections})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/droits/section', methods=['POST'])
def api_droits_section_create():
    err = _droits_require_super()
    if err: return err
    try:
        d = request.get_json() or {}
        id_proj = d.get('id_proj')
        nom = d.get('nom', '')
        archive = d.get('archive', False)
        if id_proj is None:
            return jsonify({"success": False, "error": "id_proj requis"}), 400
        result = create_section(id_proj, nom, archive)
        return jsonify(result) if result["success"] else (jsonify(result), 400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/droits/section/<int:sec_id>', methods=['PUT'])
def api_droits_section_update(sec_id):
    err = _droits_require_super()
    if err: return err
    try:
        d = request.get_json() or {}
        updates = {}
        if 'id_proj' in d: updates['id_proj'] = int(d['id_proj'])
        if 'nom' in d: updates['nom'] = d['nom']
        if 'archive' in d: updates['archive'] = bool(d['archive'])
        result = update_section(sec_id, **updates)
        return jsonify(result) if result["success"] else (jsonify(result), 400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/droits/section/<int:sec_id>/archive', methods=['POST'])
def api_droits_section_archive(sec_id):
    err = _droits_require_super()
    if err: return err
    try:
        archive = (request.get_json() or {}).get('archive', True)
        result = archive_section(sec_id, archive=archive)
        return jsonify(result) if result["success"] else (jsonify(result), 400)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Actions (admin)
@projet22_bp.route('/api/droits/actions', methods=['GET'])
def api_droits_actions():
    err = _droits_require_super()
    if err: return err
    try:
        id_section = request.args.get('id_section', type=int)
        inclure = request.args.get('archives', '1') == '1'
        actions = get_actions_toutes(inclure_archives=inclure, id_section=id_section)
        return jsonify({"success": True, "actions": actions})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/droits/action', methods=['POST'])
def api_droits_action_create():
    err = _droits_require_super()
    if err: return err
    try:
        d = request.get_json() or {}
        id_section = d.get('id_section')
        action = d.get('action', '')
        archive = d.get('archive', False)
        code_proj = d.get('code_proj')
        nom_sections = d.get('nom_sections')
        if id_section is None:
            return jsonify({"success": False, "error": "id_section requis"}), 400
        result = create_action(id_section, action, archive, code_proj, nom_sections)
        return jsonify(result) if result["success"] else (jsonify(result), 400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/droits/action/<int:act_id>', methods=['PUT'])
def api_droits_action_update(act_id):
    err = _droits_require_super()
    if err: return err
    try:
        d = request.get_json() or {}
        updates = {}
        if 'id_section' in d: updates['id_section'] = int(d['id_section'])
        if 'action' in d: updates['action'] = d['action']
        if 'archive' in d: updates['archive'] = bool(d['archive'])
        if 'code_proj' in d: updates['code_proj'] = d['code_proj']
        if 'nom_sections' in d: updates['nom_sections'] = d['nom_sections']
        result = update_action(act_id, **updates)
        return jsonify(result) if result["success"] else (jsonify(result), 400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/droits/action/<int:act_id>/archive', methods=['POST'])
def api_droits_action_archive(act_id):
    err = _droits_require_super()
    if err: return err
    try:
        archive = (request.get_json() or {}).get('archive', True)
        result = archive_action(act_id, archive=archive)
        return jsonify(result) if result["success"] else (jsonify(result), 400)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@projet22_bp.route('/api/droits/projets', methods=['GET'])
def api_droits_projets():
    """API pour récupérer les projets avec sections et actions (pour sélecteurs)"""
    err = _droits_require_super()
    if err: return err
    try:
        inclure = request.args.get('archives', '0') == '1'
        projets = get_projets_avec_sections(inclure_archives=inclure)
        return jsonify({"success": True, "projets": projets})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet22_bp.route('/api/droits/liste', methods=['GET'])
def api_droits_liste():
    """API pour récupérer tous les droits accordés"""
    err = _droits_require_super()
    if err: return err
    try:
        droits = get_droits_accordes()
        return jsonify({"success": True, "droits": droits})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet22_bp.route('/api/droits/employes-select', methods=['GET'])
def api_droits_employes_select():
    """API pour la liste des employés (sélecteur)"""
    err = _droits_require_super()
    if err: return err
    try:
        employes = get_employes_pour_select()
        return jsonify({"success": True, "employes": employes})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet22_bp.route('/api/droits/ateliers-select', methods=['GET'])
def api_droits_ateliers_select():
    """API pour la liste des ateliers (sélecteur)"""
    err = _droits_require_super()
    if err: return err
    try:
        ateliers = get_ateliers_pour_select()
        return jsonify({"success": True, "ateliers": ateliers})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet22_bp.route('/api/droits/ajouter', methods=['POST'])
def api_droits_ajouter():
    """API pour ajouter un droit d'accès"""
    err = _droits_require_super()
    if err: return err
    try:
        data = request.get_json() or {}
        cible_type = (data.get("cible_type") or "").strip().lower()
        cible_valeur = data.get("cible_valeur")
        id_action = data.get("id_action")
        if cible_type not in ("matricule", "atelier"):
            return jsonify({"success": False, "error": "cible_type doit être 'matricule' ou 'atelier'"}), 400
        if cible_valeur is None or (cible_type == "atelier" and not str(cible_valeur).strip()):
            return jsonify({"success": False, "error": "cible_valeur requis"}), 400
        try:
            id_action = int(id_action)
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "id_action invalide"}), 400
        result = ajouter_droit(cible_type, cible_valeur, id_action)
        if result["success"]:
            return jsonify(result)
        return jsonify(result), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@projet22_bp.route('/api/droits/supprimer/<int:droit_id>', methods=['DELETE'])
def api_droits_supprimer(droit_id):
    """API pour supprimer un droit"""
    err = _droits_require_super()
    if err: return err
    try:
        result = supprimer_droit(droit_id)
        if result["success"]:
            return jsonify(result)
        return jsonify(result), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
