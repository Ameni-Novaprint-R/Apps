#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour vérifier et corriger le nom du Projet 1 dans WEB_PROJETS.
"""

from db import get_db_cursor

def verifier_et_corriger_projet1():
    """Vérifie et corrige le nom du Projet 1"""
    
    print("=" * 70)
    print("Vérification et correction du Projet 1")
    print("=" * 70)
    print()
    
    try:
        with get_db_cursor() as cursor:
            # Vérifier l'état actuel
            cursor.execute("SELECT NumProj, CodeProj, Nom FROM WEB_PROJETS WHERE NumProj = 1")
            row = cursor.fetchone()
            
            if not row:
                print("[ERREUR] Le Projet 1 n'existe pas dans WEB_PROJETS")
                return False
            
            num_proj, code_proj, nom_actuel = row
            nouveau_nom = "Planning & Suivi des Délais de Livraison"
            
            print(f"[INFO] État actuel du Projet 1:")
            print(f"  - NumProj: {num_proj}")
            print(f"  - CodeProj: {code_proj}")
            print(f"  - Nom actuel: {nom_actuel}")
            print()
            
            if nom_actuel == nouveau_nom:
                print(f"[OK] Le nom est déjà correct : {nom_actuel}")
                print("=" * 70)
                return True
            
            print(f"[INFO] Mise à jour nécessaire...")
            print(f"[INFO] Ancien nom : {nom_actuel}")
            print(f"[INFO] Nouveau nom : {nouveau_nom}")
            print()
            
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
                print(f"[ERREUR] La mise à jour n'a pas fonctionné. Nom actuel : {row[0] if row else 'None'}")
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
    verifier_et_corriger_projet1()
