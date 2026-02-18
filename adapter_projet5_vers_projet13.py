#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour adapter le projet5 de prinects vers le projet13
"""

import re
from pathlib import Path

# Chemins
source_file = Path(r"\\prinects\Apps\logic\projet5.py")
target_file = Path(r"x:\routes\projet13_routes.py")
template_source = Path(r"\\prinects\Apps\templates\projet5.html")
template_target = Path(r"x:\templates\projet13.html")

def adapter_code_projet5_vers_projet13(contenu):
    """Adapte le code du projet5 vers projet13"""
    # Remplacements principaux
    remplacements = [
        # Blueprint et routes
        (r'bp = Blueprint\("projet5"', 'projet13_bp = Blueprint("projet13"'),
        (r'@bp\.route\(', '@projet13_bp.route('),
        (r'url_prefix="/projet5"', 'url_prefix="/projet13"'),
        (r'/projet5/', '/projet13/'),
        (r'"projet5"', '"projet13"'),
        (r"'projet5'", "'projet13'"),
        # Templates
        (r'render_template\("projet5\.html"', 'render_template("projet13.html"'),
        (r'"projet5\.html"', '"projet13.html"'),
        (r"'projet5\.html'", "'projet13.html'"),
        # Logs
        (r'projet5\.log', 'projet13.log'),
        (r"'projet5\.log'", "'projet13.log'"),
        # Imports à adapter
        (r'from db import get_db_cursor, get_table_structure, get_table_data, operation_autorisee', 
         'from db import get_db_cursor'),
        # Supprimer sqlite3 (non utilisé dans notre environnement)
        (r'import sqlite3\n', ''),
        (r'def get_db_connection\(\):.*?return conn\n', ''),
    ]
    
    # Appliquer les remplacements
    for pattern, replacement in remplacements:
        contenu = re.sub(pattern, replacement, contenu, flags=re.MULTILINE | re.DOTALL)
    
    # Ajouter la fonction operation_autorisee si elle n'existe pas
    if 'def operation_autorisee(' not in contenu:
        fonction_operation_autorisee = '''
def operation_autorisee(id_poste, id_operation):
    """Vérifie si une opération est autorisée pour un poste"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM GP_POSTES_OP 
                WHERE ID_POSTE = ? AND ID = ? AND Archive = 0
            """, (id_poste, id_operation))
            count = cursor.fetchone()[0]
            return count > 0
    except Exception as e:
        print(f"Erreur dans operation_autorisee: {e}")
        return False

'''
        # Insérer après les imports
        contenu = contenu.replace(
            'from db import get_db_cursor',
            'from db import get_db_cursor\n' + fonction_operation_autorisee
        )
    
    # Corriger insert_query qui n'est pas défini (ligne 113 du fichier original)
    contenu = re.sub(
        r'cursor\.execute\(insert_query, values\)',
        r'insert_query = f"""\n                    INSERT INTO GP_FICHES_OPERATIONS\n                    ({", ".join(insert_info["columns"])})\n                    VALUES ({", ".join(insert_info["placeholders"])})\n                """\n                cursor.execute(insert_query, values)',
        contenu
    )
    
    # Corriger les erreurs de syntaxe dans set_interrompu (ligne 902)
    contenu = re.sub(r'r\'(\\d{2}):(\\d{2})\'', r"r'(\\d{2}):(\\d{2})'", contenu)
    
    # Corriger recalculer_temps_reel qui prend id_fiche mais reçoit id_traitement
    contenu = re.sub(
        r'recalculer_temps_reel\(id_traitement, cursor\)',
        r'# Recalcul temps réel - récupérer id_fiche depuis id_traitement\n                    cursor.execute("SELECT ID_FICHE_TRAVAIL FROM GP_TRAITEMENTS WHERE ID = ?", (id_traitement,))\n                    row_fiche = cursor.fetchone()\n                    if row_fiche:\n                        recalculer_temps_reel(row_fiche[0], cursor)',
        contenu
    )
    
    return contenu

def adapter_template_projet5_vers_projet13(contenu):
    """Adapte le template HTML du projet5 vers projet13"""
    remplacements = [
        (r'projet5', 'projet13'),
        (r'/projet5/', '/projet13/'),
        (r'"projet5"', '"projet13"'),
        (r"'projet5'", "'projet13'"),
        (r'SUIVI PRODUCTION', 'Projet 13 - Suivi Production'),
        (r'id="projet5Tabs"', 'id="projet13Tabs"'),
        (r'id="projet5TabsContent"', 'id="projet13TabsContent"'),
    ]
    
    for pattern, replacement in remplacements:
        contenu = re.sub(pattern, replacement, contenu)
    
    return contenu

if __name__ == "__main__":
    print("Adaptation du projet5 vers projet13...")
    
    # Adapter le fichier Python
    if source_file.exists():
        print(f"Lecture de {source_file}...")
        with open(source_file, 'r', encoding='utf-8') as f:
            contenu_python = f.read()
        
        print("Adaptation du code Python...")
        contenu_adapte = adapter_code_projet5_vers_projet13(contenu_python)
        
        print(f"Écriture dans {target_file}...")
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(contenu_adapte)
        print(f"✅ Fichier Python créé: {target_file}")
    else:
        print(f"❌ Fichier source non trouvé: {source_file}")
    
    # Adapter le template HTML
    if template_source.exists():
        print(f"Lecture de {template_source}...")
        with open(template_source, 'r', encoding='utf-8') as f:
            contenu_html = f.read()
        
        print("Adaptation du template HTML...")
        contenu_html_adapte = adapter_template_projet5_vers_projet13(contenu_html)
        
        print(f"Écriture dans {template_target}...")
        template_target.parent.mkdir(parents=True, exist_ok=True)
        with open(template_target, 'w', encoding='utf-8') as f:
            f.write(contenu_html_adapte)
        print(f"✅ Template HTML créé: {template_target}")
    else:
        print(f"❌ Template source non trouvé: {template_source}")
    
    print("\n✅ Adaptation terminée!")
