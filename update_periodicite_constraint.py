"""
Script pour mettre à jour la contrainte CHECK de Periodicite
"""

from db import get_db_cursor

def update_periodicite_constraint():
    """Met à jour la contrainte CHECK pour inclure les nouvelles périodicités"""
    
    try:
        with get_db_cursor() as cursor:
            # Trouver et supprimer l'ancienne contrainte
            print("🔍 Recherche de l'ancienne contrainte...")
            cursor.execute("""
                SELECT name 
                FROM sys.check_constraints 
                WHERE parent_object_id = OBJECT_ID('WEB_GMAO_PREVENTIVE') 
                  AND definition LIKE '%Periodicite%'
            """)
            
            constraint = cursor.fetchone()
            if constraint:
                constraint_name = constraint.name
                print(f"   ✅ Contrainte trouvée: {constraint_name}")
                cursor.execute(f"ALTER TABLE dbo.WEB_GMAO_PREVENTIVE DROP CONSTRAINT {constraint_name}")
                cursor.connection.commit()
                print(f"   ✅ Ancienne contrainte supprimée")
            else:
                print("   ⚠️  Aucune contrainte existante trouvée")
            
            # Créer la nouvelle contrainte
            print("\n📝 Création de la nouvelle contrainte...")
            cursor.execute("""
                ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
                ADD CONSTRAINT CK_WEB_GMAO_PREVENTIVE_Periodicite 
                CHECK (Periodicite IN (
                    'Quotidienne', 
                    'Hebdomadaire', 
                    'Mensuelle', 
                    'Trimestrielle', 
                    'Semestrielle', 
                    'Annuelle',
                    'Tous les 2 ans',
                    'Tous les 3 ans',
                    'Tous les 5 ans'
                ) OR Periodicite IS NULL)
            """)
            cursor.connection.commit()
            
            print("✅ Nouvelle contrainte créée avec succès!")
            print("\n📌 Périodicités acceptées:")
            print("   - Quotidienne")
            print("   - Hebdomadaire")
            print("   - Mensuelle")
            print("   - Trimestrielle")
            print("   - Semestrielle")
            print("   - Annuelle")
            print("   - Tous les 2 ans")
            print("   - Tous les 3 ans")
            print("   - Tous les 5 ans")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour de la contrainte: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    update_periodicite_constraint()

















