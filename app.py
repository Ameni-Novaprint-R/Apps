from flask import Flask, render_template, Response, session, redirect, url_for
from datetime import datetime, timezone
from logic import projet1, projet2, projet3, projet4, projet5, projet6, projet8, projet9, projet10
from logic.projet7 import projet7_bp
from routes.crystal_reports_routes import crystal_reports
from routes.projet12_routes import projet12_bp
from routes.projet13_routes import projet13_bp
from routes.projet14_routes import projet14_bp
from routes.projet15_routes import projet15_bp
from routes.projet16_routes import projet16_bp
from routes.projet17_routes import projet17_bp
from routes.projet19_routes import projet19_bp
from routes.projet20_routes import projet20_bp
from routes.projet21_routes import projet21_bp
from routes.projet22_routes import projet22_bp
from routes.admin_routes import admin_bp
from routes.renommer_table_route import renommer_bp
from routes.auth_routes import auth_bp
from logic.auth import get_user_projects, is_authenticated, is_super_user, has_project_access
import os
import json
import traceback

# Forcer le rechargement des modules - 20 Oct 2025 16:10
import importlib
import sys

# Supprimer le module du cache avant import pour forcer le rechargement
if 'routes.projet11_routes' in sys.modules:
    del sys.modules['routes.projet11_routes']
if 'logic.projet11' in sys.modules:
    del sys.modules['logic.projet11']
# Forcer le rechargement - 29 Jan 2026 - Force reload
import importlib
try:
    if 'routes.projet11_routes' in sys.modules:
        importlib.reload(sys.modules['routes.projet11_routes'])
except:
    pass





app = Flask(__name__)

# Configuration de la clé secrète pour les sessions
# IMPORTANT: Doit être défini immédiatement après la création de l'app
app.secret_key = 'vraiment-secret-et-unique'
app.config['SECRET_KEY'] = 'vraiment-secret-et-unique'  # Double définition pour compatibilité

# Injection automatique de la variable "now" dans tous les templates
@app.context_processor
def inject_now():
    return {"now": datetime.now(timezone.utc)}


# Cache des fichiers statiques (1 jour) pour éviter NS_BINDING_ABORTED sur le logo
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400

# Configuration pour Crystal Reports
app.config['CRYSTAL_REPORTS_DIR'] = os.path.join(app.root_path, 'crystalreport')

# Enregistrement des blueprints
app.register_blueprint(projet1.bp)
app.register_blueprint(projet2.bp)
app.register_blueprint(projet3.bp)
app.register_blueprint(projet4.bp)
app.register_blueprint(projet5.bp)
app.register_blueprint(projet6.projet6_bp)
app.register_blueprint(projet7_bp)
app.register_blueprint(projet8.bp)
app.register_blueprint(projet9.bp)
app.register_blueprint(projet10.bp)
# Réimporter le blueprint après nettoyage du cache
from routes.projet11_routes import projet11_bp
app.register_blueprint(projet11_bp)
print("Projet11 blueprint rechargé avec toutes les routes")
app.register_blueprint(projet12_bp)
app.register_blueprint(projet13_bp)
print("Projet13 blueprint enregistré (Projet 13 - Suivi Production)")
app.register_blueprint(projet14_bp)
app.register_blueprint(projet15_bp)
app.register_blueprint(projet16_bp)
app.register_blueprint(projet17_bp)
app.register_blueprint(crystal_reports, url_prefix='/crystal')

# Import et enregistrement du projet 18 - DOIT ETRE AVANT PROJET 19
try:
    from routes.projet18_routes import projet18_bp
    app.register_blueprint(projet18_bp)
    print("Projet18 blueprint enregistre")
except ImportError as e:
    print(f"⚠️ Attention: Impossible d'importer projet18_bp: {e}")
except Exception as e:
    print(f"❌ Erreur projet18: {e}")
    import traceback
    traceback.print_exc()

# Enregistrement du projet 19 - DOIT ETRE APRES PROJET 18
app.register_blueprint(projet19_bp)
routes_projet19 = [r.rule for r in app.url_map.iter_rules() if 'projet19' in r.rule]
print(f"Projet19 blueprint enregistre - {len(routes_projet19)} routes")

# Enregistrement du projet 20
app.register_blueprint(projet20_bp)
routes_projet20 = [r.rule for r in app.url_map.iter_rules() if 'projet20' in r.rule]
print(f"Projet20 blueprint enregistre - {len(routes_projet20)} routes")

# Enregistrement du projet 21
app.register_blueprint(projet21_bp)
print("Projet21 blueprint enregistre")

# Initialisation de la synchronisation automatique pour Projet 21
# Option 1 : Utiliser APScheduler (nécessite: pip install apscheduler)
# Option 2 : Utiliser Task Scheduler Windows (voir PROJET21_AUTO_SYNC_TASK_SCHEDULER.md)
projet21_scheduler = None
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from routes.projet21_auto_sync import run_auto_sync_and_verify, is_auto_sync_enabled
    
    projet21_scheduler = BackgroundScheduler()
    projet21_scheduler.daemonic = False
    
    # Planifier la synchronisation automatique à 05:00 AM chaque jour
    if is_auto_sync_enabled():
        projet21_scheduler.add_job(
            func=run_auto_sync_and_verify,
            trigger=CronTrigger(hour=5, minute=0),
            id='projet21_auto_sync',
            name='Synchronisation automatique Projet 21',
            replace_existing=True
        )
        print("✓ Synchronisation automatique Projet 21 planifiée à 05:00 AM (APScheduler)")
    else:
        print("⏸️ Synchronisation automatique Projet 21 désactivée")
    
    projet21_scheduler.start()
    print("✓ Scheduler APScheduler démarré pour Projet 21")
    
    # Exposer le scheduler pour les routes
    app.config['PROJET21_SCHEDULER'] = projet21_scheduler
except ImportError:
    print("⚠️ APScheduler non installé.")
    print("   Option 1: Installer APScheduler: pip install apscheduler")
    print("   Option 2: Utiliser Task Scheduler Windows (voir PROJET21_AUTO_SYNC_TASK_SCHEDULER.md)")
    print("   La synchronisation automatique peut être gérée via Task Scheduler Windows.")
except Exception as e:
    print(f"⚠️ Erreur lors de l'initialisation du scheduler Projet 21: {e}")
    import traceback
    traceback.print_exc()

# Enregistrement du projet 22
app.register_blueprint(projet22_bp)
print("Projet22 blueprint enregistre")

# Admin : init. tables WEB (WEB_PROJETS, WEB_SECTIONS)
app.register_blueprint(admin_bp)
print("Admin blueprint enregistre ( /admin/init-web-tables )")
app.register_blueprint(renommer_bp)
print("Renommer blueprint enregistre ( /admin/renommer-web-droits-acces-en-web-actions )")

# Authentification - doit être après la création de l'app
from routes.auth_routes import auth_bp
from logic.auth import get_user_projects, is_authenticated, is_super_user, has_project_access, get_user_sections, has_section_access, has_action_access
from logic.project_routes import get_project_url, get_project_name, get_project_icon
from flask import jsonify
app.register_blueprint(auth_bp)
print("Auth blueprint enregistre ( /auth/login, /auth/logout )")

# Injection des fonctions d'authentification et de droits dans tous les templates
# Doit être après l'import des fonctions d'auth
@app.context_processor
def inject_auth():
    try:
        from logic.auth import get_current_user as auth_get_current_user
        
        def get_current_user_name():
            """Helper pour obtenir le nom de l'utilisateur depuis la session"""
            try:
                user = auth_get_current_user()
                if user is None:
                    return None
                # Ancien format (dict) ou nouveau format (str)
                if isinstance(user, dict):
                    return user.get('nom') or user.get('name') or None
                return str(user)
            except Exception:
                return None
        
        return {
            "is_authenticated": is_authenticated,
            "is_super_user": is_super_user,
            "get_user_projects": get_user_projects,
            "has_project_access": has_project_access,
            "get_user_sections": get_user_sections,
            "has_section_access": has_section_access,
            "has_action_access": has_action_access,
            "get_current_user": get_current_user_name,
            "get_project_url": get_project_url,
            "get_project_name": get_project_name,
            "get_project_icon": get_project_icon
        }
    except Exception as e:
        # En cas d'erreur, retourner des valeurs par défaut pour éviter de casser les templates
        print(f"Erreur dans inject_auth: {e}")
        import traceback
        traceback.print_exc()
        return {
            "is_authenticated": lambda: False,
            "is_super_user": lambda: False,
            "get_user_projects": lambda: [],
            "has_project_access": lambda x: False,
            "get_user_sections": lambda x: [],
            "has_section_access": lambda x: False,
            "has_action_access": lambda x: False,
            "get_current_user": lambda: None,
            "get_project_url": lambda x: None,
            "get_project_name": lambda x: None,
            "get_project_icon": lambda x: '📌'
        }


@app.route("/")
def index():
    """
    Page d'accueil - affiche les projets selon les droits de l'utilisateur
    """
    try:
        # Si non authentifié, rediriger vers la page de login
        if not is_authenticated():
            return redirect(url_for('auth.login'))
        
        # Passer les projets directement au template pour éviter les appels dans le template
        try:
            user_projects = get_user_projects()
            is_super = is_super_user()
        except Exception as e:
            print(f"Erreur lors de la récupération des projets: {e}")
            import traceback
            traceback.print_exc()
            user_projects = []
            is_super = False
        
        return render_template("index.html", user_projects=user_projects, is_super=is_super)
    except Exception as e:
        # En cas d'erreur, afficher une page d'erreur ou rediriger vers login
        print(f"Erreur dans la route index: {e}")
        import traceback
        traceback.print_exc()
        try:
            return redirect(url_for('auth.login'))
        except:
            return f"<h1>Erreur</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>", 500

@app.route('/api/navigation-menu')
def api_navigation_menu():
    """
    API pour obtenir les projets et sections accessibles par l'utilisateur connecté
    Retourne une structure JSON avec les projets et leurs sections
    """
    try:
        if not is_authenticated():
            return jsonify({"error": "Non authentifié"}), 401
        
        user_projects = get_user_projects()
        projects_data = []
        
        for project in user_projects:
            project_num = project.get('num')
            project_id = project.get('id')
            
            # Obtenir l'URL du projet
            project_url = get_project_url(project_num)
            project_icon = get_project_icon(project_num)
            project_name = project.get('nom') or get_project_name(project_num) or f"Projet {project_num}"
            
            # Obtenir les sections du projet
            sections = get_user_sections(project_id) if project_id else []
            
            # Construire les données des sections avec leurs URLs
            sections_data = []
            for section in sections:
                section_id = section.get('id')
                section_nom = section.get('nom', '')
                
                # Construire l'URL de la section selon le projet
                section_url = None
                if project_url:
                    # Pour le projet 11, les sections sont gérées via des routes spécifiques
                    if project_num == 11:
                        # Mapper les noms de sections aux routes du projet 11
                        section_nom_lower = section_nom.lower()
                        try:
                            from flask import url_for
                            if 'nouvelle fiche' in section_nom_lower or ('fiche' in section_nom_lower and 'production' in section_nom_lower):
                                section_url = url_for('projet11.index')
                            elif ('liste' in section_nom_lower and 'traitements' in section_nom_lower) or section_nom_lower == 'liste des traitements':
                                section_url = url_for('projet11.liste_traitements')
                            elif 'statistiques' in section_nom_lower or 'stats' in section_nom_lower:
                                section_url = url_for('projet11.statistiques')
                            else:
                                section_url = url_for('projet11.index')
                        except Exception as e:
                            # Fallback si url_for échoue
                            section_nom_lower = section_nom.lower()
                            if 'nouvelle fiche' in section_nom_lower or ('fiche' in section_nom_lower and 'production' in section_nom_lower):
                                section_url = '/projet11/'
                            elif ('liste' in section_nom_lower and 'traitements' in section_nom_lower):
                                section_url = '/projet11/traitements'
                            elif 'statistiques' in section_nom_lower or 'stats' in section_nom_lower:
                                section_url = '/projet11/statistiques'
                            else:
                                section_url = project_url
                    else:
                        # Pour les autres projets, utiliser l'URL du projet avec section_id en paramètre
                        section_url = f'{project_url}?section_id={section_id}' if section_id else project_url
                
                sections_data.append({
                    "id": section_id,
                    "nom": section_nom,
                    "url": section_url or project_url
                })
            
            projects_data.append({
                "id": project_id,
                "num": project_num,
                "nom": project_name,
                "icon": project_icon,
                "url": project_url,
                "sections": sections_data
            })
        
        return jsonify({"projects": projects_data})
    except Exception as e:
        print(f"[Erreur api_navigation_menu] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """Gestion du favicon - retourne 204 No Content pour éviter les erreurs 404"""
    return '', 204

# Gestionnaire d'erreur global pour capturer toutes les erreurs
@app.errorhandler(Exception)
def handle_exception(e):
    from flask import request
    try:
        error_msg = str(e) if e else "Erreur interne du serveur"
        error_trace = traceback.format_exc()
        # Écrire dans un fichier pour debug
        try:
            error_log_path = os.path.join('C:/Apps/.cursor', 'flask_errors.log')
            os.makedirs(os.path.dirname(error_log_path), exist_ok=True)
            with open(error_log_path, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()}\n{error_msg}\n{error_trace}\n\n")
        except:
            pass
        
        # Détecter si la requête attend du JSON ou du HTML
        # Vérifier l'en-tête Accept ou si le chemin contient /api/
        accepts_json = request.headers.get('Accept', '').find('application/json') >= 0
        is_api_route = '/api/' in request.path
        
        if accepts_json or is_api_route:
            # Retourner une réponse JSON pour les routes API
            error_json = json.dumps({
                'error': 'Erreur interne du serveur',
                'message': error_msg,
                'traceback': error_trace
            }, indent=2)
            return Response(error_json, status=500, mimetype='application/json')
        else:
            # Retourner une page HTML d'erreur pour les routes normales
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Erreur 500 - Erreur interne du serveur</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #d32f2f; }}
                    pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <h1>Erreur 500 - Erreur interne du serveur</h1>
                <p><strong>Message:</strong> {error_msg}</p>
                <details>
                    <summary>Détails techniques</summary>
                    <pre>{error_trace}</pre>
                </details>
                <p><a href="/">Retour à l'accueil</a></p>
            </body>
            </html>
            """
            return Response(error_html, status=500, mimetype='text/html')
    except Exception as handler_error:
        # Si le gestionnaire d'erreur lui-même échoue, retourner un message texte
        return Response(f'Erreur critique: {str(handler_error)}', status=500, mimetype='text/plain')

if __name__ == "__main__":
    # Désactiver le cache des templates en mode debug
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    # Désactiver complètement le cache des templates Jinja2
    app.jinja_env.auto_reload = True
    app.jinja_env.cache_size = 0
    # Forcer le rechargement du cache des templates
    if hasattr(app, 'jinja_env'):
        app.jinja_env.cache.clear()
    
    # Si lancé via watchdog, désactiver le rechargement intégré de Flask
    # pour éviter les conflits (watchdog gère le rechargement)
    use_watchdog = os.environ.get('FLASK_USE_WATCHDOG', 'false').lower() == 'true'
    
    if use_watchdog:
        # Mode watchdog : désactiver le rechargement intégré de Flask
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    else:
        # Mode normal : utiliser le rechargement intégré de Flask
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
