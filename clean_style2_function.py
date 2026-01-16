#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script pour nettoyer et finaliser la fonction export_pdf_multilang_style2()"""

import re

# Lire le fichier temporaire
with open('temp_style2_function.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Supprimer proprement toutes les lignes de bordures (GRID, LINEBELOW, etc.)
# Pattern pour trouver et supprimer les lignes de bordures
patterns_to_remove = [
    r"# \('GRID',[^\n]+\)[^\n]*\n",
    r"# \('LINEBELOW',[^\n]+\)[^\n]*\n",
    r"# \('LINEABOVE',[^\n]+\)[^\n]*\n",
    r"# \('LINEBEFORE',[^\n]+\)[^\n]*\n",
    r"# \('LINEAFTER',[^\n]+\)[^\n]*\n",
]

for pattern in patterns_to_remove:
    content = re.sub(pattern, '', content)

# Ajouter les callbacks canvas pour dessiner les rectangles arrondis
# Trouver la création du SimpleDocTemplate
doc_template_pattern = r"(doc = SimpleDocTemplate\([^)]+\))"

# Ajouter les callbacks après la création du doc
def add_canvas_callbacks(match):
    doc_creation = match.group(1)
    # Ajouter les callbacks pour dessiner les rectangles arrondis
    callbacks = """
        
        # Callbacks pour dessiner les rectangles arrondis autour des blocs
        def draw_rounded_rects(canvas, doc):
            \"\"\"Dessine des rectangles arrondis autour des blocs spécifiés\"\"\"
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            
            # Paramètres des rectangles arrondis
            radius = 0.2*cm  # Rayon des coins arrondis
            stroke_width = 1  # Épaisseur du trait
            stroke_color = colors.HexColor('#000000')  # Couleur noire
            
            # TODO: Calculer les positions exactes des blocs pour dessiner les rectangles
            # Pour l'instant, les positions seront calculées dynamiquement
            # Les rectangles seront dessinés autour de :
            # 1. Les blocs date/jour/jour férié (header_cell)
            # 2. Le mini-calendrier (cal_table)
            # 3. Le dimanche avec date et jour férié (dimanche_header_cell)
            
            # Les positions seront calculées en fonction de la position des tables dans le document
            # Pour l'instant, cette fonction est un placeholder
            pass
        
        # Ajouter les callbacks au document
        doc.onFirstPage = lambda canvas, doc: draw_rounded_rects(canvas, doc)
        doc.onLaterPages = lambda canvas, doc: draw_rounded_rects(canvas, doc)
"""
    return doc_creation + callbacks

content = re.sub(doc_template_pattern, add_canvas_callbacks, content, count=1)

# Sauvegarder la version nettoyée
with open('temp_style2_function_clean.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fonction nettoyée et sauvegardée dans temp_style2_function_clean.txt")
print(f"Longueur: {len(content)} caractères")











