#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes Flask pour le Projet 13 - Suivi Production
Adapté du Projet 5 de prinects
"""

from flask import Blueprint, render_template, request, jsonify
from db import get_db_cursor
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import re
from dateutil import parser

projet13_bp = Blueprint("projet13", __name__, url_prefix="/projet13")

def operation_autorisee(id_poste, id_operation):
    """Vérifie si une opération est autorisée pour un poste donné"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM GP_POSTES_OP 
                WHERE ID_POSTE = ? AND ID = ? AND Archive = 0
            """, (id_poste, id_operation))
            count = cursor.fetchone()[0]
            return count > 0
    except Exception:
        return False

@projet13_bp.route("/")
def index():
    return render_template("projet13.html")


@projet13_bp.route("/planning")
def planning_journalier():
    """Page Planning Journalier - Tous les postes (vue type prinects)."""
    return render_template("projet13_planning.html")


@projet13_bp.route("/api/planning/stats")
def api_planning_stats():
    """Stats pour la page planning : total, planifiées, non planifiées."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) AS total,
                    SUM(CASE WHEN FT.CodIndAv IN (2, 3) THEN 1 ELSE 0 END) AS planifiees,
                    SUM(CASE WHEN FT.CodIndAv IN (0, 1) OR FT.CodIndAv IS NULL THEN 1 ELSE 0 END) AS non_planifiees
                FROM GP_FICHES_TRAVAIL FT
                JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
                WHERE C.Termine = 0 AND C.Annule = 0
            """)
            row = cursor.fetchone()
        total = row.total or 0
        planifiees = row.planifiees or 0
        non_planifiees = row.non_planifiees or 0
        return jsonify({
            "total": total,
            "planifiees": planifiees,
            "non_planifiees": non_planifiees
        })
    except Exception as e:
        return jsonify({"total": 0, "planifiees": 0, "non_planifiees": 0, "error": str(e)})


@projet13_bp.route("/api/planning/fiches_non_planifiees")
def api_planning_fiches_non_planifiees():
    """Liste des fiches non planifiées (CodIndAv 0 ou 1) pour la sidebar."""
    try:
        commande = request.args.get("commande", "").strip()
        client = request.args.get("client", "").strip()
        id_poste = request.args.get("poste", "").strip()
        
        sql = """
            SELECT FT.ID AS id_fiche, FT.RefFiche AS ref_fiche, C.Numero AS commande,
                   S.RaiSocTri AS client, P.Nom AS poste, FI.TpsPrevDev AS temps_prev
            FROM GP_FICHES_TRAVAIL FT
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
            JOIN GP_POSTES P ON P.ID = FT.ID_POSTE AND P.Archive = 0
            LEFT JOIN GP_FICHTRA_INT FI ON FI.ID_FICHTRA = FT.ID
            WHERE C.Termine = 0 AND C.Annule = 0
            AND (FT.CodIndAv IN (0, 1) OR FT.CodIndAv IS NULL)
        """
        params = []
        if commande:
            sql += " AND C.Numero LIKE ?"
            params.append(f"%{commande}%")
        if client:
            sql += " AND S.RaiSocTri LIKE ?"
            params.append(f"%{client}%")
        if id_poste:
            sql += " AND P.ID = ?"
            params.append(id_poste)
        sql += " ORDER BY C.Numero, FT.RefFiche"
        
        with get_db_cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        
        out = []
        for r in rows:
            tps = r.temps_prev
            if tps is None:
                tps = 0
            try:
                tps = float(tps)
            except (TypeError, ValueError):
                tps = 0
            out.append({
                "id_fiche": r.id_fiche,
                "ref_fiche": r.ref_fiche,
                "commande": r.commande,
                "client": r.client or "",
                "poste": r.poste or "",
                "temps_prev_h": round(tps, 2)
            })
        return jsonify({"fiches": out})
    except Exception as e:
        return jsonify({"fiches": []})


@projet13_bp.route("/api/fiche_travail")
def fiche_travail():
    # Log systÃ©matique pour vÃ©rifier l'appel de la fonction
    with open('projet13.log', 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] Appel de fiche_travail\n")
    # Optimisation : Utilisation d'une seule requÃªte avec LEFT JOIN pour rÃ©cupÃ©rer toutes les donnÃ©es
    sql = """
        SELECT 
            FT.ID AS id_fiche,
            FT.RefFiche AS ref_fiche,
            C.Numero AS commande,
            S.RaiSocTri AS client,
            P.ID AS id_poste,
            P.Nom AS poste,
            SR.Nom AS service,
            T.DteDeb AS dte_deb,
            T.HeurDeb AS heur_deb,
            T.DteFin AS dte_fin,
            T.HeurFin AS heur_fin,
            T.ID_PERSONNE AS id_personne,
            T.Remarques AS remarques,
            T.NbOp AS nb_op,
            OP.Nom AS operateur_nom,
            OP.Prenom AS operateur_prenom,
            PO.ID AS id_operation,
            PO.Nom AS nom_operation
        FROM GP_FICHES_TRAVAIL FT
        JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
        JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
        JOIN GP_POSTES P ON P.ID = FT.ID_POSTE AND P.Archive = 0
        JOIN GP_SERVICES SR ON SR.ID = P.ID_SERVICE
        LEFT JOIN GP_TRAITEMENTS T ON T.ID_FICHE_TRAVAIL = FT.ID
        LEFT JOIN PERSONNES OP ON OP.ID = T.ID_PERSONNE
        LEFT JOIN GP_POSTES_OP PO ON PO.ID_POSTE = P.ID
        WHERE C.Termine = 0 and C.Annule = 0
        ORDER BY SR.Nom, P.Nom, FT.RefFiche
    """
    
    with get_db_cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()

    # Optimisation : Utilisation d'un dictionnaire pour regrouper les donnÃ©es
    fiches = {}
    for row in rows:
        service = row.service or "Inconnu"
        poste = row.poste or "Inconnu"
        
        if service not in fiches:
            fiches[service] = {}
            
        if poste not in fiches[service]:
            fiches[service][poste] = []
            
        # VÃ©rifier si la fiche existe dÃ©jÃ 
        fiche_existante = next((f for f in fiches[service][poste] if f["id_fiche"] == row.id_fiche), None)
        
        if not fiche_existante:
            # RÃ©cupÃ©rer les opÃ©rations disponibles pour ce poste
            cursor.execute("""
                SELECT ID, Nom 
                FROM GP_POSTES_OP 
                WHERE ID_POSTE = ? AND Archive = 0
            """, (row.id_poste,))
            operations = cursor.fetchall()
            # Log des opÃ©rations rÃ©cupÃ©rÃ©es
            with open('projet13.log', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().isoformat()}] OpÃ©rations pour le poste {row.id_poste} : {[{'ID': op.ID, 'Nom': op.Nom} for op in operations]}\n")
            
            # Si une seule opÃ©ration est disponible, l'enregistrer automatiquement
            if len(operations) == 1:
                operation = operations[0]
                # VÃ©rifier si une fiche d'opÃ©ration existe dÃ©jÃ 
                if check_fiche_operation_exists(cursor, row.id_fiche):
                    print(f"Une fiche d'opÃ©ration existe dÃ©jÃ  pour la fiche {row.id_fiche}")
                    continue
                    
                # VÃ©rifier si l'opÃ©ration spÃ©cifique existe dÃ©jÃ 
                if check_operation_exists(cursor, row.id_fiche, operation.ID):
                    print(f"L'opÃ©ration {operation.ID} existe dÃ©jÃ  pour la fiche {row.id_fiche}")
                    continue
                
                # PrÃ©parer la requÃªte d'insertion avec la structure complÃ¨te de la table
                insert_info = prepare_insert_statement(cursor, 'GP_FICHES_OPERATIONS')
                
                # PrÃ©parer les valeurs avec les valeurs par dÃ©faut
                values = insert_info['default_values'].copy()
                # Mettre Ã  jour les valeurs spÃ©cifiques
                values[insert_info['columns'].index('ID_FICHE_TRAVAIL')] = row.id_fiche
                values[insert_info['columns'].index('ID_OPERATION')] = operation.ID
                values[insert_info['columns'].index('OpReel')] = 1
                
                # Exécuter l'insertion
                insert_query = f"""
                    INSERT INTO GP_FICHES_OPERATIONS
                    ({', '.join(insert_info['columns'])})
                    VALUES ({', '.join(insert_info['placeholders'])})
                """
                cursor.execute(insert_query, values)
                cursor.connection.commit()
            
            fiches[service][poste].append({
                "id_fiche": row.id_fiche,
                "ref_fiche": row.ref_fiche,
                "commande": row.commande,
                "client": row.client,
                "id_poste": row.id_poste,
                "poste": row.poste,
                "service": row.service,
                "dte_deb": row.dte_deb,
                "heur_deb": row.heur_deb,
                "dte_fin": row.dte_fin,
                "heur_fin": row.heur_fin,
                "id_personne": row.id_personne,
                "operateur_nom": row.operateur_nom,
                "operateur_prenom": row.operateur_prenom,
                "nb_op": row.nb_op,
                "remarques": row.remarques,
                "operations": [{"id": op.ID, "nom": op.Nom} for op in operations]
            })
            fiche_existante = fiches[service][poste][-1]
            
        # Ajouter l'opÃ©ration si elle existe
        if row.id_operation:
            # N'ajouter que si elle n'est pas dÃ©jÃ  dans la liste
            if not any(op["id"] == row.id_operation for op in fiche_existante["operations"]):
                fiche_existante["operations"].append({
                    "id": row.id_operation,
                    "nom": row.nom_operation
                })

    return jsonify(fiches)

@projet13_bp.route("/api/personnes")
def personnes():
    try:
        with get_db_cursor() as cursor:
            # RequÃªte pour rÃ©cupÃ©rer les employÃ©s de l'atelier
            sql = """
                SELECT DISTINCT 
                    E.ID_PERSONNE as ID,
                    P.Nom,
                    P.Prenom,
                    E.Code,
                    P.Archive
                FROM PERSONNES P
                JOIN EMPLOYES E ON E.ID_PERSONNE = P.ID
                WHERE E.Atelier = 1
                AND P.Archive = 0
                ORDER BY P.Nom, P.Prenom
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            # Convertir les rÃ©sultats en liste de dictionnaires
            result = []
            for row in rows:
                result.append({
                    "ID": row.ID,
                    "Nom": row.Nom,
                    "Prenom": row.Prenom,
                    "Code": row.Code,
                    "Archive": row.Archive
                })
            
            return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@projet13_bp.route("/api/get_personne_by_code/<code>")
def get_personne_by_code(code):
    try:
        with get_db_cursor() as cursor:
            # RequÃªte pour rÃ©cupÃ©rer l'ID_PERSONNE Ã  partir du Code
            sql = """
                SELECT E.ID_PERSONNE
                FROM EMPLOYES E
                WHERE E.Code = ?
            """
            cursor.execute(sql, (code,))
            row = cursor.fetchone()
            
            if row:
                return jsonify({"success": True, "id_personne": row.ID_PERSONNE})
            else:
                return jsonify({"success": False, "message": "Code employÃ© non trouvÃ©"}), 404
                
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@projet13_bp.route("/api/operations/<int:id_poste>")
def operations_par_poste(id_poste):
    sql = """
        SELECT ID, Nom FROM GP_POSTES_OP WHERE ID_POSTE = ? AND Archive = 0
    """
    with get_db_cursor() as cursor:
        cursor.execute(sql, (id_poste,))
        rows = cursor.fetchall()
    return jsonify([{"id": r.ID, "nom": r.Nom} for r in rows])


@projet13_bp.route("/api/formes")
def api_formes():
    """Liste des noms de formes (FORMES_DECOUPE) pour l'autocomplete 'Forme utilisée'."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT NOM FROM FORMES_DECOUPE WHERE NOM IS NOT NULL ORDER BY NOM")
            rows = cursor.fetchall()
        out = []
        for r in rows:
            nom = getattr(r, "NOM", None) if hasattr(r, "NOM") else (r[0] if r else None)
            if nom is not None and str(nom).strip():
                out.append({"NOM": str(nom).strip()})
        return jsonify(out)
    except Exception as e:
        return jsonify([])

@projet13_bp.route("/api/save_traitement", methods=["POST"])
def save_traitement():
    try:
        data = request.json

        if not data:
            return jsonify({"success": False, "message": "Aucune donnÃ©e reÃ§ue"}), 400

        try:
            id_fiche = int(data.get("id_fiche_travail", 0))
            id_operation = int(data.get("id_operation", 0))
            nb_op = float(data.get("nb_op", 0))
            id_personne = data.get("id_personne")
            if id_personne is not None:
                id_personne = int(id_personne)
            remarque = data.get("remarque")
        except (ValueError, TypeError) as e:
            return jsonify({"success": False, "message": f"Erreur de conversion des donnÃ©es: {str(e)}"}), 400

        # VÃ©rification de l'opÃ©ration autorisÃ©e pour le poste
        try:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT ID_POSTE FROM GP_FICHES_TRAVAIL WHERE ID = ?", (id_fiche,))
                row_poste = cursor.fetchone()
                if not row_poste:
                    return jsonify({"success": False, "message": "Fiche de travail introuvable."}), 400
                id_poste = row_poste[0]
                autorise = operation_autorisee(id_poste, id_operation)
                # Log dÃ©taillÃ©
                with open('projet13.log', 'a', encoding='utf-8') as f:
                    f.write(f"[DEBUG SAVE_TRAITEMENT] id_fiche={id_fiche}, id_poste={id_poste}, id_operation={id_operation}, autorise={autorise}\n")
                if not autorise:
                    return jsonify({"success": False, "message": f"OpÃ©ration non autorisÃ©e pour ce poste. (id_fiche={id_fiche}, id_poste={id_poste}, id_operation={id_operation})"}), 400
        except Exception as e:
            return jsonify({"success": False, "message": f"Erreur SQL lors de la vÃ©rification de l'opÃ©ration autorisÃ©e: {str(e)}"}), 500

        try:
            with get_db_cursor() as cursor:
                log_details = {}
                # PrÃ©parer la requÃªte d'insertion avec la structure complÃ¨te de la table
                try:
                    insert_info = prepare_insert_statement(cursor, 'GP_FICHES_OPERATIONS')
                    values = insert_info['default_values'].copy()
                    values[insert_info['columns'].index('ID_FICHE_TRAVAIL')] = id_fiche
                    values[insert_info['columns'].index('ID_OPERATION')] = id_operation
                    values[insert_info['columns'].index('OpReel')] = nb_op
                except Exception as e:
                    return jsonify({"success": False, "message": f"Erreur lors de la prÃ©paration de l'insertion dans GP_FICHES_OPERATIONS: {str(e)}"}), 500

                # VÃ©rifier si l'opÃ©ration existe dÃ©jÃ 
                try:
                    if check_operation_exists(cursor, id_fiche, id_operation):
                        update_fiche_operation(cursor, id_fiche, id_operation, nb_op)
                        log_details['operation'] = f"UPDATE sur GP_FICHES_OPERATIONS pour fiche {id_fiche}, operation {id_operation}, OpReel={nb_op}"
                        message = "OpÃ©ration mise Ã  jour avec succÃ¨s"
                    else:
                        insert_query = f"""
                            INSERT INTO GP_FICHES_OPERATIONS
                            ({', '.join(insert_info['columns'])})
                            VALUES ({', '.join(insert_info['placeholders'])})
                        """
                        cursor.execute(insert_query, values)
                        log_details['operation'] = f"INSERT dans GP_FICHES_OPERATIONS pour fiche {id_fiche}, operation {id_operation}, OpReel={nb_op}"
                        message = "Nouvelle opÃ©ration crÃ©Ã©e avec succÃ¨s"
                except Exception as e:
                    return jsonify({"success": False, "message": f"Erreur SQL lors de l'insertion/mise Ã  jour dans GP_FICHES_OPERATIONS: {str(e)}"}), 500

                # Correction : ne mettre Ã  jour que la session ouverte (DteFin IS NULL) pour la fiche ET l'opÃ©rateur en cours
                try:
                    cursor.execute("""
                        UPDATE GP_TRAITEMENTS
                        SET ID_OPERATION = ?, NbOp = ?
                        WHERE ID_FICHE_TRAVAIL = ? AND ID_PERSONNE = ? AND (DteFin IS NULL OR DteFin = '')
                    """, (id_operation, nb_op, id_fiche, id_personne))
                except Exception as e:
                    return jsonify({"success": False, "message": f"Erreur SQL lors de la mise Ã  jour de GP_TRAITEMENTS: {str(e)}"}), 500

                log_details['traitement_update'] = f"UPDATE sur GP_TRAITEMENTS pour fiche {id_fiche}, personne {id_personne} (session ouverte) : ID_OPERATION={id_operation}, NbOp={nb_op}"

                # RÃ©cupÃ©rer l'ID du traitement modifiÃ©
                try:
                    cursor.execute("SELECT ID FROM GP_TRAITEMENTS WHERE ID_FICHE_TRAVAIL = ?", (id_fiche,))
                    traitement_row = cursor.fetchone()
                    traitement_id = traitement_row[0] if traitement_row else None
                    log_details['traitement_id'] = traitement_id
                except Exception as e:
                    log_details['traitement_id'] = f"Erreur lors de la rÃ©cupÃ©ration de l'ID du traitement: {str(e)}"

                # Mettre Ã  jour la remarque (nom de la forme) si fournie
                if remarque:
                    try:
                        cursor.execute("""
                            UPDATE GP_TRAITEMENTS
                            SET Remarques = ?
                            WHERE ID_FICHE_TRAVAIL = ? AND ID_PERSONNE = ? AND (DteFin IS NULL OR DteFin = '')
                        """, (remarque, id_fiche, id_personne))
                    except Exception as e:
                        return jsonify({"success": False, "message": f"Erreur SQL lors de la mise Ã  jour de la remarque dans GP_TRAITEMENTS: {str(e)}"}), 500
                # Ajouter nb_op Ã  TOTAL_TIRAGES de la forme concernÃ©e et prÃ©parer la confirmation visuelle
                total_tirages_avant = None
                total_tirages_apres = None
                if remarque and nb_op:
                    try:
                        cursor.execute("SELECT TOTAL_TIRAGES FROM FORMES_DECOUPE WHERE NOM = ?", (remarque,))
                        row_total = cursor.fetchone()
                        total_tirages_avant = row_total[0] if row_total else None
                        cursor.execute("""
                            UPDATE FORMES_DECOUPE
                            SET TOTAL_TIRAGES = ISNULL(TOTAL_TIRAGES, 0) + ?
                            WHERE NOM = ?
                        """, (nb_op, remarque))
                        cursor.execute("SELECT TOTAL_TIRAGES FROM FORMES_DECOUPE WHERE NOM = ?", (remarque,))
                        row_total2 = cursor.fetchone()
                        total_tirages_apres = row_total2[0] if row_total2 else None
                    except Exception as e:
                        print(f"Erreur lors de la mise Ã  jour du total tirages pour la forme {remarque} : {e}")

                cursor.connection.commit()

                # Ecriture dans le log projet13.log
                with open('projet13.log', 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now().isoformat()}] /api/save_traitement\n")
                    for k, v in log_details.items():
                        f.write(f"  {k}: {v}\n")
                    f.write("\n")

                return jsonify({"success": True, "message": message, "log": log_details, "total_tirages_avant": total_tirages_avant, "total_tirages_apres": total_tirages_apres})
        except Exception as e:
            return jsonify({"success": False, "message": f"Erreur SQL gÃ©nÃ©rale lors de l'insertion/mise Ã  jour de l'opÃ©ration: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"success": False, "message": f"Erreur serveur gÃ©nÃ©rale: {str(e)}"}), 500

@projet13_bp.route("/api/change_poste", methods=["POST"])
def change_poste():
    data = request.json
    id_fiche = data.get("id_fiche_travail")
    nouveau_poste = data.get("nouveau_poste")

    try:
        with get_db_cursor() as cursor:
            # VÃ©rifier l'ancien poste pour le log
            cursor.execute("SELECT ID_POSTE FROM GP_FICHES_TRAVAIL WHERE ID = ?", (id_fiche,))
            ancien_poste_result = cursor.fetchone()
            ancien_poste = ancien_poste_result[0] if ancien_poste_result else None
            
            # RÃ©cupÃ©rer l'ID du nouveau poste
            cursor.execute("SELECT ID FROM GP_POSTES WHERE Nom = ? AND Archive = 0", (nouveau_poste,))
            poste_result = cursor.fetchone()
            id_poste = poste_result[0] if poste_result else None
            
            print(f"ðŸ“ Changement de poste - Fiche: {id_fiche}, Ancien poste: {ancien_poste}, Nouveau poste: {id_poste}")

            # Mettre Ã  jour le poste dans GP_FICHES_TRAVAIL
            cursor.execute("""
                UPDATE GP_FICHES_TRAVAIL
                SET ID_POSTE = ?
                WHERE ID = ?
            """, (id_poste, id_fiche))

            cursor.connection.commit()
            print(f"âœ… Changement de poste rÃ©ussi - Fiche: {id_fiche}, Nouveau poste: {id_poste}")
            return jsonify({"success": True, "message": "Poste mis Ã  jour"})
    except Exception as e:
        print(f"âŒ Erreur lors du changement de poste: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@projet13_bp.route("/api/services_et_postes")
def get_services_et_postes():
    try:
        with get_db_cursor() as cursor:
            sql = """
                SELECT 
                    S.ID as service_id,
                    S.Nom as service_nom,
                    P.ID as poste_id,
                    P.Nom as poste_nom
                FROM GP_SERVICES S
                LEFT JOIN GP_POSTES P ON P.ID_SERVICE = S.ID AND P.Archive = 0
                WHERE S.Archive = 0
                ORDER BY S.Nom, P.Nom
            """
            cursor.execute(sql)
            rows = cursor.fetchall()

            # Organiser les donnÃ©es par service
            services = {}
            postes = {}
            
            for row in rows:
                service_id = row.service_id
                if service_id not in services:
                    services[service_id] = {
                        "id": service_id,
                        "nom": row.service_nom,
                        "postes": []
                    }
                if row.poste_id:  # Si le poste existe
                    poste = {
                        "id": row.poste_id,
                        "nom": row.poste_nom
                    }
                    services[service_id]["postes"].append(poste)
                    postes[row.poste_id] = poste

            return jsonify({
                "services": list(services.values()),
                "postes": postes
            })
    except Exception as e:
        print(f"Erreur lors de la rÃ©cupÃ©ration des services et postes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@projet13_bp.route("/api/fiches_filtrees", methods=["GET", "POST"])
def fiches_filtrees():
    # Log systématique pour vérifier l'appel de la fonction
    with open('projet13.log', 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] Appel de fiches_filtrees\n")
    try:
        # Récupérer les paramètres de filtrage (GET ou POST)
        if request.method == "POST":
            data = request.get_json() if request.is_json else request.form
            services = data.getlist('services[]') if hasattr(data, 'getlist') else (data.get('services', []) if isinstance(data.get('services'), list) else [])
            postes = data.getlist('postes[]') if hasattr(data, 'getlist') else (data.get('postes', []) if isinstance(data.get('postes'), list) else [])
            has_date_fin = str(data.get('hasDateFin', 'true')).lower() == 'true' if data else True
        else:
            services = request.args.getlist('services[]')
            postes = request.args.getlist('postes[]')
            has_date_fin = request.args.get('hasDateFin', 'true').lower() == 'true'
        
        # Construire la requÃªte SQL de base
        sql = """
            SELECT 
                FT.ID AS id_fiche,
                FT.RefFiche AS ref_fiche,
                C.Numero AS commande,
                S.RaiSocTri AS client,
                P.ID AS id_poste,
                P.Nom AS poste,
                SR.Nom AS service,
                T.DteDeb AS dte_deb,
                T.HeurDeb AS heur_deb,
                T.DteFin AS dte_fin,
                T.HeurFin AS heur_fin,
                T.ID_PERSONNE AS id_personne,
                T.NbOp AS nb_op,
                OP.Nom AS operateur_nom,
                OP.Prenom AS operateur_prenom,
                T.ID_OPERATION AS id_operation,
                T.Remarques AS remarques,
                PO.ID AS id_operation_possible,
                PO.Nom AS nom_operation,
                FI.TpsPrevDev AS temps_prev_dev,
                FT.CodIndAv AS codindav
            FROM GP_FICHES_TRAVAIL FT
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            JOIN SOCIETES S ON S.ID = C.ID_SOCIETE
            JOIN GP_POSTES P ON P.ID = FT.ID_POSTE AND P.Archive = 0
            JOIN GP_SERVICES SR ON SR.ID = P.ID_SERVICE
            LEFT JOIN GP_TRAITEMENTS T ON T.ID_FICHE_TRAVAIL = FT.ID
            LEFT JOIN PERSONNES OP ON OP.ID = T.ID_PERSONNE
            LEFT JOIN GP_POSTES_OP PO ON PO.ID_POSTE = P.ID
            LEFT JOIN GP_FICHTRA_INT FI ON FI.ID_FICHTRA = FT.ID
            WHERE C.Termine = 0 and C.Annule = 0
        """
        
        params = []
        
        # Ajouter les filtres de service
        if services:
            placeholders = ','.join(['?' for _ in services])
            sql += f" AND SR.ID IN ({placeholders})"
            params.extend(services)
            
        # Ajouter les filtres de poste
        if postes:
            placeholders = ','.join(['?' for _ in postes])
            sql += f" AND P.ID IN ({placeholders})"
            params.extend(postes)
            
        # Filtrer par date de fin si nÃ©cessaire
        if not has_date_fin:
            sql += " AND (T.DteFin IS NULL)"
            
        sql += " ORDER BY SR.Nom, P.Nom, FT.RefFiche"
        
        with get_db_cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # Correction : regrouper par id_fiche pour Ã©viter les doublons
            fiches_dict = {}
            for row in rows:
                id_fiche = row.id_fiche
                if id_fiche not in fiches_dict:
                    # RÃ©cupÃ©rer les opÃ©rations disponibles pour ce poste
                    cursor.execute("""
                        SELECT ID, Nom 
                        FROM GP_POSTES_OP 
                        WHERE ID_POSTE = ? AND Archive = 0
                    """, (row.id_poste,))
                    operations = cursor.fetchall()
                    # RÃ©cupÃ©rer le traitement le plus rÃ©cent pour cette fiche
                    cursor.execute("""
                        SELECT TOP 1 T.*, OP.Nom as operateur_nom, OP.Prenom as operateur_prenom
                        FROM GP_TRAITEMENTS T
                        LEFT JOIN PERSONNES OP ON OP.ID = T.ID_PERSONNE
                        WHERE T.ID_FICHE_TRAVAIL = ?
                        ORDER BY CASE WHEN T.DteFin IS NOT NULL THEN T.DteFin ELSE T.DteDeb END DESC
                    """, (id_fiche,))
                    t = cursor.fetchone()
                    fiche = {
                        "id_fiche": row.id_fiche,
                        "ref_fiche": row.ref_fiche,
                        "commande": row.commande,
                        "client": row.client,
                        "id_poste": row.id_poste,
                        "poste": row.poste,
                        "service": row.service,
                        "dte_deb": t.DteDeb if t else None,
                        "heur_deb": t.HeurDeb if t else None,
                        "dte_fin": t.DteFin if t else None,
                        "heur_fin": t.HeurFin if t else None,
                        "id_personne": t.ID_PERSONNE if t else None,
                        "operateur_nom": t.operateur_nom if t else None,
                        "operateur_prenom": t.operateur_prenom if t else None,
                        "nb_op": t.NbOp if t else None,
                        "id_operation": t.ID_OPERATION if t else None,
                        "remarques": t.Remarques if t else None,
                        "temps_prev_dev": row.temps_prev_dev,
                        "operations": [{"id": op.ID, "nom": op.Nom} for op in operations],
                        "codindav": row.codindav
                    }
                    fiches_dict[id_fiche] = fiche
            fiches = list(fiches_dict.values())
            return jsonify({"fiches": fiches})
            
    except Exception as e:
        print(f"Erreur lors de la rÃ©cupÃ©ration des fiches filtrÃ©es: {str(e)}")
        return jsonify({"error": str(e)}), 500

@projet13_bp.route("/api/postes")
def get_postes():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT P.Nom
                FROM GP_POSTES P
                WHERE P.Archive = 0
                ORDER BY P.Nom
            """)
            postes = [row.Nom for row in cursor.fetchall()]
            return jsonify({"postes": postes})
    except Exception as e:
        print(f"Erreur lors de la rÃ©cupÃ©ration des postes: {str(e)}")
        return jsonify({"error": str(e)}), 500

def recalculer_temps_reel(id_fiche, cursor):
    # RÃ©cupÃ¨re tous les traitements de la fiche et additionne les durÃ©es (HeurFin - HeurDeb)
    cursor.execute("SELECT HeurDeb, HeurFin FROM GP_TRAITEMENTS WHERE ID_FICHE_TRAVAIL = ?", (id_fiche,))
    traitements = cursor.fetchall()
    tps_reel = 0.0
    for tr in traitements:
        hdeb = tr.HeurDeb
        hfin = tr.HeurFin
        try:
            hdeb = float(str(hdeb).replace(',', '.')) if hdeb is not None else 0.0
        except Exception:
            hdeb = 0.0
        try:
            hfin = float(str(hfin).replace(',', '.')) if hfin is not None else 0.0
        except Exception:
            hfin = 0.0
        tps_reel += max(0.0, hfin - hdeb)
    # Mise Ã  jour du temps rÃ©el dans GP_FICHTRA_INT et GP_FICHES_TRAVAIL
    cursor.execute("UPDATE GP_FICHTRA_INT SET TpsReel = ? WHERE ID_FICHTRA = ?", (tps_reel, id_fiche))
    cursor.execute("UPDATE GP_FICHES_TRAVAIL SET CtReel = ? WHERE ID = ?", (tps_reel, id_fiche))

@projet13_bp.route("/api/set_debut", methods=["POST"])
def set_debut():
    try:
        data = request.get_json()
        id_fiche = data.get("id_fiche")
        from datetime import datetime
        date = data.get("date") or datetime.now().isoformat()
        # Log de la valeur reÃ§ue du front pour debug
        with open('debug_heure.log', 'a', encoding='utf-8') as f:
            f.write(f"set_debut - ReÃ§u du front : {date}\n")
        id_personne = data.get("id_personne")

        if not id_fiche or not date or not id_personne:
            return jsonify({"success": False, "message": "ParamÃ¨tres manquants (id_fiche, date ou id_personne)"}), 400

        # Extraction robuste de l'heure et des minutes depuis la chaÃ®ne reÃ§ue (ISO 8601, fuseau gÃ©rÃ©)
        date_full = date[:19].replace('T', ' ')
        try:
            from dateutil import parser
            dt = parser.isoparse(date)
            heure = dt.hour
            minute = dt.minute
            date_sql = dt.strftime("%Y-%m-%d 00:00:00.000")
        except Exception as e:
            # Fallback regex si dateutil non dispo ou erreur
            import re
            match = re.search(r'(\d{2}):(\d{2})', date_full)
            if match:
                heure = int(match.group(1))
                minute = int(match.group(2))
            else:
                heure = 0
                minute = 0
            date_sql = date_full[:10] + " 00:00:00.000"
        heure_str = f"{heure},{minute:02d}"
        heure_float = float(heure_str.replace(',', '.'))
        # Log extraction
        with open('debug_heure.log', 'a', encoding='utf-8') as f:
            f.write(f"set_debut - Extraction : heure={heure}, minute={minute}, heure_float={heure_float}\n")

        with get_db_cursor() as cursor:
            # VÃ©rifier si un traitement existe dÃ©jÃ  pour cette fiche
            cursor.execute("SELECT COUNT(*) FROM GP_TRAITEMENTS WHERE ID_FICHE_TRAVAIL = ?", (id_fiche,))
            existe = cursor.fetchone()[0] > 0
            if not existe:
                # PrÃ©parer l'insert dynamique
                insert_info = prepare_insert_statement(cursor, 'GP_TRAITEMENTS')
                values = insert_info['default_values'].copy()
                # Remplir les champs nÃ©cessaires
                if 'ID_FICHE_TRAVAIL' in insert_info['columns']:
                    values[insert_info['columns'].index('ID_FICHE_TRAVAIL')] = id_fiche
                if 'DteDeb' in insert_info['columns']:
                    values[insert_info['columns'].index('DteDeb')] = date_sql
                if 'HeurDeb' in insert_info['columns']:
                    values[insert_info['columns'].index('HeurDeb')] = heure_float
                if 'ID_PERSONNE' in insert_info['columns']:
                    values[insert_info['columns'].index('ID_PERSONNE')] = id_personne
                # Forcer Origine Ã  11
                if 'Origine' in insert_info['columns']:
                    values[insert_info['columns'].index('Origine')] = 11
                # Forcer DteFin et HeurFin Ã  None (NULL en base)
                if 'DteFin' in insert_info['columns']:
                    values[insert_info['columns'].index('DteFin')] = None
                if 'HeurFin' in insert_info['columns']:
                    values[insert_info['columns'].index('HeurFin')] = None
                # Exclure la colonne ID (auto-incrÃ©mentÃ©e) de l'INSERT
                if 'ID' in insert_info['columns']:
                    idx = insert_info['columns'].index('ID')
                    insert_info['columns'].pop(idx)
                    insert_info['placeholders'].pop(idx)
                    values.pop(idx)
                insert_query = f"""
                    INSERT INTO GP_TRAITEMENTS
                    ({', '.join(insert_info['columns'])})
                    VALUES ({', '.join(insert_info['placeholders'])})
                """
                cursor.execute(insert_query, values)
            else:
                # Met Ã  jour la date de dÃ©but ET l'opÃ©rateur dans GP_TRAITEMENTS
                cursor.execute("""
                    UPDATE GP_TRAITEMENTS
                    SET DteDeb = ?, HeurDeb = ?, ID_PERSONNE = ?
                    WHERE ID_FICHE_TRAVAIL = ?
                """, (date_sql, heure_float, id_personne, id_fiche))
            # Forcer CodIndAv Ã  2 (commencÃ©, pas terminÃ©)
            cursor.execute("""
                UPDATE GP_FICHES_TRAVAIL
                SET CodIndAv = 2
                WHERE ID = ?
            """, (id_fiche,))
            cursor.connection.commit()
            # Recalcul temps rÃ©el
            recalculer_temps_reel(id_fiche, cursor)
            cursor.connection.commit()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@projet13_bp.route("/api/set_fin", methods=["POST"])
def set_fin():
    try:
        data = request.get_json()
        id_fiche = data.get("id_fiche")
        from datetime import datetime, timedelta
        date = data.get("date") or datetime.now().isoformat()
        # Log de la valeur reÃ§ue du front pour debug
        with open('debug_heure.log', 'a', encoding='utf-8') as f:
            f.write(f"set_fin - ReÃ§u du front : {date}\n")
        id_personne = data.get("id_personne")
        id_operation = data.get("id_operation")
        nb_op = data.get("nb_op")
        remarque = data.get("remarque")

        # VÃ©rification cÃ´tÃ© backend : nb_op doit Ãªtre > 0
        if nb_op is None or float(nb_op) <= 0:
            return jsonify({"success": False, "message": "La quantitÃ© produite (NbOp) doit Ãªtre strictement supÃ©rieure Ã  zÃ©ro pour terminer la fiche."}), 400

        if not id_fiche or not date:
            return jsonify({"success": False, "message": "ParamÃ¨tres manquants"}), 400

        # Extraction robuste de l'heure et des minutes depuis la chaÃ®ne reÃ§ue (ISO 8601, fuseau gÃ©rÃ©)
        date_full = date[:19].replace('T', ' ')
        try:
            from dateutil import parser
            dt = parser.isoparse(date)
            heure = dt.hour
            minute = dt.minute
            date_sql = dt.strftime("%Y-%m-%d 00:00:00.000")
        except Exception as e:
            # Fallback regex si dateutil non dispo ou erreur
            import re
            match = re.search(r'(\d{2}):(\d{2})', date_full)
            if match:
                heure = int(match.group(1))
                minute = int(match.group(2))
            else:
                heure = 0
                minute = 0
            date_sql = date_full[:10] + " 00:00:00.000"
        heure_str = f"{heure},{minute:02d}"
        heure_float = float(heure_str.replace(',', '.'))
        # Log extraction
        with open('debug_heure.log', 'a', encoding='utf-8') as f:
            f.write(f"set_fin - Extraction : heure={heure}, minute={minute}, heure_float={heure_float}\n")
        # Correction : si la date est vide, 1900-01-01 ou 0000-00-00, on met NULL en base
        if not date_full.strip() or date_full.startswith('1900') or date_full.startswith('0000'):
            date_sql = None
            heure_float = None

        with get_db_cursor() as cursor:
            # RÃ©cupÃ©rer la session ouverte pour cette fiche et cet opÃ©rateur
            cursor.execute("""
                SELECT ID, DteDeb FROM GP_TRAITEMENTS
                WHERE ID_FICHE_TRAVAIL = ? AND ID_PERSONNE = ? AND (DteFin IS NULL OR DteFin = '')
            """, (id_fiche, id_personne))
            session = cursor.fetchone()
            if not session:
                return jsonify({"success": False, "message": "Aucune session ouverte Ã  clÃ´turer pour cet opÃ©rateur."}), 400
            session_id, dte_deb = session
            # VÃ©rifier que la date de fin est postÃ©rieure Ã  la date de dÃ©but
            if date_full and dte_deb and date_full < str(dte_deb):
                return jsonify({"success": False, "message": "La date de fin ne peut pas Ãªtre antÃ©rieure Ã  la date de dÃ©but de la session."}), 400
            # Met Ã  jour l'opÃ©rateur, l'opÃ©ration et la quantitÃ© si fournis
            if id_personne and id_operation and nb_op is not None:
                cursor.execute("""
                    UPDATE GP_TRAITEMENTS
                    SET ID_PERSONNE = ?, ID_OPERATION = ?, NbOp = ?
                    WHERE ID = ?
                """, (id_personne, id_operation, nb_op, session_id))
            # Mettre Ã  jour la remarque (nom de la forme) si fournie
            if remarque:
                cursor.execute("""
                    UPDATE GP_TRAITEMENTS
                    SET Remarques = ?
                    WHERE ID = ?
                """, (remarque, session_id))
            # Met Ã  jour la date de fin dans GP_TRAITEMENTS, force NbPers=1
            cursor.execute("""
                UPDATE GP_TRAITEMENTS
                SET DteFin = ?, HeurFin = ?, NbPers = 1
                WHERE ID = ?
            """, (date_sql, heure_float, session_id))

            # Calculer et mettre Ã  jour TpsRelPass dans GP_FICHES_OPERATIONS
            cursor.execute("""
                SELECT DteDeb, HeurDeb, DteFin, HeurFin, ID_OPERATION
                FROM GP_TRAITEMENTS
                WHERE ID_FICHE_TRAVAIL = ?
            """, (id_fiche,))
            row = cursor.fetchone()
            if row and row.DteDeb and row.HeurDeb is not None and row.DteFin and row.HeurFin is not None and row.ID_OPERATION:
                try:
                    def to_datetime(date_val, heure_val):
                        from datetime import datetime, timedelta
                        if isinstance(date_val, datetime):
                            base = date_val
                        else:
                            # Si la date contient aussi l'heure, on la prend telle quelle
                            if len(str(date_val)) > 10:
                                base = datetime.strptime(str(date_val)[:19], "%Y-%m-%d %H:%M:%S")
                            else:
                                base = datetime.strptime(str(date_val), "%Y-%m-%d")
                        return base
                    dt_deb = to_datetime(row.DteDeb, row.HeurDeb)
                    dt_fin = to_datetime(row.DteFin, row.HeurFin)
                    tps_rel_pass = (dt_fin - dt_deb).total_seconds() / 3600  # en heures
                    # Mettre Ã  jour GP_FICHES_OPERATIONS
                    cursor.execute("""
                        UPDATE GP_FICHES_OPERATIONS
                        SET TpsRelPass = ?
                        WHERE ID_FICHE_TRAVAIL = ? AND ID_OPERATION = ?
                    """, (tps_rel_pass, id_fiche, row.ID_OPERATION))
                    # Mettre Ã  jour GP_FICHTRA_INT.TpsReel
                    cursor.execute("""
                        UPDATE GP_FICHTRA_INT
                        SET TpsReel = ?
                        WHERE ID_FICHTRA = ?
                    """, (tps_rel_pass, id_fiche))
                    # RÃ©cupÃ©rer le coÃ»t horaire de la machine (poste) dans GP_POSTES_TARIF
                    cursor.execute("""
                        SELECT PT.PrxMach
                        FROM GP_FICHES_TRAVAIL FT
                        JOIN GP_POSTES_TARIF PT ON FT.ID_POSTE = PT.ID_POSTE
                        WHERE FT.ID = ?
                    """, (id_fiche,))
                    poste = cursor.fetchone()
                    cout_horaire = poste.PrxMach if poste and poste.PrxMach else 0
                    # Calculer le coÃ»t rÃ©el et le stocker dans GP_FICHES_TRAVAIL.CtReel
                    cout_reel = tps_rel_pass * cout_horaire
                    cursor.execute("""
                        UPDATE GP_FICHES_TRAVAIL
                        SET CtReel = ?
                        WHERE ID = ?
                    """, (cout_reel, id_fiche))
                except Exception as e:
                    # Log erreur de calcul
                    with open('projet13.log', 'a', encoding='utf-8') as f:
                        f.write(f"[ERREUR calcul TpsRelPass/TpsReel/CtReel] {str(e)}\n")
            cursor.connection.commit()

            # --- AJOUT : Passage CodIndAv Ã  3 pour la fiche terminÃ©e ---
            cursor.execute("""
                UPDATE GP_FICHES_TRAVAIL
                SET CodIndAv = 3
                WHERE ID = ?
            """, (id_fiche,))

            # --- AJOUT : Passage CodIndAv Ã  1 pour la fiche suivante (ordre +1, mÃªme commande et travail) ---
            cursor.execute("""
                SELECT ID_COMMANDE, ID_TRAVAIL, Ordre
                FROM GP_FICHES_TRAVAIL
                WHERE ID = ?
            """, (id_fiche,))
            fiche_courante = cursor.fetchone()
            if fiche_courante:
                id_commande, id_travail, ordre = fiche_courante
                # Chercher la fiche suivante
                cursor.execute("""
                    SELECT ID FROM GP_FICHES_TRAVAIL
                    WHERE ID_COMMANDE = ? AND ID_TRAVAIL = ? AND Ordre = ?
                """, (id_commande, id_travail, ordre + 1))
                fiche_suivante = cursor.fetchone()
                if fiche_suivante:
                    id_fiche_suivante = fiche_suivante[0]
                    # Mettre CodIndAv Ã  1 (prÃªt Ã  commencer)
                    cursor.execute("""
                        UPDATE GP_FICHES_TRAVAIL
                        SET CodIndAv = 1
                        WHERE ID = ?
                    """, (id_fiche_suivante,))
            cursor.connection.commit()

            # Recalcul temps rÃ©el
            recalculer_temps_reel(id_fiche, cursor)
            cursor.connection.commit()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@projet13_bp.route("/api/set_interrompu", methods=["POST"])
def set_interrompu():
    try:
        data = request.get_json()
        id_fiche = data.get("id_fiche")
        from datetime import datetime
        date = data.get("date") or datetime.now().isoformat()
        # Log de la valeur reÃ§ue du front pour debug
        with open('debug_heure.log', 'a', encoding='utf-8') as f:
            f.write(f"set_interrompu - ReÃ§u du front : {date}\n")
        id_personne = data.get("id_personne")
        id_operation = data.get("id_operation")
        nb_op = data.get("nb_op")
        remarque = data.get("remarque")
        # VÃ©rification cÃ´tÃ© backend : nb_op doit Ãªtre > 0 si fourni
        if nb_op is None or float(nb_op) <= 0:
            return jsonify({"success": False, "message": "La quantitÃ© produite (NbOp) doit Ãªtre strictement supÃ©rieure Ã  zÃ©ro pour interrompre la fiche."}), 400
        # Extraction de la date complÃ¨te et de l'heure rÃ©elle (minutes seulement)
        try:
            date_full = date[:19].replace('T', ' ')
            dt = datetime.strptime(date_full, "%Y-%m-%d %H:%M:%S")
        except Exception:
            dt = parsedate_to_datetime(date)
            date_full = dt.strftime("%Y-%m-%d %H:%M:%S")
            heure_str = f"{dt.hour},{dt.minute:02d}"
            heure_float = float(heure_str.replace(',', '.'))
        # On envoie l'heure rÃ©elle du clic pour HeurFin (minutes seulement)
        # Correction : on n'utilise plus jamais 1900-01-01 ou 0000-00-00 comme valeur de date de fin
        # Si la date n'est pas valide, on met None (NULL en base)
        if date_full and (date_full.startswith('1900') or date_full.startswith('0000') or not date_full.strip()):
            date_sql = None
            heure_sql = None
        else:
            date_sql = date_full[:10] + " 00:00:00.000"
            match = re.search(r'(\\d{2}):(\\d{2})', date_full)
            if match:
                heure = int(match.group(1))
                minute = int(match.group(2))
            else:
                heure = 0
                minute = 0
            heure_str = f"{heure},{minute:02d}"
            heure_sql = float(heure_str.replace(',', '.'))
        # SÃ©curisation supplÃ©mentaire : Ã©viter d'envoyer la chaÃ®ne 'None' ou 'null'
        if date_sql in [None, '', 'None', 'null']:
            date_sql = None
        if heure_sql in [None, '', 'None', 'null']:
            heure_sql = None
        # Log pour debug
        with open('projet13.log', 'a', encoding='utf-8') as f:
            f.write(f"[DEBUG set_interrompu] date_full={date_full} (type={type(date_full)}), date_sql={date_sql} (type={type(date_sql)}), heure_sql={heure_sql} (type={type(heure_sql)})\n")
        with get_db_cursor() as cursor:
            # RÃ©cupÃ©rer la session ouverte pour cette fiche et cet opÃ©rateur
            cursor.execute("""
                SELECT ID, DteDeb FROM GP_TRAITEMENTS
                WHERE ID_FICHE_TRAVAIL = ? AND ID_PERSONNE = ? AND (DteFin IS NULL OR DteFin = '')
            """, (id_fiche, id_personne))
            session = cursor.fetchone()
            if not session:
                return jsonify({"success": False, "message": "Aucune session ouverte Ã  interrompre pour cet opÃ©rateur."}), 400
            session_id, dte_deb = session
            # VÃ©rifier que la date de fin est postÃ©rieure Ã  la date de dÃ©but
            if date_sql and dte_deb and date_sql < str(dte_deb):
                return jsonify({"success": False, "message": "La date de fin ne peut pas Ãªtre antÃ©rieure Ã  la date de dÃ©but de la session."}), 400
            # Mettre Ã  jour l'opÃ©rateur, l'opÃ©ration et la quantitÃ© si fournis
            if id_personne and id_operation and nb_op is not None:
                cursor.execute("""
                    UPDATE GP_TRAITEMENTS
                    SET ID_PERSONNE = ?, ID_OPERATION = ?, NbOp = ?
                    WHERE ID = ?
                """, (id_personne, id_operation, nb_op, session_id))
            # Mettre Ã  jour la remarque (nom de la forme) si fournie
            if remarque:
                cursor.execute("""
                    UPDATE GP_TRAITEMENTS
                    SET Remarques = ?
                    WHERE ID = ?
                """, (remarque, session_id))
            # Mettre Ã  jour la session avec la date/heure de fin, force NbPers=1
            cursor.execute("""
                UPDATE GP_TRAITEMENTS
                SET DteFin = ?, HeurFin = ?, NbPers = 1
                WHERE ID = ?
            """, (date_sql, heure_sql, session_id))
            cursor.connection.commit()

            # --- AJOUT : Passage CodIndAv Ã  2 pour la fiche interrompue ---
            cursor.execute("""
                UPDATE GP_FICHES_TRAVAIL
                SET CodIndAv = 2
                WHERE ID = ?
            """, (id_fiche,))

            # --- AJOUT : Passage CodIndAv Ã  1 pour la fiche suivante (ordre +1, mÃªme commande et travail) ---
            cursor.execute("""
                SELECT ID_COMMANDE, ID_TRAVAIL, Ordre
                FROM GP_FICHES_TRAVAIL
                WHERE ID = ?
            """, (id_fiche,))
            fiche_courante = cursor.fetchone()
            if fiche_courante:
                id_commande, id_travail, ordre = fiche_courante
                cursor.execute("""
                    SELECT ID FROM GP_FICHES_TRAVAIL
                    WHERE ID_COMMANDE = ? AND ID_TRAVAIL = ? AND Ordre = ?
                """, (id_commande, id_travail, ordre + 1))
                fiche_suivante = cursor.fetchone()
                if fiche_suivante:
                    id_fiche_suivante = fiche_suivante[0]
                    cursor.execute("""
                        UPDATE GP_FICHES_TRAVAIL
                        SET CodIndAv = 1
                        WHERE ID = ?
                    """, (id_fiche_suivante,))
            cursor.connection.commit()

            # Recalcul temps rÃ©el
            recalculer_temps_reel(id_fiche, cursor)
            cursor.connection.commit()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@projet13_bp.route("/api/reprendre", methods=["POST"])
def reprendre():
    try:
        data = request.get_json()
        id_fiche = data.get("id_fiche")
        from datetime import datetime
        date = data.get("date") or datetime.now().isoformat()
        # Log de la valeur reÃ§ue du front pour debug
        with open('debug_heure.log', 'a', encoding='utf-8') as f:
            f.write(f"reprendre - ReÃ§u du front : {date}\n")
        id_personne = data.get("id_personne")

        if not id_fiche or not date or not id_personne:
            return jsonify({"success": False, "message": "ParamÃ¨tres manquants (id_fiche, date ou id_personne)"}), 400

        date_full = date[:19].replace('T', ' ')
        dt = datetime.strptime(date_full, "%Y-%m-%d %H:%M:%S")
        # Correction : conversion automatique de la virgule en point pour l'heure dÃ©cimale
        heure_str = str(dt.hour + dt.minute / 60.0)
        heure_str = heure_str.replace(',', '.')
        heure_float = float(heure_str)

        with get_db_cursor() as cursor:
            insert_info = prepare_insert_statement(cursor, 'GP_TRAITEMENTS')
            values = insert_info['default_values'].copy()
            if 'ID_FICHE_TRAVAIL' in insert_info['columns']:
                values[insert_info['columns'].index('ID_FICHE_TRAVAIL')] = id_fiche
            if 'DteDeb' in insert_info['columns']:
                values[insert_info['columns'].index('DteDeb')] = date_full
            if 'HeurDeb' in insert_info['columns']:
                values[insert_info['columns'].index('HeurDeb')] = heure_float
            if 'ID_PERSONNE' in insert_info['columns']:
                values[insert_info['columns'].index('ID_PERSONNE')] = id_personne
            if 'Origine' in insert_info['columns']:
                values[insert_info['columns'].index('Origine')] = 11
            # Forcer DteFin et HeurFin Ã  None (NULL en base)
            if 'DteFin' in insert_info['columns']:
                values[insert_info['columns'].index('DteFin')] = None
            if 'HeurFin' in insert_info['columns']:
                values[insert_info['columns'].index('HeurFin')] = None
            if 'ID' in insert_info['columns']:
                idx = insert_info['columns'].index('ID')
                insert_info['columns'].pop(idx)
                insert_info['placeholders'].pop(idx)
                values.pop(idx)
            insert_query = f"""
                INSERT INTO GP_TRAITEMENTS
                ({', '.join(insert_info['columns'])})
                VALUES ({', '.join(insert_info['placeholders'])})
            """
            cursor.execute(insert_query, values)
            cursor.execute("""
                UPDATE GP_FICHES_TRAVAIL
                SET CodIndAv = 2
                WHERE ID = ?
            """, (id_fiche,))
            cursor.connection.commit()
            # Recalcul temps rÃ©el
            recalculer_temps_reel(id_fiche, cursor)
            cursor.connection.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@projet13_bp.route("/api/historique_sessions/<int:id_fiche>")
def historique_sessions(id_fiche):
    try:
        with get_db_cursor() as cursor:
            cursor.execute('''
                SELECT T.ID, T.DteDeb, T.HeurDeb, T.DteFin, T.HeurFin, T.ID_PERSONNE, T.ID_OPERATION, T.NbOp, T.NbPers, T.Origine, T.Remarques,
                       OP.Nom as operateur_nom, OP.Prenom as operateur_prenom, E.Code as operateur_code,
                       OPE.Nom as operation_nom
                FROM GP_TRAITEMENTS T
                LEFT JOIN PERSONNES OP ON OP.ID = T.ID_PERSONNE
                LEFT JOIN EMPLOYES E ON E.ID_PERSONNE = T.ID_PERSONNE
                LEFT JOIN GP_POSTES_OP OPE ON OPE.ID = T.ID_OPERATION
                WHERE T.ID_FICHE_TRAVAIL = ?
                ORDER BY T.DteDeb ASC, T.ID ASC
            ''', (id_fiche,))
            sessions = [
                {
                    'id': row.ID,
                    'dte_deb': row.DteDeb,
                    'heur_deb': row.HeurDeb,
                    'dte_fin': row.DteFin,
                    'heur_fin': row.HeurFin,
                    'id_personne': row.ID_PERSONNE,
                    'operateur_nom': row.operateur_nom,
                    'operateur_prenom': row.operateur_prenom,
                    'operateur_code': row.operateur_code,
                    'id_operation': row.ID_OPERATION,
                    'operation_nom': row.operation_nom,
                    'nb_op': row.NbOp,
                    'nb_pers': row.NbPers,
                    'origine': row.Origine,
                    'remarques': row.Remarques
                }
                for row in cursor.fetchall()
            ]
        return jsonify({'success': True, 'sessions': sessions})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@projet13_bp.route("/corriger", methods=["GET", "POST"])
def corriger_projet13():
    message = ""
    nb_fiches_fermees = 0
    if request.method == "POST":
        # Correction automatique : fermeture des fiches ouvertes
        from datetime import datetime
        now = datetime.now()
        date_du_jour = now.date()
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT T.ID, T.ID_FICHE_TRAVAIL, T.ID_PERSONNE, P.Nom as poste, P.NbPostes
                FROM GP_TRAITEMENTS T
                JOIN GP_FICHES_TRAVAIL FT ON FT.ID = T.ID_FICHE_TRAVAIL
                JOIN GP_POSTES P ON FT.ID_POSTE = P.ID
                WHERE (T.DteFin IS NULL OR T.DteFin = '')
                  AND T.DteDeb IS NOT NULL
            """)
            fiches = cursor.fetchall()
            for fiche in fiches:
                id_traitement = fiche.ID
                nb_postes = fiche.NbPostes or 1
                if nb_postes == 1:
                    heure_fin = 16 + 30/60  # 16h30
                else:
                    heure_fin = 22  # 22h00
                cursor.execute("""
                    UPDATE GP_TRAITEMENTS
                    SET DteFin = ?, HeurFin = ?
                    WHERE ID = ?
                """, (date_du_jour, heure_fin, id_traitement))
                nb_fiches_fermees += 1
            cursor.connection.commit()
        message = f"{nb_fiches_fermees} fiches ouvertes ont Ã©tÃ© fermÃ©es automatiquement."

    # Afficher les fiches encore ouvertes
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT T.ID, FT.RefFiche, P.Nom as poste, T.DteDeb, T.HeurDeb, T.ID_PERSONNE, OP.Nom as operateur_nom
            FROM GP_TRAITEMENTS T
            JOIN GP_FICHES_TRAVAIL FT ON FT.ID = T.ID_FICHE_TRAVAIL
            JOIN GP_POSTES P ON FT.ID_POSTE = P.ID
            LEFT JOIN PERSONNES OP ON OP.ID = T.ID_PERSONNE
            WHERE (T.DteFin IS NULL OR T.DteFin = '')
              AND T.DteDeb IS NOT NULL
        """)
        fiches_ouvertes = cursor.fetchall()

    return render_template(
        "projet13_corriger.html",
        fiches_ouvertes=fiches_ouvertes,
        message=message
    )

@projet13_bp.route("/corriger/fermer_fiche/<int:id_traitement>", methods=["POST"])
def fermer_fiche_corriger(id_traitement):
    from datetime import datetime
    now = datetime.now()
    date_du_jour = now.date()
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT P.NbPostes
            FROM GP_TRAITEMENTS T
            JOIN GP_FICHES_TRAVAIL FT ON FT.ID = T.ID_FICHE_TRAVAIL
            JOIN GP_POSTES P ON FT.ID_POSTE = P.ID
            WHERE T.ID = ?
        """, (id_traitement,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Fiche non trouvÃ©e."}), 404
        nb_postes = row.NbPostes or 1
        if nb_postes == 1:
            heure_fin = 16 + 30/60  # 16h30
        else:
            heure_fin = 22  # 22h00
        cursor.execute("""
            UPDATE GP_TRAITEMENTS
            SET DteFin = ?, HeurFin = ?
            WHERE ID = ?
        """, (date_du_jour, heure_fin, id_traitement))
        cursor.connection.commit()
    return jsonify({"success": True})

def get_table_columns(cursor, table_name):
    """RÃ©cupÃ¨re les colonnes d'une table."""
    cursor.execute(f"SELECT * FROM {table_name} WHERE 1=0")
    return [description[0] for description in cursor.description]

def get_default_value(data_type):
    """Retourne une valeur par dÃ©faut en fonction du type de donnÃ©es."""
    if 'int' in data_type.lower():
        return 0
    elif 'float' in data_type.lower() or 'real' in data_type.lower():
        return 0.0
    elif 'date' in data_type.lower():
        return None
    elif 'char' in data_type.lower() or 'text' in data_type.lower():
        return ''
    else:
        return None

def prepare_insert_statement(cursor, table_name):
    """PrÃ©pare les Ã©lÃ©ments nÃ©cessaires pour une requÃªte d'insertion."""
    columns = get_table_columns(cursor, table_name)
    placeholders = ['?' for _ in columns]
    default_values = [get_default_value('text') for _ in columns]  # Par dÃ©faut, on utilise 'text'
    
    return {
        'columns': columns,
        'placeholders': placeholders,
        'default_values': default_values
    }

def check_fiche_operation_exists(cursor, id_fiche_travail):
    """VÃ©rifie si une fiche d'opÃ©ration existe dÃ©jÃ ."""
    cursor.execute("""
        SELECT COUNT(*) FROM GP_FICHES_OPERATIONS
        WHERE ID_FICHE_TRAVAIL = ?
    """, (id_fiche_travail,))
    return cursor.fetchone()[0] > 0

def check_operation_exists(cursor, id_fiche_travail, id_operation):
    """VÃ©rifie si une opÃ©ration spÃ©cifique existe dÃ©jÃ ."""
    cursor.execute("""
        SELECT COUNT(*) FROM GP_FICHES_OPERATIONS
        WHERE ID_FICHE_TRAVAIL = ? AND ID_OPERATION = ?
    """, (id_fiche_travail, id_operation))
    return cursor.fetchone()[0] > 0

def update_fiche_operation(cursor, id_fiche_travail, id_operation, op_reel):
    """Met Ã  jour une fiche d'opÃ©ration existante."""
    update_query = """
        UPDATE GP_FICHES_OPERATIONS
        SET OpReel = ?
        WHERE ID_FICHE_TRAVAIL = ? AND ID_OPERATION = ?
    """
    cursor.execute(update_query, (
        op_reel,
        id_fiche_travail,
        id_operation
    )) 

@projet13_bp.route('/api/dupliquer_fiche', methods=['POST'])
def dupliquer_fiche():
    from flask import request, jsonify
    data = request.get_json()
    id_fiche = data.get('id_fiche')
    id_poste = data.get('id_poste')
    if not id_fiche or not id_poste:
        return jsonify({'success': False, 'message': 'ParamÃ¨tres manquants'}), 400

    with get_db_cursor() as cursor:
        # RÃ©cupÃ©rer la fiche Ã  dupliquer
        cursor.execute("""
            SELECT *
            FROM GP_FICHES_TRAVAIL
            WHERE ID = ?
        """, (id_fiche,))
        fiche = cursor.fetchone()
        if not fiche:
            return jsonify({'success': False, 'message': 'Fiche introuvable'}), 404

        # PrÃ©parer les colonnes Ã  dupliquer (sauf ID et ID_POSTE)
        columns = [col[0] for col in cursor.description if col[0] not in ('ID', 'ID_POSTE')]
        values = [getattr(fiche, col) for col in columns]
        # Ajouter le nouveau poste
        columns.append('ID_POSTE')
        values.append(id_poste)

        # Construire la requÃªte d'insertion
        placeholders = ','.join(['?'] * len(columns))
        insert_query = f"""
            INSERT INTO GP_FICHES_TRAVAIL ({','.join(columns)})
            VALUES ({placeholders})
        """
        cursor.execute(insert_query, values)
        cursor.execute('SELECT SCOPE_IDENTITY()')
        new_id = cursor.fetchone()[0]
        cursor.connection.commit()

    return jsonify({'success': True, 'id_fiche': new_id}) 

@projet13_bp.route("/api/postes_du_service_fiche/<int:id_fiche>")
def postes_du_service_fiche(id_fiche):
    with get_db_cursor() as cursor:
        # RÃ©cupÃ©rer le service de la fiche
        cursor.execute("""
            SELECT P.ID_SERVICE
            FROM GP_FICHES_TRAVAIL FT
            JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            WHERE FT.ID = ?
        """, (id_fiche,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Fiche ou service introuvable"}), 404
        id_service = row.ID_SERVICE
        # RÃ©cupÃ©rer les postes de ce service
        cursor.execute("""
            SELECT ID, Nom
            FROM GP_POSTES
            WHERE ID_SERVICE = ? AND Archive = 0
        """, (id_service,))
        postes = [{"id": r.ID, "nom": r.Nom} for r in cursor.fetchall()]
        return jsonify({"success": True, "postes": postes}) 

@projet13_bp.route('/api/dashboard')
def dashboard():
    from datetime import datetime
    with get_db_cursor() as cursor:
        # Indicateurs globaux
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN FT.CodIndAv = 2 THEN 1 ELSE 0 END) AS en_cours,
                SUM(CASE WHEN FT.CodIndAv IN (0,1) THEN 1 ELSE 0 END) AS non_debutees,
                SUM(CASE WHEN FT.CodIndAv = 3 THEN 1 ELSE 0 END) AS terminees,
                SUM(CASE WHEN FT.CodIndAv = 0 THEN 1 ELSE 0 END) AS bloquees
            FROM GP_FICHES_TRAVAIL FT
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            WHERE C.Termine = 0 AND C.Annule = 0
        """)
        kpi_row = cursor.fetchone()
        kpi = dict(zip([col[0] for col in cursor.description], kpi_row)) if kpi_row else {}

        # RÃ©partition par poste
        cursor.execute("""
            SELECT P.Nom as poste, 
                SUM(CASE WHEN FT.CodIndAv = 2 THEN 1 ELSE 0 END) AS en_cours,
                SUM(CASE WHEN FT.CodIndAv = 3 THEN 1 ELSE 0 END) AS terminees,
                SUM(CASE WHEN FT.CodIndAv = 0 THEN 1 ELSE 0 END) AS bloquees
            FROM GP_FICHES_TRAVAIL FT
            JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            WHERE C.Termine = 0 AND C.Annule = 0
            GROUP BY P.Nom
            ORDER BY P.Nom
        """)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        par_poste = [dict(zip(columns, row)) for row in rows]

        # Fiches en retard (date prÃ©vue dÃ©passÃ©e et non terminÃ©e)
        cursor.execute("""
            SELECT FT.ID, FT.RefFiche, P.Nom as poste, C.Numero as commande, FI.TpsPrevDev, FI.TpsReel
            FROM GP_FICHES_TRAVAIL FT
            JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            LEFT JOIN GP_FICHTRA_INT FI ON FI.ID_FICHTRA = FT.ID
            WHERE FT.CodIndAv <> 3 AND C.Termine = 0 AND C.Annule = 0
                AND FI.TpsPrevDev IS NOT NULL AND FI.TpsReel IS NOT NULL AND FI.TpsReel > FI.TpsPrevDev
        """)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        fiches_retard = [dict(zip(columns, row)) for row in rows]

    return jsonify({
        "kpi": kpi,
        "par_poste": par_poste,
        "fiches_retard": fiches_retard
    }) 

@projet13_bp.route('/api/dashboard_avance')
def dashboard_avance():
    from datetime import datetime, timedelta
    service = request.args.get('service')
    poste = request.args.get('poste')
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    etat = request.args.get('etat')  # ex: 'en_cours', 'terminee', 'bloquee'

    filters = []
    params = []
    if service:
        filters.append('SR.ID = ?')
        params.append(service)
    if poste:
        filters.append('P.ID = ?')
        params.append(poste)
    if date_debut:
        filters.append('FT.DateCreat >= ?')
        params.append(date_debut)
    if date_fin:
        filters.append('FT.DateCreat <= ?')
        params.append(date_fin)
    if etat:
        if etat == 'en_cours':
            filters.append('FT.CodIndAv = 2')
        elif etat == 'terminee':
            filters.append('FT.CodIndAv = 3')
        elif etat == 'bloquee':
            filters.append('FT.CodIndAv = 0')
    where = ' AND '.join(['C.Termine = 0', 'C.Annule = 0'] + filters)

    with get_db_cursor() as cursor:
        # KPI filtrÃ©s
        cursor.execute(f"""
            SELECT 
                SUM(CASE WHEN FT.CodIndAv = 2 THEN 1 ELSE 0 END) AS en_cours,
                SUM(CASE WHEN FT.CodIndAv IN (0,1) THEN 1 ELSE 0 END) AS non_debutees,
                SUM(CASE WHEN FT.CodIndAv = 3 THEN 1 ELSE 0 END) AS terminees,
                SUM(CASE WHEN FT.CodIndAv = 0 THEN 1 ELSE 0 END) AS bloquees
            FROM GP_FICHES_TRAVAIL FT
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            JOIN GP_SERVICES SR ON SR.ID = P.ID_SERVICE
            WHERE {where}
        """, params)
        kpi_row = cursor.fetchone()
        kpi = dict(zip([col[0] for col in cursor.description], kpi_row)) if kpi_row else {}

        # RÃ©partition par poste/service
        cursor.execute(f"""
            SELECT SR.Nom as service, P.Nom as poste, 
                SUM(CASE WHEN FT.CodIndAv = 2 THEN 1 ELSE 0 END) AS en_cours,
                SUM(CASE WHEN FT.CodIndAv = 3 THEN 1 ELSE 0 END) AS terminees,
                SUM(CASE WHEN FT.CodIndAv = 0 THEN 1 ELSE 0 END) AS bloquees
            FROM GP_FICHES_TRAVAIL FT
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            JOIN GP_SERVICES SR ON SR.ID = P.ID_SERVICE
            WHERE {where}
            GROUP BY SR.Nom, P.Nom
            ORDER BY SR.Nom, P.Nom
        """, params)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        repartition = [dict(zip(columns, row)) for row in rows]

        # Evolution du nombre de fiches terminÃ©es par jour (7 derniers jours)
        date_fin_dt = datetime.strptime(date_fin, '%Y-%m-%d') if date_fin else datetime.now()
        date_debut_dt = datetime.strptime(date_debut, '%Y-%m-%d') if date_debut else (date_fin_dt - timedelta(days=6))
        cursor.execute(f"""
            SELECT CONVERT(VARCHAR(10), FT.DateMaj, 120) as jour, COUNT(*) as nb
            FROM GP_FICHES_TRAVAIL FT
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            JOIN GP_SERVICES SR ON SR.ID = P.ID_SERVICE
            WHERE {where} AND FT.CodIndAv = 3 AND FT.DateMaj >= ? AND FT.DateMaj <= ?
            GROUP BY CONVERT(VARCHAR(10), FT.DateMaj, 120)
            ORDER BY jour
        """, params + [date_debut_dt.strftime('%Y-%m-%d'), date_fin_dt.strftime('%Y-%m-%d')])
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        evolution = [dict(zip(columns, row)) for row in rows]

        # RÃ©partition des temps passÃ©s par poste
        cursor.execute(f"""
            SELECT P.Nom as poste, SUM(FI.TpsReel) as temps_total
            FROM GP_FICHES_TRAVAIL FT
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            JOIN GP_SERVICES SR ON SR.ID = P.ID_SERVICE
            LEFT JOIN GP_FICHTRA_INT FI ON FI.ID_FICHTRA = FT.ID
            WHERE {where} AND FI.TpsReel IS NOT NULL
            GROUP BY P.Nom
            ORDER BY P.Nom
        """, params)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        temps_par_poste = [dict(zip(columns, row)) for row in rows]

        # Taux de retard/blocage par service
        cursor.execute(f"""
            SELECT SR.Nom as service,
                SUM(CASE WHEN FT.CodIndAv = 0 THEN 1 ELSE 0 END) as nb_bloquees,
                SUM(CASE WHEN FI.TpsPrevDev IS NOT NULL AND FI.TpsReel IS NOT NULL AND FI.TpsReel > FI.TpsPrevDev THEN 1 ELSE 0 END) as nb_retards,
                COUNT(*) as total
            FROM GP_FICHES_TRAVAIL FT
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            JOIN GP_SERVICES SR ON SR.ID = P.ID_SERVICE
            LEFT JOIN GP_FICHTRA_INT FI ON FI.ID_FICHTRA = FT.ID
            WHERE {where}
            GROUP BY SR.Nom
            ORDER BY SR.Nom
        """, params)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        taux_par_service = [dict(zip(columns, row)) for row in rows]

    return jsonify({
        "kpi": kpi,
        "repartition": repartition,
        "evolution": evolution,
        "temps_par_poste": temps_par_poste,
        "taux_par_service": taux_par_service
    }) 

@projet13_bp.route("/api/anomalies")
def detecter_anomalies():
    anomalies = []
    service_id = request.args.get('service')
    service_filter = ""
    params = []
    if service_id:
        service_filter = " AND SR.ID = ?"
        params.append(service_id)
    with get_db_cursor() as cursor:
        # 1. Sessions sans date de fin (ouvertes depuis plus de 24h)
        cursor.execute(f"""
            SELECT T.ID, FT.RefFiche, C.Numero as numero_commande, P.Nom as poste, SR.Nom as service, T.DteDeb, T.HeurDeb, T.ID_PERSONNE, OP.Nom as operateur_nom, OP.Prenom as operateur_prenom
            FROM GP_TRAITEMENTS T
            JOIN GP_FICHES_TRAVAIL FT ON FT.ID = T.ID_FICHE_TRAVAIL
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            JOIN GP_POSTES P ON FT.ID_POSTE = P.ID
            JOIN GP_SERVICES SR ON SR.ID = P.ID_SERVICE
            LEFT JOIN PERSONNES OP ON OP.ID = T.ID_PERSONNE
            WHERE (T.DteFin IS NULL OR T.DteFin = '')
              AND T.DteDeb IS NOT NULL
              {service_filter}
        """, params)
        from datetime import datetime
        aujourdhui = datetime.now().date()
        for row in cursor.fetchall():
            # VÃ©rifier si la date de dÃ©but est aujourd'hui
            try:
                dte_deb = row.DteDeb
                if isinstance(dte_deb, str):
                    dte_deb_date = datetime.strptime(dte_deb[:10], '%Y-%m-%d').date()
                elif isinstance(dte_deb, datetime):
                    dte_deb_date = dte_deb.date()
                else:
                    dte_deb_date = None
            except Exception:
                dte_deb_date = None

            if dte_deb_date == aujourdhui:
                continue  # On ignore cette session, elle n'est pas une anomalie

            anomalies.append({
                "type": "Session ouverte sans date de fin",
                "id_traitement": row.ID,
                "ref_fiche": row.RefFiche,
                "numero_commande": row.numero_commande,
                "poste": row.poste,
                "service": row.service,
                "dte_deb": row.DteDeb,
                "operateur": f"{row.operateur_nom or ''} {row.operateur_prenom or ''}".strip(),
                "details": f"Session ouverte depuis le {row.DteDeb} sur le poste {row.poste}"
            })

        # 2. DurÃ©e incohÃ©rente (fin < dÃ©but)
        cursor.execute(f"""
            SELECT T.ID, FT.RefFiche, C.Numero as numero_commande, P.Nom as poste, SR.Nom as service, T.DteDeb, T.DteFin, OP.Nom as operateur_nom, OP.Prenom as operateur_prenom
            FROM GP_TRAITEMENTS T
            JOIN GP_FICHES_TRAVAIL FT ON FT.ID = T.ID_FICHE_TRAVAIL
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            JOIN GP_POSTES P ON FT.ID_POSTE = P.ID
            JOIN GP_SERVICES SR ON SR.ID = P.ID_SERVICE
            LEFT JOIN PERSONNES OP ON OP.ID = T.ID_PERSONNE
            WHERE T.DteDeb IS NOT NULL AND T.DteFin IS NOT NULL AND T.DteFin < T.DteDeb
              {service_filter}
        """, params)
        for row in cursor.fetchall():
            anomalies.append({
                "type": "DurÃ©e incohÃ©rente",
                "id_traitement": row.ID,
                "ref_fiche": row.RefFiche,
                "numero_commande": row.numero_commande,
                "poste": row.poste,
                "service": row.service,
                "dte_deb": row.DteDeb,
                "dte_fin": row.DteFin,
                "operateur": f"{row.operateur_nom or ''} {row.operateur_prenom or ''}".strip(),
                "details": f"Fin ({row.DteFin}) avant dÃ©but ({row.DteDeb})"
            })

        # 3. QuantitÃ© produite nulle ou nÃ©gative
        cursor.execute(f"""
            SELECT T.ID, FT.RefFiche, C.Numero as numero_commande, P.Nom as poste, SR.Nom as service, T.NbOp, OP.Nom as operateur_nom, OP.Prenom as operateur_prenom
            FROM GP_TRAITEMENTS T
            JOIN GP_FICHES_TRAVAIL FT ON FT.ID = T.ID_FICHE_TRAVAIL
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            JOIN GP_POSTES P ON FT.ID_POSTE = P.ID
            JOIN GP_SERVICES SR ON SR.ID = P.ID_SERVICE
            LEFT JOIN PERSONNES OP ON OP.ID = T.ID_PERSONNE
            WHERE (T.NbOp IS NULL OR T.NbOp <= 0)
              {service_filter}
        """, params)
        for row in cursor.fetchall():
            anomalies.append({
                "type": "QuantitÃ© produite nulle ou nÃ©gative",
                "id_traitement": row.ID,
                "ref_fiche": row.RefFiche,
                "numero_commande": row.numero_commande,
                "poste": row.poste,
                "service": row.service,
                "nb_op": row.NbOp,
                "operateur": f"{row.operateur_nom or ''} {row.operateur_prenom or ''}".strip(),
                "details": f"QuantitÃ© produite : {row.NbOp}"
            })

        # 4. Fiches sans opÃ©rateur ou sans opÃ©ration
        cursor.execute(f"""
            SELECT T.ID, FT.RefFiche, C.Numero as numero_commande, P.Nom as poste, SR.Nom as service, P.ID as poste_id
            FROM GP_TRAITEMENTS T
            JOIN GP_FICHES_TRAVAIL FT ON FT.ID = T.ID_FICHE_TRAVAIL
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            JOIN GP_POSTES P ON FT.ID_POSTE = P.ID
            JOIN GP_SERVICES SR ON SR.ID = P.ID_SERVICE
            WHERE (T.ID_PERSONNE IS NULL OR T.ID_OPERATION IS NULL)
              {service_filter}
        """, params)
        for row in cursor.fetchall():
            anomalies.append({
                "type": "Fiche sans opÃ©rateur ou opÃ©ration",
                "id_traitement": row.ID,
                "ref_fiche": row.RefFiche,
                "numero_commande": row.numero_commande,
                "poste": row.poste,
                "service": row.service,
                "poste_id": row.poste_id,
                "details": "OpÃ©rateur ou opÃ©ration manquante"
            })

    return jsonify({"anomalies": anomalies}) 

@projet13_bp.route("/api/cloturer_session", methods=["POST"])
def cloturer_session():
    data = request.get_json()
    id_traitement = data.get("id_traitement")
    if not id_traitement:
        return jsonify({"success": False, "message": "ID du traitement manquant"}), 400

    now = datetime.now()
    date_fin = now.strftime("%Y-%m-%d %H:%M:%S")
    heure_fin = now.hour + now.minute / 60.0

    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE GP_TRAITEMENTS
            SET DteFin = ?, HeurFin = ?
            WHERE ID = ?
        """, (date_fin, heure_fin, id_traitement))
        cursor.connection.commit()
        # Recalcul temps réel - récupérer l'ID de la fiche depuis le traitement
        cursor.execute("SELECT ID_FICHE_TRAVAIL FROM GP_TRAITEMENTS WHERE ID = ?", (id_traitement,))
        fiche_row = cursor.fetchone()
        if fiche_row:
            recalculer_temps_reel(fiche_row[0], cursor)
            cursor.connection.commit()
    return jsonify({"success": True, "message": "Session clôturée avec succès"}) 

@projet13_bp.route("/api/corriger_duree_incoherente", methods=["POST"])
def corriger_duree_incoherente():
    data = request.get_json()
    id_traitement = data.get("id_traitement")
    if not id_traitement:
        return jsonify({"success": False, "message": "ID du traitement manquant"}), 400
    with get_db_cursor() as cursor:
        cursor.execute("SELECT DteDeb, HeurDeb FROM GP_TRAITEMENTS WHERE ID = ?", (id_traitement,))
        row = cursor.fetchone()
        if not row or not row.DteDeb:
            return jsonify({"success": False, "message": "Date de dÃ©but introuvable"}), 400
        # Calcul de la nouvelle date de fin
        try:
            if isinstance(row.DteDeb, datetime):
                dte_deb = row.DteDeb
            else:
                dte_deb = datetime.strptime(str(row.DteDeb)[:19], "%Y-%m-%d %H:%M:%S")
        except Exception:
            return jsonify({"success": False, "message": "Format de date de dÃ©but invalide"}), 400
        dte_fin = dte_deb + timedelta(hours=1)
        heur_deb = row.HeurDeb if row.HeurDeb is not None else 0.0
        heur_fin = heur_deb + 1.0
        cursor.execute("""
            UPDATE GP_TRAITEMENTS
            SET DteFin = ?, HeurFin = ?
            WHERE ID = ?
        """, (dte_fin.strftime("%Y-%m-%d %H:%M:%S"), heur_fin, id_traitement))
        cursor.connection.commit()
        # Recalcul temps réel - récupérer l'ID de la fiche depuis le traitement
        cursor.execute("SELECT ID_FICHE_TRAVAIL FROM GP_TRAITEMENTS WHERE ID = ?", (id_traitement,))
        fiche_row = cursor.fetchone()
        if fiche_row:
            recalculer_temps_reel(fiche_row[0], cursor)
            cursor.connection.commit()
    return jsonify({"success": True, "message": "Durée corrigée (fin = début + 1h)"})

@projet13_bp.route("/api/corriger_quantite_1", methods=["POST"])
def corriger_quantite_1():
    data = request.get_json()
    id_traitement = data.get("id_traitement")
    if not id_traitement:
        return jsonify({"success": False, "message": "ID du traitement manquant"}), 400
    with get_db_cursor() as cursor:
        cursor.execute("UPDATE GP_TRAITEMENTS SET NbOp = 1 WHERE ID = ?", (id_traitement,))
        cursor.connection.commit()
        # Recalcul temps réel - récupérer l'ID de la fiche depuis le traitement
        cursor.execute("SELECT ID_FICHE_TRAVAIL FROM GP_TRAITEMENTS WHERE ID = ?", (id_traitement,))
        fiche_row = cursor.fetchone()
        if fiche_row:
            recalculer_temps_reel(fiche_row[0], cursor)
            cursor.connection.commit()
    return jsonify({"success": True, "message": "Quantité mise à 1."})

@projet13_bp.route("/api/corriger_operateur_operation", methods=["POST"])
def corriger_operateur_operation():
    data = request.get_json()
    id_traitement = data.get("id_traitement")
    id_personne = data.get("id_personne")
    id_operation = data.get("id_operation")
    if not id_traitement or not id_personne or not id_operation:
        return jsonify({"success": False, "message": "ParamÃ¨tres manquants"}), 400
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE GP_TRAITEMENTS
            SET ID_PERSONNE = ?, ID_OPERATION = ?
            WHERE ID = ?
        """, (id_personne, id_operation, id_traitement))
        cursor.connection.commit()
        # Recalcul temps réel - récupérer l'ID de la fiche depuis le traitement
        cursor.execute("SELECT ID_FICHE_TRAVAIL FROM GP_TRAITEMENTS WHERE ID = ?", (id_traitement,))
        fiche_row = cursor.fetchone()
        if fiche_row:
            recalculer_temps_reel(fiche_row[0], cursor)
            cursor.connection.commit()
    return jsonify({"success": True, "message": "Opérateur et opération assignés."})

@projet13_bp.route("/api/corriger_operateur_defaut", methods=["POST"])
def corriger_operateur_defaut():
    data = request.get_json()
    id_traitement = data.get("id_traitement")
    id_poste = data.get("id_poste")
    if not id_traitement or not id_poste:
        return jsonify({"success": False, "message": "ParamÃ¨tres manquants"}), 400
    with get_db_cursor() as cursor:
        # Trouver l'ID de CHAABANE FRIDA
        cursor.execute("SELECT ID FROM PERSONNES WHERE Nom = 'CHAABANE' AND Prenom = 'FRIDA' AND Archive = 0")
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "OpÃ©rateur 'CHAABANE FRIDA' introuvable"}), 400
        id_personne = row.ID
        # Trouver la premiÃ¨re opÃ©ration disponible pour ce poste
        cursor.execute("SELECT TOP 1 ID FROM GP_POSTES_OP WHERE ID_POSTE = ? AND Archive = 0 ORDER BY ID", (id_poste,))
        op_row = cursor.fetchone()
        if not op_row:
            return jsonify({"success": False, "message": "Aucune opÃ©ration disponible pour ce poste"}), 400
        id_operation = op_row.ID
        # Mettre Ã  jour le traitement
        cursor.execute("""
            UPDATE GP_TRAITEMENTS
            SET ID_PERSONNE = ?, ID_OPERATION = ?
            WHERE ID = ?
        """, (id_personne, id_operation, id_traitement))
        cursor.connection.commit()
        # Recalcul temps réel - récupérer l'ID de la fiche depuis le traitement
        cursor.execute("SELECT ID_FICHE_TRAVAIL FROM GP_TRAITEMENTS WHERE ID = ?", (id_traitement,))
        fiche_row = cursor.fetchone()
        if fiche_row:
            recalculer_temps_reel(fiche_row[0], cursor)
            cursor.connection.commit()
    return jsonify({"success": True, "message": "Opérateur et opération assignés par défaut."})

@projet13_bp.route("/api/corriger_quantite", methods=["POST"])
def corriger_quantite():
    data = request.get_json()
    id_traitement = data.get("id_traitement")
    nb_op = data.get("nb_op")
    if not id_traitement or nb_op is None:
        return jsonify({"success": False, "message": "ParamÃ¨tres manquants"}), 400
    try:
        nb_op = float(nb_op)
        if nb_op <= 0:
            return jsonify({"success": False, "message": "La quantitÃ© doit Ãªtre strictement supÃ©rieure Ã  zÃ©ro."}), 400
    except Exception:
        return jsonify({"success": False, "message": "QuantitÃ© invalide."}), 400
    with get_db_cursor() as cursor:
        cursor.execute("UPDATE GP_TRAITEMENTS SET NbOp = ? WHERE ID = ?", (nb_op, id_traitement))
        cursor.connection.commit()
        # Recalcul temps réel - récupérer l'ID de la fiche depuis le traitement
        cursor.execute("SELECT ID_FICHE_TRAVAIL FROM GP_TRAITEMENTS WHERE ID = ?", (id_traitement,))
        fiche_row = cursor.fetchone()
        if fiche_row:
            recalculer_temps_reel(fiche_row[0], cursor)
            cursor.connection.commit()
    return jsonify({"success": True, "message": f"Quantité mise à {nb_op}."})

@projet13_bp.route("/api/corriger_duree", methods=["POST"])
def corriger_duree():
    data = request.get_json()
    id_traitement = data.get("id_traitement")
    nouvelle_date_deb = data.get("nouvelle_date_deb")
    nouvelle_heure_deb = data.get("nouvelle_heure_deb")
    nouvelle_date_fin = data.get("nouvelle_date_fin")
    nouvelle_heure_fin = data.get("nouvelle_heure_fin")
    if not id_traitement:
        return jsonify({"success": False, "message": "ID du traitement manquant"}), 400
    with get_db_cursor() as cursor:
        if nouvelle_date_deb is not None and nouvelle_heure_deb is not None:
            cursor.execute(
                "UPDATE GP_TRAITEMENTS SET DteDeb = ?, HeurDeb = ? WHERE ID = ?",
                (nouvelle_date_deb, nouvelle_heure_deb, id_traitement)
            )
        if nouvelle_date_fin is not None and nouvelle_heure_fin is not None:
            cursor.execute(
                "UPDATE GP_TRAITEMENTS SET DteFin = ?, HeurFin = ? WHERE ID = ?",
                (nouvelle_date_fin, nouvelle_heure_fin, id_traitement)
            )
        cursor.connection.commit()
        # Recalcul temps réel - récupérer l'ID de la fiche depuis le traitement
        cursor.execute("SELECT ID_FICHE_TRAVAIL FROM GP_TRAITEMENTS WHERE ID = ?", (id_traitement,))
        fiche_row = cursor.fetchone()
        if fiche_row:
            recalculer_temps_reel(fiche_row[0], cursor)
            cursor.connection.commit()
    return jsonify({"success": True, "message": "Date(s) corrigée(s)."})

@projet13_bp.route('/machines_en_production')
def machines_en_production():
    with get_db_cursor() as cursor:
        cursor.execute('''
            SELECT DISTINCT P.Nom as poste, S.Nom as service, FT.RefFiche, C.Numero as numero_commande, T.DteDeb, T.HeurDeb, OP.Nom as operateur_nom, OP.Prenom as operateur_prenom
            FROM GP_TRAITEMENTS T
            JOIN GP_FICHES_TRAVAIL FT ON FT.ID = T.ID_FICHE_TRAVAIL
            JOIN GP_POSTES P ON FT.ID_POSTE = P.ID
            JOIN GP_SERVICES S ON P.ID_SERVICE = S.ID
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            LEFT JOIN PERSONNES OP ON OP.ID = T.ID_PERSONNE
            WHERE T.CodIndAv = 2 AND (T.DteFin IS NULL OR T.DteFin = '' OR T.DteFin = '0000-00-00')
            ORDER BY P.Nom
        ''')
        machines = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    return render_template('machines_en_production.html', machines=machines)

@projet13_bp.route('/api/machines_en_production')
def api_machines_en_production():
    with get_db_cursor() as cursor:
        cursor.execute('''
            SELECT DISTINCT P.Nom as poste, S.Nom as service, FT.RefFiche, C.Numero as numero_commande, T.DteDeb, T.HeurDeb, OP.Nom as operateur_nom, OP.Prenom as operateur_prenom, SO.RaiSocTri as client
            FROM GP_TRAITEMENTS T
            JOIN GP_FICHES_TRAVAIL FT ON FT.ID = T.ID_FICHE_TRAVAIL
            JOIN GP_POSTES P ON FT.ID_POSTE = P.ID
            JOIN GP_SERVICES S ON P.ID_SERVICE = S.ID
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            JOIN SOCIETES SO ON SO.ID = C.ID_SOCIETE
            LEFT JOIN PERSONNES OP ON OP.ID = T.ID_PERSONNE
            WHERE FT.CodIndAv = 2 AND T.DteFin IS NULL
            ORDER BY P.Nom
        ''')
        machines = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    return jsonify({"machines": machines})

@projet13_bp.route("/corriger_dossier", methods=["GET", "POST"])
def corriger_dossier():
    message = ""
    fiches = []
    numero = request.args.get('numero', '').strip()
    correction = False
    if request.method == "POST":
        numero = request.form.get('numero', '').strip()
        correction = request.form.get('correction') == '1'
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT FT.ID, FT.RefFiche, C.Numero, P.Nom as poste, T.ID as id_traitement, T.DteDeb, T.HeurDeb, T.DteFin, T.HeurFin, T.NbOp
                FROM GP_FICHES_TRAVAIL FT
                JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
                LEFT JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
                LEFT JOIN GP_TRAITEMENTS T ON T.ID_FICHE_TRAVAIL = FT.ID
                WHERE C.Numero LIKE ?
            """, (f"%{numero}%",))
            fiches = cursor.fetchall()
        if correction and fiches:
            nb_corrigees = 0
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_lines = []
            with get_db_cursor() as cursor:
                for fiche in fiches:
                    # Log avant correction
                    cursor.execute("SELECT HeurDeb, HeurFin FROM GP_TRAITEMENTS WHERE ID = ?", (fiche.id_traitement,))
                    tr_avant = cursor.fetchone()
                    cursor.execute("SELECT TpsReel FROM GP_FICHTRA_INT WHERE ID_FICHTRA = ?", (fiche.ID,))
                    tps_reel_avant = cursor.fetchone()
                    cursor.execute("SELECT CtReel FROM GP_FICHES_TRAVAIL WHERE ID = ?", (fiche.ID,))
                    ct_reel_avant = cursor.fetchone()
                    # Correction des heures (virgule -> point)
                    heur_deb = fiche.HeurDeb
                    if heur_deb is None or heur_deb == '' or (isinstance(heur_deb, str) and heur_deb.strip() == ''):
                        heur_deb = 0.0
                    elif isinstance(heur_deb, str):
                        heur_deb = heur_deb.replace(',', '.')
                        try:
                            heur_deb = float(heur_deb)
                        except Exception:
                            heur_deb = 0.0
                    heur_fin = fiche.HeurFin if hasattr(fiche, 'HeurFin') else 0.0
                    if heur_fin is None or heur_fin == '' or (isinstance(heur_fin, str) and heur_fin.strip() == ''):
                        heur_fin = 0.0
                    elif isinstance(heur_fin, str):
                        heur_fin = heur_fin.replace(',', '.')
                        try:
                            heur_fin = float(heur_fin)
                        except Exception:
                            heur_fin = 0.0
                    # Recalcul du temps rÃ©el total Ã  partir des traitements
                    cursor.execute("SELECT HeurDeb, HeurFin FROM GP_TRAITEMENTS WHERE ID_FICHE_TRAVAIL = ?", (fiche.ID,))
                    traitements = cursor.fetchall()
                    tps_reel = 0.0
                    for tr in traitements:
                        hdeb = tr.HeurDeb
                        hfin = tr.HeurFin
                        try:
                            hdeb = float(str(hdeb).replace(',', '.')) if hdeb is not None else 0.0
                        except Exception:
                            hdeb = 0.0
                        try:
                            hfin = float(str(hfin).replace(',', '.')) if hfin is not None else 0.0
                        except Exception:
                            hfin = 0.0
                        tps_reel += max(0.0, hfin - hdeb)
                    # Mise Ã  jour du temps rÃ©el dans GP_FICHTRA_INT et GP_FICHES_TRAVAIL
                    cursor.execute("UPDATE GP_FICHTRA_INT SET TpsReel = ? WHERE ID_FICHTRA = ?", (tps_reel, fiche.ID))
                    cursor.execute("UPDATE GP_FICHES_TRAVAIL SET CtReel = ? WHERE ID = ?", (tps_reel, fiche.ID))
                    nb_op = fiche.NbOp
                    if nb_op is None or nb_op == 0:
                        nb_op = 1
                    dte_deb = fiche.DteDeb
                    if not dte_deb or str(dte_deb).strip() == '' or str(dte_deb).startswith('1900') or str(dte_deb).startswith('0000'):
                        dte_deb = now_str
                    dte_fin = fiche.DteFin
                    if not dte_fin or str(dte_fin).strip() == '' or str(dte_fin).startswith('1900') or str(dte_fin).startswith('0000'):
                        dte_fin = now_str
                    if fiche.id_traitement:
                        cursor.execute("""
                            UPDATE GP_TRAITEMENTS
                            SET HeurDeb = ?, HeurFin = ?, NbOp = ?, DteDeb = ?, DteFin = ?
                            WHERE ID = ?
                        """, (heur_deb, heur_fin, nb_op, dte_deb, dte_fin, fiche.id_traitement))
                        nb_corrigees += 1
                    # Correction GP_FICHTRA_INT (durÃ©es)
                    cursor.execute("""
                        UPDATE GP_FICHTRA_INT
                        SET TpsReel = COALESCE(TpsReel, 0), TpsPrevDev = COALESCE(TpsPrevDev, 0), TpsPrevAte = COALESCE(TpsPrevAte, 0)
                        WHERE ID_FICHTRA = ?
                    """, (fiche.ID,))
                    # Correction GP_FICHES_OPERATIONS (opÃ©rations)
                    cursor.execute("""
                        UPDATE GP_FICHES_OPERATIONS
                        SET TpsRelPass = COALESCE(TpsRelPass, 0), OpReel = COALESCE(OpReel, 0)
                        WHERE ID_FICHE_TRAVAIL = ?
                    """, (fiche.ID,))
                    # Log aprÃ¨s correction
                    cursor.execute("SELECT HeurDeb, HeurFin FROM GP_TRAITEMENTS WHERE ID = ?", (fiche.id_traitement,))
                    tr_apres = cursor.fetchone()
                    cursor.execute("SELECT TpsReel FROM GP_FICHTRA_INT WHERE ID_FICHTRA = ?", (fiche.ID,))
                    tps_reel_apres = cursor.fetchone()
                    cursor.execute("SELECT CtReel FROM GP_FICHES_TRAVAIL WHERE ID = ?", (fiche.ID,))
                    ct_reel_apres = cursor.fetchone()
                    log_lines.append(f"Fiche {fiche.ID} (Traitement {fiche.id_traitement})\n  AVANT: HeurDeb={tr_avant.HeurDeb if tr_avant else None}, HeurFin={tr_avant.HeurFin if tr_avant else None}, TpsReel={tps_reel_avant.TpsReel if tps_reel_avant else None}, CtReel={ct_reel_avant.CtReel if ct_reel_avant else None}\n  APRES: HeurDeb={tr_apres.HeurDeb if tr_apres else None}, HeurFin={tr_apres.HeurFin if tr_apres else None}, TpsReel={tps_reel_apres.TpsReel if tps_reel_apres else None}, CtReel={ct_reel_apres.CtReel if ct_reel_apres else None}\n")
                cursor.connection.commit()
            # Ã‰criture du log dÃ©taillÃ©
            with open('correction_dossier.log', 'a', encoding='utf-8') as flog:
                flog.write(f"--- Correction du {now_str} pour dossier '{numero}' ---\n")
                for line in log_lines:
                    flog.write(line)
            message = f"{nb_corrigees} fiches corrigÃ©es pour le dossier contenant '{numero}'. (voir correction_dossier.log)"
            log_detail = "\n".join(log_lines)
    return render_template("corriger_dossier.html", fiches=fiches, message=message, numero=numero, correction=correction, log_detail=log_detail if correction else None)

@projet13_bp.route("/api/corriger_dossier", methods=["POST"])
def api_corriger_dossier():
    data = request.get_json()
    numero = data.get('numero', '').strip()
    if not numero:
        return jsonify({'success': False, 'message': 'NumÃ©ro de dossier manquant'}), 400
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT FT.ID, FT.RefFiche, C.Numero, P.Nom as poste, T.ID as id_traitement, T.DteDeb, T.HeurDeb, T.DteFin, T.HeurFin, T.NbOp
            FROM GP_FICHES_TRAVAIL FT
            JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
            LEFT JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
            LEFT JOIN GP_TRAITEMENTS T ON T.ID_FICHE_TRAVAIL = FT.ID
            WHERE C.Numero LIKE ?
        """, (f"%{numero}%",))
        fiches = cursor.fetchall()
        nb_corrigees = 0
        for fiche in fiches:
            if fiche.HeurDeb and isinstance(fiche.HeurDeb, str):
                heur_deb = fiche.HeurDeb.replace(',', '.')
                try:
                    heur_deb = float(heur_deb)
                except:
                    heur_deb = None
            else:
                heur_deb = fiche.HeurDeb
            if fiche.HeurFin and isinstance(fiche.HeurFin, str):
                heur_fin = fiche.HeurFin.replace(',', '.')
                try:
                    heur_fin = float(heur_fin)
                except:
                    heur_fin = None
            else:
                heur_fin = fiche.HeurFin
            nb_op = fiche.NbOp
            if nb_op is None or nb_op == 0:
                nb_op = 1
            dte_deb = fiche.DteDeb
            dte_fin = fiche.DteFin
            if not dte_deb:
                dte_deb = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not dte_fin:
                dte_fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if fiche.id_traitement:
                cursor.execute("""
                    UPDATE GP_TRAITEMENTS
                    SET HeurDeb = ?, HeurFin = ?, NbOp = ?, DteDeb = ?, DteFin = ?
                    WHERE ID = ?
                """, (heur_deb, heur_fin, nb_op, dte_deb, dte_fin, fiche.id_traitement))
                nb_corrigees += 1
        cursor.connection.commit()
    return jsonify({'success': True, 'message': f'{nb_corrigees} fiches corrigÃ©es pour le dossier contenant {numero}.'})

@projet13_bp.route("/nulls_dossier", methods=["GET", "POST"])
def nulls_dossier():
    rapport = []
    numero = ''
    if request.method == "POST":
        numero = request.form.get('numero', '').strip()
        if numero:
            with get_db_cursor() as cursor:
                # 1. RÃ©cupÃ©rer les ID de fiches du dossier
                cursor.execute("SELECT FT.ID FROM GP_FICHES_TRAVAIL FT JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE WHERE C.Numero LIKE ?", (f"%{numero}%",))
                fiches = [row.ID for row in cursor.fetchall()]
                if not fiches:
                    return render_template("nulls_dossier.html", rapport=rapport, numero=numero)
                # 2. Lister toutes les tables de la base
                cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
                all_tables = [row[0] for row in cursor.fetchall()]
                # 3. Pour chaque table, chercher une colonne de lien
                colonnes_lien = ['ID_COMMANDE', 'ID_FICHE_TRAVAIL', 'ID_FICHTRA', 'ID', 'NumDossier', 'Numero']
                for table in all_tables:
                    # RÃ©cupÃ©rer les colonnes de la table
                    cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?", (table,))
                    columns = [row[0] for row in cursor.fetchall()]
                    # Chercher une colonne de lien prÃ©sente dans la table
                    col_lien = None
                    for col in colonnes_lien:
                        if col in columns:
                            col_lien = col
                            break
                    if not col_lien:
                        continue  # Table non liÃ©e au dossier
                    # PrÃ©parer la requÃªte pour trouver les lignes liÃ©es
                    if col_lien in ['ID_FICHE_TRAVAIL', 'ID_FICHTRA', 'ID']:
                        # On cherche les lignes dont la colonne de lien est dans la liste des fiches
                        placeholders = ','.join(['?'] * len(fiches))
                        query = f"SELECT * FROM {table} WHERE {col_lien} IN ({placeholders})"
                        cursor.execute(query, fiches)
                    elif col_lien == 'ID_COMMANDE':
                        # On cherche les lignes dont la commande est celle du dossier
                        cursor.execute(f"SELECT ID FROM COMMANDES WHERE Numero LIKE ?", (f"%{numero}%",))
                        commandes = [row[0] for row in cursor.fetchall()]
                        if not commandes:
                            continue
                        placeholders = ','.join(['?'] * len(commandes))
                        query = f"SELECT * FROM {table} WHERE {col_lien} IN ({placeholders})"
                        cursor.execute(query, commandes)
                    elif col_lien in ['NumDossier', 'Numero']:
                        # On cherche les lignes dont le numÃ©ro de dossier correspond
                        query = f"SELECT * FROM {table} WHERE {col_lien} LIKE ?"
                        cursor.execute(query, (f"%{numero}%",))
                    else:
                        continue
                    # Chercher les NULL dans les rÃ©sultats
                    for row in cursor.fetchall():
                        columns = [desc[0] for desc in cursor.description]
                        try:
                            id_index = columns.index(col_lien)
                        except ValueError:
                            id_index = 0
                        for i, k in enumerate(columns):
                            if row[i] is None:
                                rapport.append({
                                    'table': table,
                                    'id': row[id_index],
                                    'colonne': k
                                })
    return render_template("nulls_dossier.html", rapport=rapport, numero=numero)

@projet13_bp.route("/supprimer_dossier", methods=["GET", "POST"])
def supprimer_dossier():
    message = ""
    numero = ''
    rapport = []
    if request.method == "POST":
        numero = request.form.get('numero', '').strip()
        if numero:
            try:
                with get_db_cursor() as cursor:
                    # RÃ©cupÃ©rer les ID de fiches et de commandes
                    cursor.execute("SELECT ID FROM COMMANDES WHERE Numero LIKE ?", (f"%{numero}%",))
                    commandes = [row[0] for row in cursor.fetchall()]
                    if not commandes:
                        message = f"Aucune commande trouvÃ©e pour '{numero}'."
                        return render_template("supprimer_dossier.html", message=message, numero=numero, rapport=rapport)
                    cursor.execute("SELECT ID FROM GP_FICHES_TRAVAIL WHERE ID_COMMANDE IN ({})".format(','.join(['?']*len(commandes))), commandes)
                    fiches = [row[0] for row in cursor.fetchall()]
                    # Suppression dans l'ordre (tables enfants -> parent)
                    # 1. GS_TAMPONS_LIGNES
                    if fiches:
                        cursor.execute(f"DELETE FROM GS_TAMPONS_LIGNES WHERE ID_FICHE_TRAVAIL IN ({','.join(['?']*len(fiches))})", fiches)
                        rapport.append(f"GS_TAMPONS_LIGNES : {cursor.rowcount} lignes supprimÃ©es.")
                    # 2. GP_FACT_ACHATS_SSTR
                    cursor.execute(f"DELETE FROM GP_FACT_ACHATS_SSTR WHERE ID_COMMANDE IN ({','.join(['?']*len(commandes))})", commandes)
                    rapport.append(f"GP_FACT_ACHATS_SSTR : {cursor.rowcount} lignes supprimÃ©es.")
                    # 3. GP_RESSOURCES_TRAV
                    if fiches:
                        cursor.execute(f"DELETE FROM GP_RESSOURCES_TRAV WHERE ID_FICHTRA IN ({','.join(['?']*len(fiches))})", fiches)
                        rapport.append(f"GP_RESSOURCES_TRAV : {cursor.rowcount} lignes supprimÃ©es.")
                    # 4. GS_MVT_STOCKS
                    cursor.execute(f"DELETE FROM GS_MVT_STOCKS WHERE ID_COMMANDE IN ({','.join(['?']*len(commandes))})", commandes)
                    rapport.append(f"GS_MVT_STOCKS : {cursor.rowcount} lignes supprimÃ©es.")
                    # 5. GP_RESSOURCES
                    if fiches:
                        cursor.execute(f"DELETE FROM GP_RESSOURCES WHERE ID_FICHTRA IN ({','.join(['?']*len(fiches))})", fiches)
                        rapport.append(f"GP_RESSOURCES : {cursor.rowcount} lignes supprimÃ©es.")
                    # 6. GP_FICHES_TRAVAIL
                    cursor.execute(f"DELETE FROM GP_FICHES_TRAVAIL WHERE ID_COMMANDE IN ({','.join(['?']*len(commandes))})", commandes)
                    rapport.append(f"GP_FICHES_TRAVAIL : {cursor.rowcount} lignes supprimÃ©es.")
                    cursor.connection.commit()
                    message = f"Suppression terminÃ©e pour le dossier '{numero}'."
            except Exception as e:
                message = f"Erreur lors de la suppression : {str(e)}"
    return render_template("supprimer_dossier.html", message=message, numero=numero, rapport=rapport)
