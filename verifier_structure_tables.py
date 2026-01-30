"""
Script pour vérifier la structure des tables WEB_PROJETS, WEB_SECTIONS, WEB_ACTIONS et personel
"""
from db import get_db_cursor

try:
    with get_db_cursor() as cursor:
        print("=" * 80)
        print("VERIFICATION DE LA STRUCTURE DES TABLES")
        print("=" * 80)
        
        # Vérifier WEB_PROJETS
        print("\n1. Table WEB_PROJETS:")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_PROJETS'
            ORDER BY ORDINAL_POSITION
        """)
        colonnes_projets = cursor.fetchall()
        for col in colonnes_projets:
            print(f"  - {col.COLUMN_NAME}: {col.DATA_TYPE} (Nullable: {col.IS_NULLABLE})")
        
        cursor.execute("SELECT * FROM WEB_PROJETS ORDER BY ID")
        projets = cursor.fetchall()
        print(f"\n  Projets existants ({len(projets)}):")
        for p in projets:
            print(f"    {p}")
        
        # Vérifier WEB_SECTIONS
        print("\n2. Table WEB_SECTIONS:")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_SECTIONS'
            ORDER BY ORDINAL_POSITION
        """)
        colonnes_sections = cursor.fetchall()
        for col in colonnes_sections:
            print(f"  - {col.COLUMN_NAME}: {col.DATA_TYPE} (Nullable: {col.IS_NULLABLE})")
        
        cursor.execute("SELECT * FROM WEB_SECTIONS ORDER BY ID")
        sections = cursor.fetchall()
        print(f"\n  Sections existantes ({len(sections)}):")
        for s in sections:
            print(f"    {s}")
        
        # Vérifier WEB_ACTIONS
        print("\n3. Table WEB_ACTIONS:")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_ACTIONS'
            ORDER BY ORDINAL_POSITION
        """)
        colonnes_actions = cursor.fetchall()
        for col in colonnes_actions:
            print(f"  - {col.COLUMN_NAME}: {col.DATA_TYPE} (Nullable: {col.IS_NULLABLE})")
        
        cursor.execute("SELECT * FROM WEB_ACTIONS ORDER BY ID")
        actions = cursor.fetchall()
        print(f"\n  Actions existantes ({len(actions)}):")
        for a in actions:
            print(f"    {a}")
        
        # Vérifier personel (colonne MDP)
        print("\n4. Table personel (colonne MDP):")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'personel'
            AND COLUMN_NAME IN ('Matricule', 'MDP', 'Nom', 'Prenom')
            ORDER BY ORDINAL_POSITION
        """)
        colonnes_personel = cursor.fetchall()
        for col in colonnes_personel:
            print(f"  - {col.COLUMN_NAME}: {col.DATA_TYPE} (Nullable: {col.IS_NULLABLE})")
        
        # Vérifier quelques exemples de MDP
        cursor.execute("SELECT TOP 5 Matricule, MDP FROM personel WHERE MDP IS NOT NULL")
        exemples_mdp = cursor.fetchall()
        print(f"\n  Exemples de mots de passe (5 premiers):")
        for emp in exemples_mdp:
            mdp_preview = str(emp.MDP)[:20] + "..." if len(str(emp.MDP)) > 20 else str(emp.MDP)
            print(f"    Matricule {emp.Matricule}: {mdp_preview}")
        
        print("\n" + "=" * 80)
            
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()
