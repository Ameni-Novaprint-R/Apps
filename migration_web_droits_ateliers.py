"""
Correction WEB_DROITS_ACCES pour les ateliers :
1. Supprimer NomAtelier des lignes existantes (IDs 1..10 = employés par Matricule)
2. Rendre Matricule nullable pour permettre des lignes atelier (NomAtelier seul)
3. Insérer pour chaque atelier (WEB_ATELIER_ACCES) des lignes avec ID_Action 1, 2, 3, 4, 5
"""
from db import get_db_cursor

ACTIONS_ATELIER = [1, 2, 3, 4, 5]  # ID_Action à associer à chaque atelier


def run():
    with get_db_cursor() as cursor:
        # 1. Supprimer NomAtelier de toutes les lignes (restaurer les lignes employés)
        try:
            cursor.execute("""
                UPDATE [dbo].[WEB_DROITS_ACCES] SET NomAtelier = NULL WHERE NomAtelier IS NOT NULL
            """)
            cursor.connection.commit()
            print("NomAtelier supprimé des lignes existantes (employés) : OK")
        except Exception as e:
            print(f"Erreur suppression NomAtelier: {e}")
            cursor.connection.rollback()
            return

        # 2. Rendre Matricule nullable (pour lignes atelier sans Matricule)
        try:
            cursor.execute("""
                ALTER TABLE [dbo].[WEB_DROITS_ACCES] ALTER COLUMN [Matricule] INT NULL
            """)
            cursor.connection.commit()
            print("Colonne Matricule rendue nullable : OK")
        except Exception as e:
            print(f"Note Matricule nullable (peut déjà être NULL): {e}")
            cursor.connection.rollback()

        # 2b. Supprimer la contrainte UNIQUE (Matricule, ID_Action) pour permettre plusieurs (NULL, ID_Action)
        try:
            cursor.execute("""
                ALTER TABLE [dbo].[WEB_DROITS_ACCES] DROP CONSTRAINT [UQ_WEB_DROITS_ACCES_Matricule_Action]
            """)
            cursor.connection.commit()
            print("Contrainte UQ_WEB_DROITS_ACCES_Matricule_Action supprimée : OK")
        except Exception as e:
            print(f"Note suppression contrainte (nom peut varier): {e}")
            cursor.connection.rollback()

        # 2c. Recréer un index unique filtré : (Matricule, ID_Action) uniquement quand Matricule IS NOT NULL
        try:
            cursor.execute("""
                CREATE UNIQUE NONCLUSTERED INDEX [UQ_WEB_DROITS_ACCES_Matricule_Action]
                ON [dbo].[WEB_DROITS_ACCES] ([Matricule], [ID_Action])
                WHERE [Matricule] IS NOT NULL
            """)
            cursor.connection.commit()
            print("Index unique filtré (Matricule, ID_Action) créé : OK")
        except Exception as e:
            print(f"Note index unique Matricule: {e}")
            cursor.connection.rollback()

        # 2d. Index unique filtré (NomAtelier, ID_Action) pour éviter doublons atelier+action
        try:
            cursor.execute("""
                CREATE UNIQUE NONCLUSTERED INDEX [UQ_WEB_DROITS_ACCES_NomAtelier_Action]
                ON [dbo].[WEB_DROITS_ACCES] ([NomAtelier], [ID_Action])
                WHERE [NomAtelier] IS NOT NULL
            """)
            cursor.connection.commit()
            print("Index unique filtré (NomAtelier, ID_Action) créé : OK")
        except Exception as e:
            print(f"Note index unique NomAtelier: {e}")
            cursor.connection.rollback()

        # 3. Vérifier quelles actions existent dans WEB_ACTIONS (1, 2, 3, 4, 5 ou autres)
        try:
            cursor.execute("""
                SELECT ID FROM [dbo].[WEB_ACTIONS] WHERE ID IN (1, 2, 3, 4, 5) ORDER BY ID
            """)
            actions_existantes = [row.ID for row in cursor.fetchall()]
            if not actions_existantes:
                cursor.execute("SELECT TOP 5 ID FROM [dbo].[WEB_ACTIONS] ORDER BY ID")
                actions_existantes = [row.ID for row in cursor.fetchall()]
            if not actions_existantes:
                print("Aucune action trouvée dans WEB_ACTIONS. Vérifiez la table.")
                return
            print(f"Actions utilisées pour les ateliers: {actions_existantes}")
        except Exception as e:
            print(f"Erreur lecture WEB_ACTIONS: {e}")
            return

        # 4. Pour chaque atelier (WEB_ATELIER_ACCES), insérer une ligne par action
        try:
            cursor.execute("SELECT ID, Nom FROM [dbo].[WEB_ATELIER_ACCES] ORDER BY ID")
            ateliers = cursor.fetchall()
            if not ateliers:
                print("Aucun atelier dans WEB_ATELIER_ACCES.")
                return

            inserted = 0
            for at in ateliers:
                nom_atelier = at.Nom if at.Nom is not None else ""
                if not nom_atelier.strip():
                    continue
                for id_action in actions_existantes:
                    # Éviter doublon (NomAtelier, ID_Action)
                    cursor.execute("""
                        SELECT 1 FROM [dbo].[WEB_DROITS_ACCES]
                        WHERE NomAtelier = ? AND ID_Action = ?
                    """, (nom_atelier.strip(), id_action))
                    if cursor.fetchone():
                        continue
                    cursor.execute("""
                        INSERT INTO [dbo].[WEB_DROITS_ACCES] (Matricule, NomAtelier, ID_Action, Autorise)
                        VALUES (NULL, ?, ?, 1)
                    """, (nom_atelier.strip(), id_action))
                    inserted += 1
            cursor.connection.commit()
            print(f"Lignes atelier insérées (NomAtelier + ID_Action 1..5 par atelier): {inserted}")
        except Exception as e:
            print(f"Erreur insertion lignes atelier: {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()
            # Si la colonne Matricule est encore NOT NULL, proposer de la rendre nullable
            if "NULL" in str(e) or "Matricule" in str(e):
                print("Assurez-vous que la colonne Matricule accepte NULL (ALTER COLUMN Matricule INT NULL).")
            return

    print("Migration WEB_DROITS_ACCES (ateliers) terminée.")


if __name__ == "__main__":
    run()
