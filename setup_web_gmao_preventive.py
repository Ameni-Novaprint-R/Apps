"""
Script pour créer la table WEB_GMAO_PREVENTIVE dans la base de données novaprint_restored
"""

from db import get_db_cursor

def setup_web_gmao_preventive():
    """Crée la table WEB_GMAO_PREVENTIVE avec ses triggers de synchronisation"""
    
    try:
        with get_db_cursor() as cursor:
            # Vérifier si la table existe déjà
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'dbo' 
                AND TABLE_NAME = 'WEB_GMAO_PREVENTIVE'
            """)
            
            if cursor.fetchone()[0] > 0:
                print("⚠️ La table WEB_GMAO_PREVENTIVE existe déjà.")
                print("Pour recréer la table, supprimez-la d'abord avec: DROP TABLE WEB_GMAO_PREVENTIVE;")
                return False
            
            print("📝 Création de la table WEB_GMAO_PREVENTIVE...")
            
            # Créer la table
            cursor.execute("""
                CREATE TABLE dbo.WEB_GMAO_PREVENTIVE (
                    ID INT IDENTITY(1,1) PRIMARY KEY,
                    Nom_GP_POSTES VARCHAR(50) NULL,
                    NomPrenom_personel NVARCHAR(101) NULL,
                    Matricule_personel INT NULL,
                    DateCreation DATETIME DEFAULT GETDATE(),
                    DateModification DATETIME DEFAULT GETDATE(),
                    CONSTRAINT FK_WEB_GMAO_PREVENTIVE_personel 
                        FOREIGN KEY (Matricule_personel) REFERENCES personel(Matricule)
                )
            """)
            cursor.connection.commit()
            print("✅ Table créée avec succès!")
            
            # Créer les index
            print("📝 Création des index...")
            cursor.execute("""
                CREATE NONCLUSTERED INDEX IX_WEB_GMAO_PREVENTIVE_Matricule_personel 
                ON dbo.WEB_GMAO_PREVENTIVE(Matricule_personel)
            """)
            cursor.execute("""
                CREATE NONCLUSTERED INDEX IX_WEB_GMAO_PREVENTIVE_Nom_GP_POSTES 
                ON dbo.WEB_GMAO_PREVENTIVE(Nom_GP_POSTES)
            """)
            cursor.connection.commit()
            print("✅ Index créés avec succès!")
            
            # Supprimer les triggers existants s'ils existent
            print("📝 Création des triggers de synchronisation...")
            
            triggers = [
                ("TR_GP_POSTES_UPDATE_WEB_GMAO_PREVENTIVE", """
                    CREATE TRIGGER TR_GP_POSTES_UPDATE_WEB_GMAO_PREVENTIVE
                    ON [dbo].[GP_POSTES]
                    AFTER UPDATE
                    AS
                    BEGIN
                        SET NOCOUNT ON;
                        UPDATE w
                        SET w.Nom_GP_POSTES = i.Nom,
                            w.DateModification = GETDATE()
                        FROM [dbo].[WEB_GMAO_PREVENTIVE] w
                        INNER JOIN inserted i ON w.Nom_GP_POSTES = (SELECT Nom FROM deleted WHERE ID = i.ID)
                        WHERE i.Nom IS NOT NULL AND i.Nom != '';
                    END
                """),
                ("TR_PERSONEL_UPDATE_WEB_GMAO_PREVENTIVE", """
                    CREATE TRIGGER TR_PERSONEL_UPDATE_WEB_GMAO_PREVENTIVE
                    ON [dbo].[personel]
                    AFTER UPDATE
                    AS
                    BEGIN
                        SET NOCOUNT ON;
                        UPDATE w
                        SET w.NomPrenom_personel = LTRIM(RTRIM(COALESCE(i.Nom, '') + ' ' + COALESCE(i.Prenom, ''))),
                            w.DateModification = GETDATE()
                        FROM [dbo].[WEB_GMAO_PREVENTIVE] w
                        INNER JOIN inserted i ON w.Matricule_personel = i.Matricule
                        WHERE i.Matricule IS NOT NULL;
                    END
                """),
                ("TR_WEB_GMAO_PREVENTIVE_INSERT", """
                    CREATE TRIGGER TR_WEB_GMAO_PREVENTIVE_INSERT
                    ON [dbo].[WEB_GMAO_PREVENTIVE]
                    AFTER INSERT
                    AS
                    BEGIN
                        SET NOCOUNT ON;
                        UPDATE w
                        SET w.NomPrenom_personel = LTRIM(RTRIM(COALESCE(p.Nom, '') + ' ' + COALESCE(p.Prenom, '')))
                        FROM [dbo].[WEB_GMAO_PREVENTIVE] w
                        INNER JOIN inserted i ON w.ID = i.ID
                        LEFT JOIN [dbo].[personel] p ON w.Matricule_personel = p.Matricule
                        WHERE w.Matricule_personel IS NOT NULL;
                    END
                """),
                ("TR_WEB_GMAO_PREVENTIVE_UPDATE", """
                    CREATE TRIGGER TR_WEB_GMAO_PREVENTIVE_UPDATE
                    ON [dbo].[WEB_GMAO_PREVENTIVE]
                    AFTER UPDATE
                    AS
                    BEGIN
                        SET NOCOUNT ON;
                        UPDATE w
                        SET w.NomPrenom_personel = LTRIM(RTRIM(COALESCE(p.Nom, '') + ' ' + COALESCE(p.Prenom, ''))),
                            w.DateModification = GETDATE()
                        FROM [dbo].[WEB_GMAO_PREVENTIVE] w
                        INNER JOIN inserted i ON w.ID = i.ID
                        LEFT JOIN [dbo].[personel] p ON w.Matricule_personel = p.Matricule
                        WHERE w.Matricule_personel IS NOT NULL
                          AND (i.Matricule_personel != (SELECT Matricule_personel FROM deleted WHERE ID = i.ID)
                               OR i.Matricule_personel IS NOT NULL);
                    END
                """)
            ]
            
            for trigger_name, trigger_sql in triggers:
                # Supprimer le trigger s'il existe
                cursor.execute(f"""
                    IF OBJECT_ID('{trigger_name}', 'TR') IS NOT NULL
                        DROP TRIGGER {trigger_name}
                """)
                # Créer le trigger
                cursor.execute(trigger_sql)
                print(f"✅ Trigger {trigger_name} créé")
            
            cursor.connection.commit()
            print("✅ Tous les triggers créés avec succès!")
            
            print("")
            print("📌 Structure de la table:")
            print("   - ID : Identifiant unique (IDENTITY)")
            print("   - Nom_GP_POSTES : Nom de la machine (lecture seule depuis la page)")
            print("   - NomPrenom_personel : Nom complet de l'opérateur (synchronisé automatiquement)")
            print("   - Matricule_personel : Matricule de l'opérateur (FK vers personel.Matricule)")
            print("   - DateCreation : Date de création")
            print("   - DateModification : Date de modification")
            print("")
            print("🔄 Triggers créés:")
            print("   - TR_GP_POSTES_UPDATE_WEB_GMAO_PREVENTIVE : Synchronise Nom_GP_POSTES depuis GP_POSTES")
            print("   - TR_PERSONEL_UPDATE_WEB_GMAO_PREVENTIVE : Synchronise NomPrenom_personel depuis personel")
            print("   - TR_WEB_GMAO_PREVENTIVE_INSERT : Synchronise NomPrenom_personel lors de l'insertion")
            print("   - TR_WEB_GMAO_PREVENTIVE_UPDATE : Synchronise NomPrenom_personel lors de la mise à jour")
            print("")
            print("⚠️ IMPORTANT:")
            print("   - Les données de GP_POSTES et personel sont en lecture seule depuis la page")
            print("   - Toute mise à jour dans GP_POSTES ou personel sera automatiquement reflétée dans WEB_GMAO_PREVENTIVE")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table WEB_GMAO_PREVENTIVE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    setup_web_gmao_preventive()

















