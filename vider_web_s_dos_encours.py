#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour vider la table WEB_S_DOS_ENCOURS et réinitialiser l'ID
- Supprime toutes les données de la table WEB_S_DOS_ENCOURS
- Réinitialise le compteur IDENTITY pour recommencer la numérotation à partir de 1
La table doit rester vide par défaut selon les nouvelles règles
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from db import get_db_cursor

def vider_table():
    """Vide la table WEB_S_DOS_ENCOURS et réinitialise l'ID pour recommencer à partir de 1"""
    
    print("=" * 80)
    print("Vidage de la table WEB_S_DOS_ENCOURS")
    print("=" * 80)
    print()
    
    try:
        with get_db_cursor() as cursor:
            # Compter les lignes avant suppression
            cursor.execute("SELECT COUNT(*) FROM WEB_S_DOS_ENCOURS")
            count_before = cursor.fetchone()[0]
            
            if count_before == 0:
                print("[INFO] La table WEB_S_DOS_ENCOURS est deja vide.")
                return
            
            print(f"[INFO] Nombre de lignes a supprimer: {count_before}")
            
            # Vider la table
            print("Suppression de toutes les lignes...")
            cursor.execute("DELETE FROM WEB_S_DOS_ENCOURS")
            cursor.connection.commit()
            
            # Réinitialiser l'ID pour recommencer à partir de 1
            print("Réinitialisation de l'ID (IDENTITY) pour recommencer à partir de 1...")
            cursor.execute("DBCC CHECKIDENT('WEB_S_DOS_ENCOURS', RESEED, 0)")
            cursor.connection.commit()
            
            # Vérifier
            cursor.execute("SELECT COUNT(*) FROM WEB_S_DOS_ENCOURS")
            count_after = cursor.fetchone()[0]
            
            # Vérifier la valeur actuelle de l'IDENTITY
            cursor.execute("""
                SELECT IDENT_CURRENT('WEB_S_DOS_ENCOURS') AS CurrentIdentity
            """)
            current_identity = cursor.fetchone()[0]
            
            print(f"[OK] {count_before} lignes supprimees")
            print(f"[OK] Nombre de lignes restantes: {count_after}")
            print(f"[OK] ID réinitialisé - Prochain ID sera: 1")
            print()
            print("=" * 80)
            print("[OK] Table WEB_S_DOS_ENCOURS videe avec succes !")
            print("[OK] ID réinitialisé pour recommencer la numérotation à partir de 1")
            print("=" * 80)
            
    except Exception as e:
        print(f"[ERREUR] Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    vider_table()




