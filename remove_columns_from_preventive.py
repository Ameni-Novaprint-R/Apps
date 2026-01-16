"""
Script pour supprimer les colonnes de WEB_GMAO_PREVENTIVE
- NomPrenom_personel
- Matricule_personel
- DtePrev
- DteReal
"""
from db import get_db_cursor

def remove_columns_from_preventive():
    """Supprime les colonnes spécifiées de WEB_GMAO_PREVENTIVE"""
    try:
        with get_db_cursor() as cursor:
            print("=" * 60)
            print("SUPPRESSION DES COLONNES DE WEB_GMAO_PREVENTIVE")
            print("=" * 60)
            print()
            
            # Supprimer d'abord les dépendances (indexes et contraintes)
            print("🔍 Recherche et suppression des dépendances...")
            
            # Supprimer l'index sur Matricule_personel
            cursor.execute("""
                SELECT name FROM sys.indexes
                WHERE object_id = OBJECT_ID('WEB_GMAO_PREVENTIVE')
                AND name = 'IX_WEB_GMAO_PREVENTIVE_Matricule_personel'
            """)
            if cursor.fetchone():
                print("📝 Suppression de l'index IX_WEB_GMAO_PREVENTIVE_Matricule_personel...")
                cursor.execute("DROP INDEX IX_WEB_GMAO_PREVENTIVE_Matricule_personel ON WEB_GMAO_PREVENTIVE")
                cursor.connection.commit()
                print("   ✅ Index supprimé")
            
            # Supprimer la contrainte de clé étrangère sur Matricule_personel
            cursor.execute("""
                SELECT name FROM sys.foreign_keys
                WHERE parent_object_id = OBJECT_ID('WEB_GMAO_PREVENTIVE')
                AND name = 'FK_WEB_GMAO_PREVENTIVE_personel'
            """)
            fk = cursor.fetchone()
            if fk:
                print("📝 Suppression de la contrainte FK_WEB_GMAO_PREVENTIVE_personel...")
                cursor.execute("ALTER TABLE WEB_GMAO_PREVENTIVE DROP CONSTRAINT FK_WEB_GMAO_PREVENTIVE_personel")
                cursor.connection.commit()
                print("   ✅ Contrainte supprimée")
            
            # Supprimer l'index sur DtePrev
            cursor.execute("""
                SELECT name FROM sys.indexes
                WHERE object_id = OBJECT_ID('WEB_GMAO_PREVENTIVE')
                AND name = 'IX_WEB_GMAO_PREVENTIVE_DtePrev'
            """)
            if cursor.fetchone():
                print("📝 Suppression de l'index IX_WEB_GMAO_PREVENTIVE_DtePrev...")
                cursor.execute("DROP INDEX IX_WEB_GMAO_PREVENTIVE_DtePrev ON WEB_GMAO_PREVENTIVE")
                cursor.connection.commit()
                print("   ✅ Index supprimé")
            
            # Supprimer l'index sur DteReal
            cursor.execute("""
                SELECT name FROM sys.indexes
                WHERE object_id = OBJECT_ID('WEB_GMAO_PREVENTIVE')
                AND name = 'IX_WEB_GMAO_PREVENTIVE_DteReal'
            """)
            if cursor.fetchone():
                print("📝 Suppression de l'index IX_WEB_GMAO_PREVENTIVE_DteReal...")
                cursor.execute("DROP INDEX IX_WEB_GMAO_PREVENTIVE_DteReal ON WEB_GMAO_PREVENTIVE")
                cursor.connection.commit()
                print("   ✅ Index supprimé")
            
            print()
            
            columns_to_remove = [
                'NomPrenom_personel',
                'Matricule_personel',
                'DtePrev',
                'DteReal'
            ]
            
            for column_name in columns_to_remove:
                # Vérifier si la colonne existe
                cursor.execute("""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'WEB_GMAO_PREVENTIVE'
                    AND COLUMN_NAME = ?
                """, (column_name,))
                
                if cursor.fetchone():
                    print(f"📝 Suppression de la colonne '{column_name}'...")
                    try:
                        cursor.execute(f"""
                            ALTER TABLE WEB_GMAO_PREVENTIVE
                            DROP COLUMN {column_name}
                        """)
                        cursor.connection.commit()
                        print(f"   ✅ Colonne '{column_name}' supprimée avec succès!")
                    except Exception as e:
                        print(f"   ❌ Erreur lors de la suppression de '{column_name}': {e}")
                        # Continuer avec les autres colonnes même en cas d'erreur
                else:
                    print(f"   ⚠️ La colonne '{column_name}' n'existe pas (déjà supprimée ou jamais créée)")
                print()
            
            # Vérifier les colonnes restantes
            print("📊 Colonnes restantes dans WEB_GMAO_PREVENTIVE:")
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_GMAO_PREVENTIVE'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns = cursor.fetchall()
            for col in columns:
                print(f"   - {col.COLUMN_NAME} ({col.DATA_TYPE}, Nullable: {col.IS_NULLABLE})")
            
            print()
            print("=" * 60)
            print("✅ Opération terminée!")
            print("=" * 60)
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la suppression des colonnes : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    remove_columns_from_preventive()

