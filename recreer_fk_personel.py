"""Script pour recréer les contraintes de clé étrangère vers personel"""

from db import get_db_cursor

# Informations des FK à recréer (basées sur ce qui a été supprimé)
fk_to_recreate = [
    {
        'name': 'FK_WEB_GMAO_PERSONEL_OPREC',
        'parent_table': 'WEB_GMAO',
        'parent_column': 'MatrOpRec',
        'referenced_column': 'Matricule'
    },
    {
        'name': 'FK_WEB_GMAO_REPARATION_Intervenant',
        'parent_table': 'WEB_GMAO_REPARATION',
        'parent_column': 'MatInter',
        'referenced_column': 'Matricule'
    },
    {
        'name': 'FK_WEB_GMAO_PREVENTIVE_personel',
        'parent_table': 'WEB_GMAO_PREVENTIVE',
        'parent_column': 'Matricule_personel',
        'referenced_column': 'Matricule'
    }
]

with get_db_cursor() as cursor:
    print("Recreation des contraintes de cle etrangere vers personel...")
    print("")
    
    for fk in fk_to_recreate:
        try:
            # Vérifier si la FK existe déjà
            cursor.execute("""
                SELECT name
                FROM sys.foreign_keys
                WHERE name = ?
            """, (fk['name'],))
            
            if cursor.fetchone():
                print(f"[INFO] La contrainte {fk['name']} existe deja")
                continue
            
            # Créer la FK
            cursor.execute(f"""
                ALTER TABLE dbo.[{fk['parent_table']}]
                ADD CONSTRAINT [{fk['name']}] 
                FOREIGN KEY ([{fk['parent_column']}]) 
                REFERENCES dbo.personel([{fk['referenced_column']}])
            """)
            print(f"[OK] Contrainte FK {fk['name']} recreee sur {fk['parent_table']} ({fk['parent_column']} -> personel.{fk['referenced_column']})")
        except Exception as e:
            print(f"[ERREUR] Impossible de recreer la FK {fk['name']}: {e}")
    
    cursor.connection.commit()
    print("")
    print("Termine!")
