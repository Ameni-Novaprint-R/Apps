"""
Créer la table WEB_ATELIER_ACCES dans la base novaprint_restored (serveur 192.168.10.225)
et insérer les enregistrements Atelier1 à Atelier10.
"""
from db import get_db_cursor

def run():
    with get_db_cursor() as cursor:
        # Créer la table si elle n'existe pas
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_ATELIER_ACCES')
            BEGIN
                CREATE TABLE [dbo].[WEB_ATELIER_ACCES] (
                    [ID] INT IDENTITY(1,1) PRIMARY KEY,
                    [Nom] NVARCHAR(255) NOT NULL
                )
            END
        """)
        cursor.connection.commit()
        print("Table WEB_ATELIER_ACCES créée ou déjà existante.")

        # Insérer les enregistrements 1 à 10 s'ils n'existent pas
        cursor.execute("SET IDENTITY_INSERT [dbo].[WEB_ATELIER_ACCES] ON")
        for i in range(1, 11):
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM [dbo].[WEB_ATELIER_ACCES] WHERE [ID] = ?) "
                "INSERT INTO [dbo].[WEB_ATELIER_ACCES] ([ID], [Nom]) VALUES (?, ?)",
                (i, i, f"Atelier{i}"))
        cursor.execute("SET IDENTITY_INSERT [dbo].[WEB_ATELIER_ACCES] OFF")
        cursor.connection.commit()
        print("Enregistrements Atelier1 à Atelier10 insérés (déjà existants ignorés).")

if __name__ == "__main__":
    run()
