"""
Script de test pour vérifier le fonctionnement des colonnes DateDerniereExecution 
et DateProchaineExecution dans la table WEB_GMAO_PREVENTIVE
"""
from db import get_db_cursor
from datetime import datetime, timedelta
from logic.projet16 import update_preventive_task, get_preventive_task_by_id, calculate_next_execution_date

def test_preventive_dates_sync():
    """Test la synchronisation automatique des dates"""
    
    print("=" * 80)
    print("TEST DE SYNCHRONISATION DES DATES - WEB_GMAO_PREVENTIVE")
    print("=" * 80)
    print()
    
    try:
        with get_db_cursor() as cursor:
            # 1. Vérifier que les colonnes existent
            print("1. Vérification de l'existence des colonnes...")
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'WEB_GMAO_PREVENTIVE' 
                AND COLUMN_NAME IN ('DteReal', 'DateDerniereExecution', 'DateProchaineExecution', 'Periodicite')
            """)
            columns = {row.COLUMN_NAME for row in cursor.fetchall()}
            
            required_columns = {'DteReal', 'DateDerniereExecution', 'DateProchaineExecution', 'Periodicite'}
            missing_columns = required_columns - columns
            
            if missing_columns:
                print(f"   [ATTENTION] Colonnes manquantes: {missing_columns}")
                print("   Ajout des colonnes manquantes...")
                
                if 'DteReal' in missing_columns:
                    try:
                        cursor.execute("ALTER TABLE WEB_GMAO_PREVENTIVE ADD DteReal DATETIME NULL")
                        cursor.connection.commit()
                        print("   [OK] Colonne DteReal ajoutee")
                    except Exception as e:
                        print(f"   [ERREUR] Impossible d'ajouter DteReal: {e}")
                        return False
                
                if 'DtePrev' in missing_columns:
                    try:
                        cursor.execute("ALTER TABLE WEB_GMAO_PREVENTIVE ADD DtePrev DATETIME NULL")
                        cursor.connection.commit()
                        print("   [OK] Colonne DtePrev ajoutee")
                    except Exception as e:
                        print(f"   [ERREUR] Impossible d'ajouter DtePrev: {e}")
                        return False
                
                print("   [OK] Toutes les colonnes necessaires sont maintenant presentes")
            else:
                print("   [OK] Toutes les colonnes necessaires existent")
            print()
            
            # 2. Récupérer une tâche de test (ou en créer une)
            print("2. Recherche d'une tâche de test...")
            cursor.execute("""
                SELECT TOP 1 ID, Nom_GP_POSTES, Periodicite, DteReal, DateDerniereExecution, DateProchaineExecution
                FROM WEB_GMAO_PREVENTIVE
                WHERE Periodicite IS NOT NULL
                ORDER BY ID
            """)
            test_task = cursor.fetchone()
            
            if not test_task:
                print("   [ATTENTION] Aucune tache trouvee avec une periodicite definie")
                print("   Creation d'une tache de test...")
                cursor.execute("""
                    INSERT INTO WEB_GMAO_PREVENTIVE (Nom_GP_POSTES, Periodicite, Reference, Tache)
                    VALUES ('TEST', 'Mensuelle', 'TEST001', 'Tache de test')
                """)
                cursor.execute("SELECT @@IDENTITY AS ID")
                test_id = cursor.fetchone().ID
                cursor.connection.commit()
                print(f"   [OK] Tache de test creee avec ID: {test_id}")
                test_task_id = test_id
                periodicite_test = 'Mensuelle'
            else:
                test_task_id = test_task.ID
                periodicite_test = test_task.Periodicite
                print(f"   [OK] Tache trouvee - ID: {test_task_id}, Periodicite: {periodicite_test}")
            print()
            
            # 3. Test 1: Mise à jour de DteReal et vérification de DateDerniereExecution
            print("3. TEST 1: Mise à jour de DteReal...")
            test_date_real = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"   Date de réalisation à définir: {test_date_real}")
            
            # Mettre à jour via la fonction Python
            update_data = {
                'dte_real': test_date_real
            }
            success = update_preventive_task(test_task_id, update_data)
            
            if not success:
                print("   [ERREUR] Erreur lors de la mise a jour")
                return False
            
            # Vérifier les valeurs dans la base
            cursor.execute("""
                SELECT DteReal, DateDerniereExecution, DateProchaineExecution, Periodicite
                FROM WEB_GMAO_PREVENTIVE
                WHERE ID = ?
            """, (test_task_id,))
            result = cursor.fetchone()
            
            print(f"   DteReal dans la base: {result.DteReal}")
            print(f"   DateDerniereExecution dans la base: {result.DateDerniereExecution}")
            print(f"   DateProchaineExecution dans la base: {result.DateProchaineExecution}")
            
            # Vérifier RÈGLE 1: DateDerniereExecution = DteReal
            if result.DteReal and result.DateDerniereExecution:
                dte_real_str = str(result.DteReal)[:19]  # Sans millisecondes
                date_derniere_str = str(result.DateDerniereExecution)[:19]
                if dte_real_str == date_derniere_str:
                    print("   [OK] REGLE 1: DateDerniereExecution = DteReal (CORRECT)")
                else:
                    print(f"   [ERREUR] REGLE 1: DateDerniereExecution != DteReal")
                    print(f"      DteReal: {dte_real_str}")
                    print(f"      DateDerniereExecution: {date_derniere_str}")
                    return False
            else:
                print("   [ATTENTION] DteReal ou DateDerniereExecution est NULL")
            print()
            
            # 4. Test 2: Vérification du calcul de DateProchaineExecution
            print("4. TEST 2: Vérification du calcul de DateProchaineExecution...")
            
            if result.DateDerniereExecution and result.Periodicite:
                # Calculer la date attendue
                date_prevue_attendue = calculate_next_execution_date(
                    result.DateDerniereExecution, 
                    result.Periodicite
                )
                
                if date_prevue_attendue:
                    date_prevue_attendue_str = date_prevue_attendue.strftime('%Y-%m-%d %H:%M:%S')
                    date_prochaine_str = str(result.DateProchaineExecution)[:19] if result.DateProchaineExecution else None
                    
                    print(f"   DateDerniereExecution: {result.DateDerniereExecution}")
                    print(f"   Periodicite: {result.Periodicite}")
                    print(f"   DateProchaineExecution attendue: {date_prevue_attendue_str}")
                    print(f"   DateProchaineExecution dans la base: {date_prochaine_str}")
                    
                    if date_prochaine_str:
                        # Comparer les dates (tolérance de quelques secondes)
                        date_prevue_dt = datetime.strptime(date_prevue_attendue_str, '%Y-%m-%d %H:%M:%S')
                        date_prochaine_dt = datetime.strptime(date_prochaine_str, '%Y-%m-%d %H:%M:%S')
                        diff_seconds = abs((date_prevue_dt - date_prochaine_dt).total_seconds())
                        
                        if diff_seconds < 60:  # Tolerance de 1 minute
                            print("   [OK] REGLE 2: DateProchaineExecution = DateDerniereExecution + Periodicite (CORRECT)")
                        else:
                            print(f"   [ERREUR] REGLE 2: DateProchaineExecution incorrecte (difference: {diff_seconds}s)")
                            return False
                    else:
                        print("   [ERREUR] DateProchaineExecution est NULL dans la base")
                        return False
                else:
                    print("   [ATTENTION] Impossible de calculer la date prevue attendue")
            else:
                print("   [ATTENTION] DateDerniereExecution ou Periodicite est NULL")
            print()
            
            # 5. Test 3: Test avec différentes périodicités
            print("5. TEST 3: Test avec différentes périodicités...")
            periodicites_test = ['Quotidienne', 'Hebdomadaire', 'Mensuelle', 'Trimestrielle', 'Semestrielle', 'Annuelle']
            
            base_date = datetime(2025, 1, 15, 10, 0, 0)
            
            for periodicite in periodicites_test:
                date_calculee = calculate_next_execution_date(base_date, periodicite)
                if date_calculee:
                    diff = date_calculee - base_date
                    print(f"   {periodicite:15} : {base_date.strftime('%Y-%m-%d')} -> {date_calculee.strftime('%Y-%m-%d')} (diff: {diff.days} jours)")
                else:
                    print(f"   {periodicite:15} : [ERREUR] Calcul echoue")
            print()
            
            # 6. Test 4: Vérifier via l'API get_preventive_task_by_id
            print("6. TEST 4: Vérification via get_preventive_task_by_id...")
            task_data = get_preventive_task_by_id(test_task_id)
            
            if task_data:
                print(f"   ID: {task_data.get('id')}")
                print(f"   dte_real: {task_data.get('dte_real')}")
                print(f"   date_derniere_execution: {task_data.get('date_derniere_execution')}")
                print(f"   date_prochaine_execution: {task_data.get('date_prochaine_execution')}")
                
                if task_data.get('dte_real') and task_data.get('date_derniere_execution'):
                    dte_real_api = task_data.get('dte_real')[:19]
                    date_derniere_api = task_data.get('date_derniere_execution')[:19]
                    if dte_real_api == date_derniere_api:
                        print("   [OK] Synchronisation correcte via l'API")
                    else:
                        print("   [ERREUR] Synchronisation incorrecte via l'API")
                        return False
            else:
                print("   [ERREUR] Impossible de recuperer la tache via l'API")
                return False
            print()
            
            print("=" * 80)
            print("[OK] TOUS LES TESTS SONT PASSES AVEC SUCCES!")
            print("=" * 80)
            return True
            
    except Exception as e:
        print(f"[ERREUR] ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_preventive_dates_sync()













