# -*- coding: utf-8 -*-
"""
Routes Projet 28 – Rapport de Visite Client (migration Prinects Projet 4).
Préfixe /projet28. Contenu intégré dans base.html (header/footer portail).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from db import get_db_cursor, get_contact_principal, creer_prospect, ajouter_contact, get_contact_by_id
from logic.auth import login_required, has_project_access, is_super_user, get_user_sections
from logic import projet28 as p28
from datetime import datetime

projet28_bp = Blueprint('projet28', __name__, url_prefix='/projet28')

PROJET28_SECTION_KEYS = p28.PROJET28_SECTION_KEYS


def _current_user():
    return session.get('username') or session.get('nom') or str(session.get('matricule', 'user'))


def _check_access():
    return has_project_access(28) or is_super_user()


def get_projet28_allowed_sections():
    if is_super_user():
        return list(PROJET28_SECTION_KEYS.values())
    raw = get_user_sections(28)
    allowed = []
    for s in raw:
        nom = (s.get('nom') or s.get('Nom') or '').strip()
        key = PROJET28_SECTION_KEYS.get(nom)
        if not key and nom:
            nl = nom.lower()
            if 'nouveau' in nl or 'rapport' in nl:
                key = 'nouveau'
            elif 'historique' in nl:
                key = 'historique'
            elif 'tableau' in nl or 'bord' in nl or 'dashboard' in nl:
                key = 'dashboard'
        if key and key not in allowed:
            allowed.append(key)
    return allowed


@projet28_bp.before_request
def _projet28_before():
    from logic.auth import is_authenticated
    p28.init_projet28()
    if not is_authenticated():
        return redirect(url_for('auth.login', next=request.url))
    if not _check_access():
        return redirect(url_for('index'))

# =============================================
# Routes principales
# =============================================

@projet28_bp.route("/", methods=["GET", "POST"])
def rapport_visite():
    if request.method == "POST":
        try:
            data = request.form
            user = _current_user()
            is_new = data.get("is_new_prospect") == "true"

            if is_new:
                id_societe = creer_prospect(
                    raison_sociale=data.get("raison_sociale"),
                    ville=data.get("ville"),
                    pays=data.get("pays"),
                    telephone=data.get("telephone"),
                    email=data.get("email"),
                    id_categorie=data.get("id_categorie") or None,
                )
                id_personne = ajouter_contact(
                    id_societe=id_societe,
                    nom=data.get("contact_nom"),
                    prenom=data.get("contact_prenom") or "",
                    telephone=data.get("contact_telephone"),
                    email=data.get("contact_email"),
                    id_fonction=data.get("id_fonction") or data.get("contact_fonction") or None,
                )
            else:
                id_societe = data.get("id_societe")
                id_personne = data.get("id_personne")
                id_fonction = data.get("id_fonction") or data.get("contact_fonction")
                if id_personne and id_fonction:
                    with get_db_cursor() as cursor:
                        cursor.execute("DELETE FROM PERSONNES_FONCTIONS WHERE ID_PERSONNE = ?", id_personne)
                        cursor.execute(
                            "INSERT INTO PERSONNES_FONCTIONS (ID_PERSONNE, ID_FONCTION, Ordre) VALUES (?, ?, 1)",
                            (id_personne, id_fonction),
                        )
                        cursor.connection.commit()

            action_selects = request.form.getlist("action_select[]")
            action_priorities = request.form.getlist("action_priority[]")
            action_dates = request.form.getlist("date_echeance[]")

            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO VISITES_CLIENTS
                    (ID_SOCIETE, RaisonSociale, DateVisite, NatureVisite, Sujets, Bilan, Visiteur, CreePar, CreeLe)
                    OUTPUT INSERTED.ID
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    id_societe,
                    data.get('raison_sociale'),
                    data.get('date_visite'),
                    data.get('nature_visite'),
                    data.get('resume_visite'),
                    data.get('bilan'),
                    data.get('visiteur'),
                    user,
                ))
                id_visite = cursor.fetchone()[0]

                if id_personne:
                    try:
                        cursor.execute(
                            "INSERT INTO VISITES_PERSONNES (ID_VISITE, ID_PERSONNE) VALUES (?, ?)",
                            (id_visite, id_personne),
                        )
                    except Exception as e:
                        print(f"[projet28] VISITES_PERSONNES: {e}")

                for action_id, priority, date_echeance in zip(action_selects, action_priorities, action_dates):
                    if not action_id:
                        continue
                    cursor.execute(
                        "SELECT DESCRIPTION FROM ACTIONS_PREDEFINIES WHERE ID = ?",
                        (action_id,),
                    )
                    row = cursor.fetchone()
                    description = row.DESCRIPTION if row else str(action_id)
                    cursor.execute("""
                        INSERT INTO ACTIONS_VISITE
                        (ID_VISITE, DESCRIPTION, PRIORITE, DATE_ECHEANCE, CREE_PAR)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        id_visite,
                        description,
                        priority,
                        date_echeance if date_echeance else None,
                        user,
                    ))

                cursor.connection.commit()

            flash("Rapport enregistré avec succès.", "success")
            return redirect(url_for("projet28.rapport_visite"))

        except Exception as e:
            print(f"Erreur lors de l'enregistrement de la visite: {str(e)}")
            flash(f"Erreur lors de l'enregistrement: {str(e)}", "error")
            return redirect(url_for("projet28.rapport_visite"))

    return render_template("projet28.html", allowed_sections=get_projet28_allowed_sections(), section='nouveau')

@projet28_bp.route("/historique", methods=["GET"])
def historique_visites():
    return render_template("projet28_historique.html")

@projet28_bp.route("/visite/<int:id_visite>", methods=["GET"])
def details_visite(id_visite):
    try:
        with get_db_cursor() as cursor:
            # Récupérer les détails de la visite
            cursor.execute("""
                SELECT 
                    V.ID,
                    V.DateVisite,
                    V.NatureVisite,
                    V.Sujets,
                    V.Bilan,
                    V.Visiteur,
                    V.RaisonSociale,
                    V.Objet,
                    V.Origine,
                    S.Ville,
                    S.Telephone,
                    S.Mail,
                    P.Nom as NomPays
                FROM VISITES_CLIENTS V
                LEFT JOIN SOCIETES_ADRESSES S ON S.ID_SOCIETE = V.ID_SOCIETE
                LEFT JOIN PAYS P ON P.ID = S.ID_PAYS
                WHERE V.ID = ?
            """, id_visite)
            visite = cursor.fetchone()
            
            if not visite:
                return render_template("error.html", message="Visite non trouvée"), 404

            # Convertir la date en objet datetime si c'est une chaîne
            if isinstance(visite.DateVisite, str):
                try:
                    visite.DateVisite = datetime.strptime(visite.DateVisite, '%Y-%m-%d').date()
                except ValueError:
                    visite.DateVisite = None

            # Récupérer les actions de la visite
            cursor.execute("""
                SELECT 
                    A.ID,
                    A.DESCRIPTION,
                    A.DATE_ECHEANCE,
                    A.STATUT,
                    A.PRIORITE,
                    A.NOTES,
                    S.COULEUR as COULEUR_STATUT,
                    P.COULEUR as COULEUR_PRIORITE
                FROM ACTIONS_VISITE A
                LEFT JOIN STATUTS_ACTION S ON S.NOM = A.STATUT
                LEFT JOIN PRIORITES_ACTION P ON P.NOM = A.PRIORITE
                WHERE A.ID_VISITE = ?
                ORDER BY A.DATE_ECHEANCE ASC, P.ORDRE DESC
            """, id_visite)
            actions = cursor.fetchall()

            # Convertir les dates d'échéance des actions en objets datetime si ce sont des chaînes
            for action in actions:
                if isinstance(action.DATE_ECHEANCE, str):
                    try:
                        action.DATE_ECHEANCE = datetime.strptime(action.DATE_ECHEANCE, '%Y-%m-%d').date()
                    except ValueError:
                        action.DATE_ECHEANCE = None

            # Récupérer les contacts présents lors de la visite
            try:
                cursor.execute("""
                    SELECT 
                        P.Nom,
                        P.Prenom,
                        P.Telephone,
                        P.Mobile,
                        M.Mail,
                        FCT.Fonction
                    FROM VISITES_PERSONNES VP
                    INNER JOIN PERSONNES P ON P.ID = VP.ID_PERSONNE
                    LEFT JOIN (
                        SELECT ID_PERSONNE, Mail
                        FROM PERSONNES_MAIL
                        WHERE ParDefaut = 1
                    ) M ON M.ID_PERSONNE = P.ID
                    LEFT JOIN (
                        SELECT PF.ID_PERSONNE, FO.Nom AS Fonction, 
                               ROW_NUMBER() OVER (PARTITION BY PF.ID_PERSONNE ORDER BY PF.Ordre ASC) AS rn
                        FROM PERSONNES_FONCTIONS PF
                        INNER JOIN FONCTIONS FO ON FO.ID = PF.ID_FONCTION
                    ) FCT ON FCT.ID_PERSONNE = P.ID AND FCT.rn = 1
                    WHERE VP.ID_VISITE = ?
                """, id_visite)
                contacts = cursor.fetchall()
            except Exception as e:
                print(f"Erreur lors de la récupération des contacts: {str(e)}")
                contacts = []

            return render_template("projet28_details_visite.html", 
                visite=visite,
                actions=actions,
                contacts=contacts
            )

    except Exception as e:
        print(f"Erreur lors de la récupération des détails de la visite: {str(e)}")
        return render_template("error.html", message=str(e)), 500

@projet28_bp.route("/visite/<int:id_visite>/edit", methods=["GET"])
def edit_visite(id_visite):
    try:
        with get_db_cursor() as cursor:
            # Récupérer les détails de la visite
            cursor.execute("""
                SELECT 
                    V.ID,
                    V.DateVisite,
                    V.NatureVisite,
                    V.Sujets,
                    V.Bilan,
                    V.Visiteur,
                    V.RaisonSociale,
                    V.ID_SOCIETE,
                    V.Objet,
                    V.Origine
                FROM VISITES_CLIENTS V
                WHERE V.ID = ?
            """, id_visite)
            visite = cursor.fetchone()
            
            if not visite:
                return render_template("error.html", message="Visite non trouvée"), 404

            # Convertir la date en objet datetime si c'est une chaîne
            if isinstance(visite.DateVisite, str):
                try:
                    visite.DateVisite = datetime.strptime(visite.DateVisite, '%Y-%m-%d').date()
                except ValueError:
                    visite.DateVisite = None

            # Récupérer les actions de la visite
            cursor.execute("""
                SELECT 
                    A.ID,
                    A.DESCRIPTION,
                    A.DATE_ECHEANCE,
                    A.PRIORITE
                FROM ACTIONS_VISITE A
                WHERE A.ID_VISITE = ?
                ORDER BY A.DATE_ECHEANCE ASC
            """, id_visite)
            actions = cursor.fetchall()

            # Convertir les dates d'échéance des actions en objets datetime si ce sont des chaînes
            for action in actions:
                if isinstance(action.DATE_ECHEANCE, str):
                    try:
                        action.DATE_ECHEANCE = datetime.strptime(action.DATE_ECHEANCE, '%Y-%m-%d').date()
                    except ValueError:
                        action.DATE_ECHEANCE = None

            return render_template("projet28_edit_visite.html", 
                visite=visite,
                actions=actions
            )

    except Exception as e:
        print(f"Erreur lors de la récupération des détails de la visite: {str(e)}")
        return render_template("error.html", message=str(e)), 500

@projet28_bp.route("/visite/<int:id_visite>/update", methods=["POST"])
def update_visite(id_visite):
    try:
        with get_db_cursor() as cursor:
            # Mettre à jour les détails de la visite
            cursor.execute("""
                UPDATE VISITES_CLIENTS
                SET 
                    DateVisite = ?,
                    NatureVisite = ?,
                    Sujets = ?,
                    Bilan = ?
                WHERE ID = ?
            """, (
                request.form.get('date_visite'),
                request.form.get('nature_visite'),
                request.form.get('sujets'),
                request.form.get('bilan'),
                id_visite
            ))

            # Supprimer les anciennes actions
            cursor.execute("DELETE FROM ACTIONS_VISITE WHERE ID_VISITE = ?", id_visite)

            # Ajouter les nouvelles actions
            descriptions = request.form.getlist('action_description[]')
            dates_echeance = request.form.getlist('date_echeance[]')
            priorities = request.form.getlist('action_priority[]')

            for description, date_echeance, priority in zip(descriptions, dates_echeance, priorities):
                if description:  # Ne pas ajouter d'actions vides
                    cursor.execute("""
                        INSERT INTO ACTIONS_VISITE 
                        (ID_VISITE, DESCRIPTION, DATE_ECHEANCE, PRIORITE, CREE_PAR)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        id_visite,
                        description,
                        date_echeance if date_echeance else None,
                        priority,
                        _current_user(),
                    ))

            cursor.connection.commit()
            flash("Visite mise à jour avec succès", "success")
            return redirect(url_for('projet28.details_visite', id_visite=id_visite))

    except Exception as e:
        print(f"Erreur lors de la mise à jour de la visite: {str(e)}")
        flash(f"Erreur lors de la mise à jour: {str(e)}", "error")
        return redirect(url_for('projet28.edit_visite', id_visite=id_visite))

@projet28_bp.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("projet28_dashboard.html")

# =============================================
# API - Gestion des sociétés
# =============================================

@projet28_bp.route("/api/societes", methods=["GET"])
def get_societes():
    filter_query = request.args.get("filter", "").strip().lower()
    
    with get_db_cursor() as cursor:
        sql_query = """
            SELECT 
                A.ID_SOCIETE AS ID,
                A.Nom AS NomClient,
                A.Ville,
                P.Nom AS NomPays,
                A.Telephone,
                A.Fax,
                A.Mail,
                IC.NOM AS Importance,
                S.ID_CATEGORIE
            FROM [SOCIETES_ADRESSES] A
            LEFT JOIN PAYS P ON P.ID = A.ID_PAYS
            LEFT JOIN SOCIETES_IMPORTANCE SI ON SI.ID_SOCIETE = A.ID_SOCIETE
            LEFT JOIN IMPORTANCE_CLIENT IC ON IC.ID = SI.ID_IMPORTANCE
            LEFT JOIN SOCIETES S ON S.ID = A.ID_SOCIETE
            WHERE LOWER(A.Nom) LIKE LOWER(?) AND S.Archive = 0
            ORDER BY A.Nom
        """
        filter_term = f"%{filter_query}%"
        cursor.execute(sql_query, filter_term)
        rows = cursor.fetchall()

    societes = []
    for row in rows:
        societes.append({
            "id": row.ID,
            "raison_sociale": row.NomClient,
            "ville": row.Ville,
            "pays": row.NomPays,
            "telephone": row.Telephone,
            "fax": row.Fax,
            "email": row.Mail,
            "importance": row.Importance or "Moyen",
            "id_categorie": row.ID_CATEGORIE
        })

    return jsonify(societes)

@projet28_bp.route("/api/societes", methods=["POST"])
def create_societe():
    try:
        data = request.get_json()
        
        # Vérification des champs obligatoires
        if not data.get('RaiSocTri'):
            return jsonify({"error": "Le nom de la société est obligatoire"}), 400
            
        # Conversion des champs texte en majuscules
        rai_soc_tri = data.get('RaiSocTri', '').upper()
        ville = data.get('Ville', '').upper()
        telex = data.get('Telex', '').upper()
        site_web = data.get('SiteWeb', '').upper()
        siret = data.get('SIRET', '').upper()
        email = data.get('Email', '').upper()
        fax = data.get('Fax', '').upper()
            
        with get_db_cursor() as cursor:
            # Insertion dans la table SOCIETES
            cursor.execute("""
                INSERT INTO SOCIETES (
                    RaiSocTri, ID_CATEGORIE, ID_SECTEUR, ID_ACTIVITE, ID_DEVISE, 
                    ID_EXPEDITEUR, Archive, Telex, SiteWeb, DateCreation, 
                    DateModification, Langue, Effectif, CA, IdTVA, Modele, 
                    DepotFichiers, ApprobationEnLigne, ExpediteurSocUtil, SIRET, 
                    ID_PAP_CERTIF_FAMILLE
                ) 
                OUTPUT INSERTED.ID
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rai_soc_tri,
                data.get('ID_CATEGORIE'),
                data.get('ID_SECTEUR'),
                data.get('ID_ACTIVITE'),
                data.get('ID_DEVISE', 'TND'),
                data.get('ID_EXPEDITEUR'),
                data.get('Archive', 0),
                telex,
                site_web,
                data.get('DateCreation', datetime.now()),
                data.get('DateModification', datetime.now()),
                1036,  # Langue par défaut (1036 pour français)
                data.get('Effectif'),
                data.get('CA'),
                data.get('IdTVA'),
                data.get('Modele', 0),
                data.get('DepotFichiers', 0),
                data.get('ApprobationEnLigne', 0),
                data.get('ExpediteurSocUtil', 0),
                siret,
                data.get('ID_PAP_CERTIF_FAMILLE')
            ))
            
            # Récupérer l'ID de la société créée directement depuis l'OUTPUT
            new_id = cursor.fetchone()[0]
            
            if not new_id:
                raise Exception("Impossible de récupérer l'ID de la société créée")
            
            # Créer une adresse par défaut pour la société
            cursor.execute("""
                INSERT INTO SOCIETES_ADRESSES (
                    ID_SOCIETE, Nom, Ville, Telephone, Fax, Mail
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                new_id,
                rai_soc_tri,
                ville,
                telex,
                fax,
                email
            ))
            
            cursor.connection.commit()
            return jsonify({"id": new_id, "message": "Société créée avec succès"})
            
    except Exception as e:
        print(f"Erreur lors de la création de la société: {str(e)}")
        return jsonify({"error": str(e)}), 500

@projet28_bp.route("/api/update_societe", methods=["POST"])
def update_societe():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Données manquantes"}), 400

        id_societe = data.get('id_societe')
        if not id_societe:
            return jsonify({"success": False, "error": "ID société manquant"}), 400

        with get_db_cursor() as cursor:
            # Mise à jour de la table SOCIETES_ADRESSES
            cursor.execute("""
                UPDATE SOCIETES_ADRESSES
                SET 
                    Nom = ?,
                    Ville = ?,
                    Telephone = ?,
                    Fax = ?,
                    Mail = ?,
                    ID_PAYS = ?
                WHERE ID_SOCIETE = ?
            """, (
                data.get('raison_sociale', '').upper(),
                data.get('ville', '').upper(),
                data.get('telephone', ''),
                data.get('fax', '').upper(),
                data.get('email', '').upper(),
                data.get('pays'),
                id_societe
            ))

            # Mise à jour de la catégorie dans SOCIETES
            if data.get('id_categorie'):
                cursor.execute("""
                    UPDATE SOCIETES
                    SET ID_CATEGORIE = ?
                    WHERE ID = ?
                """, (data.get('id_categorie'), id_societe))

            # Mise à jour de l'importance
            if data.get('importance'):
                cursor.execute("""
                    MERGE INTO SOCIETES_IMPORTANCE AS target
                    USING (SELECT ? AS ID_SOCIETE, ? AS ID_IMPORTANCE) AS source
                    ON target.ID_SOCIETE = source.ID_SOCIETE
                    WHEN MATCHED THEN
                        UPDATE SET ID_IMPORTANCE = source.ID_IMPORTANCE,
                                  DATE_MODIFICATION = GETDATE(),
                                  MODIFIE_PAR = ?
                    WHEN NOT MATCHED THEN
                        INSERT (ID_SOCIETE, ID_IMPORTANCE, MODIFIE_PAR)
                        VALUES (source.ID_SOCIETE, source.ID_IMPORTANCE, ?);
                """, (
                    id_societe,
                    data.get('importance'),
                    _current_user(),
                    _current_user(),
                ))

            cursor.connection.commit()
            return jsonify({"success": True, "message": "Société mise à jour avec succès"})
            
    except Exception as e:
        print(f"Erreur lors de la mise à jour de la société: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@projet28_bp.route("/api/societes/<int:id>", methods=["GET"])
def get_societe_details(id):
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    S.ID,
                    A.Nom AS raison_sociale,
                    A.Ville,
                    A.ID_PAYS,
                    A.Telephone,
                    A.Fax,
                    A.Mail AS email,
                    S.ID_CATEGORIE,
                    IC.NOM AS importance
                FROM SOCIETES S
                LEFT JOIN SOCIETES_ADRESSES A ON A.ID_SOCIETE = S.ID
                LEFT JOIN SOCIETES_IMPORTANCE SI ON SI.ID_SOCIETE = S.ID
                LEFT JOIN IMPORTANCE_CLIENT IC ON IC.ID = SI.ID_IMPORTANCE
                WHERE S.ID = ?
            """, id)
            row = cursor.fetchone()
            
            if not row:
                return jsonify({"error": "Société non trouvée"}), 404
                
            societe = {
                "id": row.ID,
                "raison_sociale": row.raison_sociale,
                "ville": row.Ville,
                "id_pays": row.ID_PAYS,
                "telephone": row.Telephone,
                "fax": row.Fax,
                "email": row.email,
                "id_categorie": row.ID_CATEGORIE,
                "importance": row.importance
            }
            
            return jsonify(societe)
            
    except Exception as e:
        print(f"Erreur lors de la récupération des détails de la société: {str(e)}")
        return jsonify({"error": str(e)}), 500

# =============================================
# API - Gestion des contacts
# =============================================

@projet28_bp.route("/api/contacts", methods=["GET"])
def get_contacts():
    id_societe = request.args.get("id_societe")
    if not id_societe:
        return jsonify({"error": "ID société manquant"}), 400

    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                P.ID AS ID_PERSONNE,
                P.Nom,
                P.Prenom,
                P.Telephone,
                P.Mobile,
                M.Mail,
                FCT.Fonction,
                FCT.ID_FONCTION
            FROM SOCIETES_PERSONNES SP
            INNER JOIN PERSONNES P ON P.ID = SP.ID_PERSONNE
            LEFT JOIN (
                SELECT ID_PERSONNE, Mail
                FROM PERSONNES_MAIL
                WHERE ParDefaut = 1
            ) M ON M.ID_PERSONNE = P.ID
            LEFT JOIN (
                SELECT PF.ID_PERSONNE, FO.Nom AS Fonction, FO.ID AS ID_FONCTION,
                       ROW_NUMBER() OVER (PARTITION BY PF.ID_PERSONNE ORDER BY PF.Ordre ASC) AS rn
                FROM PERSONNES_FONCTIONS PF
                INNER JOIN FONCTIONS FO ON FO.ID = PF.ID_FONCTION
            ) FCT ON FCT.ID_PERSONNE = P.ID AND FCT.rn = 1
            WHERE SP.ID_SOCIETE = ?
        """, id_societe)

        rows = cursor.fetchall()
        contacts = []
        for row in rows:
            contacts.append({
                "id": row.ID_PERSONNE,
                "nom": row.Nom,
                "prenom": row.Prenom,
                "telephone": row.Telephone or row.Mobile,
                "email": row.Mail,
                "fonction": row.Fonction,
                "id_fonction": row.ID_FONCTION
            })

    return jsonify(contacts)

@projet28_bp.route("/api/contacts/<int:id_contact>", methods=["GET"])
def get_contact(id_contact):
    contact = get_contact_by_id(id_contact)
    if contact:
        return jsonify(contact)
    return jsonify({"error": "Aucun contact trouvé"}), 404

@projet28_bp.route("/api/contacts", methods=["POST"])
def add_contact():
    data = request.get_json()
    id_societe = data.get("id_societe")
    nom = data.get("nom")
    email = data.get("email")
    telephone = data.get("telephone")
    id_fonction = data.get("id_fonction")

    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO PERSONNES (Nom, Telephone)
            OUTPUT INSERTED.ID
            VALUES (?, ?)
        """, nom, telephone)
        id_personne = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO SOCIETES_PERSONNES (ID_SOCIETE, ID_PERSONNE)
            VALUES (?, ?)
        """, id_societe, id_personne)

        if email:
            cursor.execute("""
                INSERT INTO PERSONNES_MAIL (ID_PERSONNE, Mail, ParDefaut)
                VALUES (?, ?, 1)
            """, id_personne, email)

        if id_fonction:
            cursor.execute("""
                INSERT INTO PERSONNES_FONCTIONS (ID_PERSONNE, ID_FONCTION, Ordre)
                VALUES (?, ?, 1)
            """, id_personne, id_fonction)

        cursor.connection.commit()

    return jsonify({"success": True, "id_personne": id_personne})

@projet28_bp.route("/api/contacts/<int:id_contact>", methods=["PUT"])
def update_contact(id_contact):
    data = request.get_json()
    with get_db_cursor() as cursor:
        # Mise à jour des informations de base du contact
        cursor.execute("""
            UPDATE PERSONNES
            SET Nom = ?, Prenom = ?, Telephone = ?
            WHERE ID = ?
        """, (
            data.get("nom"),
            data.get("prenom"),
            data.get("telephone"),
            id_contact
        ))

        # Mise à jour de l'email si fourni
        if data.get("email"):
            cursor.execute("""
                UPDATE PERSONNES_MAIL
                SET Mail = ?
                WHERE ID_PERSONNE = ? AND ParDefaut = 1
            """, (
                data.get("email"),
                id_contact
            ))

        # Mise à jour de la fonction si fournie
        if data.get("id_fonction"):
            # Supprimer l'ancienne fonction
            cursor.execute("DELETE FROM PERSONNES_FONCTIONS WHERE ID_PERSONNE = ?", id_contact)
            # Ajouter la nouvelle fonction
            cursor.execute("""
                INSERT INTO PERSONNES_FONCTIONS (ID_PERSONNE, ID_FONCTION, Ordre)
                VALUES (?, ?, 1)
            """, (id_contact, data.get("id_fonction")))

        cursor.connection.commit()
    return jsonify({"success": True})

# =============================================
# API - Gestion des actions
# =============================================

@projet28_bp.route("/api/actions", methods=["GET"])
def get_actions():
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT ID, DESCRIPTION, PRIORITE_DEFAUT 
            FROM ACTIONS_PREDEFINIES 
            ORDER BY DESCRIPTION
        """)
        rows = cursor.fetchall()
        
    actions = [{
        "id": row.ID,
        "nom": row.DESCRIPTION,
        "description": row.DESCRIPTION,
        "priorite_defaut": row.PRIORITE_DEFAUT
    } for row in rows]
    return jsonify(actions)

@projet28_bp.route("/api/actions", methods=["POST"])
def add_action():
    data = request.get_json()
    id_visite = data.get("id_visite")
    description = data.get("description")
    date_echeance = data.get("date_echeance")
    priorite = data.get("priorite", "Normal")

    if not id_visite or not description:
        return jsonify({"error": "Données manquantes"}), 400

    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO ACTIONS_VISITE 
            (ID_VISITE, DESCRIPTION, DATE_ECHEANCE, PRIORITE, CREE_PAR)
            VALUES (?, ?, ?, ?, ?)
            OUTPUT INSERTED.ID
        """, (
            id_visite,
            description,
            date_echeance,
            priorite,
            _current_user(),
        ))
        id_action = cursor.fetchone()[0]
        cursor.connection.commit()

    return jsonify({"success": True, "id_action": id_action})

@projet28_bp.route("/api/actions/<int:id_action>", methods=["PUT"])
def update_action(id_action):
    data = request.get_json()
    statut = data.get("statut")
    notes = data.get("notes")

    if not id_action:
        return jsonify({"error": "ID action manquant"}), 400

    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE ACTIONS_VISITE
            SET STATUT = ?,
                NOTES = ?,
                MODIFIE_PAR = ?,
                MODIFIE_LE = GETDATE()
            WHERE ID = ?
        """, (
            statut,
            notes,
            _current_user(),
            id_action
        ))
        cursor.connection.commit()

    return jsonify({"success": True})

@projet28_bp.route("/api/actions/<int:id_action>", methods=["DELETE"])
def delete_action(id_action):
    if not id_action:
        return jsonify({"error": "ID action manquant"}), 400

    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM ACTIONS_VISITE WHERE ID = ?", id_action)
        cursor.connection.commit()

    return jsonify({"success": True})

@projet28_bp.route("/api/actions/a_venir", methods=["GET"])
def get_actions_a_venir():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    A.ID,
                    A.DESCRIPTION,
                    A.DATE_ECHEANCE,
                    A.STATUT,
                    A.PRIORITE,
                    A.NOTES,
                    V.RaisonSociale,
                    V.DateVisite,
                    V.Visiteur,
                    P.Nom + ' ' + P.Prenom as Contact
                FROM ACTIONS_VISITE A
                JOIN VISITES_CLIENTS V ON V.ID = A.ID_VISITE
                LEFT JOIN VISITES_PERSONNES VP ON VP.ID_VISITE = V.ID
                LEFT JOIN PERSONNES P ON P.ID = VP.ID_PERSONNE
                WHERE A.DATE_ECHEANCE >= GETDATE()
                ORDER BY A.DATE_ECHEANCE ASC
            """)
            actions = []
            for row in cursor.fetchall():
                # Gérer la date d'échéance
                date_echeance = row.DATE_ECHEANCE
                if isinstance(date_echeance, str):
                    try:
                        date_echeance = datetime.strptime(date_echeance, '%Y-%m-%d').date()
                    except ValueError:
                        date_echeance = None
                
                # Gérer la date de visite
                date_visite = row.DateVisite
                if isinstance(date_visite, str):
                    try:
                        date_visite = datetime.strptime(date_visite, '%Y-%m-%d').date()
                    except ValueError:
                        date_visite = None

                actions.append({
                    "id": row.ID,
                    "description": row.DESCRIPTION,
                    "date_echeance": date_echeance.strftime("%Y-%m-%d") if date_echeance else None,
                    "statut": row.STATUT,
                    "priorite": row.PRIORITE,
                    "notes": row.NOTES,
                    "raison_sociale": row.RaisonSociale,
                    "date_visite": date_visite.strftime("%Y-%m-%d") if date_visite else None,
                    "visiteur": row.Visiteur,
                    "contact": row.Contact
                })
            return jsonify(actions)
    except Exception as e:
        print(f"Erreur lors de la récupération des actions à venir: {str(e)}")
        return jsonify({"error": str(e)}), 500

# =============================================
# API - Données de référence
# =============================================

@projet28_bp.route("/api/pays", methods=["GET"])
def get_pays():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT ID, Nom FROM PAYS ORDER BY Nom")
        return jsonify([{"id": row.ID, "nom": row.Nom} for row in cursor.fetchall()])

@projet28_bp.route("/api/categories", methods=["GET"])
def get_categories():
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT ID, Nom FROM CATEGORIES_SOCIETES
            WHERE Archive = 0
            ORDER BY Nom
        """)
        rows = cursor.fetchall()
        categories = [{"id": row.ID, "nom": row.Nom} for row in rows]
    return jsonify(categories)

@projet28_bp.route("/api/fonctions", methods=["GET"])
def get_fonctions():
    try:
        with get_db_cursor() as cursor:
            print("Tentative de récupération des fonctions...")
            cursor.execute("SELECT ID, Nom FROM FONCTIONS WHERE Archive = 0 ORDER BY Nom")
            rows = cursor.fetchall()
            print(f"Nombre de fonctions trouvées: {len(rows)}")
            print(f"Fonctions: {rows}")
            fonctions = [{"id": row.ID, "nom": row.Nom} for row in rows]
            return jsonify(fonctions)
    except Exception as e:
        print(f"Erreur lors de la récupération des fonctions: {str(e)}")
        return jsonify({"error": str(e)}), 500

@projet28_bp.route("/api/statuts", methods=["GET"])
def get_statuts():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT NOM, COULEUR FROM STATUTS_ACTION ORDER BY ORDRE")
        rows = cursor.fetchall()
        statuts = [{"nom": row.NOM, "couleur": row.COULEUR} for row in rows]
    return jsonify(statuts)

@projet28_bp.route("/api/priorites", methods=["GET"])
def get_priorites():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT NOM, COULEUR FROM PRIORITES_ACTION ORDER BY ORDRE")
        rows = cursor.fetchall()
        priorites = [{"nom": row.NOM, "couleur": row.COULEUR} for row in rows]
    return jsonify(priorites)

@projet28_bp.route("/api/importance", methods=["GET"])
def get_importance():
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT ID, NOM, COULEUR 
            FROM IMPORTANCE_CLIENT 
            ORDER BY ORDRE
        """)
        rows = cursor.fetchall()
        importance = [{
            "id": row.ID,
            "nom": row.NOM,
            "couleur": row.COULEUR
        } for row in rows]
    return jsonify(importance)

# =============================================
# API - Historique et rapports
# =============================================

@projet28_bp.route("/api/historique", methods=["GET"])
def get_historique():
    try:
        query = request.args.get("query", "").strip().lower()
        print(f"Recherche d'historique avec la requête: {query}")

        with get_db_cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT 
                        V.ID,
                        V.DateVisite,
                        V.NatureVisite,
                        V.Sujets,
                        V.Bilan,
                        V.Visiteur,
                        V.RaisonSociale,
                        COUNT(A.ID) as NB_ACTIONS,
                        SUM(CASE WHEN A.STATUT = 'Terminé' THEN 1 ELSE 0 END) as NB_ACTIONS_TERMINEES
                    FROM VISITES_CLIENTS V
                    LEFT JOIN ACTIONS_VISITE A ON A.ID_VISITE = V.ID
                    WHERE V.RaisonSociale LIKE ?
                    GROUP BY V.ID, V.DateVisite, V.NatureVisite, V.Sujets, V.Bilan, V.Visiteur, V.RaisonSociale
                    ORDER BY V.DateVisite DESC
                """, f"%{query}%")
                rows = cursor.fetchall()
                print(f"Nombre de visites trouvées: {len(rows)}")
                
                visites = []
                for row in rows:
                    try:
                        # Gérer la date de visite
                        date_visite = row.DateVisite
                        if isinstance(date_visite, str):
                            try:
                                date_visite = datetime.strptime(date_visite, '%Y-%m-%d').date()
                            except ValueError:
                                date_visite = None
                        
                        visites.append({
                            "id": row.ID,
                            "date_visite": date_visite.strftime("%Y-%m-%d") if date_visite else None,
                            "nature_visite": row.NatureVisite,
                            "sujets": row.Sujets,
                            "bilan": row.Bilan,
                            "visiteur": row.Visiteur,
                            "raison_sociale": row.RaisonSociale,
                            "nb_actions": row.NB_ACTIONS,
                            "nb_actions_terminees": row.NB_ACTIONS_TERMINEES
                        })
                    except (AttributeError, TypeError) as e:
                        print(f"Erreur lors du traitement d'une ligne: {str(e)}")
                        continue
                
                print(f"Données formatées: {visites}")
                return jsonify(visites)
                
            except Exception as e:
                print(f"Erreur lors de l'exécution de la requête SQL: {str(e)}")
                return jsonify({"error": "Erreur lors de la récupération des données"}), 500
                
    except Exception as e:
        print(f"Erreur lors de la récupération de l'historique: {str(e)}")
        return jsonify({"error": "Erreur lors du traitement de la requête"}), 500


def ensure_projet28_in_web_projets():
    p28.init_projet28()
