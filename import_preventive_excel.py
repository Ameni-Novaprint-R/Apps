"""
Script pour importer les données de maintenance préventive depuis un fichier Excel
"""

import pandas as pd
from db import get_db_cursor
import sys
import os

def import_preventive_from_excel(excel_file_path, machine_name="KBA 75"):
    """
    Importe les données de maintenance préventive depuis un fichier Excel
    
    Args:
        excel_file_path: Chemin vers le fichier Excel
        machine_name: Nom de la machine (par défaut "KBA 75")
    """
    
    if not os.path.exists(excel_file_path):
        print(f"❌ Le fichier {excel_file_path} n'existe pas.")
        return False
    
    try:
        # Lire le fichier Excel
        print(f"📖 Lecture du fichier Excel: {excel_file_path}")
        df = pd.read_excel(excel_file_path)
        
        # Afficher les colonnes disponibles pour debug
        print(f"\n📊 Colonnes trouvées dans le fichier Excel:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1}. {col}")
        
        print(f"\n📋 Premières lignes du fichier:")
        print(df.head())
        
        # Mapper les colonnes Excel aux colonnes de la base de données
        # Ajuster ces mappings selon la structure réelle du fichier Excel
        column_mapping = {
            'Tâche': 'Tache',
            'Périodicité': 'Periodicite',
            'Durée': 'Duree',
            'Temps nécessaire': 'RoleRequis',
            'Personne en charge': 'RoleRequis',  # Alternative si cette colonne existe
            'Spécifications / Observations': 'SpecificationsObservations',
            'Spécifications/Observations': 'SpecificationsObservations',
            'Observations': 'SpecificationsObservations',
        }
        
        # Nettoyer et préparer les données
        print(f"\n📝 Préparation des données...")
        
        with get_db_cursor() as cursor:
            imported_count = 0
            skipped_count = 0
            
            for index, row in df.iterrows():
                try:
                    # Extraire les données selon les colonnes disponibles
                    tache = None
                    periodicite = None
                    duree = None
                    role_requis = None
                    specifications = None
                    reference = None
                    ordre = index + 1  # Utiliser l'index comme ordre par défaut
                    
                    # Chercher les colonnes correspondantes
                    for excel_col in df.columns:
                        excel_col_str = str(excel_col).strip()
                        excel_col_clean = excel_col_str.lower()
                        
                        # Normaliser les accents pour la comparaison (mais garder aussi la version originale)
                        excel_col_normalized = excel_col_clean.replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('à', 'a').replace('â', 'a')
                        
                        # Détection de la colonne Tâche (avec ou sans accent)
                        if 'tache' in excel_col_normalized or 'tâche' in excel_col_str.lower() or 'task' in excel_col_normalized:
                            tache = str(row[excel_col]).strip() if pd.notna(row[excel_col]) else None
                        # Détection de la colonne Fréquence/Périodicité
                        elif 'frequence' in excel_col_normalized or 'fréquence' in excel_col_str.lower() or 'periodicite' in excel_col_normalized or 'périodicité' in excel_col_str.lower():
                            periodicite = str(row[excel_col]).strip() if pd.notna(row[excel_col]) else None
                        # Détection de la colonne Durée
                        elif 'duree' in excel_col_normalized or 'durée' in excel_col_str.lower():
                            duree = str(row[excel_col]).strip() if pd.notna(row[excel_col]) else None
                        # Détection de la colonne Responsable/Rôle
                        elif 'responsable' in excel_col_normalized or 'temps necessaire' in excel_col_normalized or 'role' in excel_col_normalized:
                            role_requis = str(row[excel_col]).strip() if pd.notna(row[excel_col]) else None
                        # Détection de la colonne Spécifications/Observations/Pièces de rechange
                        elif 'specifications' in excel_col_normalized or 'observations' in excel_col_normalized or 'pieces de rechange' in excel_col_normalized or 'pièces de rechange' in excel_col_str.lower():
                            specifications = str(row[excel_col]).strip() if pd.notna(row[excel_col]) else None
                        # Détection de la colonne Référence (première colonne vide ou contenant une référence)
                        elif excel_col_str.strip() == '' or 'reference' in excel_col_normalized or 'référence' in excel_col_str.lower():
                            # Si c'est la première colonne vide et qu'elle contient une valeur qui ressemble à une référence
                            ref_value = str(row[excel_col]).strip() if pd.notna(row[excel_col]) else None
                            if ref_value and (not reference or excel_col_str.strip() == ''):
                                reference = ref_value
                    
                    # Ignorer les lignes vides ou les en-têtes
                    if not tache or tache.lower() in ['tâche', 'task', 'description']:
                        skipped_count += 1
                        continue
                    
                    # Normaliser la périodicité
                    if periodicite:
                        periodicite_original = periodicite.strip()
                        periodicite_lower = periodicite_original.lower()
                        
                        # Mapping complet des périodicités
                        periodicite_map = {
                            # Quotidienne
                            'quotidienne': 'Quotidienne',
                            'quotidien': 'Quotidienne',
                            'daily': 'Quotidienne',
                            # Hebdomadaire
                            'hebdomadaire': 'Hebdomadaire',
                            'hebdomadaire': 'Hebdomadaire',
                            'weekly': 'Hebdomadaire',
                            # Mensuelle
                            'mensuelle': 'Mensuelle',
                            'mensuel': 'Mensuelle',
                            'monthly': 'Mensuelle',
                            # Trimestrielle
                            'trimestrielle': 'Trimestrielle',
                            'trimestriel': 'Trimestrielle',
                            'quarterly': 'Trimestrielle',
                            # Semestrielle
                            'semestrielle': 'Semestrielle',
                            'semestriel': 'Semestrielle',
                            'semiannual': 'Semestrielle',
                            # Annuelle
                            'annuelle': 'Annuelle',
                            'annuel': 'Annuelle',
                            'annual': 'Annuelle',
                            'yearly': 'Annuelle',
                            # Périodicités spéciales
                            'tous les 2 ans': 'Tous les 2 ans',
                            'tous les 3 ans': 'Tous les 3 ans',
                            'tous les 5 ans': 'Tous les 5 ans',
                            '2 ans': 'Tous les 2 ans',
                            '3 ans': 'Tous les 3 ans',
                            '5 ans': 'Tous les 5 ans'
                        }
                        
                        # Chercher une correspondance exacte
                        if periodicite_lower in periodicite_map:
                            periodicite = periodicite_map[periodicite_lower]
                        elif periodicite_original in ['Quotidienne', 'Hebdomadaire', 'Mensuelle', 'Trimestrielle', 'Semestrielle', 'Annuelle', 'Tous les 2 ans', 'Tous les 3 ans', 'Tous les 5 ans']:
                            # La valeur est déjà correcte
                            periodicite = periodicite_original
                        else:
                            # Chercher une correspondance partielle
                            found = False
                            for key, value in periodicite_map.items():
                                if key in periodicite_lower or periodicite_lower in key:
                                    periodicite = value
                                    found = True
                                    break
                            if not found:
                                # Si aucune correspondance, essayer de détecter "tous les X ans"
                                import re
                                match = re.search(r'tous?\s*les?\s*(\d+)\s*ans?', periodicite_lower)
                                if match:
                                    years = int(match.group(1))
                                    if years == 2:
                                        periodicite = 'Tous les 2 ans'
                                    elif years == 3:
                                        periodicite = 'Tous les 3 ans'
                                    elif years == 5:
                                        periodicite = 'Tous les 5 ans'
                                    else:
                                        periodicite = None  # Valeur non supportée
                                else:
                                    periodicite = None  # Valeur non reconnue
                    
                    # Insérer dans la base de données
                    cursor.execute("""
                        INSERT INTO dbo.WEB_GMAO_PREVENTIVE (
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
                        machine_name,
                        reference,
                        tache,
                        periodicite,
                        duree,
                        role_requis,
                        specifications,
                        ordre
                    ))
                    
                    imported_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Erreur lors de l'import de la ligne {index + 1}: {e}")
                    skipped_count += 1
                    continue
            
            cursor.connection.commit()
            
            print(f"\n✅ Import terminé!")
            print(f"   - {imported_count} lignes importées")
            print(f"   - {skipped_count} lignes ignorées")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de l'import: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_preventive_excel.py <chemin_vers_fichier_excel> [nom_machine]")
        print("Exemple: python import_preventive_excel.py planning_kba75.xlsx \"KBA 75\"")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    machine = sys.argv[2] if len(sys.argv) > 2 else "KBA 75"
    
    import_preventive_from_excel(excel_file, machine)

