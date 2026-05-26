# -*- coding: utf-8 -*-
"""
Routes Projet 25 – Gestion des congés et autorisations de sortie.
Préfixe /projet25 — ne modifie aucun autre projet.
"""
import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename

from logic.auth import login_required, get_current_user, get_user_sections, has_project_access, is_super_user
from logic import projet25 as p25

projet25_bp = Blueprint('projet25', __name__, url_prefix='/projet25')

PROJET25_SECTION_KEYS = {
    'Demande de congé': 'conge',
    "Demande d'autorisation de sortie": 'sortie',
    'Mes demandes': 'mes',
    'Demandes à valider': 'valider',
    'Vue RH': 'rh',
    'Statistiques': 'stats',
    'Organigramme validateurs': 'validateurs',
    'Jours fériés': 'feries',
}


def _ensure_tables():
    try:
        p25.init_web_conge_tables()
    except Exception as e:
        print(f'[Projet25] init tables: {e}')


def get_projet25_allowed_sections():
    if is_super_user():
        return list(PROJET25_SECTION_KEYS.values())
    raw = get_user_sections(25)
    allowed = []
    for s in raw:
        nom = (s.get('nom') or s.get('Nom') or '').strip()
        key = PROJET25_SECTION_KEYS.get(nom)
        if not key and nom:
            nl = nom.lower()
            if 'congé' in nl and 'sortie' not in nl and 'demande' in nl:
                key = 'conge'
            elif 'autorisation' in nl or ('sortie' in nl and 'demande' in nl):
                key = 'sortie'
            elif 'mes demandes' in nl:
                key = 'mes'
            elif 'valider' in nl:
                key = 'valider'
            elif 'vue rh' in nl or nom.lower() == 'rh':
                key = 'rh'
            elif 'statist' in nl:
                key = 'stats'
            elif 'validateur' in nl or 'organigramme' in nl:
                key = 'validateurs'
            elif 'féri' in nl or 'ferie' in nl:
                key = 'feries'
        if key and key not in allowed:
            allowed.append(key)
    if is_super_user() and not allowed:
        return list(PROJET25_SECTION_KEYS.values())
    return allowed


def render_projet25(section=None, **kwargs):
    allowed = get_projet25_allowed_sections()
    mat = session.get('matricule')
    kwargs.update(
        section=section,
        allowed_sections=allowed,
        is_rh=p25.is_rh(mat, is_super_user()),
        is_super=is_super_user(),
        matricule_connecte=mat,
        matricule_rh=p25.MATRICULE_RH,
        personel_list=p25.list_personel_actifs(''),
    )
    return render_template('projet25.html', **kwargs)


@projet25_bp.before_request
def _before():
    _ensure_tables()
    p25.ensure_projet25_in_web_projets()
    try:
        p25.sync_official_conge_types()
        p25.migrate_feries_columns()
    except Exception as e:
        print(f'[Projet25] sync types: {e}')


@projet25_bp.route('/')
@login_required
def index():
    if not has_project_access(25) and not is_super_user():
        return redirect(url_for('index'))
    return render_projet25(section=None)


# ---------- API ----------

@projet25_bp.route('/api/types-conge')
@login_required
def api_types_conge():
    return jsonify(p25.list_types_conge())


@projet25_bp.route('/api/personel')
@login_required
def api_personel():
    q = request.args.get('q', '')
    return jsonify(p25.list_personel_actifs(q))


@projet25_bp.route('/api/session-info')
@login_required
def api_session_info():
    mat = session.get('matricule')
    return jsonify({
        'matricule': mat,
        'is_rh': p25.is_rh(mat, is_super_user()),
        'is_super': is_super_user(),
    })


@projet25_bp.route('/api/solde')
@login_required
def api_solde():
    mat = request.args.get('matricule') or session.get('matricule')
    annee = request.args.get('annee', type=int)
    return jsonify(p25.get_solde(mat, annee))


@projet25_bp.route('/api/calcul-jours-ouvres')
@login_required
def api_calcul_jours():
    d1 = request.args.get('date_debut')
    d2 = request.args.get('date_fin')
    demi = request.args.get('demi_journee')
    nb = p25.compter_jours_ouvres(d1, d2, demi or None)
    return jsonify({'nb_jours_ouvres': nb})


@projet25_bp.route('/api/demandes')
@login_required
def api_demandes():
    scope = request.args.get('scope', 'mes')
    filtre = {
        'type_demande': request.args.get('type'),
        'statut': request.args.get('statut'),
    }
    mat = session.get('matricule')
    rows = p25.list_demandes(filtre, mat, scope, is_super_user())
    return jsonify(rows)


@projet25_bp.route('/api/demandes/<int:demande_id>')
@login_required
def api_demande_detail(demande_id):
    d = p25.get_demande(demande_id)
    if not d:
        return jsonify({'error': 'Introuvable'}), 404
    if not p25.user_can_see_demande(session.get('matricule'), d, is_super_user()):
        return jsonify({'error': 'Accès refusé'}), 403
    return jsonify(d)


@projet25_bp.route('/api/demandes/conge', methods=['POST'])
@login_required
def api_creer_conge():
    if request.files and request.files.get('fichier'):
        data = request.form.to_dict()
        f = request.files['fichier']
        if f.filename:
            fn = secure_filename(f.filename)
            base, ext = os.path.splitext(fn)
            fn = f"{base}_{os.urandom(4).hex()}{ext}"
            f.save(os.path.join(p25.upload_dir(), fn))
            data['fichier_joint'] = fn
        if data.get('id_type_conge'):
            data['id_type_conge'] = int(data['id_type_conge'])
        if data.get('matricule_demandeur'):
            data['matricule_demandeur'] = int(data['matricule_demandeur'])
    else:
        data = request.get_json() or {}
    mat = session.get('matricule')
    dem, err = p25.creer_demande_conge(
        data, mat, p25.is_rh(mat, is_super_user()), is_super_user()
    )
    if err:
        return jsonify({'error': err}), 400
    return jsonify(dem), 201


@projet25_bp.route('/api/demandes/sortie', methods=['POST'])
@login_required
def api_creer_sortie():
    try:
        data = request.get_json() or {}
        if data.get('matricule_demandeur'):
            data['matricule_demandeur'] = int(data['matricule_demandeur'])
        mat = session.get('matricule')
        if mat is None:
            return jsonify({'error': 'Session invalide : reconnectez-vous.'}), 401
        dem, err = p25.creer_demande_sortie(
            data, mat, p25.is_rh(mat, is_super_user()), is_super_user()
        )
        if err:
            return jsonify({'error': err}), 400
        return jsonify(dem), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@projet25_bp.route('/api/demandes/<int:demande_id>/annuler', methods=['POST'])
@login_required
def api_annuler(demande_id):
    dem, err = p25.annuler_demande(demande_id, session.get('matricule'), is_super_user())
    if err:
        return jsonify({'error': err}), 400
    return jsonify(dem)


@projet25_bp.route('/api/demandes/<int:demande_id>/valider', methods=['POST'])
@login_required
def api_valider(demande_id):
    dem, err = p25.valider_demande(demande_id, session.get('matricule'), is_super_user())
    if err:
        return jsonify({'error': err}), 400
    return jsonify(dem)


@projet25_bp.route('/api/demandes/<int:demande_id>/refuser', methods=['POST'])
@login_required
def api_refuser(demande_id):
    data = request.get_json() or {}
    dem, err = p25.refuser_demande(
        demande_id, session.get('matricule'), data.get('commentaire_refus'), is_super_user()
    )
    if err:
        return jsonify({'error': err}), 400
    return jsonify(dem)


@projet25_bp.route('/api/demandes/<int:demande_id>/devalider', methods=['POST'])
@login_required
def api_devalider(demande_id):
    dem, err = p25.devalider_demande(demande_id, session.get('matricule'), is_super_user())
    if err:
        return jsonify({'error': err}), 400
    return jsonify(dem)


@projet25_bp.route('/api/notifications')
@login_required
def api_notifications():
    non_lues = request.args.get('non_lues') == '1'
    return jsonify(p25.get_notifications(session.get('matricule'), non_lues))


@projet25_bp.route('/api/notifications/lire', methods=['POST'])
@login_required
def api_notifications_lire():
    data = request.get_json() or {}
    p25.marquer_notifications_lues(session.get('matricule'), data.get('ids'))
    return jsonify({'ok': True})


@projet25_bp.route('/api/stats')
@login_required
def api_stats():
    if not (p25.is_rh(session.get('matricule'), is_super_user()) or is_super_user()):
        return jsonify({'error': 'Accès refusé'}), 403
    return jsonify(p25.stats_tableau_bord())


@projet25_bp.route('/api/validateurs', methods=['GET', 'POST'])
@login_required
def api_validateurs():
    if not (p25.is_rh(session.get('matricule'), is_super_user()) or is_super_user()):
        return jsonify({'error': 'Accès refusé'}), 403
    if request.method == 'GET':
        return jsonify(p25.list_validateurs_liens())
    data = request.get_json() or {}
    ok, err = p25.save_validateur_lien(data)
    if err:
        return jsonify({'error': err}), 400
    return jsonify({'ok': ok})


@projet25_bp.route('/api/validateurs/<int:lid>', methods=['DELETE'])
@login_required
def api_validateur_delete(lid):
    if not (p25.is_rh(session.get('matricule'), is_super_user()) or is_super_user()):
        return jsonify({'error': 'Accès refusé'}), 403
    p25.delete_validateur_lien(lid)
    return jsonify({'ok': True})


@projet25_bp.route('/api/rh-utilisateurs', methods=['GET', 'POST'])
@login_required
def api_rh_utilisateurs():
    if not (p25.is_rh(session.get('matricule'), is_super_user()) or is_super_user()):
        return jsonify({'error': 'Accès refusé'}), 403
    if request.method == 'GET':
        return jsonify(p25.list_rh_utilisateurs())
    data = request.get_json() or {}
    ok, err = p25.add_rh_matricule(data.get('matricule'))
    if err:
        return jsonify({'error': err}), 400
    return jsonify({'ok': ok})


@projet25_bp.route('/api/rh-utilisateurs/<int:matricule>', methods=['DELETE'])
@login_required
def api_rh_utilisateur_delete(matricule):
    if not (p25.is_rh(session.get('matricule'), is_super_user()) or is_super_user()):
        return jsonify({'error': 'Accès refusé'}), 403
    ok, err = p25.remove_rh_matricule(matricule)
    if err:
        return jsonify({'error': err}), 400
    return jsonify({'ok': ok})


@projet25_bp.route('/api/feries', methods=['GET', 'POST'])
@login_required
def api_feries():
    if not (p25.is_rh(session.get('matricule'), is_super_user()) or is_super_user()):
        return jsonify({'error': 'Accès refusé'}), 403
    if request.method == 'GET':
        annee = request.args.get('annee', type=int)
        if request.args.get('config') == '1':
            return jsonify(p25.get_feries_config(annee))
        return jsonify(p25.list_jours_feries(annee))
    data = request.get_json() or {}
    if data.get('code') and data.get('date_debut'):
        ok, err = p25.save_ferie_variable(
            data['code'],
            data.get('annee') or __import__('datetime').date.today().year,
            data['date_debut'],
        )
        if err:
            return jsonify({'error': err}), 400
        return jsonify({'ok': ok})
    p25.save_jour_ferie(data)
    return jsonify({'ok': True})


@projet25_bp.route('/api/feries/variable', methods=['DELETE'])
@login_required
def api_ferie_variable_delete():
    if not (p25.is_rh(session.get('matricule'), is_super_user()) or is_super_user()):
        return jsonify({'error': 'Accès refusé'}), 403
    code = request.args.get('code')
    annee = request.args.get('annee', type=int)
    if not code or not annee:
        return jsonify({'error': 'code et annee requis'}), 400
    p25.delete_ferie_variable(code, annee)
    return jsonify({'ok': True})


@projet25_bp.route('/api/feries/<int:fid>', methods=['DELETE'])
@login_required
def api_ferie_delete(fid):
    if not (p25.is_rh(session.get('matricule'), is_super_user()) or is_super_user()):
        return jsonify({'error': 'Accès refusé'}), 403
    p25.delete_jour_ferie(fid)
    return jsonify({'ok': True})


@projet25_bp.route('/api/soldes', methods=['GET', 'POST'])
@login_required
def api_soldes():
    if not (p25.is_rh(session.get('matricule'), is_super_user()) or is_super_user()):
        return jsonify({'error': 'Accès refusé'}), 403
    if request.method == 'GET':
        annee = request.args.get('annee', type=int)
        return jsonify(p25.list_soldes(annee))
    data = request.get_json() or {}
    p25.save_solde(data['matricule'], data.get('annee') or __import__('datetime').date.today().year, float(data['solde_jours']))
    return jsonify({'ok': True})


@projet25_bp.route('/api/staff-admin', methods=['GET', 'POST'])
@login_required
def api_staff_admin():
    if not (p25.is_rh(session.get('matricule'), is_super_user()) or is_super_user()):
        return jsonify({'error': 'Accès refusé'}), 403
    if request.method == 'GET':
        return jsonify(p25.list_staff_admin())
    data = request.get_json() or {}
    p25.toggle_staff_admin(data['matricule'], data.get('add', True))
    return jsonify({'ok': True})


@projet25_bp.route('/api/staff-admin/<int:matricule>', methods=['DELETE'])
@login_required
def api_staff_admin_del(matricule):
    if not (p25.is_rh(session.get('matricule'), is_super_user()) or is_super_user()):
        return jsonify({'error': 'Accès refusé'}), 403
    p25.toggle_staff_admin(matricule, False)
    return jsonify({'ok': True})


@projet25_bp.route('/uploads/<path:filename>')
@login_required
def serve_upload(filename):
    return send_from_directory(p25.upload_dir(), filename)


def ensure_projet25_in_web_projets():
    p25.ensure_projet25_in_web_projets()
