"""
Script pour nettoyer et réimporter proprement les données de maintenance préventive
"""

from db import get_db_cursor
import pandas as pd

def clean_and_reimport():
    """Supprime toutes les données et réimporte depuis Excel"""
    
    print("=" * 70)
    print("NETTOYAGE ET RÉIMPORT DES DONNÉES")
    print("=" * 70)
    
    # 1. Supprimer toutes les données existantes
    print("\n1. SUPPRESSION DES DONNÉES EXISTANTES")
    print("-" * 70)
    
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM WEB_GMAO_PREVENTIVE WHERE Nom_GP_POSTES = 'KBA 75'")
        count_before = cursor.fetchone().count
        print(f"📊 Lignes avant suppression: {count_before}")
        
        cursor.execute("DELETE FROM WEB_GMAO_PREVENTIVE WHERE Nom_GP_POSTES = 'KBA 75'")
        cursor.connection.commit()
        
        cursor.execute("SELECT COUNT(*) as count FROM WEB_GMAO_PREVENTIVE WHERE Nom_GP_POSTES = 'KBA 75'")
        count_after = cursor.fetchone().count
        print(f"✅ Lignes après suppression: {count_after}")
    
    # 2. Lire le fichier Excel
    print("\n2. LECTURE DU FICHIER EXCEL")
    print("-" * 70)
    excel_file = "uploads/preventive/kba maint - Copie.xlsx"
    df = pd.read_excel(excel_file)
    
    print(f"📊 Lignes dans Excel: {len(df)}")
    
    # Identifier les colonnes
    reference_col = None
    tache_col = None
    frequence_col = None
    duree_col = None
    responsable_col = None
    pieces_col = None
    
    for col in df.columns:
        col_str = str(col).strip()
        col_lower = col_str.lower()
        
        if col_str.strip() == '' or 'reference' in col_lower or 'référence' in col_lower:
            reference_col = col
        elif 'tache' in col_lower or 'tâche' in col_lower or 'task' in col_lower:
            tache_col = col
        elif 'frequence' in col_lower or 'fréquence' in col_lower or 'periodicite' in col_lower:
            frequence_col = col
        elif 'duree' in col_lower or 'durée' in col_lower:
            duree_col = col
        elif 'responsable' in col_lower or 'role' in col_lower:
            responsable_col = col
        elif 'pieces' in col_lower or 'pièces' in col_lower:
            pieces_col = col
    
    print(f"✅ Colonnes identifiées:")
    print(f"   - Référence: {reference_col}")
    print(f"   - Tâche: {tache_col}")
    print(f"   - Fréquence: {frequence_col}")
    print(f"   - Durée: {duree_col}")
    print(f"   - Responsable: {responsable_col}")
    print(f"   - Pièces: {pieces_col}")
    
    # 3. Importer les données
    print("\n3. IMPORT DES DONNÉES")
    print("-" * 70)
    
    with get_db_cursor() as cursor:
        imported = 0
        errors = 0
        
        for index, row in df.iterrows():
            try:
                # Extraire les valeurs
                reference = str(row[reference_col]).strip() if reference_col and pd.notna(row[reference_col]) else None
                tache = str(row[tache_col]).strip() if tache_col and pd.notna(row[tache_col]) else None
                frequence = str(row[frequence_col]).strip() if frequence_col and pd.notna(row[frequence_col]) else None
                duree = str(row[duree_col]).strip() if duree_col and pd.notna(row[duree_col]) else None
                responsable = str(row[responsable_col]).strip() if responsable_col and pd.notna(row[responsable_col]) else None
                pieces = str(row[pieces_col]).strip() if pieces_col and pd.notna(row[pieces_col]) else None
                
                # Ignorer les lignes vides ou les en-têtes
                if not tache or tache.lower() in ['tâche', 'task', 'description']:
                    continue
                
                # Normaliser la périodicité
                periodicite = None
                if frequence:
                    frequence_lower = frequence.lower().strip()
                    periodicite_map = {
                        'quotidienne': 'Quotidienne',
                        'hebdomadaire': 'Hebdomadaire',
                        'mensuelle': 'Mensuelle',
                        'trimestrielle': 'Trimestrielle',
                        'semestrielle': 'Semestrielle',
                        'annuelle': 'Annuelle',
                        'tous les 2 ans': 'Tous les 2 ans',
                        'tous les 3 ans': 'Tous les 3 ans',
                        'tous les 5 ans': 'Tous les 5 ans'
                    }
                    
                    if frequence_lower in periodicite_map:
                        periodicite = periodicite_map[frequence_lower]
                    elif frequence in ['Quotidienne', 'Hebdomadaire', 'Mensuelle', 'Trimestrielle', 'Semestrielle', 'Annuelle', 'Tous les 2 ans', 'Tous les 3 ans', 'Tous les 5 ans']:
                        periodicite = frequence
                    else:
                        # Détecter "tous les X ans"
                        import re
                        match = re.search(r'tous?\s*les?\s*(\d+)\s*ans?', frequence_lower)
                        if match:
                            years = int(match.group(1))
                            if years == 2:
                                periodicite = 'Tous les 2 ans'
                            elif years == 3:
                                periodicite = 'Tous les 3 ans'
                            elif years == 5:
                                periodicite = 'Tous les 5 ans'
                
                # Vérifier que la périodicité est valide
                if not periodicite:
                    print(f"   ⚠️  Ligne {index + 1}: Périodicité non reconnue '{frequence}' - IGNORÉE")
                    errors += 1
                    continue
                
                # Insérer dans la base
                cursor.execute("""
                    INSERT INTO WEB_GMAO_PREVENTIVE (
                        Nom_GP_POSTES,
                        Reference,
                        Tache,
                        Periodicite,
                        Duree,
                        RoleRequis,
                        SpecificationsObservations,
                        OrdreAffichage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'KBA 75',
                    reference,
                    tache,
                    periodicite,
                    duree,
                    responsable,
                    pieces if pieces and pieces != '-' else None,
                    index + 1
                ))
                
                imported += 1
                
            except Exception as e:
                print(f"   ❌ Erreur ligne {index + 1}: {e}")
                errors += 1
        
        cursor.connection.commit()
        
        print(f"\n✅ Import terminé:")
        print(f"   - {imported} lignes importées")
        print(f"   - {errors} erreurs")
    
    # 4. Vérification finale
    print("\n4. VÉRIFICATION FINALE")
    print("-" * 70)
    
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM WEB_GMAO_PREVENTIVE WHERE Nom_GP_POSTES = 'KBA 75'")
        total = cursor.fetchone().count
        print(f"📊 Total dans la base: {total}")
        
        cursor.execute("""
            SELECT Periodicite, COUNT(*) as count
            FROM WEB_GMAO_PREVENTIVE
            WHERE Nom_GP_POSTES = 'KBA 75'
            GROUP BY Periodicite
            ORDER BY Periodicite
        """)
        
        print(f"\n📈 Répartition par périodicité:")
        for row in cursor.fetchall():
            periodicite = row.Periodicite if row.Periodicite else 'NULL'
            print(f"   - '{periodicite}': {row.count} ligne(s)")
        
        # Vérifier les doublons
        cursor.execute("""
            SELECT Tache, Periodicite, COUNT(*) as count
            FROM WEB_GMAO_PREVENTIVE
            WHERE Nom_GP_POSTES = 'KBA 75'
            GROUP BY Tache, Periodicite
            HAVING COUNT(*) > 1
        """)
        
        doublons = cursor.fetchall()
        if doublons:
            print(f"\n   ⚠️  {len(doublons)} groupe(s) de doublons trouvé(s)")
        else:
            print(f"\n   ✅ Aucun doublon")
        
        # Vérifier les NULL
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM WEB_GMAO_PREVENTIVE
            WHERE Nom_GP_POSTES = 'KBA 75'
            AND Periodicite IS NULL
        """)
        null_count = cursor.fetchone().count
        if null_count > 0:
            print(f"\n   ⚠️  {null_count} ligne(s) avec Periodicite NULL")
        else:
            print(f"\n   ✅ Aucune ligne avec Periodicite NULL")

if __name__ == "__main__":
    clean_and_reimport()

















