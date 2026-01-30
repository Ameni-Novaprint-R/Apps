#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Python pour créer la table WEB_DROITS_ACCES
Base de données: novaprint_restored
Description: Gestion des droits d'accès des employés aux actions des sections des projets
"""

from db import get_db_cursor

def creer_table_web_droits_acces():
    """Crée la table WEB_DROITS_ACCES avec toutes ses contraintes"""
    
    try:
        with get_db_cursor() as cursor:
            # Vérifier si la table existe déjà
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'WEB_DROITS_ACCES'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if table_exists:
                print("La table WEB_DROITS_ACCES existe déjà.")
                print("Pour la recréer, supprimez-la d'abord avec: DROP TABLE WEB_DROITS_ACCES;")
                return False
            
            # Créer la table WEB_DROITS_ACCES
            cursor.execute("""
                CREATE TABLE WEB_DROITS_ACCES (
                    ID INT IDENTITY(1,1) NOT NULL,
                    Matricule INT NOT NULL,
                    ID_Action INT NOT NULL,
                    Autorise BIT NOT NULL DEFAULT 1,
                    
                    -- Contraintes de clé primaire
                    CONSTRAINT PK_WEB_DROITS_ACCES PRIMARY KEY (ID),
                    
                    -- Contraintes de clé étrangère
                    CONSTRAINT FK_WEB_DROITS_ACCES_Matricule 
                        FOREIGN KEY (Matricule) 
                        REFERENCES personel(Matricule)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    
                    CONSTRAINT FK_WEB_DROITS_ACCES_ID_Action 
                        FOREIGN KEY (ID_Action) 
                        REFERENCES WEB_ACTIONS(ID)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    
                    -- Contrainte d'unicité : un employé ne peut avoir qu'un seul droit par action
                    CONSTRAINT UQ_WEB_DROITS_ACCES_Matricule_ID_Action 
                        UNIQUE (Matricule, ID_Action)
                )
            """)
            
            # Créer des index pour améliorer les performances
            cursor.execute("""
                CREATE INDEX IDX_WEB_DROITS_ACCES_Matricule 
                ON WEB_DROITS_ACCES(Matricule)
            """)
            
            cursor.execute("""
                CREATE INDEX IDX_WEB_DROITS_ACCES_ID_Action 
                ON WEB_DROITS_ACCES(ID_Action)
            """)
            
            cursor.execute("""
                CREATE INDEX IDX_WEB_DROITS_ACCES_Autorise 
                ON WEB_DROITS_ACCES(Autorise)
            """)
            
            cursor.connection.commit()
            
            print("=" * 50)
            print("Table WEB_DROITS_ACCES créée avec succès!")
            print("=" * 50)
            print()
            print("Structure de la table:")
            print("  - ID: INT IDENTITY(1,1) PRIMARY KEY")
            print("  - Matricule: INT NOT NULL (FK -> personel.Matricule)")
            print("  - ID_Action: INT NOT NULL (FK -> WEB_ACTIONS.ID)")
            print("  - Autorise: BIT NOT NULL DEFAULT 1")
            print()
            print("Contraintes:")
            print("  - PK_WEB_DROITS_ACCES: Clé primaire sur ID")
            print("  - FK_WEB_DROITS_ACCES_Matricule: Clé étrangère vers personel(Matricule)")
            print("  - FK_WEB_DROITS_ACCES_ID_Action: Clé étrangère vers WEB_ACTIONS(ID)")
            print("  - UQ_WEB_DROITS_ACCES_Matricule_ID_Action: Unicité (Matricule, ID_Action)")
            print()
            print("Index créés:")
            print("  - IDX_WEB_DROITS_ACCES_Matricule")
            print("  - IDX_WEB_DROITS_ACCES_ID_Action")
            print("  - IDX_WEB_DROITS_ACCES_Autorise")
            print()
            
            return True
            
    except Exception as e:
        print(f"ERREUR lors de la création de la table: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Création de la table WEB_DROITS_ACCES...")
    print()
    success = creer_table_web_droits_acces()
    if success:
        print("Opération terminée avec succès!")
    else:
        print("Opération échouée!")
