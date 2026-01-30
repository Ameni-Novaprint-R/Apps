"""
Script Python pour créer la table WEB_DROITS_ACCES
Base de données: novaprint_restored
Serveur: 192.168.10.225
"""
import sys
from db import get_db_cursor

def create_table_web_droits_acces():
    """
    Crée la table WEB_DROITS_ACCES pour gérer les droits d'accès des employés
    aux actions des sections des projets de la page web.
    """
    try:
        with get_db_cursor() as cursor:
            # Vérifier si la table existe déjà
            cursor.execute("""
                SELECT COUNT(*) as table_exists
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_DROITS_ACCES'
            """)
            result = cursor.fetchone()
            
            if result and result.table_exists > 0:
                print("La table WEB_DROITS_ACCES existe déjà.")
                confirmation = input("Voulez-vous la supprimer et la recréer? (oui/non): ")
                if confirmation.lower() not in ['oui', 'o', 'yes', 'y']:
                    print("Opération annulée.")
                    return False
                
                # Supprimer les contraintes de clé étrangère d'abord
                print("Suppression des contraintes de clé étrangère...")
                try:
                    cursor.execute("ALTER TABLE [dbo].[WEB_DROITS_ACCES] DROP CONSTRAINT [FK_WEB_DROITS_ACCES_Matricule]")
                except Exception as e:
                    print(f"  Note: {e}")
                
                try:
                    cursor.execute("ALTER TABLE [dbo].[WEB_DROITS_ACCES] DROP CONSTRAINT [FK_WEB_DROITS_ACCES_ID_Action]")
                except Exception as e:
                    print(f"  Note: {e}")
                
                # Supprimer la table
                print("Suppression de la table WEB_DROITS_ACCES...")
                cursor.execute("DROP TABLE [dbo].[WEB_DROITS_ACCES]")
                cursor.connection.commit()
                print("Table supprimée avec succès.")
            
            # Vérifier que les tables référencées existent
            print("\nVérification des tables référencées...")
            
            # Vérifier personel
            cursor.execute("""
                SELECT COUNT(*) as table_exists
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'personel'
            """)
            result_personel = cursor.fetchone()
            if not result_personel or result_personel.table_exists == 0:
                print("ERREUR: La table 'personel' n'existe pas!")
                return False
            print("  [OK] Table 'personel' trouvee")
            
            # Vérifier que la colonne Matricule existe dans personel
            cursor.execute("""
                SELECT COUNT(*) as col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo' 
                AND TABLE_NAME = 'personel' 
                AND COLUMN_NAME = 'Matricule'
            """)
            result_matricule = cursor.fetchone()
            if not result_matricule or result_matricule.col_exists == 0:
                print("ERREUR: La colonne 'Matricule' n'existe pas dans la table 'personel'!")
                return False
            print("  [OK] Colonne 'Matricule' trouvee dans 'personel'")
            
            # Vérifier WEB_ACTIONS
            cursor.execute("""
                SELECT COUNT(*) as table_exists
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_ACTIONS'
            """)
            result_actions = cursor.fetchone()
            if not result_actions or result_actions.table_exists == 0:
                print("ERREUR: La table 'WEB_ACTIONS' n'existe pas!")
                return False
            print("  [OK] Table 'WEB_ACTIONS' trouvee")
            
            # Vérifier que la colonne ID existe dans WEB_ACTIONS
            cursor.execute("""
                SELECT COUNT(*) as col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo' 
                AND TABLE_NAME = 'WEB_ACTIONS' 
                AND COLUMN_NAME = 'ID'
            """)
            result_id = cursor.fetchone()
            if not result_id or result_id.col_exists == 0:
                print("ERREUR: La colonne 'ID' n'existe pas dans la table 'WEB_ACTIONS'!")
                return False
            print("  [OK] Colonne 'ID' trouvee dans 'WEB_ACTIONS'")
            
            # Créer la table WEB_DROITS_ACCES
            print("\nCréation de la table WEB_DROITS_ACCES...")
            cursor.execute("""
                CREATE TABLE [dbo].[WEB_DROITS_ACCES] (
                    [ID] INT IDENTITY(1,1) NOT NULL,
                    [Matricule] INT NOT NULL,
                    [ID_Action] INT NOT NULL,
                    [Autorise] BIT NOT NULL DEFAULT 1,
                    
                    CONSTRAINT [PK_WEB_DROITS_ACCES] PRIMARY KEY CLUSTERED ([ID] ASC),
                    
                    CONSTRAINT [FK_WEB_DROITS_ACCES_Matricule] FOREIGN KEY ([Matricule])
                        REFERENCES [dbo].[personel] ([Matricule])
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    
                    CONSTRAINT [FK_WEB_DROITS_ACCES_ID_Action] FOREIGN KEY ([ID_Action])
                        REFERENCES [dbo].[WEB_ACTIONS] ([ID])
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    
                    CONSTRAINT [UQ_WEB_DROITS_ACCES_Matricule_Action] UNIQUE ([Matricule], [ID_Action])
                )
            """)
            
            # Créer les index pour améliorer les performances
            print("Création des index...")
            try:
                cursor.execute("""
                    CREATE NONCLUSTERED INDEX [IX_WEB_DROITS_ACCES_Matricule] 
                    ON [dbo].[WEB_DROITS_ACCES] ([Matricule] ASC)
                """)
                print("  ✓ Index sur Matricule créé")
            except Exception as e:
                print(f"  Note lors de la création de l'index sur Matricule: {e}")
            
            try:
                cursor.execute("""
                    CREATE NONCLUSTERED INDEX [IX_WEB_DROITS_ACCES_ID_Action] 
                    ON [dbo].[WEB_DROITS_ACCES] ([ID_Action] ASC)
                """)
                print("  ✓ Index sur ID_Action créé")
            except Exception as e:
                print(f"  Note lors de la création de l'index sur ID_Action: {e}")
            
            try:
                cursor.execute("""
                    CREATE NONCLUSTERED INDEX [IX_WEB_DROITS_ACCES_Matricule_Autorise] 
                    ON [dbo].[WEB_DROITS_ACCES] ([Matricule] ASC, [Autorise] ASC)
                """)
                print("  ✓ Index composite sur Matricule et Autorise créé")
            except Exception as e:
                print(f"  Note lors de la création de l'index composite: {e}")
            
            cursor.connection.commit()
            
            print("\n" + "=" * 80)
            print("TABLE WEB_DROITS_ACCES CREE AVEC SUCCES!")
            print("=" * 80)
            print("\nStructure de la table:")
            print("  - ID: INT IDENTITY(1,1) PRIMARY KEY")
            print("  - Matricule: INT NOT NULL (FK vers personel.Matricule)")
            print("  - ID_Action: INT NOT NULL (FK vers WEB_ACTIONS.ID)")
            print("  - Autorise: BIT NOT NULL DEFAULT 1 (1=autorise, 0=autorisation retiree)")
            print("\nContraintes:")
            print("  - PK_WEB_DROITS_ACCES: Cle primaire sur ID")
            print("  - FK_WEB_DROITS_ACCES_Matricule: Cle etrangere vers personel(Matricule)")
            print("  - FK_WEB_DROITS_ACCES_ID_Action: Cle etrangere vers WEB_ACTIONS(ID)")
            print("  - UQ_WEB_DROITS_ACCES_Matricule_Action: Contrainte unique (Matricule, ID_Action)")
            print("\nIndex crees:")
            print("  - IX_WEB_DROITS_ACCES_Matricule")
            print("  - IX_WEB_DROITS_ACCES_ID_Action")
            print("  - IX_WEB_DROITS_ACCES_Matricule_Autorise")
            print("=" * 80)
            
            return True
            
    except Exception as e:
        print(f"\nERREUR lors de la création de la table: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("CREATION DE LA TABLE WEB_DROITS_ACCES")
    print("Base de donnees: novaprint_restored")
    print("Serveur: 192.168.10.225")
    print("=" * 80)
    print()
    
    success = create_table_web_droits_acces()
    
    if success:
        print("\n[OK] Operation terminee avec succes!")
        sys.exit(0)
    else:
        print("\n[ERREUR] Operation echouee!")
        sys.exit(1)
