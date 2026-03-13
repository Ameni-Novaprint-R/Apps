# -*- coding: utf-8 -*-
"""
Crée la table WEB_PROJET23_SYNTHESE pour stocker la dernière synthèse trésorerie.
"""
from db import get_db_cursor

def run():
    with get_db_cursor() as cursor:
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES 
                           WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_PROJET23_SYNTHESE')
            BEGIN
                CREATE TABLE [dbo].[WEB_PROJET23_SYNTHESE] (
                    [ID] INT IDENTITY(1,1) PRIMARY KEY,
                    [SoldeData] NVARCHAR(MAX) NULL,
                    [LignesData] NVARCHAR(MAX) NULL,
                    [DateMaj] DATETIME DEFAULT GETDATE(),
                    [EnregistrePar] NVARCHAR(100) NULL
                )
            END
        """)
        cursor.connection.commit()
        print("Table WEB_PROJET23_SYNTHESE créée ou déjà existante.")

if __name__ == "__main__":
    run()
