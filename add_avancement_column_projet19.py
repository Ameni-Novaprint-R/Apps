"""
Script pour ajouter la colonne Nom_GP_SERVICES (Avancement) à la table WEB_S_DOS_ENCOURS
Projet 19 - Gestion des Dossiers en Cours
CORRECTION : Utilise Nom_GP_SERVICES au lieu de Nom_GP_POSTES
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from db import get_db_cursor

def add_avancement_column():
    """Ajoute la colonne Nom_GP_SERVICES si elle n'existe pas"""
    try:
        with get_db_cursor() as cursor:
            print("=" * 80)
            print("AJOUT DE LA COLONNE Nom_GP_SERVICES À WEB_S_DOS_ENCOURS")
            print("=" * 80)
            print()
            
            # Vérifier si la colonne Nom_GP_SERVICES existe déjà
            cursor.execute("""
                SELECT COUNT(*) as col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                AND COLUMN_NAME = 'Nom_GP_SERVICES'
            """)
            col_exists = cursor.fetchone().col_exists > 0
            
            if col_exists:
                print("✅ La colonne Nom_GP_SERVICES existe déjà dans WEB_S_DOS_ENCOURS")
                print()
                
                # Afficher les informations de la colonne
                cursor.execute("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        CHARACTER_MAXIMUM_LENGTH,
                        IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                    AND COLUMN_NAME = 'Nom_GP_SERVICES'
                """)
                col_info = cursor.fetchone()
                if col_info:
                    max_len = f"({col_info.CHARACTER_MAXIMUM_LENGTH})" if col_info.CHARACTER_MAXIMUM_LENGTH else ""
                    nullable = "NULL" if col_info.IS_NULLABLE == "YES" else "NOT NULL"
                    print(f"   Type: {col_info.DATA_TYPE}{max_len}")
                    print(f"   Nullable: {nullable}")
                    print()
            else:
                print("⚠️  La colonne Nom_GP_SERVICES n'existe pas encore")
                print("   Ajout de la colonne...")
                print()
                
                try:
                    cursor.execute("""
                        ALTER TABLE WEB_S_DOS_ENCOURS
                        ADD Nom_GP_SERVICES NVARCHAR(255) NULL
                    """)
                    cursor.connection.commit()
                    print("✅ Colonne Nom_GP_SERVICES ajoutée avec succès!")
                    print()
                except Exception as e:
                    print(f"❌ Erreur lors de l'ajout de la colonne: {e}")
                    print()
                    raise
            
            # Vérifier et migrer depuis Nom_GP_POSTES si elle existe
            cursor.execute("""
                SELECT COUNT(*) as col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                AND COLUMN_NAME = 'Nom_GP_POSTES'
            """)
            old_col_exists = cursor.fetchone().col_exists > 0
            
            if old_col_exists:
                print("⚠️  Ancienne colonne Nom_GP_POSTES détectée")
                print("   Migration des données vers Nom_GP_SERVICES...")
                print()
                
                try:
                    # Copier les données
                    cursor.execute("""
                        UPDATE WEB_S_DOS_ENCOURS
                        SET Nom_GP_SERVICES = Nom_GP_POSTES
                        WHERE Nom_GP_SERVICES IS NULL AND Nom_GP_POSTES IS NOT NULL
                    """)
                    cursor.connection.commit()
                    print("✅ Données migrées de Nom_GP_POSTES vers Nom_GP_SERVICES")
                    print()
                    
                    # Supprimer l'ancienne colonne
                    cursor.execute("""
                        ALTER TABLE WEB_S_DOS_ENCOURS
                        DROP COLUMN Nom_GP_POSTES
                    """)
                    cursor.connection.commit()
                    print("✅ Ancienne colonne Nom_GP_POSTES supprimée")
                    print()
                except Exception as e:
                    print(f"⚠️  Erreur lors de la migration: {e}")
                    print("   La colonne Nom_GP_POSTES sera conservée")
                    print()
            
            print("=" * 80)
            print("OPÉRATION TERMINÉE")
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    add_avancement_column()
