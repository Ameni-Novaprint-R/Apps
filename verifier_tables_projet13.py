#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier l'existence des tables nécessaires pour le Projet 13
"""

from db import get_db_cursor

# Liste des tables nécessaires pour le Projet 13 (basé sur le Projet 5 de prinects)
TABLES_REQUISES = [
    'GP_FICHES_TRAVAIL',
    'GP_TRAITEMENTS',
    'GP_FICHES_OPERATIONS',
    'GP_POSTES',
    'GP_SERVICES',
    'GP_POSTES_OP',
    'GP_FICHTRA_INT',
    'GP_POSTES_TARIF',
    'COMMANDES',
    'SOCIETES',
    'PERSONNES',
    'EMPLOYES',
    'FORMES_DECOUPE',
    'GS_TAMPONS_LIGNES',
    'GP_FACT_ACHATS_SSTR',
    'GP_RESSOURCES_TRAV',
    'GS_MVT_STOCKS',
    'GP_RESSOURCES'
]

def verifier_tables():
    """Vérifie l'existence des tables dans la base de données"""
    print("=" * 60)
    print("VÉRIFICATION DES TABLES POUR LE PROJET 13")
    print("=" * 60)
    
    tables_existantes = []
    tables_manquantes = []
    
    try:
        with get_db_cursor() as cursor:
            # Récupérer toutes les tables de la base
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            toutes_les_tables = [row.TABLE_NAME for row in cursor.fetchall()]
            
            print(f"\n[INFO] Nombre total de tables dans la base: {len(toutes_les_tables)}")
            
            # Vérifier chaque table requise
            for table in TABLES_REQUISES:
                if table in toutes_les_tables:
                    tables_existantes.append(table)
                    print(f"[OK] Table '{table}' existe")
                else:
                    tables_manquantes.append(table)
                    print(f"[MANQUANTE] Table '{table}' n'existe pas")
            
            print("\n" + "=" * 60)
            print("RÉSUMÉ")
            print("=" * 60)
            print(f"Tables existantes: {len(tables_existantes)}/{len(TABLES_REQUISES)}")
            print(f"Tables manquantes: {len(tables_manquantes)}/{len(TABLES_REQUISES)}")
            
            if tables_manquantes:
                print("\n[ATTENTION] Tables manquantes:")
                for table in tables_manquantes:
                    print(f"  - {table}")
                print("\n[ACTION REQUISE] Ces tables doivent être créées ou vérifiées avant d'utiliser le Projet 13.")
            else:
                print("\n[SUCCÈS] Toutes les tables requises existent dans la base de données!")
            
            # Vérifier aussi les colonnes critiques de certaines tables
            print("\n" + "=" * 60)
            print("VÉRIFICATION DES COLONNES CRITIQUES")
            print("=" * 60)
            
            verifications_colonnes = [
                ('GP_FICHES_TRAVAIL', ['ID', 'RefFiche', 'ID_COMMANDE', 'ID_POSTE', 'CodIndAv']),
                ('GP_TRAITEMENTS', ['ID', 'ID_FICHE_TRAVAIL', 'ID_PERSONNE', 'DteDeb', 'HeurDeb', 'DteFin', 'HeurFin', 'NbOp', 'ID_OPERATION']),
                ('GP_POSTES', ['ID', 'Nom', 'ID_SERVICE', 'Archive']),
                ('GP_SERVICES', ['ID', 'Nom', 'Archive']),
                ('GP_POSTES_OP', ['ID', 'ID_POSTE', 'Nom', 'Archive']),
            ]
            
            for table, colonnes in verifications_colonnes:
                if table in tables_existantes:
                    cursor.execute(f"""
                        SELECT COLUMN_NAME 
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_NAME = ?
                    """, (table,))
                    colonnes_existantes = [row.COLUMN_NAME for row in cursor.fetchall()]
                    
                    colonnes_manquantes = [col for col in colonnes if col not in colonnes_existantes]
                    if colonnes_manquantes:
                        print(f"[ATTENTION] Table '{table}' - Colonnes manquantes: {', '.join(colonnes_manquantes)}")
                    else:
                        print(f"[OK] Table '{table}' - Toutes les colonnes critiques existent")
                else:
                    print(f"[SKIP] Table '{table}' n'existe pas - vérification des colonnes ignorée")
            
            return {
                'tables_existantes': tables_existantes,
                'tables_manquantes': tables_manquantes,
                'toutes_les_tables': toutes_les_tables
            }
            
    except Exception as e:
        print(f"\n[ERREUR] Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    resultat = verifier_tables()
    if resultat:
        print("\n" + "=" * 60)
        print("Vérification terminée.")
        print("=" * 60)
