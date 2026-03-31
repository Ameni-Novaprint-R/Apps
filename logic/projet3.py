from flask import Blueprint, render_template, jsonify, request, session
from db import (
    get_db_cursor,
    get_commandes_bat,
    update_date_bat,
    update_reception_elem,
    update_pourcentage_reception,
    envoyer_bat
)
from logic.auth import is_super_user

bp = Blueprint("projet3", __name__, url_prefix="/projet3")

# Section "Tableau de suivi BAT" du projet 3 : seule l'action Saisie autorise la modification des dates BAT et réception
SECTION_TABLEAU_SUIVI_BAT = "Tableau de suivi BAT"
ACTION_SAISIE = "Saisie"


def _has_projet3_saisie_right_current_user():
    """
    Vérifie directement WEB_DROITS_ACCES pour l'utilisateur connecté :
    action contenant 'saisie' sur une section du projet 3 contenant 'bat'.
    Cette vérification est volontairement tolérante aux variantes d'intitulés.
    """
    try:
        matricule = session.get("matricule")
        nom_atelier = (session.get("atelier_nom") or session.get("nom") or "").strip()

        if matricule is None and not nom_atelier:
            return False

        with get_db_cursor() as cursor:
            if matricule is not None:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS nb
                    FROM dbo.WEB_DROITS_ACCES WDA
                    INNER JOIN dbo.WEB_ACTIONS WA ON WA.ID = WDA.ID_Action
                    INNER JOIN dbo.WEB_SECTIONS WS ON WS.ID = WA.ID_Section
                    INNER JOIN dbo.WEB_PROJETS WP ON WP.ID = WS.ID_Proj
                    WHERE WP.NumProj = 3
                      AND (WDA.Autorise = 1 OR WDA.Autorise IS NULL)
                      AND WDA.Matricule = ?
                      AND LOWER(RTRIM(LTRIM(WA.Action))) LIKE '%saisie%'
                      AND LOWER(RTRIM(LTRIM(WS.Nom))) LIKE '%bat%'
                    """,
                    (matricule,),
                )
            else:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS nb
                    FROM dbo.WEB_DROITS_ACCES WDA
                    INNER JOIN dbo.WEB_ACTIONS WA ON WA.ID = WDA.ID_Action
                    INNER JOIN dbo.WEB_SECTIONS WS ON WS.ID = WA.ID_Section
                    INNER JOIN dbo.WEB_PROJETS WP ON WP.ID = WS.ID_Proj
                    WHERE WP.NumProj = 3
                      AND (WDA.Autorise = 1 OR WDA.Autorise IS NULL)
                      AND WDA.NomAtelier = ?
                      AND LOWER(RTRIM(LTRIM(WA.Action))) LIKE '%saisie%'
                      AND LOWER(RTRIM(LTRIM(WS.Nom))) LIKE '%bat%'
                    """,
                    (nom_atelier,),
                )
            row = cursor.fetchone()
            return bool(row and getattr(row, "nb", 0) > 0)
    except Exception as e:
        print(f"[projet3] _has_projet3_saisie_right_current_user: {e}")
        return False


def can_saisie_dates_bat():
    """True si l'utilisateur connecté peut saisir les dates BAT et réception (super-user ou droit Saisie sur la section Tableau de suivi BAT)."""
    if is_super_user():
        return True
    return _has_projet3_saisie_right_current_user()


# Page HTML principale
@bp.route("/")
def page_projet3():
    return render_template("projet3.html", can_saisie_dates_bat=can_saisie_dates_bat())

# API pour retourner les données du suivi BAT
@bp.route("/api/commandes")
def api_commandes_bat():
    rows = get_commandes_bat()
    data = [
        {
            "ID": row["ID"],
            "Numero": row["Numero"],
            "RaisonSociale": row["RaisonSociale"],
            "DteBat": row["DteBat"].strftime('%Y-%m-%d') if row["DteBat"] else "",
            "DteReceptElem": row["DteReceptElem"].strftime('%Y-%m-%d') if row["DteReceptElem"] else "",
            "EtatPrepress": row["EtatPrepress"],
            "PourcentageReceptElem": row["PourcentageReceptElem"],
            "EtatLiv": row["EtatLiv"]
        } for row in rows
    ]
    return jsonify({"data": data})

# API pour mettre à jour la date BAT (réservé aux utilisateurs ayant l'action Saisie sur la section Tableau de suivi BAT)
@bp.route("/api/commandes/<int:id_commande>/date_bat", methods=["PUT"])
def maj_date_bat(id_commande):
    if not can_saisie_dates_bat():
        return jsonify({"success": False, "error": "Droit de saisie requis pour modifier la date BAT"}), 403
    data = request.get_json() or {}
    date_bat = data.get("date_bat") or data.get("DteBat")
    if not date_bat:
        return jsonify({"success": False, "error": "date_bat requis"}), 400
    success = update_date_bat(id_commande, date_bat)
    return jsonify({"success": success})

# API pour mettre à jour la date de réception (réservé aux utilisateurs ayant l'action Saisie sur la section Tableau de suivi BAT)
@bp.route("/api/commandes/<int:id_commande>/date_reception", methods=["PUT"])
def maj_date_reception(id_commande):
    if not can_saisie_dates_bat():
        return jsonify({"success": False, "error": "Droit de saisie requis pour modifier la date de réception"}), 403
    data = request.get_json() or {}
    date_reception = data.get("date_reception")
    success = update_reception_elem(id_commande, date_reception)
    return jsonify({"success": success})

# API pour valider envoi BAT
@bp.route("/api/commandes/<int:id_commande>/envoi", methods=["PUT"])
def maj_envoi_bat(id_commande):
    return jsonify({"success": envoyer_bat(id_commande)})

# API pour mettre à jour le pourcentage de réception (0%, 50%, 100%)
@bp.route("/api/commandes/<int:id_commande>/pourcentage", methods=["PUT"])
def maj_pourcentage(id_commande):
    data = request.get_json() or {}
    pourcentage = data.get("pourcentage")
    if pourcentage is None:
        return jsonify({"success": False, "error": "pourcentage requis"}), 400
    success = update_pourcentage_reception(id_commande, pourcentage)
    return jsonify({"success": success})
