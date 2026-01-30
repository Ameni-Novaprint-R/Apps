#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test le rendu du template projet11_liste.html"""

from jinja2 import Environment, FileSystemLoader, Undefined
from flask import Flask

# Créer une app Flask minimale pour avoir accès à url_for
app = Flask(__name__)

with app.app_context():
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('projet11_liste.html')
    
    # Données de test
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
    
    # Fonction format_hhmm pour le template
    def format_hhmm(hours, show_sign=False):
        if hours is None:
            return "-"
        sign = "+" if show_sign and hours > 0 else ("-" if show_sign and hours < 0 else "")
        h = int(abs(hours))
        m = int((abs(hours) - h) * 60)
        return f"{sign}{h:02d}:{m:02d}"
    
    result = template.render(
        traitements=traitements,
        format_hhmm=format_hhmm
    )
    
    # Vérifier si les icônes sont dans le résultat
    if 'fa-file-excel' in result or 'fa-file-pdf' in result or 'export-excel' in result or 'export-pdf' in result:
        print("SUCCES: Les icônes d'export sont dans le rendu du template!")
        import re
        matches = re.findall(r'(fa-file-excel|fa-file-pdf|export-excel|export-pdf)', result)
        print(f"Nombre d'occurrences trouvées: {len(matches)}")
        for m in matches[:5]:
            print(f"  - {m}")
    else:
        print("ERREUR: Les icônes d'export ne sont PAS dans le rendu du template!")
        # Chercher où se termine la colonne Actions
        if 'btn-delete-traitement' in result:
            idx = result.find('btn-delete-traitement')
            print(f"\nContexte autour de btn-delete-traitement:")
            print(result[idx:idx+500])
