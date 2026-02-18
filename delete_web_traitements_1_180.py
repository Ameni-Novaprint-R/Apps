#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour supprimer les lignes de WEB_TRAITEMENTS avec ID entre 1 et 180
ATTENTION: Cette opération est irréversible !
"""

from db import get_db_cursor

def delete_web_traitements_1_180():
    """
    Supprime toutes les lignes de WEB_TRAITEMENTS avec ID entre 1 et 180
    """
    try:
        with get_db_cursor() as cursor:
            # D'abord, vérifier combien de lignes seront supprimées
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM WEB_TRAITEMENTS
                WHERE ID >= 1 AND ID <= 180
            """)
            count_row = cursor.fetchone()
            count = count_row[0] if count_row else 0
            
            print(f"[ATTENTION] Nombre de lignes a supprimer: {count}")
            
            if count == 0:
                print("[INFO] Aucune ligne a supprimer (ID entre 1 et 180)")
                return True
            
            # Afficher quelques exemples de lignes qui seront supprimées
            cursor.execute("""
                SELECT TOP 5 ID, Numero_COMMANDES, Nom_GP_SERVICES, DteDeb, DteFin
                FROM WEB_TRAITEMENTS
                WHERE ID >= 1 AND ID <= 180
                ORDER BY ID
            """)
            print("\n[EXEMPLES] Lignes qui seront supprimees:")
            print("-" * 80)
            for row in cursor.fetchall():
                print(f"  ID: {row.ID}, Commande: {row.Numero_COMMANDES}, Service: {row.Nom_GP_SERVICES}, Debut: {row.DteDeb}, Fin: {row.DteFin}")
            print("-" * 80)
            
            # Confirmation automatique (déjà confirmée par l'utilisateur)
            print(f"\n[ATTENTION] Suppression de {count} ligne(s) de WEB_TRAITEMENTS")
            print("   Cette operation est IRREVERSIBLE !")
            print("[CONFIRMATION] Suppression confirmee - execution en cours...")
            
            # Exécuter la suppression
            cursor.execute("""
                DELETE FROM WEB_TRAITEMENTS
                WHERE ID >= 1 AND ID <= 180
            """)
            cursor.connection.commit()
            
            rows_deleted = cursor.rowcount
            print(f"[SUCCES] {rows_deleted} ligne(s) supprimee(s) avec succes")
            return True
            
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la suppression: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("SUPPRESSION DES LIGNES WEB_TRAITEMENTS (ID entre 1 et 180)")
    print("=" * 80)
    delete_web_traitements_1_180()
