#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script pour corriger l'erreur de syntaxe dans projet18_routes.py"""

missing_code = """                            rowHeights=[12, 12]  # Hauteur exactement égale au leading pour garantir exactement 2 lignes sans ligne supplémentaire
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
                        textColor=colors.HexColor('#0066CC'),
                        alignment=TA_CENTER,
                        leading=30  # Augmenter leading pour éviter superposition
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
                ], colWidths=[5.5*cm], rowHeights=[1.2*cm, 0.8*cm])  # Hauteurs explicites pour éviter superposition
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
                        ('ALIGN', (0, 1), (0, 1), 'CENTER'),  # Jours centrés
                        ('LEFTPADDING', (0, 0), (-1, -1), 2),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                        ('TOPPADDING', (0, 0), (0, 0), 4),  # Padding réduit pour la date (décalée vers le haut)
                        ('BOTTOMPADDING', (0, 0), (0, 0), 4),  # Espacement entre date et jours
                        ('TOPPADDING', (0, 1), (0, 1), 2),  # Padding réduit pour les jours (décalés vers le haut)
                        ('BOTTOMPADDING', (0, 1), (0, 1), 0),  # Pas de padding en bas des jours quand il y a un jour férié
                    ]))
                    dimanche_ferie_para = Paragraph(
                        f"<font color='#FF0000'>{nom_ferie}</font>",
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
                    dimanche_notes_rows.append([Paragraph("_" * 60, ligne_note_style)])
                
                dimanche_notes_cell = Table(
                    dimanche_notes_rows,
                    colWidths=[11*cm]  # Largeur de 2 colonnes (5.5cm + 5.5cm)
                )
                dimanche_notes_cell.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),  # Padding à gauche réduit pour décaler un peu les lignes vers la gauche
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
            # Hauteur ligne semaine : texte "2026" avec fontSize=18, leading=20 ≈ 0.7cm
            # Hauteur ligne en-tête : header_cell (2.4cm) + TOPPADDING (0.3cm) = 2.7cm
            page2_row_heights = [None] * len(page2_data)  # None = hauteur automatique
            page2_row_heights[semaine_row2_index] = 0.7*cm  # Hauteur fixe pour la ligne de la semaine (identique à page 1)
            page2_row_heights[header_row2_index] = 2.7*cm  # Hauteur fixe pour la ligne d'en-tête
            # Hauteur de la ligne vide = même hauteur que les lignes horaires (2 lignes de 12 points chacune = 24 points ≈ 0.85cm)
            page2_row_heights[ligne_vide2_index] = 24  # Même hauteur que les lignes horaires (2 lignes de 12 points)
            page2_table = Table(page2_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm], rowHeights=page2_row_heights)
            page2_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                # Pas de bordures pour le style 2 (cadres arrondis dessinés par canvas)
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
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
        doc.build(elements, onFirstPage=draw_rounded_rects_page1, onLaterPages=draw_rounded_rects_page2)
        buffer.seek(0)
        
        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        # Nom de fichier différent pour indiquer que c'est la version multilingue style 2
        response.headers['Content-Disposition'] = f'attachment; filename=agenda_semainier_2026_multilang_style2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        return response
    
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        # #region agent log
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
        # #endregion
        
        raise
"""

# Lire le fichier
with open('routes/projet18_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ajouter le code manquant
content += missing_code

# Écrire le fichier
with open('routes/projet18_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Code manquant ajouté avec succès!")










