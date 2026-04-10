from flask import Blueprint, jsonify, render_template, request, Response
from flask import redirect, url_for, flash
import io
import base64
from db import (
    get_controles_qualite, 
    get_controle_qualite_by_id,
    create_controle_qualite,
    update_controle_qualite,
    delete_controle_qualite,
    get_statistiques_controle_qualite,
    get_performance_par_machine,
    get_evolution_qualite,
    get_dossiers_probleme,
    get_numeros_commandes_disponibles,
    get_operateurs,
    get_comparaison_periodes,
    get_comparaison_machines,
    get_machines_impression,
    get_machines_decoupe,
    get_traitement_data_for_controle,
    get_projet10_schema_info,
    get_db_cursor,
    recalcul_tous_controles_qualite_manq_gan_et_crebut,
)
from logic.auth import get_user_sections, is_super_user, has_action_access

# Déclaration du blueprint
bp = Blueprint("projet10", __name__, url_prefix="/projet10")

@bp.route("/")
def index():
    """Page principale du Projet 10 - affiche uniquement les sections autorisées"""
    try:
        # Récupérer les sections autorisées pour le Projet 10 (NumProj = 10)
        authorized_sections = get_user_sections(10)
        
        # Créer un dictionnaire pour faciliter la vérification dans le template
        sections_dict = {s['id']: s['nom'] for s in authorized_sections}
        
        # Créer un set des IDs des sections autorisées pour vérification rapide
        authorized_section_ids = {s['id'] for s in authorized_sections}
        
        # Récupérer tous les IDs des sections du Projet 10 pour faire le mapping nom -> ID
        all_sections_map = {}  # {nom_lower: id}
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT WS.ID, WS.Nom
                    FROM WEB_SECTIONS WS
                    INNER JOIN WEB_PROJETS WP ON WP.ID = WS.ID_Proj
                    WHERE WP.NumProj = 10 OR WP.ID = 10
                """)
                for row in cursor.fetchall():
                    all_sections_map[row.Nom.lower()] = row.ID
        except Exception as e:
            print(f"Erreur lors de la récupération des IDs de sections: {e}")
        
        # Déterminer quelles sections afficher basé sur les sections autorisées
        show_liste_controles = False
        show_nouveau_controle = False
        show_statistiques = False
        show_rapports_cq = False

        if is_super_user():
            # Super-utilisateur : toutes les sections
            show_liste_controles = True
            show_nouveau_controle = True
            show_statistiques = True
            show_rapports_cq = True
        else:
            # Vérifier chaque section autorisée par son nom pour déterminer quelle carte afficher
            for section in authorized_sections:
                section_nom_lower = section['nom'].lower()
                section_id = section['id']
                
                # Section "Liste des contrôles" - vérifier par nom ET par ID si disponible
                if (section_id in authorized_section_ids and 
                    (('liste' in section_nom_lower and 'contr' in section_nom_lower) or
                     section_id == all_sections_map.get('liste des contrôles', -1))):
                    show_liste_controles = True
                
                # Section "Nouveau contrôle"
                if (section_id in authorized_section_ids and 
                    (('nouveau' in section_nom_lower and 'contr' in section_nom_lower) or
                     section_id == all_sections_map.get('nouveau contrôle', -1))):
                    show_nouveau_controle = True
                
                # Section "Statistiques"
                if (section_id in authorized_section_ids and 
                    (('statistiques' in section_nom_lower or 'stats' in section_nom_lower) or
                     section_id == all_sections_map.get('statistiques', -1))):
                    show_statistiques = True

                # Section "Rapports CQ" (analyse des rapports PDF machine de contrôle qualité)
                if (section_id in authorized_section_ids and 
                    (('rapport' in section_nom_lower and 'cq' in section_nom_lower) or
                     'rapports cq' in section_nom_lower or
                     section_id == all_sections_map.get('rapports cq', -1))):
                    show_rapports_cq = True
            # Si l'utilisateur a accès à la liste ou aux stats, lui afficher aussi Rapports CQ (éviter config section dédiée)
            if show_rapports_cq or show_liste_controles or show_statistiques:
                show_rapports_cq = True

        return render_template('projet10.html',
                             authorized_sections=sections_dict,
                             show_liste_controles=show_liste_controles,
                             show_nouveau_controle=show_nouveau_controle,
                             show_statistiques=show_statistiques,
                             show_rapports_cq=show_rapports_cq,
                             has_action_access=has_action_access)
    except Exception as e:
        print(f"Erreur dans projet10.index: {e}")
        import traceback
        traceback.print_exc()
        # En cas d'erreur, afficher toutes les sections pour éviter de casser l'interface
        return render_template('projet10.html',
                             authorized_sections={},
                             show_liste_controles=True,
                             show_nouveau_controle=True,
                             show_statistiques=True,
                             show_rapports_cq=True,
                             has_action_access=has_action_access)

# ---------------------------
# PAGE STATS SEPAREE
# ---------------------------
@bp.route("/stat")
def stats_page():
    """Page dédiée d'affichage des statistiques (hors onglets)."""
    return render_template("projet10stat.html")

# ---------------------------
# API CONTRÔLE QUALITÉ
# ---------------------------
@bp.route("/api/controles")
def api_controles():
    """API pour récupérer tous les contrôles qualité"""
    return jsonify(get_controles_qualite())


@bp.route("/api/controles/recalcul-manq-crebut", methods=["POST"])
def api_recalcul_manq_crebut():
    """
    Recalcule ManqAGan et CRebut pour toutes les fiches existantes.
    Réservé aux super-utilisateurs (opération de maintenance).
    """
    if not is_super_user():
        return jsonify({"error": "Accès refusé"}), 403
    n = recalcul_tous_controles_qualite_manq_gan_et_crebut()
    if n is None:
        return jsonify({"error": "Échec du recalcul"}), 500
    return jsonify({"status": "success", "mis_a_jour": n})


@bp.route("/controles/export-excel")
def export_controles_excel():
    """Export de la liste des contrôles (Excel) - vérifie ID_Action 6."""
    if not is_super_user() and not has_action_access(6):
        flash("Vous n'avez pas accès à cette action (Export Excel).", "error")
        return redirect(url_for('projet10.index'))
    try:
        import pandas as pd
        from io import BytesIO
        from datetime import datetime

        controles = get_controles_qualite() or []
        if not controles:
            return jsonify({"error": "Aucun contrôle à exporter"}), 404

        rows = []
        for c in controles:
            rows.append({
                "ID": c.get("id", ""),
                "Date": c.get("date_controle", ""),
                "N° Dossier": c.get("Numero_COMMANDES", ""),
                "Article": c.get("Article", ""),
                "Client": c.get("Client", ""),
                "Opérateur": c.get("operateur", ""),
                "Machine Impression": c.get("machine_impression", ""),
                "Opérateur M. d'impression": c.get("operateur_machine_impression", ""),
                "Machine Découpe": c.get("machine_decoupe", ""),
                "Opérateur M. de découpe": c.get("operateur_machine_decoupe", ""),
                "Rebuts": c.get("rebus", 0),
                "Total conforme (enreg.)": c.get("TotalConforme", ""),
                "Manque à Gagner": c.get("ManqAGan", ""),
                "Coût de Rebuts": c.get("CRebut", ""),
                "Taux de Rebuts (%)": c.get("TauxRebuts", ""),
                "Validation": c.get("validation_chef", ""),
            })

        df = pd.DataFrame(rows)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Controles", index=False)
            worksheet = writer.sheets["Controles"]
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(str(col)))
                col_letter = chr(65 + idx) if idx < 26 else "A" + chr(65 + idx - 26)
                worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)

        output.seek(0)
        filename = f"controles_projet10_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return Response(
            output.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ImportError:
        return jsonify({"error": "pandas et openpyxl sont requis pour l'export Excel"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/api/controle/<int:controle_id>")
def api_controle(controle_id):
    """API pour récupérer un contrôle qualité par ID"""
    controle = get_controle_qualite_by_id(controle_id)
    if controle:
        return jsonify(controle)
    return jsonify({"error": "Contrôle non trouvé"}), 404

# ---------------------------
# PAGE FICHE D'EDITION DETAILLEE
# ---------------------------
@bp.route("/fiche/<int:controle_id>")
def fiche_controle(controle_id: int):
    """Affiche une page dédiée de fiche avec tableau éditable des tolérances."""
    return render_template("projet10_fiche.html", controle_id=controle_id)

@bp.route("/api/numeros-commandes")
def api_numeros_commandes():
    """API pour récupérer les numéros de commandes disponibles"""
    return jsonify(get_numeros_commandes_disponibles())

@bp.route("/api/debug/schema")
def api_debug_schema():
    """Diagnostic: vérifier schéma et base active pour projet10."""
    return jsonify(get_projet10_schema_info())

@bp.route("/api/statistiques")
def api_statistiques():
    """API pour récupérer les statistiques globales de contrôle qualité"""
    return jsonify(get_statistiques_controle_qualite())

@bp.route("/api/statistiques/machines")
def api_statistiques_machines():
    """API pour récupérer les statistiques par machine"""
    return jsonify(get_performance_par_machine())

@bp.route("/api/statistiques/evolution")
def api_statistiques_evolution():
    """API pour récupérer l'évolution de la qualité sur 30 jours"""
    jours = request.args.get('jours', 30, type=int)
    return jsonify(get_evolution_qualite(jours))

@bp.route("/api/statistiques/dossiers-probleme")
def api_statistiques_dossiers_probleme():
    """API pour récupérer les dossiers avec rebus élevé"""
    seuil = request.args.get('seuil', 5, type=float)
    return jsonify(get_dossiers_probleme(seuil))

@bp.route("/api/operateurs")
def api_operateurs():
    """API pour récupérer la liste des opérateurs disponibles"""
    try:
        operateurs = get_operateurs()
        return jsonify(operateurs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/api/controle", methods=["POST"])
def api_create_controle():
    """API pour créer un nouveau contrôle qualité"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Données manquantes"}), 400
        
        # Validation des champs obligatoires
        required_fields = ['date_controle', 'Numero_COMMANDES', 'operateur']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Champ obligatoire manquant: {field}"}), 400
        
        controle_id = create_controle_qualite(data)
        
        if controle_id:
            return jsonify({"status": "success", "id": controle_id}), 201
        else:
            return jsonify({"error": "Erreur lors de la création - la fonction a retourné None"}), 500
    except Exception as e:
        print(f"ERREUR API CREATE CONTROLE: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@bp.route("/api/controle/<int:controle_id>", methods=["PUT"])
def api_update_controle(controle_id):
    """API pour mettre à jour un contrôle qualité"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Données manquantes"}), 400
        
        success = update_controle_qualite(controle_id, data)
        
        if success:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"error": "Erreur lors de la mise à jour - la fonction a retourné False"}), 500
    except Exception as e:
        print(f"ERREUR API UPDATE CONTROLE: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@bp.route("/api/controle/<int:controle_id>", methods=["DELETE"])
def api_delete_controle(controle_id):
    """API pour supprimer un contrôle qualité"""
    try:
        success = delete_controle_qualite(controle_id)
        if success:
            return jsonify({"status": "success", "message": "Contrôle supprimé avec succès"}), 200
        else:
            return jsonify({"error": "Contrôle non trouvé"}), 404
    except Exception as e:
        print(f"ERREUR API DELETE CONTROLE: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@bp.route("/api/statistiques/comparaison-periodes")
def api_comparaison_periodes():
    """API pour comparer deux périodes"""
    date_debut1 = request.args.get('date_debut1', type=str)
    date_fin1 = request.args.get('date_fin1', type=str)
    date_debut2 = request.args.get('date_debut2', type=str)
    date_fin2 = request.args.get('date_fin2', type=str)
    
    if not all([date_debut1, date_fin1, date_debut2, date_fin2]):
        return jsonify({"error": "Toutes les dates sont requises"}), 400
    
    return jsonify(get_comparaison_periodes(date_debut1, date_fin1, date_debut2, date_fin2))

@bp.route("/api/statistiques/comparaison-machines")
def api_comparaison_machines():
    """API pour comparer deux machines"""
    machine1 = request.args.get('machine1', type=str)
    machine2 = request.args.get('machine2', type=str)
    jours = request.args.get('jours', 30, type=int)
    
    if not machine1 or not machine2:
        return jsonify({"error": "Les deux machines sont requises"}), 400
    
    return jsonify(get_comparaison_machines(machine1, machine2, jours))

@bp.route("/api/machines-disponibles")
def api_machines_disponibles():
    """API pour récupérer la liste des machines d'impression (GP_SERVICES.ID = 1)"""
    try:
        machines = get_machines_impression()
        # Retourner seulement les noms pour la compatibilité avec le frontend
        noms_machines = [m["nom"] for m in machines]
        return jsonify(noms_machines)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/api/machines-decoupe-disponibles")
def api_machines_decoupe_disponibles():
    """API pour récupérer la liste des machines de découpe (GP_SERVICES.ID = 5)"""
    try:
        machines = get_machines_decoupe()
        # Retourner seulement les noms pour la compatibilité avec le frontend
        noms_machines = [m["nom"] for m in machines]
        return jsonify(noms_machines)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/api/traitement-data/<numero_commande>")
def api_traitement_data(numero_commande):
    """API pour récupérer les données de WEB_TRAITEMENTS pour pré-remplir le formulaire"""
    try:
        data = get_traitement_data_for_controle(numero_commande)
        if data:
            return jsonify(data)
        else:
            return jsonify({"machine_impression": None, "operateurs": []})
    except Exception as e:
        print(f"Erreur lors de la récupération des données traitement: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/rapport_cq/analyser", methods=["POST"])
def api_rapport_cq_analyser():
    """Reçoit un fichier PDF rapport CQ (machine de contrôle qualité), l'analyse et retourne summary + défauts pour graphiques."""
    try:
        fichier = request.files.get("fichier") or request.files.get("file")
        if not fichier or not fichier.filename or not fichier.filename.lower().endswith(".pdf"):
            return jsonify({"success": False, "error": "Veuillez envoyer un fichier PDF."})
        stream = io.BytesIO(fichier.read())
        from logic.rapport_cq import analyser_rapport_cq_pdf
        result = analyser_rapport_cq_pdf(stream)
        if result.get("error"):
            return jsonify({"success": False, "error": result["error"]})
        return jsonify({
            "success": True,
            "summary": result["summary"],
            "defect_types": result["defect_types"],
            "by_side": result["by_side"],
            "by_ipu": result["by_ipu"],
            "nb_lignes_defaut": result.get("nb_lignes_defaut", 0),
            "nb_sheets_uniques": result.get("nb_sheets_uniques"),
            "rapport_texte": result.get("rapport_texte", ""),
            "area_energy": result.get("area_energy"),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


def _generer_pdf_rapport_cq(data, images):
    """Génère le PDF côté serveur avec ReportLab (identique à l'affichage web)."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm, mm
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
            Image, PageBreak
        )
    except ImportError:
        return None, "reportlab non installé"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=1.5*cm, rightMargin=1.5*cm)
    elements = []
    styles = getSampleStyleSheet()

    RAPPORT_CQ_LABELS = {
        'Machine': 'Identifiant de la machine', 'BatchCode': 'Code du lot',
        'ModelNam': 'Nom du modèle', 'ModelPath': 'Chemin du modèle',
        'Total': 'Nombre total contrôlé', 'Pass': 'Conformes',
        'PassRate': 'Taux de conformité', 'Bad': 'Défectueux',
        'BadRate': 'Taux de défauts', 'Team': 'Équipe',
        'ReportTime': 'Date et heure du rapport', 'CreateDate': 'Date de création',
        'SideCount': 'Nombre de côtés', 'IPUCount': "Nombre d'unités d'inspection (IPU)"
    }
    order = ['Machine', 'BatchCode', 'ModelNam', 'Total', 'Pass', 'PassRate', 'Bad', 'BadRate',
             'Team', 'ReportTime', 'SideCount', 'IPUCount', 'ModelPath', 'CreateDate']

    summary = data.get('summary') or {}
    defect_types = data.get('defect_types') or {}
    by_side = data.get('by_side') or {}
    by_ipu = data.get('by_ipu') or {}
    area_energy = data.get('area_energy')
    nb_lignes = data.get('nb_lignes_defaut', 0)
    nb_sheets = data.get('nb_sheets_uniques')
    bad = int(summary.get('Bad') or 0)
    total_defect = sum(defect_types.values())

    title_style = ParagraphStyle('Titre', parent=styles['Heading2'], fontSize=14, spaceAfter=8)
    sub_style = ParagraphStyle('Sous', parent=styles['Normal'], fontSize=9, textColor=colors.grey, spaceAfter=4)

    elements.append(Paragraph("Résumé du rapport", title_style))
    summary_data = []
    for key in order:
        v = summary.get(key)
        if v is None or v == '':
            continue
        label = RAPPORT_CQ_LABELS.get(key, key)
        summary_data.append([key + ': ' + str(v), label])
    if summary_data:
        t = Table(summary_data, colWidths=[8*cm, 8*cm])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elements.append(t)
    elements.append(Spacer(1, 0.5*cm))

    verif_msg = "Bad = nombre d'articles rejetés ({})".format(bad)
    verif_msg += ". Les chiffres par DefectType : total {} enregistrements.".format(total_defect)
    if nb_lignes:
        verif_msg += " Lignes de défaut : {}.".format(nb_lignes)
    if nb_sheets is not None:
        verif_msg += " Articles défectueux distincts : {}.".format(nb_sheets)
    elements.append(Paragraph("<b>Vérification :</b> " + verif_msg, ParagraphStyle('Verif', fontSize=8, textColor=colors.HexColor('#0c5460'))))
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph("Indicateurs", title_style))
    if defect_types:
        total_dt = sum(defect_types.values())
        recap_data = [['Type de défaut', 'Effectif', '%']]
        for k, v in sorted(defect_types.items(), key=lambda x: -x[1]):
            pct = (v / total_dt * 100) if total_dt else 0
            recap_data.append([k, str(v), "{:.1f}".format(pct) + '%'])
        t = Table(recap_data, colWidths=[8*cm, 3*cm, 3*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.3*cm))

    if by_side:
        total_side = sum(by_side.values())
        side_data = [['Côté', 'Effectif', '%']]
        for k, v in sorted(by_side.items(), key=lambda x: -x[1]):
            pct = (v / total_side * 100) if total_side else 0
            side_data.append([k, str(v), "{:.1f}".format(pct) + '%'])
        t = Table(side_data, colWidths=[8*cm, 3*cm, 3*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.3*cm))

    if area_energy and area_energy.get('global'):
        g = area_energy['global']
        ae_lines = ['Global: Area moy. {} (max {})  Energy moy. {} (max {})'.format(
            g.get('mean_area', '-'), g.get('max_area', '-'),
            g.get('mean_energy', '-'), g.get('max_energy', '-'))]
        if area_energy.get('by_type'):
            for typ, t in area_energy['by_type'].items():
                ae_lines.append('  {}: Area moy. {}  Energy moy. {}'.format(
                    typ, t.get('mean_area', '-'), t.get('mean_energy', '-')))
        elements.append(Paragraph('<br/>'.join(ae_lines), sub_style))
        elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph("Graphiques", title_style))
    elements.append(Spacer(1, 0.3*cm))

    def _add_image(data_url, w_cm=6, h_cm=None, label=''):
        if not data_url or not isinstance(data_url, str) or 'base64,' not in data_url:
            return
        try:
            b64 = data_url.split('base64,', 1)[1]
            img_bytes = base64.b64decode(b64)
            h = (h_cm or w_cm * 0.7) * cm
            img = Image(io.BytesIO(img_bytes), width=w_cm*cm, height=h)
            if label:
                elements.append(Paragraph(label, sub_style))
            elements.append(img)
            elements.append(Spacer(1, 0.3*cm))
        except Exception:
            pass

    imgs = images or {}
    _add_image(imgs.get('passBad'), 5, 5, 'Pass / Bad — Conformes vs défectueux')
    _add_image(imgs.get('defectType'), 5, 4, 'DefectType — Répartition par type de défaut')
    elements.append(PageBreak())
    _add_image(imgs.get('side'), 5, 4, 'Side — Répartition par côté / caméra')
    _add_image(imgs.get('ipu'), 5, 4, "IPU — Répartition par unité d'inspection")

    try:
        doc.build(elements)
        return buffer.getvalue(), None
    except Exception as e:
        return None, str(e)


@bp.route("/api/rapport_cq/pdf", methods=["POST"])
def api_rapport_cq_pdf():
    """Génère le PDF côté serveur (même contenu que l'affichage web)."""
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "Données manquantes"}), 400
        data = payload.get('data') or {}
        images = payload.get('images') or {}
        pdf_bytes, err = _generer_pdf_rapport_cq(data, images)
        if err:
            return jsonify({"error": err}), 500
        batch = (data.get('summary') or {}).get('BatchCode', 'rapport')
        from datetime import date
        fn = 'analyse_CQ_{}_{}.pdf'.format(batch, date.today().isoformat())
        return Response(pdf_bytes, mimetype='application/pdf',
                       headers={'Content-Disposition': 'attachment; filename="' + fn + '"'})
    except Exception as e:
        return jsonify({"error": str(e)}), 500