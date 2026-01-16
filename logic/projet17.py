"""
Projet 17 - Fusion de fichiers HTML
Fusionne le contenu de tous les fichiers HTML du dossier html_sources
"""
import os
from pathlib import Path

def get_all_html_files():
    """Récupère tous les fichiers HTML du dossier html_sources"""
    html_sources_dir = Path(__file__).parent.parent / 'projet17' / 'html_sources'
    
    if not html_sources_dir.exists():
        return []
    
    # Récupérer tous les fichiers .html et .htm
    html_files = []
    for ext in ['*.html', '*.htm']:
        html_files.extend(html_sources_dir.glob(ext))
    
    # Trier par nom de fichier
    html_files.sort(key=lambda x: x.name)
    
    return html_files

def read_html_file_content(file_path):
    """Lit le contenu d'un fichier HTML avec gestion d'erreurs d'encodage et neutralisation des ressources externes"""
    import re
    try:
        # Essayer UTF-8 d'abord
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            # Essayer latin-1 si UTF-8 échoue
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            return f"<p style='color: red;'>Erreur lors de la lecture du fichier: {str(e)}</p>"
    except Exception as e:
        return f"<p style='color: red;'>Erreur lors de la lecture du fichier: {str(e)}</p>"
    
    # Neutraliser les références aux ressources externes pour éviter les erreurs 404
    # Supprimer les balises <link> pour les CSS (qui pointent vers css/, images/, js/)
    content = re.sub(r'<link[^>]*href=["\'](?:css|images|js|static)/[^"\']*["\'][^>]*/?>', '', content, flags=re.IGNORECASE)
    
    # Supprimer les balises <script> avec src vers des fichiers locaux (css/, images/, js/, static/)
    # Gérer les balises auto-fermantes et les balises avec contenu
    content = re.sub(r'<script[^>]*src=["\'](?:css|images|js|static)/[^"\']*["\'][^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<script[^>]*src=["\'](?:css|images|js|static)/[^"\']*["\'][^>]*/?>', '', content, flags=re.IGNORECASE)
    
    # Remplacer les attributs src des images par un placeholder SVG vide (pour éviter les erreurs 404)
    content = re.sub(r'(<img[^>]*\s)src=["\'](?:css|images|js|static)/[^"\']*["\']', r'\1src="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\'%3E%3C/svg%3E"', content, flags=re.IGNORECASE)
    
    # Remplacer les attributs href des liens vers des ressources externes (mais garder les liens vers d'autres fichiers HTML)
    # Ne remplacer que si ce n'est pas un lien vers un autre fichier HTML
    content = re.sub(r'(<a[^>]*\s)href=["\'](?:css|images|js|static)/[^"\']*["\']', r'\1href="#"', content, flags=re.IGNORECASE)
    
    return content

def get_merged_html_content():
    """Fusionne le contenu de tous les fichiers HTML"""
    html_files = get_all_html_files()
    
    if not html_files:
        return "<p>Aucun fichier HTML trouvé dans le dossier html_sources.</p>", 0
    
    merged_content = []
    file_count = 0
    
    for html_file in html_files:
        file_count += 1
        file_name = html_file.name
        file_content = read_html_file_content(html_file)
        
        # Créer un en-tête pour chaque fichier
        header = f"""
        <div class="file-header" id="file-{file_count}">
            <h2 class="file-title">
                <span class="file-number">{file_count}</span>
                <span class="file-name">{file_name}</span>
            </h2>
            <div class="file-separator"></div>
        </div>
        """
        
        # Ajouter le contenu du fichier
        content_section = f"""
        <div class="file-content" data-filename="{file_name}">
            {file_content}
        </div>
        """
        
        merged_content.append(header + content_section)
    
    return '\n'.join(merged_content), file_count











