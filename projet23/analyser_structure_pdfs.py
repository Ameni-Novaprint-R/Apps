#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script temporaire pour analyser la structure des PDFs du projet 23."""
import pdfplumber
from pathlib import Path
import sys

def safe(s):
    return (s or '').encode('utf-8', errors='replace').decode('utf-8')

def analyse_solde_tresorerie():
    p = Path(r'x:\projet23\donnees_a_analyser\solde_tresorerie\SITUATION_DES_COMPTES_BANCAIRES_SYNTHETISEE_DU_25-02_AU_05-03-2026.pdf')
    out = Path(r'x:\projet23\analyse_structure_solde.txt')
    print('Analyse solde trésorerie...')
    if not p.exists():
        print(f'Fichier non trouvé: {p}')
        return
    with open(out, 'w', encoding='utf-8') as f:
        with pdfplumber.open(p) as pdf:
            f.write(f'Nombre de pages: {len(pdf.pages)}\n\n')
            for i, page in enumerate(pdf.pages):
                txt = page.extract_text() or ''
                tables = page.extract_tables()
                f.write(f'\n=== PAGE {i+1} ===\n')
                f.write('TEXTE:\n' + safe(txt[:4000]) + '\n\n')
                f.write(f'TABLES: {len(tables or [])}\n')
                for j, t in enumerate(tables or []):
                    f.write(f'  Table {j+1}: {len(t)} lignes\n')
                    for row in (t or [])[:25]:
                        f.write('    ' + str(row) + '\n')
    print(f'Écrit dans {out}')

def analyse_lignes_financement():
    p = Path(r'x:\projet23\donnees_a_analyser\lignes_financement\Ligne_Fin._Plac._26-02-202613.pdf')
    out = Path(r'x:\projet23\analyse_structure_lignes.txt')
    print('Analyse lignes financement...')
    if not p.exists():
        print(f'Fichier non trouvé: {p}')
        return
    with open(out, 'w', encoding='utf-8') as f:
        with pdfplumber.open(p) as pdf:
            f.write(f'Nombre de pages: {len(pdf.pages)}\n\n')
            for i, page in enumerate(pdf.pages):
                txt = page.extract_text() or ''
                tables = page.extract_tables()
                f.write(f'\n=== PAGE {i+1} ===\n')
                f.write('TEXTE:\n' + safe(txt[:4000]) + '\n\n')
                f.write(f'TABLES: {len(tables or [])}\n')
                for j, t in enumerate(tables or []):
                    f.write(f'  Table {j+1}: {len(t)} lignes\n')
                    for row in (t or [])[:30]:
                        f.write('    ' + str(row) + '\n')
    print(f'Écrit dans {out}')

if __name__ == '__main__':
    analyse_solde_tresorerie()
    analyse_lignes_financement()
    print('Terminé.')
