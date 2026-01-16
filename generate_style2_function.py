#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script pour générer la fonction export_pdf_multilang_style2() modifiée"""

import sys
import re
import inspect
sys.path.insert(0, '.')

from routes.projet18_routes import export_pdf_multilang

# Obtenir le code source de la fonction
src = inspect.getsource(export_pdf_multilang)

# Modifier le nom de la fonction et la route
src_modified = re.sub(r'def export_pdf_multilang\(\):', 'def export_pdf_multilang_style2():', src)
src_modified = re.sub(r"@projet18_bp.route\('/export-pdf-multilang'\)", "@projet18_bp.route('/export-pdf-multilang-style2')", src_modified)
src_modified = re.sub(r'agenda_semainier_2026_multilang_', 'agenda_semainier_2026_multilang_style2_', src_modified)
src_modified = re.sub(r'export_pdf_multilang:start', 'export_pdf_multilang_style2:start', src_modified)
src_modified = re.sub(r'export_pdf_multilang:error', 'export_pdf_multilang_style2:error', src_modified)

# Supprimer toutes les bordures GRID, LINEBELOW, LINEABOVE, LINEBEFORE, LINEAFTER
# Remplacer GRID par des commentaires
src_modified = re.sub(r"\(\s*'GRID',\s*[^)]+\)", "# ('GRID', ...) - Supprimé pour style2", src_modified)
src_modified = re.sub(r"\(\s*'LINEBELOW',\s*[^)]+\)", "# ('LINEBELOW', ...) - Supprimé pour style2", src_modified)
src_modified = re.sub(r"\(\s*'LINEABOVE',\s*[^)]+\)", "# ('LINEABOVE', ...) - Supprimé pour style2", src_modified)
src_modified = re.sub(r"\(\s*'LINEBEFORE',\s*[^)]+\)", "# ('LINEBEFORE', ...) - Supprimé pour style2", src_modified)
src_modified = re.sub(r"\(\s*'LINEAFTER',\s*[^)]+\)", "# ('LINEAFTER', ...) - Supprimé pour style2", src_modified)

# Sauvegarder dans un fichier temporaire
with open('temp_style2_function.txt', 'w', encoding='utf-8') as f:
    f.write(src_modified)

print(f"Fonction générée, longueur: {len(src_modified)} caractères")
print("Fichier sauvegardé dans temp_style2_function.txt")











