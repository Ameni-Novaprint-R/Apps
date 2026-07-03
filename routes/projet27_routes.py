# -*- coding: utf-8 -*-
"""
Routes Projet 27 – Crédit Leasing.
Préfixe /projet27
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session

from logic.auth import login_required, has_project_access, is_super_user, get_user_sections
from logic import projet27 as p27

projet27_bp = Blueprint('projet27', __name__, url_prefix='/projet27')

PROJET27_SECTION_KEYS = {
    'Tableau de bord': 'tableau',
    'Gestion des crédits': 'credits',
    'Nouveau crédit': 'nouveau',
}


def _ensure_tables():
    try:
        p27.init_web_credit_tables()
    except Exception as e:
        print(f'[Projet27] init tables: {e}')


def get_projet27_allowed_sections():
    if is_super_user():
        return list(PROJET27_SECTION_KEYS.values())
    raw = get_user_sections(27)
    allowed = []
    for s in raw:
        nom = (s.get('nom') or s.get('Nom') or '').strip()
        key = PROJET27_SECTION_KEYS.get(nom)
        if not key and nom:
            nl = nom.lower()
            if 'tableau' in nl or 'bord' in nl:
                key = 'tableau'
            elif 'gestion' in nl and 'crédit' in nl or 'gestion' in nl and 'credit' in nl:
                key = 'credits'
            elif 'nouveau' in nl and ('crédit' in nl or 'credit' in nl):
                key = 'nouveau'
        if key and key not in allowed:
            allowed.append(key)
    if is_super_user() and not allowed:
        return list(PROJET27_SECTION_KEYS.values())
    return allowed


def render_projet27(section=None, **kwargs):
    allowed = get_projet27_allowed_sections()
    if section is not None and section not in allowed:
        if allowed:
            first = allowed[0]
            if first == 'tableau':
                return redirect(url_for('projet27.tableau'))
            if first == 'credits':
                return redirect(url_for('projet27.credits'))
            if first == 'nouveau':
                return redirect(url_for('projet27.nouveau_credit'))
        return redirect(url_for('projet27.index'))
    kwargs['section'] = section
    kwargs['allowed_sections'] = allowed
    kwargs['is_super'] = is_super_user()
    return render_template('projet27.html', **kwargs)


@projet27_bp.before_request
def _projet27_before():
    _ensure_tables()


@projet27_bp.route('/')
@login_required
def index():
    if not has_project_access(27) and not is_super_user():
        return redirect(url_for('index'))
    allowed = get_projet27_allowed_sections()
    if 'tableau' in allowed:
        return redirect(url_for('projet27.tableau'))
    if allowed:
        first = allowed[0]
        if first == 'credits':
            return redirect(url_for('projet27.credits'))
        if first == 'nouveau':
            return redirect(url_for('projet27.nouveau_credit'))
    return render_projet27(section=None)


@projet27_bp.route('/tableau')
@login_required
def tableau():
    if not has_project_access(27) and not is_super_user():
        return redirect(url_for('index'))
    return render_projet27(section='tableau')


@projet27_bp.route('/credits')
@login_required
def credits():
    if not has_project_access(27) and not is_super_user():
        return redirect(url_for('index'))
    return render_projet27(section='credits')


@projet27_bp.route('/nouveau-credit')
@login_required
def nouveau_credit():
    if not has_project_access(27) and not is_super_user():
        return redirect(url_for('index'))
    return render_projet27(section='nouveau')


# --- API ---

@projet27_bp.route('/api/referentiels')
@login_required
def api_referentiels():
    return jsonify({
        'banques': p27.list_banques(actif_only=False),
        'types': p27.list_types(),
        'jours_prelevement': list(p27.JOURS_PRELEVEMENT),
        'seuil_total': float(p27.get_seuil_total()),
        'annees': p27.get_annees_disponibles(),
    })


@projet27_bp.route('/api/tableau')
@login_required
def api_tableau():
    annee_param = (request.args.get('annee') or '').strip()
    if annee_param:
        data = p27.get_tableau(annee=int(annee_param))
    else:
        data = p27.get_tableau(annee=None)
    return jsonify(data)


@projet27_bp.route('/api/credits')
@login_required
def api_credits():
    actif = request.args.get('actif')
    actif_only = actif in ('1', 'true', 'oui')
    type_code = request.args.get('type') or None
    id_banque = request.args.get('banque', type=int)
    return jsonify(p27.list_credits(
        actif_only=actif_only,
        type_code=type_code,
        id_banque=id_banque,
    ))


@projet27_bp.route('/api/credits/<int:credit_id>')
@login_required
def api_credit_detail(credit_id):
    c = p27.get_credit(credit_id)
    if not c:
        return jsonify({'error': 'Crédit introuvable'}), 404
    return jsonify(c)


@projet27_bp.route('/api/credits', methods=['POST'])
@login_required
def api_credit_create():
    data = request.get_json(silent=True) or {}
    user = session.get('username') or session.get('nom') or str(session.get('matricule', ''))
    credit, err = p27.create_credit(data, utilisateur=user)
    if err:
        return jsonify({'success': False, 'error': err}), 400
    return jsonify({'success': True, 'credit': credit})


@projet27_bp.route('/api/credits/<int:credit_id>', methods=['PUT'])
@login_required
def api_credit_update(credit_id):
    data = request.get_json(silent=True) or {}
    user = session.get('username') or session.get('nom') or str(session.get('matricule', ''))
    credit, err = p27.update_credit(credit_id, data, utilisateur=user)
    if err:
        return jsonify({'success': False, 'error': err}), 400
    return jsonify({'success': True, 'credit': credit})


@projet27_bp.route('/api/credits/<int:credit_id>', methods=['DELETE'])
@login_required
def api_credit_delete(credit_id):
    ok, err = p27.delete_credit(credit_id)
    if not ok:
        return jsonify({'success': False, 'error': err}), 404
    return jsonify({'success': True})


@projet27_bp.route('/api/credits/<int:credit_id>/generer-echeances', methods=['POST'])
@login_required
def api_generer_echeances(credit_id):
    data = request.get_json(silent=True) or {}
    remplacer = data.get('remplacer', True)
    n, err = p27.generer_echeances(credit_id, remplacer=remplacer)
    if err:
        return jsonify({'success': False, 'error': err}), 400
    return jsonify({'success': True, 'nb_echeances': n})


@projet27_bp.route('/api/param/seuil', methods=['PUT'])
@login_required
def api_set_seuil():
    if not is_super_user():
        return jsonify({'error': 'Accès réservé'}), 403
    data = request.get_json(silent=True) or {}
    try:
        v = p27.set_seuil_total(data.get('valeur'))
        return jsonify({'success': True, 'seuil_total': v})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


def ensure_projet27_in_web_projets():
    p27.ensure_projet27_in_web_projets()
