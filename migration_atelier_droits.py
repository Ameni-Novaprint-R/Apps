"""
Migration :
- WEB_ATELIER_ACCES : ajouter colonnes mdp (bcrypt), archive (défaut 0), mot de passe par défaut 000000
- WEB_DROITS_ACCES : ajouter colonne NomAtelier et remplir avec les noms des ateliers (Atelier1..Atelier10)
"""
import sys
from db import get_db_cursor

try:
    import bcrypt
except ImportError:
    print("Erreur: bcrypt requis. pip install bcrypt")
    sys.exit(1)

MDP_DEFAUT = "000000"


def run():
    with get_db_cursor() as cursor:
        # --- WEB_ATELIER_ACCES : colonnes mdp et archive ---
        try:
            cursor.execute("""
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_ATELIER_ACCES' AND COLUMN_NAME = 'mdp'
                )
                BEGIN
                    ALTER TABLE [dbo].[WEB_ATELIER_ACCES] ADD [mdp] NVARCHAR(255) NULL;
                END
            """)
            cursor.connection.commit()
            print("Colonne WEB_ATELIER_ACCES.mdp : OK")
        except Exception as e:
            print(f"Colonne mdp: {e}")
            cursor.connection.rollback()

        try:
            cursor.execute("""
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_ATELIER_ACCES' AND COLUMN_NAME = 'archive'
                )
                BEGIN
                    ALTER TABLE [dbo].[WEB_ATELIER_ACCES] ADD [archive] BIT NOT NULL DEFAULT 0;
                END
            """)
            cursor.connection.commit()
            print("Colonne WEB_ATELIER_ACCES.archive : OK")
        except Exception as e:
            print(f"Colonne archive: {e}")
            cursor.connection.rollback()

        # Mettre mdp par défaut 000000 (hashé) pour les ateliers qui n'ont pas encore de mdp
        try:
            hash_default = bcrypt.hashpw(MDP_DEFAUT.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cursor.execute("""
                UPDATE [dbo].[WEB_ATELIER_ACCES]
                SET mdp = ?
                WHERE mdp IS NULL OR mdp = ''
            """, (hash_default,))
            cursor.connection.commit()
            print("Mot de passe par défaut 000000 appliqué aux ateliers sans mdp : OK")
        except Exception as e:
            print(f"Update mdp défaut: {e}")
            cursor.connection.rollback()

        # Mettre archive = 0 pour les lignes où archive est NULL (si la colonne venait d'être ajoutée)
        try:
            cursor.execute("""
                UPDATE [dbo].[WEB_ATELIER_ACCES] SET archive = 0 WHERE archive IS NULL
            """)
            cursor.connection.commit()
        except Exception:
            pass

        # --- WEB_DROITS_ACCES : colonne NomAtelier ---
        try:
            cursor.execute("""
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_DROITS_ACCES' AND COLUMN_NAME = 'NomAtelier'
                )
                BEGIN
                    ALTER TABLE [dbo].[WEB_DROITS_ACCES] ADD [NomAtelier] NVARCHAR(255) NULL;
                END
            """)
            cursor.connection.commit()
            print("Colonne WEB_DROITS_ACCES.NomAtelier : OK")
        except Exception as e:
            print(f"Colonne NomAtelier: {e}")
            cursor.connection.rollback()

        # Remplir NomAtelier avec les noms des ateliers (Atelier1..Atelier10) sur les premiers enregistrements
        try:
            cursor.execute("SELECT ID, Nom FROM [dbo].[WEB_ATELIER_ACCES] ORDER BY ID ASC")
            ateliers = cursor.fetchall()
            if ateliers:
                n = min(len(ateliers), 100)
                cursor.execute(f"SELECT TOP ({n}) ID FROM [dbo].[WEB_DROITS_ACCES] ORDER BY ID ASC")
                droits_ids = [row.ID for row in cursor.fetchall()]
                for i, at in enumerate(ateliers):
                    if i < len(droits_ids):
                        cursor.execute(
                            "UPDATE [dbo].[WEB_DROITS_ACCES] SET NomAtelier = ? WHERE ID = ?",
                            (at.Nom, droits_ids[i])
                        )
                cursor.connection.commit()
                print("NomAtelier rempli avec les noms des ateliers (WEB_ATELIER_ACCES) : OK")
            else:
                print("Aucun atelier dans WEB_ATELIER_ACCES, NomAtelier non rempli.")
        except Exception as e:
            print(f"Remplissage NomAtelier: {e}")
            cursor.connection.rollback()

    print("Migration terminée.")


if __name__ == "__main__":
    run()
