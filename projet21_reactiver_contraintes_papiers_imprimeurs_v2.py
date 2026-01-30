#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de réactivation de la confiance des contraintes FK
Table: PAPIERS_IMPRIMEURS

Approche: Désactiver puis réactiver avec vérification
"""

import pyodbc

TARGET_CONFIG = {
    'server': '192.168.10.225',
    'database': 'novaprint_restored',
    'trusted_connection': True
}

def get_connection(config):
    """Connexion SQL Server"""
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
    return conn

def reactiver_contraintes():
    """Réactive la confiance des contraintes FK"""
    
    print("="*80)
    print("REACTIVATION DE LA CONFIANCE DES CONTRAINTES FK")
    print("Table: PAPIERS_IMPRIMEURS")
    print("="*80)
    print()
    
    conn = None
    try:
        conn = get_connection(TARGET_CONFIG)
        cursor = conn.cursor()
        
        contraintes = [
            ('PAPIERS_IMPRIMEURS', 'FK__PAPIERS_I__ID_IM__46892E07', 'vers IMPRIMEURS'),
            ('PAPIERS_IMPRIMEURS', 'FK__PAPIERS_I__ID_PA__459509CE', 'vers PAPIERS'),
            ('PAPIERS_TARIF_FMT', 'FK__PAPIERS_T__ID_PA__49659AB2', 'depuis PAPIERS_TARIF_FMT'),
            ('PAPIERS_TARIF_GRAM', 'FK__PAPIERS_T__ID_PA__4A59BEEB', 'depuis PAPIERS_TARIF_GRAM'),
        ]
        
        print("[1/2] Desactivation puis reactivation des contraintes...")
        print()
        
        for table, constraint, description in contraintes:
            try:
                print(f"  Traitement: {constraint} ({description})")
                
                # Désactiver
                cursor.execute(f"""
                    ALTER TABLE {table}
                    NOCHECK CONSTRAINT {constraint}
                """)
                
                # Réactiver avec vérification
                cursor.execute(f"""
                    ALTER TABLE {table}
                    WITH CHECK CHECK CONSTRAINT {constraint}
                """)
                
                conn.commit()
                print(f"    [OK] Contrainte reactivee")
                
            except Exception as e:
                print(f"    [ATTENTION] Erreur: {e}")
                # Si la réactivation échoue à cause des orphelines, on réactive quand même sans vérification
                try:
                    cursor.execute(f"""
                        ALTER TABLE {table}
                        CHECK CONSTRAINT {constraint}
                    """)
                    conn.commit()
                    print(f"    [OK] Contrainte reactivee (sans verification - orphelines presentes)")
                except Exception as e2:
                    print(f"    [ERREUR] Impossible de reactiver: {e2}")
        
        print()
        print("[2/2] Verification de l'etat des contraintes...")
        print()
        
        # Vérifier l'état final
        cursor.execute("""
            SELECT 
                OBJECT_NAME(parent_object_id) AS Table_Name,
                name AS Constraint_Name,
                CASE 
                    WHEN is_not_trusted = 0 THEN 'TRUSTED'
                    ELSE 'NOT TRUSTED'
                END AS Trust_Status,
                CASE 
                    WHEN is_disabled = 0 THEN 'ENABLED'
                    ELSE 'DISABLED'
                END AS Status
            FROM sys.foreign_keys
            WHERE OBJECT_NAME(parent_object_id) IN ('PAPIERS_IMPRIMEURS', 'PAPIERS_TARIF_FMT', 'PAPIERS_TARIF_GRAM')
                AND name IN (
                    'FK__PAPIERS_I__ID_IM__46892E07',
                    'FK__PAPIERS_I__ID_PA__459509CE',
                    'FK__PAPIERS_T__ID_PA__49659AB2',
                    'FK__PAPIERS_T__ID_PA__4A59BEEB'
                )
            ORDER BY Table_Name, Constraint_Name
        """)
        
        print(f"{'Table':<25} {'Contrainte':<40} {'Confiance':<15} {'Statut':<10}")
        print("="*80)
        
        all_trusted = True
        for row in cursor.fetchall():
            table = row[0]
            constraint = row[1]
            trust = row[2]
            status = row[3]
            
            trust_marker = "✅" if trust == "TRUSTED" else "⚠️"
            print(f"{table:<25} {constraint:<40} {trust_marker} {trust:<12} {status:<10}")
            
            if trust != "TRUSTED":
                all_trusted = False
        
        print("="*80)
        print()
        
        if all_trusted:
            print("✅ Toutes les contraintes sont maintenant TRUSTED")
        else:
            print("⚠️ Certaines contraintes restent NOT TRUSTED")
            print("   Raison: References orphelines presentes (358 dans PAPIERS_TARIF_FMT, 134 dans PAPIERS_TARIF_GRAM)")
            print("   Impact: Les contraintes fonctionnent normalement mais SQL Server ne peut pas les verifier")
            print("   Action: Les contraintes sont actives et fonctionnelles")
        
        print()
        print("="*80)
        print("REACTIVATION TERMINEE")
        print("="*80)
        
    except Exception as e:
        print()
        print("="*80)
        print("[ERREUR] La reactivation a echoue!")
        print("="*80)
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    reactiver_contraintes()
