#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vérifier la structure de la table WEB_DROITS_ACCES
"""

def get_connection(config):
    import pyodbc
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
    return conn

TARGET_CONFIG = {
    'server': '192.168.10.225',
    'database': 'novaprint_restored',
    'trusted_connection': True
}

def main():
    print("=" * 80)
    print("VERIFICATION DE LA TABLE WEB_DROITS_ACCES")
    print("=" * 80)
    print()
    
    conn = get_connection(TARGET_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 1. Vérifier que la table existe
        print("[1] Verification de l'existence de la table...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'WEB_DROITS_ACCES' AND TABLE_TYPE = 'BASE TABLE'
        """)
        exists = cursor.fetchone()[0] > 0
        print(f"  Table existe: {exists}")
        print()
        
        if not exists:
            print("❌ La table WEB_DROITS_ACCES n'existe pas !")
            return
        
        # 2. Vérifier la structure des colonnes
        print("[2] Structure des colonnes...")
        cursor.execute("""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE, 
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'WEB_DROITS_ACCES'
            ORDER BY ORDINAL_POSITION
        """)
        columns = cursor.fetchall()
        print(f"  Nombre de colonnes: {len(columns)}")
        for col in columns:
            lon = f"({col.CHARACTER_MAXIMUM_LENGTH})" if col.CHARACTER_MAXIMUM_LENGTH else ""
            defaut = f" DEFAULT {col.COLUMN_DEFAULT}" if col.COLUMN_DEFAULT else ""
            print(f"    - {col.COLUMN_NAME}: {col.DATA_TYPE}{lon} {col.IS_NULLABLE}{defaut}")
        print()
        
        # 3. Vérifier la clé primaire
        print("[3] Verification de la clé primaire...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sys.key_constraints 
            WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
            AND type = 'PK'
        """)
        has_pk = cursor.fetchone()[0] > 0
        print(f"  Clé primaire existe: {has_pk}")
        if has_pk:
            cursor.execute("""
                SELECT name 
                FROM sys.key_constraints 
                WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
                AND type = 'PK'
            """)
            pk_name = cursor.fetchone()[0]
            print(f"  Nom de la PK: {pk_name}")
        print()
        
        # 4. Vérifier la contrainte UNIQUE (ID_Section, Action)
        print("[4] Verification de la contrainte UNIQUE (ID_Section, Action)...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sys.key_constraints 
            WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
            AND name = 'UQ_WEB_DROITS_ACCES_ID_Section_Action'
        """)
        has_unique = cursor.fetchone()[0] > 0
        print(f"  Contrainte UNIQUE existe: {has_unique}")
        print()
        
        # 5. Vérifier la clé étrangère vers WEB_SECTIONS
        print("[5] Verification de la clé étrangère vers WEB_SECTIONS...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sys.foreign_keys 
            WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
            AND name = 'FK_WEB_DROITS_ACCES_ID_Section'
        """)
        has_fk = cursor.fetchone()[0] > 0
        print(f"  Clé étrangère existe: {has_fk}")
        if has_fk:
            cursor.execute("""
                SELECT 
                    fk.name AS FK_Name,
                    tp.name AS Parent_Table,
                    cp.name AS Parent_Column,
                    tr.name AS Referenced_Table,
                    cr.name AS Referenced_Column,
                    fk.delete_referential_action_desc AS Delete_Action
                FROM sys.foreign_keys AS fk
                INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
                INNER JOIN sys.tables AS tp ON fkc.parent_object_id = tp.object_id
                INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id 
                    AND fkc.parent_column_id = cp.column_id
                INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
                INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id 
                    AND fkc.referenced_column_id = cr.column_id
                WHERE fk.parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
            """)
            fk_info = cursor.fetchone()
            if fk_info:
                print(f"    FK: {fk_info.FK_Name}")
                print(f"    {fk_info.Parent_Table}.{fk_info.Parent_Column} -> {fk_info.Referenced_Table}.{fk_info.Referenced_Column}")
                print(f"    Action DELETE: {fk_info.Delete_Action}")
        print()
        
        # 6. Compter les lignes
        print("[6] Nombre de lignes dans la table...")
        cursor.execute("SELECT COUNT(*) FROM WEB_DROITS_ACCES")
        total = cursor.fetchone()[0]
        print(f"  Total: {total} ligne(s)")
        print()
        
        # 7. Conclusion
        print("=" * 80)
        print("CONCLUSION")
        print("=" * 80)
        if exists and has_pk and has_unique and has_fk:
            print("✓ La table WEB_DROITS_ACCES est correctement créée avec toutes les contraintes !")
            print(f"  - Structure: {len(columns)} colonnes")
            print(f"  - Clé primaire: {'✓' if has_pk else '✗'}")
            print(f"  - Contrainte UNIQUE (ID_Section, Action): {'✓' if has_unique else '✗'}")
            print(f"  - Clé étrangère vers WEB_SECTIONS: {'✓' if has_fk else '✗'}")
            print(f"  - Lignes: {total}")
        else:
            print("⚠️ La table existe mais certaines contraintes manquent:")
            if not has_pk:
                print("  ✗ Clé primaire manquante")
            if not has_unique:
                print("  ✗ Contrainte UNIQUE (ID_Section, Action) manquante")
            if not has_fk:
                print("  ✗ Clé étrangère vers WEB_SECTIONS manquante")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
