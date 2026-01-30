"""
Script pour ajouter les colonnes suivantes à la table personel :
- id : identifiant technique unique (PRIMARY KEY, AUTO_INCREMENT)
- mdp : mot de passe haché avec bcrypt
- archive : indicateur d'archivage (0 par défaut, 1 si archivé)

Ce script exécute les modifications SQL nécessaires.
"""

from db import get_db_cursor
import os

def add_columns_to_personel():
    """Ajoute les colonnes id, mdp et archive à la table personel"""
    
    try:
        with get_db_cursor() as cursor:
            print("[INFO] Debut de la modification de la table personel...")
            print("")
            
            # ========================================================================
            # ÉTAPE 1 : Vérifier et ajouter la colonne id
            # ========================================================================
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'personel' AND COLUMN_NAME = 'id'
            """)
            
            id_exists = cursor.fetchone() is not None
            
            if not id_exists:
                print("[ETAPE 1] Ajout de la colonne id...")
                
                # Vérifier si une clé primaire existe déjà
                cursor.execute("""
                    SELECT name
                    FROM sys.key_constraints
                    WHERE type = 'PK' 
                      AND parent_object_id = OBJECT_ID('dbo.personel')
                """)
                
                pk_row = cursor.fetchone()
                pk_name = pk_row.name if pk_row else None
                
                # SQL Server ne permet pas d'ajouter IDENTITY directement avec ALTER TABLE
                # On doit utiliser une table temporaire pour recréer la table
                print("    [ATTENTION] SQL Server necessite de recreer la table pour ajouter IDENTITY.")
                print("    Creation d'une table temporaire...")
                
                # Récupérer toutes les colonnes existantes
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, 
                           NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE, COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'personel'
                    ORDER BY ORDINAL_POSITION
                """)
                
                columns_info = cursor.fetchall()
                
                # Construire les définitions de colonnes pour la table temporaire
                column_defs = []
                column_names_insert = []  # Pour l'INSERT (sans id)
                column_names_select = []  # Pour le SELECT (sans id)
                
                # Ajouter id en premier avec IDENTITY
                column_defs.append("[id] INT IDENTITY(1,1) NOT NULL")
                
                for col in columns_info:
                    col_name = col.COLUMN_NAME
                    col_type = col.DATA_TYPE.upper()
                    
                    # Types numériques qui ne prennent pas de longueur
                    numeric_types_no_length = ['INT', 'SMALLINT', 'TINYINT', 'BIGINT', 'BIT', 'MONEY', 'SMALLMONEY']
                    
                    # Gérer la longueur des types
                    if col.CHARACTER_MAXIMUM_LENGTH:
                        # Types caractères
                        if col.CHARACTER_MAXIMUM_LENGTH == -1:
                            col_type += "(MAX)"
                        else:
                            col_type += f"({col.CHARACTER_MAXIMUM_LENGTH})"
                    elif col.NUMERIC_PRECISION and col_type not in numeric_types_no_length:
                        # Types numériques avec précision (DECIMAL, NUMERIC, FLOAT, REAL)
                        if col.NUMERIC_SCALE is not None:
                            col_type += f"({col.NUMERIC_PRECISION},{col.NUMERIC_SCALE})"
                        elif col_type in ['FLOAT', 'REAL']:
                            # FLOAT peut avoir une précision
                            if col.NUMERIC_PRECISION != 53:  # 53 est la valeur par défaut
                                col_type += f"({col.NUMERIC_PRECISION})"
                    
                    nullable = "NULL" if col.IS_NULLABLE == "YES" else "NOT NULL"
                    default = ""
                    if col.COLUMN_DEFAULT:
                        default = f" DEFAULT {col.COLUMN_DEFAULT}"
                    
                    column_defs.append(f"[{col_name}] {col_type} {nullable}{default}")
                    column_names_insert.append(f"[{col_name}]")
                    column_names_select.append(f"[{col_name}]")
                
                # Créer la table temporaire
                create_sql = f"""
                    CREATE TABLE dbo.personel_temp (
                        {', '.join(column_defs)},
                        CONSTRAINT PK_personel_temp_id PRIMARY KEY (id)
                    )
                """
                
                cursor.execute(create_sql)
                print("    [OK] Table temporaire creee")
                
                # Copier les données (id sera généré automatiquement par IDENTITY)
                insert_sql = f"""
                    INSERT INTO dbo.personel_temp ({', '.join(column_names_insert)})
                    SELECT {', '.join(column_names_select)}
                    FROM dbo.personel
                """
                
                cursor.execute(insert_sql)
                row_count = cursor.rowcount
                print(f"    [OK] {row_count} lignes copiees")
                
                # Identifier et sauvegarder toutes les contraintes de clé étrangère qui référencent personel
                print("    Identification des contraintes de cle etrangere...")
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
                
                # Sauvegarder les informations des FK dans une liste
                fk_info = []
                for fk in fk_constraints:
                    fk_info.append({
                        'name': fk.fk_name,
                        'parent_table': fk.parent_table,
                        'parent_column': fk.parent_column,
                        'referenced_column': fk.referenced_column
                    })
                
                # Supprimer les contraintes de clé étrangère
                for fk in fk_info:
                    try:
                        cursor.execute(f"ALTER TABLE dbo.[{fk['parent_table']}] DROP CONSTRAINT [{fk['name']}]")
                        print(f"    [OK] Contrainte FK {fk['name']} supprimee de {fk['parent_table']}")
                    except Exception as e:
                        print(f"    [ATTENTION] Erreur lors de la suppression de la FK {fk['name']}: {e}")
                
                # Supprimer l'ancienne clé primaire si elle existe
                if pk_name:
                    try:
                        cursor.execute(f"ALTER TABLE dbo.personel DROP CONSTRAINT [{pk_name}]")
                        print(f"    [OK] Ancienne cle primaire ({pk_name}) supprimee")
                    except Exception as e:
                        print(f"    [ATTENTION] Erreur lors de la suppression de la cle primaire: {e}")
                
                # Supprimer l'ancienne table
                cursor.execute("DROP TABLE dbo.personel")
                print("    [OK] Ancienne table supprimee")
                
                # Renommer la table temporaire
                cursor.execute("EXEC sp_rename 'dbo.personel_temp', 'personel'")
                print("    [OK] Table renommee")
                
                # Si Matricule était la clé primaire, créer une contrainte UNIQUE sur Matricule
                if pk_name:
                    cursor.execute("""
                        SELECT name
                        FROM sys.key_constraints 
                        WHERE type = 'UQ' 
                          AND parent_object_id = OBJECT_ID('dbo.personel')
                          AND name LIKE '%Matricule%'
                    """)
                    
                    uq_row = cursor.fetchone()
                    if not uq_row:
                        cursor.execute("""
                            ALTER TABLE dbo.personel 
                            ADD CONSTRAINT UQ_personel_Matricule UNIQUE (Matricule)
                        """)
                        print("    [OK] Contrainte UNIQUE creee sur Matricule")
                    else:
                        print("    [INFO] Une contrainte UNIQUE existe deja sur Matricule")
                
                # Recréer les contraintes de clé étrangère
                print("    Recreation des contraintes de cle etrangere...")
                for fk in fk_info:
                    try:
                        cursor.execute(f"""
                            ALTER TABLE dbo.[{fk['parent_table']}]
                            ADD CONSTRAINT [{fk['name']}] 
                            FOREIGN KEY ([{fk['parent_column']}]) 
                            REFERENCES dbo.personel([{fk['referenced_column']}])
                        """)
                        print(f"    [OK] Contrainte FK {fk['name']} recreee sur {fk['parent_table']} ({fk['parent_column']} -> personel.{fk['referenced_column']})")
                    except Exception as e:
                        print(f"    [ATTENTION] Impossible de recreer la FK {fk['name']}: {e}")
                        print(f"    [INFO] Vous devrez recreer manuellement cette contrainte")
                
                print("[OK] Colonne id ajoutee avec IDENTITY(1,1) et definie comme PRIMARY KEY")
                print("[ATTENTION] Note: Verifiez que toutes les contraintes de cle etrangere ont ete recreees correctement")
            else:
                print("[ATTENTION] La colonne id existe deja")
            
            # ========================================================================
            # ÉTAPE 2 : Ajouter la colonne mdp (mot de passe haché avec bcrypt)
            # ========================================================================
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'personel' AND COLUMN_NAME = 'mdp'
            """)
            
            mdp_exists = cursor.fetchone() is not None
            
            if not mdp_exists:
                print("[ETAPE 2] Ajout de la colonne mdp...")
                cursor.execute("""
                    ALTER TABLE dbo.personel 
                    ADD mdp VARCHAR(60) NULL
                """)
                print("[OK] Colonne mdp ajoutee (VARCHAR(60) pour stocker le hash bcrypt)")
            else:
                print("[ATTENTION] La colonne mdp existe deja")
            
            # ========================================================================
            # ÉTAPE 3 : Ajouter la colonne archive
            # ========================================================================
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'personel' AND COLUMN_NAME = 'archive'
            """)
            
            archive_exists = cursor.fetchone() is not None
            
            if not archive_exists:
                print("[ETAPE 3] Ajout de la colonne archive...")
                cursor.execute("""
                    ALTER TABLE dbo.personel 
                    ADD archive TINYINT NOT NULL DEFAULT 0
                """)
                print("[OK] Colonne archive ajoutee (TINYINT, DEFAULT 0)")
                
                # Mettre à jour les valeurs existantes à 0 si elles sont NULL
                cursor.execute("""
                    UPDATE dbo.personel 
                    SET archive = 0 
                    WHERE archive IS NULL
                """)
                print("[OK] Valeurs existantes initialisees a 0")
            else:
                print("[ATTENTION] La colonne archive existe deja")
            
            conn = cursor.connection
            conn.commit()
            
            # ========================================================================
            # RÉSUMÉ FINAL
            # ========================================================================
            print("")
            print("[OK] Modification de la table personel terminee!")
            print("")
            print("[RESUME] Colonnes ajoutees:")
            print("   - id : INT IDENTITY(1,1) PRIMARY KEY")
            print("   - mdp : VARCHAR(60) NULL (pour stocker le hash bcrypt)")
            print("   - archive : TINYINT NOT NULL DEFAULT 0 (0 = actif, 1 = archive)")
            print("")
            
            # Afficher la structure actuelle
            print("[STRUCTURE] Structure actuelle de la table personel:")
            cursor.execute("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    CASE 
                        WHEN COLUMNPROPERTY(OBJECT_ID('dbo.personel'), COLUMN_NAME, 'IsIdentity') = 1 
                        THEN 'OUI' 
                        ELSE 'NON' 
                    END AS IS_IDENTITY
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'personel'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns = cursor.fetchall()
            for col in columns:
                identity = " (IDENTITY)" if col.IS_IDENTITY == "OUI" else ""
                nullable = "NULL" if col.IS_NULLABLE == "YES" else "NOT NULL"
                length = f"({col.CHARACTER_MAXIMUM_LENGTH})" if col.CHARACTER_MAXIMUM_LENGTH else ""
                default = f" DEFAULT {col.COLUMN_DEFAULT}" if col.COLUMN_DEFAULT else ""
                print(f"   - {col.COLUMN_NAME}: {col.DATA_TYPE}{length} {nullable}{identity}{default}")
            
            return True
            
    except Exception as e:
        print(f"[ERREUR] Erreur lors de l'ajout des colonnes: {e}")
        import traceback
        traceback.print_exc()
        try:
            conn = cursor.connection
            conn.rollback()
        except:
            pass
        return False

if __name__ == "__main__":
    add_columns_to_personel()
