"""
Script pour vérifier et corriger les contraintes de clé étrangère vers personel
"""

from db import get_db_cursor

def verifier_corriger_fk_personel():
    """Vérifie et corrige les contraintes de clé étrangère vers personel"""
    
    try:
        with get_db_cursor() as cursor:
            print("[INFO] Verification et correction des contraintes de cle etrangere vers personel...")
            print("")
            
            # ========================================================================
            # ÉTAPE 1 : Vérifier les contraintes existantes
            # ========================================================================
            print("[ETAPE 1] Verification des contraintes existantes...")
            cursor.execute("""
                SELECT 
                    fk.name AS fk_name,
                    OBJECT_NAME(fk.parent_object_id) AS parent_table,
                    COL_NAME(fc.parent_object_id, fc.parent_column_id) AS parent_column,
                    COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS referenced_column
                FROM sys.foreign_keys fk
                INNER JOIN sys.foreign_key_columns fc ON fk.object_id = fc.constraint_object_id
                WHERE fk.referenced_object_id = OBJECT_ID('dbo.personel')
            """)
            
            fk_constraints = cursor.fetchall()
            print(f"    {len(fk_constraints)} contrainte(s) de cle etrangere trouvee(s)")
            
            if len(fk_constraints) == 0:
                print("    [ATTENTION] Aucune contrainte FK trouvee. Recreation necessaire.")
                return False
            
            # ========================================================================
            # ÉTAPE 2 : Vérifier l'intégrité des données pour chaque FK
            # ========================================================================
            print("")
            print("[ETAPE 2] Verification de l'integrite des donnees...")
            
            for fk in fk_constraints:
                fk_name = fk.fk_name
                parent_table = fk.parent_table
                parent_column = fk.parent_column
                referenced_column = fk.referenced_column
                
                print(f"    Verification de {fk_name} sur {parent_table}...")
                
                # Vérifier les valeurs orphelines (qui n'existent pas dans personel)
                cursor.execute(f"""
                    SELECT COUNT(*) as count_orphelins
                    FROM dbo.[{parent_table}] t
                    LEFT JOIN dbo.personel p ON t.[{parent_column}] = p.[{referenced_column}]
                    WHERE t.[{parent_column}] IS NOT NULL
                      AND p.[{referenced_column}] IS NULL
                """)
                
                orphelins = cursor.fetchone()
                count_orphelins = orphelins.count_orphelins if orphelins else 0
                
                if count_orphelins > 0:
                    print(f"        [ATTENTION] {count_orphelins} valeur(s) orpheline(s) trouvee(s)")
                    
                    # Afficher les valeurs orphelines
                    cursor.execute(f"""
                        SELECT DISTINCT t.[{parent_column}] as valeur_orpheline
                        FROM dbo.[{parent_table}] t
                        LEFT JOIN dbo.personel p ON t.[{parent_column}] = p.[{referenced_column}]
                        WHERE t.[{parent_column}] IS NOT NULL
                          AND p.[{referenced_column}] IS NULL
                    """)
                    
                    orphelins_list = cursor.fetchall()
                    print(f"        Valeurs orphelines: {[str(o.valeur_orpheline) for o in orphelins_list]}")
                    
                    # Option: Mettre à NULL les valeurs orphelines
                    print(f"        [ACTION] Mise a NULL des valeurs orphelines...")
                    cursor.execute(f"""
                        UPDATE dbo.[{parent_table}]
                        SET [{parent_column}] = NULL
                        WHERE [{parent_column}] IS NOT NULL
                          AND [{parent_column}] NOT IN (
                              SELECT [{referenced_column}] 
                              FROM dbo.personel 
                              WHERE [{referenced_column}] IS NOT NULL
                          )
                    """)
                    rows_updated = cursor.rowcount
                    print(f"        [OK] {rows_updated} ligne(s) mise(s) a NULL")
                else:
                    print(f"        [OK] Aucune valeur orpheline")
            
            # ========================================================================
            # ÉTAPE 3 : Vérifier que les contraintes sont actives
            # ========================================================================
            print("")
            print("[ETAPE 3] Verification de l'etat des contraintes...")
            
            for fk in fk_constraints:
                fk_name = fk.fk_name
                parent_table = fk.parent_table
                
                cursor.execute("""
                    SELECT is_disabled
                    FROM sys.foreign_keys
                    WHERE name = ?
                      AND parent_object_id = OBJECT_ID(?)
                """, (fk_name, f"dbo.[{parent_table}]"))
                
                fk_state = cursor.fetchone()
                if fk_state:
                    is_disabled = fk_state.is_disabled
                    if is_disabled:
                        print(f"    [ATTENTION] La contrainte {fk_name} est desactivee")
                        print(f"        [ACTION] Reactivation de la contrainte...")
                        try:
                            cursor.execute(f"ALTER TABLE dbo.[{parent_table}] CHECK CONSTRAINT [{fk_name}]")
                            print(f"        [OK] Contrainte {fk_name} reactivee")
                        except Exception as e:
                            print(f"        [ERREUR] Impossible de reactiver: {e}")
                    else:
                        print(f"    [OK] Contrainte {fk_name} est activee")
            
            # ========================================================================
            # ÉTAPE 4 : Vérifier que les contraintes fonctionnent correctement
            # ========================================================================
            print("")
            print("[ETAPE 4] Test de fonctionnement des contraintes...")
            
            for fk in fk_constraints:
                fk_name = fk.fk_name
                parent_table = fk.parent_table
                parent_column = fk.parent_column
                referenced_column = fk.referenced_column
                
                # Tester en essayant d'insérer une valeur invalide (doit échouer)
                # On va juste vérifier que la contrainte existe et est valide
                cursor.execute("""
                    SELECT 
                        fk.name,
                        OBJECT_NAME(fk.parent_object_id) AS parent_table,
                        OBJECT_NAME(fk.referenced_object_id) AS referenced_table,
                        fk.is_disabled,
                        fk.is_not_trusted
                    FROM sys.foreign_keys fk
                    WHERE fk.name = ?
                """, (fk_name,))
                
                fk_info = cursor.fetchone()
                if fk_info:
                    if fk_info.is_not_trusted:
                        print(f"    [ATTENTION] La contrainte {fk_name} n'est pas consideree comme fiable")
                        print(f"        [ACTION] Revalidation de la contrainte...")
                        try:
                            cursor.execute(f"ALTER TABLE dbo.[{parent_table}] WITH CHECK CHECK CONSTRAINT [{fk_name}]")
                            print(f"        [OK] Contrainte {fk_name} revalidee")
                        except Exception as e:
                            print(f"        [ERREUR] Impossible de revalider: {e}")
                    else:
                        print(f"    [OK] Contrainte {fk_name} est validee et fiable")
            
            # Commit des modifications
            conn = cursor.connection
            conn.commit()
            
            # ========================================================================
            # RÉSUMÉ FINAL
            # ========================================================================
            print("")
            print("[OK] Verification et correction terminees!")
            print("")
            print("[RESUME] Contraintes de cle etrangere vers personel:")
            for fk in fk_constraints:
                print(f"   - {fk.fk_name}")
                print(f"     Table: {fk.parent_table}")
                print(f"     Colonne: {fk.parent_column} -> personel.{fk.referenced_column}")
                print("")
            
            return True
            
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la verification: {e}")
        import traceback
        traceback.print_exc()
        try:
            conn = cursor.connection
            conn.rollback()
        except:
            pass
        return False

if __name__ == "__main__":
    verifier_corriger_fk_personel()
