# -*- coding: utf-8 -*-
"""
Routes Projet 26 – Gestion des formations.
Préfixe /projet26
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session

from logic.auth import login_required, get_user_sections, has_project_access, is_super_user, get_current_user
from logic import projet26 as p26

projet26_bp = Blueprint('projet26', __name__, url_prefix='/projet26')

PROJET26_SECTION_KEYS = {
    'Demande de formation': 'demande',
    'Évaluation de formation': 'evaluation',
    'Liste des formations': 'formations',
}


def _ensure_tables():
    try:
        p26.init_web_formation_tables()
    except Exception as e:
        print(f'[Projet26] init tables: {e}')


def get_projet26_allowed_sections():
    if is_super_user():
        return list(PROJET26_SECTION_KEYS.values())
    raw = get_user_sections(26)
    allowed = []
    for s in raw:
        nom = (s.get('nom') or s.get('Nom') or '').strip()
        key = PROJET26_SECTION_KEYS.get(nom)
        if not key and nom:
            nl = nom.lower()
            if 'demande' in nl and 'formation' in nl:
                key = 'demande'
            elif 'évaluation' in nl or 'evaluation' in nl:
                key = 'evaluation'
            elif 'liste' in nl and 'formation' in nl:
                key = 'formations'
        if key and key not in allowed:
            allowed.append(key)
    if is_super_user() and not allowed:
        return list(PROJET26_SECTION_KEYS.values())
    return allowed


def render_projet26(section=None, **kwargs):
    mat = session.get('matricule')
    pers = p26.get_person(mat) if mat else None
    kwargs.update(
        section=section,
        allowed_sections=get_projet26_allowed_sections(),
        is_rh=p26.is_rh(mat, is_super_user()),
        is_super=is_super_user(),
        matricule_connecte=mat,
        manager_label=pers['label'] if pers else (get_current_user() or ''),
        manager_matricule=mat,
        personel_list=p26.list_personel_pour_demande(mat, is_super_user()),
        equipe_matricules=p26.get_equipe_manager_matricules(mat, is_super_user()),
    )
    return render_template('projet26.html', **kwargs)


@projet26_bp.before_request
def _before():
    _ensure_tables()
    p26.ensure_projet26_in_web_projets()
    try:
        p26.process_rappels_eval_froid()
    except Exception as e:
        print(f'[Projet26] rappels: {e}')


@projet26_bp.route('/')
@login_required
def index():
    if not has_project_access(26) and not is_super_user():
        return redirect(url_for('index'))
    return render_projet26(section=None)


@projet26_bp.route('/api/session-info')
@login_required
def api_session_info():
    mat = session.get('matricule')
    return jsonify({
        'matricule': mat,
        'is_rh': p26.is_rh(mat, is_super_user()),
        'is_super': is_super_user(),
    })


@projet26_bp.route('/api/personel')
@login_required
def api_personel():
    return jsonify(p26.list_personel_actifs(request.args.get('q', '')))


@projet26_bp.route('/api/equipe-demande')
@login_required
def api_equipe_demande():
    mat = session.get('matricule')
    return jsonify({
        'personel': p26.list_personel_pour_demande(mat, is_super_user()),
        'equipe_matricules': p26.get_equipe_manager_matricules(mat, is_super_user()),
    })


@projet26_bp.route('/api/notifications')
@login_required
def api_notifications():
    mat = session.get('matricule')
    return jsonify(p26.list_notifications(mat, lu=False))


@projet26_bp.route('/api/notifications/lire', methods=['POST'])
@login_required
def api_notifications_lire():
    p26.marquer_notifications_lues(session.get('matricule'))
    return jsonify({'ok': True})


@projet26_bp.route('/api/demandes', methods=['GET', 'POST'])
@login_required
def api_demandes():
    if request.method == 'GET':
        statut = request.args.get('statut')
        return jsonify(p26.list_demandes(session.get('matricule'), is_super_user(), statut))
    data = request.get_json() or {}
    try:
        row, err = p26.create_demande(data, session.get('matricule'), is_super_user())
    except Exception as e:
        print(f'[Projet26] api_demandes POST: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erreur serveur lors de l\'enregistrement.'}), 500
    if err:
        return jsonify({'error': err}), 400
    return jsonify(row), 201


@projet26_bp.route('/api/demandes/<int:demande_id>', methods=['GET', 'PUT'])
@login_required
def api_demande_detail(demande_id):
    if not p26._demande_visible_for(session.get('matricule'), demande_id, is_super_user()):
        return jsonify({'error': 'Non autorisé'}), 403
    if request.method == 'PUT':
        if not p26._can_edit_demande(session.get('matricule'), demande_id, is_super_user()):
            return jsonify({'error': 'Modification non autorisée ou demande déjà traitée.'}), 403
        data = request.get_json() or {}
        try:
            row, err = p26.update_demande(
                demande_id, data, session.get('matricule'), is_super_user(),
            )
        except Exception as e:
            print(f'[Projet26] api_demande PUT: {e}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Erreur serveur lors de la modification.'}), 500
        if err:
            return jsonify({'error': err}), 400
        return jsonify(row)
    d = p26.get_demande(demande_id)
    if not d:
        return jsonify({'error': 'Introuvable'}), 404
    return jsonify(d)


@projet26_bp.route('/api/demandes/<int:demande_id>/valider', methods=['POST'])
@login_required
def api_demande_valider(demande_id):
    data = request.get_json() or {}
    row, err = p26.valider_demande_rh(demande_id, data, session.get('matricule'), is_super_user())
    if err:
        return jsonify({'error': err}), 400
    return jsonify(row)


@projet26_bp.route('/api/demandes/<int:demande_id>/refuser', methods=['POST'])
@login_required
def api_demande_refuser(demande_id):
    data = request.get_json() or {}
    row, err = p26.refuser_demande_rh(
        demande_id,
        data.get('commentaire_refus'),
        session.get('matricule'),
        is_super_user(),
    )
    if err:
        return jsonify({'error': err}), 400
    return jsonify(row)


@projet26_bp.route('/api/formations')
@login_required
def api_formations():
    return jsonify(p26.list_formations(session.get('matricule'), is_super_user()))


@projet26_bp.route('/api/formations/<int:formation_id>')
@login_required
def api_formation_detail(formation_id):
    f = p26.get_formation(formation_id)
    if not f:
        return jsonify({'error': 'Introuvable'}), 404
    return jsonify(f)


@projet26_bp.route('/api/formations-eval-admin')
@login_required
def api_formations_eval_admin():
    return jsonify(p26.formations_pour_eval_admin(session.get('matricule'), is_super_user()))


@projet26_bp.route('/api/evaluations-admin')
@login_required
def api_evaluations_admin():
    fid = request.args.get('id_formation', type=int)
    return jsonify(p26.list_evaluations_admin(session.get('matricule'), is_super_user(), fid))


@projet26_bp.route('/api/evaluations-admin/participant')
@login_required
def api_evaluations_participant():
    fid = request.args.get('id_formation', type=int)
    part = request.args.get('matricule_participant', type=int)
    if not fid or not part:
        return jsonify({'error': 'Formation et participant obligatoires.'}), 400
    return jsonify(p26.get_evals_participant(fid, part))


@projet26_bp.route('/api/evaluations-admin/chaud', methods=['POST'])
@login_required
def api_eval_chaud():
    data = request.get_json() or {}
    row, err = p26.save_eval_admin_chaud(data, session.get('matricule'), is_super_user())
    if err:
        return jsonify({'error': err}), 400
    return jsonify(row)


@projet26_bp.route('/api/evaluations-admin/froid', methods=['POST'])
@login_required
def api_eval_froid():
    data = request.get_json() or {}
    row, err = p26.save_eval_admin_froid(data, session.get('matricule'), is_super_user())
    if err:
        return jsonify({'error': err}), 400
    return jsonify(row)


def ensure_projet26_in_web_projets():
    p26.ensure_projet26_in_web_projets()
