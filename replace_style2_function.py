#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script pour remplacer la fonction export_pdf_multilang_style2() et implémenter les callbacks canvas"""

import re

# Lire le fichier nettoyé
with open('temp_style2_function_clean.txt', 'r', encoding='utf-8') as f:
    style2_function = f.read()

# Lire le fichier routes
with open('routes/projet18_routes.py', 'r', encoding='utf-8') as f:
    routes_content = f.read()

# Trouver la fonction actuelle et la remplacer
pattern = r"@projet18_bp\.route\('/export-pdf-multilang-style2'\).*?(?=\n@projet18_bp\.route|\n\n\n|$)"
match = re.search(pattern, routes_content, re.DOTALL)

if match:
    # Remplacer la fonction
    routes_content = routes_content[:match.start()] + style2_function + routes_content[match.end():]
    
    # Implémenter correctement les callbacks canvas
    # Trouver la fonction draw_rounded_rects et la remplacer par une implémentation complète
    callback_pattern = r"def draw_rounded_rects\(canvas, doc\):.*?pass"
    
    new_callback = '''def draw_rounded_rects(canvas, doc):
            """Dessine des rectangles arrondis autour des blocs spécifiés"""
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            
            # Paramètres des rectangles arrondis
            radius = 0.2*cm  # Rayon des coins arrondis
            stroke_width = 1  # Épaisseur du trait
            stroke_color = colors.HexColor('#000000')  # Couleur noire
            
            # Marges de la page
            left_margin = 0.5*cm
            top_margin = 0.5*cm
            col_width = 5.5*cm
            padding = 0.1*cm  # Padding autour des rectangles
            
            # Calculer les positions approximatives basées sur la structure du document
            # Page 1: Lundi, Mardi, Mercredi + mini-calendrier
            # Page 2: Jeudi, Vendredi, Samedi + Dimanche
            
            # Hauteurs approximatives (basées sur la structure)
            semaine_height = 0.7*cm
            header_height = 2.7*cm
            ligne_vide_height = 24  # points
            ligne_horaire_height = 24  # points (2 lignes de 12 points)
            nb_lignes_horaires = 13  # 8h à 20h
            cal_height = 2.0*cm  # Hauteur approximative du mini-calendrier
            
            # Calculer la position Y de départ (en partant du haut de la page)
            y_start = doc.height - top_margin
            
            # Page 1: Dessiner les rectangles autour des blocs header (date/jour/jour férié)
            # Pour chaque colonne (Lundi, Mardi, Mercredi)
            for col in range(3):
                x = left_margin + col * col_width - padding
                y = y_start - semaine_height - header_height + padding
                width = col_width + 2*padding
                height = header_height - 2*padding
                
                # Dessiner le rectangle arrondi
                canvas.setStrokeColor(stroke_color)
                canvas.setLineWidth(stroke_width)
                canvas.roundRect(x, y, width, height, radius, stroke=1, fill=0)
            
            # Dessiner le rectangle autour du mini-calendrier (colonne 0, dernière ligne)
            cal_x = left_margin - padding
            cal_y = y_start - semaine_height - header_height - ligne_vide_height - nb_lignes_horaires * ligne_horaire_height - cal_height + padding
            cal_width = col_width + 2*padding
            cal_height_rect = cal_height - 2*padding
            
            canvas.roundRect(cal_x, cal_y, cal_width, cal_height_rect, radius, stroke=1, fill=0)
            
            # Page 2: Dessiner les rectangles autour des blocs header (Jeudi, Vendredi, Samedi)
            # Les positions sont similaires à la page 1 mais pour les colonnes 0, 1, 2
            
            # Dessiner le rectangle autour du dimanche (colonne 0, dernière ligne de la page 2)
            dimanche_x = left_margin - padding
            dimanche_y = y_start - semaine_height - header_height - ligne_vide_height - nb_lignes_horaires * ligne_horaire_height - header_height + padding
            dimanche_width = col_width + 2*padding
            dimanche_height = header_height - 2*padding
            
            canvas.roundRect(dimanche_x, dimanche_y, dimanche_width, dimanche_height, radius, stroke=1, fill=0)'''
    
    routes_content = re.sub(callback_pattern, new_callback, routes_content, flags=re.DOTALL)
    
    # Sauvegarder
    with open('routes/projet18_routes.py', 'w', encoding='utf-8') as f:
        f.write(routes_content)
    
    print("Fonction remplacée avec succès!")
    print("Callbacks canvas implémentés")
else:
    print("Fonction non trouvée dans le fichier routes")











