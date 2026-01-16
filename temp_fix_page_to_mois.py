# Script temporaire pour corriger l'erreur page_to_mois dans export_pdf_multilang
with open('routes/projet18_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_next = False
skip_count = 0

for i, line in enumerate(lines):
    # Ligne 1693 (index 1692) : commentaire "# Mapper le numéro de page"
    if i == 1692 and '# Mapper le numéro de page au mois correspondant' in line:
        skip_count = 9  # Skip les 9 lignes suivantes
        continue
    if skip_count > 0:
        skip_count -= 1
        continue
    new_lines.append(line)

with open('routes/projet18_routes.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Fixed: Removed page_to_mois references from export_pdf_multilang')








