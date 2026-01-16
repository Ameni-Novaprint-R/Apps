"""Test du projet 17"""
import sys
sys.path.insert(0, r'c:\Apps')

try:
    from routes.projet17_routes import projet17_bp
    print("OK - Import projet17_bp")
except Exception as e:
    print(f"ERREUR import projet17_bp: {e}")
    sys.exit(1)

try:
    from logic.projet17 import get_all_html_files, get_merged_html_content
    print("OK - Import logic.projet17")
    
    files = get_all_html_files()
    print(f"OK - Fichiers HTML trouves: {len(files)}")
    
    if len(files) > 0:
        print(f"   Premier fichier: {files[0].name}")
        print(f"   Dernier fichier: {files[-1].name}")
    
except Exception as e:
    print(f"ERREUR logic.projet17: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nOK - Tous les tests sont passes!")











