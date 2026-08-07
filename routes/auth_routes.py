"""
Routes d'authentification
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from logic.auth import login_user, login_atelier, logout_user, is_authenticated, get_current_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Page de connexion
    """
    try:
        if request.method == 'POST':
            identifiant = request.form.get('matricule', '').strip()
            password = request.form.get('password', '')
            
            if not identifiant:
                flash("Veuillez saisir votre matricule ou nom d'atelier.", "error")
                return render_template('auth/login.html')
            
            if not password:
                flash("Veuillez saisir votre mot de passe.", "error")
                return render_template('auth/login.html')
            
            try:
                # Connexion par matricule (nombre) ou par nom d'atelier (texte)
                is_numeric = identifiant.isdigit()
                if is_numeric:
                    matricule_int = int(identifiant)
                    success, message = login_user(matricule_int, password)
                else:
                    success, message = login_atelier(identifiant, password)
                
                if success:
                    next_page = request.args.get('next')
                    if next_page:
                        return redirect(next_page)
                    return redirect(url_for('index'))
                else:
                    flash(message, "error")
                    return render_template('auth/login.html')
            except Exception as e:
                error_msg = str(e)
                import traceback
                traceback.print_exc()
                flash(f"Erreur lors de la connexion: {error_msg}", "error")
                return render_template('auth/login.html')
        
        # GET : afficher le formulaire de connexion
        return render_template('auth/login.html')
    except Exception as e:
        # Gestion d'erreur globale pour la route
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERREUR dans la route login: {e}")
        print(error_trace)
        return f"<h1>Erreur de connexion</h1><p>{str(e)}</p><pre>{error_trace}</pre>", 500

@auth_bp.route('/logout')
def logout():
    """
    Déconnexion
    """
    logout_user()
    flash("Vous avez été déconnecté avec succès.", "success")
    return redirect(url_for('auth.login'))
