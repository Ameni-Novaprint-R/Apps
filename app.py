from flask import Flask, render_template, Response
from datetime import datetime, timezone
from logic import projet1, projet2, projet3, projet4, projet5, projet6, projet8, projet9, projet10
from logic.projet7 import projet7_bp
from routes.crystal_reports_routes import crystal_reports
from routes.projet11_routes import projet11_bp
from routes.projet12_routes import projet12_bp
from routes.projet14_routes import projet14_bp
from routes.projet15_routes import projet15_bp
from routes.projet16_routes import projet16_bp
from routes.projet17_routes import projet17_bp
from routes.projet19_routes import projet19_bp
from routes.projet20_routes import projet20_bp
from routes.projet21_routes import projet21_bp
import os
import json
import traceback

# Forcer le rechargement des modules - 20 Oct 2025 16:10
import importlib
import sys
if 'logic.projet11' in sys.modules:
    importlib.reload(sys.modules['logic.projet11'])
if 'routes.projet11_routes' in sys.modules:
    importlib.reload(sys.modules['routes.projet11_routes'])





app = Flask(__name__)

# Injection automatique de la variable "now" dans tous les templates
@app.context_processor
def inject_now():
    return {"now": datetime.now(timezone.utc)}

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
app.register_blueprint(projet11_bp)
app.register_blueprint(projet12_bp)
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


@app.route("/")
def index():
    return render_template("index.html")  # plus besoin d'ajouter now ici

@app.route('/favicon.ico')
def favicon():
    """Gestion du favicon - retourne 204 No Content pour éviter les erreurs 404"""
    return '', 204

app.secret_key = 'vraiment-secret-et-unique'

# Gestionnaire d'erreur global pour capturer toutes les erreurs
@app.errorhandler(Exception)
def handle_exception(e):
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
        # Retourner une réponse JSON
        error_json = json.dumps({
            'error': 'Erreur interne du serveur',
            'message': error_msg,
            'traceback': error_trace
        }, indent=2)
        return Response(error_json, status=500, mimetype='application/json')
    except Exception as handler_error:
        # Si le gestionnaire d'erreur lui-même échoue, retourner un message texte
        return Response(f'Erreur critique: {str(handler_error)}', status=500, mimetype='text/plain')

if __name__ == "__main__":
    # Désactiver le cache des templates en mode debug
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Si lancé via watchdog, désactiver le rechargement intégré de Flask
    # pour éviter les conflits (watchdog gère le rechargement)
    use_watchdog = os.environ.get('FLASK_USE_WATCHDOG', 'false').lower() == 'true'
    
    if use_watchdog:
        # Mode watchdog : désactiver le rechargement intégré de Flask
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    else:
        # Mode normal : utiliser le rechargement intégré de Flask
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
