from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from db import get_db_cursor
from datetime import datetime, timedelta
from contextlib import contextmanager
try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False
    pdfkit = None



projet6_bp = Blueprint('projet6', __name__)

@projet6_bp.route('/projet6', methods=['GET'])
def programme_voyage():
    with get_db_cursor() as cur:
        # 🔽 On récupère la liste des camions pour le menu déroulant
        cur.execute("SELECT * FROM CAMIONS ORDER BY Immatriculation")
        camions = cur.fetchall()

    return render_template('projet6.html', camions=camions)

@projet6_bp.route('/projet6/save', methods=['POST'])
def save_programme():
    with get_db_cursor() as cur:
        date_voyage = request.form.get('date')
        destination = request.form.get('destination')
        camion = request.form.get('camion')
        chauffeur = request.form.get('chauffeur')

        lignes = []
        index = 0
        while True:
            client = request.form.get(f'client_{index}')
            num_dossier = request.form.get(f'num_dossier_{index}')
            quantite = request.form.get(f'quantite_{index}')
            pieces_par_carton = request.form.get(f'pieces_par_carton_{index}')
            cartons_par_palette = request.form.get(f'cartons_par_palette_{index}')
            nb_carton = request.form.get(f'nb_carton_{index}')
            nb_palette = request.form.get(f'nb_palette_{index}')
            termine = request.form.get(f'termine_{index}') == 'on'

            if not client and not num_dossier:
                break

            lignes.append({
                'Client': client,
                'NumDossier': num_dossier,
                'Quantite': quantite,
                'PiecesParCarton': pieces_par_carton,
                'CartonsParPalette': cartons_par_palette,
                'NbCarton': nb_carton,
                'NbPalette': nb_palette,
                'Termine': termine
            })
            index += 1

        try:
            cur.execute("""
                INSERT INTO VOYAGES (DateVoyage, Destination, Camion, Chauffeur)
                OUTPUT INSERTED.ID, INSERTED.NumeroVoyage
                VALUES (?, ?, ?, ?)
            """, (date_voyage, destination, camion, chauffeur))
            result = cur.fetchone()
            id_voyage, numero_voyage = result

            for ligne in lignes:
                cur.execute("""
                    INSERT INTO VOYAGE_LIGNES (
                        ID_VOYAGE, Client, NumDossier, Quantite,
                        PiecesParCarton, CartonsParPalette, NbCarton,
                        NbPalette, Termine
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (id_voyage, ligne['Client'], ligne['NumDossier'], ligne['Quantite'],
                      ligne['PiecesParCarton'], ligne['CartonsParPalette'],
                      ligne['NbCarton'], ligne['NbPalette'], ligne['Termine']))

                if ligne['Termine']:
                    cur.execute("UPDATE COMMANDES SET Termine = 1 WHERE Numero = ?", (ligne['NumDossier'],))

            cur.connection.commit()
            flash("Programme de voyage enregistré avec succès", "success")

            # ✅ Re-render form avec les infos remplies et lignes conservées
            return render_template(
                'projet6.html', 
                date=date_voyage, destination=destination, camion_selectionne=camion,
                chauffeur=chauffeur, id_voyage=id_voyage, numero_voyage=numero_voyage,
                lignes=lignes, camions=get_camions(cur)
            )

        except Exception as e:
            cur.connection.rollback()
            flash(f"Erreur lors de l'enregistrement : {e}", "danger")
            return render_template('projet6.html', camions=get_camions(cur))


@projet6_bp.route('/api/commandes')
def api_commandes():
    try:
        q = request.args.get('q', '')
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT c.Numero, s.RaiSocTri as Client, c.QteComm, c.Reference
                FROM COMMANDES c
                LEFT JOIN SOCIETES s ON c.ID_SOCIETE = s.ID
                WHERE (c.Numero LIKE ? OR s.RaiSocTri LIKE ?) AND c.Termine = 0
                ORDER BY c.Numero DESC
                OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY
            """, (f"%{q}%", f"%{q}%"))
            
            rows = cur.fetchall()
            resultats = [
                {"Numero": row[0], "Client": row[1], "QteComm": row[2], "Reference": row[3]}
                for row in rows
            ]
            return jsonify(resultats)
    except Exception as e:
        print("❌ Erreur dans /api/commandes :", e)
        return jsonify([]), 500

@projet6_bp.route('/projet6/voyages', methods=['GET'])
def list_voyages():
    numero = request.args.get('numero', '').strip()
    date = request.args.get('date', '').strip()

    query = """
        SELECT ID, NumeroVoyage, DateVoyage, Destination, Camion, Chauffeur
        FROM VOYAGES
        WHERE 1=1
    """
    params = []

    if numero:
        query += " AND NumeroVoyage LIKE ?"
        params.append(f"%{numero}%")

    if date:
        query += " AND DateVoyage = ?"
        params.append(date)

    query += " ORDER BY ID DESC"

    with get_db_cursor() as cur:
        cur.execute(query, params)
        voyages = cur.fetchall()

    return render_template('voyages_list.html', voyages=voyages, search_numero=numero, search_date=date)


@projet6_bp.route('/projet6/edit/<int:id>', methods=['GET', 'POST'])
def edit_voyage(id):
    with get_db_cursor() as cur:
        if request.method == 'GET':
            cur.execute("SELECT ID, NumeroVoyage, DateVoyage, Destination, Camion, Chauffeur FROM VOYAGES WHERE ID = ?", (id,))
            voyage = cur.fetchone()
            if not voyage:
                flash("Voyage introuvable", "danger")
                return redirect(url_for('projet6.list_voyages'))

            cur.execute("""
                SELECT ID, Client, NumDossier, Quantite, PiecesParCarton, CartonsParPalette, NbCarton, NbPalette, Termine
                FROM VOYAGE_LIGNES WHERE ID_VOYAGE = ? ORDER BY ID
            """, (id,))
            lignes = cur.fetchall()

            cur.execute("SELECT * FROM CAMIONS")
            camions = cur.fetchall()

            return render_template('edit_voyage.html', voyage=voyage, lignes=lignes, camions=camions)

        else:
            date_voyage = request.form.get('date')
            destination = request.form.get('destination')
            camion = request.form.get('camion')
            chauffeur = request.form.get('chauffeur')

            try:
                cur.execute("""
                    UPDATE VOYAGES SET DateVoyage=?, Destination=?, Camion=?, Chauffeur=? WHERE ID=?
                """, (date_voyage, destination, camion, chauffeur, id))

                cur.execute("DELETE FROM VOYAGE_LIGNES WHERE ID_VOYAGE = ?", (id,))

                nb_lignes = int(request.form.get('nb_lignes'))
                for index in range(nb_lignes):
                    client = request.form.get(f'client_{index}')
                    num_dossier = request.form.get(f'num_dossier_{index}')
                    quantite = request.form.get(f'quantite_{index}')
                    pieces_par_carton = request.form.get(f'pieces_par_carton_{index}')
                    cartons_par_palette = request.form.get(f'cartons_par_palette_{index}')
                    nb_carton = request.form.get(f'nb_carton_{index}')
                    nb_palette = request.form.get(f'nb_palette_{index}')
                    termine = request.form.get(f'termine_{index}') == 'on'

                    cur.execute("""
                        INSERT INTO VOYAGE_LIGNES (ID_VOYAGE, Client, NumDossier, Quantite,
                            PiecesParCarton, CartonsParPalette, NbCarton, NbPalette, Termine)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (id, client, num_dossier, quantite, pieces_par_carton, cartons_par_palette, nb_carton, nb_palette, termine))

                cur.connection.commit()
                flash("Voyage mis à jour avec succès.", "success")
                return redirect(url_for('projet6.edit_voyage', id=id))

            except Exception as e:
                cur.connection.rollback()
                flash(f"Erreur de mise à jour : {e}", "danger")
                return redirect(url_for('projet6.edit_voyage', id=id))

def get_camions(cur):
    cur.execute("SELECT * FROM CAMIONS")
    return cur.fetchall()

@projet6_bp.route('/projet6/ajouter-camion', methods=['GET', 'POST'])
def ajouter_camion():
    with get_db_cursor() as cur:
        if request.method == 'POST':
            immat = request.form.get('immat')
            marque = request.form.get('marque')
            modele = request.form.get('modele')
            date_achat = request.form.get('date_achat')
            try:
                cur.execute("""
                    INSERT INTO CAMIONS (Immatriculation, Marque, Modele, DateAchat)
                    VALUES (?, ?, ?, ?)
                """, (immat, marque, modele, date_achat))
                cur.connection.commit()
                flash("Camion ajouté avec succès", "success")
                return redirect(url_for('projet6.ajouter_camion'))
            except Exception as e:
                cur.connection.rollback()
                flash(f"Erreur : {e}", "danger")

        return render_template('ajouter_camion.html')

from datetime import datetime, timedelta

@projet6_bp.route('/projet6/camions', methods=['GET'])
def liste_camions():
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT ID, Immatriculation, Marque, Modele, DateAchat,
                   DateVisiteTechnique, DatePaiementTaxe, Observations
            FROM CAMIONS
            ORDER BY Immatriculation
        """)
        rows = cur.fetchall()

    # 🧠 Conversion manuelle des champs date (index 4, 5, 6)
    camions = []
    for row in rows:
        row = list(row)
        for i in [4, 5, 6]:
            if row[i] and isinstance(row[i], str):
                try:
                    row[i] = datetime.strptime(row[i], "%Y-%m-%d").date()
                except:
                    row[i] = None
        camions.append(row)

    return render_template(
        'liste_camions.html',
        camions=camions,
        today=datetime.today().date(),
        timedelta=timedelta
    )

@projet6_bp.route('/projet6/camion/<int:id>/edit', methods=['GET', 'POST'])
def edit_camion(id):
    with get_db_cursor() as cur:
        if request.method == 'POST':
            visite = request.form.get('date_visite')
            taxe = request.form.get('date_taxe')
            observations = request.form.get('observations')

            try:
                cur.execute("""
                    UPDATE CAMIONS
                    SET DateVisiteTechnique = ?, DatePaiementTaxe = ?, Observations = ?
                    WHERE ID = ?
                """, (visite, taxe, observations, id))
                cur.connection.commit()
                flash("Camion mis à jour avec succès", "success")
                return redirect(url_for('projet6.liste_camions'))
            except Exception as e:
                cur.connection.rollback()
                flash(f"Erreur : {e}", "danger")

        cur.execute("SELECT * FROM CAMIONS WHERE ID = ?", (id,))
        camion = cur.fetchone()

    return render_template('edit_camion.html', camion=camion)
@projet6_bp.route('/api/camions', methods=['GET'])
def api_camions():
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT Immatriculation, Marque, Modele
            FROM CAMIONS
            ORDER BY Immatriculation
        """)
        rows = cur.fetchall()
    return jsonify([
        {"immat": r[0], "marque": r[1], "modele": r[2]} for r in rows
    ])
from flask import make_response, render_template



if PDFKIT_AVAILABLE:
    try:
        config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    except Exception:
        config = None
else:
    config = None

@projet6_bp.route('/projet6/pdf/<int:id>')
def export_pdf(id):
    if not PDFKIT_AVAILABLE or config is None:
        flash("Export PDF non disponible : pdfkit n'est pas installé ou wkhtmltopdf n'est pas configuré.", "danger")
        return redirect(url_for('projet6.programme_voyage'))
    with get_db_cursor() as cur:
        cur.execute("SELECT NumeroVoyage, DateVoyage, Destination, Camion, Chauffeur FROM VOYAGES WHERE ID = ?", (id,))
        voyage_data = cur.fetchone()

        if not voyage_data:
            flash("Voyage introuvable.", "danger")
            return redirect(url_for('projet6.programme_voyage'))

        voyage = {
            "NumeroVoyage": voyage_data[0],
            "DateVoyage": voyage_data[1],
            "Destination": voyage_data[2],
            "Camion": voyage_data[3],
            "Chauffeur": voyage_data[4]
        }

        cur.execute("""
            SELECT Client, NumDossier, Quantite, PiecesParCarton, 
                   CartonsParPalette, NbCarton, NbPalette, Termine
            FROM VOYAGE_LIGNES
            WHERE ID_VOYAGE = ?
        """, (id,))
        lignes_data = cur.fetchall()

        lignes = [{
            "Client": ligne[0],
            "NumDossier": ligne[1],
            "Quantite": ligne[2],
            "PiecesParCarton": ligne[3],
            "CartonsParPalette": ligne[4],
            "NbCarton": ligne[5],
            "NbPalette": ligne[6],
            "Termine": bool(ligne[7])
        } for ligne in lignes_data]

    rendered = render_template("programme_pdf.html", voyage=voyage, lignes=lignes)
    options = {'enable-local-file-access': None, 'quiet': ''}
    pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=programme_voyage_{voyage['NumeroVoyage']}.pdf"
    return response
