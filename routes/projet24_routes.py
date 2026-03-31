# -*- coding: utf-8 -*-
"""
Routes pour le Projet 24 – Formes de Découpe.
Préfixe : /projet24. Contenu intégré dans le layout base.html (header/footer communs).
Les sections affichées sont filtrées selon WEB_DROITS_ACCES (get_user_sections),
avec accès complet pour les super-utilisateurs.
"""
import os
from flask import Blueprint, render_template, request, jsonify, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from logic.auth import login_required, get_current_user, get_user_sections, has_project_access, is_super_user
from logic import projet24 as p24
from db import init_formes_tables

# Dossier d'upload PDF (à adapter selon l'environnement 192.168.10.225)
UPLOAD_FOLDER = os.environ.get('PROJET24_UPLOAD_FOLDER', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'BCFORMES'))
ALLOWED_EXTENSIONS = {'pdf'}

# Correspondance nom de section (WEB_SECTIONS.Nom) -> clé template (URL / section)
PROJET24_SECTION_NAME_TO_KEY = {
    'Nouvelle forme': 'nouvelle',
    'Modifier forme existante': 'modifier',
    'Suivi des formes de découpe': 'suivi',
    'Tableau de bord': 'dashboard',
}

def allowed_file(filename):
    return filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_projet24_allowed_sections():
    """
    Retourne la liste des clés de sections (nouvelle, modifier, suivi, dashboard)
    auxquelles l'utilisateur connecté a accès pour le projet 24.
    Utilise get_user_sections(24) pour respecter WEB_DROITS_ACCES.
    """
    # Super-utilisateur : accès complet à toutes les sections, sans dépendre des noms en base
    if is_super_user():
        return ['nouvelle', 'modifier', 'suivi', 'dashboard']
    # get_user_sections accepte ID ou NumProj (WHERE WP.ID = ? OR WP.NumProj = ?)
    sections_raw = get_user_sections(24)
    allowed = []
    for s in sections_raw:
        nom = (s.get('nom') or s.get('Nom') or '').strip()
        key = PROJET24_SECTION_NAME_TO_KEY.get(nom)
        # Tolérance : accepter des variantes d'intitulés (accents, majuscules, petites différences)
        if not key and nom:
            nom_lower = nom.lower()
            if 'nouvelle' in nom_lower:
                key = 'nouvelle'
            elif 'modifier' in nom_lower or 'existante' in nom_lower:
                key = 'modifier'
            elif 'suivi' in nom_lower:
                key = 'suivi'
            elif 'tableau' in nom_lower or 'bord' in nom_lower:
                key = 'dashboard'
        if key and key not in allowed:
            allowed.append(key)
    return allowed


def render_projet24(section=None, template='projet24.html', **kwargs):
    """Rend le template projet24 avec allowed_sections et vérification d'accès à la section."""
    allowed_sections = get_projet24_allowed_sections()
    if section is not None and section not in allowed_sections:
        # Accès direct à une section non autorisée -> rediriger vers l'accueil ou première section
        if allowed_sections:
            first = allowed_sections[0]
            if first == 'nouvelle':
                return redirect(url_for('projet24.nouvelle_forme'))
            if first == 'modifier':
                return redirect(url_for('projet24.modifier_forme'))
            if first == 'suivi':
                return redirect(url_for('projet24.suivi_formes'))
            if first == 'dashboard':
                return redirect(url_for('projet24.dashboard'))
        return redirect(url_for('projet24.index'))
    kwargs['section'] = section
    kwargs['allowed_sections'] = allowed_sections
    return render_template(template, **kwargs)


projet24_bp = Blueprint('projet24', __name__, url_prefix='/projet24')


@projet24_bp.route('/')
@login_required
def index():
    """Page principale : titre + sections, aucun contenu affiché par défaut."""
    if not has_project_access(24):
        return redirect(url_for('index'))
    return render_projet24(section=None)


@projet24_bp.route('/nouvelle-forme')
@login_required
def nouvelle_forme():
    """Section « Nouvelle forme » : formulaire de création."""
    if not has_project_access(24):
        return redirect(url_for('index'))
    return render_projet24(section='nouvelle')


@projet24_bp.route('/modifier-forme')
@login_required
def modifier_forme():
    """Section « Modifier forme existante » : sélection + formulaire d'édition."""
    if not has_project_access(24):
        return redirect(url_for('index'))
    return render_projet24(section='modifier')


@projet24_bp.route('/suivi-formes')
@login_required
def suivi_formes():
    """Section « Suivi des formes de découpe » : tableau des formes uniquement."""
    if not has_project_access(24):
        return redirect(url_for('index'))
    return render_projet24(section='suivi')


@projet24_bp.route('/dashboard')
@login_required
def dashboard():
    """Section « Tableau de bord »."""
    if not has_project_access(24):
        return redirect(url_for('index'))
    allowed_sections = get_projet24_allowed_sections()
    if 'dashboard' not in allowed_sections:
        if allowed_sections:
            first = allowed_sections[0]
            if first == 'nouvelle':
                return redirect(url_for('projet24.nouvelle_forme'))
            if first == 'modifier':
                return redirect(url_for('projet24.modifier_forme'))
            if first == 'suivi':
                return redirect(url_for('projet24.suivi_formes'))
        return redirect(url_for('projet24.index'))
    return render_template('projet24_dashboard.html', allowed_sections=allowed_sections)


@projet24_bp.route('/export-excel')
@login_required
def export_formes_excel():
    """Export du tableau des formes au format Excel."""
    from flask import Response
    from datetime import datetime
    try:
        import pandas as pd
        from io import BytesIO
    except ImportError:
        try:
            import csv
            from io import StringIO
        except ImportError:
            return jsonify({"error": "Aucun module d'export disponible"}), 500
        formes = p24.get_all_formes()
        if not formes:
            return jsonify({"error": "Aucune forme à exporter"}), 404
        output = StringIO()
        writer = csv.writer(output, delimiter=';')
        headers = ['Type forme', 'Type produit', 'Nom', 'Dimension', 'Format fini', 'Sens fibre', 'Fichier', 'Poses', 'Tirages', 'Coût initial', 'Coût amélioration', 'État', 'Créé le', 'Créateur']
        writer.writerow(headers)
        for f in formes:
            date_cre = f.get('date_creation')
            if date_cre:
                try:
                    date_cre = date_cre.strftime('%Y-%m-%d') if hasattr(date_cre, 'strftime') else str(date_cre)
                except Exception:
                    date_cre = str(date_cre)
            writer.writerow([
                f.get('type_forme'), f.get('type_produit'), f.get('nom'), f.get('dimension'), f.get('format_fini'),
                f.get('sens_fibre'), f.get('fichier_source'), f.get('nombre_pose'), f.get('total_tirages'),
                f.get('cout_initial'), f.get('cout_amelioration'), f.get('etat'), date_cre, f.get('createur')
            ])
        output.seek(0)
        filename = f"formes_decoupe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            output.getvalue(),
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    formes = p24.get_all_formes()
    if not formes:
        return jsonify({"error": "Aucune forme à exporter"}), 404
    data = []
    for f in formes:
        date_cre = f.get('date_creation')
        if date_cre and hasattr(date_cre, 'strftime'):
            date_cre = date_cre.strftime('%Y-%m-%d')
        data.append({
            'Type forme': f.get('type_forme'), 'Type produit': f.get('type_produit'), 'Nom': f.get('nom'),
            'Dimension': f.get('dimension'), 'Format fini': f.get('format_fini'), 'Sens fibre': f.get('sens_fibre'),
            'Fichier': f.get('fichier_source'), 'Poses': f.get('nombre_pose'), 'Tirages': f.get('total_tirages'),
            'Coût initial': f.get('cout_initial'), 'Coût amélioration': f.get('cout_amelioration'),
            'État': f.get('etat'), 'Créé le': date_cre, 'Créateur': f.get('createur')
        })
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Formes', index=False)
        ws = writer.sheets['Formes']
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(str(col)))
            col_letter = chr(65 + idx) if idx < 26 else 'A' + chr(65 + idx - 26)
            ws.column_dimensions[col_letter].width = min(max_len + 2, 50)
    output.seek(0)
    filename = f"formes_decoupe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


# ---------- API ----------

@projet24_bp.route('/api/formes', methods=['GET'])
@login_required
def api_list_formes():
    """Liste toutes les formes."""
    try:
        formes = p24.get_all_formes()
        return jsonify(formes)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@projet24_bp.route('/api/formes', methods=['POST'])
@login_required
def api_create_forme():
    """Création d'une forme (nouvelle ou existante)."""
    try:
        data = request.form.to_dict() if request.form else (request.get_json() or {})
        if request.files and 'fichier_source' in request.files:
            f = request.files['fichier_source']
            if f and f.filename and allowed_file(f.filename):
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filename = secure_filename(f.filename)
                # Préfixer par un identifiant unique pour éviter les collisions
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{os.urandom(4).hex()}{ext}"
                f.save(os.path.join(UPLOAD_FOLDER, filename))
                data['fichier_source'] = filename
        createur = get_current_user() or 'System'
        forme, err = p24.create_forme(data, createur=createur)
        if err:
            return jsonify({'success': False, 'error': err}), 400
        return jsonify({'success': True, 'forme': forme})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@projet24_bp.route('/api/formes/<nom>', methods=['GET'])
@login_required
def api_get_forme_nom(nom):
    """Détail d'une forme par NOM."""
    try:
        forme = p24.get_forme_by_nom(nom)
        if not forme:
            return jsonify({'error': 'Forme introuvable'}), 404
        return jsonify(forme)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@projet24_bp.route('/api/formes/<nom>', methods=['PUT'])
@login_required
def api_update_forme_nom(nom):
    """Mise à jour d'une forme par NOM (formulaire ou JSON)."""
    try:
        if request.is_json:
            data = request.get_json()
            fichier_source = None
        else:
            data = request.form.to_dict()
            fichier_source = None
            if request.files and 'fichier_source' in request.files:
                f = request.files['fichier_source']
                if f and f.filename and allowed_file(f.filename):
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    filename = secure_filename(f.filename)
                    base, ext = os.path.splitext(filename)
                    filename = f"{base}_{os.urandom(4).hex()}{ext}"
                    f.save(os.path.join(UPLOAD_FOLDER, filename))
                    fichier_source = filename
        ok, err = p24.update_forme_by_nom(nom, data, fichier_source=fichier_source)
        if not ok:
            return jsonify({'success': False, 'error': err}), 400
        return jsonify({'success': True, 'forme': p24.get_forme_by_nom(nom)})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@projet24_bp.route('/api/formes/<nom>', methods=['DELETE'])
@login_required
def api_delete_forme_nom(nom):
    """Suppression réelle d'une forme par NOM."""
    try:
        ok, err = p24.delete_forme_by_nom(nom)
        if not ok:
            return jsonify({'success': False, 'error': err}), 400
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@projet24_bp.route('/api/formes/<nom>/tirages', methods=['POST'])
@login_required
def api_add_tirages(nom):
    """Ajoute des tirages à une forme."""
    try:
        data = request.get_json() or {}
        n = data.get('nombre_tirages')
        ok, err = p24.add_tirages(nom, n, createur=get_current_user() or 'System')
        if not ok:
            return jsonify({'success': False, 'error': err}), 400
        return jsonify({'success': True, 'forme': p24.get_forme_by_nom(nom)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@projet24_bp.route('/api/formes/<nom>/couts', methods=['GET'])
@login_required
def api_list_couts(nom):
    """Liste les coûts d'amélioration d'une forme."""
    try:
        couts = p24.get_couts_by_nom(nom)
        return jsonify(couts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@projet24_bp.route('/api/formes/<nom>/couts', methods=['POST'])
@login_required
def api_add_cout(nom):
    """Ajoute une ligne de coût d'amélioration."""
    try:
        data = request.get_json() or {}
        montant = data.get('montant')
        description = data.get('description', '')
        ok, err = p24.add_cout(nom, montant, description, createur=get_current_user() or 'System')
        if not ok:
            return jsonify({'success': False, 'error': err}), 400
        return jsonify({'success': True, 'couts': p24.get_couts_by_nom(nom)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@projet24_bp.route('/api/formes/<nom>/etat', methods=['PUT'])
@login_required
def api_set_etat(nom):
    """Change l'état d'une forme (EN_COMMANDE, PRETE, EN_MODIFICATION)."""
    try:
        data = request.get_json() or {}
        etat = data.get('etat')
        ok, err = p24.set_etat(nom, etat)
        if not ok:
            return jsonify({'success': False, 'error': err}), 400
        return jsonify({'success': True, 'forme': p24.get_forme_by_nom(nom)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@projet24_bp.route('/api/dashboard')
@login_required
def api_dashboard():
    """Stats pour le tableau de bord."""
    try:
        stats = p24.get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@projet24_bp.route('/api/generate-identifiant')
@login_required
def api_generate_identifiant():
    """Génère un identifiant suggéré (ex: type=VAR -> VAR26001)."""
    try:
        t = request.args.get('type', '').strip().upper()[:10]
        if not t:
            return jsonify({'identifiant': None})
        ident = p24.generate_identifiant(t)
        return jsonify({'identifiant': ident})
    except Exception as e:
        return jsonify({'identifiant': None, 'error': str(e)}), 500


@projet24_bp.route('/uploads/<filename>')
@login_required
def serve_upload(filename):
    """Sert un fichier PDF uploadé."""
    return send_from_directory(UPLOAD_FOLDER, filename, mimetype='application/pdf')


def register_formes_tables():
    """Appelé au démarrage pour créer les tables si besoin."""
    try:
        init_formes_tables()
    except Exception as e:
        print(f"[Projet 24] init_formes_tables: {e}")


def ensure_projet24_in_web_projets():
    """Insère le Projet 24 dans WEB_PROJETS si absent (pour affichage page d'accueil et menu sandwich)."""
    try:
        from db import get_db_cursor
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = ?",
                (24,)
            )
            if cursor.fetchone():
                return
            cursor.execute("""
                INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive)
                VALUES (24, 'Projet 24', 'Formes de Découpe', 0)
            """)
            cursor.connection.commit()
            print("[Projet 24] Entrée WEB_PROJETS ajoutée (NumProj=24).")
    except Exception as e:
        print(f"[Projet 24] ensure_projet24_in_web_projets: {e}")
