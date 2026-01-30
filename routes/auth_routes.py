"""
Routes d'authentification
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from logic.auth import login_user, logout_user, is_authenticated, get_current_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Page de connexion
    """
    try:
        if request.method == 'POST':
            matricule = request.form.get('matricule', '').strip()
            password = request.form.get('password', '')
            
            if not matricule:
                flash("Veuillez saisir votre matricule.", "error")
                return render_template('auth/login.html')
            
            if not password:
                flash("Veuillez saisir votre mot de passe.", "error")
                return render_template('auth/login.html')
            
            try:
                matricule_int = int(matricule)
            except ValueError:
                flash("Le matricule doit être un nombre.", "error")
                return render_template('auth/login.html')
            
            try:
                success, message = login_user(matricule_int, password)
                
                if success:
                    flash(message, "success")
                    # Rediriger vers la page demandée ou l'accueil
                    next_page = request.args.get('next')
                    if next_page:
                        return redirect(next_page)
                    return redirect(url_for('index'))
                else:
                    flash(message, "error")
                    return render_template('auth/login.html')
            except Exception as e:
                # Gestion d'erreur pour login_user
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
