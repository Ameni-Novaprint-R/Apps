from flask import Blueprint, render_template, jsonify, request
from db import (
    get_commandes_bat,
    update_date_bat,
    update_reception_elem,
    update_pourcentage_reception,
    envoyer_bat
)

bp = Blueprint("projet3", __name__, url_prefix="/projet3")

# Page HTML principale
@bp.route("/")
def page_projet3():
    return render_template("projet3.html")

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

# API pour mettre à jour la date BAT
@bp.route("/api/commandes/<int:id_commande>/date_bat", methods=["PUT"])
def maj_date_bat(id_commande):
    data = request.get_json() or {}
    date_bat = data.get("date_bat") or data.get("DteBat")
    if not date_bat:
        return jsonify({"success": False, "error": "date_bat requis"}), 400
    success = update_date_bat(id_commande, date_bat)
    return jsonify({"success": success})

# API pour mettre à jour la date de réception (met aussi % à 100)
@bp.route("/api/commandes/<int:id_commande>/date_reception", methods=["PUT"])
def maj_date_reception(id_commande):
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
