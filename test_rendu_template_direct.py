#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test direct du rendu du template pour voir si les icônes sont rendues"""

import sys
sys.path.insert(0, '.')

from flask import Flask
from jinja2 import Environment, FileSystemLoader

app = Flask(__name__)

# Créer un environnement Jinja2 identique à Flask
env = Environment(loader=FileSystemLoader('templates'))

# Ajouter url_for comme fonction globale
def url_for(endpoint, **values):
    # Simulation simple de url_for
    if endpoint == 'projet11.export_statistiques_excel':
        return '/projet11/statistiques/export-excel'
    elif endpoint == 'projet11.export_statistiques_pdf':
        return '/projet11/statistiques/export-pdf'
    return f'/{endpoint}'

env.globals['url_for'] = url_for

# Fonction format_hhmm
def format_hhmm(hours, show_sign=False):
    if hours is None:
        return "-"
    sign = "+" if show_sign and hours > 0 else ("-" if show_sign and hours < 0 else "")
    h = int(abs(hours))
    m = int((abs(hours) - h) * 60)
    return f"{sign}{h:02d}:{m:02d}"

try:
    template = env.get_template('projet11_liste.html')
    
    traitements = [{
        'id': 1,
        'dte_deb': '2026-01-01',
        'dte_fin': None,
        'numero_commande': '123',
        'reference': 'Test',
        'client': 'Client',
        'service': 'Service',
        'poste': 'Poste',
        'postes_reel': None,
        'operateur': 'Op',
        'nb_op': 10,
        'nb_pers': 1,
        'tps_prev_dev': None,
        'tps_reel': None,
        'ecart_temps': None
    }]
    
    result = template.render(traitements=traitements, format_hhmm=format_hhmm)
    
    # Chercher les icônes dans le résultat
    if 'fa-file-excel' in result or 'fa-file-pdf' in result:
        print("SUCCES: Les icônes sont dans le rendu!")
        import re
        # Trouver la section col-actions
        match = re.search(r'<td class="col-actions">.*?</td>', result, re.DOTALL)
        if match:
            print("\nSection col-actions dans le rendu:")
            print(match.group(0)[:500])
    else:
        print("ERREUR: Les icônes ne sont PAS dans le rendu!")
        # Trouver où se termine la colonne Actions
        idx = result.find('btn-delete-traitement')
        if idx > 0:
            print(f"\nContexte autour de btn-delete (position {idx}):")
            print(result[idx:idx+500])
            
except Exception as e:
    print(f"ERREUR lors du rendu: {e}")
    import traceback
    traceback.print_exc()
