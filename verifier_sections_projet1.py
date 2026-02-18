"""Script pour vérifier les sections du projet 1 dans WEB_SECTIONS"""
from db import get_db_cursor

def verifier_sections_projet1():
    try:
        with get_db_cursor() as cursor:
            # Vérifier le projet 1 dans WEB_PROJETS
            cursor.execute("SELECT ID, NumProj, Nom FROM WEB_PROJETS WHERE NumProj = 1")
            projet = cursor.fetchone()
            if not projet:
                print("[ERREUR] Le projet 1 n'existe pas dans WEB_PROJETS")
                return False
            print(f"[OK] Projet trouve: ID={projet.ID}, NumProj={projet.NumProj}, Nom={projet.Nom}")
            
            # Vérifier les sections du projet 1
            cursor.execute("""
                SELECT ID, Nom, ID_Proj, archive
                FROM WEB_SECTIONS
                WHERE ID_Proj = ?
                ORDER BY ID
            """, (projet.ID,))
            sections = cursor.fetchall()
            
            print(f"\n[INFO] Sections trouvees pour le projet 1: {len(sections)}")
            for s in sections:
                print(f"  - ID: {s.ID}, Nom: '{s.Nom}', Archive: {s.archive}")
            
            # Les 3 sections attendues selon le template projet1.html
            sections_attendues = [
                "Planning",
                "Suivi",
                "Performance"
            ]
            
            print(f"\n[INFO] Sections attendues (selon template projet1.html):")
            for nom in sections_attendues:
                trouvee = any(s.Nom.strip().lower() == nom.lower() for s in sections)
                print(f"  - '{nom}': {'TROUVEE' if trouvee else 'MANQUANTE'}")
            
            return True
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verifier_sections_projet1()
