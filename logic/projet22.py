"""
Projet 22 - Gestion des employés et mots de passe
"""

from db import get_db_cursor
import bcrypt

def _normalize_bcrypt_hash(value):
    """
    Normalise un hash bcrypt provenant de SQL Server/pyodbc.
    Retourne une string sans espaces en début/fin (cas colonne CHAR).
    """
    if value is None:
        return None
    v = value
    if isinstance(v, memoryview):
        v = v.tobytes()
    elif isinstance(v, bytearray):
        v = bytes(v)
    if isinstance(v, bytes):
        try:
            return v.decode("utf-8", errors="strict").strip()
        except Exception:
            return v.decode("latin-1", errors="ignore").strip()
    return str(v).strip()

def get_all_employes():
    """Récupère la liste de tous les employés"""
    with get_db_cursor() as cursor:
        try:
            cursor.execute("""
                SELECT 
                    Matricule,
                    Nom,
                    Prenom,
                    Adresse_mail,
                    mdp,
                    archive
                FROM [dbo].[personel]
                ORDER BY CAST(Matricule AS INT) ASC
            """)
            
            employes = []
            for row in cursor.fetchall():
                employes.append({
                    "matricule": row.Matricule,
                    "nom": row.Nom or "",
                    "prenom": row.Prenom or "",
                    "email": row.Adresse_mail or "",
                    "a_mot_de_passe": row.mdp is not None and row.mdp != "",
                    "archive": bool(row.archive) if row.archive is not None else False
                })
            
            return employes
        except Exception as e:
            print(f"Erreur lors de la récupération des employés: {e}")
            import traceback
            traceback.print_exc()
            return []

def get_employe_by_matricule(matricule):
    """Récupère un employé par son matricule"""
    with get_db_cursor() as cursor:
        try:
            cursor.execute("""
                SELECT 
                    Matricule,
                    Nom,
                    Prenom,
                    Adresse_mail,
                    mdp,
                    archive
                FROM [dbo].[personel]
                WHERE Matricule = ?
            """, (matricule,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "matricule": row.Matricule,
                    "nom": row.Nom or "",
                    "prenom": row.Prenom or "",
                    "email": row.Adresse_mail or "",
                    "a_mot_de_passe": row.mdp is not None and row.mdp != "",
                    "archive": bool(row.archive) if row.archive is not None else False
                }
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération de l'employé: {e}")
            import traceback
            traceback.print_exc()
            return None

def create_employe(matricule, nom, prenom, email=None, mdp=None):
    """Crée un nouvel employé avec optionnellement un mot de passe"""
    with get_db_cursor() as cursor:
        try:
            # Vérifier si le matricule existe déjà
            cursor.execute("""
                SELECT Matricule FROM [dbo].[personel] WHERE Matricule = ?
            """, (matricule,))
            
            if cursor.fetchone():
                return {"success": False, "error": f"Le matricule {matricule} existe déjà"}
            
            # Hasher le mot de passe si fourni
            mdp_hash = None
            if mdp:
                mdp_hash = bcrypt.hashpw(mdp.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Insérer l'employé
            cursor.execute("""
                INSERT INTO [dbo].[personel] (Matricule, Nom, Prenom, Adresse_mail, mdp, archive)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (matricule, nom, prenom, email, mdp_hash))
            
            cursor.connection.commit()
            return {"success": True, "message": f"Employé {nom} {prenom} créé avec succès"}
        except Exception as e:
            print(f"Erreur lors de la création de l'employé: {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}

def update_employe(matricule, nom=None, prenom=None, email=None):
    """Met à jour les informations d'un employé (sans le mot de passe)"""
    with get_db_cursor() as cursor:
        try:
            # Construire la requête dynamiquement
            updates = []
            params = []
            
            if nom is not None:
                updates.append("Nom = ?")
                params.append(nom)
            
            if prenom is not None:
                updates.append("Prenom = ?")
                params.append(prenom)
            
            if email is not None:
                updates.append("Adresse_mail = ?")
                params.append(email)
            
            if not updates:
                return {"success": False, "error": "Aucune donnée à mettre à jour"}
            
            params.append(matricule)
            
            query = f"""
                UPDATE [dbo].[personel]
                SET {', '.join(updates)}
                WHERE Matricule = ?
            """
            
            cursor.execute(query, params)
            cursor.connection.commit()
            
            return {"success": True, "message": "Employé mis à jour avec succès"}
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'employé: {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}

def set_mot_de_passe(matricule, new_mdp, old_mdp=None):
    """Définit ou met à jour le mot de passe d'un employé
    Si old_mdp est fourni, vérifie que l'ancien mot de passe est correct avant de mettre à jour
    """
    with get_db_cursor() as cursor:
        try:
            # Vérifier que l'employé existe et récupérer son mot de passe actuel
            cursor.execute("""
                SELECT Matricule, mdp FROM [dbo].[personel] WHERE Matricule = ?
            """, (matricule,))
            
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": f"Employé avec matricule {matricule} non trouvé"}
            
            current_mdp_hash = row.mdp if hasattr(row, 'mdp') else None
            current_mdp_hash = _normalize_bcrypt_hash(current_mdp_hash)
            has_existing_password = current_mdp_hash is not None and current_mdp_hash != ""
            
            # Si l'employé a déjà un mot de passe, vérifier l'ancien mot de passe
            if has_existing_password:
                if not old_mdp:
                    return {"success": False, "error": "L'ancien mot de passe est requis pour modifier le mot de passe"}
                
                # Vérifier que l'ancien mot de passe correspond
                try:
                    if not bcrypt.checkpw(old_mdp.encode('utf-8'), current_mdp_hash.encode('utf-8')):
                        return {"success": False, "error": "L'ancien mot de passe est incorrect"}
                except Exception as e:
                    print(f"Erreur lors de la vérification de l'ancien mot de passe: {e}")
                    return {"success": False, "error": "Erreur lors de la vérification de l'ancien mot de passe"}
            
            # Hasher le nouveau mot de passe
            new_mdp_hash = bcrypt.hashpw(new_mdp.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Mettre à jour le mot de passe
            cursor.execute("""
                UPDATE [dbo].[personel]
                SET mdp = ?
                WHERE Matricule = ?
            """, (new_mdp_hash, matricule))
            
            cursor.connection.commit()
            
            if has_existing_password:
                return {"success": True, "message": "Mot de passe modifié avec succès"}
            else:
                return {"success": True, "message": "Mot de passe défini avec succès"}
        except Exception as e:
            print(f"Erreur lors de la définition du mot de passe: {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}

def archiver_employe(matricule, archive=True):
    """Archive ou désarchive un employé"""
    with get_db_cursor() as cursor:
        try:
            archive_value = 1 if archive else 0
            cursor.execute("""
                UPDATE [dbo].[personel]
                SET archive = ?
                WHERE Matricule = ?
            """, (archive_value, matricule))
            
            cursor.connection.commit()
            action = "archivé" if archive else "désarchivé"
            return {"success": True, "message": f"Employé {action} avec succès"}
        except Exception as e:
            print(f"Erreur lors de l'archivage de l'employé: {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}

def verifier_mot_de_passe(matricule, mdp):
    """Vérifie si le mot de passe fourni correspond à celui de l'employé"""
    with get_db_cursor() as cursor:
        try:
            cursor.execute("""
                SELECT mdp FROM [dbo].[personel]
                WHERE Matricule = ? AND archive = 0
            """, (matricule,))
            
            row = cursor.fetchone()
            stored = _normalize_bcrypt_hash(row.mdp if row and hasattr(row, "mdp") else (row[0] if row else None))
            if not stored:
                return False
            
            # Vérifier le mot de passe avec bcrypt
            return bcrypt.checkpw(mdp.encode('utf-8'), stored.encode('utf-8'))
        except Exception as e:
            print(f"Erreur lors de la vérification du mot de passe: {e}")
            import traceback
            traceback.print_exc()
            return False

def get_matricules_disponibles(limit=20):
    """Trouve les matricules disponibles (trous dans la séquence)
    Retourne une liste de matricules qui n'existent pas encore, y compris ceux inférieurs au dernier matricule
    """
    with get_db_cursor() as cursor:
        try:
            # Récupérer tous les matricules existants triés
            cursor.execute("""
                SELECT Matricule 
                FROM [dbo].[personel]
                ORDER BY Matricule
            """)
            
            matricules_existants = [row.Matricule for row in cursor.fetchall()]
            
            if not matricules_existants:
                # Si aucun matricule n'existe, suggérer à partir de 1
                return list(range(1, limit + 1))
            
            # Trouver le min et max
            min_matricule = min(matricules_existants)
            max_matricule = max(matricules_existants)
            
            # Créer un set pour une recherche rapide
            matricules_set = set(matricules_existants)
            
            # Trouver les trous dans la séquence
            matricules_disponibles = []
            
            # Chercher les trous avant le min (de 1 à min-1)
            for i in range(1, min_matricule):
                if len(matricules_disponibles) >= limit:
                    break
                matricules_disponibles.append(i)
            
            # Chercher les trous entre min et max
            for i in range(min_matricule + 1, max_matricule):
                if len(matricules_disponibles) >= limit:
                    break
                if i not in matricules_set:
                    matricules_disponibles.append(i)
            
            # Si on n'a pas assez de suggestions, ajouter après le max
            if len(matricules_disponibles) < limit:
                next_matricule = max_matricule + 1
                while len(matricules_disponibles) < limit:
                    matricules_disponibles.append(next_matricule)
                    next_matricule += 1
            
            # Trier et limiter
            matricules_disponibles.sort()
            return matricules_disponibles[:limit]
            
        except Exception as e:
            print(f"Erreur lors de la recherche des matricules disponibles: {e}")
            import traceback
            traceback.print_exc()
            return []
