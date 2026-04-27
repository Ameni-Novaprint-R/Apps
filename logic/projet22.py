"""
Projet 22 - Gestion des employés et des ateliers
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


def set_mot_de_passe_force(matricule, new_mdp):
    """
    Force le mot de passe d'un employé sans vérifier l'ancien (maintenance / admin).
    Ne pas exposer sur une route publique sans contrôle strict.
    """
    if new_mdp is None or len(str(new_mdp).strip()) < 1:
        return {"success": False, "error": "Mot de passe requis"}
    try:
        m = int(matricule)
    except (TypeError, ValueError):
        return {"success": False, "error": "Matricule invalide"}
    with get_db_cursor() as cursor:
        try:
            cursor.execute(
                "SELECT Matricule FROM [dbo].[personel] WHERE Matricule = ?",
                (m,),
            )
            if not cursor.fetchone():
                return {"success": False, "error": f"Employé matricule {m} introuvable"}
            new_mdp_hash = bcrypt.hashpw(
                str(new_mdp).encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            cursor.execute(
                "UPDATE [dbo].[personel] SET mdp = ? WHERE Matricule = ?",
                (new_mdp_hash, m),
            )
            cursor.connection.commit()
            return {"success": True, "message": f"Mot de passe réinitialisé pour le matricule {m}"}
        except Exception as e:
            print(f"Erreur set_mot_de_passe_force: {e}")
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


# --- Gestion des ateliers (WEB_ATELIER_ACCES) ---

MDP_ATELIER_DEFAUT = "000000"


def get_all_ateliers():
    """Récupère la liste de tous les ateliers (avec mdp et archive si colonnes présentes)"""
    with get_db_cursor() as cursor:
        try:
            cursor.execute("""
                SELECT ID, Nom, mdp, archive
                FROM [dbo].[WEB_ATELIER_ACCES]
                ORDER BY ID ASC
            """)
        except Exception:
            try:
                cursor.execute("SELECT ID, Nom FROM [dbo].[WEB_ATELIER_ACCES] ORDER BY ID ASC")
                return [
                    {"id": row.ID, "nom": row.Nom or "", "a_mot_de_passe": False, "archive": False}
                    for row in cursor.fetchall()
                ]
            except Exception as e2:
                print(f"Erreur get_all_ateliers: {e2}")
                import traceback
                traceback.print_exc()
                return []
        rows = cursor.fetchall()
        result = []
        for row in rows:
            item = {"id": row.ID, "nom": row.Nom or ""}
            item["a_mot_de_passe"] = getattr(row, "mdp", None) is not None and str(getattr(row, "mdp", "") or "").strip() != ""
            item["archive"] = bool(getattr(row, "archive", False)) if getattr(row, "archive", None) is not None else False
            result.append(item)
        return result


def get_atelier_by_id(atelier_id):
    """Récupère un atelier par son ID"""
    with get_db_cursor() as cursor:
        try:
            cursor.execute("""
                SELECT ID, Nom, mdp, archive
                FROM [dbo].[WEB_ATELIER_ACCES] WHERE ID = ?
            """, (atelier_id,))
            row = cursor.fetchone()
            if row:
                item = {"id": row.ID, "nom": row.Nom or ""}
                item["a_mot_de_passe"] = getattr(row, "mdp", None) is not None and str(getattr(row, "mdp", "") or "").strip() != ""
                item["archive"] = bool(getattr(row, "archive", False)) if getattr(row, "archive", None) is not None else False
                return item
            return None
        except Exception as e:
            try:
                cursor.execute("SELECT ID, Nom FROM [dbo].[WEB_ATELIER_ACCES] WHERE ID = ?", (atelier_id,))
                row = cursor.fetchone()
                if row:
                    return {"id": row.ID, "nom": row.Nom or "", "a_mot_de_passe": False, "archive": False}
            except Exception:
                pass
            print(f"Erreur lors de la récupération de l'atelier: {e}")
            import traceback
            traceback.print_exc()
            return None


def create_atelier(nom):
    """Crée un nouvel atelier (mdp par défaut 000000, archive=0)"""
    with get_db_cursor() as cursor:
        try:
            nom = (nom or "").strip()
            if not nom:
                return {"success": False, "error": "Le nom de l'atelier est requis"}
            mdp_hash = bcrypt.hashpw(MDP_ATELIER_DEFAUT.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            try:
                cursor.execute("""
                    INSERT INTO [dbo].[WEB_ATELIER_ACCES] (Nom, mdp, archive) VALUES (?, ?, 0)
                """, (nom, mdp_hash))
            except Exception:
                cursor.execute("""
                    INSERT INTO [dbo].[WEB_ATELIER_ACCES] (Nom) VALUES (?)
                """, (nom,))
            cursor.connection.commit()
            return {"success": True, "message": f"Atelier « {nom} » créé avec succès (mdp par défaut: {MDP_ATELIER_DEFAUT})"}
        except Exception as e:
            print(f"Erreur lors de la création de l'atelier: {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}


def update_atelier(atelier_id, nom):
    """Met à jour le nom d'un atelier"""
    with get_db_cursor() as cursor:
        try:
            nom = (nom or "").strip()
            if not nom:
                return {"success": False, "error": "Le nom de l'atelier est requis"}
            cursor.execute("""
                UPDATE [dbo].[WEB_ATELIER_ACCES] SET Nom = ? WHERE ID = ?
            """, (nom, atelier_id))
            if cursor.rowcount == 0:
                return {"success": False, "error": "Atelier non trouvé"}
            cursor.connection.commit()
            return {"success": True, "message": "Atelier modifié avec succès"}
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'atelier: {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}


def set_atelier_mdp(atelier_id, new_mdp, old_mdp=None):
    """Définit ou met à jour le mot de passe d'un atelier (bcrypt)."""
    with get_db_cursor() as cursor:
        try:
            cursor.execute("SELECT ID, mdp FROM [dbo].[WEB_ATELIER_ACCES] WHERE ID = ?", (atelier_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Atelier non trouvé"}
            mdp_actuel = getattr(row, "mdp", None)
            mdp_actuel = _normalize_bcrypt_hash(mdp_actuel) if mdp_actuel else None
            if mdp_actuel and mdp_actuel.strip():
                if not old_mdp:
                    return {"success": False, "error": "L'ancien mot de passe est requis"}
                if not bcrypt.checkpw(old_mdp.encode("utf-8"), mdp_actuel.encode("utf-8")):
                    return {"success": False, "error": "Ancien mot de passe incorrect"}
            if not new_mdp or len(new_mdp) < 6:
                return {"success": False, "error": "Le mot de passe doit contenir au moins 6 caractères"}
            hash_new = bcrypt.hashpw(new_mdp.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cursor.execute("UPDATE [dbo].[WEB_ATELIER_ACCES] SET mdp = ? WHERE ID = ?", (hash_new, atelier_id))
            cursor.connection.commit()
            return {"success": True, "message": "Mot de passe atelier modifié avec succès"}
        except Exception as e:
            print(f"Erreur set_atelier_mdp: {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}


def archive_atelier(atelier_id, archive=True):
    """Archive ou désarchive un atelier."""
    with get_db_cursor() as cursor:
        try:
            val = 1 if archive else 0
            cursor.execute("UPDATE [dbo].[WEB_ATELIER_ACCES] SET archive = ? WHERE ID = ?", (val, atelier_id))
            if cursor.rowcount == 0:
                return {"success": False, "error": "Atelier non trouvé"}
            cursor.connection.commit()
            return {"success": True, "message": "Atelier archivé avec succès" if archive else "Atelier désarchivé avec succès"}
        except Exception as e:
            print(f"Erreur archive_atelier: {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}


def delete_atelier(atelier_id):
    """Supprime un atelier"""
    with get_db_cursor() as cursor:
        try:
            cursor.execute("DELETE FROM [dbo].[WEB_ATELIER_ACCES] WHERE ID = ?", (atelier_id,))
            if cursor.rowcount == 0:
                return {"success": False, "error": "Atelier non trouvé"}
            cursor.connection.commit()
            return {"success": True, "message": "Atelier supprimé avec succès"}
        except Exception as e:
            print(f"Erreur lors de la suppression de l'atelier: {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()
            return {"success": False, "error": str(e)}
