"""
Script pour vérifier et corriger les données de maintenance préventive
"""

import pandas as pd
from db import get_db_cursor

def verify_preventive_data():
    """Vérifie les données Excel vs Base de données"""
    
    print("=" * 70)
    print("VÉRIFICATION DES DONNÉES DE MAINTENANCE PRÉVENTIVE")
    print("=" * 70)
    
    # 1. Analyser le fichier Excel
    print("\n1. ANALYSE DU FICHIER EXCEL")
    print("-" * 70)
    excel_file = "uploads/preventive/kba maint - Copie.xlsx"
    df = pd.read_excel(excel_file)
    
    print(f"📊 Nombre total de lignes dans Excel: {len(df)}")
    print(f"📋 Colonnes: {list(df.columns)}")
    
    # Vérifier les périodicités dans Excel
    if 'Fréquence' in df.columns:
        freq_column = 'Fréquence'
    else:
        # Chercher la colonne de fréquence
        for col in df.columns:
            if 'fréquence' in str(col).lower() or 'frequence' in str(col).lower():
                freq_column = col
                break
        else:
            freq_column = None
    
    if freq_column:
        print(f"\n📈 Analyse de la colonne '{freq_column}':")
        freq_values = df[freq_column].dropna()
        freq_counts = freq_values.value_counts()
        
        print(f"   - Lignes avec valeur: {len(freq_values)}")
        print(f"   - Lignes vides: {len(df) - len(freq_values)}")
        print(f"\n   Valeurs uniques de périodicité:")
        for value, count in freq_counts.items():
            print(f"      - '{value}': {count} ligne(s)")
        
        # Vérifier s'il y a des valeurs vides ou "Non spécifiée"
        empty_freq = df[freq_column].isna().sum()
        non_specifiee = (df[freq_column].astype(str).str.strip().str.lower() == 'non spécifiée').sum()
        print(f"\n   ⚠️  Lignes avec Fréquence vide: {empty_freq}")
        print(f"   ⚠️  Lignes avec 'Non spécifiée': {non_specifiee}")
    
    # 2. Analyser la base de données
    print("\n2. ANALYSE DE LA BASE DE DONNÉES")
    print("-" * 70)
    
    with get_db_cursor() as cursor:
        # Compter le total
        cursor.execute("SELECT COUNT(*) as count FROM WEB_GMAO_PREVENTIVE WHERE Nom_GP_POSTES = 'KBA 75'")
        total_db = cursor.fetchone().count
        print(f"📊 Nombre total de lignes dans la base (KBA 75): {total_db}")
        
        # Compter par périodicité
        cursor.execute("""
            SELECT Periodicite, COUNT(*) as count
            FROM WEB_GMAO_PREVENTIVE
            WHERE Nom_GP_POSTES = 'KBA 75'
            GROUP BY Periodicite
            ORDER BY Periodicite
        """)
        
        print(f"\n📈 Répartition par périodicité:")
        periodicites_db = {}
        for row in cursor.fetchall():
            periodicite = row.Periodicite if row.Periodicite else 'NULL'
            count = row.count
            periodicites_db[periodicite] = count
            print(f"   - '{periodicite}': {count} ligne(s)")
        
        # Vérifier les doublons (même tâche, même périodicité)
        print(f"\n🔍 Vérification des doublons:")
        cursor.execute("""
            SELECT Tache, Periodicite, COUNT(*) as count
            FROM WEB_GMAO_PREVENTIVE
            WHERE Nom_GP_POSTES = 'KBA 75'
            GROUP BY Tache, Periodicite
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
        """)
        
        doublons = cursor.fetchall()
        if doublons:
            print(f"   ⚠️  {len(doublons)} groupe(s) de doublons trouvé(s):")
            for row in doublons:
                print(f"      - '{row.Tache}' ({row.Periodicite or 'NULL'}): {row.count} fois")
        else:
            print(f"   ✅ Aucun doublon trouvé")
        
        # Vérifier les lignes avec NULL ou "Non spécifiée"
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM WEB_GMAO_PREVENTIVE
            WHERE Nom_GP_POSTES = 'KBA 75'
            AND (Periodicite IS NULL OR Periodicite = 'Non spécifiée')
        """)
        null_periodicite = cursor.fetchone().count
        print(f"\n   ⚠️  Lignes avec Periodicite NULL ou 'Non spécifiée': {null_periodicite}")
    
    # 3. Comparaison
    print("\n3. COMPARAISON EXCEL vs BASE DE DONNÉES")
    print("-" * 70)
    print(f"📊 Lignes Excel: {len(df)}")
    print(f"📊 Lignes Base: {total_db}")
    
    if len(df) != total_db:
        print(f"   ⚠️  DIFFÉRENCE: {abs(len(df) - total_db)} ligne(s)")
    else:
        print(f"   ✅ Nombre de lignes correspond")
    
    if null_periodicite > 0:
        print(f"\n   ⚠️  PROBLÈME: {null_periodicite} ligne(s) avec périodicité NULL ou 'Non spécifiée'")
        print(f"      alors que le fichier Excel ne devrait pas contenir de valeurs vides")
    
    return {
        'excel_rows': len(df),
        'db_rows': total_db,
        'null_periodicite': null_periodicite,
        'doublons': len(doublons) if doublons else 0
    }

if __name__ == "__main__":
    verify_preventive_data()

















