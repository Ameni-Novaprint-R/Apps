"""

Routes pour le Projet 18 - Agenda semainier 2026

"""

from flask import Blueprint, render_template, make_response, request

from pathlib import Path

from logic.projet18 import get_semaines_2026, is_jour_ferie, get_nom_jour_ferie, get_mois_nom

from datetime import datetime, timedelta

from io import BytesIO



projet18_bp = Blueprint('projet18', __name__, url_prefix='/projet18')



@projet18_bp.route('/')

def index():

    """Page principale affichant l'agenda semainier"""

    semaines_all = get_semaines_2026()

    # Ajouter la semaine 53 (du lundi 28/12/2026 au dimanche 03/01/2027) si absente

    if not any(s.get('numero') == 53 for s in semaines_all):

        semaines_all.append({

            'numero': 53,

            'lundi': datetime(2026, 12, 28),

            'mardi': datetime(2026, 12, 29),

            'mercredi': datetime(2026, 12, 30),

            'jeudi': datetime(2026, 12, 31),

            'vendredi': datetime(2027, 1, 1),

            'samedi': datetime(2027, 1, 2),

            'dimanche': datetime(2027, 1, 3),

        })



    # Filtre par année (afficher uniquement les semaines contenant au moins un jour de l'année choisie)

    annee_selectionnee = request.args.get('annee', '2026')

    try:

        annee_selectionnee_int = int(annee_selectionnee)

    except ValueError:

        annee_selectionnee_int = 2026



    def semaine_concerne_annee(semaine_dict, annee):

        for key in ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']:

            date_jour = semaine_dict.get(key)

            if date_jour and date_jour.year == annee:

                return True

        return False



    semaines = [s for s in semaines_all if semaine_concerne_annee(s, annee_selectionnee_int)]



    # Années disponibles pour le sélecteur (toutes les années présentes dans les semaines)

    annees_disponibles = sorted({d.year for s in semaines_all for d in s.values() if isinstance(d, datetime)})



    return render_template(

        'projet18.html',

        semaines=semaines,

        annees_disponibles=annees_disponibles,

        annee_selectionnee=annee_selectionnee_int,

        is_jour_ferie=is_jour_ferie,

        get_nom_jour_ferie=get_nom_jour_ferie,

        get_mois_nom=get_mois_nom

    )



@projet18_bp.route('/export-pdf')

def export_pdf():

    """Exporte l'agenda semainier en PDF selon le modèle Quo Vadis"""

    import json

    import traceback

    from pathlib import Path

    

    log_path = Path(__file__).parent.parent / '.cursor' / 'debug.log'
    
    # Créer le dossier .cursor s'il n'existe pas
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:

        # Log début

        # #region agent log

        with open(log_path, 'a', encoding='utf-8') as f:

            f.write(json.dumps({

                'timestamp': datetime.now().isoformat(),

                'location': 'projet18_routes.py:export_pdf:start',

                'message': 'Debut export PDF',

                'sessionId': 'debug-session',

                'runId': 'run1',

                'hypothesisId': 'A'

            }) + '\n')

        # #endregion

        

        from reportlab.lib.pagesizes import A4, landscape

        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        from reportlab.lib.units import cm, mm

        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

        from reportlab.lib import colors

        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

        from calendar import monthrange

        

        semaines = get_semaines_2026()

        # Limiter à 52 semaines

        semaines = semaines[:52]

        

        # Log nombre de semaines

        with open(log_path, 'a', encoding='utf-8') as f:

            f.write(json.dumps({

                'timestamp': datetime.now().isoformat(),

                'location': 'projet18_routes.py:export_pdf:semaines',

                'message': 'Nombre de semaines',

                'data': {'nb_semaines': len(semaines)},

                'sessionId': 'debug-session',

                'runId': 'run1'

            }) + '\n')

        

        buffer = BytesIO()

        # Format A4 portrait

        doc = SimpleDocTemplate(

            buffer,

            pagesize=A4,  # Portrait au lieu de landscape

            rightMargin=0.5*cm,

            leftMargin=0.5*cm,

            topMargin=0.5*cm,

            bottomMargin=0.5*cm

        )

        

        styles = getSampleStyleSheet()

        

        # Styles selon le modèle Quo Vadis

        base_style = ParagraphStyle(

            'Base',

            parent=styles['Normal'],

            fontSize=9,

            textColor=colors.HexColor('#000000'),

            fontName='Helvetica',

            leading=10

        )

        

        # Style pour les noms de jours (anglais/français)

        jour_nom_style = ParagraphStyle(

            'JourNom',

            parent=base_style,

            fontSize=9,

            fontName='Helvetica',

            alignment=TA_LEFT

        )

        

        # Style pour les dates (grand, gras, noir selon l'image)

        date_style = ParagraphStyle(

            'Date',

            parent=base_style,

            fontSize=12,

            fontName='Helvetica-Bold',

            textColor=colors.HexColor('#000000'),  # Noir au lieu de bleu

            alignment=TA_RIGHT

        )

        

        # Style pour les numéros d'heures (gris clair, petit)

        # Utiliser un style qui ne coupe pas les nombres

        heure_style = ParagraphStyle(

            'Heure',

            parent=base_style,

            fontSize=7,

            textColor=colors.HexColor('#999999'),

            alignment=TA_LEFT,

            leading=14

        )

        

        # Style pour les lignes horaires (gris clair)

        ligne_horaire_style = ParagraphStyle(

            'LigneHoraire',

            parent=base_style,

            fontSize=8,

            textColor=colors.HexColor('#CCCCCC'),

            leading=10

        )

        

        # Style pour Dimanche

        dimanche_nom_style = ParagraphStyle(

            'DimancheNom',

            parent=base_style,

            fontSize=9,

            fontName='Helvetica',

            alignment=TA_LEFT

        )

        

        dimanche_date_style = ParagraphStyle(

            'DimancheDate',

            parent=base_style,

            fontSize=12,

            fontName='Helvetica-Bold',

            textColor=colors.HexColor('#000000'),  # Noir au lieu de bleu

            alignment=TA_RIGHT

        )

        

        # Style pour les lignes de notes Dimanche

        ligne_note_style = ParagraphStyle(

            'LigneNote',

            parent=base_style,

            fontSize=8,

            textColor=colors.HexColor('#CCCCCC'),

            leading=14

        )

        

        # Style pour jours fériés

        ferie_style = ParagraphStyle(

            'Ferie',

            parent=base_style,

            fontSize=9,

            textColor=colors.HexColor('#FF0000'),

            fontName='Helvetica-Bold'

        )

        

        # Style pour le mini-calendrier

        cal_header_style = ParagraphStyle(

            'CalHeader',

            parent=base_style,

            fontSize=10,

            fontName='Helvetica-Bold',

            alignment=TA_CENTER

        )

        

        cal_semaine_style = ParagraphStyle(

            'CalSemaine',

            parent=base_style,

            fontSize=7,

            textColor=colors.HexColor('#999999'),

            alignment=TA_LEFT,

            leading=10

        )

        

        cal_date_style = ParagraphStyle(

            'CalDate',

            parent=base_style,

            fontSize=8,

            alignment=TA_CENTER,

            leading=10

        )

        

        elements = []

        

        # Heures de 8h à 20h (13 lignes) -> 26 lignes de champs de saisie (2 lignes par heure)

        heures = list(range(8, 21))  # 8, 9, 10, ..., 20



        # Largeur cible des champs de saisie pour chaque jour (lundi à samedi) :

        # on part de la largeur interne du cadre des jours (~5.1cm)

        # et on réduit volontairement la largeur des lignes de 0.3cm pour

        # minimiser visuellement les 26 lignes tout en gardant l'alignement.

        # Largeur cadre jour ≈ 5.1cm -> largeur lignes = 5.1cm - 0.3cm = 4.8cm

        ligne_col_width = 4.8 * cm



        # Fonction utilitaire pour calculer automatiquement la longueur des lignes de saisie

        # en fonction de la largeur disponible, de la police et de la taille de police.

        # Cela permet de garder les 26 lignes alignées exactement sur le cadre du jour.

        def build_ligne_underscore(col_width_points, right_padding_points=2, char="_"):

            """

            Retourne une chaîne de '_' dont la largeur correspond à la largeur disponible

            dans la colonne des champs de saisie, en tenant compte du padding droit.

            """

            # Largeur disponible = largeur de la colonne - padding droit

            available_width = max(col_width_points - right_padding_points, 0)

            # Utiliser la même police et taille que ligne_horaire_style (fontSize=8)

            char_width = pdfmetrics.stringWidth(char, ligne_horaire_style.fontName, ligne_horaire_style.fontSize)

            if char_width <= 0:

                return "_" * 1

            max_chars = int(available_width / char_width)

            return char * max(1, max_chars)

        # Dictionnaire (inutile ici mais nécessaire pour éeviter NameError si du code commun l'utilise)

        page_to_mois = {}

        

        # Générer chaque semaine (2 pages par semaine)

        semaine_index = 0

        for semaine in semaines:

            # Calculer le mois de référence pour le mini-calendrier

            date_ref = semaine['jeudi'] if semaine['jeudi'] is not None else semaine['vendredi']

            if date_ref is None:

                date_ref = semaine['samedi'] if semaine['samedi'] is not None else datetime(2026, 1, 1)

            mois_ref = date_ref.month if date_ref else 1

            annee_ref = date_ref.year if date_ref else 2026

            

            # ========== PAGE 1 : LUNDI / MARDI / MERCREDI + DIMANCHE ==========

            page1_data = []

            

            # En-têtes des 3 colonnes (Lundi, Mardi, Mercredi)

            header_row = []

            jours_page1 = [

                ('lundi', 'Monday', 'Lundi'),

                ('mardi', 'Tuesday', 'Mardi'),

                ('mercredi', 'Wednesday', 'Mercredi')

            ]

            

            for jour_key, jour_en, jour_fr in jours_page1:

                date_jour = semaine[jour_key]

                if date_jour is not None:

                    # En-tête : jour à gauche, date à droite sur la même ligne (ex: "lundi 29")

                    # Format avec zéro devant si < 10 (01, 02, 03, 04)

                    date_formatee = f"{date_jour.day:02d}"

                    # Créer un tableau avec jour à gauche et date à droite

                    # #region agent log

                    with open(log_path, 'a', encoding='utf-8') as f:

                        f.write(json.dumps({

                            'timestamp': datetime.now().isoformat(),

                            'location': 'projet18_routes.py:export_pdf:before_header_table_page2',

                            'message': 'Avant creation header_table page2',

                            'data': {'jour': jour_fr, 'date': date_formatee},

                            'sessionId': 'debug-session',

                            'runId': 'run1',

                            'hypothesisId': 'A'

                        }) + '\n')

                    # #endregion

                    try:

                        header_table = Table([

                            [Paragraph(jour_fr, ParagraphStyle(

                                'HeaderJour',

                                parent=base_style,

                                fontSize=15,

                                fontName='Helvetica-Bold',

                                alignment=TA_LEFT

                            )), 

                             Paragraph(date_formatee, ParagraphStyle(

                                'HeaderDate',

                                parent=base_style,

                                fontSize=18,

                                fontName='Helvetica-Bold',

                                textColor=colors.HexColor('#004499'),  # Bleu plus foncé  # Bleu comeme dans l'image

                                alignment=TA_RIGHT

                            ))]

                        ], colWidths=[3.5*cm, 2*cm])

                        header_table.setStyle(TableStyle([

                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                            ('ALIGN', (0, 0), (0, 0), 'LEFT'),

                            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),

                            ('LEFTPADDING', (0, 0), (-1, -1), 2),

                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                            ('TOPPADDING', (0, 0), (-1, -1), 4),

                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),

                        ]))

                        # #region agent log

                        with open(log_path, 'a', encoding='utf-8') as f:

                            f.write(json.dumps({

                                'timestamp': datetime.now().isoformat(),

                                'location': 'projet18_routes.py:export_pdf:after_header_table_page2',

                                'message': 'Apres creation header_table page2',

                                'data': {'success': True},

                                'sessionId': 'debug-session',

                                'runId': 'run1',

                                'hypothesisId': 'A'

                            }) + '\n')

                        # #endregion

                    except Exception as e_header:

                        # #region agent log

                        with open(log_path, 'a', encoding='utf-8') as f:

                            f.write(json.dumps({

                                'timestamp': datetime.now().isoformat(),

                                'location': 'projet18_routes.py:export_pdf:error_header_table_page2',

                                'message': 'Erreur creation header_table page2',

                                'data': {'error': str(e_header)},

                                'sessionId': 'debug-session',

                                'runId': 'run1',

                                'hypothesisId': 'A'

                            }) + '\n')

                        # #endregion

                        raise

                    # Créer une table avec header_table (jour+date) et jour férié éventuel

                    # Utiliser une structure qui préserve la disposition horizontale de header_table

                    jour_ferie = is_jour_ferie(date_jour)

                    if jour_ferie:

                        nom_ferie = get_nom_jour_ferie(date_jour)

                        ferie_para = Paragraph(

                            f"<font color='#004499'>{nom_ferie}</font>",  # Même bleu que les dates

                            ferie_style

                        )

                        # Table avec 2 lignes : header_table en haut, jour férié en bas

                        header_cell = Table(

                            [[header_table], [ferie_para]],

                            colWidths=[5.5*cm]

                        )

                    else:

                        # Table avec seulement header_table

                        header_cell = Table(

                            [[header_table]],

                            colWidths=[5.5*cm]

                        )

                    

                    header_cell.setStyle(TableStyle([

                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                        ('LEFTPADDING', (0, 0), (-1, -1), 2),

                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                        ('TOPPADDING', (0, 0), (-1, -1), 8),

                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),

                    ]))

                    header_row.append(header_cell)

                else:

                    header_row.append(Paragraph("", base_style))

            

            page1_data.append(header_row)

            

            # 13 lignes horaires pour chaque colonne (8h-20h) -> 26 lignes de champs de saisie

            for heure in heures:

                ligne_row = []

                for jour_key, jour_en, jour_fr in jours_page1:

                    date_jour = semaine[jour_key]

                    if date_jour is not None:

                        # Ligne avec numéro d'heure à gauche et deux lignes grises identiques

                        # Créer deux lignes distinctes avec exactement le même nombre de caractères pour garantir une longueur uniforme

                        # Utiliser un nombre de caractères fixe (42) pour remplir la largeur disponible sans retour à la ligne

                        # Créer exactement 2 lignes de longueur adaptée sans retour à la ligne

                        # Utiliser un nombre de caractères réduit pour éeviter tout retour à la ligne dans le Paragraph

                        # Environ 30-32 caractères pour une largeur de 4.7cm avec fontSize=8 pour éeviter tout débordement

                        # Longueur augmentée de 0,25cm pour la version multilingue style 2 (29 -> 34 caractères)

                        ligne_underscore = "_" * 34

                        # Créer un style spécifique pour empêcher les retours à la ligne

                        ligne_horaire_style_no_wrap = ParagraphStyle(

                            'LigneHoraireNoWrap',

                            parent=ligne_horaire_style,

                            leading=12,  # Leading exactement égal à rowHeights pour garantir exactement 2 lignes sans débordement

                            spaceBefore=0,

                            spaceAfter=0

                        )

                        # Style pour le numéro d'heure aligné avec la première ligne

                        # Utiliser exactement le même leading que la ligne pour un alignement parfait

                        heure_num_style = ParagraphStyle(

                            'HeureNum',

                            parent=base_style,

                            fontSize=7,

                            textColor=colors.HexColor('#666666'),  # Même gris foncé que la 1re ligne horaire

                            alignment=TA_LEFT,

                            leading=12,  # Exactement le même leading que ligne_horaire_style_no_wrap

                            spaceBefore=0,

                            spaceAfter=0,

                            firstLineIndent=0,

                            leftIndent=0,

                            rightIndent=0

                        )

                        heure_cell = Table(

                            [

                                [Paragraph(str(heure), heure_num_style), Paragraph(ligne_underscore, ligne_horaire_style_no_wrap)],

                                [Paragraph("", base_style), Paragraph(ligne_underscore, ligne_horaire_style_no_wrap)]

                            ],

                            colWidths=[0.6*cm, 5.2*cm],  # Largeur augmentée pour les champs de saisie

                            rowHeights=[12, 12]  # Hauteur exactement égale au leading pour garantir exactement 2 lignes sans ligne supplémentaire

                        )

                        heure_cell.setStyle(TableStyle([

                            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),  # Alignement à droite pour le numéro (plus proche de la ligne)

                            ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Alignement à gauche pour les lignes

                            ('VALIGN', (0, 0), (0, 0), 'TOP'),  # Alignement en haut pour permettre le décalage avec TOPPADDING

                            ('VALIGN', (1, 0), (1, 0), 'BOTTOM'),  # Aligner la première ligne sur sa ligne de base

                            ('VALIGN', (1, 1), (1, 1), 'TOP'),  # Alignement en haut pour la deuxième ligne

                            ('LEFTPADDING', (0, 0), (0, 0), 5),  # Padding à gauche encore augmenté pour décaler davantage le numéro vers la droite

                            ('RIGHTPADDING', (0, 0), (0, 0), 0),  # Pas de padding à droite pour le numéro (très proche de la ligne)

                            ('LEFTPADDING', (1, 0), (1, -1), 0),  # Pas de padding à gauche pour les lignes (très proche du numéro)

                            ('RIGHTPADDING', (1, 0), (1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 2),  # Padding en haut légèrement augmenté pour descendre très légèrement le numéro

                            ('TOPPADDING', (1, 0), (-1, -1), 0),  # Pas de padding en haut pour les lignes

                            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),  # Pas de padding en bas

                            ('BOTTOMPADDING', (1, 1), (1, 1), 0),  # Pas de padding en bas de la dernière ligne

                        ]))

                        ligne_row.append(heure_cell)

                    else:

                        ligne_row.append(Paragraph("", base_style))

                page1_data.append(ligne_row)

            

            # Ligne vide après le dernier champ de saisie (heure 20)

            # Utiliser un style avec leading minimal pour garantir que la ligne a une hauteur

            ligne_vide_style = ParagraphStyle('LigneVide', parent=base_style, fontSize=1, leading=24, spaceBefore=0, spaceAfter=0)

            ligne_vide_apres_heures = [Paragraph(" ", ligne_vide_style)] * len(jours_page1)

            page1_data.append(ligne_vide_apres_heures)

            

            # Mini-calendrier du mois (déplacé de la page 2 vers la page 1)

            # Créer le mini-calendrier avec numéros de semaine

            _, nb_jours_mois = monthrange(annee_ref, mois_ref)

            premier_jour_mois = datetime(annee_ref, mois_ref, 1)

            jour_semaine_premier = premier_jour_mois.weekday()

            

            # Construire le mini-calendrier comeme une grille horizontale

            # Structure : une table avec plusieurs lignes

            cal_table_rows = []

            

            # Dictionnaire des noms de mois en arabe pour l'en-tête mini-calendrier (style multilingue 2)

            mois_arabe = {

                1: 'جانفي',

                2: 'فيفري',

                3: 'مارس',

                4: 'أفريل',

                5: 'ماي',

                6: 'جوان',

                7: 'جويلية',

                8: 'أوت',

                9: 'سبتمبر',

                10: 'أكتوبر',

                11: 'نوفمبر',

                12: 'ديسمبر',

            }

            mois_fr = get_mois_nom(mois_ref)

            mois_ar = mois_arabe.get(mois_ref, '')

            

            # Ligne 1 : en-tête avec mois FR à gauche et mois AR à droite (sans cadre)

            cal_table_rows.append([

                Paragraph(mois_fr, cal_header_style),

                Paragraph("", base_style), Paragraph("", base_style),

                Paragraph("", base_style),

                Paragraph("", base_style),

                Paragraph("", base_style), Paragraph("", base_style),

                Paragraph(fix_arabic_text(mois_ar), cal_header_style),

            ])

            

            # Ligne 2 : Abréviations des jours ("lu ma me je ve sa di")

            jours_abrev = ["lu", "ma", "me", "je", "ve", "sa", "di"]

            cal_jours_abrev_row = [Paragraph("", base_style)]  # Espace pour numéro semaine

            for abrev in jours_abrev:

                cal_jours_abrev_row.append(Paragraph(

                    abrev,

                    ParagraphStyle(

                        'CalJoursAbrev',

                        parent=base_style,

                        fontSize=7,

                        alignment=TA_CENTER,

                        leading=10

                    )

                ))

            cal_table_rows.append(cal_jours_abrev_row)

            

            # Créer la grille du calendrier avec numéros de semaine

            semaine_cal = []

            jours_cal = []

            semaine_num_cal = []

            

            # Trouver le numéro de semaine pour chaque jour

            def get_semaine_num_for_date(date_cible):

                for s in semaines:

                    jours_semaine_list = [s['lundi'], s['mardi'], s['mercredi'], s['jeudi'], s['vendredi'], s['samedi'], s['dimanche']]

                    for d in jours_semaine_list:

                        if d and d.date() == date_cible.date():

                            return s['numero']

                return None

            

            # Calculer correctement le positionnement du premier jour du mois

            # Le premier jour doit être à la position jour_semaine_premier (0=lundi, 3=jeudi, etc.)

            

            # Ajouter les dates de décembre avant janvier (si mois_ref == 1)

            if mois_ref == 1:

                mois_precedent = 12

                annee_precedente = annee_ref - 1

                _, nb_jours_decembre = monthrange(annee_precedente, mois_precedent)

                

                # Stocker les dates complètes pour vérifier les jours fériés

                dates_cal = []  # Liste de tuples (jour_str, date_complete) ou None pour les espaces

                

                # Ajouter les 3 derniers jours de décembre (29, 30, 31)

                for jour_dec in range(29, 32):

                    date_dec = datetime(annee_precedente, mois_precedent, jour_dec)

                    semaine_num = get_semaine_num_for_date(date_dec)

                    semaine_num_cal.append(str(semaine_num) if semaine_num else "")

                    jour_str = f"{jour_dec:02d}"

                    jours_cal.append(jour_str)

                    dates_cal.append((jour_str, date_dec))  # Stocker la date complète

                

                # Après avoir ajouté 29, 30, 31, on a 3 éléments dans jours_cal

                # Le 29 décembre 2025 est un lundi (weekday=0), donc :

                # - Position 0: 29 (lundi)

                # - Position 1: 30 (mardi)  

                # - Position 2: 31 (mercredi)

                # Le 1er janvier 2026 est un jeudi (weekday=3), donc il doit être à la position 3

                # Comeme on a déjà 3 éléments, la prochaine position est 3, ce qui est correct

                # Donc pas besoin d'espaces supplémentaires

                nb_espaces_a_ajouter = 0

                # #region agent log

                with open(log_path, 'a', encoding='utf-8') as f:

                    f.write(json.dumps({

                        'timestamp': datetime.now().isoformat(),

                        'location': 'projet18_routes.py:export_pdf:cal_decembre',

                        'message': 'Jours decembre ajoutes',

                        'data': {

                            'nb_jours_decembre': len(jours_cal),

                            'jour_semaine_premier': jour_semaine_premier,

                            'nb_espaces': nb_espaces_a_ajouter,

                            'jours_cal': jours_cal,

                            'position_apres_decembre': len(jours_cal)

                        },

                        'sessionId': 'debug-session',

                        'runId': 'run1',

                        'hypothesisId': 'F'

                    }) + '\n')

                # #endregion

            else:

                # Pour les autres mois, ajouter simplement les espaces nécessaires

                nb_espaces_a_ajouter = jour_semaine_premier

                # Stocker les dates complètes pour vérifier les jours fériés

                dates_cal = []  # Liste de tuples (jour_str, date_complete) ou None pour les espaces

            

            # Ajouter les espaces nécessaires

            for _ in range(nb_espaces_a_ajouter):

                if len(jours_cal) < 7:  # Ne pas dépasser 7 jours par semaine

                    semaine_num_cal.append("")

                    jours_cal.append("")

                    dates_cal.append(None)  # Pas de date pour les espaces

            

            # Ajouter les jours du mois courant avec numéro de semaine

            jour_courant = 1

            while jour_courant <= nb_jours_mois:

                jour_date = datetime(annee_ref, mois_ref, jour_courant)

                semaine_num = get_semaine_num_for_date(jour_date)

                

                semaine_num_cal.append(str(semaine_num) if semaine_num else "")

                # Format avec zéro devant si < 10

                jour_str = f"{jour_courant:02d}"

                jours_cal.append(jour_str)

                dates_cal.append((jour_str, jour_date))  # Stocker la date complète

                

                jour_courant += 1

                

                if len(jours_cal) == 7:

                    # Trouver le numéro de semaine pour cette ligne (prendre le premier non vide)

                    semaine_num_ligne = None

                    for sn in semaine_num_cal:

                        if sn:

                            semaine_num_ligne = sn

                            break

                    

                    # Créer une ligne avec numéro de semaine à gauche et dates à droite

                    cal_row_cells = []

                    # Numéro de semaine à gauche (petit, gris)

                    cal_row_cells.append(Paragraph(

                        semaine_num_ligne if semaine_num_ligne else "",

                        cal_semaine_style

                    ))

                    

                    # Dates à droite (7 colonnes)

                    for idx, jour_str in enumerate(jours_cal):

                        # Vérifier si c'est un jour férié (uniquement pour les jours du mois courant)

                        if idx < len(dates_cal) and dates_cal[idx] is not None:

                            _, date_complete = dates_cal[idx]

                            if is_jour_ferie(date_complete):

                                # Highlight bleu clair pour les jours fériés uniquement

                                cal_row_cells.append(Paragraph(

                                    jour_str,

                                    ParagraphStyle(

                                        'CalDateHighlight',

                                        parent=base_style,

                                        fontSize=8,

                                        textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                                        backColor=colors.HexColor('#E6F3FF'),  # Bleu clair

                                        alignment=TA_CENTER,

                                        leading=10

                                    )

                                ))

                            else:

                                cal_row_cells.append(Paragraph(jour_str, cal_date_style))

                        else:

                            # Espace vide ou jour d'un autre mois

                            cal_row_cells.append(Paragraph(jour_str, cal_date_style))

                    

                    # Ajouter la ligne directement à cal_table_rows

                    cal_table_rows.append(cal_row_cells)

                    

                    semaine_cal = []

                    jours_cal = []

                    semaine_num_cal = []

                    dates_cal = []

            

            # Compléter la dernière semaine avec le début de février (si nécessaire)

            if len(jours_cal) > 0 and len(jours_cal) < 7:

                mois_suivant = mois_ref + 1 if mois_ref < 12 else 1

                annee_suivante = annee_ref if mois_ref < 12 else annee_ref + 1

                jour_fevrier = 1

                while len(jours_cal) < 7:

                    date_fev = datetime(annee_suivante, mois_suivant, jour_fevrier)

                    semaine_num = get_semaine_num_for_date(date_fev)

                    semaine_num_cal.append(str(semaine_num) if semaine_num else "")

                    jours_cal.append(f"{jour_fevrier:02d}")

                    jour_fevrier += 1

                

                # Créer la dernière ligne avec numéro de semaine à gauche

                # Trouver le numéro de semaine pour cette ligne

                semaine_num_ligne = None

                for sn in semaine_num_cal:

                    if sn:

                        semaine_num_ligne = sn

                        break

                

                cal_row_cells = []

                # Numéro de semaine à gauche

                cal_row_cells.append(Paragraph(

                    semaine_num_ligne if semaine_num_ligne else "",

                    cal_semaine_style

                ))

                

                # Dates à droite

                for jour_str in jours_cal:

                    cal_row_cells.append(Paragraph(jour_str, cal_date_style))

                

                cal_table_rows.append(cal_row_cells)

            

            # Limiter à 6 lignes de dates (en plus de l'en-tête et des abréviations)

            # Total : 1 en-tête + 1 abréviations + 6 lignes dates = 8 lignes max

            if len(cal_table_rows) > 8:

                cal_table_rows = cal_table_rows[:8]

            

            # Créer le tableau du mini-calendrier comeme une grille horizontale

            # #region agent log

            with open(log_path, 'a', encoding='utf-8') as f:

                f.write(json.dumps({

                    'timestamp': datetime.now().isoformat(),

                    'location': 'projet18_routes.py:export_pdf:before_cal_table',

                    'message': 'Avant creation cal_table',

                    'data': {'nb_rows': len(cal_table_rows)},

                    'sessionId': 'debug-session',

                    'runId': 'run1',

                    'hypothesisId': 'D'

                }) + '\n')

            # #endregion

            try:

                cal_table = Table(

                    cal_table_rows,

                    colWidths=[0.6*cm] + [0.7*cm] * 7  # Numéro semaine (ajusté) + 7 dates = 8 colonnes

                )

                cal_table.setStyle(TableStyle([

                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # En-tête mois centré sur toutes les colonnes

                    ('SPAN', (0, 0), (-1, 0)),  # Fusionner les colonnes pour l'en-tête

                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Numéros de semaine à gauche

                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Dates et abréviations centrées

                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                    ('LEFTPADDING', (0, 0), (-1, -1), 2),

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (-1, -1), 2),

                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),

                    # Cadre supprimé - pas de GRID

                ]))

                # #region agent log

                with open(log_path, 'a', encoding='utf-8') as f:

                    f.write(json.dumps({

                        'timestamp': datetime.now().isoformat(),

                        'location': 'projet18_routes.py:export_pdf:after_cal_table',

                        'message': 'Apres creation cal_table',

                        'data': {'success': True},

                        'sessionId': 'debug-session',

                        'runId': 'run1',

                        'hypothesisId': 'D'

                    }) + '\n')

                # #endregion

            except Exception as e_cal_table:

                # #region agent log

                with open(log_path, 'a', encoding='utf-8') as f:

                    f.write(json.dumps({

                        'timestamp': datetime.now().isoformat(),

                        'location': 'projet18_routes.py:export_pdf:error_cal_table',

                        'message': 'Erreur creation cal_table',

                        'data': {'error': str(e_cal_table), 'nb_rows': len(cal_table_rows)},

                        'sessionId': 'debug-session',

                        'runId': 'run1',

                        'hypothesisId': 'D'

                    }) + '\n')

                # #endregion

                raise

            

            # Ajouter la ligne avec mini-calendrier à gauche

            cal_row = [

                cal_table,  # Mini-calendrier colonne 1 (à gauche)

                Paragraph("", base_style),  # Espace vide colonne 2

                Paragraph("", base_style)  # Espace vide colonne 3

            ]

            page1_data.append(cal_row)

            

            # Trouver l'index de la ligne du mini-calendrier (dernière ligne)

            cal_row_index = len(page1_data) - 1

            # Trouver l'index de la ligne vide après les heures (juste avant le calendrier)

            ligne_vide_apres_heures_index = cal_row_index - 1

            

            # Créer le tableau pour la page 1 (format portrait - colonnes plus étroites)

            page1_table = Table(page1_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])

            page1_table.setStyle(TableStyle([

                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),  # Bordures grises fines

                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#CCCCCC')),  # Ligne sous les en-têtes

                # Supprimer la ligne verticale entre Mardi (colonne 1) et Mercredi (colonne 2) uniquement pour la ligne du mini-calendrier

                ('LINEAFTER', (1, cal_row_index), (1, cal_row_index), 0, colors.white),

                # Centrer le calendrier dans sa cellule (cadre)

                ('ALIGN', (0, cal_row_index), (0, cal_row_index), 'CENTER'),

                ('VALIGN', (0, cal_row_index), (0, cal_row_index), 'MIDDLE'),

                ('LEFTPADDING', (0, 0), (-1, -1), 0),

                ('RIGHTPADDING', (0, 0), (-1, -1), 0),

                ('TOPPADDING', (0, 0), (-1, -1), 0),

                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),

            ]))

            

            elements.append(page1_table)

            elements.append(PageBreak())

            

            # ========== PAGE 2 : JEUDI / VENDREDI / SAMEDI + DIMANCHE ==========

            page2_data = []

            

            # En-têtes des 3 colonnes (Jeudi, Vendredi, Samedi)

            header_row2 = []

            jours_page2 = [

                ('jeudi', 'Thursday', 'Jeudi'),

                ('vendredi', 'Friday', 'Vendredi'),

                ('samedi', 'Saturday', 'Samedi')

            ]

            

            for jour_key, jour_en, jour_fr in jours_page2:

                date_jour = semaine[jour_key]

                if date_jour is not None:

                    # En-tête : jour à gauche, date à droite sur la même ligne (ex: "jeudi 01")

                    # Format avec zéro devant si < 10 (01, 02, 03, 04)

                    date_formatee = f"{date_jour.day:02d}"

                    # Créer un tableau avec jour à gauche et date à droite

                    # #region agent log

                    with open(log_path, 'a', encoding='utf-8') as f:

                        f.write(json.dumps({

                            'timestamp': datetime.now().isoformat(),

                            'location': 'projet18_routes.py:export_pdf:before_header_table_page2',

                            'message': 'Avant creation header_table page2',

                            'data': {'jour': jour_fr, 'date': date_formatee},

                            'sessionId': 'debug-session',

                            'runId': 'run1',

                            'hypothesisId': 'A'

                        }) + '\n')

                    # #endregion

                    try:

                        header_table = Table([

                            [Paragraph(jour_fr, ParagraphStyle(

                                'HeaderJour',

                                parent=base_style,

                                fontSize=15,

                                fontName='Helvetica-Bold',

                                alignment=TA_LEFT

                            )), 

                             Paragraph(date_formatee, ParagraphStyle(

                                'HeaderDate',

                                parent=base_style,

                                fontSize=18,

                                fontName='Helvetica-Bold',

                                textColor=colors.HexColor('#004499'),  # Bleu plus foncé  # Bleu comeme dans l'image

                                alignment=TA_RIGHT

                            ))]

                        ], colWidths=[3.5*cm, 2*cm])

                        header_table.setStyle(TableStyle([

                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                            ('ALIGN', (0, 0), (0, 0), 'LEFT'),

                            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),

                            ('LEFTPADDING', (0, 0), (-1, -1), 2),

                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                            ('TOPPADDING', (0, 0), (-1, -1), 4),

                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),

                        ]))

                        # #region agent log

                        with open(log_path, 'a', encoding='utf-8') as f:

                            f.write(json.dumps({

                                'timestamp': datetime.now().isoformat(),

                                'location': 'projet18_routes.py:export_pdf:after_header_table_page2',

                                'message': 'Apres creation header_table page2',

                                'data': {'success': True},

                                'sessionId': 'debug-session',

                                'runId': 'run1',

                                'hypothesisId': 'A'

                            }) + '\n')

                        # #endregion

                    except Exception as e_header:

                        # #region agent log

                        with open(log_path, 'a', encoding='utf-8') as f:

                            f.write(json.dumps({

                                'timestamp': datetime.now().isoformat(),

                                'location': 'projet18_routes.py:export_pdf:error_header_table_page2',

                                'message': 'Erreur creation header_table page2',

                                'data': {'error': str(e_header)},

                                'sessionId': 'debug-session',

                                'runId': 'run1',

                                'hypothesisId': 'A'

                            }) + '\n')

                        # #endregion

                        raise

                    # Créer une table avec header_table (jour+date) et jour férié éventuel

                    # Utiliser une structure qui préserve la disposition horizontale de header_table

                    jour_ferie = is_jour_ferie(date_jour)

                    if jour_ferie:

                        nom_ferie = get_nom_jour_ferie(date_jour)

                        ferie_para = Paragraph(

                            f"<font color='#004499'>{nom_ferie}</font>",  # Même bleu que les dates

                            ferie_style

                        )

                        # Table avec 2 lignes : header_table en haut, jour férié en bas

                        header_cell = Table(

                            [[header_table], [ferie_para]],

                            colWidths=[5.5*cm]

                        )

                    else:

                        # Table avec seulement header_table

                        header_cell = Table(

                            [[header_table]],

                            colWidths=[5.5*cm]

                        )

                    

                    header_cell.setStyle(TableStyle([

                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                        ('LEFTPADDING', (0, 0), (-1, -1), 2),

                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                        ('TOPPADDING', (0, 0), (-1, -1), 8),

                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),

                    ]))

                    header_row2.append(header_cell)

                else:

                    header_row2.append(Paragraph("", base_style))

            

            page2_data.append(header_row2)

            

            # 13 lignes horaires pour chaque colonne (8h-20h) -> 26 lignes de champs de saisie

            for heure in heures:

                ligne_row = []

                for jour_key, jour_en, jour_fr in jours_page2:

                    date_jour = semaine[jour_key]

                    if date_jour is not None:

                        # Ligne avec numéro d'heure à gauche et deux lignes grises identiques

                        # Créer deux lignes distinctes avec exactement le même nombre de caractères pour garantir une longueur uniforme

                        # Utiliser un nombre de caractères fixe (42) pour remplir la largeur disponible sans retour à la ligne

                        # Créer exactement 2 lignes de longueur adaptée sans retour à la ligne

                        # Utiliser un nombre de caractères réduit pour éeviter tout retour à la ligne dans le Paragraph

                        # Environ 30-32 caractères pour une largeur de 4.7cm avec fontSize=8 pour éeviter tout débordement

                        # Longueur augmentée de 0,25cm pour la version multilingue style 2 (29 -> 34 caractères)

                        ligne_underscore = "_" * 34

                        # Créer un style spécifique pour empêcher les retours à la ligne

                        ligne_horaire_style_no_wrap = ParagraphStyle(

                            'LigneHoraireNoWrap',

                            parent=ligne_horaire_style,

                            leading=12,  # Leading exactement égal à rowHeights pour garantir exactement 2 lignes sans débordement

                            spaceBefore=0,

                            spaceAfter=0

                        )

                        # Style pour le numéro d'heure aligné avec la première ligne

                        # Utiliser exactement le même leading que la ligne pour un alignement parfait

                        heure_num_style = ParagraphStyle(

                            'HeureNum',

                            parent=base_style,

                            fontSize=7,

                            textColor=colors.HexColor('#666666'),  # Même gris foncé que la 1re ligne horaire

                            alignment=TA_LEFT,

                            leading=12,  # Exactement le même leading que ligne_horaire_style_no_wrap

                            spaceBefore=0,

                            spaceAfter=0,

                            firstLineIndent=0,

                            leftIndent=0,

                            rightIndent=0

                        )

                        heure_cell = Table(

                            [

                                [Paragraph(str(heure), heure_num_style), Paragraph(ligne_underscore, ligne_horaire_style_no_wrap)],

                                [Paragraph("", base_style), Paragraph(ligne_underscore, ligne_horaire_style_no_wrap)]

                            ],

                            colWidths=[0.6*cm, 5.2*cm],  # Largeur augmentée pour les champs de saisie

                            rowHeights=[12, 12]  # Hauteur exactement égale au leading pour garantir exactement 2 lignes sans ligne supplémentaire

                        )

                        heure_cell.setStyle(TableStyle([

                            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),  # Alignement à droite pour le numéro (plus proche de la ligne)

                            ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Alignement à gauche pour les lignes

                            ('VALIGN', (0, 0), (0, 0), 'TOP'),  # Alignement en haut pour permettre le décalage avec TOPPADDING

                            ('VALIGN', (1, 0), (1, 0), 'BOTTOM'),  # Aligner la première ligne sur sa ligne de base

                            ('VALIGN', (1, 1), (1, 1), 'TOP'),  # Alignement en haut pour la deuxième ligne

                            ('LEFTPADDING', (0, 0), (0, 0), 5),  # Padding à gauche encore augmenté pour décaler davantage le numéro vers la droite

                            ('RIGHTPADDING', (0, 0), (0, 0), 0),  # Pas de padding à droite pour le numéro (très proche de la ligne)

                            ('LEFTPADDING', (1, 0), (1, -1), 0),  # Pas de padding à gauche pour les lignes (très proche du numéro)

                            ('RIGHTPADDING', (1, 0), (1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 2),  # Padding en haut légèrement augmenté pour descendre très légèrement le numéro

                            ('TOPPADDING', (1, 0), (-1, -1), 0),  # Pas de padding en haut pour les lignes

                            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),  # Pas de padding en bas

                            ('BOTTOMPADDING', (1, 1), (1, 1), 0),  # Pas de padding en bas de la dernière ligne

                        ]))

                        ligne_row.append(heure_cell)

                    else:

                        ligne_row.append(Paragraph("", base_style))

                page2_data.append(ligne_row)

            

            # Ligne vide après le dernier champ de saisie (heure 20)

            # Utiliser un espace avec un style ayant un leading minimal pour garantir que la ligne a une hauteur

            ligne_vide_style = ParagraphStyle('LigneVide', parent=base_style, fontSize=1, leading=24, spaceBefore=0, spaceAfter=0)

            ligne_vide_apres_heures = [Paragraph(" ", ligne_vide_style)] * len(jours_page2)

            page2_data.append(ligne_vide_apres_heures)

            

            # Zone Dimanche : en-tête dans colonne 1, lignes grises dans colonnes 2 et 3 (déplacé de la page 1 vers la page 2)

            dimanche_row = []

            if semaine['dimanche'] is not None:

                jour_ferie = is_jour_ferie(semaine['dimanche'])

                nom_ferie = get_nom_jour_ferie(semaine['dimanche']) if jour_ferie else ""

                

                # Contenu Dimanche : jour + date sur une ligne (ex: "Dimanche 04")

                # Format avec zéro devant si < 10

                date_dimanche_formatee = f"{semaine['dimanche'].day:02d}"

                # Créer un tableau avec jour à gauche et date à droite

                dimanche_header_table = Table([

                    [Paragraph("Dimanche", ParagraphStyle(

                        'DimancheJour',

                        parent=base_style,

                        fontSize=15,

                        fontName='Helvetica-Bold',

                        alignment=TA_LEFT

                    )), 

                     Paragraph(date_dimanche_formatee, ParagraphStyle(

                        'DimancheDate',

                        parent=base_style,

                        fontSize=18,

                        fontName='Helvetica-Bold',

                        textColor=colors.HexColor('#004499'),  # Bleu plus foncé  # Bleu comeme dans l'image

                        alignment=TA_RIGHT

                    ))]

                ], colWidths=[3.5*cm, 2*cm])

                dimanche_header_table.setStyle(TableStyle([

                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),

                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),

                    ('LEFTPADDING', (0, 0), (-1, -1), 2),

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (-1, -1), 4),

                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),

                ]))

                

                # Colonne 1 : En-tête Dimanche + date (et jour férié si applicable)

                dimanche_header_rows = [[dimanche_header_table]]

                if jour_ferie:

                    dimanche_header_rows.append([Paragraph(

                        f"<b><font color='#FF0000'>{nom_ferie}</font></b>",

                        ferie_style

                    )])

                

                dimanche_header_cell = Table(

                    dimanche_header_rows,

                    colWidths=[5.5*cm]

                )

                dimanche_header_cell.setStyle(TableStyle([

                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                    ('LEFTPADDING', (0, 0), (-1, -1), 2),

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (0, 0), 12),  # Padding pour l'en-tête Dimanche

                    ('BOTTOMPADDING', (0, 0), (0, 0), 12),

                    ('TOPPADDING', (1, 0), (-1, -1), 2),  # Padding pour le jour férié

                    ('BOTTOMPADDING', (1, 0), (-1, -1), 2),

                ]))

                

                # Colonnes 2 et 3 : 5 lignes grises (fusionnées sur 2 colonnes)

                dimanche_notes_rows = []

                for i in range(5):

                    dimanche_notes_rows.append([Paragraph("_" * 72, ligne_note_style)])  # Augmenter de 12 caractères pour ajouter 1cm de largeur

                

                dimanche_notes_cell = Table(

                    dimanche_notes_rows,

                    colWidths=[12*cm]  # Largeur augmentée de 1cm (11cm + 1cm = 12cm)

                )

                dimanche_notes_cell.setStyle(TableStyle([

                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                    ('LEFTPADDING', (0, 0), (-1, -1), 15 + 0.1*cm),  # Décaler les lignes vers la droite de 0,1 cm

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (-1, -1), 2),

                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),

                ]))

                

                # Structure finale : colonne 0 = en-tête, colonnes 1-2 = lignes grises (fusionnées)

                # Le contenu doit être dans la première colonne du SPAN (colonne 1)

                dimanche_row.append(dimanche_header_cell)  # Colonne 0 (Jeudi)

                dimanche_row.append(dimanche_notes_cell)  # Colonne 1 (Vendredi) - sera fusionnée avec colonne 2

                dimanche_row.append(Paragraph("", base_style))  # Colonne 2 (Samedi) - sera fusionnée avec colonne 1

            else:

                dimanche_row = [Paragraph("", base_style)] * 3

            

            page2_data.append(dimanche_row)

            

            # Créer le tableau pour la page 2 (format portrait - colonnes plus étroites)

            page2_table = Table(page2_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])

            # Trouver l'index de la ligne Dimanche (dernière ligne)

            dimanche_row_index = len(page2_data) - 1

            page2_table.setStyle(TableStyle([

                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),  # Bordures grises fines

                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#CCCCCC')),  # Ligne sous les en-têtes

                # Fusionner les colonnes 1 et 2 (Vendredi et Samedi) pour les lignes grises du Dimanche

                ('SPAN', (1, dimanche_row_index), (2, dimanche_row_index)),

                ('LEFTPADDING', (0, 0), (-1, -1), 0),

                ('RIGHTPADDING', (0, 0), (-1, -1), 0),

                ('TOPPADDING', (0, 0), (-1, -1), 0),

                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),

            ]))

            

            elements.append(page2_table)

            

            # Log pour debug

            with open(log_path, 'a', encoding='utf-8') as f:

                f.write(json.dumps({

                    'timestamp': datetime.now().isoformat(),

                    'location': 'projet18_routes.py:export_pdf:semaine',

                    'message': 'Semaine generee',

                    'data': {

                        'semaine_num': semaine['numero'],

                        'has_lundi': semaine['lundi'] is not None,

                        'has_jeudi': semaine['jeudi'] is not None,

                        'has_dimanche': semaine['dimanche'] is not None

                    },

                    'sessionId': 'debug-session',

                    'runId': 'run1'

                }) + '\n')

            

            # Saut de page entre les semaines (sauf pour la dernière)

            if semaine != semaines[-1]:

                elements.append(PageBreak())

        

        # Générer le PDF

        with open(log_path, 'a', encoding='utf-8') as f:

            f.write(json.dumps({

                'timestamp': datetime.now().isoformat(),

                'location': 'projet18_routes.py:export_pdf:before_build',

                'message': 'Avant doc.build',

                'data': {'nb_elements': len(elements)},

                'sessionId': 'debug-session',

                'runId': 'run1'

            }) + '\n')

        

        doc.build(elements)

        buffer.seek(0)

        

        with open(log_path, 'a', encoding='utf-8') as f:

            f.write(json.dumps({

                'timestamp': datetime.now().isoformat(),

                'location': 'projet18_routes.py:export_pdf:after_build',

                'message': 'Apres doc.build',

                'data': {'buffer_size': len(buffer.getvalue())},

                'sessionId': 'debug-session',

                'runId': 'run1'

            }) + '\n')

        

        response = make_response(buffer.read())

        response.headers['Content-Type'] = 'application/pdf'

        response.headers['Content-Disposition'] = f'attachment; filename=agenda_semainier_2026_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'

        

        with open(log_path, 'a', encoding='utf-8') as f:

            f.write(json.dumps({

                'timestamp': datetime.now().isoformat(),

                'location': 'projet18_routes.py:export_pdf:success',

                'message': 'PDF genere avec succes',

                'sessionId': 'debug-session',

                'runId': 'run1'

            }) + '\n')

        

        return response

    

    except Exception as e:

        error_msg = str(e)

        error_trace = traceback.format_exc()

        

        # #region agent log

        with open(log_path, 'a', encoding='utf-8') as f:

            f.write(json.dumps({

                'timestamp': datetime.now().isoformat(),

                'location': 'projet18_routes.py:export_pdf:error',

                'message': 'Erreur generation PDF',

                'data': {'error': error_msg, 'traceback': error_trace},

                'sessionId': 'debug-session',

                'runId': 'run1',

                'hypothesisId': 'E'

            }) + '\n')

        # #endregion

        

        raise



@projet18_bp.route('/export-pdf-multilang')

def export_pdf_multilang():

    """Exporte l'agenda semainier en PDF version multilingue (arabe et anglais) - À développer séparément"""

    # NOTE: Cette fonction est une copie indépendante de export_pdf()

    # Elle peut être modifiée pour la version multilingue sans affecter export_pdf()

    # ⚠️ IMPORTANT: Cette fonction NE DOIT PAS être modifiée - utiliser export_pdf_multilang_style2() pour les modifications

    # Pour l'instant, elle génère le même PDF que export_pdf() mais avec un nom de fichier différent

    import json

    import traceback

    from pathlib import Path

    

    log_path = Path(__file__).parent.parent / '.cursor' / 'debug.log'
    
    # Créer le dossier .cursor s'il n'existe pas
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:

        # Log début

        # #region agent log

        with open(log_path, 'a', encoding='utf-8') as f:

            f.write(json.dumps({

                'timestamp': datetime.now().isoformat(),

                'location': 'projet18_routes.py:export_pdf_multilang:start',

                'message': 'Debut export PDF multilingue',

                'sessionId': 'debug-session',

                'runId': 'run1',

                'hypothesisId': 'A'

            }) + '\n')

        # #endregion

        

        from reportlab.lib.pagesizes import A4, landscape

        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        from reportlab.lib.units import cm, mm

        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

        from reportlab.lib import colors

        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

        from calendar import monthrange

        from reportlab.pdfbase import pdfmetrics

        from reportlab.pdfbase.ttfonts import TTFont

        import os

        

        # Fonction pour corriger l'ordre du texte arabe (RTL) en préservant les connexions entre lettres

        def fix_arabic_text(text):

            """Corrige l'ordre du texte arabe pour l'affichage RTL dans ReportLab en préservant les connexions"""

            if not text:

                return text

            

            # #region agent log

            try:

                with open(log_path, 'a', encoding='utf-8') as f:

                    f.write(json.dumps({

                        'timestamp': datetime.now().isoformat(),

                        'location': 'projet18_routes.py:fix_arabic_text:start',

                        'message': 'Correction texte arabe',

                        'data': {'text_original': text, 'text_length': len(text)},

                        'sessionId': 'debug-session',

                        'runId': 'run1',

                        'hypothesisId': 'A'

                    }) + '\n')

            except:

                pass

            # #endregion

            

            try:

                # Solution correcte pour ReportLab : reshaper puis inverser pour l'ordre visuel

                # ReportLab affiche le texte dans l'ordre logique (de gauche à droite)

                # Pour l'arabe, il faut inverser l'ordre après le reshaping pour obtenir l'ordre visuel correct

                import arabic_reshaper

                

                # Étape 1: Reshaper pour obtenir les bonnes formes contextuelles (lettres attachées)

                reshaper = arabic_reshaper.ArabicReshaper()

                reshaped_text = reshaper.reshape(text)

                

                # Étape 2: Inverser l'ordre des caractères pour l'affichage visuel RTL

                # ReportLab affiche de gauche à droite, donc on inverse pour obtenir l'ordre RTL correct

                visual_text = reshaped_text[::-1]

                

                # Retourner le texte visual sans marqueur RTL (qui cause des carrés)

                result = visual_text

                

                # #region agent log

                try:

                    with open(log_path, 'a', encoding='utf-8') as f:

                        f.write(json.dumps({

                            'timestamp': datetime.now().isoformat(),

                            'location': 'projet18_routes.py:fix_arabic_text:success',

                            'message': 'Utilise reshape puis inversion (ordre visuel correct pour ReportLab)',

                            'data': {

                                'text_original': text,

                                'text_reshaped': reshaped_text,

                                'text_visual': visual_text,

                                'text_result': result,

                                'length_original': len(text),

                                'length_reshaped': len(reshaped_text),

                                'length_visual': len(visual_text),

                                'length_result': len(result)

                            },

                            'sessionId': 'debug-session',

                            'runId': 'run1',

                            'hypothesisId': 'A'

                        }) + '\n')

                except:

                    pass

                # #endregion

                return result

            except ImportError as e:

                # #region agent log

                try:

                    with open(log_path, 'a', encoding='utf-8') as f:

                        f.write(json.dumps({

                            'timestamp': datetime.now().isoformat(),

                            'location': 'projet18_routes.py:fix_arabic_text:import_error',

                            'message': 'Erreur import bidi/reshaper',

                            'data': {'error': str(e)},

                            'sessionId': 'debug-session',

                            'runId': 'run1',

                            'hypothesisId': 'B'

                        }) + '\n')

                except:

                    pass

                # #endregion

                # Si arabic_reshaper n'est pas disponible, utiliser le texte original

                # La police TTF devrait gérer les formes contextuelles de base

                pass

                

            # Si arabic_reshaper n'est pas disponible, utiliser le texte original sans modification

            # La police TTF devrait gérer les formes contextuelles de base

            has_arabic = any('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F' or 

                            '\u08A0' <= c <= '\u08FF' or '\uFB50' <= c <= '\uFDFF' or 

                            '\uFE70' <= c <= '\uFEFF' for c in text)

            if has_arabic:

                # Retourner le texte original sans marqueur RTL (qui cause des carrés)

                # La police TTF (Arial Unicode MS, Tahoma, etc.) devrait gérer les formes contextuelles

                result = text

                # #region agent log

                try:

                    with open(log_path, 'a', encoding='utf-8') as f:

                        f.write(json.dumps({

                            'timestamp': datetime.now().isoformat(),

                            'location': 'projet18_routes.py:fix_arabic_text:fallback',

                            'message': 'Utilise texte original (arabic_reshaper non disponible)',

                            'data': {'text_result': result, 'has_arabic': has_arabic},

                            'sessionId': 'debug-session',

                            'runId': 'run1',

                            'hypothesisId': 'B'

                        }) + '\n')

                except:

                    pass

                # #endregion

                return result

            # #region agent log

            try:

                with open(log_path, 'a', encoding='utf-8') as f:

                    f.write(json.dumps({

                        'timestamp': datetime.now().isoformat(),

                        'location': 'projet18_routes.py:fix_arabic_text:no_arabic',

                        'message': 'Pas de caractères arabes',

                        'data': {'text': text},

                        'sessionId': 'debug-session',

                        'runId': 'run1',

                        'hypothesisId': 'C'

                    }) + '\n')

            except:

                pass

            # #endregion

            return text

        

        # Charger la police Square721 BT (Regular et Bold) pour le texte latin/chiffres

        # ET une police qui supporte l'arabe pour le texte arabe

        square721_font_name = 'Helvetica'  # Par défaut en cas d'erreur

        square721_bold_font_name = 'Helvetica-Bold'  # Par défaut en cas d'erreur

        arabic_font_name = 'Helvetica'  # Par défaut (ne supporte pas l'arabe)

        

        # D'abord charger une police qui supporte l'arabe (priorité)

        try:

            # Essayer Arial Unicode MS (souvent disponible sur Windows et supporte l'arabe)

            arial_unicode_paths = [

                'C:/Windows/Fonts/ARIALUNI.TTF',

                'C:/Windows/Fonts/arialuni.ttf',

                'C:/Windows/Fonts/ARIALUNI.OTF',

            ]

            for path in arial_unicode_paths:

                if os.path.exists(path):

                    try:

                        pdfmetrics.registerFont(TTFont('ArialUnicodeMS', path))

                        arabic_font_name = 'ArialUnicodeMS'

                        break

                    except Exception as e:

                        try:

                            with open(log_path, 'a', encoding='utf-8') as f:

                                f.write(json.dumps({

                                    'timestamp': datetime.now().isoformat(),

                                    'location': 'projet18_routes.py:export_pdf_multilang:arial_unicode_error',

                                    'message': f'Erreur chargement Arial Unicode: {str(e)}',

                                    'path': path,

                                    'sessionId': 'debug-session',

                                    'runId': 'run1'

                                }) + '\n')

                        except:

                            pass

                        pass

            

            # Si Arial Unicode MS n'est pas disponible, essayer Tahoma (supporte l'arabe)

            if arabic_font_name == 'Helvetica':

                tahoma_paths = [

                    'C:/Windows/Fonts/tahoma.ttf',

                    'C:/Windows/Fonts/Tahoma.ttf',

                ]

                for path in tahoma_paths:

                    if os.path.exists(path):

                        try:

                            pdfmetrics.registerFont(TTFont('Tahoma', path))

                            arabic_font_name = 'Tahoma'

                            break

                        except:

                            pass

            

            # Si Tahoma n'est pas disponible, essayer DejaVuSans (supporte l'arabe)

            if arabic_font_name == 'Helvetica':

                dejavu_paths = [

                    'C:/Windows/Fonts/DejaVuSans.ttf',

                    'C:/Windows/Fonts/dejavu-sans.ttf',

                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',

                    '/usr/share/fonts/TTF/DejaVuSans.ttf'

                ]

                for path in dejavu_paths:

                    if os.path.exists(path):

                        try:

                            pdfmetrics.registerFont(TTFont('DejaVuSans', path))

                            arabic_font_name = 'DejaVuSans'

                            break

                        except:

                            pass

        except Exception as e:

            # En cas d'erreur, utiliser Helvetica (texte arabe ne s'affichera pas correctement)

            arabic_font_name = 'Helvetica'

        

        # Ensuite charger Square721 BT (pour le texte latin/chiffres)

        try:

            # Chemins possibles pour Square721 BT (chercher dans tous les dossiers possibles)

            # Bitstream est l'éditeur de Square721 BT, donc chercher aussi sous ce nom

            square721_paths = [

                'C:/Windows/Fonts/SQUA721N.TTF',  # Square721 BT Normal

                'C:/Windows/Fonts/squa721n.ttf',

                'C:/Windows/Fonts/SQUA721R.TTF',  # Square721 BT Regular

                'C:/Windows/Fonts/squa721r.ttf',

                'C:/Windows/Fonts/SQUA721.TTF',

                'C:/Windows/Fonts/squa721.ttf',

                'C:/Windows/Fonts/SQUA721N.OTF',

                'C:/Windows/Fonts/squa721n.otf',

                # Variantes possibles

                'C:/Windows/Fonts/SQUARE721.TTF',

                'C:/Windows/Fonts/square721.ttf',

                'C:/Windows/Fonts/SQUARE721N.TTF',

                'C:/Windows/Fonts/square721n.ttf',

            ]

            square721_bold_paths = [

                'C:/Windows/Fonts/SQUA721B.TTF',  # Square721 BT Bold

                'C:/Windows/Fonts/squa721b.ttf',

                'C:/Windows/Fonts/SQUA721D.TTF',  # Square721 BT Demi

                'C:/Windows/Fonts/squa721d.ttf',

                'C:/Windows/Fonts/SQUA721B.OTF',

                'C:/Windows/Fonts/squa721b.otf',

                # Variantes possibles

                'C:/Windows/Fonts/SQUARE721B.TTF',

                'C:/Windows/Fonts/square721b.ttf',

                'C:/Windows/Fonts/SQUARE721D.TTF',

                'C:/Windows/Fonts/square721d.ttf',

            ]

            

            # Recherche dynamique dans le dossier Fonts si les chemins standards ne fonctionnent pas

            if square721_font_name == 'Helvetica':

                try:

                    fonts_dir = 'C:/Windows/Fonts'

                    if os.path.exists(fonts_dir):

                        for font_file in os.listdir(fonts_dir):

                            font_lower = font_file.lower()

                            if ('square' in font_lower or 'squa' in font_lower or '721' in font_lower) and (font_lower.endswith('.ttf') or font_lower.endswith('.otf')):

                                if 'bold' not in font_lower and 'demi' not in font_lower and 'b' not in font_lower[-5:]:

                                    font_path = os.path.join(fonts_dir, font_file)

                                    try:

                                        pdfmetrics.registerFont(TTFont('Square721BT', font_path))

                                        square721_font_name = 'Square721BT'

                                        break

                                    except:

                                        pass

                except:

                    pass

            

            if square721_bold_font_name == 'Helvetica-Bold':

                try:

                    fonts_dir = 'C:/Windows/Fonts'

                    if os.path.exists(fonts_dir):

                        for font_file in os.listdir(fonts_dir):

                            font_lower = font_file.lower()

                            if ('square' in font_lower or 'squa' in font_lower or '721' in font_lower) and (font_lower.endswith('.ttf') or font_lower.endswith('.otf')):

                                if 'bold' in font_lower or 'demi' in font_lower or font_lower[-5:-4] == 'b' or font_lower[-5:-4] == 'd':

                                    font_path = os.path.join(fonts_dir, font_file)

                                    try:

                                        pdfmetrics.registerFont(TTFont('Square721BT-Bold', font_path))

                                        square721_bold_font_name = 'Square721BT-Bold'

                                        break

                                    except:

                                        pass

                except:

                    pass

            

            # Charger Square721 BT Regular

            for path in square721_paths:

                if os.path.exists(path):

                    try:

                        pdfmetrics.registerFont(TTFont('Square721BT', path))

                        square721_font_name = 'Square721BT'

                        break

                    except Exception as e:

                        # Log l'erreur pour debug

                        try:

                            with open(log_path, 'a', encoding='utf-8') as f:

                                f.write(json.dumps({

                                    'timestamp': datetime.now().isoformat(),

                                    'location': 'projet18_routes.py:export_pdf_multilang:square721_error',

                                    'message': f'Erreur chargement Square721 BT: {str(e)}',

                                    'path': path,

                                    'sessionId': 'debug-session',

                                    'runId': 'run1'

                                }) + '\n')

                        except:

                            pass

                        pass

            

            # Charger Square721 BT Bold

            for path in square721_bold_paths:

                if os.path.exists(path):

                    try:

                        pdfmetrics.registerFont(TTFont('Square721BT-Bold', path))

                        square721_bold_font_name = 'Square721BT-Bold'

                        break

                    except:

                        pass

            

            # Si Bold n'est pas trouvé, utiliser la même police que Regular

            if square721_bold_font_name == 'Helvetica-Bold' and square721_font_name != 'Helvetica':

                square721_bold_font_name = square721_font_name

        except Exception as e:

            # En cas d'erreur, utiliser la police arabe comeme fallback

            if square721_font_name == 'Helvetica':

                square721_font_name = arabic_font_name

            if square721_bold_font_name == 'Helvetica-Bold':

                square721_bold_font_name = arabic_font_name

        

        # Si Square721 BT n'est pas trouvé, utiliser la police arabe pour tout

        # (la police arabe supporte aussi le latin, donc c'est acceptable)

        # Mais on essaie d'abord de créer une version Bold de la police arabe

        if square721_font_name == 'Helvetica':

            square721_font_name = arabic_font_name

            # Essayer de créer une version Bold de la police arabe

            if arabic_font_name == 'ArialUnicodeMS':

                try:

                    # Arial Unicode MS n'a pas de version Bold séparée, utiliser la même

                    square721_bold_font_name = arabic_font_name

                except:

                    square721_bold_font_name = arabic_font_name

            elif arabic_font_name == 'Tahoma':

                try:

                    # Essayer Tahoma Bold

                    tahoma_bold_paths = [

                        'C:/Windows/Fonts/tahomabd.ttf',

                        'C:/Windows/Fonts/TahomaBd.ttf',

                    ]

                    for path in tahoma_bold_paths:

                        if os.path.exists(path):

                            try:

                                pdfmetrics.registerFont(TTFont('Tahoma-Bold', path))

                                square721_bold_font_name = 'Tahoma-Bold'

                                break

                            except:

                                pass

                    if square721_bold_font_name == 'Helvetica-Bold':

                        square721_bold_font_name = arabic_font_name

                except:

                    square721_bold_font_name = arabic_font_name

            else:

                square721_bold_font_name = arabic_font_name

        elif square721_bold_font_name == 'Helvetica-Bold':

            square721_bold_font_name = square721_font_name

        

        # Log les polices chargées

        try:

            with open(log_path, 'a', encoding='utf-8') as f:

                f.write(json.dumps({

                    'timestamp': datetime.now().isoformat(),

                    'location': 'projet18_routes.py:export_pdf_multilang:fonts_loaded',

                    'message': 'Polices chargees',

                    'data': {

                        'square721_font': square721_font_name,

                        'square721_bold_font': square721_bold_font_name,

                        'arabic_font': arabic_font_name

                    },

                    'sessionId': 'debug-session',

                    'runId': 'run1'

                }) + '\n')

        except:

            pass

        

        semaines = get_semaines_2026()

        # Limiter à 52 semaines

        semaines = semaines[:52]

        

        # Log nombre de semaines

        with open(log_path, 'a', encoding='utf-8') as f:

            f.write(json.dumps({

                'timestamp': datetime.now().isoformat(),

                'location': 'projet18_routes.py:export_pdf_multilang:semaines',

                'message': 'Nombre de semaines',

                'data': {'nb_semaines': len(semaines)},

                'sessionId': 'debug-session',

                'runId': 'run1'

            }) + '\n')

        

        buffer = BytesIO()

        # Format A4 portrait

        doc = SimpleDocTemplate(

            buffer,

            pagesize=A4,  # Portrait au lieu de landscape

            rightMargin=0.5*cm,

            leftMargin=0.5*cm,

            topMargin=0.5*cm,

            bottomMargin=0.5*cm

        )

        

        styles = getSampleStyleSheet()

        

        # Styles selon le modèle Quo Vadis

        base_style = ParagraphStyle(

            'Base',

            parent=styles['Normal'],

            fontSize=9,

            textColor=colors.HexColor('#000000'),

            fontName=square721_font_name,

            leading=10

        )

        

        # Style pour les noms de jours (anglais/français)

        jour_nom_style = ParagraphStyle(

            'JourNom',

            parent=base_style,

            fontSize=9,

            fontName=square721_font_name,

            alignment=TA_LEFT

        )

        

        # Style pour les dates (grand, gras, noir selon l'image)

        date_style = ParagraphStyle(

            'Date',

            parent=base_style,

            fontSize=12,

            fontName=square721_bold_font_name,

            textColor=colors.HexColor('#000000'),  # Noir au lieu de bleu

            alignment=TA_RIGHT

        )

        

        # Style pour les numéros d'heures (gris clair, petit)

        # Utiliser un style qui ne coupe pas les nombres

        heure_style = ParagraphStyle(

            'Heure',

            parent=base_style,

            fontSize=7,

            textColor=colors.HexColor('#999999'),

            alignment=TA_LEFT,

            leading=14

        )

        

        # Style pour les lignes horaires (gris clair)

        # Utiliser un leading strictement égal à la hauteur de ligne pour garantir exactement 2 lignes

        ligne_horaire_style = ParagraphStyle(

            'LigneHoraire',

            parent=base_style,

            fontSize=8,

            textColor=colors.HexColor('#CCCCCC'),

            leading=8,  # Leading égal à la hauteur de ligne pour garantir exactement 2 lignes sans débordement

            spaceBefore=0,

            spaceAfter=0,

            leftIndent=0,

            rightIndent=0,

            firstLineIndent=0

        )

        

        # Style pour Dimanche

        dimanche_nom_style = ParagraphStyle(

            'DimancheNom',

            parent=base_style,

            fontSize=9,

            fontName=square721_font_name,

            alignment=TA_LEFT

        )

        

        dimanche_date_style = ParagraphStyle(

            'DimancheDate',

            parent=base_style,

            fontSize=12,

            fontName=square721_bold_font_name,

            textColor=colors.HexColor('#000000'),  # Noir au lieu de bleu

            alignment=TA_RIGHT

        )

        

        # Style pour les lignes de notes Dimanche

        ligne_note_style = ParagraphStyle(

            'LigneNote',

            parent=base_style,

            fontSize=8,

            textColor=colors.HexColor('#CCCCCC'),

            leading=14

        )

        

        # Style pour jours fériés

        ferie_style = ParagraphStyle(

            'Ferie',

            parent=base_style,

            fontSize=9,

            textColor=colors.HexColor('#FF0000'),

            fontName=square721_font_name,

            alignment=TA_CENTER

        )

        

        # Style pour le mini-calendrier

        cal_header_style = ParagraphStyle(

            'CalHeader',

            parent=base_style,

            fontSize=10,

            fontName=square721_bold_font_name,

            alignment=TA_CENTER

        )

        # Style spécifique pour le mois en arabe dans le mini-calendrier (version multilingue style 2)

        cal_header_ar_style = ParagraphStyle(

            'CalHeaderArabicStyle2',

            parent=base_style,

            fontSize=10,

            fontName=arabic_font_name,

            alignment=TA_RIGHT

        )

        # Style spécifique pour le mois en arabe dans le mini-calendrier (même ligne, police arabe)

        cal_header_ar_style = ParagraphStyle(

            'CalHeaderArabic',

            parent=base_style,

            fontSize=10,

            fontName=arabic_font_name,

            alignment=TA_RIGHT

        )

        

        cal_semaine_style = ParagraphStyle(

            'CalSemaine',

            parent=base_style,

            fontSize=7,

            textColor=colors.HexColor('#999999'),

            alignment=TA_LEFT,

            leading=10

        )

        

        cal_date_style = ParagraphStyle(

            'CalDate',

            parent=base_style,

            fontSize=8,

            alignment=TA_CENTER,

            leading=10

        )

        

        # Style Bold dédié pour le numéro de semaine

        # Utiliser un style avec la police Bold directement (sans balise HTML)

        # Même leading que les autres pour un alignement parfait

        semaine_num_bold_style = ParagraphStyle(

            'SemaineNumBold',

            parent=base_style,

            fontSize=10,  # Légèrement plus grand pour plus de visibilité

            fontName=square721_bold_font_name,  # Police Bold directement dans le style

            textColor=colors.HexColor('#0066CC'),

            alignment=TA_LEFT,

            leading=14,  # Même leading que les autres styles

            spaceBefore=0,

            spaceAfter=0,

            firstLineIndent=0,

            leftIndent=0,

            rightIndent=0

        )

        

        # Style pour le texte "Semaine Week"

        # Même leading que le numéro pour un alignement parfait

        semaine_text_style = ParagraphStyle(

            'SemaineText',

            parent=base_style,

            fontSize=9,

            fontName=square721_font_name,

            alignment=TA_LEFT,

            leading=14,  # Même leading que le numéro

            spaceBefore=0,

            spaceAfter=0,

            firstLineIndent=0,

            leftIndent=0,

            rightIndent=0

        )

        

        # Style pour le texte arabe

        # Même leading que les autres pour un alignement parfait

        semaine_arabic_style = ParagraphStyle(

            'SemaineArabic',

            parent=base_style,

            fontSize=9,

            fontName=arabic_font_name,

            alignment=TA_LEFT,

            leading=14,  # Même leading que les autres

            spaceBefore=0,

            spaceAfter=0,

            firstLineIndent=0,

            leftIndent=0,

            rightIndent=0

        )

        

        # Largeur cible des champs de saisie pour chaque jour (lundi à samedi) – VERSION MULTILINGUE STYLE 2 :

        # on part de la largeur interne du cadre des jours (~5.1cm) utilisée pour les cadres,

        # puis on réduit volontairement la largeur des lignes de 0,3cm pour qu'elles soient

        # légèrement plus courtes que le cadre tout en restant bien alignées.

        # Largeur cadre jour ≈ 5.1cm -> largeur lignes style2 = 5.1cm - 0.3cm = 4.8cm

        ligne_col_width = 4.8 * cm



        # Fonction utilitaire pour calculer automatiquement la longueur des lignes de saisie

        # en fonction de la largeur disponible, de la police et de la taille de police.

        # Cela permet de garder les 26 lignes alignées exactement sur le cadre du jour.

        def build_ligne_underscore(col_width_points, right_padding_points=2, char="_"):

            """

            Retourne une chaîne de '_' dont la largeur correspond à la largeur disponible

            dans la colonne des champs de saisie, en tenant compte du padding droit.

            """

            # Largeur disponible = largeur de la colonne - padding droit

            available_width = max(col_width_points - right_padding_points, 0)

            # Utiliser la même police et taille que ligne_horaire_style (fontSize=8)

            char_width = pdfmetrics.stringWidth(char, ligne_horaire_style.fontName, ligne_horaire_style.fontSize)

            if char_width <= 0:

                return "_" * 1

            max_chars = int(available_width / char_width)

            return char * max(1, max_chars)



        elements = []

        

        # Dictionnaire des traductions des jours en arabe (pour version multilingue)

        jours_arabe = {

            'lundi': 'الإثنين',

            'mardi': 'الثلاثاء',

            'mercredi': 'الأربعاء',

            'jeudi': 'الخميس',

            'vendredi': 'الجمعة',

            'samedi': 'السبت',

            'dimanche': 'الأحد'

        }

        

        # Heures de 8h à 20h (13 lignes) -> 26 lignes de champs de saisie (2 lignes par heure)

        heures = list(range(8, 21))  # 8, 9, 10, ..., 20

        

        # Générer chaque semaine (2 pages par semaine)

        semaine_index = 0

        for semaine in semaines:

            # Calculer le mois de référence pour le mini-calendrier

            date_ref = semaine['jeudi'] if semaine['jeudi'] is not None else semaine['vendredi']

            if date_ref is None:

                date_ref = semaine['samedi'] if semaine['samedi'] is not None else datetime(2026, 1, 1)

            mois_ref = date_ref.month if date_ref else 1

            annee_ref = date_ref.year if date_ref else 2026

            

            # Mapper le numéro de page au mois correspondant (uniquement dans export_pdf_multilang_style2)

            # Chaque semaine génère 2 pages : page 1 (semaine 0), page 3 (semaine 1), page 5 (semaine 2), etc.

            # Page impaire (page 1 de la semaine) = 2 * semaine_index + 1

            page_num_page1 = 2 * semaine_index + 1

            page_to_mois[page_num_page1] = mois_ref

            # Page paire (page 2 de la semaine) = 2 * semaine_index + 2

            page_num_page2 = 2 * semaine_index + 2

            page_to_mois[page_num_page2] = mois_ref

            

            semaine_index += 1

            

            # ========== PAGE 1 : LUNDI / MARDI / MERCREDI + MINI-CALENDRIER ==========

            page1_data = []

            # Dictionnaire des traductions des jours en arabe (pour version multilingue)
            jours_arabe = {
                'lundi': 'الإثنين',
                'mardi': 'الثلاثاء',
                'mercredi': 'الأربعاء',
                'jeudi': 'الخميس',
                'vendredi': 'الجمعة',
                'samedi': 'السبت',
                'dimanche': 'الأحد'
            }

            # Ligne avec texte de la semaine en haut à gauche

            # Utiliser un seul Paragraph avec des balises font pour tout mettre sur une seule ligne

            semaine_num_formate1 = f"{semaine['numero']:02d}"

            semaine_ar1 = 'الأسبوع'

            # Un seul Paragraph avec des balises font pour changer les polices et le style

            # Le numéro utilise la police Bold directement dans la balise font

            semaine_row1 = [

                Paragraph(

                    f"<font face='{square721_font_name}'>Semaine Week  </font><font face='{square721_bold_font_name}' color='#004499' size='10'>{semaine_num_formate1}</font><font face='{arabic_font_name}'>  {fix_arabic_text(semaine_ar1)}</font>",

                    ParagraphStyle(

                        'SemaineHeader',

                        parent=base_style,

                        fontSize=9,

                        fontName=arabic_font_name,  # Police de base

                        alignment=TA_LEFT,

                        leading=14,

                        spaceBefore=0,

                        spaceAfter=0

                    )

                ),

                Paragraph("", base_style),  # Colonne vide

                Paragraph("", base_style)   # Colonne vide

            ]

            page1_data.append(semaine_row1)

            

            # En-têtes des 3 colonnes (Lundi, Mardi, Mercredi) - Version multilingue

            header_row = []

            jours_page1 = [

                ('lundi', 'Monday', 'Lundi'),

                ('mardi', 'Tuesday', 'Mardi'),

                ('mercredi', 'Wednesday', 'Mercredi')

            ]

            

            for jour_key, jour_en, jour_fr in jours_page1:

                date_jour = semaine[jour_key]

                if date_jour is not None:

                    # Format avec zéro devant si < 10 (01, 02, 03, 04)

                    date_formatee = f"{date_jour.day:02d}"

                    jour_ar = jours_arabe.get(jour_key, '')

                    

                    # Structure : Date en haut (grande), jours en bas (3 langues)

                    # Créer un tableau avec date en haut et jours en bas

                    try:

                        # Ligne 1 : Date (grande, centrée en haut)

                        # Ligne 2 : Français, Anglais, Arabe (en bas)

                        # Utiliser Square721 BT Bold pour les dates (chiffres uniquement)

                        # Utiliser la police arabe pour le texte mixte (contient de l'arabe)

                        header_table = Table([

                            [Paragraph(date_formatee, ParagraphStyle(

                                'HeaderDateMultilang',

                                parent=base_style,

                                fontSize=24,  # Plus grande que la version standard

                                fontName=square721_bold_font_name,  # Square721 BT Bold pour les dates (chiffres)

                                textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                                alignment=TA_CENTER,

                                leading=30  # Augmenter leading pour éeviter superposition

                            ))],  # Ligne 1 : Date seule (chiffres uniquement)

                            [Paragraph(

                                f"<font face='{square721_font_name}'>{jour_fr}</font> / <font face='{square721_font_name}'>{jour_en}</font> / <font face='{arabic_font_name}'>{fix_arabic_text(jour_ar)}</font>",

                                ParagraphStyle(

                                    'HeaderJourMultilang',

                                    parent=base_style,

                                    fontSize=10,  # Taille ajustée pour les jours

                                    fontName=arabic_font_name,  # Police de base (arabe) pour le Paragraph

                                    alignment=TA_CENTER,

                                    leading=17  # Leading ajusté pour garder un bon espacement

                                )

                            )]  # Ligne 2 : Trois langues (contient de l'arabe)

                        ], colWidths=[5.5*cm], rowHeights=[1.2*cm, 0.8*cm])  # Hauteurs explicites pour éeviter superposition

                        header_table.setStyle(TableStyle([

                            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Date centrée verticalement dans sa ligne

                            ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),  # Jours centrés verticalement dans leur ligne

                            ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Date centrée

                            ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés

                            ('LEFTPADDING', (0, 0), (-1, -1), 2),

                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)

                            ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours

                            ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)

                            ('BOTTOMPADDING', (0, 1), (0, 1), 8),  # Padding pour les jours

                        ]))

                    except Exception as e_header:

                        raise

                    # Créer une table avec header_table (date+jours) et jour férié éventuel

                    # Toujours utiliser 2 lignes pour uniformiser la hauteur

                    jour_ferie = is_jour_ferie(date_jour)

                    if jour_ferie:

                        nom_ferie = get_nom_jour_ferie(date_jour)

                        # ⚠️ PROTECTION: Cette section NE DOIT PAS être modifiée dans export_pdf_multilang()

                        # Cette fonction export_pdf_multilang() doit rester inchangée

                        # Toutes les modifications doivent être appliquées uniquement à export_pdf_multilang_style2()

                        # Garder le même BOTTOMPADDING pour les jours pour que le nom du jour reste au même niveau vertical

                        # Date et jours décalés vers le haut pour tous les jours

                        header_table.setStyle(TableStyle([

                            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Date centrée verticalement dans sa ligne

                            ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),  # Jours centrés verticalement dans leur ligne

                            ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Date centrée

                            ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés

                            ('LEFTPADDING', (0, 0), (-1, -1), 2),

                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)

                            ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours

                            ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)

                            ('BOTTOMPADDING', (0, 1), (0, 1), 8),  # Même padding en bas des jours pour alignement vertical uniforme

                        ]))

                        ferie_para = Paragraph(

                            f"<font color='#004499'>{nom_ferie}</font>",  # Même bleu que les dates

                            ferie_style

                        )

                    else:

                        # Paragraph vide pour maintenir la même hauteur

                        ferie_para = Paragraph("", base_style)

                    

                    # Table avec toujours 2 lignes : header_table en haut, jour férié (ou vide) en bas

                    # Hauteurs fixes : header_table (2.0cm) + ligne férié (0.4cm) = 2.4cm total

                    header_cell = Table(

                        [[header_table], [ferie_para]],

                        colWidths=[5.5*cm],

                        rowHeights=[2.0*cm, 0.4*cm]  # Hauteurs fixes pour uniformiser

                    )

                    

                    header_cell.setStyle(TableStyle([

                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

                        ('LEFTPADDING', (0, 0), (-1, -1), 2),

                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                        ('TOPPADDING', (0, 0), (-1, -1), 4 - 0.15*cm),  # Décaler le contenu vers le haut de 0,15 cm

                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),

                        # Réduire l'espacement entre header_table (ligne 0) et jour férié (ligne 1)

                        ('BOTTOMPADDING', (0, 0), (-1, 0), 0),  # Pas de padding en bas de header_table

                        ('TOPPADDING', (0, 1), (-1, 1), -0.25*cm),  # Décaler le texte du jour férié vers le haut de 0,25 cm (décalé vers le bas de 0,3 cm par rapport à -0.55)

                    ]))

                    header_row.append(header_cell)

                else:

                    header_row.append(Paragraph("", base_style))

            

            page1_data.append(header_row)

            

            # Ligne vide pour séparer les en-têtes des jours des champs de saisie

            page1_data.append([Paragraph("", base_style), Paragraph("", base_style), Paragraph("", base_style)])

            

            # 13 lignes horaires pour chaque colonne (8h-20h)

            for heure in heures:

                ligne_row = []

                for jour_key, jour_en, jour_fr in jours_page1:

                    date_jour = semaine[jour_key]

                    if date_jour is not None:

                        # Ligne avec numéro d'heure à gauche et deux lignes grises identiques

                        # Créer deux lignes distinctes avec exactement le même nombre de caractères pour garantir une longueur uniforme

                        # Utiliser un nombre de caractères fixe (42) pour remplir la largeur disponible sans retour à la ligne

                        # Créer exactement 2 lignes de longueur adaptée sans retour à la ligne

                        # Utiliser un nombre de caractères réduit pour éeviter tout retour à la ligne dans le Paragraph

                        # Environ 30-32 caractères pour une largeur de 4.7cm avec fontSize=8 pour éeviter tout débordement

                        # Longueur augmentée de 0,25cm pour la version multilingue style 2 (29 -> 34 caractères)

                        ligne_underscore = "_" * 34

                        # Créer un style spécifique pour empêcher les retours à la ligne

                        ligne_horaire_style_no_wrap = ParagraphStyle(

                            'LigneHoraireNoWrap',

                            parent=ligne_horaire_style,

                            leading=12,  # Leading exactement égal à rowHeights pour garantir exactement 2 lignes sans débordement

                            spaceBefore=0,

                            spaceAfter=0

                        )

                        # Style pour le numéro d'heure aligné avec la première ligne

                        # Utiliser exactement le même leading que la ligne pour un alignement parfait

                        heure_num_style = ParagraphStyle(

                            'HeureNum',

                            parent=base_style,

                            fontSize=7,

                            textColor=colors.HexColor('#999999'),

                            alignment=TA_LEFT,

                            leading=12,  # Exactement le même leading que ligne_horaire_style_no_wrap

                            spaceBefore=0,

                            spaceAfter=0,

                            firstLineIndent=0,

                            leftIndent=0,

                            rightIndent=0

                        )

                        heure_cell = Table(

                            [

                                [Paragraph(str(heure), heure_num_style), Paragraph(ligne_underscore, ligne_horaire_style_no_wrap)],

                                [Paragraph("", base_style), Paragraph(ligne_underscore, ligne_horaire_style_no_wrap)]

                            ],

                            colWidths=[0.6*cm, 5.2*cm],  # Largeur augmentée pour les champs de saisie

                            rowHeights=[12, 12]  # Hauteur exactement égale au leading pour garantir exactement 2 lignes sans ligne supplémentaire

                        )

                        heure_cell.setStyle(TableStyle([

                            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),  # Alignement à droite pour le numéro (plus proche de la ligne)

                            ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Alignement à gauche pour les lignes

                            ('VALIGN', (0, 0), (0, 0), 'TOP'),  # Alignement en haut pour permettre le décalage avec TOPPADDING

                            ('VALIGN', (1, 0), (1, 0), 'BOTTOM'),  # Aligner la première ligne sur sa ligne de base

                            ('VALIGN', (1, 1), (1, 1), 'TOP'),  # Alignement en haut pour la deuxième ligne

                            ('LEFTPADDING', (0, 0), (0, 0), 5),  # Padding à gauche encore augmenté pour décaler davantage le numéro vers la droite

                            ('RIGHTPADDING', (0, 0), (0, 0), 0),  # Pas de padding à droite pour le numéro (très proche de la ligne)

                            ('LEFTPADDING', (1, 0), (1, -1), 0),  # Pas de padding à gauche pour les lignes (très proche du numéro)

                            ('RIGHTPADDING', (1, 0), (1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 2),  # Padding en haut légèrement augmenté pour descendre très légèrement le numéro

                            ('TOPPADDING', (1, 0), (-1, -1), 0),  # Pas de padding en haut pour les lignes

                            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),  # Pas de padding en bas

                            ('BOTTOMPADDING', (1, 1), (1, 1), 0),  # Pas de padding en bas de la dernière ligne

                        ]))

                        ligne_row.append(heure_cell)

                    else:

                        ligne_row.append(Paragraph("", base_style))

                page1_data.append(ligne_row)

            

            # Ligne vide après le dernier champ de saisie (heure 20)

            # Utiliser un style avec leading minimal pour garantir que la ligne a une hauteur

            ligne_vide_style = ParagraphStyle('LigneVide', parent=base_style, fontSize=1, leading=24, spaceBefore=0, spaceAfter=0)

            ligne_vide_apres_heures = [Paragraph(" ", ligne_vide_style)] * len(jours_page1)

            page1_data.append(ligne_vide_apres_heures)

            

            # Mini-calendrier du mois (déplacé de la page 2 vers la page 1)

            # Créer le mini-calendrier avec numéros de semaine

            _, nb_jours_mois = monthrange(annee_ref, mois_ref)

            premier_jour_mois = datetime(annee_ref, mois_ref, 1)

            jour_semaine_premier = premier_jour_mois.weekday()

            

            # Construire le mini-calendrier comeme une grille horizontale

            # Structure : une table avec plusieurs lignes

            cal_table_rows = []

            

            # Noms de mois en arabe pour l'en-tête mini-calendrier (style multilingue 2)

            mois_arabe = {

                1: 'جانفي',

                2: 'فيفري',

                3: 'مارس',

                4: 'أفريل',

                5: 'ماي',

                6: 'جوان',

                7: 'جويلية',

                8: 'أوت',

                9: 'سبتمبر',

                10: 'أكتوبر',

                11: 'نوفمبر',

                12: 'ديسمبر',

            }

            mois_fr = get_mois_nom(mois_ref)

            mois_ar = mois_arabe.get(mois_ref, '')

            

            # Ligne 1 : afficher mois FR + mois AR dans une seule cellule centrée,

            # span sur toute la largeur pour éeviter tout retour à la ligne.

            header_text = f"{mois_fr}  {fix_arabic_text(mois_ar)}"

            cal_table_rows.append([

                Paragraph(header_text, cal_header_ar_style),

                Paragraph("", base_style), Paragraph("", base_style), Paragraph("", base_style),

                Paragraph("", base_style), Paragraph("", base_style), Paragraph("", base_style),

                Paragraph("", base_style),

            ])

            

            # Ligne 2 : Abréviations des jours ("lu ma me je ve sa di")

            jours_abrev = ["lu", "ma", "me", "je", "ve", "sa", "di"]

            cal_jours_abrev_row = [Paragraph("", base_style)]  # Espace pour numéro semaine

            for abrev in jours_abrev:

                cal_jours_abrev_row.append(Paragraph(

                    abrev,

                    ParagraphStyle(

                        'CalJoursAbrev',

                        parent=base_style,

                        fontSize=7,

                        alignment=TA_CENTER,

                        leading=10

                    )

                ))

            cal_table_rows.append(cal_jours_abrev_row)

            

            # Créer la grille du calendrier avec numéros de semaine

            semaine_cal = []

            jours_cal = []

            semaine_num_cal = []

            

            # Trouver le numéro de semaine pour chaque jour

            def get_semaine_num_for_date(date_cible):

                for s in semaines:

                    jours_semaine_list = [s['lundi'], s['mardi'], s['mercredi'], s['jeudi'], s['vendredi'], s['samedi'], s['dimanche']]

                    for d in jours_semaine_list:

                        if d and d.date() == date_cible.date():

                            return s['numero']

                return None

            

            # Calculer correctement le positionnement du premier jour du mois

            # Le premier jour doit être à la position jour_semaine_premier (0=lundi, 3=jeudi, etc.)

            

            # Stocker les dates complètes pour vérifier les jours fériés

            dates_cal = []  # Liste de tuples (jour_str, date_complete) ou None pour les espaces

            

            # Ajouter les dates de décembre avant janvier (si mois_ref == 1)

            if mois_ref == 1:

                mois_precedent = 12

                annee_precedente = annee_ref - 1

                _, nb_jours_decembre = monthrange(annee_precedente, mois_precedent)

                

                # Ajouter les 3 derniers jours de décembre (29, 30, 31)

                for jour_dec in range(29, 32):

                    date_dec = datetime(annee_precedente, mois_precedent, jour_dec)

                    semaine_num = get_semaine_num_for_date(date_dec)

                    semaine_num_cal.append(str(semaine_num) if semaine_num else "")

                    jour_str = f"{jour_dec:02d}"

                    jours_cal.append(jour_str)

                    dates_cal.append((jour_str, date_dec))  # Stocker la date complète

                

                # Après avoir ajouté 29, 30, 31, on a 3 éléments dans jours_cal

                # Le 29 décembre 2025 est un lundi (weekday=0), donc :

                # - Position 0: 29 (lundi)

                # - Position 1: 30 (mardi)  

                # - Position 2: 31 (mercredi)

                # Le 1er janvier 2026 est un jeudi (weekday=3), donc il doit être à la position 3

                # Comeme on a déjà 3 éléments, la prochaine position est 3, ce qui est correct

                # Donc pas besoin d'espaces supplémentaires

                nb_espaces_a_ajouter = 0

            else:

                # Pour les autres mois, ajouter simplement les espaces nécessaires

                nb_espaces_a_ajouter = jour_semaine_premier

            

            # Ajouter les espaces nécessaires

            for _ in range(nb_espaces_a_ajouter):

                if len(jours_cal) < 7:  # Ne pas dépasser 7 jours par semaine

                    semaine_num_cal.append("")

                    jours_cal.append("")

                    dates_cal.append(None)  # Pas de date pour les espaces

            

            # Ajouter les jours du mois courant avec numéro de semaine

            jour_courant = 1

            while jour_courant <= nb_jours_mois:

                jour_date = datetime(annee_ref, mois_ref, jour_courant)

                semaine_num = get_semaine_num_for_date(jour_date)

                

                semaine_num_cal.append(str(semaine_num) if semaine_num else "")

                # Format avec zéro devant si < 10

                jour_str = f"{jour_courant:02d}"

                jours_cal.append(jour_str)

                dates_cal.append((jour_str, jour_date))  # Stocker la date complète

                

                jour_courant += 1

                

                if len(jours_cal) == 7:

                    # Trouver le numéro de semaine pour cette ligne (prendre le premier non vide)

                    semaine_num_ligne = None

                    for sn in semaine_num_cal:

                        if sn:

                            semaine_num_ligne = sn

                            break

                    

                    # Créer une ligne avec numéro de semaine à gauche et dates à droite

                    cal_row_cells = []

                    # Numéro de semaine à gauche (petit, gris)

                    cal_row_cells.append(Paragraph(

                        semaine_num_ligne if semaine_num_ligne else "",

                        cal_semaine_style

                    ))

                    

                    # Dates à droite (7 colonnes)

                    for idx, jour_str in enumerate(jours_cal):

                        # Vérifier si c'est un jour férié (uniquement pour les jours du mois courant)

                        if idx < len(dates_cal) and dates_cal[idx] is not None:

                            _, date_complete = dates_cal[idx]

                            if is_jour_ferie(date_complete):

                                # Highlight bleu clair pour les jours fériés uniquement

                                cal_row_cells.append(Paragraph(

                                    jour_str,

                                    ParagraphStyle(

                                        'CalDateHighlight',

                                        parent=base_style,

                                        fontSize=8,

                                        textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                                        backColor=colors.HexColor('#E6F3FF'),  # Bleu clair

                                        alignment=TA_CENTER,

                                        leading=10

                                    )

                                ))

                            else:

                                cal_row_cells.append(Paragraph(jour_str, cal_date_style))

                        else:

                            # Espace vide ou jour d'un autre mois

                            cal_row_cells.append(Paragraph(jour_str, cal_date_style))

                    

                    # Ajouter la ligne directement à cal_table_rows

                    cal_table_rows.append(cal_row_cells)

                    

                    semaine_cal = []

                    jours_cal = []

                    semaine_num_cal = []

                    dates_cal = []

            

            # Compléter la dernière semaine avec le début de février (si nécessaire)

            if len(jours_cal) > 0 and len(jours_cal) < 7:

                mois_suivant = mois_ref + 1 if mois_ref < 12 else 1

                annee_suivante = annee_ref if mois_ref < 12 else annee_ref + 1

                jour_fevrier = 1

                while len(jours_cal) < 7:

                    date_fev = datetime(annee_suivante, mois_suivant, jour_fevrier)

                    semaine_num = get_semaine_num_for_date(date_fev)

                    semaine_num_cal.append(str(semaine_num) if semaine_num else "")

                    jour_str = f"{jour_fevrier:02d}"

                    jours_cal.append(jour_str)

                    dates_cal.append((jour_str, date_fev))  # Stocker la date complète

                    jour_fevrier += 1

                

                # Créer la dernière ligne avec numéro de semaine à gauche

                # Trouver le numéro de semaine pour cette ligne

                semaine_num_ligne = None

                for sn in semaine_num_cal:

                    if sn:

                        semaine_num_ligne = sn

                        break

                

                cal_row_cells = []

                # Numéro de semaine à gauche

                cal_row_cells.append(Paragraph(

                    semaine_num_ligne if semaine_num_ligne else "",

                    cal_semaine_style

                ))

                

                # Dates à droite

                for idx, jour_str in enumerate(jours_cal):

                    # Vérifier si c'est un jour férié

                    if idx < len(dates_cal) and dates_cal[idx] is not None:

                        _, date_complete = dates_cal[idx]

                        if is_jour_ferie(date_complete):

                            # Highlight bleu clair pour les jours fériés uniquement

                            cal_row_cells.append(Paragraph(

                                jour_str,

                                ParagraphStyle(

                                    'CalDateHighlight',

                                    parent=base_style,

                                    fontSize=8,

                                    textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                                    backColor=colors.HexColor('#E6F3FF'),  # Bleu clair

                                    alignment=TA_CENTER,

                                    leading=10

                                )

                            ))

                        else:

                            cal_row_cells.append(Paragraph(jour_str, cal_date_style))

                    else:

                        # Espace vide

                        cal_row_cells.append(Paragraph(jour_str, cal_date_style))

                

                cal_table_rows.append(cal_row_cells)

            

            # Limiter à 6 lignes de dates (en plus de l'en-tête et des abréviations)

            # Total : 1 en-tête + 1 abréviations + 6 lignes dates = 8 lignes max

            if len(cal_table_rows) > 8:

                cal_table_rows = cal_table_rows[:8]

            

            # Créer le tableau du mini-calendrier comeme une grille horizontale

            try:

                cal_table = Table(

                    cal_table_rows,

                    colWidths=[0.6*cm] + [0.7*cm] * 7  # Numéro semaine (ajusté) + 7 dates = 8 colonnes

                )

                cal_table.setStyle(TableStyle([

                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # En-tête mois centré sur toutes les colonnes

                    ('SPAN', (0, 0), (-1, 0)),  # Fusionner les colonnes pour l'en-tête

                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Numéros de semaine à gauche

                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Dates et abréviations centrées

                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                    ('LEFTPADDING', (0, 0), (-1, -1), 2),

                    ('LEFTPADDING', (0, 1), (0, -1), 6),  # Padding encore augmenté pour décaler davantage le numéro de semaine vers la droite

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (-1, -1), 2),

                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),

                    # Cadre supprimé - pas de GRID

                ]))

            except Exception as e_cal_table:

                raise

            

            # Ajouter la ligne avec mini-calendrier à gauche

            cal_row = [

                cal_table,  # Mini-calendrier colonne 1 (à gauche)

                Paragraph("", base_style),  # Espace vide colonne 2

                Paragraph("", base_style)  # Espace vide colonne 3

            ]

            page1_data.append(cal_row)

            

            # Trouver l'index de la ligne du mini-calendrier (dernière ligne)

            cal_row_index = len(page1_data) - 1

            

            # Trouver l'index de la ligne des en-têtes (après la ligne de la semaine)

            header_row_index = 1  # La ligne de la semaine est à l'index 0, les en-têtes sont à l'index 1

            semaine_row_index = 0  # La ligne de la semaine est à l'index 0

            ligne_vide_index = 2  # La ligne vide est à l'index 2 (après la semaine et les en-têtes)

            

            # Trouver l'index de la dernière ligne horaire (20h)

            # Il y a 1 ligne vide + 13 lignes horaires (8h-20h), donc la dernière est à l'index ligne_vide_index + 13

            derniere_ligne_horaire_index = ligne_vide_index + len(heures)  # ligne_vide_index (2) + 13 lignes horaires = 15

            # Index de la ligne vide après les heures (juste après la dernière ligne horaire)

            ligne_vide_apres_heures_index = derniere_ligne_horaire_index + 1

            

            # Créer le tableau pour la page 1 (format portrait - colonnes plus étroites)

            # Calculer les hauteurs de lignes : ligne semaine (fixe), ligne en-tête (fixe), autres lignes (auto)

            # Hauteur ligne semaine : identique à la page 2 (0.7cm) pour que les tableaux comemencent au même niveau

            # Hauteur ligne en-tête : header_cell (2.4cm) + TOPPADDING (0.3cm) = 2.7cm

            page1_row_heights = [None] * len(page1_data)  # None = hauteur automatique

            page1_row_heights[semaine_row_index] = 0.7*cm  # Hauteur fixe pour la ligne de la semaine (identique à page 2)

            page1_row_heights[header_row_index] = 2.7*cm  # Hauteur fixe pour la ligne d'en-tête

            # Hauteur de la ligne vide = même hauteur que les lignes horaires (2 lignes de 12 points chacune = 24 points ≈ 0.85cm)

            page1_row_heights[ligne_vide_index] = 24  # Même hauteur que les lignes horaires (2 lignes de 12 points)

            # Hauteur de la ligne vide après les heures (réduite de 1 cm pour décaler le mini-calendrier vers le haut)
            # 1 cm = 28.35 points, donc on réduit de 28 points (environ 1 cm) pour décaler le mini-calendrier vers le haut

            if ligne_vide_apres_heures_index < len(page1_row_heights):

                page1_row_heights[ligne_vide_apres_heures_index] = 0  # Réduite pour décaler le mini-calendrier de 1 cm vers le haut

            page1_table = Table(page1_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm], rowHeights=page1_row_heights)

            page1_table.setStyle(TableStyle([

                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                # Bordures pour toutes les lignes sauf la ligne de la semaine

                ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),  # Bordures grises fines (à partir de la ligne 1)

                # Supprimer toutes les bordures de la ligne de la semaine (ligne 0)

                ('LINEABOVE', (0, semaine_row_index), (-1, semaine_row_index), 0, colors.white),  # Pas de bordure au-dessus

                ('LINEBELOW', (0, semaine_row_index), (-1, semaine_row_index), 0, colors.white),  # Pas de bordure en-dessous

                ('LINEBEFORE', (0, semaine_row_index), (0, semaine_row_index), 0, colors.white),  # Pas de bordure à gauche

                ('LINEAFTER', (-1, semaine_row_index), (-1, semaine_row_index), 0, colors.white),  # Pas de bordure à droite

                ('LINEBELOW', (0, header_row_index), (-1, header_row_index), 1, colors.HexColor('#CCCCCC')),  # Ligne sous les en-têtes

                # Supprimer la ligne verticale entre Mardi (colonne 1) et Mercredi (colonne 2) uniquement pour la ligne du mini-calendrier

                ('LINEAFTER', (1, cal_row_index), (1, cal_row_index), 0, colors.white),

                # Centrer le calendrier dans sa cellule (cadre)

                ('ALIGN', (0, cal_row_index), (0, cal_row_index), 'CENTER'),

                ('VALIGN', (0, cal_row_index), (0, cal_row_index), 'MIDDLE'),

                ('LEFTPADDING', (0, 0), (-1, -1), 0),

                ('RIGHTPADDING', (0, 0), (-1, -1), 0),

                ('TOPPADDING', (0, 0), (-1, -1), 0),

                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),

                # Ajouter un espacement en haut de la ligne des en-têtes pour décaler le reste du tableau vers le bas (identique à la page 2)

                ('TOPPADDING', (0, header_row_index), (-1, header_row_index), 0.3*cm),

            ]))

            

            elements.append(page1_table)

            elements.append(PageBreak())

            

            # ========== PAGE 2 : JEUDI / VENDREDI / SAMEDI + DIMANCHE ==========

            page2_data = []

            

            # Ligne avec texte de la semaine en haut à gauche et "2026" en haut à droite

            semaine_num_formate2 = f"{semaine['numero']:02d}"

            semaine_ar2 = 'الأسبوع'

            # Utiliser un seul Paragraph avec des balises font pour tout mettre sur une seule ligne (même approche que page 1)

            # Le numéro utilise la police Bold directement dans la balise font

            semaine_row2 = [

                Paragraph(

                    f"<font face='{square721_font_name}'>Semaine Week  </font><font face='{square721_bold_font_name}' color='#004499' size='10'>{semaine_num_formate2}</font><font face='{arabic_font_name}'>  {fix_arabic_text(semaine_ar2)}</font>",

                    ParagraphStyle(

                        'SemaineHeader',

                        parent=base_style,

                        fontSize=9,

                        fontName=arabic_font_name,  # Police de base

                        alignment=TA_LEFT,

                        leading=14,

                        spaceBefore=0,

                        spaceAfter=0

                    )

                ),

                Paragraph("", base_style),  # Colonne vide

                Paragraph("2026", ParagraphStyle(

                    'AnneePage2',

                    parent=base_style,

                    fontSize=20,

                    fontName=square721_bold_font_name,

                    textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                    alignment=TA_RIGHT,

                    leading=20,

                    leftIndent=0  # Retirer leftIndent car on utilise LEFTPADDING sur la cellule

                ))

            ]

            page2_data.append(semaine_row2)

            

            # En-têtes des 3 colonnes (Jeudi, Vendredi, Samedi) - Version multilingue

            header_row2 = []

            jours_page2 = [

                ('jeudi', 'Thursday', 'Jeudi'),

                ('vendredi', 'Friday', 'Vendredi'),

                ('samedi', 'Saturday', 'Samedi')

            ]

            

            for jour_key, jour_en, jour_fr in jours_page2:

                date_jour = semaine[jour_key]

                if date_jour is not None:

                    # Format avec zéro devant si < 10 (01, 02, 03, 04)

                    date_formatee = f"{date_jour.day:02d}"

                    jour_ar = jours_arabe.get(jour_key, '')

                    

                    # Structure : Date en haut (grande), jours en bas (3 langues)

                    # Créer un tableau avec date en haut et jours en bas

                    try:

                        # Ligne 1 : Date (grande, centrée en haut)

                        # Ligne 2 : Français, Anglais, Arabe (en bas)

                        # Utiliser Square721 BT Bold pour les dates (chiffres uniquement)

                        # Utiliser la police arabe pour le texte mixte (contient de l'arabe)

                        header_table = Table([

                            [Paragraph(date_formatee, ParagraphStyle(

                                'HeaderDateMultilang',

                                parent=base_style,

                                fontSize=24,  # Plus grande que la version standard

                                fontName=square721_bold_font_name,  # Square721 BT Bold pour les dates (chiffres)

                                textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                                alignment=TA_CENTER,

                                leading=30  # Augmenter leading pour éeviter superposition

                            ))],  # Ligne 1 : Date seule (chiffres uniquement)

                            [Paragraph(

                                f"<font face='{square721_font_name}'>{jour_fr}</font> / <font face='{square721_font_name}'>{jour_en}</font> / <font face='{arabic_font_name}'>{fix_arabic_text(jour_ar)}</font>",

                                ParagraphStyle(

                                    'HeaderJourMultilang',

                                    parent=base_style,

                                    fontSize=10,  # Taille ajustée pour les jours

                                    fontName=arabic_font_name,  # Police de base (arabe) pour le Paragraph

                                    alignment=TA_CENTER,

                                    leading=17  # Leading ajusté pour garder un bon espacement

                                )

                            )]  # Ligne 2 : Trois langues (contient de l'arabe)

                        ], colWidths=[5.5*cm], rowHeights=[1.2*cm, 0.8*cm])  # Hauteurs explicites pour éeviter superposition

                        header_table.setStyle(TableStyle([

                            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Date centrée verticalement dans sa ligne

                            ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),  # Jours centrés verticalement dans leur ligne

                            ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Date centrée

                            ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés

                            ('LEFTPADDING', (0, 0), (-1, -1), 2),

                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)

                            ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours

                            ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)

                            ('BOTTOMPADDING', (0, 1), (0, 1), 8),  # Padding pour les jours

                        ]))

                    except Exception as e_header:

                        raise

                    # Créer une table avec header_table (date+jours) et jour férié éventuel

                    # Toujours utiliser 2 lignes pour uniformiser la hauteur

                    jour_ferie = is_jour_ferie(date_jour)

                    if jour_ferie:

                        nom_ferie = get_nom_jour_ferie(date_jour)

                        # ⚠️ PROTECTION: Cette section NE DOIT PAS être modifiée dans export_pdf_multilang()

                        # Cette fonction export_pdf_multilang() doit rester inchangée

                        # Toutes les modifications doivent être appliquées uniquement à export_pdf_multilang_style2()

                        # Garder le même BOTTOMPADDING pour les jours pour que le nom du jour reste au même niveau vertical

                        # Date et jours décalés vers le haut pour tous les jours

                        header_table.setStyle(TableStyle([

                            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Date centrée verticalement dans sa ligne

                            ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),  # Jours centrés verticalement dans leur ligne

                            ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Date centrée

                            ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés

                            ('LEFTPADDING', (0, 0), (-1, -1), 2),

                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)

                            ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours

                            ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)

                            ('BOTTOMPADDING', (0, 1), (0, 1), 8),  # Même padding en bas des jours pour alignement vertical uniforme

                        ]))

                        ferie_para = Paragraph(

                            f"<font color='#004499'>{nom_ferie}</font>",  # Même bleu que les dates

                            ferie_style

                        )

                    else:

                        # Paragraph vide pour maintenir la même hauteur

                        ferie_para = Paragraph("", base_style)

                    

                    # Table avec toujours 2 lignes : header_table en haut, jour férié (ou vide) en bas

                    # Hauteurs fixes : header_table (2.0cm) + ligne férié (0.4cm) = 2.4cm total

                    header_cell = Table(

                        [[header_table], [ferie_para]],

                        colWidths=[5.5*cm],

                        rowHeights=[2.0*cm, 0.4*cm]  # Hauteurs fixes pour uniformiser

                    )

                    

                    header_cell.setStyle(TableStyle([

                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

                        ('LEFTPADDING', (0, 0), (-1, -1), 2),

                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                        ('TOPPADDING', (0, 0), (-1, -1), 4 - 0.15*cm),  # Décaler le contenu vers le haut de 0,15 cm

                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),

                        # Réduire l'espacement entre header_table (ligne 0) et jour férié (ligne 1)

                        ('BOTTOMPADDING', (0, 0), (-1, 0), 0),  # Pas de padding en bas de header_table

                        ('TOPPADDING', (0, 1), (-1, 1), -0.25*cm),  # Décaler le texte du jour férié vers le haut de 0,25 cm (décalé vers le bas de 0,3 cm par rapport à -0.55)

                    ]))

                    header_row2.append(header_cell)

                else:

                    header_row2.append(Paragraph("", base_style))

            

            page2_data.append(header_row2)

            

            # Ligne vide pour séparer les en-têtes des jours des champs de saisie

            page2_data.append([Paragraph("", base_style), Paragraph("", base_style), Paragraph("", base_style)])

            

            # 13 lignes horaires pour chaque colonne (8h-20h)

            for heure in heures:

                ligne_row = []

                for jour_key, jour_en, jour_fr in jours_page2:

                    date_jour = semaine[jour_key]

                    if date_jour is not None:

                        # Ligne avec numéro d'heure à gauche et deux lignes grises identiques

                        # Créer deux lignes distinctes avec exactement le même nombre de caractères pour garantir une longueur uniforme

                        # Utiliser un nombre de caractères fixe (42) pour remplir la largeur disponible sans retour à la ligne

                        # Créer exactement 2 lignes de longueur adaptée sans retour à la ligne

                        # Utiliser un nombre de caractères réduit pour éeviter tout retour à la ligne dans le Paragraph

                        # Environ 30-32 caractères pour une largeur de 4.7cm avec fontSize=8 pour éeviter tout débordement

                        # Longueur augmentée de 0,25cm pour la version multilingue style 2 (29 -> 34 caractères)

                        ligne_underscore = "_" * 34

                        # Créer un style spécifique pour empêcher les retours à la ligne

                        ligne_horaire_style_no_wrap = ParagraphStyle(

                            'LigneHoraireNoWrap',

                            parent=ligne_horaire_style,

                            leading=12,  # Leading exactement égal à rowHeights pour garantir exactement 2 lignes sans débordement

                            spaceBefore=0,

                            spaceAfter=0

                        )

                        # Style pour le numéro d'heure aligné avec la première ligne

                        # Utiliser exactement le même leading que la ligne pour un alignement parfait

                        heure_num_style = ParagraphStyle(

                            'HeureNum',

                            parent=base_style,

                            fontSize=7,

                            textColor=colors.HexColor('#999999'),

                            alignment=TA_LEFT,

                            leading=12,  # Exactement le même leading que ligne_horaire_style_no_wrap

                            spaceBefore=0,

                            spaceAfter=0,

                            firstLineIndent=0,

                            leftIndent=0,

                            rightIndent=0

                        )

                        heure_cell = Table(

                            [

                                [Paragraph(str(heure), heure_num_style), Paragraph(ligne_underscore, ligne_horaire_style_no_wrap)],

                                [Paragraph("", base_style), Paragraph(ligne_underscore, ligne_horaire_style_no_wrap)]

                            ],

                            colWidths=[0.6*cm, 5.2*cm],  # Largeur augmentée pour les champs de saisie

                            rowHeights=[12, 12]  # Hauteur exactement égale au leading pour garantir exactement 2 lignes sans ligne supplémentaire

                        )

                        heure_cell.setStyle(TableStyle([

                            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),  # Alignement à droite pour le numéro (plus proche de la ligne)

                            ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Alignement à gauche pour les lignes

                            ('VALIGN', (0, 0), (0, 0), 'TOP'),  # Alignement en haut pour permettre le décalage avec TOPPADDING

                            ('VALIGN', (1, 0), (1, 0), 'BOTTOM'),  # Aligner la première ligne sur sa ligne de base

                            ('VALIGN', (1, 1), (1, 1), 'TOP'),  # Alignement en haut pour la deuxième ligne

                            ('LEFTPADDING', (0, 0), (0, 0), 5),  # Padding à gauche encore augmenté pour décaler davantage le numéro vers la droite

                            ('RIGHTPADDING', (0, 0), (0, 0), 0),  # Pas de padding à droite pour le numéro (très proche de la ligne)

                            ('LEFTPADDING', (1, 0), (1, -1), 0),  # Pas de padding à gauche pour les lignes (très proche du numéro)

                            ('RIGHTPADDING', (1, 0), (1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 2),  # Padding en haut légèrement augmenté pour descendre très légèrement le numéro

                            ('TOPPADDING', (1, 0), (-1, -1), 0),  # Pas de padding en haut pour les lignes

                            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),  # Pas de padding en bas

                            ('BOTTOMPADDING', (1, 1), (1, 1), 0),  # Pas de padding en bas de la dernière ligne

                        ]))

                        ligne_row.append(heure_cell)

                    else:

                        ligne_row.append(Paragraph("", base_style))

                page2_data.append(ligne_row)

            

            # Ligne vide après le dernier champ de saisie (heure 20)

            # Utiliser un espace avec un style ayant un leading minimal pour garantir que la ligne a une hauteur

            ligne_vide_style = ParagraphStyle('LigneVide', parent=base_style, fontSize=1, leading=24, spaceBefore=0, spaceAfter=0)

            ligne_vide_apres_heures = [Paragraph(" ", ligne_vide_style)] * len(jours_page2)

            page2_data.append(ligne_vide_apres_heures)

            

            # Zone Dimanche : en-tête dans colonne 1, lignes grises dans colonnes 2 et 3 (déplacé de la page 1 vers la page 2)

            dimanche_row = []

            if semaine['dimanche'] is not None:

                jour_ferie = is_jour_ferie(semaine['dimanche'])

                nom_ferie = get_nom_jour_ferie(semaine['dimanche']) if jour_ferie else ""

                

                # Contenu Dimanche : Date en haut (grande), jours en bas (3 langues)

                # Format avec zéro devant si < 10

                date_dimanche_formatee = f"{semaine['dimanche'].day:02d}"

                dimanche_ar = jours_arabe.get('dimanche', 'الأحد')

                

                # Structure : Date en haut (grande), jours en bas (3 langues)

                # Utiliser Square721 BT Bold pour les dates (chiffres uniquement, pas besoin d'arabe)

                # Utiliser Square721 BT pour tous les textes

                dimanche_header_table = Table([

                    [Paragraph(date_dimanche_formatee, ParagraphStyle(

                        'DimancheDateMultilang',

                        parent=base_style,

                        fontSize=24,  # Plus grande que la version standard

                                fontName=square721_bold_font_name,  # Square721 BT Bold pour les dates

                        textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                        alignment=TA_CENTER,

                        leading=30  # Augmenter leading pour éeviter superposition

                    ))],  # Ligne 1 : Date seule

                    [Paragraph(

                        f"<font face='{square721_font_name}'>Dimanche</font> / <font face='{square721_font_name}'>Sunday</font> / <font face='{arabic_font_name}'>{fix_arabic_text(dimanche_ar)}</font>",

                        ParagraphStyle(

                            'DimancheJourMultilang',

                            parent=base_style,

                            fontSize=9,

                            fontName=arabic_font_name,

                            alignment=TA_CENTER,

                            leading=16  # Augmenter leading pour l'espacement

                        )

                    )]  # Ligne 2 : Trois langues

                ], colWidths=[5.5*cm], rowHeights=[1.2*cm, 0.8*cm])  # Hauteurs explicites pour éeviter superposition

                dimanche_header_table.setStyle(TableStyle([

                    ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Date centrée verticalement dans sa ligne

                    ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),  # Jours centrés verticalement dans leur ligne

                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Date centrée

                    ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés

                    ('LEFTPADDING', (0, 0), (-1, -1), 2),

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)

                    ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours

                    ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)

                    ('BOTTOMPADDING', (0, 1), (0, 1), 8),  # Padding pour les jours

                ]))

                

                # Colonne 1 : En-tête Dimanche + date (et jour férié si applicable)

                # Toujours utiliser 2 lignes pour uniformiser la hauteur

                if jour_ferie:

                    # Réduire le BOTTOMPADDING de la ligne des jours dans dimanche_header_table quand il y a un jour férié

                    # Date et jours décalés vers le haut pour tous les jours

                    dimanche_header_table.setStyle(TableStyle([

                            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Date centrée verticalement dans sa ligne

                            ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),  # Jours centrés verticalement dans leur ligne

                            ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Date centrée

                            ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés (dimanche reste centré dans fonction originale)

                            ('LEFTPADDING', (0, 0), (-1, -1), 2),

                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)

                            ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours

                            ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)

                            ('BOTTOMPADDING', (0, 1), (0, 1), 0),  # Pas de padding en bas des jours quand il y a un jour férié

                        ]))

                    dimanche_ferie_para = Paragraph(

                        f"<font color='#004499'>{nom_ferie}</font>",  # Même bleu que les dates

                        ferie_style

                    )

                else:

                    # Paragraph vide pour maintenir la même hauteur

                    dimanche_ferie_para = Paragraph("", base_style)

                

                # Table avec toujours 2 lignes : dimanche_header_table en haut, jour férié (ou vide) en bas

                # Hauteurs fixes : dimanche_header_table (2.0cm) + ligne férié (0.4cm) = 2.4cm total

                dimanche_header_cell = Table(

                    [[dimanche_header_table], [dimanche_ferie_para]],

                    colWidths=[5.5*cm],

                    rowHeights=[2.0*cm, 0.4*cm]  # Hauteurs fixes pour uniformiser

                )

                dimanche_header_cell.setStyle(TableStyle([

                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

                    ('LEFTPADDING', (0, 0), (-1, -1), 2),

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour décaler dimanche_header_table vers le haut

                    ('BOTTOMPADDING', (0, 0), (0, 0), 12),

                    # Réduire l'espacement entre dimanche_header_table (ligne 0) et jour férié (ligne 1)

                    ('BOTTOMPADDING', (0, 0), (-1, 0), 0),  # Pas de padding en bas de dimanche_header_table

                    ('TOPPADDING', (0, 1), (-1, 1), 0),  # Pas de padding en haut du jour férié

                ]))

                

                # Colonnes 2 et 3 : 5 lignes grises (fusionnées sur 2 colonnes)

                dimanche_notes_rows = []

                for i in range(5):

                    dimanche_notes_rows.append([Paragraph("_" * 72, ligne_note_style)])  # Augmenter de 12 caractères pour ajouter 1cm de largeur

                

                dimanche_notes_cell = Table(

                    dimanche_notes_rows,

                    colWidths=[12*cm]  # Largeur augmentée de 1cm (11cm + 1cm = 12cm)

                )

                dimanche_notes_cell.setStyle(TableStyle([

                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                    ('LEFTPADDING', (0, 0), (-1, -1), 15 + 0.1*cm),  # Décaler les lignes vers la droite de 0,1 cm

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (-1, -1), 2),

                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),

                ]))

                

                # Structure finale : colonne 0 = en-tête, colonnes 1-2 = lignes grises (fusionnées)

                # Le contenu doit être dans la première colonne du SPAN (colonne 1)

                dimanche_row.append(dimanche_header_cell)  # Colonne 0 (Jeudi)

                dimanche_row.append(dimanche_notes_cell)  # Colonne 1 (Vendredi) - sera fusionnée avec colonne 2

                dimanche_row.append(Paragraph("", base_style))  # Colonne 2 (Samedi) - sera fusionnée avec colonne 1

            else:

                dimanche_row = [Paragraph("", base_style)] * 3

            

            page2_data.append(dimanche_row)

            

            # Trouver l'index de la ligne Dimanche (dernière ligne)

            dimanche_row_index = len(page2_data) - 1

            # Trouver l'index de la ligne des en-têtes (après la ligne de la semaine)

            header_row2_index = 1  # La ligne de la semaine est à l'index 0, les en-têtes sont à l'index 1

            semaine_row2_index = 0  # La ligne de la semaine est à l'index 0

            ligne_vide2_index = 2  # La ligne vide est à l'index 2 (après la semaine et les en-têtes)

            

            # Trouver l'index de la dernière ligne horaire (20h)

            # Il y a 1 ligne vide + 13 lignes horaires (8h-20h), donc la dernière est à l'index ligne_vide2_index + 13

            derniere_ligne_horaire2_index = ligne_vide2_index + len(heures)  # ligne_vide2_index (2) + 13 lignes horaires = 15

            

            # Créer le tableau pour la page 2 (format portrait - colonnes plus étroites)

            # Calculer les hauteurs de lignes : ligne semaine (fixe), ligne en-tête (fixe), autres lignes (auto)

            # Hauteur ligne semaine : texte "2026" avec fontSize=20, leading=20 ≈ 0.7cm

            # Hauteur ligne en-tête : header_cell (2.4cm) + TOPPADDING (0.3cm) = 2.7cm

            page2_row_heights = [None] * len(page2_data)  # None = hauteur automatique

            page2_row_heights[semaine_row2_index] = 0.7*cm  # Hauteur fixe pour la ligne de la semaine (identique à page 1)

            page2_row_heights[header_row2_index] = 2.7*cm  # Hauteur fixe pour la ligne d'en-tête

            # Hauteur de la ligne vide = même hauteur que les lignes horaires (2 lignes de 12 points chacune = 24 points ≈ 0.85cm)

            page2_row_heights[ligne_vide2_index] = 24  # Même hauteur que les lignes horaires (2 lignes de 12 points)

            # Index de la ligne vide après les heures (juste après la dernière ligne horaire)

            ligne_vide_apres_heures2_index = derniere_ligne_horaire2_index + 1

            # Hauteur de la ligne vide après les heures (même hauteur qu'une ligne horaire)

            if ligne_vide_apres_heures2_index < len(page2_row_heights):

                page2_row_heights[ligne_vide_apres_heures2_index] = 24  # Même hauteur que les lignes horaires

            page2_table = Table(page2_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm], rowHeights=page2_row_heights)

            page2_table.setStyle(TableStyle([

                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                # Centrer verticalement le texte de la semaine et "2026" sur la même ligne

                ('VALIGN', (0, semaine_row2_index), (2, semaine_row2_index), 'MIDDLE'),

                # Bordures pour toutes les lignes sauf la ligne de la semaine

                ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),  # Bordures grises fines (à partir de la ligne 1)

                # Supprimer toutes les bordures de la ligne de la semaine (ligne 0)

                ('LINEABOVE', (0, semaine_row2_index), (-1, semaine_row2_index), 0, colors.white),  # Pas de bordure au-dessus

                ('LINEBELOW', (0, semaine_row2_index), (-1, semaine_row2_index), 0, colors.white),  # Pas de bordure en-dessous

                ('LINEBEFORE', (0, semaine_row2_index), (0, semaine_row2_index), 0, colors.white),  # Pas de bordure à gauche

                ('LINEAFTER', (-1, semaine_row2_index), (-1, semaine_row2_index), 0, colors.white),  # Pas de bordure à droite

                ('LINEBELOW', (0, header_row2_index), (-1, header_row2_index), 1, colors.HexColor('#CCCCCC')),  # Ligne sous les en-têtes

                # Fusionner les colonnes 1 et 2 (Vendredi et Samedi) pour les lignes grises du Dimanche

                ('SPAN', (1, dimanche_row_index), (2, dimanche_row_index)),

                ('LEFTPADDING', (0, 0), (-1, -1), 0),

                # Décaler le texte "2026" vers la droite (colonne 2, ligne semaine)

                ('LEFTPADDING', (2, semaine_row2_index), (2, semaine_row2_index), 0.3*cm),

                ('RIGHTPADDING', (0, 0), (-1, -1), 0),

                ('TOPPADDING', (0, 0), (-1, -1), 0),

                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),

                # Réduire l'espacement en haut de la ligne des en-têtes pour décaler le bloc (date+jours+jour férié) vers le haut (sauf dimanche)

                ('TOPPADDING', (0, header_row2_index), (2, header_row2_index), 0.05*cm),  # Seulement colonnes 0-2 (Jeudi, Vendredi, Samedi), pas dimanche

            ]))

            

            elements.append(page2_table)

            

            # Saut de page entre les semaines (sauf pour la dernière)

            if semaine != semaines[-1]:

                elements.append(PageBreak())

        

        # Générer le PDF

        doc.build(elements)

        buffer.seek(0)

        

        response = make_response(buffer.read())

        response.headers['Content-Type'] = 'application/pdf'

        # Nom de fichier différent pour indiquer que c'est la version multilingue

        response.headers['Content-Disposition'] = f'attachment; filename=agenda_semainier_2026_multilang_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'

        

        return response

    

    except Exception as e:

        error_msg = str(e)

        error_trace = traceback.format_exc()

        

        # #region agent log

        with open(log_path, 'a', encoding='utf-8') as f:

            f.write(json.dumps({

                'timestamp': datetime.now().isoformat(),

                'location': 'projet18_routes.py:export_pdf_multilang:error',

                'message': 'Erreur generation PDF multilingue',

                'data': {'error': error_msg, 'traceback': error_trace},

                'sessionId': 'debug-session',

                'runId': 'run1',

                'hypothesisId': 'E'

            }) + '\n')

        # #endregion

        

        raise



@projet18_bp.route('/export-pdf-multilang-style2')

def export_pdf_multilang_style2():

    """Exporte l'agenda semainier en PDF version multilingue (arabe et anglais) - À développer séparément"""

    # ⚠️ IMPORTANT: Cette fonction export_pdf_multilang_style2() est la SEULE fonction qui peut être modifiée

    # Les fonctions export_pdf() et export_pdf_multilang() NE DOIVENT JAMAIS être modifiées

    # Toutes les modifications demandées doivent être appliquées UNIQUEMENT dans cette fonction

    import json

    import traceback

    from pathlib import Path

    from datetime import datetime

    from flask import make_response

    # Utiliser un chemin absolu pour éviter les problèmes avec __file__
    import os
    log_dir = Path('C:/Apps/.cursor')
    log_path = log_dir / 'debug.log'
    
    # Créer le dossier .cursor s'il n'existe pas
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass  # Ignorer les erreurs de création de dossier

    # Log très tôt pour vérifier que le code est exécuté
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'timestamp': datetime.now().isoformat(),
                'location': 'projet18_routes.py:export_pdf_multilang_style2:very_start',
                'message': 'DEBUT FONCTION - Code nouveau charge',
                'sessionId': 'debug-session',
                'runId': 'run1'
            }) + '\n')
    except Exception:
        pass  # Ignorer les erreurs de log

    try:

        # Log début

        # #region agent log

        try:
            with open(log_path, 'a', encoding='utf-8') as f:

                f.write(json.dumps({

                    'timestamp': datetime.now().isoformat(),

                    'location': 'projet18_routes.py:export_pdf_multilang_style2:start',

                    'message': 'Debut export PDF multilingue',

                    'sessionId': 'debug-session',

                    'runId': 'run1',

                    'hypothesisId': 'A'

                }) + '\n')
        except:
            pass  # Ignorer les erreurs d'écriture de log

        # #endregion

        

        from reportlab.lib.pagesizes import A4, landscape

        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        from reportlab.lib.units import cm, mm

        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

        from reportlab.lib import colors

        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

        from calendar import monthrange

        from reportlab.pdfbase import pdfmetrics

        from reportlab.pdfbase.ttfonts import TTFont

        import os

        

        # Fonction pour corriger l'ordre du texte arabe (RTL) en préservant les connexions entre lettres

        def fix_arabic_text(text):

            """Corrige l'ordre du texte arabe pour l'affichage RTL dans ReportLab en préservant les connexions"""

            if not text:

                return text

            

            # #region agent log

            try:

                with open(log_path, 'a', encoding='utf-8') as f:

                    f.write(json.dumps({

                        'timestamp': datetime.now().isoformat(),

                        'location': 'projet18_routes.py:fix_arabic_text:start',

                        'message': 'Correction texte arabe',

                        'data': {'text_original': text, 'text_length': len(text)},

                        'sessionId': 'debug-session',

                        'runId': 'run1',

                        'hypothesisId': 'A'

                    }) + '\n')

            except:

                pass

            # #endregion

            

            try:

                # Solution correcte pour ReportLab : reshaper puis inverser pour l'ordre visuel

                # ReportLab affiche le texte dans l'ordre logique (de gauche à droite)

                # Pour l'arabe, il faut inverser l'ordre après le reshaping pour obtenir l'ordre visuel correct

                import arabic_reshaper

                

                # Étape 1: Reshaper pour obtenir les bonnes formes contextuelles (lettres attachées)

                reshaper = arabic_reshaper.ArabicReshaper()

                reshaped_text = reshaper.reshape(text)

                

                # Étape 2: Inverser l'ordre des caractères pour l'affichage visuel RTL

                # ReportLab affiche de gauche à droite, donc on inverse pour obtenir l'ordre RTL correct

                visual_text = reshaped_text[::-1]

                

                # Retourner le texte visual sans marqueur RTL (qui cause des carrés)

                result = visual_text

                

                # #region agent log

                try:

                    with open(log_path, 'a', encoding='utf-8') as f:

                        f.write(json.dumps({

                            'timestamp': datetime.now().isoformat(),

                            'location': 'projet18_routes.py:fix_arabic_text:success',

                            'message': 'Utilise reshape puis inversion (ordre visuel correct pour ReportLab)',

                            'data': {

                                'text_original': text,

                                'text_reshaped': reshaped_text,

                                'text_visual': visual_text,

                                'text_result': result,

                                'length_original': len(text),

                                'length_reshaped': len(reshaped_text),

                                'length_visual': len(visual_text),

                                'length_result': len(result)

                            },

                            'sessionId': 'debug-session',

                            'runId': 'run1',

                            'hypothesisId': 'A'

                        }) + '\n')

                except:

                    pass

                # #endregion

                return result

            except ImportError as e:

                # #region agent log

                try:

                    with open(log_path, 'a', encoding='utf-8') as f:

                        f.write(json.dumps({

                            'timestamp': datetime.now().isoformat(),

                            'location': 'projet18_routes.py:fix_arabic_text:import_error',

                            'message': 'Erreur import bidi/reshaper',

                            'data': {'error': str(e)},

                            'sessionId': 'debug-session',

                            'runId': 'run1',

                            'hypothesisId': 'B'

                        }) + '\n')

                except:

                    pass

                # #endregion

                # Si arabic_reshaper n'est pas disponible, utiliser le texte original

                # La police TTF devrait gérer les formes contextuelles de base

                pass

                

            # Si arabic_reshaper n'est pas disponible, utiliser le texte original sans modification

            # La police TTF devrait gérer les formes contextuelles de base

            has_arabic = any('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F' or 

                            '\u08A0' <= c <= '\u08FF' or '\uFB50' <= c <= '\uFDFF' or 

                            '\uFE70' <= c <= '\uFEFF' for c in text)

            if has_arabic:

                # Retourner le texte original sans marqueur RTL (qui cause des carrés)

                # La police TTF (Arial Unicode MS, Tahoma, etc.) devrait gérer les formes contextuelles

                result = text

                # #region agent log

                try:

                    with open(log_path, 'a', encoding='utf-8') as f:

                        f.write(json.dumps({

                            'timestamp': datetime.now().isoformat(),

                            'location': 'projet18_routes.py:fix_arabic_text:fallback',

                            'message': 'Utilise texte original (arabic_reshaper non disponible)',

                            'data': {'text_result': result, 'has_arabic': has_arabic},

                            'sessionId': 'debug-session',

                            'runId': 'run1',

                            'hypothesisId': 'B'

                        }) + '\n')

                except:

                    pass

                # #endregion

                return result

            # #region agent log

            try:

                with open(log_path, 'a', encoding='utf-8') as f:

                    f.write(json.dumps({

                        'timestamp': datetime.now().isoformat(),

                        'location': 'projet18_routes.py:fix_arabic_text:no_arabic',

                        'message': 'Pas de caractères arabes',

                        'data': {'text': text},

                        'sessionId': 'debug-session',

                        'runId': 'run1',

                        'hypothesisId': 'C'

                    }) + '\n')

            except:

                pass

            # #endregion

            return text

        

        # Charger la police Square721 BT (Regular et Bold) pour le texte latin/chiffres

        # ET une police qui supporte l'arabe pour le texte arabe

        square721_font_name = 'Helvetica'  # Par défaut en cas d'erreur

        square721_bold_font_name = 'Helvetica-Bold'  # Par défaut en cas d'erreur

        arabic_font_name = 'Helvetica'  # Par défaut (ne supporte pas l'arabe)

        

        # D'abord charger une police qui supporte l'arabe (priorité)

        try:

            # Essayer Arial Unicode MS (souvent disponible sur Windows et supporte l'arabe)

            arial_unicode_paths = [

                'C:/Windows/Fonts/ARIALUNI.TTF',

                'C:/Windows/Fonts/arialuni.ttf',

                'C:/Windows/Fonts/ARIALUNI.OTF',

            ]

            for path in arial_unicode_paths:

                if os.path.exists(path):

                    try:

                        pdfmetrics.registerFont(TTFont('ArialUnicodeMS', path))

                        arabic_font_name = 'ArialUnicodeMS'

                        break

                    except Exception as e:

                        try:

                            with open(log_path, 'a', encoding='utf-8') as f:

                                f.write(json.dumps({

                                    'timestamp': datetime.now().isoformat(),

                                    'location': 'projet18_routes.py:export_pdf_multilang:arial_unicode_error',

                                    'message': f'Erreur chargement Arial Unicode: {str(e)}',

                                    'path': path,

                                    'sessionId': 'debug-session',

                                    'runId': 'run1'

                                }) + '\n')

                        except:

                            pass

                        pass

            

            # Si Arial Unicode MS n'est pas disponible, essayer Tahoma (supporte l'arabe)

            if arabic_font_name == 'Helvetica':

                tahoma_paths = [

                    'C:/Windows/Fonts/tahoma.ttf',

                    'C:/Windows/Fonts/Tahoma.ttf',

                ]

                for path in tahoma_paths:

                    if os.path.exists(path):

                        try:

                            pdfmetrics.registerFont(TTFont('Tahoma', path))

                            arabic_font_name = 'Tahoma'

                            break

                        except:

                            pass

            

            # Si Tahoma n'est pas disponible, essayer DejaVuSans (supporte l'arabe)

            if arabic_font_name == 'Helvetica':

                dejavu_paths = [

                    'C:/Windows/Fonts/DejaVuSans.ttf',

                    'C:/Windows/Fonts/dejavu-sans.ttf',

                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',

                    '/usr/share/fonts/TTF/DejaVuSans.ttf'

                ]

                for path in dejavu_paths:

                    if os.path.exists(path):

                        try:

                            pdfmetrics.registerFont(TTFont('DejaVuSans', path))

                            arabic_font_name = 'DejaVuSans'

                            break

                        except:

                            pass

        except Exception as e:

            # En cas d'erreur, utiliser Helvetica (texte arabe ne s'affichera pas correctement)

            arabic_font_name = 'Helvetica'

        

        # Ensuite charger Square721 BT (pour le texte latin/chiffres)

        try:

            # Chemins possibles pour Square721 BT (chercher dans tous les dossiers possibles)

            # Bitstream est l'éditeur de Square721 BT, donc chercher aussi sous ce nom

            square721_paths = [

                'C:/Windows/Fonts/SQUA721N.TTF',  # Square721 BT Normal

                'C:/Windows/Fonts/squa721n.ttf',

                'C:/Windows/Fonts/SQUA721R.TTF',  # Square721 BT Regular

                'C:/Windows/Fonts/squa721r.ttf',

                'C:/Windows/Fonts/SQUA721.TTF',

                'C:/Windows/Fonts/squa721.ttf',

                'C:/Windows/Fonts/SQUA721N.OTF',

                'C:/Windows/Fonts/squa721n.otf',

                # Variantes possibles

                'C:/Windows/Fonts/SQUARE721.TTF',

                'C:/Windows/Fonts/square721.ttf',

                'C:/Windows/Fonts/SQUARE721N.TTF',

                'C:/Windows/Fonts/square721n.ttf',

            ]

            square721_bold_paths = [

                'C:/Windows/Fonts/SQUA721B.TTF',  # Square721 BT Bold

                'C:/Windows/Fonts/squa721b.ttf',

                'C:/Windows/Fonts/SQUA721D.TTF',  # Square721 BT Demi

                'C:/Windows/Fonts/squa721d.ttf',

                'C:/Windows/Fonts/SQUA721B.OTF',

                'C:/Windows/Fonts/squa721b.otf',

                # Variantes possibles

                'C:/Windows/Fonts/SQUARE721B.TTF',

                'C:/Windows/Fonts/square721b.ttf',

                'C:/Windows/Fonts/SQUARE721D.TTF',

                'C:/Windows/Fonts/square721d.ttf',

            ]

            

            # Recherche dynamique dans le dossier Fonts si les chemins standards ne fonctionnent pas

            if square721_font_name == 'Helvetica':

                try:

                    fonts_dir = 'C:/Windows/Fonts'

                    if os.path.exists(fonts_dir):

                        for font_file in os.listdir(fonts_dir):

                            font_lower = font_file.lower()

                            if ('square' in font_lower or 'squa' in font_lower or '721' in font_lower) and (font_lower.endswith('.ttf') or font_lower.endswith('.otf')):

                                if 'bold' not in font_lower and 'demi' not in font_lower and 'b' not in font_lower[-5:]:

                                    font_path = os.path.join(fonts_dir, font_file)

                                    try:

                                        pdfmetrics.registerFont(TTFont('Square721BT', font_path))

                                        square721_font_name = 'Square721BT'

                                        break

                                    except:

                                        pass

                except:

                    pass

            

            if square721_bold_font_name == 'Helvetica-Bold':

                try:

                    fonts_dir = 'C:/Windows/Fonts'

                    if os.path.exists(fonts_dir):

                        for font_file in os.listdir(fonts_dir):

                            font_lower = font_file.lower()

                            if ('square' in font_lower or 'squa' in font_lower or '721' in font_lower) and (font_lower.endswith('.ttf') or font_lower.endswith('.otf')):

                                if 'bold' in font_lower or 'demi' in font_lower or font_lower[-5:-4] == 'b' or font_lower[-5:-4] == 'd':

                                    font_path = os.path.join(fonts_dir, font_file)

                                    try:

                                        pdfmetrics.registerFont(TTFont('Square721BT-Bold', font_path))

                                        square721_bold_font_name = 'Square721BT-Bold'

                                        break

                                    except:

                                        pass

                except:

                    pass

            

            # Charger Square721 BT Regular

            for path in square721_paths:

                if os.path.exists(path):

                    try:

                        pdfmetrics.registerFont(TTFont('Square721BT', path))

                        square721_font_name = 'Square721BT'

                        break

                    except Exception as e:

                        # Log l'erreur pour debug

                        try:

                            with open(log_path, 'a', encoding='utf-8') as f:

                                f.write(json.dumps({

                                    'timestamp': datetime.now().isoformat(),

                                    'location': 'projet18_routes.py:export_pdf_multilang:square721_error',

                                    'message': f'Erreur chargement Square721 BT: {str(e)}',

                                    'path': path,

                                    'sessionId': 'debug-session',

                                    'runId': 'run1'

                                }) + '\n')

                        except:

                            pass

                        pass

            

            # Charger Square721 BT Bold

            for path in square721_bold_paths:

                if os.path.exists(path):

                    try:

                        pdfmetrics.registerFont(TTFont('Square721BT-Bold', path))

                        square721_bold_font_name = 'Square721BT-Bold'

                        break

                    except:

                        pass

            

            # Si Bold n'est pas trouvé, utiliser la même police que Regular

            if square721_bold_font_name == 'Helvetica-Bold' and square721_font_name != 'Helvetica':

                square721_bold_font_name = square721_font_name

        except Exception as e:

            # En cas d'erreur, utiliser la police arabe comeme fallback

            if square721_font_name == 'Helvetica':

                square721_font_name = arabic_font_name

            if square721_bold_font_name == 'Helvetica-Bold':

                square721_bold_font_name = arabic_font_name

        

        # Si Square721 BT n'est pas trouvé, utiliser la police arabe pour tout

        # (la police arabe supporte aussi le latin, donc c'est acceptable)

        # Mais on essaie d'abord de créer une version Bold de la police arabe

        if square721_font_name == 'Helvetica':

            square721_font_name = arabic_font_name

            # Essayer de créer une version Bold de la police arabe

            if arabic_font_name == 'ArialUnicodeMS':

                try:

                    # Arial Unicode MS n'a pas de version Bold séparée, utiliser la même

                    square721_bold_font_name = arabic_font_name

                except:

                    square721_bold_font_name = arabic_font_name

            elif arabic_font_name == 'Tahoma':

                try:

                    # Essayer Tahoma Bold

                    tahoma_bold_paths = [

                        'C:/Windows/Fonts/tahomabd.ttf',

                        'C:/Windows/Fonts/TahomaBd.ttf',

                    ]

                    for path in tahoma_bold_paths:

                        if os.path.exists(path):

                            try:

                                pdfmetrics.registerFont(TTFont('Tahoma-Bold', path))

                                square721_bold_font_name = 'Tahoma-Bold'

                                break

                            except:

                                pass

                    if square721_bold_font_name == 'Helvetica-Bold':

                        square721_bold_font_name = arabic_font_name

                except:

                    square721_bold_font_name = arabic_font_name

            else:

                square721_bold_font_name = arabic_font_name

        elif square721_bold_font_name == 'Helvetica-Bold':

            square721_bold_font_name = square721_font_name

        

        # Log les polices chargées

        try:

            with open(log_path, 'a', encoding='utf-8') as f:

                f.write(json.dumps({

                    'timestamp': datetime.now().isoformat(),

                    'location': 'projet18_routes.py:export_pdf_multilang:fonts_loaded',

                    'message': 'Polices chargees',

                    'data': {

                        'square721_font': square721_font_name,

                        'square721_bold_font': square721_bold_font_name,

                        'arabic_font': arabic_font_name

                    },

                    'sessionId': 'debug-session',

                    'runId': 'run1'

                }) + '\n')

        except:

            pass

        # Log avant get_semaines_2026
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'location': 'projet18_routes.py:export_pdf_multilang_style2:before_get_semaines',
                    'message': 'Avant get_semaines_2026',
                    'sessionId': 'debug-session',
                    'runId': 'run1'
                }) + '\n')
        except:
            pass

        semaines = get_semaines_2026()

        # Log après get_semaines_2026
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'location': 'projet18_routes.py:export_pdf_multilang_style2:after_get_semaines',
                    'message': 'Apres get_semaines_2026',
                    'data': {'nb_semaines': len(semaines)},
                    'sessionId': 'debug-session',
                    'runId': 'run1'
                }) + '\n')
        except:
            pass

        # Ajouter la semaine 53 (du lundi 28/12/2026 au dimanche 03/01/2027)

        semaine_53 = {

            'numero': 53,

            'lundi': datetime(2026, 12, 28),

            'mardi': datetime(2026, 12, 29),

            'mercredi': datetime(2026, 12, 30),

            'jeudi': datetime(2026, 12, 31),

            'vendredi': datetime(2027, 1, 1),

            'samedi': datetime(2027, 1, 2),

            'dimanche': datetime(2027, 1, 3),

        }

        semaines.append(semaine_53)

        

        # Log nombre de semaines

        try:
            with open(log_path, 'a', encoding='utf-8') as f:

                f.write(json.dumps({

                    'timestamp': datetime.now().isoformat(),

                    'location': 'projet18_routes.py:export_pdf_multilang_style2:semaines',

                    'message': 'Nombre de semaines',

                    'data': {'nb_semaines': len(semaines)},

                    'sessionId': 'debug-session',

                    'runId': 'run1'

                }) + '\n')
        except:
            pass  # Ignorer les erreurs d'écriture de log

        # Log avant création buffer
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'location': 'projet18_routes.py:export_pdf_multilang_style2:before_buffer',
                    'message': 'Avant creation buffer',
                    'sessionId': 'debug-session',
                    'runId': 'run1'
                }) + '\n')
        except:
            pass

        buffer = BytesIO()

        # Format A4 portrait

        doc = SimpleDocTemplate(

            buffer,

            pagesize=A4,  # Portrait au lieu de landscape

            rightMargin=0.5*cm,

            leftMargin=0.5*cm,

            topMargin=0.5*cm,

            bottomMargin=0.5*cm

        )

        

        # Callbacks pour dessiner les rectangles arrondis autour des blocs

        # Callbacks pour dessiner les rectangles arrondis autour des blocs spécifiés

        # Dictionnaire pour mapper le numéro de page au mois correspondant

        # Chaque semaine génère 2 pages : page 1 (impaire) = semaine 1, page 3 = semaine 2, etc.

        page_to_mois = {}  # {numéro_page: mois}

        

        def draw_rounded_rects_page1(canvas, doc):

            """Dessine des rectangles arrondis autour des blocs de la page 1 (Lundi, Mardi, Mercredi + mini-calendrier)"""

            from reportlab.lib.units import cm

            from reportlab.lib import colors

            

            # Paramètres des rectangles arrondis

            radius = 0.2*cm  # Rayon des coins arrondis

            stroke_width = 0.5  # Épaisseur du trait (réduite pour des lignes plus fines)

            # Couleur des cadres (jours + mini-calendrier) pour multilingue style 2 : gris foncé au lieu de noir

            stroke_color = colors.HexColor('#666666')

            

            # Marges de la page

            left_margin = 0.5*cm

            top_margin = 0.5*cm

            col_width = 5.5*cm

            padding = 0.1*cm  # Padding autour des rectangles

            

            # Hauteurs approximatives (basées sur la structure)

            semaine_height = 0.7*cm

            header_height = 2.7*cm

            ligne_vide_height = 0.85*cm  # 24 points en cm

            ligne_horaire_height = 0.85*cm  # 24 points en cm (2 lignes de 12 points)

            nb_lignes_horaires = 13  # 8h à 20h

            cal_height = 2.0*cm  # Hauteur approximative du mini-calendrier

            

            # Calculer la position Y (dans ReportLab, Y=0 est en bas de la page)

            page_height = doc.pagesize[1]  # Hauteur de la page A4 (29.7cm pour A4)

            

            # Dessiner les rectangles autour des blocs header (date/jour/jour férié)

            # Position depuis le haut : top_margin + semaine_height

            # Position Y depuis le bas : page_height - top_margin - semaine_height - header_height

            # Décaler vers la droite et réduire la largeur pour éeviter les chevauchements

            x_offset = 1.8*cm  # Décalage vers la droite (très très léger)

            width_reduction = 0.4*cm  # Réduction de largeur (augmentée légèrement)

            for col in range(3):

                # Décaler les cadres des jours (lundi à samedi) vers la droite de 0,25 cm

                x = left_margin + col * col_width - padding + x_offset + 0.25*cm

                y = page_height - top_margin - semaine_height - header_height - padding

                # Réduire la longueur horizontale des cadres jours de 0,2 cm (garder le bord gauche fixe)

                width = col_width + 2*padding - width_reduction - 0.2*cm

                height = header_height - 2*padding

                

                # Dessiner le rectangle arrondi (cadre jours), puis ouvrir le haut :

                # - on dessine un roundRect complet

                # - puis on masque toute la bande supérieure (y+height-radius -> y+height)

                canvas.setStrokeColor(stroke_color)

                canvas.setLineWidth(stroke_width)

                canvas.roundRect(x, y, width, height, radius, stroke=1, fill=0)

                # Masquer la partie supérieure (ligne du haut + coins arrondis supérieurs)

                canvas.setFillColor(colors.white)

                canvas.setStrokeColor(colors.white)

                canvas.rect(

                    x - 0.5,

                    y + height - radius,

                    width + 1.0,

                    radius + 1.0,

                    stroke=0,

                    fill=1,

                )

            

            # Dessiner le rectangle autour du mini-calendrier (colonne 0, dernière ligne)

            # Position depuis le haut : top_margin + semaine_height + header_height + ligne_vide_height + nb_lignes_horaires * ligne_horaire_height

            # Position Y depuis le bas : page_height - (top_margin + semaine_height + header_height + ligne_vide_height + nb_lignes_horaires * ligne_horaire_height + cal_height)

            # Augmenter la hauteur uniquement par le haut, en conservant la position du bas

            height_increase_top = 1.7*cm  # Augmentation de la hauteur par le haut (someme de bottom + top précédents pour conserver la hauteur totale)

            # Augmenter la hauteur du cadre uniquement pour mars (3), août (8) et novembre (11)

            # Garder la position de la ligne du haut (cal_y_frame) et décaler la ligne du bas vers le bas

            # Utiliser le numéro de page pour déterminer le mois

            page_num = canvas.getPageNumber()

            mois_actuel = page_to_mois.get(page_num, 1)  # Par défaut janvier si non trouvé

            if mois_actuel in [3, 8, 11]:  # Mars, août, novembre

                height_increase_bottom = 0.5*cm  # Augmentation de la hauteur par le bas (décaler la ligne du bas vers le bas)

            else:

                height_increase_bottom = 0  # Pas d'augmentation pour les autres mois

            # Décaler très très légèrement vers la gauche

            cal_x_offset = 1.8*cm  # Décalage vers la droite (réduit pour décaler vers la gauche)

            cal_x = left_margin - padding + cal_x_offset

            # Ajuster cal_y pour augmenter uniquement par le haut (décaler vers le haut pour conserver la position du bas)

            # La position du bas reste : page_height - top_margin - semaine_height - header_height - ligne_vide_height - nb_lignes_horaires * ligne_horaire_height - cal_height - padding

            # Décaler très légèrement vers le haut (augmenter Y pour décaler vers le haut dans ReportLab)

            vertical_offset = 0.1*cm  # Décalage très léger vers le haut

            cal_y = page_height - top_margin - semaine_height - header_height - ligne_vide_height - nb_lignes_horaires * ligne_horaire_height - cal_height - padding - height_increase_top + vertical_offset

            cal_width = col_width + 2*padding

            # Augmenter cal_height_rect en ajoutant height_increase_bottom (la ligne du haut reste fixe, la ligne du bas descend)

            cal_height_rect = cal_height - 2*padding + height_increase_top + height_increase_bottom

            

            # Anciennement : dessin du cadre autour du mini-calendrier.

            # Pour la version multilingue style 2, on supprime complètement le cadre du mini-calendrier.

            

            # Dessiner le rectangle bleu autour de la semaine courante dans le mini-calendrier

            page_num = canvas.getPageNumber()

            semaine_encadree_key = f'semaine_encadree_{page_num}'

            semaine_encadree_row = page_to_mois.get(semaine_encadree_key)
            
            # Récupérer le mois de la page pour déterminer si on utilise le système spécial
            mois_page = page_to_mois.get(page_num)
            
            # Récupérer le numéro de semaine dans le mois pour septembre, novembre et décembre
            numero_semaine_mois_key = f'numero_semaine_mois_{page_num}'
            numero_semaine_mois = page_to_mois.get(numero_semaine_mois_key)

            

            if semaine_encadree_row is not None:

                # Position du mini-calendrier (même calcul que pour le cadre supprimé)

                cal_x_offset = 1.8*cm

                cal_x_start = left_margin + cal_x_offset

                cal_width_total = 7 * 0.73*cm  # 7 colonnes de 0.73cm (largeur réduite de 0.2cm)

                

                # Hauteur d'une ligne de dates (approximative)

                ligne_date_height = 0.4*cm

                

                # Position Y de la première ligne de dates (ligne 2 du tableau, après mois et jours)
                # Le mini-calendrier commence après les heures
                # Ajuster pour la nouvelle hauteur de la ligne vide : 15 points au lieu de 24 points
                # Différence : 24 - 15 = 9 points = 0.32cm (le calendrier commence plus haut)
                
                ligne_vide_height_reelle = 15 / 28.35 * cm  # Hauteur réelle de la ligne vide (15 points en cm)
                ligne_vide_height_ancienne = 24 / 28.35 * cm  # Ancienne hauteur (24 points en cm)
                difference_ligne_vide = ligne_vide_height_ancienne - ligne_vide_height_reelle  # Différence = 0.32cm
                
                # Position Y du haut du mini-calendrier (ajustée pour la nouvelle hauteur de ligne vide)
                cal_y_top_base = page_height - top_margin - semaine_height - header_height - ligne_vide_height_reelle - nb_lignes_horaires * ligne_horaire_height
                
                # Hauteurs des lignes du mini-calendrier
                cal_ligne_mois_height = 0.5*cm  # Hauteur approximative de la ligne de mois
                cal_ligne_jours_height = 0.4*cm  # Hauteur approximative de la ligne de jours
                
                # Position Y de la première ligne de dates (ligne 2 du tableau)
                # = position du haut du calendrier - hauteur ligne mois - hauteur ligne jours
                cal_y_premiere_ligne_dates = cal_y_top_base - cal_ligne_mois_height - cal_ligne_jours_height
                
                # Calculer la position Y réelle de la ligne de la semaine encadrée
                # Ligne 0 = mois, ligne 1 = jours, ligne 2+ = dates
                # On encadre la ligne (semaine_encadree_row + 2) du tableau
                # Premier cadre (semaine_encadree_row == 0) : décalage fixe de 1.57cm (garder fixe - NE JAMAIS MODIFIER)
                # Augmenter la distance entre les cadres de manière cumulative :
                # - Distance entre cadre n°1 et n°2 : +0.03cm
                # - Distance entre cadre n°2 et n°3 : +0.06cm
                # - Distance entre cadre n°3 et n°4 : +0.09cm
                # - Distance entre cadre n°4 et n°5 : +0.12cm
                decalage_base = 1.0*cm + 0.5*cm + 0.2*cm - 0.1*cm - 0.05*cm - 0.02*cm  # 1.57cm
                decalage_global = 0.04*cm  # Décalage global de tous les cadres vers le bas (0.03cm + 0.01cm)
                
                # Décalage supplémentaire pour mars, août et novembre : décaler tous les cadres vers le haut de 0.06cm (0.03cm + 0.03cm)
                decalage_mois_speciaux = 0
                if mois_page in [3, 8, 11]:  # Mars, août, novembre
                    decalage_mois_speciaux = 0.06*cm  # Décaler vers le haut (ajouter au Y)
                
                # Calculer la position du premier cadre UNE SEULE FOIS (position fixe - ne jamais modifier)
                cal_y_rect_top_premier = cal_y_premiere_ligne_dates - decalage_base - decalage_global + decalage_mois_speciaux
                
                # Calculer la position des autres cadres par rapport au premier cadre
                # Distances ajustées selon les spécifications :
                # - Entre cadre 1 et 2 : 0.06cm (réduit de 0.01cm supplémentaire)
                # - Entre cadre 2 et 3 : 0.12cm
                # - Entre cadre 3 et 4 : 0.10cm (réduit de 0.03cm)
                # - Entre cadre 4 et 5 : 0.06cm (augmenté de 0.03cm)
                if semaine_encadree_row == 0:
                    # Premier cadre : position fixe avec décalage global
                    cal_y_rect_top = cal_y_rect_top_premier
                elif semaine_encadree_row == 1:
                    # Cadre 2 : position du premier cadre - 1 ligne - 0.06cm (distance entre cadre 1 et 2 réduite)
                    cal_y_rect_top = cal_y_rect_top_premier - 1 * ligne_date_height - 0.06*cm
                elif semaine_encadree_row == 2:
                    # Cadre 3 : position du premier cadre - 2 lignes - 0.18cm (0.06 + 0.12 cumulatif)
                    cal_y_rect_top = cal_y_rect_top_premier - 2 * ligne_date_height - 0.06*cm - 0.12*cm
                elif semaine_encadree_row == 3:
                    # Cadre 4 : position du premier cadre - 3 lignes - 0.28cm (0.06 + 0.12 + 0.10 cumulatif)
                    cal_y_rect_top = cal_y_rect_top_premier - 3 * ligne_date_height - 0.06*cm - 0.12*cm - 0.10*cm
                elif semaine_encadree_row == 4:
                    # Cadre 5 : position du premier cadre - 4 lignes - 0.34cm (0.06 + 0.12 + 0.10 + 0.06 cumulatif)
                    cal_y_rect_top = cal_y_rect_top_premier - 4 * ligne_date_height - 0.06*cm - 0.12*cm - 0.10*cm - 0.06*cm
                else:
                    # Autres cadres : position du premier cadre - nombre de lignes
                    cal_y_rect_top = cal_y_rect_top_premier - semaine_encadree_row * ligne_date_height
                
                cal_y_rect_bottom = cal_y_rect_top - ligne_date_height

                # Décaler vers la droite de 0.15cm (0.25cm - 0.1cm vers la gauche = 0.15cm net vers la droite)

                cal_x_start_rect = cal_x_start + 0.15*cm

                

                # Dessiner le rectangle bleu fin autour de la semaine

                canvas.setStrokeColor(colors.HexColor('#004499'))  # Bleu clairement plus foncé que #0066CC

                canvas.setLineWidth(0.5)  # Épaisseur fine (modifiable)

                canvas.rect(

                    cal_x_start_rect,

                    cal_y_rect_bottom,

                    cal_width_total,

                    ligne_date_height,

                    stroke=1,

                    fill=0

                )

        

        def draw_rounded_rects_page2(canvas, doc):

            """Dessine des rectangles arrondis autour des blocs de la page 2 (Jeudi, Vendredi, Samedi + Dimanche)"""

            from reportlab.lib.units import cm

            from reportlab.lib import colors

            

            # Paramètres des rectangles arrondis

            radius = 0.2*cm  # Rayon des coins arrondis

            stroke_width = 0.5  # Épaisseur du trait (réduite pour des lignes plus fines)

            # Couleur des cadres (jours jeudi-dimanche) pour multilingue style 2 : gris foncé au lieu de noir

            stroke_color = colors.HexColor('#666666')

            

            # Marges de la page

            left_margin = 0.5*cm

            top_margin = 0.5*cm

            col_width = 5.5*cm

            padding = 0.1*cm  # Padding autour des rectangles

            

            # Hauteurs approximatives (basées sur la structure)

            semaine_height = 0.7*cm

            header_height = 2.7*cm

            ligne_vide_height = 0.85*cm  # 24 points en cm

            ligne_horaire_height = 0.85*cm  # 24 points en cm (2 lignes de 12 points)

            nb_lignes_horaires = 13  # 8h à 20h

            

            # Calculer la position Y (dans ReportLab, Y=0 est en bas de la page)

            page_height = doc.pagesize[1]  # Hauteur de la page A4 (29.7cm pour A4)

            

            # Dessiner les rectangles autour des blocs header (date/jour/jour férié)

            # Position depuis le haut : top_margin + semaine_height

            # Position Y depuis le bas : page_height - top_margin - semaine_height - header_height

            # Décaler vers la droite et réduire la largeur pour éeviter les chevauchements

            x_offset = 1.8*cm  # Décalage vers la droite (très très léger)

            width_reduction = 0.4*cm  # Réduction de largeur (augmentée légèrement)

            for col in range(3):

                # Décaler les cadres des jours (jeudi à samedi) vers la droite de 0,25 cm

                x = left_margin + col * col_width - padding + x_offset + 0.25*cm

                y = page_height - top_margin - semaine_height - header_height - padding

                # Réduire la longueur horizontale des cadres jours de 0,2 cm (garder le bord gauche fixe)

                width = col_width + 2*padding - width_reduction - 0.2*cm

                height = header_height - 2*padding

                

                # Dessiner le rectangle arrondi (cadre jours), puis ouvrir le haut

                canvas.setStrokeColor(stroke_color)

                canvas.setLineWidth(stroke_width)

                canvas.roundRect(x, y, width, height, radius, stroke=1, fill=0)

                canvas.setFillColor(colors.white)

                canvas.setStrokeColor(colors.white)

                canvas.rect(

                    x - 0.5,

                    y + height - radius,

                    width + 1.0,

                    radius + 1.0,

                    stroke=0,

                    fill=1,

                )

            

            # Dessiner le rectangle autour du dimanche (colonne 0, dernière ligne de la page 2)

            # Appliquer exactement les mêmes paramètres de position et dimension que le mini-calendrier

            # Utiliser exactement les mêmes valeurs que le mini-calendrier pour avoir la même hauteur et le même alignement

            cal_height = 2.0*cm  # Même hauteur de base que le mini-calendrier (au lieu de header_height)

            height_increase_top = 1.7*cm  # Même augmentation de hauteur par le haut que le mini-calendrier

            cal_x_offset = 1.8*cm  # Même décalage horizontal que le mini-calendrier

            vertical_offset = 0.1*cm  # Même décalage vertical vers le haut que le mini-calendrier

            dimanche_x = left_margin - padding + cal_x_offset  # Même position X que le mini-calendrier

            # Exactement le même calcul de position Y que le mini-calendrier

            dimanche_y = page_height - top_margin - semaine_height - header_height - ligne_vide_height - nb_lignes_horaires * ligne_horaire_height - cal_height - padding - height_increase_top + vertical_offset

            dimanche_width = col_width + 2*padding  # Même largeur que le mini-calendrier

            dimanche_height = cal_height - 2*padding + height_increase_top  # Exactement la même hauteur que le mini-calendrier

            

            # Déplacer uniquement le cadre vers le bas de 0,60 cm (diminuer Y pour déplacer vers le bas dans ReportLab), puis décaler vers le haut de 0.25cm (0.2cm + 0.05cm)

            dimanche_y_frame = dimanche_y - 0.85*cm + 0.2*cm + 0.05*cm

            # Cadre du dimanche avec le nouveau modèle : rectangle ouvert en haut,

            # on garde seulement les coins arrondis inférieurs et les bordures gauche/droite/bas

            canvas.setStrokeColor(stroke_color)

            canvas.setLineWidth(stroke_width)

            canvas.roundRect(dimanche_x, dimanche_y_frame, dimanche_width, dimanche_height, radius, stroke=1, fill=0)

            # Masquer toute la bande supérieure (ligne + coins supérieurs)

            canvas.setFillColor(colors.white)

            canvas.setStrokeColor(colors.white)

            canvas.rect(

                dimanche_x - 0.5,

                dimanche_y_frame + dimanche_height - radius,

                dimanche_width + 1.0,

                radius + 1.0,

                stroke=0,

                fill=1,

            )

        

        # Ajouter les callbacks au document

        # Utiliser une fonction qui détermine quelle page on est

        def draw_rounded_rects(canvas, doc):

            """Dessine les rectangles arrondis selon la page"""

            # Utiliser canvas.getPageNumber() pour déterminer si c'est une page impaire (page 1) ou paire (page 2)

            # Les pages impaires sont les pages 1, 3, 5, etc. (page 1 de chaque semaine)

            # Les pages paires sont les pages 2, 4, 6, etc. (page 2 de chaque semaine)

            page_num = canvas.getPageNumber()

            if page_num % 2 == 1:

                # Page impaire = page 1 de la semaine (Lundi-Mercredi)

                draw_rounded_rects_page1(canvas, doc)

            else:

                # Page paire = page 2 de la semaine (Jeudi-Dimanche)

                draw_rounded_rects_page2(canvas, doc)

        

        doc.onFirstPage = draw_rounded_rects

        doc.onLaterPages = draw_rounded_rects



        

        styles = getSampleStyleSheet()

        

        # Styles selon le modèle Quo Vadis

        base_style = ParagraphStyle(

            'Base',

            parent=styles['Normal'],

            fontSize=9,

            textColor=colors.HexColor('#000000'),

            fontName=square721_font_name,

            leading=10

        )

        

        # Style pour les noms de jours (anglais/français)

        jour_nom_style = ParagraphStyle(

            'JourNom',

            parent=base_style,

            fontSize=9,

            fontName=square721_font_name,

            alignment=TA_LEFT

        )

        

        # Style pour les dates (grand, gras, noir selon l'image)

        date_style = ParagraphStyle(

            'Date',

            parent=base_style,

            fontSize=12,

            fontName=square721_bold_font_name,

            textColor=colors.HexColor('#000000'),  # Noir au lieu de bleu

            alignment=TA_RIGHT

        )

        

        # Style pour les numéros d'heures (gris clair, petit)

        # Utiliser un style qui ne coupe pas les nombres

        heure_style = ParagraphStyle(

            'Heure',

            parent=base_style,

            fontSize=7,

            textColor=colors.HexColor('#999999'),

            alignment=TA_LEFT,

            leading=14

        )

        

        # Style pour les lignes horaires (gris clair)

        # Utiliser un leading strictement égal à la hauteur de ligne pour garantir exactement 2 lignes

        ligne_horaire_style = ParagraphStyle(

            'LigneHoraire',

            parent=base_style,

            fontSize=8,

            textColor=colors.HexColor('#CCCCCC'),

            leading=8,  # Leading égal à la hauteur de ligne pour garantir exactement 2 lignes sans débordement

            spaceBefore=0,

            spaceAfter=0,

            leftIndent=0,

            rightIndent=0,

            firstLineIndent=0

        )

        

        # Style pour Dimanche

        dimanche_nom_style = ParagraphStyle(

            'DimancheNom',

            parent=base_style,

            fontSize=9,

            fontName=square721_font_name,

            alignment=TA_LEFT

        )

        

        dimanche_date_style = ParagraphStyle(

            'DimancheDate',

            parent=base_style,

            fontSize=12,

            fontName=square721_bold_font_name,

            textColor=colors.HexColor('#000000'),  # Noir au lieu de bleu

            alignment=TA_RIGHT

        )

        

        # Style pour les lignes de notes Dimanche

        ligne_note_style = ParagraphStyle(

            'LigneNote',

            parent=base_style,

            fontSize=8,

            textColor=colors.HexColor('#CCCCCC'),

            leading=14

        )

        

        # Style pour jours fériés

        ferie_style = ParagraphStyle(

            'Ferie',

            parent=base_style,

            fontSize=9,

            textColor=colors.HexColor('#FF0000'),

            fontName=square721_font_name,

            alignment=TA_CENTER

        )

        

        # Style pour le mini-calendrier

        cal_header_style = ParagraphStyle(

            'CalHeader',

            parent=base_style,

            fontSize=10,

            fontName=square721_bold_font_name,

            alignment=TA_CENTER

        )

        # Style pour le mois en arabe dans le mini-calendrier (multilingue style 2)

        cal_header_ar_style = ParagraphStyle(

            'CalHeaderArabicStyle2',

            parent=base_style,

            fontSize=10,

            fontName=arabic_font_name,

            alignment=TA_RIGHT

        )

        

        cal_semaine_style = ParagraphStyle(

            'CalSemaine',

            parent=base_style,

            fontSize=7,

            textColor=colors.HexColor('#999999'),

            alignment=TA_LEFT,

            leading=10

        )

        

        cal_date_style = ParagraphStyle(

            'CalDate',

            parent=base_style,

            fontSize=8,

            alignment=TA_CENTER,

            leading=10

        )

        

        # Style Bold dédié pour le numéro de semaine

        # Utiliser un style avec la police Bold directement (sans balise HTML)

        # Même leading que les autres pour un alignement parfait

        semaine_num_bold_style = ParagraphStyle(

            'SemaineNumBold',

            parent=base_style,

            fontSize=10,  # Légèrement plus grand pour plus de visibilité

            fontName=square721_bold_font_name,  # Police Bold directement dans le style

            textColor=colors.HexColor('#0066CC'),

            alignment=TA_LEFT,

            leading=14,  # Même leading que les autres styles

            spaceBefore=0,

            spaceAfter=0,

            firstLineIndent=0,

            leftIndent=0,

            rightIndent=0

        )

        

        # Style pour le texte "Semaine Week"

        # Même leading que le numéro pour un alignement parfait

        semaine_text_style = ParagraphStyle(

            'SemaineText',

            parent=base_style,

            fontSize=9,

            fontName=square721_font_name,

            alignment=TA_LEFT,

            leading=14,  # Même leading que le numéro

            spaceBefore=0,

            spaceAfter=0,

            firstLineIndent=0,

            leftIndent=0,

            rightIndent=0

        )

        

        # Style pour le texte arabe

        # Même leading que les autres pour un alignement parfait

        semaine_arabic_style = ParagraphStyle(

            'SemaineArabic',

            parent=base_style,

            fontSize=9,

            fontName=arabic_font_name,

            alignment=TA_LEFT,

            leading=14,  # Même leading que les autres

            spaceBefore=0,

            spaceAfter=0,

            firstLineIndent=0,

            leftIndent=0,

            rightIndent=0

        )

        

        # Largeur cible des champs de saisie pour chaque jour (lundi à samedi) – VERSION MULTILINGUE STYLE 2 :

        # largeur interne du cadre ≈ 5.1cm, on réduit volontairement les lignes de 0,3cm

        # pour qu'elles soient légèrement plus courtes que le cadre tout en restant alignées.

        # 5.1cm - 0.3cm = 4.8cm

        ligne_col_width = 4.8 * cm



        # Fonction utilitaire pour calculer automatiquement la longueur des lignes de saisie

        # en fonction de la largeur disponible, de la police et de la taille de police.

        # Cela permet de garder les lignes alignées exactement sur le cadre du jour.

        def build_ligne_underscore(col_width_points, right_padding_points=2, char="_"):

            """

            Retourne une chaîne de '_' dont la largeur correspond à la largeur disponible

            dans la colonne des champs de saisie, en tenant compte du padding droit.

            """

            # Largeur disponible = largeur de la colonne - padding droit

            available_width = max(col_width_points - right_padding_points, 0)

            # Utiliser la même police et taille que ligne_horaire_style (fontSize=8)

            char_width = pdfmetrics.stringWidth(char, ligne_horaire_style.fontName, ligne_horaire_style.fontSize)

            if char_width <= 0:

                return "_" * 1

            max_chars = int(available_width / char_width)

            return char * max(1, max_chars)



        elements = []

        

        # Dictionnaire des traductions des jours en arabe (pour version multilingue)

        jours_arabe = {

            'lundi': 'الإثنين',

            'mardi': 'الثلاثاء',

            'mercredi': 'الأربعاء',

            'jeudi': 'الخميس',

            'vendredi': 'الجمعة',

            'samedi': 'السبت',

            'dimanche': 'الأحد'

        }

        

        # Heures de 8h à 20h (13 lignes) -> 26 lignes de champs de saisie (2 lignes par heure)

        heures = list(range(8, 21))  # 8, 9, 10, ..., 20

        

        # Générer chaque semaine (2 pages par semaine)

        semaine_index = 0

        for semaine in semaines:

            # Calculer le mois de référence pour le mini-calendrier

            date_ref = semaine['jeudi'] if semaine['jeudi'] is not None else semaine['vendredi']

            if date_ref is None:

                date_ref = semaine['samedi'] if semaine['samedi'] is not None else datetime(2026, 1, 1)

            mois_ref = date_ref.month if date_ref else 1

            annee_ref = date_ref.year if date_ref else 2026

            

            # Mapper le numéro de page au mois correspondant (uniquement dans export_pdf_multilang_style2)

            # Chaque semaine génère 2 pages : page 1 (semaine 0), page 3 (semaine 1), page 5 (semaine 2), etc.

            # Page impaire (page 1 de la semaine) = 2 * semaine_index + 1

            page_num_page1 = 2 * semaine_index + 1

            page_to_mois[page_num_page1] = mois_ref

            # Page paire (page 2 de la semaine) = 2 * semaine_index + 2

            page_num_page2 = 2 * semaine_index + 2

            page_to_mois[page_num_page2] = mois_ref

            

            semaine_index += 1

            

            # ========== PAGE 1 : LUNDI / MARDI / MERCREDI + MINI-CALENDRIER ==========

            page1_data = []

            # Dictionnaire des traductions des jours en arabe (pour version multilingue)
            jours_arabe = {
                'lundi': 'الإثنين',
                'mardi': 'الثلاثاء',
                'mercredi': 'الأربعاء',
                'jeudi': 'الخميس',
                'vendredi': 'الجمعة',
                'samedi': 'السبت',
                'dimanche': 'الأحد'
            }

            # Ligne avec texte de la semaine en haut à gauche

            # Utiliser un seul Paragraph avec des balises font pour tout mettre sur une seule ligne

            semaine_num_formate1 = f"{semaine['numero']:02d}"

            semaine_ar1 = 'الأسبوع'

            # Un seul Paragraph avec des balises font pour changer les polices et le style

            # Le numéro utilise la police Bold directement dans la balise font

            semaine_row1 = [

                Paragraph(

                    f"<font face='{square721_font_name}'>Semaine Week  </font><font face='{square721_bold_font_name}' color='#004499' size='10'>{semaine_num_formate1}</font><font face='{arabic_font_name}'>  {fix_arabic_text(semaine_ar1)}</font>",

                    ParagraphStyle(

                        'SemaineHeader',

                        parent=base_style,

                        fontSize=9,

                        fontName=arabic_font_name,  # Police de base

                        alignment=TA_LEFT,

                        leading=14,

                        spaceBefore=0,

                        spaceAfter=0

                    )

                ),

                Paragraph("", base_style),  # Colonne vide

                Paragraph("", base_style)   # Colonne vide

            ]

            page1_data.append(semaine_row1)

            

            # En-têtes des 3 colonnes (Lundi, Mardi, Mercredi) - Version multilingue

            header_row = []

            jours_page1 = [

                ('lundi', 'Monday', 'Lundi'),

                ('mardi', 'Tuesday', 'Mardi'),

                ('mercredi', 'Wednesday', 'Mercredi')

            ]

            

            for jour_key, jour_en, jour_fr in jours_page1:

                date_jour = semaine[jour_key]

                if date_jour is not None:

                    # Format avec zéro devant si < 10 (01, 02, 03, 04)

                    date_formatee = f"{date_jour.day:02d}"

                    jour_ar = jours_arabe.get(jour_key, '')

                    

                    # Structure : Date en haut (grande), jours en bas (3 langues)

                    # Créer un tableau avec date en haut et jours en bas

                    try:

                        # Ligne 1 : Date (grande, centrée en haut)

                        # Ligne 2 : Français, Anglais, Arabe (en bas)

                        # Utiliser Square721 BT Bold pour les dates (chiffres uniquement)

                        # Utiliser la police arabe pour le texte mixte (contient de l'arabe)

                        header_table = Table([

                            [Paragraph(date_formatee, ParagraphStyle(

                                'HeaderDateMultilang',

                                parent=base_style,

                                fontSize=24,  # Plus grande que la version standard

                                fontName=square721_bold_font_name,  # Square721 BT Bold pour les dates (chiffres)

                                textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                                alignment=TA_CENTER,

                                leading=30  # Augmenter leading pour éeviter superposition

                            ))],  # Ligne 1 : Date seule (chiffres uniquement)

                            [Paragraph(

                                f"<font face='{square721_font_name}'>{jour_fr}</font> / <font face='{square721_font_name}'>{jour_en}</font> / <font face='{arabic_font_name}'>{fix_arabic_text(jour_ar)}</font>",

                                ParagraphStyle(

                                    'HeaderJourMultilang',

                                    parent=base_style,

                                    fontSize=10,  # Taille ajustée pour les jours

                                    fontName=arabic_font_name,  # Police de base (arabe) pour le Paragraph

                                    alignment=TA_CENTER,

                                    leading=17  # Leading ajusté pour garder un bon espacement

                                )

                            )]  # Ligne 2 : Trois langues (contient de l'arabe)

                        ], colWidths=[5.5*cm], rowHeights=[1.2*cm, 0.8*cm])  # Hauteurs explicites pour éeviter superposition

                        header_table.setStyle(TableStyle([

                            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Date centrée verticalement dans sa ligne

                            ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),  # Jours centrés verticalement dans leur ligne

                            ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Date centrée

                            ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés

                            ('LEFTPADDING', (0, 0), (-1, -1), 2),

                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)

                            ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours

                            ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)

                            ('BOTTOMPADDING', (0, 1), (0, 1), 8),  # Padding pour les jours

                        ]))

                    except Exception as e_header:

                        raise

                    # Créer une table avec header_table (date+jours) et jour férié éventuel

                    # Toujours utiliser 2 lignes pour uniformiser la hauteur

                    jour_ferie = is_jour_ferie(date_jour)

                    if jour_ferie:

                        nom_ferie = get_nom_jour_ferie(date_jour)

                        # ⚠️ PROTECTION: Cette section NE DOIT PAS être modifiée dans export_pdf_multilang()

                        # Cette fonction export_pdf_multilang() doit rester inchangée

                        # Toutes les modifications doivent être appliquées uniquement à export_pdf_multilang_style2()

                        # Garder le même BOTTOMPADDING pour les jours pour que le nom du jour reste au même niveau vertical

                        # Date et jours décalés vers le haut pour tous les jours

                        header_table.setStyle(TableStyle([

                            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Date centrée verticalement dans sa ligne

                            ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),  # Jours centrés verticalement dans leur ligne

                            ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Date centrée

                            ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés

                            ('LEFTPADDING', (0, 0), (-1, -1), 2),

                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)

                            ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours

                            ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)

                            ('BOTTOMPADDING', (0, 1), (0, 1), 8),  # Même padding en bas des jours pour alignement vertical uniforme

                        ]))

                        ferie_para = Paragraph(

                            f"<font color='#004499'>{nom_ferie}</font>",  # Même bleu que les dates

                            ferie_style

                        )

                    else:

                        # Paragraph vide pour maintenir la même hauteur

                        ferie_para = Paragraph("", base_style)

                    

                    # Table avec toujours 2 lignes : header_table en haut, jour férié (ou vide) en bas

                    # Hauteurs fixes : header_table (2.0cm) + ligne férié (0.4cm) = 2.4cm total

                    header_cell = Table(

                        [[header_table], [ferie_para]],

                        colWidths=[5.5*cm],

                        rowHeights=[2.0*cm, 0.4*cm]  # Hauteurs fixes pour uniformiser

                    )

                    

                    header_cell.setStyle(TableStyle([

                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

                        ('LEFTPADDING', (0, 0), (-1, -1), 2),

                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                        ('TOPPADDING', (0, 0), (-1, -1), 4 - 0.15*cm),  # Décaler le contenu vers le haut de 0,15 cm

                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),

                        # Réduire l'espacement entre header_table (ligne 0) et jour férié (ligne 1)

                        ('BOTTOMPADDING', (0, 0), (-1, 0), 0),  # Pas de padding en bas de header_table

                        ('TOPPADDING', (0, 1), (-1, 1), -0.25*cm),  # Décaler le texte du jour férié vers le haut de 0,25 cm (décalé vers le bas de 0,3 cm par rapport à -0.55)

                    ]))

                    header_row.append(header_cell)

                else:

                    header_row.append(Paragraph("", base_style))

            

            page1_data.append(header_row)

            

            # Ligne vide pour séparer les en-têtes des jours des champs de saisie

            page1_data.append([Paragraph("", base_style), Paragraph("", base_style), Paragraph("", base_style)])

            

            # 13 lignes horaires pour chaque colonne (8h-20h)

            for heure in heures:

                ligne_row = []

                for jour_key, jour_en, jour_fr in jours_page1:

                    date_jour = semaine[jour_key]

                    if date_jour is not None:

                        # Ligne avec numéro d'heure à gauche et deux lignes grises identiques

                        # Créer deux lignes distinctes avec exactement le même nombre de caractères pour garantir une longueur uniforme

                        # Utiliser un nombre de caractères fixe (42) pour remplir la largeur disponible sans retour à la ligne

                        # Créer exactement 2 lignes de longueur adaptée sans retour à la ligne

                        # Utiliser un calcul automatique basé sur la largeur disponible pour éeviter les retours à la ligne

                        # et aligner la fin des lignes exactement sur le cadre du jour.

                        # Première ligne : trait continu, gris foncé

                        ligne_underscore_solid = build_ligne_underscore(ligne_col_width, right_padding_points=2, char="_")

                        # Deuxième ligne : pointillée, gris clair (séquence de points espacés)

                        ligne_underscore_dotted = build_ligne_underscore(ligne_col_width, right_padding_points=2, char=". ")

                        # Styles spécifiques pour empêcher les retours à la ligne

                        ligne_horaire_style_solid = ParagraphStyle(

                            'LigneHoraireSolid',

                            parent=ligne_horaire_style,

                            textColor=colors.HexColor('#666666'),  # Gris foncé

                            leading=12,

                            spaceBefore=0,

                            spaceAfter=0

                        )

                        ligne_horaire_style_dotted = ParagraphStyle(

                            'LigneHoraireDotted',

                            parent=ligne_horaire_style,

                            textColor=colors.HexColor('#CCCCCC'),  # Gris clair

                            leading=12,

                            spaceBefore=0,

                            spaceAfter=0

                        )

                        # Style pour le numéro d'heure aligné avec la première ligne

                        # Utiliser exactement le même leading que la ligne pour un alignement parfait

                        heure_num_style = ParagraphStyle(

                            'HeureNum',

                            parent=base_style,

                            fontSize=7,

                            textColor=colors.HexColor('#999999'),

                            alignment=TA_LEFT,

                            leading=12,  # Exactement le même leading que ligne_horaire_style_no_wrap

                            spaceBefore=0,

                            spaceAfter=0,

                            firstLineIndent=0,

                            leftIndent=0,

                            rightIndent=0

                        )

                        heure_cell = Table(

                            [

                                # 1re sous-ligne : heure + trait continu gris foncé

                                [Paragraph(str(heure), heure_num_style), Paragraph(ligne_underscore_solid, ligne_horaire_style_solid)],

                                # 2e sous-ligne : trait pointillé gris clair

                                [Paragraph("", base_style), Paragraph(ligne_underscore_dotted, ligne_horaire_style_dotted)]

                            ],

                            # Largeurs des colonnes :

                            # - 0.6cm pour le numéro d'heure

                            # - ligne_col_width pour les lignes de saisie, aligné sur le cadre du jour

                            colWidths=[0.6*cm, ligne_col_width],

                            rowHeights=[12, 12]  # Hauteur exactement égale au leading pour garantir exactement 2 lignes sans ligne supplémentaire

                        )

                        heure_cell.setStyle(TableStyle([

                            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),  # Alignement à droite pour le numéro (plus proche de la ligne)

                            ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Alignement à gauche pour les lignes

                            ('VALIGN', (0, 0), (0, 0), 'TOP'),  # Alignement en haut pour permettre le décalage avec TOPPADDING

                            ('VALIGN', (1, 0), (1, 0), 'BOTTOM'),  # Aligner la première ligne sur sa ligne de base

                            ('VALIGN', (1, 1), (1, 1), 'TOP'),  # Alignement en haut pour la deuxième ligne

                            ('LEFTPADDING', (0, 0), (0, 0), 5),  # Padding à gauche encore augmenté pour décaler davantage le numéro vers la droite

                            ('RIGHTPADDING', (0, 0), (0, 0), 0),  # Pas de padding à droite pour le numéro (très proche de la ligne)

                            ('LEFTPADDING', (1, 0), (1, -1), 0),  # Pas de padding à gauche pour les lignes (très proche du numéro)

                            ('RIGHTPADDING', (1, 0), (1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 2),  # Padding en haut légèrement augmenté pour descendre très légèrement le numéro

                            ('TOPPADDING', (1, 0), (-1, -1), 0),  # Pas de padding en haut pour les lignes

                            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),  # Pas de padding en bas

                            ('BOTTOMPADDING', (1, 1), (1, 1), 0),  # Pas de padding en bas de la dernière ligne

                        ]))

                        ligne_row.append(heure_cell)

                    else:

                        ligne_row.append(Paragraph("", base_style))

                page1_data.append(ligne_row)

            

            # Ligne vide après le dernier champ de saisie (heure 20)

            # Utiliser un style avec leading minimal pour garantir que la ligne a une hauteur

            ligne_vide_style = ParagraphStyle('LigneVide', parent=base_style, fontSize=1, leading=24, spaceBefore=0, spaceAfter=0)

            ligne_vide_apres_heures = [Paragraph(" ", ligne_vide_style)] * len(jours_page1)

            page1_data.append(ligne_vide_apres_heures)

            

            # Mini-calendrier du mois (nouveau modèle style 2)

            # Structure selon le modèle : mois FR/AR, jours AR/FR, dates avec spillover, semaine encadrée

            _, nb_jours_mois = monthrange(annee_ref, mois_ref)

            premier_jour_mois = datetime(annee_ref, mois_ref, 1)

            jour_semaine_premier = premier_jour_mois.weekday()

            

            # Noms de mois en arabe

            mois_arabe = {

                1: 'جانفي', 2: 'فيفري', 3: 'مارس', 4: 'أفريل',

                5: 'ماي', 6: 'جوان', 7: 'جويلية', 8: 'أوت',

                9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر',

            }

            mois_fr = get_mois_nom(mois_ref)

            mois_ar = mois_arabe.get(mois_ref, '')

            

            # Noms de jours en arabe (ordre Lundi→Dimanche)

            jours_arabe_cal = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']

            # Abréviations françaises (3 premières lettres)

            jours_abrev_fr = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']

            

            # Styles pour le nouveau mini-calendrier

            cal_mois_style = ParagraphStyle(

                'CalMois',

                parent=base_style,

                fontSize=10,

                fontName=square721_bold_font_name,

                textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                alignment=TA_LEFT

            )

            cal_mois_ar_style = ParagraphStyle(

                'CalMoisArabic',

                parent=base_style,

                fontSize=10,

                fontName=arabic_font_name,

                textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                alignment=TA_RIGHT,

                leading=12,

                spaceBefore=0,

                spaceAfter=0

            )

            cal_jour_ar_style = ParagraphStyle(

                'CalJourArabic',

                parent=base_style,

                fontSize=5,

                fontName=arabic_font_name,

                textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                alignment=TA_CENTER,

                leading=8

            )

            cal_jour_fr_style = ParagraphStyle(

                'CalJourFR',

                parent=base_style,

                fontSize=7,

                fontName=square721_font_name,

                textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                alignment=TA_CENTER,

                leading=8

            )

            cal_date_style_bleu = ParagraphStyle(

                'CalDateBleu',

                parent=base_style,

                fontSize=8,

                fontName=square721_font_name,

                textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                alignment=TA_CENTER,

                leading=10

            )

            cal_date_dimanche_style = ParagraphStyle(

                'CalDateDimanche',

                parent=base_style,

                fontSize=8,

                fontName=square721_bold_font_name,

                textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                alignment=TA_CENTER,

                leading=10

            )
            
            # Style pour les dates spillover (mois précédent/suivant) : bleu plus clair
            cal_date_spillover_style = ParagraphStyle(
                'CalDateSpillover',
                parent=base_style,
                fontSize=8,
                fontName=square721_font_name,
                textColor=colors.HexColor('#66AAFF'),  # Bleu plus clair que #0066CC
                alignment=TA_CENTER,
                leading=10
            )
            
            cal_date_spillover_dimanche_style = ParagraphStyle(
                'CalDateSpilloverDimanche',
                parent=base_style,
                fontSize=8,
                fontName=square721_bold_font_name,
                textColor=colors.HexColor('#66AAFF'),  # Bleu plus clair que #0066CC
                alignment=TA_CENTER,
                leading=10
            )

            

            # Construire le mini-calendrier

            cal_table_rows = []

            

            # Ligne 1 : Mois FR à gauche, mois AR à droite (bleu)
            # Pour septembre, novembre et décembre, utiliser plus de colonnes pour le mois français (colonnes 0-2 au lieu de 0-1)
            if mois_ref in [9, 11, 12]:  # Septembre, novembre ou décembre
                cal_table_rows.append([
                    Paragraph(mois_fr, cal_mois_style),  # Colonne 0 (taille normale pour tous les mois)
                    Paragraph("", base_style),  # Colonne 1 (pour le SPAN du mois FR sur colonnes 0-2)
                    Paragraph("", base_style),  # Colonne 2 (pour le SPAN du mois FR sur colonnes 0-2)
                    Paragraph(fix_arabic_text(mois_ar), cal_mois_ar_style),  # Colonne 3 (première colonne du SPAN pour le mois AR sur colonnes 3-6)
                    Paragraph("", base_style), Paragraph("", base_style), Paragraph("", base_style),  # Colonnes 4-6 (pour le SPAN du mois AR)
                ])
            else:
                cal_table_rows.append([
                    Paragraph(mois_fr, cal_mois_style),  # Colonne 0
                    Paragraph("", base_style),  # Colonne 1 (pour le SPAN du mois FR sur colonnes 0-1)
                    Paragraph(fix_arabic_text(mois_ar), cal_mois_ar_style),  # Colonne 2 (première colonne du SPAN pour le mois AR sur colonnes 2-6)
                    Paragraph("", base_style), Paragraph("", base_style), Paragraph("", base_style), Paragraph("", base_style),  # Colonnes 3-6 (pour le SPAN du mois AR)
                ])

            

            # Ligne 2 : Jours AR en haut, abréviations FR en dessous (bleu)

            # Créer une table imbriquée pour chaque colonne (AR au-dessus, FR en dessous)

            cal_jours_row = []

            for i in range(7):

                # Table imbriquée : AR en haut, FR en dessous

                jour_cell_table = Table([

                    [Paragraph(fix_arabic_text(jours_arabe_cal[i]), cal_jour_ar_style)],

                    [Paragraph(jours_abrev_fr[i], cal_jour_fr_style)]

                ], colWidths=[0.7*cm], rowHeights=[10, 8])

                jour_cell_table.setStyle(TableStyle([

                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                    ('LEFTPADDING', (0, 0), (-1, -1), 2),

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (-1, -1), 2),

                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),

                ]))

                cal_jours_row.append(jour_cell_table)

            cal_table_rows.append(cal_jours_row)

            

            # Construire la grille des dates (nouveau modèle)

            # Identifier la semaine courante (celle affichée sur la page)

            semaine_courante_num = semaine['numero']

            semaine_courante_lundi = semaine['lundi']
            
            # Calculer le numéro de semaine dans le mois (1ère, 2ème, etc.) pour septembre, novembre et décembre
            # Ces mois ont besoin d'un positionnement spécial comme janvier
            numero_semaine_dans_mois = None
            if semaine_courante_lundi and mois_ref in [9, 11, 12]:  # Septembre, novembre, décembre
                # Vérifier si le lundi de la semaine courante est dans le mois de référence
                if semaine_courante_lundi.month == mois_ref and semaine_courante_lundi.year == annee_ref:
                    # Le lundi est dans le mois de référence
                    jour_lundi = semaine_courante_lundi.day
                    # Calculer le numéro de semaine dans le mois (1ère semaine = jours 1-7, 2ème semaine = jours 8-14, etc.)
                    numero_semaine_dans_mois = ((jour_lundi - 1) // 7) + 1
                else:
                    # Le lundi est dans le mois précédent (spillover) : c'est la première semaine du mois
                    numero_semaine_dans_mois = 1

            

            # Construire la grille : dates du mois + spillover du mois précédent et suivant

            dates_grille = []  # Liste de listes : chaque sous-liste = une semaine (7 jours)

            semaine_encadree_row = None  # Index de la ligne à encadrer

            

            # Ajouter les dates du mois précédent avant le premier jour du mois (spillover)

            if jour_semaine_premier > 0:

                if len(dates_grille) == 0:

                    dates_grille.append([])

                # Calculer le mois précédent

                mois_precedent = mois_ref - 1 if mois_ref > 1 else 12

                annee_precedente = annee_ref if mois_ref > 1 else annee_ref - 1

                _, nb_jours_mois_precedent = monthrange(annee_precedente, mois_precedent)

                # Ajouter les dates du mois précédent (du dernier jour vers le premier)

                for i in range(jour_semaine_premier):

                    jour_precedent = nb_jours_mois_precedent - jour_semaine_premier + i + 1

                    date_precedente = datetime(annee_precedente, mois_precedent, jour_precedent)

                    dates_grille[-1].append(date_precedente)

            

            # Ajouter les jours du mois

            jour_courant = 1

            while jour_courant <= nb_jours_mois:

                if len(dates_grille) == 0 or len(dates_grille[-1]) == 7:

                    dates_grille.append([])

                

                jour_date = datetime(annee_ref, mois_ref, jour_courant)

                dates_grille[-1].append(jour_date)

                

                # Vérifier si cette semaine est la semaine courante

                if semaine_encadree_row is None and semaine_courante_lundi:

                    # Calculer le lundi de la semaine de ce jour

                    jour_semaine = jour_date.weekday()

                    lundi_semaine = jour_date - timedelta(days=jour_semaine)

                    if lundi_semaine.date() == semaine_courante_lundi.date():

                        semaine_encadree_row = len(dates_grille) - 1

                

                jour_courant += 1

            

            # Compléter la dernière semaine avec spillover du mois suivant (toujours)

            derniere_semaine = dates_grille[-1] if dates_grille else []

            if len(derniere_semaine) < 7:

                mois_suivant = mois_ref + 1 if mois_ref < 12 else 1

                annee_suivante = annee_ref if mois_ref < 12 else annee_ref + 1

                jour_suivant = 1

                

                # Toujours compléter avec les dates du mois suivant

                while len(derniere_semaine) < 7:

                    date_suiv = datetime(annee_suivante, mois_suivant, jour_suivant)

                    derniere_semaine.append(date_suiv)

                    jour_suivant += 1

            

            # Construire les lignes du tableau

            for row_idx, semaine_dates in enumerate(dates_grille):

                cal_row_cells = []

                

                # Pour chaque jour de la semaine (7 colonnes)

                for col_idx, date_jour in enumerate(semaine_dates):

                    if date_jour is None:

                        # Espace vide (ne devrait plus arriver avec les spillover)

                        cal_row_cells.append(Paragraph("", cal_date_style_bleu))

                    else:

                        jour_str = f"{date_jour.day:02d}"

                        # Vérifier si la date est du mois courant ou spillover

                        est_du_mois_courant = (date_jour.month == mois_ref and date_jour.year == annee_ref)

                        # Dimanche (colonne 6) en gras

                        if col_idx == 6:  # Dimanche

                            if est_du_mois_courant:

                                cal_row_cells.append(Paragraph(jour_str, cal_date_dimanche_style))

                            else:

                                cal_row_cells.append(Paragraph(jour_str, cal_date_spillover_dimanche_style))

                        else:

                            if est_du_mois_courant:

                                cal_row_cells.append(Paragraph(jour_str, cal_date_style_bleu))

                            else:

                                cal_row_cells.append(Paragraph(jour_str, cal_date_spillover_style))

                

                cal_table_rows.append(cal_row_cells)

            

            # Limiter à 6 lignes de dates (en plus de l'en-tête et des abréviations)

            # Total : 1 en-tête + 1 abréviations + 6 lignes dates = 8 lignes max

            if len(cal_table_rows) > 8:

                cal_table_rows = cal_table_rows[:8]

            

            # Créer le tableau du mini-calendrier (nouveau modèle : 7 colonnes, pas de numéro de semaine)

            try:

                cal_table = Table(

                    cal_table_rows,

                    colWidths=[0.73*cm] * 7  # 7 colonnes pour les jours (augmenté de 0.2cm au total : 0.7 + 0.2/7 ≈ 0.73cm par colonne)

                )

                # Créer le TableStyle avec SPAN conditionnel selon le mois
                cal_table_style_list = [
                    # Ligne 0 : Mois FR/AR
                ]
                
                # SPAN conditionnel selon le mois
                if mois_ref in [9, 11, 12]:  # Septembre, novembre ou décembre : mois FR sur colonnes 0-2, mois AR sur colonnes 3-6
                    cal_table_style_list.extend([
                        ('SPAN', (0, 0), (2, 0)),              # Mois FR sur colonnes 0 à 2 (augmenté pour septembre, novembre et décembre)
                        ('SPAN', (3, 0), (6, 0)),              # Mois AR sur colonnes 3 à 6 (réduit pour septembre, novembre et décembre)
                        ('ALIGN', (0, 0), (2, 0), 'LEFT'),     # Mois FR aligné à gauche
                        ('ALIGN', (3, 0), (6, 0), 'RIGHT'),    # Mois AR aligné à droite
                    ])
                else:  # Autres mois : mois FR sur colonnes 0-1, mois AR sur colonnes 2-6
                    cal_table_style_list.extend([
                        ('SPAN', (0, 0), (1, 0)),              # Mois FR sur colonnes 0 à 1 (réduit pour donner plus d'espace au mois AR)
                        ('SPAN', (2, 0), (6, 0)),              # Mois AR sur colonnes 2 à 6 (augmenté pour afficher entièrement sur une ligne)
                        ('ALIGN', (0, 0), (1, 0), 'LEFT'),     # Mois FR aligné à gauche
                        ('ALIGN', (2, 0), (6, 0), 'RIGHT'),    # Mois AR aligné à droite
                    ])
                
                cal_table_style_list.extend([

                    # Ligne 1 : Jours AR/FR

                    ('ALIGN', (0, 1), (-1, 1), 'CENTER'),  # Jours centrés

                    # Ligne de séparation bleue après les jours (ligne 1)

                    ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor('#004499')),  # Bleu clairement plus foncé que #0066CC

                    # Lignes de dates (ligne 2+)

                    ('ALIGN', (0, 2), (-1, -1), 'CENTER'), # Dates centrées

                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                    ('LEFTPADDING', (0, 0), (-1, -1), 2),

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (-1, -1), 2),

                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),

                ])
                
                cal_table.setStyle(TableStyle(cal_table_style_list))

                

                # Stocker l'index de la semaine encadrée pour le callback

                # On stocke dans page_to_mois avec une clé spéciale

                # page_num_page1 est déjà calculé avant l'incrémentation de semaine_index

                page_to_mois[f'semaine_encadree_{page_num_page1}'] = semaine_encadree_row
                
                # Stocker le numéro de semaine dans le mois pour septembre, novembre et décembre
                if numero_semaine_dans_mois is not None:
                    page_to_mois[f'numero_semaine_mois_{page_num_page1}'] = numero_semaine_dans_mois

            except Exception as e_cal_table:

                raise

            

            # Ajouter la ligne avec mini-calendrier à gauche et 5 lignes grises à droite (comeme dimanche dans page 2)

            # Créer les 5 lignes grises avec symboles : @ pour la ligne 1, ✆ pour la ligne 4 (lignes 2, 3, 5 sans symbole)

            # Lignes 1 et 4 : longueur réduite de 0,1cm (65 caractères), lignes 2, 3, 5 : longueur augmentée de 0,1cm (67 caractères)

            cal_notes_rows = []

            # Ajouter une ligne vide en haut
            cal_notes_rows.append([Paragraph("", ligne_note_style)])

            for i in range(5):

                if i == 0:  # Ligne 1 : @, longueur augmentée de 0,5cm

                    cal_notes_rows.append([Paragraph("@" + "_" * 68, ligne_note_style)])

                elif i == 3:  # Ligne 4 : ✆ avec taille 9, longueur augmentée de 0,5cm

                    cal_notes_rows.append([Paragraph('<font size="9">✆</font>' + "_" * 68, ligne_note_style)])

                else:  # Lignes 2, 3, 5 : pas de symbole, longueur augmentée de 0,5cm

                    cal_notes_rows.append([Paragraph("_" * 70, ligne_note_style)])

            # Ajouter une 6ème ligne en bas (sans symbole, longueur augmentée de 0,5cm)
            cal_notes_rows.append([Paragraph("_" * 70, ligne_note_style)])

            

            cal_notes_cell = Table(

                cal_notes_rows,

                colWidths=[12.0*cm]  # Largeur augmentée de 0,5cm (11,5cm + 0,5cm = 12,0cm)

            )

            cal_notes_cell.setStyle(TableStyle([

                ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                ('LEFTPADDING', (0, 0), (-1, -1), 15 + 0.3*cm),  # Décaler les lignes vers la droite de 0,3 cm (0,1 + 0,2)

                ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                ('TOPPADDING', (0, 0), (-1, -1), 2),

                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),

            ]))

            

            cal_row = [

                cal_table,  # Mini-calendrier colonne 0 (à gauche)

                cal_notes_cell,  # 5 lignes grises colonnes 1-2 (fusionnées) - identique à dimanche dans page 2

                Paragraph("", base_style)  # Colonne 2 (sera fusionnée avec colonne 1)

            ]

            page1_data.append(cal_row)

            

            # Trouver l'index de la ligne du mini-calendrier (dernière ligne)

            cal_row_index = len(page1_data) - 1

            

            # Trouver l'index de la ligne des en-têtes (après la ligne de la semaine)

            header_row_index = 1  # La ligne de la semaine est à l'index 0, les en-têtes sont à l'index 1

            semaine_row_index = 0  # La ligne de la semaine est à l'index 0

            ligne_vide_index = 2  # La ligne vide est à l'index 2 (après la semaine et les en-têtes)

            

            # Trouver l'index de la dernière ligne horaire (20h)

            # Il y a 1 ligne vide + 13 lignes horaires (8h-20h), donc la dernière est à l'index ligne_vide_index + 13

            derniere_ligne_horaire_index = ligne_vide_index + len(heures)  # ligne_vide_index (2) + 13 lignes horaires = 15

            # Index de la ligne vide après les heures (juste après la dernière ligne horaire)

            ligne_vide_apres_heures_index = derniere_ligne_horaire_index + 1

            

            # Créer le tableau pour la page 1 (format portrait - colonnes plus étroites)

            # Calculer les hauteurs de lignes : ligne semaine (fixe), ligne en-tête (fixe), autres lignes (auto)

            # Hauteur ligne semaine : identique à la page 2 (0.7cm) pour que les tableaux comemencent au même niveau

            # Hauteur ligne en-tête : header_cell (2.4cm) + TOPPADDING (0.3cm) = 2.7cm

            page1_row_heights = [None] * len(page1_data)  # None = hauteur automatique

            page1_row_heights[semaine_row_index] = 0.7*cm  # Hauteur fixe pour la ligne de la semaine (identique à page 2)

            page1_row_heights[header_row_index] = 2.7*cm  # Hauteur fixe pour la ligne d'en-tête

            # Hauteur de la ligne vide = même hauteur que les lignes horaires (2 lignes de 12 points chacune = 24 points ≈ 0.85cm)

            page1_row_heights[ligne_vide_index] = 24  # Même hauteur que les lignes horaires (2 lignes de 12 points)

            # Hauteur de la ligne vide après les heures (même hauteur qu'une ligne horaire)

            if ligne_vide_apres_heures_index < len(page1_row_heights):

                page1_row_heights[ligne_vide_apres_heures_index] = 15  # Hauteur réduite encore plus (20 -> 15)

            page1_table = Table(page1_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm], rowHeights=page1_row_heights)

            page1_table.setStyle(TableStyle([

                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                # Toutes les bordures supprimées pour le style 2 (rectangles arrondis à la place)

                # Centrer le calendrier dans sa cellule (cadre)

                ('ALIGN', (0, cal_row_index), (0, cal_row_index), 'CENTER'),

                ('VALIGN', (0, cal_row_index), (0, cal_row_index), 'MIDDLE'),

                # Fusionner les colonnes 1 et 2 pour les 5 lignes grises (comeme dimanche dans page 2)

                ('SPAN', (1, cal_row_index), (2, cal_row_index)),

                ('LEFTPADDING', (0, 0), (-1, -1), 0),

                ('RIGHTPADDING', (0, 0), (-1, -1), 0),

                ('TOPPADDING', (0, 0), (-1, -1), 0),

                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),

                # Ajouter un espacement en haut de la ligne des en-têtes pour décaler le reste du tableau vers le bas (identique à la page 2)

                ('TOPPADDING', (0, header_row_index), (-1, header_row_index), 0.3*cm),

                # Décaler le texte de la semaine (ligne 0, toutes colonnes) vers le bas de 0,35 cm

                ('TOPPADDING', (0, semaine_row_index), (-1, semaine_row_index), 0.35*cm),

            ]))

            

            elements.append(page1_table)

            elements.append(PageBreak())

            

            # ========== PAGE 2 : JEUDI / VENDREDI / SAMEDI + DIMANCHE ==========

            page2_data = []

            

            # Ligne avec texte de la semaine en haut à gauche et "2026" en haut à droite

            semaine_num_formate2 = f"{semaine['numero']:02d}"

            semaine_ar2 = 'الأسبوع'

            # Utiliser un seul Paragraph avec des balises font pour tout mettre sur une seule ligne (même approche que page 1)

            # Le numéro utilise la police Bold directement dans la balise font

            semaine_row2 = [

                Paragraph(

                    f"<font face='{square721_font_name}'>Semaine Week  </font><font face='{square721_bold_font_name}' color='#004499' size='10'>{semaine_num_formate2}</font><font face='{arabic_font_name}'>  {fix_arabic_text(semaine_ar2)}</font>",

                    ParagraphStyle(

                        'SemaineHeader',

                        parent=base_style,

                        fontSize=9,

                        fontName=arabic_font_name,  # Police de base

                        alignment=TA_LEFT,

                        leading=14,

                        spaceBefore=0,

                        spaceAfter=0

                    )

                ),

                Paragraph("", base_style),  # Colonne vide

                Paragraph("2026", ParagraphStyle(

                    'AnneePage2',

                    parent=base_style,

                    fontSize=20,

                    fontName=square721_bold_font_name,

                    textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                    alignment=TA_RIGHT,

                    leading=20,

                    leftIndent=0  # Retirer leftIndent car on utilise LEFTPADDING sur la cellule

                ))

            ]

            page2_data.append(semaine_row2)

            

            # En-têtes des 3 colonnes (Jeudi, Vendredi, Samedi) - Version multilingue

            header_row2 = []

            jours_page2 = [

                ('jeudi', 'Thursday', 'Jeudi'),

                ('vendredi', 'Friday', 'Vendredi'),

                ('samedi', 'Saturday', 'Samedi')

            ]

            

            for jour_key, jour_en, jour_fr in jours_page2:

                date_jour = semaine[jour_key]

                if date_jour is not None:

                    # Format avec zéro devant si < 10 (01, 02, 03, 04)

                    date_formatee = f"{date_jour.day:02d}"

                    jour_ar = jours_arabe.get(jour_key, '')

                    

                    # Structure : Date en haut (grande), jours en bas (3 langues)

                    # Créer un tableau avec date en haut et jours en bas

                    try:

                        # Ligne 1 : Date (grande, centrée en haut)

                        # Ligne 2 : Français, Anglais, Arabe (en bas)

                        # Utiliser Square721 BT Bold pour les dates (chiffres uniquement)

                        # Utiliser la police arabe pour le texte mixte (contient de l'arabe)

                        header_table = Table([

                            [Paragraph(date_formatee, ParagraphStyle(

                                'HeaderDateMultilang',

                                parent=base_style,

                                fontSize=24,  # Plus grande que la version standard

                                fontName=square721_bold_font_name,  # Square721 BT Bold pour les dates (chiffres)

                                textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                                alignment=TA_CENTER,

                                leading=30  # Augmenter leading pour éeviter superposition

                            ))],  # Ligne 1 : Date seule (chiffres uniquement)

                            [Paragraph(

                                f"<font face='{square721_font_name}'>{jour_fr}</font> / <font face='{square721_font_name}'>{jour_en}</font> / <font face='{arabic_font_name}'>{fix_arabic_text(jour_ar)}</font>",

                                ParagraphStyle(

                                    'HeaderJourMultilang',

                                    parent=base_style,

                                    fontSize=10,  # Taille ajustée pour les jours

                                    fontName=arabic_font_name,  # Police de base (arabe) pour le Paragraph

                                    alignment=TA_CENTER,

                                    leading=17  # Leading ajusté pour garder un bon espacement

                                )

                            )]  # Ligne 2 : Trois langues (contient de l'arabe)

                        ], colWidths=[5.5*cm], rowHeights=[1.2*cm, 0.8*cm])  # Hauteurs explicites pour éeviter superposition

                        header_table.setStyle(TableStyle([

                            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Date centrée verticalement dans sa ligne

                            ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),  # Jours centrés verticalement dans leur ligne

                            ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Date centrée

                            ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés

                            ('LEFTPADDING', (0, 0), (-1, -1), 2),

                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)

                            ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours

                            ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)

                            ('BOTTOMPADDING', (0, 1), (0, 1), 8),  # Padding pour les jours

                        ]))

                    except Exception as e_header:

                        raise

                    # Créer une table avec header_table (date+jours) et jour férié éventuel

                    # Toujours utiliser 2 lignes pour uniformiser la hauteur

                    jour_ferie = is_jour_ferie(date_jour)

                    if jour_ferie:

                        nom_ferie = get_nom_jour_ferie(date_jour)

                        # ⚠️ PROTECTION: Cette section NE DOIT PAS être modifiée dans export_pdf_multilang()

                        # Cette fonction export_pdf_multilang() doit rester inchangée

                        # Toutes les modifications doivent être appliquées uniquement à export_pdf_multilang_style2()

                        # Garder le même BOTTOMPADDING pour les jours pour que le nom du jour reste au même niveau vertical

                        # Date et jours décalés vers le haut pour tous les jours

                        header_table.setStyle(TableStyle([

                            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Date centrée verticalement dans sa ligne

                            ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),  # Jours centrés verticalement dans leur ligne

                            ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Date centrée

                            ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés

                            ('LEFTPADDING', (0, 0), (-1, -1), 2),

                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)

                            ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours

                            ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)

                            ('BOTTOMPADDING', (0, 1), (0, 1), 8),  # Même padding en bas des jours pour alignement vertical uniforme

                        ]))

                        ferie_para = Paragraph(

                            f"<font color='#004499'>{nom_ferie}</font>",  # Même bleu que les dates

                            ferie_style

                        )

                    else:

                        # Paragraph vide pour maintenir la même hauteur

                        ferie_para = Paragraph("", base_style)

                    

                    # Table avec toujours 2 lignes : header_table en haut, jour férié (ou vide) en bas

                    # Hauteurs fixes : header_table (2.0cm) + ligne férié (0.4cm) = 2.4cm total

                    header_cell = Table(

                        [[header_table], [ferie_para]],

                        colWidths=[5.5*cm],

                        rowHeights=[2.0*cm, 0.4*cm]  # Hauteurs fixes pour uniformiser

                    )

                    

                    header_cell.setStyle(TableStyle([

                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

                        ('LEFTPADDING', (0, 0), (-1, -1), 2),

                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                        ('TOPPADDING', (0, 0), (-1, -1), 4 - 0.15*cm),  # Décaler le contenu vers le haut de 0,15 cm

                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),

                        # Réduire l'espacement entre header_table (ligne 0) et jour férié (ligne 1)

                        ('BOTTOMPADDING', (0, 0), (-1, 0), 0),  # Pas de padding en bas de header_table

                        ('TOPPADDING', (0, 1), (-1, 1), -0.25*cm),  # Décaler le texte du jour férié vers le haut de 0,25 cm (décalé vers le bas de 0,3 cm par rapport à -0.55)

                    ]))

                    header_row2.append(header_cell)

                else:

                    header_row2.append(Paragraph("", base_style))

            

            page2_data.append(header_row2)

            

            # Ligne vide pour séparer les en-têtes des jours des champs de saisie

            page2_data.append([Paragraph("", base_style), Paragraph("", base_style), Paragraph("", base_style)])

            

            # 13 lignes horaires pour chaque colonne (8h-20h)

            for heure in heures:

                ligne_row = []

                for jour_key, jour_en, jour_fr in jours_page2:

                    date_jour = semaine[jour_key]

                    if date_jour is not None:

                        # Ligne avec numéro d'heure à gauche et deux lignes grises identiques

                        # Créer deux lignes distinctes avec exactement le même nombre de caractères pour garantir une longueur uniforme

                        # Utiliser un nombre de caractères fixe (42) pour remplir la largeur disponible sans retour à la ligne

                        # Créer exactement 2 lignes de longueur adaptée sans retour à la ligne

                        # Utiliser un calcul automatique basé sur la largeur disponible pour éeviter les retours à la ligne

                        # et aligner la fin des lignes exactement sur le cadre du jour.

                        # Première ligne : trait continu, gris foncé

                        ligne_underscore_solid = build_ligne_underscore(ligne_col_width, right_padding_points=2, char="_")

                        # Deuxième ligne : pointillée, gris clair (séquence de points espacés)

                        ligne_underscore_dotted = build_ligne_underscore(ligne_col_width, right_padding_points=2, char=". ")

                        # Styles spécifiques pour empêcher les retours à la ligne

                        ligne_horaire_style_solid = ParagraphStyle(

                            'LigneHoraireSolid',

                            parent=ligne_horaire_style,

                            textColor=colors.HexColor('#666666'),  # Gris foncé

                            leading=12,

                            spaceBefore=0,

                            spaceAfter=0

                        )

                        ligne_horaire_style_dotted = ParagraphStyle(

                            'LigneHoraireDotted',

                            parent=ligne_horaire_style,

                            textColor=colors.HexColor('#CCCCCC'),  # Gris clair

                            leading=12,

                            spaceBefore=0,

                            spaceAfter=0

                        )

                        # Style pour le numéro d'heure aligné avec la première ligne

                        # Utiliser exactement le même leading que la ligne pour un alignement parfait

                        heure_num_style = ParagraphStyle(

                            'HeureNum',

                            parent=base_style,

                            fontSize=7,

                            textColor=colors.HexColor('#999999'),

                            alignment=TA_LEFT,

                            leading=12,  # Exactement le même leading que ligne_horaire_style_no_wrap

                            spaceBefore=0,

                            spaceAfter=0,

                            firstLineIndent=0,

                            leftIndent=0,

                            rightIndent=0

                        )

                        heure_cell = Table(

                            [

                                # 1re sous-ligne : heure + trait continu gris foncé

                                [Paragraph(str(heure), heure_num_style), Paragraph(ligne_underscore_solid, ligne_horaire_style_solid)],

                                # 2e sous-ligne : trait pointillé gris clair

                                [Paragraph("", base_style), Paragraph(ligne_underscore_dotted, ligne_horaire_style_dotted)]

                            ],

                            # Largeurs des colonnes :

                            # - 0.6cm pour le numéro d'heure

                            # - ligne_col_width pour les lignes de saisie, aligné sur le cadre du jour

                            colWidths=[0.6*cm, ligne_col_width],

                            rowHeights=[12, 12]  # Hauteur exactement égale au leading pour garantir exactement 2 lignes sans ligne supplémentaire

                        )

                        heure_cell.setStyle(TableStyle([

                            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),  # Alignement à droite pour le numéro (plus proche de la ligne)

                            ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Alignement à gauche pour les lignes

                            ('VALIGN', (0, 0), (0, 0), 'TOP'),  # Alignement en haut pour permettre le décalage avec TOPPADDING

                            ('VALIGN', (1, 0), (1, 0), 'BOTTOM'),  # Aligner la première ligne sur sa ligne de base

                            ('VALIGN', (1, 1), (1, 1), 'TOP'),  # Alignement en haut pour la deuxième ligne

                            ('LEFTPADDING', (0, 0), (0, 0), 5),  # Padding à gauche encore augmenté pour décaler davantage le numéro vers la droite

                            ('RIGHTPADDING', (0, 0), (0, 0), 0),  # Pas de padding à droite pour le numéro (très proche de la ligne)

                            ('LEFTPADDING', (1, 0), (1, -1), 0),  # Pas de padding à gauche pour les lignes (très proche du numéro)

                            ('RIGHTPADDING', (1, 0), (1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 2),  # Padding en haut légèrement augmenté pour descendre très légèrement le numéro

                            ('TOPPADDING', (1, 0), (-1, -1), 0),  # Pas de padding en haut pour les lignes

                            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),  # Pas de padding en bas

                            ('BOTTOMPADDING', (1, 1), (1, 1), 0),  # Pas de padding en bas de la dernière ligne

                        ]))

                        ligne_row.append(heure_cell)

                    else:

                        ligne_row.append(Paragraph("", base_style))

                page2_data.append(ligne_row)

            

            # Ligne vide après le dernier champ de saisie (heure 20)

            # Utiliser un espace avec un style ayant un leading minimal pour garantir que la ligne a une hauteur

            ligne_vide_style = ParagraphStyle('LigneVide', parent=base_style, fontSize=1, leading=24, spaceBefore=0, spaceAfter=0)

            ligne_vide_apres_heures = [Paragraph(" ", ligne_vide_style)] * len(jours_page2)

            page2_data.append(ligne_vide_apres_heures)

            

                # Zone Dimanche : en-tête dans colonne 1, lignes grises dans colonnes 2 et 3 (déplacé de la page 1 vers la page 2)

            dimanche_row = []

            if semaine['dimanche'] is not None:

                jour_ferie = is_jour_ferie(semaine['dimanche'])

                nom_ferie = get_nom_jour_ferie(semaine['dimanche']) if jour_ferie else ""

                

                # Contenu Dimanche : Date en haut (grande), jours en bas (3 langues)

                # Format avec zéro devant si < 10

                date_dimanche_formatee = f"{semaine['dimanche'].day:02d}"

                dimanche_ar = jours_arabe.get('dimanche', 'الأحد')

                

                # Structure : Date en haut (grande), jours en bas (3 langues)

                # Utiliser Square721 BT Bold pour les dates (chiffres uniquement, pas besoin d'arabe)

                # Utiliser Square721 BT pour tous les textes

                dimanche_header_table = Table([

                    [Paragraph(date_dimanche_formatee, ParagraphStyle(

                        'DimancheDateMultilangStyle2',

                        parent=base_style,

                        fontSize=24,  # Plus grande que la version standard

                        fontName=square721_bold_font_name,  # Square721 BT Bold pour les dates

                        textColor=colors.HexColor('#004499'),  # Bleu plus foncé

                        alignment=TA_CENTER,

                        leading=30  # Augmenter leading pour éeviter superposition

                    ))],  # Ligne 1 : Date seule

                    [Paragraph(

                        f"<font face='{square721_font_name}'>Dimanche</font> / <font face='{square721_font_name}'>Sunday</font> / <font face='{arabic_font_name}'>{fix_arabic_text(dimanche_ar)}</font>",

                        ParagraphStyle(

                            'DimancheJourMultilangStyle2',

                            parent=base_style,

                            fontSize=9,

                            fontName=arabic_font_name,

                            alignment=TA_CENTER,

                            leading=16  # Augmenter leading pour l'espacement

                        )

                    )]  # Ligne 2 : Trois langues

                ], colWidths=[5.5*cm], rowHeights=[1.2*cm, 0.8*cm])  # Hauteurs explicites pour éeviter superposition

                dimanche_header_table.setStyle(TableStyle([

                    ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Date centrée verticalement dans sa ligne

                    ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),  # Jours centrés verticalement dans leur ligne

                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Date centrée

                    ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés (dimanche reste centré)

                    ('LEFTPADDING', (0, 0), (-1, -1), 2),

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)

                    ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours

                    ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)

                    ('BOTTOMPADDING', (0, 1), (0, 1), 8),  # Padding pour les jours

                ]))

                

                # Colonne 1 : En-tête Dimanche + date (et jour férié si applicable)

                # Toujours utiliser 2 lignes pour uniformiser la hauteur

                if jour_ferie:

                    # Garder le même BOTTOMPADDING pour les jours pour que le dimanche reste au même niveau vertical

                    # Date et jours décalés vers le haut pour tous les jours

                    dimanche_header_table.setStyle(TableStyle([

                            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Date centrée verticalement dans sa ligne

                            ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),  # Jours centrés verticalement dans leur ligne

                            ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Date centrée

                            ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés (dimanche reste centré même pour jours fériés)

                            ('LEFTPADDING', (0, 0), (-1, -1), 2),

                            ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                            ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)

                            ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours

                            ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)

                            ('BOTTOMPADDING', (0, 1), (0, 1), 8),  # Même padding en bas des jours pour garder le dimanche au même emplacement

                        ]))

                    dimanche_ferie_para = Paragraph(

                        f"<font color='#004499'>{nom_ferie}</font>",  # Même bleu que les dates

                        ferie_style

                    )

                else:

                    # Paragraph vide pour maintenir la même hauteur

                    dimanche_ferie_para = Paragraph("", base_style)

                

                # Table avec toujours 2 lignes : dimanche_header_table en haut, jour férié (ou vide) en bas

                # Hauteurs fixes : dimanche_header_table (2.0cm) + ligne férié (0.4cm) = 2.4cm total

                dimanche_header_cell = Table(

                    [[dimanche_header_table], [dimanche_ferie_para]],

                    colWidths=[5.5*cm],

                    rowHeights=[2.0*cm, 0.4*cm]  # Hauteurs fixes pour uniformiser

                )

                dimanche_header_cell.setStyle(TableStyle([

                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

                    ('LEFTPADDING', (0, 0), (-1, -1), 2),

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (0, 0), 4 + 0.5*cm),  # Décaler dimanche_header_table vers le bas de 0,5 cm (date et jour décalés ensemble) - position originale

                    ('BOTTOMPADDING', (0, 0), (0, 0), 12),

                    # Réduire l'espacement entre dimanche_header_table (ligne 0) et jour férié (ligne 1)

                    ('BOTTOMPADDING', (0, 0), (-1, 0), 0),  # Pas de padding en bas de dimanche_header_table

                    ('TOPPADDING', (0, 1), (-1, 1), 0.55*cm),  # Décaler le texte du jour férié vers le haut de 0,2 cm (0.55 = 0.75 - 0.2)

                ]))

                

                # Colonnes 2 et 3 : 5 lignes grises (fusionnées sur 2 colonnes)

                dimanche_notes_rows = []

                for i in range(5):

                    dimanche_notes_rows.append([Paragraph("_" * 71, ligne_note_style)])  # Ajuster pour 12,2cm de largeur (augmenté de 0,5cm)

                # Ajouter une 6ème ligne en bas
                dimanche_notes_rows.append([Paragraph("_" * 71, ligne_note_style)])  # Ajuster pour 12,2cm de largeur (augmenté de 0,5cm)

                

                dimanche_notes_cell = Table(

                    dimanche_notes_rows,

                    colWidths=[12.2*cm]  # Largeur augmentée de 0,5cm (11,7cm + 0,5cm = 12,2cm)

                )

                dimanche_notes_cell.setStyle(TableStyle([

                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                    ('LEFTPADDING', (0, 0), (-1, -1), 15 + 0.1*cm),  # Décaler les lignes vers la droite de 0,1 cm

                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),

                    ('TOPPADDING', (0, 0), (-1, -1), 2),

                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),

                ]))

                

                # Structure finale : colonne 0 = en-tête, colonnes 1-2 = lignes grises (fusionnées)

                # Le contenu doit être dans la première colonne du SPAN (colonne 1)

                dimanche_row.append(dimanche_header_cell)  # Colonne 0 (Jeudi)

                dimanche_row.append(dimanche_notes_cell)  # Colonne 1 (Vendredi) - sera fusionnée avec colonne 2

                dimanche_row.append(Paragraph("", base_style))  # Colonne 2 (Samedi) - sera fusionnée avec colonne 1

            else:

                dimanche_row = [Paragraph("", base_style)] * 3

            

            page2_data.append(dimanche_row)

            

            # Trouver l'index de la ligne Dimanche (dernière ligne)

            dimanche_row_index = len(page2_data) - 1

            # Trouver l'index de la ligne des en-têtes (après la ligne de la semaine)

            header_row2_index = 1  # La ligne de la semaine est à l'index 0, les en-têtes sont à l'index 1

            semaine_row2_index = 0  # La ligne de la semaine est à l'index 0

            ligne_vide2_index = 2  # La ligne vide est à l'index 2 (après la semaine et les en-têtes)

            

            # Trouver l'index de la dernière ligne horaire (20h)

            # Il y a 1 ligne vide + 13 lignes horaires (8h-20h), donc la dernière est à l'index ligne_vide2_index + 13

            derniere_ligne_horaire2_index = ligne_vide2_index + len(heures)  # ligne_vide2_index (2) + 13 lignes horaires = 15

            # Index de la ligne vide après les heures (juste après la dernière ligne horaire)

            ligne_vide_apres_heures2_index = derniere_ligne_horaire2_index + 1

            

            # Créer le tableau pour la page 2 (format portrait - colonnes plus étroites)

            # Calculer les hauteurs de lignes : ligne semaine (fixe), ligne en-tête (fixe), autres lignes (auto)

            # Hauteur ligne semaine : texte "2026" avec fontSize=18, leading=20 ≈ 0.7cm

            # Hauteur ligne en-tête : header_cell (2.4cm) + TOPPADDING (0.3cm) = 2.7cm

            page2_row_heights = [None] * len(page2_data)  # None = hauteur automatique

            page2_row_heights[semaine_row2_index] = 0.7*cm  # Hauteur fixe pour la ligne de la semaine (identique à page 1)

            page2_row_heights[header_row2_index] = 2.7*cm  # Hauteur fixe pour la ligne d'en-tête

            # Hauteur de la ligne vide = même hauteur que les lignes horaires (2 lignes de 12 points chacune = 24 points ≈ 0.85cm)

            page2_row_heights[ligne_vide2_index] = 24  # Même hauteur que les lignes horaires (2 lignes de 12 points)

            # Hauteur de la ligne vide après les heures (même hauteur qu'une ligne horaire)

            if ligne_vide_apres_heures2_index < len(page2_row_heights):

                page2_row_heights[ligne_vide_apres_heures2_index] = 15  # Hauteur réduite encore plus (24 -> 15)

            page2_table = Table(page2_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm], rowHeights=page2_row_heights)

            page2_table.setStyle(TableStyle([

                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

                ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                # Centrer verticalement la ligne semaine (texte + "2026")

                ('VALIGN', (0, semaine_row2_index), (2, semaine_row2_index), 'MIDDLE'),

                # Pas de bordures pour le style 2 (cadres arrondis dessinés par canvas)

                ('LEFTPADDING', (0, 0), (-1, -1), 0),

                # Décaler le texte "2026" vers la droite (colonne 2, ligne semaine)

                ('LEFTPADDING', (2, semaine_row2_index), (2, semaine_row2_index), 0.3*cm),

                ('RIGHTPADDING', (0, 0), (-1, -1), 0),

                # Padding global par défaut

                ('TOPPADDING', (0, 0), (-1, -1), 0),

                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),

                # Aligné sur page 1 : même TOPPADDING que page 1 pour alignement horizontal identique

                ('TOPPADDING', (0, header_row2_index), (2, header_row2_index), 0.3*cm),  # Même valeur que page 1 (0.3cm) pour alignement horizontal

                # Décaler uniquement le texte de la semaine (colonne 0) vers le bas de 0,5 cm

                ('TOPPADDING', (0, semaine_row2_index), (0, semaine_row2_index), 0.5*cm),

            ]))

            

            elements.append(page2_table)

            

            # Saut de page entre les semaines (sauf pour la dernière)

            if semaine != semaines[-1]:

                elements.append(PageBreak())

        

        # Générer le PDF

        # Utiliser draw_rounded_rects pour que le mini-calendrier soit dessiné avec les mêmes paramètres sur toutes les pages impaires

        try:
            # Log avant génération PDF
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'location': 'projet18_routes.py:export_pdf_multilang_style2:before_build',
                        'message': 'Avant doc.build',
                        'data': {'nb_elements': len(elements)},
                        'sessionId': 'debug-session',
                        'runId': 'run1'
                    }) + '\n')
            except:
                pass

            # Utiliser les callbacks déjà définis sur doc au lieu de les passer en paramètre
            # doc.onFirstPage et doc.onLaterPages sont déjà définis à la ligne 7055-7057
            doc.build(elements)
        except Exception as build_error:
            # Si doc.build échoue, relancer l'erreur pour qu'elle soit capturée par le except principal
            # Log l'erreur avant de la relancer
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'location': 'projet18_routes.py:export_pdf_multilang_style2:build_error',
                        'message': 'Erreur lors de doc.build',
                        'data': {'error': str(build_error), 'traceback': traceback.format_exc()},
                        'sessionId': 'debug-session',
                        'runId': 'run1'
                    }) + '\n')
            except:
                pass
            raise build_error

        buffer.seek(0)
        
        # Lire le contenu du buffer
        pdf_content = buffer.read()
        
        # Vérifier que le contenu n'est pas vide
        if not pdf_content:
            raise ValueError("Le buffer PDF est vide après la génération")

        # Créer la réponse
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        
        # Nom de fichier différent pour indiquer que c'est la version multilingue style 2
        filename = f'agenda_semainier_2026_multilang_style2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'

        # Log avant retour pour vérifier que tout fonctionne
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'location': 'projet18_routes.py:export_pdf_multilang_style2:before_return',
                    'message': 'Avant retour response',
                    'data': {'pdf_size': len(pdf_content), 'filename': filename},
                    'sessionId': 'debug-session',
                    'runId': 'run1'
                }) + '\n')
        except:
            pass

        return response

    

    except Exception as e:

        error_msg = str(e)

        error_trace = traceback.format_exc()

        

        # #region agent log

        try:
            # S'assurer que le dossier existe avant d'écrire
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:

                f.write(json.dumps({

                    'timestamp': datetime.now().isoformat(),

                    'location': 'projet18_routes.py:export_pdf_multilang_style2:error',

                    'message': 'Erreur generation PDF multilingue style 2',

                    'data': {'error': error_msg, 'traceback': error_trace},

                    'sessionId': 'debug-session',

                    'runId': 'run1',

                    'hypothesisId': 'E'

                }) + '\n')
        except:
            pass  # Ignorer les erreurs d'écriture de log

        # #endregion

        
        # Retourner une réponse HTTP avec l'erreur pour faciliter le diagnostic
        from flask import Response
        # Simplifier au maximum pour éviter toute erreur
        try:
            # Essayer d'abord avec JSON
            error_json_str = json.dumps({
                'error': 'Erreur lors de la génération du PDF',
                'message': error_msg[:500],  # Limiter la taille
                'traceback': error_trace[:2000]  # Limiter la taille
            })
            resp = Response(error_json_str, status=500)
            resp.headers['Content-Type'] = 'application/json; charset=utf-8'
            return resp
        except Exception as json_err:
            # Si JSON échoue, utiliser texte simple
            try:
                error_text = f'Erreur: {error_msg[:500]}\n\nTraceback:\n{error_trace[:1000]}'
                resp = Response(error_text, status=500)
                resp.headers['Content-Type'] = 'text/plain; charset=utf-8'
                return resp
            except:
                # Dernier recours : message minimal
                return Response(f'Erreur: {str(e)[:200]}', status=500, mimetype='text/plain')





