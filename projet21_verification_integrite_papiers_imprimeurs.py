#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vérification complète de l'intégrité des données après réalignement des IDs
Table: PAPIERS_IMPRIMEURS

Vérifie:
- Préservation de tous les enregistrements
- Intégrité des clés étrangères (2 FK entrantes)
- Cohérence des tables liées
- Absence de perte ou duplication de données
- Validité des contraintes et index
- Volume de données identique
"""

import pyodbc
from datetime import datetime
import json

# Configuration des bases de données
SOURCE_CONFIG = {
    'server': 'SageSRV\\Graphisoft',
    'database': 'Novaprint',
    'username': 'sa',
    'password': 'Graphis0ft'
}

TARGET_CONFIG = {
    'server': '192.168.10.225',
    'database': 'novaprint_restored',
    'trusted_connection': True
}

def get_connection(config, readonly=False):
    """Connexion SQL Server"""
    if config.get('trusted_connection'):
        driver_candidates = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]
        last_err = None
        conn = None
        for drv in driver_candidates:
            try:
                conn_str = (
                    f"DRIVER={{{drv}}};"
                    f"SERVER={config['server']};"
                    f"DATABASE={config['database']};"
                    f"Trusted_Connection=yes;"
                    f"TrustServerCertificate=yes"
                )
                conn = pyodbc.connect(conn_str)
                break
            except Exception as e:
                last_err = e
                conn = None
        if conn is None:
            raise last_err
    else:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={config['server']};"
            f"DATABASE={config['database']};"
            f"UID={config['username']};"
            f"PWD={config['password']}"
        )
        conn = pyodbc.connect(conn_str)
    if readonly:
        conn.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
    return conn

def verification_complete():
    """Effectue une vérification complète de l'intégrité"""
    
    print("="*80)
    print("VERIFICATION DE L'INTEGRITE APRES REALIGNEMENT")
    print("Table: PAPIERS_IMPRIMEURS")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    source_conn = None
    target_conn = None
    rapport = {
        'date_verification': datetime.now().isoformat(),
        'table_verifiee': 'PAPIERS_IMPRIMEURS',
        'verifications': {},
        'resultat_global': 'EN_ATTENTE',
        'risques_detectes': []
    }
    
    try:
        # Connexions
        print("[1/9] Connexion aux bases de donnees...")
        source_conn = get_connection(SOURCE_CONFIG, readonly=True)
        target_conn = get_connection(TARGET_CONFIG, readonly=True)
        print("  [OK] Connexions etablies")
        print()
        
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # ========================================================================
        # VÉRIFICATION 1: Volume de Données
        # ========================================================================
        print("[2/9] Verification du volume de donnees...")
        
        source_cursor.execute("SELECT COUNT(*) FROM PAPIERS_IMPRIMEURS")
        source_count = source_cursor.fetchone()[0]
        
        target_cursor.execute("SELECT COUNT(*) FROM PAPIERS_IMPRIMEURS")
        target_count = target_cursor.fetchone()[0]
        
        print(f"  Source (Novaprint): {source_count:,} lignes")
        print(f"  Cible (novaprint_restored): {target_count:,} lignes")
        
        diff = target_count - source_count
        if diff == 0:
            print("  [OK] Nombre d'enregistrements identique")
            rapport['verifications']['volume'] = {'statut': 'OK', 'source': source_count, 'cible': target_count, 'difference': 0}
        elif diff > 0:
            print(f"  [ATTENTION] {diff:,} enregistrements supplementaires en cible")
            rapport['verifications']['volume'] = {'statut': 'ATTENTION', 'source': source_count, 'cible': target_count, 'difference': diff}
        else:
            print(f"  [ERREUR] {abs(diff):,} enregistrements manquants en cible")
            rapport['verifications']['volume'] = {'statut': 'ERREUR', 'source': source_count, 'cible': target_count, 'difference': diff}
            rapport['risques_detectes'].append(f"Perte de {abs(diff)} enregistrements")
        
        print()
        
        # ========================================================================
        # VÉRIFICATION 2: Correspondance des IDs
        # ========================================================================
        print("[3/9] Verification de la correspondance des IDs...")
        
        # Identifier les colonnes communes (sauf ID)
        source_cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'PAPIERS_IMPRIMEURS'
            AND COLUMN_NAME != 'ID'
            ORDER BY ORDINAL_POSITION
        """)
        source_columns = set(row[0] for row in source_cursor.fetchall())
        
        target_cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'PAPIERS_IMPRIMEURS'
            AND COLUMN_NAME != 'ID'
            ORDER BY ORDINAL_POSITION
        """)
        target_columns = set(row[0] for row in target_cursor.fetchall())
        
        columns = sorted(list(source_columns & target_columns))
        columns_str = ', '.join(columns)
        
        # Comparer les IDs en lisant les données des deux bases
        source_cursor.execute(f"""
            SELECT ID, ID_PAPIER, ID_IMPRIMEUR, {columns_str}
            FROM PAPIERS_IMPRIMEURS
        """)
        source_data = {}
        for row in source_cursor.fetchall():
            key = (row[1], row[2])  # ID_PAPIER, ID_IMPRIMEUR
            source_data[key] = row[0]  # ID source
        
        target_cursor.execute(f"""
            SELECT ID, ID_PAPIER, ID_IMPRIMEUR, {columns_str}
            FROM PAPIERS_IMPRIMEURS
        """)
        
        mismatch_count = 0
        for row in target_cursor.fetchall():
            key = (row[1], row[2])  # ID_PAPIER, ID_IMPRIMEUR
            if key in source_data:
                if row[0] != source_data[key]:
                    mismatch_count += 1
        
        if mismatch_count == 0:
            print("  [OK] Tous les IDs correspondent")
            rapport['verifications']['correspondance_ids'] = {'statut': 'OK', 'mismatches': 0}
        else:
            print(f"  [ERREUR] {mismatch_count} IDs ne correspondent pas")
            rapport['verifications']['correspondance_ids'] = {'statut': 'ERREUR', 'mismatches': mismatch_count}
            rapport['risques_detectes'].append(f"{mismatch_count} IDs ne correspondent pas")
        
        print()
        
        # ========================================================================
        # VÉRIFICATION 3: Intégrité des FK Entrantes - PAPIERS_TARIF_FMT
        # ========================================================================
        print("[4/9] Verification de l'integrite des FK entrantes (PAPIERS_TARIF_FMT)...")
        
        target_cursor.execute("""
            SELECT 
                COUNT(*) AS total_references,
                COUNT(DISTINCT ID_PAPIMPRIM) AS references_distinctes,
                SUM(CASE WHEN pi.ID IS NULL THEN 1 ELSE 0 END) AS references_orphelines,
                SUM(CASE WHEN pi.ID IS NOT NULL THEN 1 ELSE 0 END) AS references_valides
            FROM PAPIERS_TARIF_FMT ptf
            LEFT JOIN PAPIERS_IMPRIMEURS pi ON ptf.ID_PAPIMPRIM = pi.ID
            WHERE ptf.ID_PAPIMPRIM IS NOT NULL
        """)
        row = target_cursor.fetchone()
        total_ref_fmt = row[0]
        distinct_ref_fmt = row[1]
        orphan_ref_fmt = row[2]
        valid_ref_fmt = row[3]
        
        print(f"  Total references: {total_ref_fmt:,}")
        print(f"  References distinctes: {distinct_ref_fmt:,}")
        print(f"  References valides: {valid_ref_fmt:,}")
        print(f"  References orphelines: {orphan_ref_fmt:,}")
        
        if orphan_ref_fmt == 0:
            print("  [OK] Aucune reference orpheline")
            rapport['verifications']['fk_entrantes_fmt'] = {'statut': 'OK', 'total': total_ref_fmt, 'valides': valid_ref_fmt, 'orphelines': orphan_ref_fmt}
        else:
            print(f"  [ATTENTION] {orphan_ref_fmt:,} references orphelines")
            rapport['verifications']['fk_entrantes_fmt'] = {'statut': 'ATTENTION', 'total': total_ref_fmt, 'valides': valid_ref_fmt, 'orphelines': orphan_ref_fmt}
            rapport['risques_detectes'].append(f"{orphan_ref_fmt} références orphelines dans PAPIERS_TARIF_FMT")
        
        print()
        
        # ========================================================================
        # VÉRIFICATION 4: Intégrité des FK Entrantes - PAPIERS_TARIF_GRAM
        # ========================================================================
        print("[5/9] Verification de l'integrite des FK entrantes (PAPIERS_TARIF_GRAM)...")
        
        target_cursor.execute("""
            SELECT 
                COUNT(*) AS total_references,
                COUNT(DISTINCT ID_PAPIMPRIM) AS references_distinctes,
                SUM(CASE WHEN pi.ID IS NULL THEN 1 ELSE 0 END) AS references_orphelines,
                SUM(CASE WHEN pi.ID IS NOT NULL THEN 1 ELSE 0 END) AS references_valides
            FROM PAPIERS_TARIF_GRAM ptg
            LEFT JOIN PAPIERS_IMPRIMEURS pi ON ptg.ID_PAPIMPRIM = pi.ID
            WHERE ptg.ID_PAPIMPRIM IS NOT NULL
        """)
        row = target_cursor.fetchone()
        total_ref_gram = row[0]
        distinct_ref_gram = row[1]
        orphan_ref_gram = row[2]
        valid_ref_gram = row[3]
        
        print(f"  Total references: {total_ref_gram:,}")
        print(f"  References distinctes: {distinct_ref_gram:,}")
        print(f"  References valides: {valid_ref_gram:,}")
        print(f"  References orphelines: {orphan_ref_gram:,}")
        
        if orphan_ref_gram == 0:
            print("  [OK] Aucune reference orpheline")
            rapport['verifications']['fk_entrantes_gram'] = {'statut': 'OK', 'total': total_ref_gram, 'valides': valid_ref_gram, 'orphelines': orphan_ref_gram}
        else:
            print(f"  [ATTENTION] {orphan_ref_gram:,} references orphelines")
            rapport['verifications']['fk_entrantes_gram'] = {'statut': 'ATTENTION', 'total': total_ref_gram, 'valides': valid_ref_gram, 'orphelines': orphan_ref_gram}
            rapport['risques_detectes'].append(f"{orphan_ref_gram} références orphelines dans PAPIERS_TARIF_GRAM")
        
        print()
        
        # ========================================================================
        # VÉRIFICATION 5: Intégrité des FK Sortantes
        # ========================================================================
        print("[6/9] Verification de l'integrite des FK sortantes...")
        
        # Vers IMPRIMEURS
        target_cursor.execute("""
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN i.ID_SOCIETE IS NULL THEN 1 ELSE 0 END) AS orphelines,
                SUM(CASE WHEN i.ID_SOCIETE IS NOT NULL THEN 1 ELSE 0 END) AS valides
            FROM PAPIERS_IMPRIMEURS pi
            LEFT JOIN IMPRIMEURS i ON pi.ID_IMPRIMEUR = i.ID_SOCIETE
            WHERE pi.ID_IMPRIMEUR IS NOT NULL
        """)
        row = target_cursor.fetchone()
        total_imp = row[0]
        orphan_imp = row[1]
        valid_imp = row[2]
        
        print(f"  Vers IMPRIMEURS: {valid_imp:,} valides, {orphan_imp:,} orphelines")
        
        # Vers PAPIERS
        target_cursor.execute("""
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN p.ID IS NULL THEN 1 ELSE 0 END) AS orphelines,
                SUM(CASE WHEN p.ID IS NOT NULL THEN 1 ELSE 0 END) AS valides
            FROM PAPIERS_IMPRIMEURS pi
            LEFT JOIN PAPIERS p ON pi.ID_PAPIER = p.ID
            WHERE pi.ID_PAPIER IS NOT NULL
        """)
        row = target_cursor.fetchone()
        total_pap = row[0]
        orphan_pap = row[1]
        valid_pap = row[2]
        
        print(f"  Vers PAPIERS: {valid_pap:,} valides, {orphan_pap:,} orphelines")
        
        if orphan_imp == 0 and orphan_pap == 0:
            print("  [OK] Toutes les FK sortantes sont valides")
            rapport['verifications']['fk_sortantes'] = {'statut': 'OK', 'imp': {'valides': valid_imp, 'orphelines': orphan_imp}, 'pap': {'valides': valid_pap, 'orphelines': orphan_pap}}
        else:
            print(f"  [ERREUR] {orphan_imp + orphan_pap} references orphelines")
            rapport['verifications']['fk_sortantes'] = {'statut': 'ERREUR', 'imp': {'valides': valid_imp, 'orphelines': orphan_imp}, 'pap': {'valides': valid_pap, 'orphelines': orphan_pap}}
            rapport['risques_detectes'].append(f"{orphan_imp + orphan_pap} références orphelines dans les FK sortantes")
        
        print()
        
        # ========================================================================
        # VÉRIFICATION 6: Absence de Duplication
        # ========================================================================
        print("[7/9] Verification de l'absence de duplication...")
        
        # IDs dupliqués
        target_cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT ID, COUNT(*) AS cnt
                FROM PAPIERS_IMPRIMEURS
                GROUP BY ID
                HAVING COUNT(*) > 1
            ) AS dup
        """)
        dup_ids = target_cursor.fetchone()[0]
        
        # Vérifier les doublons basés sur les colonnes de correspondance
        target_cursor.execute(f"""
            SELECT COUNT(*)
            FROM (
                SELECT {columns_str}, COUNT(*) AS cnt
                FROM PAPIERS_IMPRIMEURS
                GROUP BY {columns_str}
                HAVING COUNT(*) > 1
            ) AS dup
        """)
        dup_data = target_cursor.fetchone()[0]
        
        print(f"  IDs dupliques: {dup_ids}")
        print(f"  Donnees dupliquees: {dup_data}")
        
        if dup_ids == 0 and dup_data == 0:
            print("  [OK] Aucune duplication detectee")
            rapport['verifications']['duplication'] = {'statut': 'OK', 'ids_dupliques': dup_ids, 'donnees_dupliquees': dup_data}
        else:
            print(f"  [ERREUR] Duplications detectees")
            rapport['verifications']['duplication'] = {'statut': 'ERREUR', 'ids_dupliques': dup_ids, 'donnees_dupliquees': dup_data}
            rapport['risques_detectes'].append(f"Duplications détectées: {dup_ids} IDs, {dup_data} données")
        
        print()
        
        # ========================================================================
        # VÉRIFICATION 7: Validité des Index
        # ========================================================================
        print("[8/9] Verification de la validite des index...")
        
        target_cursor.execute("""
            SELECT 
                i.name AS index_name,
                i.is_primary_key,
                i.is_unique,
                i.is_disabled
            FROM sys.indexes i
            INNER JOIN sys.tables t ON i.object_id = t.object_id
            WHERE t.name = 'PAPIERS_IMPRIMEURS'
            AND i.name IS NOT NULL
        """)
        
        indexes = []
        for row in target_cursor.fetchall():
            indexes.append({
                'name': row[0],
                'is_primary_key': bool(row[1]),
                'is_unique': bool(row[2]),
                'is_disabled': bool(row[3])
            })
            status = "OK" if not row[3] else "DESACTIVE"
            pk_marker = " (PK)" if row[1] else ""
            print(f"  {row[0]}{pk_marker}: {status}")
        
        disabled_count = sum(1 for idx in indexes if idx['is_disabled'])
        if disabled_count == 0:
            print("  [OK] Tous les index sont actifs")
            rapport['verifications']['index'] = {'statut': 'OK', 'indexes': indexes}
        else:
            print(f"  [ATTENTION] {disabled_count} index desactives")
            rapport['verifications']['index'] = {'statut': 'ATTENTION', 'indexes': indexes}
        
        print()
        
        # ========================================================================
        # VÉRIFICATION 8: Cohérence des Tables Liées
        # ========================================================================
        print("[9/9] Verification de la coherence des tables liees...")
        
        # Vérifier que les références dans PAPIERS_TARIF_FMT pointent vers les bons IDs
        # En comparant avec les données source
        source_cursor.execute("""
            SELECT ID, ID_PAPIER, ID_IMPRIMEUR
            FROM PAPIERS_IMPRIMEURS
        """)
        source_mapping = {}
        for row in source_cursor.fetchall():
            key = (row[1], row[2])  # ID_PAPIER, ID_IMPRIMEUR
            source_mapping[key] = row[0]  # ID source
        
        target_cursor.execute("""
            SELECT ptf.ID_PAPIMPRIM, pi.ID, pi.ID_PAPIER, pi.ID_IMPRIMEUR
            FROM PAPIERS_TARIF_FMT ptf
            INNER JOIN PAPIERS_IMPRIMEURS pi ON ptf.ID_PAPIMPRIM = pi.ID
            WHERE ptf.ID_PAPIMPRIM IS NOT NULL
        """)
        
        incoherent_fmt = 0
        for row in target_cursor.fetchall():
            key = (row[2], row[3])  # ID_PAPIER, ID_IMPRIMEUR
            if key in source_mapping:
                if row[1] != source_mapping[key]:  # ID cible != ID source
                    incoherent_fmt += 1
        
        # Vérifier que les références dans PAPIERS_TARIF_GRAM pointent vers les bons IDs
        target_cursor.execute("""
            SELECT ptg.ID_PAPIMPRIM, pi.ID, pi.ID_PAPIER, pi.ID_IMPRIMEUR
            FROM PAPIERS_TARIF_GRAM ptg
            INNER JOIN PAPIERS_IMPRIMEURS pi ON ptg.ID_PAPIMPRIM = pi.ID
            WHERE ptg.ID_PAPIMPRIM IS NOT NULL
        """)
        
        incoherent_gram = 0
        for row in target_cursor.fetchall():
            key = (row[2], row[3])  # ID_PAPIER, ID_IMPRIMEUR
            if key in source_mapping:
                if row[1] != source_mapping[key]:  # ID cible != ID source
                    incoherent_gram += 1
        
        print(f"  References incoherentes dans PAPIERS_TARIF_FMT: {incoherent_fmt}")
        print(f"  References incoherentes dans PAPIERS_TARIF_GRAM: {incoherent_gram}")
        
        if incoherent_fmt == 0 and incoherent_gram == 0:
            print("  [OK] Toutes les references sont coherentes")
            rapport['verifications']['coherence'] = {'statut': 'OK', 'incoherent_fmt': incoherent_fmt, 'incoherent_gram': incoherent_gram}
        else:
            print(f"  [ATTENTION] {incoherent_fmt + incoherent_gram} references incoherentes")
            rapport['verifications']['coherence'] = {'statut': 'ATTENTION', 'incoherent_fmt': incoherent_fmt, 'incoherent_gram': incoherent_gram}
        
        print()
        
        # ========================================================================
        # RÉSULTAT GLOBAL
        # ========================================================================
        print("="*80)
        print("RESULTAT GLOBAL")
        print("="*80)
        
        # Déterminer le résultat global
        erreurs = [v for v in rapport['verifications'].values() if v.get('statut') == 'ERREUR']
        attentions = [v for v in rapport['verifications'].values() if v.get('statut') == 'ATTENTION']
        
        if len(erreurs) > 0:
            rapport['resultat_global'] = 'ERREUR'
            print("[ERREUR] Des erreurs ont ete detectees")
            print(f"  - {len(erreurs)} verification(s) en erreur")
        elif len(attentions) > 0:
            rapport['resultat_global'] = 'ATTENTION'
            print("[ATTENTION] Des points d'attention ont ete detectes")
            print(f"  - {len(attentions)} verification(s) avec attention requise")
        else:
            rapport['resultat_global'] = 'OK'
            print("[OK] Toutes les verifications sont passees avec succes")
        
        if rapport['risques_detectes']:
            print("\nRisques detectes:")
            for risque in rapport['risques_detectes']:
                print(f"  - {risque}")
        
        print()
        print("="*80)
        
        # Sauvegarder le rapport
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rapport_file = f"projet21_verification_integrite_papiers_imprimeurs_{timestamp}.json"
        with open(rapport_file, 'w', encoding='utf-8') as f:
            json.dump(rapport, f, indent=2, ensure_ascii=False)
        
        print(f"Rapport sauvegarde: {rapport_file}")
        
        return rapport
        
    except Exception as e:
        print()
        print("="*80)
        print("[ERREUR] La verification a echoue!")
        print("="*80)
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        rapport['resultat_global'] = 'ERREUR'
        rapport['erreur'] = str(e)
        return rapport
        
    finally:
        if source_conn:
            source_conn.close()
        if target_conn:
            target_conn.close()

if __name__ == '__main__':
    verification_complete()
