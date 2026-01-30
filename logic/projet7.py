from flask import Blueprint, render_template, request
import os
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    pdfplumber = None
import re
from werkzeug.utils import secure_filename
from datetime import datetime
from db import get_db_cursor

projet7_bp = Blueprint('projet7_bp', __name__, template_folder='templates')

def convert_date_fr(date_str):
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except:
        return None

def extract_facture_data(file_path):
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError("pdfplumber n'est pas installe. Installez-le avec: pip install pdfplumber")
    donnees = {}
    with pdfplumber.open(file_path) as pdf:
        lignes = pdf.pages[0].extract_text().splitlines()

        for i, ligne in enumerate(lignes):
            print(f"Ligne {i + 1}: {ligne}")

        match_num = re.search(r'\b\d{5,}\b', lignes[0])
        donnees['numero_facture'] = match_num.group() if match_num else ''

        match_date = re.search(r'(\d{2})/(\d{4})', lignes[1])
        if match_date:
            donnees['mois'] = match_date.group(1)
            donnees['annee'] = match_date.group(2)

        if len(lignes) >= 10:
            ligne_10 = lignes[9]
            print(f"🔍 Analyse forcée ligne 10: {ligne_10}")
            valeurs = ligne_10.split()
            print(f"🔢 Valeurs extraites ligne 10 : {valeurs}")
            if len(valeurs) >= 8:
                donnees.update({
                    'consommation_totale_decomp': valeurs[0] + ' ' + valeurs[1],
                    'additionnel_1': valeurs[2],
                    'additionnel_2': valeurs[3],
                    'difference_indices': valeurs[4],
                    'coefficient': valeurs[5],
                    'index_debut': valeurs[6],
                    'index_fin': valeurs[7],
                })

        match_13 = re.findall(r'\d{1,3} \d{3}|\d+', lignes[12])
        if len(match_13) >= 2:
            donnees['prix_unitaire_kwh'] = match_13[0]
            donnees['consommation_totale'] = match_13[1]

        match_bonif = re.search(r'-?\d+,\d+', lignes[16])
        if match_bonif:
            donnees['bonification'] = float(match_bonif.group().replace(',', '.'))

        match_19 = re.findall(r'\d{1,3} \d{3},\d{3}|\d+,\d{4}', lignes[18])
        if len(match_19) >= 2:
            donnees['montant_ht'] = float(match_19[0].replace(' ', '').replace(',', '.'))
            donnees['coef_k'] = float(match_19[1].replace(',', '.'))

        match_cosphi = re.search(r'\d+\.\d+', lignes[17])
        if match_cosphi:
            donnees['cosphi'] = float(match_cosphi.group())

        match_banque = re.search(r'[A-Z\\.]+', lignes[24])
        match_date_paiement = re.search(r'\d{2}/\d{2}/\d{4}', lignes[24])
        donnees['banque'] = match_banque.group() if match_banque else ''
        donnees['date_paiement'] = match_date_paiement.group() if match_date_paiement else ''

        match_ttc = re.search(r'\d{1,3}(?: \d{3})?,\d{3}', lignes[31])
        if match_ttc:
            donnees['montant_ttc'] = float(match_ttc.group().replace(' ', '').replace(',', '.'))

    return donnees

def get_factures_enregistrees():
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT NumFacture, PeriodeDebut, PeriodeFin, ConsommationKWh, MontantHT,
                   CoefficientK, CosPHI, DatePaiement, MoyenPaiement
            FROM FACTURES_STEG
            ORDER BY DatePaiement DESC
        """)
        colonnes = [desc[0] for desc in cursor.description]
        return [dict(zip(colonnes, row)) for row in cursor.fetchall()]

@projet7_bp.route('/import_facture', methods=['GET', 'POST'])
def import_facture():
    factures_table = get_factures_enregistrees() if request.args.get("voir") == "1" else []

    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            file.save(file_path)

            factures = extract_facture_data(file_path)
            if factures:
                return render_template('projet7.html', factures=factures, table=factures_table)
            else:
                return "Erreur d'extraction", 400

    return render_template('projet7.html', table=factures_table)

@projet7_bp.route('/valider_facture', methods=['POST'])
def valider_facture():
    data = request.form.to_dict()
    print("\n📥 Données reçues:", data)

    if 'index_debut' not in data or 'index_fin' not in data:
        return render_template("projet7.html", factures=data, message="❌ Index début/fin manquant dans les données.")

    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM FACTURES_STEG WHERE NumFacture = ?", (data['numero_facture'],))
            if cursor.fetchone()[0] > 0:
                return render_template("projet7.html", factures=data, message="⚠️ Facture déjà enregistrée.")

            num_facture = data['numero_facture']
            annee, mois = data['annee'], data['mois']
            periode_debut = f"{annee}-{mois}-01"
            periode_fin = f"{annee}-{mois}-30"
            date_emission = date_echeance = periode_fin
            date_paiement = convert_date_fr(data['date_paiement'])

            conso = float(data['consommation_totale'].replace(' ', '').replace(',', '.'))
            montant_ht = float(data['montant_ht'])
            cosphi = float(data.get('cosphi', 0))
            prix_unit_kwh = float(data['prix_unitaire_kwh'].replace(' ', '').replace(',', '.')) / 1000
            coef_k = float(data['coef_k'])
            bonification = float(data.get('bonification', 0))
            montant_energie = montant_ht
            index_debut = int(data['index_debut'])
            index_fin = int(data['index_fin'])
            moyen_paiement = f"Domiciliation {data.get('banque', '')}"
            observations = "Facture extraite automatiquement depuis PDF"

            cursor.execute("""
                INSERT INTO FACTURES_STEG (
                    NumFacture, PeriodeDebut, PeriodeFin, DateEmission, DateEcheance,
                    TypeEnergie, ConsommationKWh, PrixUnitaireKWh, MontantEnergie, Bonification,
                    MontantHT, CosPHI, StatutPaiement, DatePaiement, MoyenPaiement,
                    CoefficientK, Observations, IndexDebut, IndexFin
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                num_facture, periode_debut, periode_fin, date_emission, date_echeance,
                "Electricité", conso, prix_unit_kwh, montant_energie, bonification,
                montant_ht, cosphi, "Payée", date_paiement, moyen_paiement,
                coef_k, observations, index_debut, index_fin
            ))
            cursor.connection.commit()

    except Exception as e:
        print("❌ Erreur d'insertion :", e)
        return render_template("projet7.html", factures=data, message=f"❌ Erreur : {e}")

    table = get_factures_enregistrees()
    return render_template("projet7.html", message="✅ Facture enregistrée en base avec succès.", table=table)
