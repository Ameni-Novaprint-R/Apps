"""
Module d'authentification et de gestion des droits d'accès
"""
from flask import session, redirect, url_for, request, flash
from functools import wraps
from db import get_db_cursor

# Import bcrypt avec gestion d'erreur
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    print("ATTENTION: Le module bcrypt n'est pas installe. L'authentification ne fonctionnera pas.")
    print("Installez-le avec: pip install bcrypt")

# Matricule du super-utilisateur
SUPER_USER_MATRICULE = 321

def hash_password(password):
    """
    Hash un mot de passe avec bcrypt
    """
    if not BCRYPT_AVAILABLE:
        raise ImportError("Le module bcrypt n'est pas installe. Installez-le avec: pip install bcrypt")
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    """
    Vérifie un mot de passe contre un hash bcrypt
    """
    if not BCRYPT_AVAILABLE:
        return False
    try:
        # Normaliser le hash venant de SQL Server / pyodbc :
        # - VARCHAR/NVARCHAR -> str
        # - VARBINARY -> bytes/bytearray/memoryview
        # - Certaines colonnes CHAR peuvent contenir des espaces en fin
        if hashed is None:
            return False

        # bytes-like -> bytes
        if isinstance(hashed, memoryview):
            hashed = hashed.tobytes()
        elif isinstance(hashed, bytearray):
            hashed = bytes(hashed)

        # "b'...'" (string) -> bytes
        if isinstance(hashed, str):
            h = hashed.strip()
            # Cas fréquent: la valeur a été stockée sous forme de repr(b'...')
            if (h.startswith("b'") and h.endswith("'")) or (h.startswith('b"') and h.endswith('"')):
                try:
                    import ast
                    maybe_bytes = ast.literal_eval(h)
                    if isinstance(maybe_bytes, (bytes, bytearray)):
                        h = bytes(maybe_bytes).decode("utf-8", errors="strict")
                except Exception:
                    # On garde h tel quel si le parsing échoue
                    pass
            hashed_bytes = h.strip().encode("utf-8", errors="strict")
        elif isinstance(hashed, (bytes,)):
            # Hash bcrypt est ASCII -> decode/strip/re-encode pour enlever les espaces éventuels
            try:
                h = hashed.decode("utf-8", errors="strict").strip()
            except Exception:
                h = hashed.decode("latin-1", errors="ignore").strip()
            hashed_bytes = h.encode("utf-8", errors="strict")
        else:
            # Fallback: convertir en str
            hashed_bytes = str(hashed).strip().encode("utf-8", errors="strict")

        return bcrypt.checkpw(password.encode("utf-8"), hashed_bytes)
    except Exception:
        return False

def login_user(matricule, password):
    """
    Authentifie un utilisateur par matricule et mot de passe
    Retourne (success: bool, message: str)
    Note: Cette fonction doit être appelée dans le contexte d'une requête Flask
    """
    from flask import session as flask_session
    
    try:
        with get_db_cursor() as cursor:
            # Vérifier que l'employé existe
            cursor.execute("""
                SELECT Matricule, Nom, Prenom, mdp
                FROM personel
                WHERE Matricule = ?
            """, (matricule,))
            
            employee = cursor.fetchone()
            if not employee:
                return False, "Matricule introuvable"
            
            # Vérifier le mot de passe (utiliser la colonne mdp en minuscule)
            mdp_hash = None
            
            # Essayer plusieurs méthodes pour récupérer le hash
            # pyodbc peut retourner soit un objet Row avec attributs, soit un tuple
            try:
                # Méthode 1: Attribut (si pyodbc retourne un Row)
                if hasattr(employee, 'mdp'):
                    mdp_hash = employee.mdp
                # Méthode 2: Index (si c'est un tuple/liste)
                # SELECT Matricule, Nom, Prenom, mdp -> index 0,1,2,3
                elif hasattr(employee, '__getitem__'):
                    try:
                        mdp_hash = employee[3]  # Index 3 = colonne mdp
                    except (IndexError, TypeError):
                        pass
                # Méthode 3: Requête séparée si les méthodes précédentes échouent
                if mdp_hash is None:
                    cursor.execute("SELECT mdp FROM personel WHERE Matricule = ?", (matricule,))
                    row = cursor.fetchone()
                    if row:
                        if hasattr(row, 'mdp'):
                            mdp_hash = row.mdp
                        elif hasattr(row, '__getitem__'):
                            mdp_hash = row[0]
            except Exception as e:
                print(f"[ERREUR] Erreur lors de la récupération du mot de passe: {e}")
                import traceback
                traceback.print_exc()
            
            # Debug: afficher le type et les premiers caractères du hash récupéré
            if mdp_hash:
                hash_str = str(mdp_hash).strip()
                print(f"[DEBUG login_user] Hash récupéré: type={type(mdp_hash).__name__}, longueur={len(hash_str)}, début={hash_str[:30]}")
            else:
                print(f"[DEBUG login_user] Aucun hash récupéré pour matricule {matricule}")
            
            if not mdp_hash:
                return False, "Aucun mot de passe défini pour cet employé"
            
            # Vérifier le mot de passe avec la fonction normalisée
            password_check_result = check_password(password, mdp_hash)
            print(f"[DEBUG login_user] check_password(password, hash) = {password_check_result}")
            
            if not password_check_result:
                return False, "Mot de passe incorrect"
            
            # Vérifier que l'employé a au moins un droit ou est super-utilisateur
            if matricule == SUPER_USER_MATRICULE:
                # Super-utilisateur : accès complet
                try:
                    flask_session['matricule'] = matricule
                    flask_session['nom'] = f"{employee.Nom} {employee.Prenom}"
                    flask_session['is_super_user'] = True
                    return True, "Connexion réussie (Super-utilisateur)"
                except RuntimeError as e:
                    return False, f"Erreur de session Flask: {str(e)}"
            
            # Vérifier les droits dans WEB_DROITS_ACCES
            cursor.execute("""
                SELECT COUNT(*) as nb_droits
                FROM WEB_DROITS_ACCES
                WHERE Matricule = ? AND Autorise = 1
            """, (matricule,))
            
            result = cursor.fetchone()
            if not result or result.nb_droits == 0:
                # L'employé n'a aucun droit, mais peut accéder à la page d'accueil
                flask_session['matricule'] = matricule
                flask_session['nom'] = f"{employee.Nom} {employee.Prenom}"
                flask_session['is_super_user'] = False
                flask_session['has_rights'] = False
                return True, "Connexion réussie (Accès limité à la page d'accueil)"
            
            # L'employé a des droits
            flask_session['matricule'] = matricule
            flask_session['nom'] = f"{employee.Nom} {employee.Prenom}"
            flask_session['is_super_user'] = False
            flask_session['has_rights'] = True
            return True, "Connexion réussie"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Erreur lors de l'authentification: {str(e)}"

def logout_user():
    """
    Déconnecte l'utilisateur
    """
    from flask import session as flask_session
    flask_session.clear()

def is_authenticated():
    """
    Vérifie si l'utilisateur est authentifié
    """
    try:
        from flask import session as flask_session
        return 'matricule' in flask_session and flask_session.get('matricule') is not None
    except Exception:
        return False

def get_current_user():
    """
    Retourne les informations de l'utilisateur connecté
    """
    try:
        from flask import session as flask_session
        if not is_authenticated():
            return None
        
        return {
            'matricule': flask_session.get('matricule'),
            'nom': flask_session.get('nom'),
            'is_super_user': flask_session.get('is_super_user', False),
            'has_rights': flask_session.get('has_rights', True)
        }
    except Exception:
        return None

def is_super_user():
    """
    Vérifie si l'utilisateur connecté est le super-utilisateur
    """
    try:
        from flask import session as flask_session
        if not is_authenticated():
            return False
        return flask_session.get('is_super_user', False) or flask_session.get('matricule') == SUPER_USER_MATRICULE
    except Exception:
        return False

def has_project_access(project_id):
    """
    Vérifie si l'utilisateur connecté a accès à un projet spécifique
    Retourne True si super-utilisateur ou si l'utilisateur a au moins un droit sur ce projet
    """
    try:
        from flask import session as flask_session
        if not is_authenticated():
            return False
        
        matricule = flask_session.get('matricule')
        
        # Super-utilisateur : accès complet
        if is_super_user():
            return True
        
        with get_db_cursor() as cursor:
            # Vérifier si l'utilisateur a au moins un droit sur ce projet
            cursor.execute("""
                SELECT COUNT(*) as nb_droits
                FROM WEB_DROITS_ACCES WDA
                INNER JOIN WEB_ACTIONS WA ON WA.ID = WDA.ID_Action
                INNER JOIN WEB_SECTIONS WS ON WS.ID = WA.ID_Section
                WHERE WDA.Matricule = ?
                AND WDA.Autorise = 1
                AND WS.ID_Proj = ?
            """, (matricule, project_id))
            
            result = cursor.fetchone()
            return result and result.nb_droits > 0
            
    except Exception as e:
        print(f"Erreur lors de la vérification des droits projet: {e}")
        return False

def has_action_access(action_id):
    """
    Vérifie si l'utilisateur connecté a accès à une action spécifique
    Retourne True si super-utilisateur ou si l'utilisateur a le droit sur cette action
    """
    try:
        from flask import session as flask_session
        if not is_authenticated():
            return False
        
        matricule = flask_session.get('matricule')
        
        # Super-utilisateur : accès complet
        if is_super_user():
            return True
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as nb_droits
                FROM WEB_DROITS_ACCES
                WHERE Matricule = ?
                AND ID_Action = ?
                AND Autorise = 1
            """, (matricule, action_id))
            
            result = cursor.fetchone()
            return result and result.nb_droits > 0
            
    except Exception as e:
        print(f"Erreur lors de la vérification des droits action: {e}")
        return False

def has_section_access(section_id):
    """
    Vérifie si l'utilisateur connecté a accès à une section spécifique
    Retourne True si super-utilisateur ou si l'utilisateur a au moins une action autorisée pour cette section
    """
    try:
        from flask import session as flask_session
        if not is_authenticated():
            return False
        
        matricule = flask_session.get('matricule')
        
        # Super-utilisateur : accès complet
        if is_super_user():
            return True
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as nb_droits
                FROM WEB_DROITS_ACCES WDA
                INNER JOIN WEB_ACTIONS WA ON WA.ID = WDA.ID_Action
                WHERE WDA.Matricule = ?
                AND WA.ID_Section = ?
                AND WDA.Autorise = 1
            """, (matricule, section_id))
            
            result = cursor.fetchone()
            return result and result.nb_droits > 0
            
    except Exception as e:
        print(f"Erreur lors de la vérification des droits section: {e}")
        return False

def get_user_sections(project_id):
    """
    Retourne la liste des sections d'un projet auxquelles l'utilisateur connecté a accès
    Une section est visible si l'utilisateur a au moins une action autorisée pour cette section
    Retourne toutes les sections si super-utilisateur
    """
    try:
        from flask import session as flask_session
        if not is_authenticated():
            return []
        
        matricule = flask_session.get('matricule')
        if not matricule:
            return []
        
        # Super-utilisateur : toutes les sections du projet
        if is_super_user():
            try:
                with get_db_cursor() as cursor:
                    cursor.execute("""
                        SELECT DISTINCT WS.ID, WS.Nom, WS.ID_Proj
                        FROM WEB_SECTIONS WS
                        INNER JOIN WEB_PROJETS WP ON WP.ID = WS.ID_Proj
                        WHERE WP.ID = ? OR WP.NumProj = ?
                        ORDER BY WS.ID
                    """, (project_id, project_id))
                    sections = cursor.fetchall()
                    return [{'id': s.ID, 'nom': s.Nom, 'id_proj': s.ID_Proj} for s in sections]
            except Exception as e:
                print(f"Erreur lors de la récupération des sections (super-user): {e}")
                import traceback
                traceback.print_exc()
                return []
        
        try:
            with get_db_cursor() as cursor:
                # Récupérer uniquement les sections pour lesquelles l'utilisateur a au moins une action autorisée
                cursor.execute("""
                    SELECT DISTINCT WS.ID, WS.Nom, WS.ID_Proj
                    FROM WEB_SECTIONS WS
                    INNER JOIN WEB_PROJETS WP ON WP.ID = WS.ID_Proj
                    INNER JOIN WEB_ACTIONS WA ON WA.ID_Section = WS.ID
                    INNER JOIN WEB_DROITS_ACCES WDA ON WDA.ID_Action = WA.ID
                    WHERE (WP.ID = ? OR WP.NumProj = ?)
                    AND WDA.Matricule = ?
                    AND WDA.Autorise = 1
                    ORDER BY WS.ID
                """, (project_id, project_id, matricule))
                
                sections = cursor.fetchall()
                return [{'id': s.ID, 'nom': s.Nom, 'id_proj': s.ID_Proj} for s in sections]
                
        except Exception as e:
            print(f"Erreur lors de la récupération des sections: {e}")
            import traceback
            traceback.print_exc()
            return []
    except Exception as e:
        print(f"Erreur dans get_user_sections: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_user_projects():
    """
    Retourne la liste des projets auxquels l'utilisateur connecté a accès
    Retourne tous les projets si super-utilisateur
    """
    try:
        from flask import session as flask_session
        if not is_authenticated():
            return []
        
        matricule = flask_session.get('matricule')
        if not matricule:
            return []
        
        # Super-utilisateur : tous les projets
        if is_super_user():
            try:
                with get_db_cursor() as cursor:
                    cursor.execute("""
                        SELECT DISTINCT ID, NumProj, CodeProj, Nom
                        FROM WEB_PROJETS
                        WHERE archive = 0
                        ORDER BY NumProj
                    """)
                    projets = cursor.fetchall()
                    return [{'id': p.ID, 'num': p.NumProj, 'code': p.CodeProj, 'nom': p.Nom} for p in projets]
            except Exception as e:
                print(f"Erreur lors de la récupération des projets (super-user): {e}")
                import traceback
                traceback.print_exc()
                return []
        
        try:
            with get_db_cursor() as cursor:
                # Récupérer les projets pour lesquels l'utilisateur a au moins un droit
                cursor.execute("""
                    SELECT DISTINCT WP.ID, WP.NumProj, WP.CodeProj, WP.Nom
                    FROM WEB_PROJETS WP
                    INNER JOIN WEB_SECTIONS WS ON WS.ID_Proj = WP.ID
                    INNER JOIN WEB_ACTIONS WA ON WA.ID_Section = WS.ID
                    INNER JOIN WEB_DROITS_ACCES WDA ON WDA.ID_Action = WA.ID
                    WHERE WDA.Matricule = ?
                    AND WDA.Autorise = 1
                    AND WP.archive = 0
                    ORDER BY WP.NumProj
                """, (matricule,))
                
                projets = cursor.fetchall()
                return [{'id': p.ID, 'num': p.NumProj, 'code': p.CodeProj, 'nom': p.Nom} for p in projets]
                
        except Exception as e:
            print(f"Erreur lors de la récupération des projets: {e}")
            import traceback
            traceback.print_exc()
            return []
    except Exception as e:
        print(f"Erreur dans get_user_projects: {e}")
        import traceback
        traceback.print_exc()
        return []

def login_required(f):
    """
    Décorateur pour protéger une route : nécessite une authentification
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def project_access_required(project_id_param='project_id'):
    """
    Décorateur pour protéger une route : nécessite un accès au projet
    Le project_id peut être passé en paramètre de route ou récupéré depuis la route
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_authenticated():
                return redirect(url_for('auth.login', next=request.url))
            
            # Récupérer le project_id depuis les kwargs ou depuis la route
            project_id = kwargs.get(project_id_param)
            if not project_id:
                # Essayer de récupérer depuis la route (ex: /projet11/...)
                path_parts = request.path.split('/')
                for part in path_parts:
                    if part.startswith('projet') and part[6:].isdigit():
                        project_id = int(part[6:])
                        break
            
            if project_id and not has_project_access(project_id):
                flash("Vous n'avez pas accès à ce projet.", "error")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
