#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer un Gist GitHub avec les fichiers du Projet 18
"""
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Erreur: Le module 'requests' n'est pas installé.")
    print("Installez-le avec: pip install requests")
    sys.exit(1)

def read_file_content(file_path):
    """Lit le contenu d'un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Erreur lors de la lecture de {file_path}: {e}")
        return None

def create_gist(github_token, files, description="Projet 18 - Agenda Semainier 2026", public=False):
    """Crée un Gist GitHub"""
    url = "https://api.github.com/gists"
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "description": description,
        "public": public,
        "files": files
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la création du Gist: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Réponse: {e.response.text}")
        return None

def main():
    # Chemins des fichiers du projet 18
    base_dir = Path(__file__).parent
    files_to_upload = {
        "routes/projet18_routes.py": base_dir / "routes" / "projet18_routes.py",
        "logic/projet18.py": base_dir / "logic" / "projet18.py",
        "templates/projet18.html": base_dir / "templates" / "projet18.html",
        "PROJET18_README.md": base_dir / "PROJET18_README.md"
    }
    
    # Lire les fichiers
    files_content = {}
    for gist_filename, file_path in files_to_upload.items():
        if not file_path.exists():
            print(f"Attention: Le fichier {file_path} n'existe pas.")
            continue
        
        content = read_file_content(file_path)
        if content is not None:
            files_content[gist_filename] = {"content": content}
            print(f"✓ Fichier lu: {gist_filename}")
    
    if not files_content:
        print("Erreur: Aucun fichier à uploader.")
        sys.exit(1)
    
    # Demander le token GitHub
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("\n" + "="*60)
        print("Pour créer un Gist, vous avez besoin d'un token GitHub.")
        print("="*60)
        print("\n1. Créez un token GitHub:")
        print("   - Allez sur https://github.com/settings/tokens")
        print("   - Cliquez sur 'Generate new token (classic)'")
        print("   - Cochez la case 'gist' dans les permissions")
        print("   - Copiez le token généré")
        print("\n2. Utilisez l'une de ces méthodes:")
        print("   a) Définissez la variable d'environnement:")
        print("      Windows PowerShell: $env:GITHUB_TOKEN='votre_token'")
        print("      Windows CMD: set GITHUB_TOKEN=votre_token")
        print("   b) Entrez le token maintenant:")
        github_token = input("\nToken GitHub: ").strip()
    
    if not github_token:
        print("Erreur: Token GitHub requis.")
        sys.exit(1)
    
    # Demander si le Gist doit être public
    print("\nLe Gist doit-il être public? (o/n, défaut: n)")
    public_input = input().strip().lower()
    public = public_input in ['o', 'oui', 'y', 'yes']
    
    # Description
    description = "Projet 18 - Agenda Semainier 2026 (Tunisie)\n\n" \
                 "Application Flask pour générer un agenda semainier 2026 avec:\n" \
                 "- Génération de PDF avec ReportLab\n" \
                 "- Support multilingue (Français, Anglais, Arabe)\n" \
                 "- Jours fériés tunisiens\n" \
                 "- Format Quo Vadis (2 pages par semaine)\n\n" \
                 "Fichiers inclus:\n" \
                 "- routes/projet18_routes.py (Routes Flask et génération PDF)\n" \
                 "- logic/projet18.py (Logique métier: semaines, jours fériés)\n" \
                 "- templates/projet18.html (Interface web)\n" \
                 "- PROJET18_README.md (Documentation complète)"
    
    print(f"\nCréation du Gist avec {len(files_content)} fichier(s)...")
    
    # Créer le Gist
    result = create_gist(github_token, files_content, description, public)
    
    if result:
        gist_url = result.get('html_url')
        gist_id = result.get('id')
        print("\n" + "="*60)
        print("✓ Gist créé avec succès!")
        print("="*60)
        print(f"\nURL du Gist: {gist_url}")
        print(f"ID du Gist: {gist_id}")
        print(f"Visibilité: {'Public' if public else 'Secret'}")
        print(f"\nFichiers inclus:")
        for filename in files_content.keys():
            print(f"  - {filename}")
        print("\n" + "="*60)
    else:
        print("\n✗ Échec de la création du Gist.")
        sys.exit(1)

if __name__ == "__main__":
    main()











