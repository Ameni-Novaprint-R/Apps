#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script temporaire pour analyser la structure d'un rapport PDF de controle qualite."""
import pdfplumber
import sys

path = r'x:\projet13\rapports_controle_qualite_exemples\FAMODINE40MG2_260228002 (3).pdf'
out_path = r'x:\projet13\rapports_controle_qualite_exemples\analyse_structure.txt'

def safe(s):
    return (s or '').encode('utf-8', errors='replace').decode('utf-8')

try:
    with open(out_path, 'w', encoding='utf-8') as out:
        with pdfplumber.open(path) as pdf:
            out.write(f'Nombre de pages: {len(pdf.pages)}\n')
            defect_types = set()
            sides = set()
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for t in (tables or []):
                    if t and len(t[0]) >= 4:
                        header = [str(x or '').strip() for x in t[0]]
                        if 'DefectType' in header:
                            for row in t[1:]:
                                if row and len(row) >= 4:
                                    dt = (row[3] or '').strip()
                                    sd = (row[1] or '').strip()
                                    if dt: defect_types.add(dt)
                                    if sd: sides.add(sd)
            out.write(f'Types de defaut trouves: {sorted(defect_types)}\n')
            out.write(f'Cotes/Sides: {sorted(sides)}\n\n')
            for i, page in enumerate(pdf.pages[:8]):
                text = page.extract_text()
                tables = page.extract_tables()
                out.write(f'\n--- PAGE {i+1} ---\n')
                if text:
                    out.write('TEXTE (debut):\n')
                    txt = (text[:3000] if len(text) > 3000 else text).replace('\n', '\n  ')
                    out.write(safe(txt) + '\n')
                if tables:
                    out.write(f'\nTABLES: {len(tables)} table(s)\n')
                    for j, t in enumerate(tables[:5]):
                        out.write(f'  Table {j+1}: {len(t)} lignes\n')
                        if t:
                            for row in t[:12]:
                                out.write('    ' + str(row) + '\n')
    print(f'Analyse ecrite dans {out_path}')
except Exception as e:
    print(f'Erreur: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
