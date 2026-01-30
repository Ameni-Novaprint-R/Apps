#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour forcer Flask à recharger le template projet11_liste.html
en modifiant le fichier de manière significative.
"""

import os
from pathlib import Path
from datetime import datetime

template_path = Path("templates/projet11_liste.html")

if not template_path.exists():
    print(f"[ERREUR] Fichier {template_path} introuvable")
    exit(1)

# Lire le contenu
with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Vérifier si les icônes sont présentes
if 'fa-file-excel' not in content or 'fa-file-pdf' not in content:
    print("[ERREUR] Les icônes d'export ne sont pas dans le template!")
    exit(1)

# Ajouter un commentaire avec timestamp pour forcer le rechargement
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
comment = f"<!-- TEMPLATE MODIFIE LE {timestamp} -->\n"

# Trouver la position après le bouton delete
if 'btn-delete-traitement' in content:
    idx = content.find('</button>', content.find('btn-delete-traitement'))
    if idx > 0:
        # Insérer le commentaire après le bouton delete
        new_content = content[:idx+9] + '\n                                        ' + comment + '                                        ' + content[idx+9:]
        
        # Écrire le nouveau contenu
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"[SUCCES] Template modifié avec timestamp {timestamp}")
        print("[INFO] Redémarrez Flask pour voir les changements")
    else:
        print("[ERREUR] Impossible de trouver la position d'insertion")
else:
    print("[ERREUR] btn-delete-traitement non trouvé dans le template")
