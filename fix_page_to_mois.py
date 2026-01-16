# Script pour corriger l'erreur page_to_mois dans export_pdf_multilang
with open('routes/projet18_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_export_multilang = False
skip_count = 0

for i, line in enumerate(lines):
    # Détecter le début de export_pdf_multilang
    if '@projet18_bp.route(\'/export-pdf-multilang\')' in line or 'def export_pdf_multilang():' in line:
        in_export_multilang = True
    # Détecter le début de export_pdf_multilang_style2 (fin de export_pdf_multilang)
    elif '@projet18_bp.route(\'/export-pdf-multilang-style2\')' in line or 'def export_pdf_multilang_style2():' in line:
        in_export_multilang = False
    
    # Dans export_pdf_multilang, supprimer les lignes qui utilisent page_to_mois
    if in_export_multilang and '# Mapper le numéro de page au mois correspondant (uniquement dans export_pdf_multilang_style2)' in line:
        skip_count = 9  # Skip les 9 lignes suivantes (commentaires + code)
        continue
    
    if skip_count > 0:
        skip_count -= 1
        continue
    
    new_lines.append(line)

with open('routes/projet18_routes.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Fixed: Removed page_to_mois references from export_pdf_multilang')








