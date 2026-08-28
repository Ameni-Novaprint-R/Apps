# -*- coding: utf-8 -*-
"""
Projet 29 – Suivi des connexions.
Préfixe /projet29 — consultation réservée aux super-utilisateurs.
Le heartbeat est ouvert à tout utilisateur authentifié (présence).
"""
from functools import wraps

from flask import (
    Blueprint, jsonify, redirect, render_template, request, url_for,
)

from logic.auth import is_authenticated, is_super_user, login_required
from logic import projet29 as p29

projet29_bp = Blueprint('projet29', __name__, url_prefix='/projet29')


def super_user_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_super_user():
            if request.path.startswith('/projet29/api/'):
                return jsonify({'error': 'Accès réservé aux super-utilisateurs'}), 403
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


def _client_ip():
    forwarded = (request.headers.get('X-Forwarded-For') or '').strip()
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or ''


def _ident():
    from flask import session
    return p29.identity_from_session(session)


@projet29_bp.before_request
def _ensure():
    try:
        p29.init_presence_tables()
    except Exception as e:
        print(f'[Projet 29] init: {e}')


def ensure_projet29_in_web_projets():
    p29.ensure_projet29_in_web_projets()


@projet29_bp.route('/')
@login_required
@super_user_required
def index():
    return render_template('projet29.html')


@projet29_bp.route('/api/heartbeat', methods=['POST'])
@login_required
def api_heartbeat():
    data = request.get_json(silent=True) or request.form or {}
    result = p29.heartbeat(
        ident=_ident(),
        tab_id=data.get('tab_id') or '',
        page_path=data.get('path') or request.headers.get('Referer') or '/',
        page_title=data.get('title') or '',
        ip=_client_ip(),
        user_agent=request.headers.get('User-Agent') or '',
    )
    status = 200 if result.get('ok') else 400
    return jsonify(result), status


@projet29_bp.route('/api/leave', methods=['POST'])
def api_leave():
    data = request.get_json(silent=True) or request.form or {}
    tab_id = data.get('tab_id') or ''
    ident = None
    if is_authenticated():
        ident = _ident()
    return jsonify(p29.mark_tab_closing(tab_id, ident))


@projet29_bp.route('/api/connectes')
@login_required
@super_user_required
def api_connectes():
    return jsonify({'users': p29.list_connected()})


@projet29_bp.route('/api/historique')
@login_required
@super_user_required
def api_historique():
    return jsonify({'rows': p29.list_history()})
