#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Application Flask principale - Portail Novaprint
"""
from local_env import load_project_env

load_project_env()

from datetime import datetime
from flask import Flask, render_template, jsonify
from logic.auth import is_authenticated, get_current_user, get_user_projects, get_user_sections, has_action_access, is_super_user

app = Flask(__name__)
app.secret_key = 'portail-novaprint-secret-key'

# Mapping NumProj -> URL de base (cas spéciaux : projet6 sans /, projet7 = /import_facture)
NUM_TO_URL = {
    1: '/projet1/',
    2: '/projet2/',
    3: '/projet3/',
    4: '/projet4/',
    5: '/projet5/',
    6: '/projet6',
    7: '/import_facture',
    8: '/projet8/',
    9: '/projet9/',
    10: '/projet10/',
    11: '/projet11',
    12: '/projet12',
    13: '/projet13/',
    14: '/projet14/',
    15: '/projet15/',
    16: '/projet16/',
    17: '/projet17/',
    18: '/projet18/',
    19: '/projet19/',
    20: '/projet20/',
    21: '/projet21/',
    22: '/projet22/',
    23: '/projet23/',
    24: '/projet24/',
    25: '/projet25/',
    26: '/projet26/',
}


@app.route('/api/navigation-menu')
def api_navigation_menu():
    """API pour le menu déroulant des projets (base.html, projet19, etc.)"""
    try:
        from logic.project_routes import get_project_icon, get_project_url
        # Garantir que le Projet 24 est dans WEB_PROJETS avant de récupérer la liste
        try:
            from routes.projet24_routes import ensure_projet24_in_web_projets
            ensure_projet24_in_web_projets()
        except Exception as e:
            print(f"[navigation-menu] ensure_projet24: {e}")
        try:
            from routes.projet25_routes import ensure_projet25_in_web_projets
            ensure_projet25_in_web_projets()
        except Exception as e:
            print(f"[navigation-menu] ensure_projet25: {e}")
        try:
            from routes.projet26_routes import ensure_projet26_in_web_projets
            ensure_projet26_in_web_projets()
        except Exception as e:
            print(f"[navigation-menu] ensure_projet26: {e}")
        projects_raw = get_user_projects()
        if not projects_raw:
            return jsonify({'projects': []})
        projects = []
        has_24 = False
        has_25 = False
        has_26 = False
        for p in projects_raw:
            num = p.get('num') or p.get('NumProj')
            if num == 24:
                has_24 = True
            if num == 25:
                has_25 = True
            if num == 26:
                has_26 = True
            url = get_project_url(num) or NUM_TO_URL.get(num, f'/projet{num}/' if num else '#')
            sections_raw = get_user_sections(p.get('id') or num)
            sections = [{'nom': s.get('nom', s.get('Nom', '')), 'url': url} for s in sections_raw]
            nom = p.get('nom', p.get('Nom', ''))
            if num == 23:
                nom = 'Projet 23 – TBD de la situation de la trésorerie'
            if num == 24:
                nom = 'Formes de Découpe'
            if num == 25:
                nom = 'Gestion des congés et autorisations de sortie'
            if num == 26:
                nom = 'Gestion des formations'
            projects.append({
                'id': p.get('id'),
                'url': url,
                'icon': get_project_icon(num) if num else '📌',
                'nom': nom,
                'sections': sections if sections else None,
            })
        # Si le Projet 24 n'est pas dans la liste (droits ou BDD), l'ajouter pour le menu
        if not has_24 and is_authenticated():
            projects.append({
                'id': 24,
                'url': get_project_url(24) or '/projet24/',
                'icon': get_project_icon(24),
                'nom': 'Formes de Découpe',
                'sections': None,
            })
        if not has_25 and is_authenticated():
            projects.append({
                'id': 25,
                'url': get_project_url(25) or '/projet25/',
                'icon': get_project_icon(25),
                'nom': 'Gestion des congés et autorisations de sortie',
                'sections': None,
            })
        if not has_26 and is_authenticated():
            projects.append({
                'id': 26,
                'url': get_project_url(26) or '/projet26/',
                'icon': get_project_icon(26),
                'nom': 'Gestion des formations',
                'sections': None,
            })
        return jsonify({'projects': projects})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'projects': []}), 500


@app.context_processor
def inject_template_context():
    """Injecte is_authenticated, get_current_user, has_action_access, is_super_user, get_project_url, get_project_icon et now dans tous les templates"""
    from logic.project_routes import get_project_url, get_project_icon
    return {
        'is_authenticated': is_authenticated,
        'get_current_user': get_current_user,
        'has_action_access': has_action_access,
        'is_super_user': is_super_user,
        'get_project_url': get_project_url,
        'get_project_icon': get_project_icon,
        'now': datetime.now(),
    }


@app.route('/')
def index():
    """Page d'accueil du portail"""
    user_projects = get_user_projects() if is_authenticated() else []
    for p in user_projects:
        num = p.get('num') or p.get('NumProj')
        if num == 23:
            p['nom'] = 'Tableau de bord de la situation de la trésorerie'
        if num == 26:
            p['nom'] = 'Gestion des formations'
    return render_template('index.html', user_projects=user_projects)


# Blueprints - Auth
from routes.auth_routes import auth_bp
app.register_blueprint(auth_bp)

# Blueprints - Projets (logic)
from logic.projet1 import bp as projet1_bp
from logic.projet2 import bp as projet2_bp
from logic.projet3 import bp as projet3_bp
from logic.projet4 import bp as projet4_bp
from logic.projet5 import bp as projet5_bp
from logic.projet8 import bp as projet8_bp
from logic.projet9 import bp as projet9_bp
from logic.projet10 import bp as projet10_bp
from logic.projet7 import projet7_bp
from logic.projet6 import projet6_bp

app.register_blueprint(projet1_bp)
app.register_blueprint(projet2_bp)
app.register_blueprint(projet3_bp)
app.register_blueprint(projet4_bp)
app.register_blueprint(projet5_bp)
app.register_blueprint(projet8_bp)
app.register_blueprint(projet9_bp)
app.register_blueprint(projet10_bp)
app.register_blueprint(projet7_bp)
app.register_blueprint(projet6_bp)

# Blueprints - Projets (routes)
from routes.projet11_routes import projet11_bp
from routes.projet12_routes import projet12_bp
from routes.projet13_routes import projet13_bp
from routes.projet14_routes import projet14_bp
from routes.projet15_routes import projet15_bp
from routes.projet16_routes import projet16_bp
from routes.projet17_routes import projet17_bp
from routes.projet18_routes import projet18_bp
from routes.projet19_routes import projet19_bp
from routes.projet20_routes import projet20_bp
from routes.projet21_routes import projet21_bp
from routes.projet22_routes import projet22_bp
from routes.projet23_routes import projet23_bp
from routes.projet24_routes import projet24_bp
from routes.projet25_routes import projet25_bp
from routes.projet26_routes import projet26_bp
from routes.admin_routes import admin_bp
from routes.crystal_reports_routes import crystal_reports
from routes.renommer_table_route import renommer_bp

app.register_blueprint(projet11_bp)
app.register_blueprint(projet12_bp)
app.register_blueprint(projet13_bp)
app.register_blueprint(projet14_bp)
app.register_blueprint(projet15_bp)
app.register_blueprint(projet16_bp)
app.register_blueprint(projet17_bp)
app.register_blueprint(projet18_bp)
app.register_blueprint(projet19_bp)
app.register_blueprint(projet20_bp)
app.register_blueprint(projet21_bp)
app.register_blueprint(projet22_bp)
app.register_blueprint(projet23_bp)
app.register_blueprint(projet24_bp)
app.register_blueprint(projet25_bp)
app.register_blueprint(projet26_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(crystal_reports)
app.register_blueprint(renommer_bp)


@app.before_request
def _ensure_projets_web_menu():
    """Une fois par démarrage : projets 24/25 dans WEB_PROJETS si absents (menu + accueil)."""
    if not getattr(app, '_projet24_web_projets_ensured', False):
        try:
            from routes.projet24_routes import ensure_projet24_in_web_projets
            ensure_projet24_in_web_projets()
        except Exception as e:
            print(f"[Projet 24] ensure_projet24_in_web_projets: {e}")
        app._projet24_web_projets_ensured = True
    if not getattr(app, '_projet25_web_projets_ensured', False):
        try:
            from routes.projet25_routes import ensure_projet25_in_web_projets
            ensure_projet25_in_web_projets()
        except Exception as e:
            print(f"[Projet 25] ensure_projet25_in_web_projets: {e}")
        app._projet25_web_projets_ensured = True
    if not getattr(app, '_projet26_web_projets_ensured', False):
        try:
            from routes.projet26_routes import ensure_projet26_in_web_projets
            ensure_projet26_in_web_projets()
        except Exception as e:
            print(f"[Projet 26] ensure_projet26_in_web_projets: {e}")
        app._projet26_web_projets_ensured = True


if __name__ == '__main__':
    try:
        from routes.projet24_routes import register_formes_tables, ensure_projet24_in_web_projets
        register_formes_tables()
        ensure_projet24_in_web_projets()
    except Exception as e:
        print(f"[Démarrage] Projet 24: {e}")
    app.run(host='0.0.0.0', port=5000, debug=True)
