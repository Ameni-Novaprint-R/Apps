#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour renommer le Projet 1 dans la table WEB_PROJETS.

Ancien nom : Planning
Nouveau nom : Planning & Suivi des Délais de Livraison
"""

from db import get_db_cursor

def renommer_projet1():
    """Renomme le Projet 1 dans WEB_PROJETS"""
    
    print("=" * 70)
    print("Renommage du Projet 1")
    print("=" * 70)
    print()
    
    try:
        with get_db_cursor() as cursor:
            # Vérifier que le projet 1 existe
            cursor.execute("SELECT Nom FROM WEB_PROJETS WHERE NumProj = 1")
            row = cursor.fetchone()
            
            if not row:
                print("[ERREUR] Le Projet 1 n'existe pas dans WEB_PROJETS")
                return False
            
            ancien_nom = row[0]
            nouveau_nom = "Planning & Suivi des Délais de Livraison"
            
            print(f"[INFO] Ancien nom : {ancien_nom}")
            print(f"[INFO] Nouveau nom : {nouveau_nom}")
            
            # Mettre à jour le nom
            cursor.execute("""
                UPDATE WEB_PROJETS 
                SET Nom = ? 
                WHERE NumProj = 1
            """, nouveau_nom)
            
            cursor.connection.commit()
            
            # Vérifier la mise à jour
            cursor.execute("SELECT Nom FROM WEB_PROJETS WHERE NumProj = 1")
            row = cursor.fetchone()
            
            if row and row[0] == nouveau_nom:
                print(f"[OK] Projet 1 renommé avec succès : {row[0]}")
                print("=" * 70)
                return True
            else:
                print("[ERREUR] La mise à jour n'a pas fonctionné")
                return False
                
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        try:
            cursor.connection.rollback()
        except Exception:
            pass
        return False

if __name__ == "__main__":
    renommer_projet1()
