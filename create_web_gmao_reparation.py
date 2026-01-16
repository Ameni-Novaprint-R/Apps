"""
Script Python pour créer la table WEB_GMAO_REPARATION
et migrer les données depuis WEB_GMAO
"""
from db import get_db_cursor
import sys

def create_web_gmao_reparation_table():
    """Crée la table WEB_GMAO_REPARATION et migre les données"""
    try:
        with get_db_cursor() as cursor:
            # Vérifier si la table existe déjà
            cursor.execute("""
                SELECT COUNT(*) as table_exists
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = 'WEB_GMAO_REPARATION'
            """)
            result = cursor.fetchone()
            if result and result.table_exists > 0:
                print("⚠️ La table WEB_GMAO_REPARATION existe déjà.")
                response = input("Voulez-vous la supprimer et la recréer? (o/n): ")
                if response.lower() == 'o':
                    cursor.execute("DROP TABLE WEB_GMAO_REPARATION")
                    cursor.connection.commit()
                    print("✅ Table supprimée.")
                else:
                    print("❌ Opération annulée.")
                    return False
            
            print("📝 Création de la table WEB_GMAO_REPARATION...")
            
            # Créer la table
            cursor.execute("""
                CREATE TABLE dbo.WEB_GMAO_REPARATION (
                    ID INT IDENTITY(1,1) PRIMARY KEY,
                    DteDeb DATETIME NULL,
                    DteFin DATETIME NULL,
                    TpsReel AS (CASE 
                        WHEN DteDeb IS NOT NULL AND DteFin IS NOT NULL 
                        THEN CAST(DATEDIFF(MINUTE, DteDeb, DteFin) AS FLOAT) / 60.0 
                        ELSE NULL 
                    END) PERSISTED,
                    Nat VARCHAR(4) NULL CHECK (Nat IN ('Mec', 'Elec')),
                    ID_StatRep INT NULL,
                    TypeIN CHAR(1) NULL CHECK (TypeIN IN ('R','P')) DEFAULT 'R',
                    MatInter INT NULL,
                    Intervenant NVARCHAR(101) NULL,
                    ID_WEB_GMAO_Dem_In INT NULL,
                    PostesReel VARCHAR(50) NULL,
                    DateCreation DATETIME DEFAULT GETDATE(),
                    DateModification DATETIME DEFAULT GETDATE(),
                    CONSTRAINT FK_WEB_GMAO_REPARATION_WEB_GMAO 
                        FOREIGN KEY (ID_WEB_GMAO_Dem_In) REFERENCES WEB_GMAO(ID) ON DELETE SET NULL,
                    CONSTRAINT FK_WEB_GMAO_REPARATION_StatRep 
                        FOREIGN KEY (ID_StatRep) REFERENCES WEB_GMAO_StatRep(ID),
                    CONSTRAINT FK_WEB_GMAO_REPARATION_Intervenant 
                        FOREIGN KEY (MatInter) REFERENCES personel(Matricule),
                    CONSTRAINT CK_WEB_GMAO_REPARATION_StatRep_When_DemIn_Null
                        CHECK (ID_WEB_GMAO_Dem_In IS NOT NULL OR ID_StatRep IS NULL)
                )
            """)
            cursor.connection.commit()
            print("✅ Table créée avec succès!")
            
            # Créer les index
            print("📝 Création des index...")
            cursor.execute("""
                CREATE NONCLUSTERED INDEX IX_WEB_GMAO_REPARATION_ID_WEB_GMAO_Dem_In 
                ON dbo.WEB_GMAO_REPARATION(ID_WEB_GMAO_Dem_In)
            """)
            cursor.execute("""
                CREATE NONCLUSTERED INDEX IX_WEB_GMAO_REPARATION_MatInter 
                ON dbo.WEB_GMAO_REPARATION(MatInter)
            """)
            cursor.execute("""
                CREATE NONCLUSTERED INDEX IX_WEB_GMAO_REPARATION_ID_StatRep 
                ON dbo.WEB_GMAO_REPARATION(ID_StatRep)
            """)
            cursor.connection.commit()
            print("✅ Index créés!")
            
            # Migrer les données
            print("📝 Migration des données depuis WEB_GMAO...")
            cursor.execute("""
                INSERT INTO dbo.WEB_GMAO_REPARATION (
                    DteDeb, DteFin, Nat, ID_StatRep, TypeIN, MatInter, Intervenant,
                    ID_WEB_GMAO_Dem_In, PostesReel, DateCreation, DateModification
                )
                SELECT 
                    g.DteDeb, g.DteFin, g.Nat, g.ID_StatRep, 'R', g.MatInter, g.Internvenant,
                    g.ID as ID_WEB_GMAO_Dem_In, g.PostesReel, g.DateCreation, g.DateModification
                FROM WEB_GMAO g
                WHERE g.DteDeb IS NOT NULL 
                   OR g.DteFin IS NOT NULL 
                   OR g.MatInter IS NOT NULL 
                   OR g.ID_StatRep IS NOT NULL
                   OR g.Nat IS NOT NULL
            """)
            rows_affected = cursor.rowcount
            cursor.connection.commit()
            print(f"✅ {rows_affected} lignes migrées!")
            
            # Afficher les statistiques
            cursor.execute("""
                SELECT 
                    COUNT(*) as NombreReparations,
                    COUNT(ID_WEB_GMAO_Dem_In) as AvecDemandeIntervention,
                    COUNT(*) - COUNT(ID_WEB_GMAO_Dem_In) as SansDemandeIntervention
                FROM WEB_GMAO_REPARATION
            """)
            stats = cursor.fetchone()
            print("\n📊 Statistiques:")
            print(f"   - Nombre total de réparations: {stats.NombreReparations}")
            print(f"   - Avec demande d'intervention: {stats.AvecDemandeIntervention}")
            print(f"   - Sans demande d'intervention: {stats.SansDemandeIntervention}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Création de la table WEB_GMAO_REPARATION")
    print("=" * 60)
    success = create_web_gmao_reparation_table()
    print("=" * 60)
    if success:
        print("✅ Opération terminée avec succès!")
    else:
        print("❌ Opération échouée!")
        sys.exit(1)





