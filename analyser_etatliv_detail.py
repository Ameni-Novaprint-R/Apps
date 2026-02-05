#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script d'analyse detaillee de la colonne EtatLiv dans LIVRAISONS_CMDE"""

from db import get_db_cursor
from datetime import datetime

print("=" * 80)
print("ANALYSE DETAILLEE DE LA COLONNE EtatLiv DANS LIVRAISONS_CMDE")
print("=" * 80)

with get_db_cursor() as cursor:
    # 1. Analyse des patterns pour chaque valeur d'EtatLiv
    print("\n1. ANALYSE DES PATTERNS POUR CHAQUE VALEUR:")
    print("-" * 80)
    
    for etat in [0, 1, 2, 3]:
        print(f"\n   EtatLiv = {etat}:")
        print("   " + "-" * 76)
        
        # Statistiques sur les dates
        cursor.execute("""
            SELECT 
                COUNT(*) as Total,
                SUM(CASE WHEN DteLiv IS NULL THEN 1 ELSE 0 END) as DteLiv_NULL,
                SUM(CASE WHEN DteLiv = '9999-12-31 00:00:00.000' THEN 1 ELSE 0 END) as DteLiv_9999,
                SUM(CASE WHEN DteLiv IS NOT NULL AND DteLiv <> '9999-12-31 00:00:00.000' 
                         AND DteLiv > '1900-01-01' AND DteLiv < '2100-01-01' THEN 1 ELSE 0 END) as DteLiv_Valide,
                MIN(DteLiv) as Date_Min,
                MAX(DteLiv) as Date_Max
            FROM LIVRAISONS_CMDE
            WHERE EtatLiv = ?
        """, (etat,))
        
        stats = cursor.fetchone()
        print(f"   - Total d'enregistrements: {stats[0]}")
        print(f"   - DteLiv NULL: {stats[1]}")
        print(f"   - DteLiv = 9999-12-31: {stats[2]}")
        print(f"   - DteLiv valide: {stats[3]}")
        if stats[4] and str(stats[4]) != '9999-12-31 00:00:00':
            print(f"   - Date minimum: {stats[4]}")
        if stats[5] and str(stats[5]) != '9999-12-31 00:00:00':
            print(f"   - Date maximum: {stats[5]}")
    
    # 2. Comparaison avec EtatLiv dans COMMANDES
    print("\n\n2. COMPARAISON AVEC EtatLiv DANS COMMANDES:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT DISTINCT EtatLiv, COUNT(*) as count
        FROM COMMANDES
        WHERE EtatLiv IS NOT NULL
        GROUP BY EtatLiv
        ORDER BY EtatLiv
    """)
    valeurs_cmd = cursor.fetchall()
    print("   Valeurs dans COMMANDES:")
    for val, count in valeurs_cmd:
        print(f"   - EtatLiv = {val}: {count} occurrences")
    
    # 3. Jointure pour voir la relation entre les deux tables
    print("\n\n3. RELATION ENTRE LIVRAISONS_CMDE.EtatLiv ET COMMANDES.EtatLiv:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            L.EtatLiv as EtatLiv_LIVRAISONS,
            C.EtatLiv as EtatLiv_COMMANDES,
            COUNT(*) as Nombre,
            SUM(CASE WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' 
                     AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' THEN 1 ELSE 0 END) as Avec_Date_Valide
        FROM LIVRAISONS_CMDE L
        INNER JOIN COMMANDES C ON C.ID = L.ID_COMMANDE
        WHERE L.EtatLiv IS NOT NULL AND C.EtatLiv IS NOT NULL
        GROUP BY L.EtatLiv, C.EtatLiv
        ORDER BY L.EtatLiv, C.EtatLiv
    """)
    relations = cursor.fetchall()
    if relations:
        print("   Combinaisons trouvees:")
        for rel in relations:
            print(f"   - LIVRAISONS_CMDE.EtatLiv={rel[0]} + COMMANDES.EtatLiv={rel[1]}: {rel[2]} occurrences ({rel[3]} avec date valide)")
    
    # 4. Recherche dans le code de references aux valeurs
    print("\n\n4. EXEMPLES DE DONNEES POUR CHAQUE ETAT:")
    print("-" * 80)
    
    for etat in [0, 1, 2, 3]:
        cursor.execute("""
            SELECT TOP 2 
                L.ID,
                L.ID_COMMANDE,
                C.Numero,
                C.Termine,
                C.EtatLiv as EtatLiv_CMD,
                L.DteLiv,
                L.EtatLiv
            FROM LIVRAISONS_CMDE L
            LEFT JOIN COMMANDES C ON C.ID = L.ID_COMMANDE
            WHERE L.EtatLiv = ?
            ORDER BY L.ID
        """, (etat,))
        
        exemples = cursor.fetchall()
        print(f"\n   Exemples pour EtatLiv = {etat}:")
        for ex in exemples:
            dte_liv_str = str(ex[5]) if ex[5] else "NULL"
            if dte_liv_str.startswith('9999'):
                dte_liv_str = "9999-12-31 (invalide)"
            print(f"   - ID={ex[0]}, Cmd={ex[2]}, Termine={ex[3]}, EtatLiv_CMD={ex[4]}, DteLiv={dte_liv_str}")
    
    # 5. Analyse des transitions possibles
    print("\n\n5. ANALYSE DES TRANSITIONS D'ETAT:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            L1.EtatLiv as Etat_Avant,
            L2.EtatLiv as Etat_Apres,
            COUNT(*) as Nombre_Transitions
        FROM LIVRAISONS_CMDE L1
        INNER JOIN LIVRAISONS_CMDE L2 ON L1.ID_COMMANDE = L2.ID_COMMANDE AND L1.ID < L2.ID
        GROUP BY L1.EtatLiv, L2.EtatLiv
        ORDER BY L1.EtatLiv, L2.EtatLiv
    """)
    transitions = cursor.fetchall()
    if transitions:
        print("   Transitions d'etat trouvees (pour les memes commandes):")
        for trans in transitions:
            print(f"   - {trans[0]} -> {trans[1]}: {trans[2]} fois")
    else:
        print("   Pas de transitions trouvees (peut-etre une seule livraison par commande)")
    
    # 6. Statistiques par rapport a Termine dans COMMANDES
    print("\n\n6. RELATION AVEC LE CHAMP Termine DANS COMMANDES:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            L.EtatLiv,
            C.Termine,
            COUNT(*) as Nombre,
            SUM(CASE WHEN L.DteLiv IS NOT NULL AND L.DteLiv <> '9999-12-31 00:00:00.000' 
                     AND L.DteLiv > '1900-01-01' AND L.DteLiv < '2100-01-01' THEN 1 ELSE 0 END) as Avec_Date_Valide
        FROM LIVRAISONS_CMDE L
        INNER JOIN COMMANDES C ON C.ID = L.ID_COMMANDE
        WHERE L.EtatLiv IS NOT NULL
        GROUP BY L.EtatLiv, C.Termine
        ORDER BY L.EtatLiv, C.Termine
    """)
    relations_termine = cursor.fetchall()
    if relations_termine:
        print("   Relation EtatLiv / Termine:")
        for rel in relations_termine:
            termine_str = "Termine" if rel[1] == 1 else "Non termine"
            print(f"   - EtatLiv={rel[0]} + {termine_str}: {rel[2]} occurrences ({rel[3]} avec date valide)")

print("\n" + "=" * 80)
print("ANALYSE TERMINEE")
print("=" * 80)
print("\nINTERPRETATION PROBABLE:")
print("-" * 80)
print("EtatLiv = 0: Non livre / En attente (dates invalides)")
print("EtatLiv = 1: Livre (probablement)")
print("EtatLiv = 2: Etat intermediaire (a confirmer)")
print("EtatLiv = 3: Etat intermediaire ou final (a confirmer)")
print("=" * 80)
