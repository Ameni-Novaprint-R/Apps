"""
Script de test pour vérifier le pré-remplissage automatique depuis WEB_TRAITEMENTS
"""
from db import get_traitement_data_for_controle, get_db_cursor

def test():
    print("=" * 80)
    print("TEST: Pre-remplissage automatique Projet 10")
    print("=" * 80)
    print()
    
    # 1. Trouver des numéros de commande avec traitement OFFSET FEUILLES et TYPO
    with get_db_cursor() as cursor:
        # OFFSET FEUILLES
        cursor.execute("""
            SELECT DISTINCT TOP 3
                WT.Numero_COMMANDES,
                WT.Nom_GP_SERVICES,
                WT.PostesReel,
                WT.Nom_personel,
                WT.Prenom_personel
            FROM WEB_TRAITEMENTS WT
            WHERE WT.Nom_GP_SERVICES = 'OFFSET FEUILLES'
              AND WT.PostesReel IS NOT NULL
              AND WT.PostesReel != ''
              AND WT.Nom_personel IS NOT NULL
              AND WT.Prenom_personel IS NOT NULL
            ORDER BY WT.Numero_COMMANDES DESC
        """)
        rows_offset = cursor.fetchall()
        
        # TYPO
        cursor.execute("""
            SELECT DISTINCT TOP 3
                WT.Numero_COMMANDES,
                WT.Nom_GP_SERVICES,
                WT.PostesReel,
                WT.Nom_personel,
                WT.Prenom_personel
            FROM WEB_TRAITEMENTS WT
            WHERE WT.Nom_GP_SERVICES = 'TYPO'
              AND WT.PostesReel IS NOT NULL
              AND WT.PostesReel != ''
              AND WT.Nom_personel IS NOT NULL
              AND WT.Prenom_personel IS NOT NULL
            ORDER BY WT.Numero_COMMANDES DESC
        """)
        rows_typo = cursor.fetchall()
        
        if not rows_offset and not rows_typo:
            print("  [ATTENTION] Aucun traitement OFFSET FEUILLES ou TYPO trouve dans WEB_TRAITEMENTS")
            print("  [INFO] Le pre-remplissage ne fonctionnera que si des donnees existent.")
            return
        
        print(f"Nombre de traitements OFFSET FEUILLES trouves: {len(rows_offset)}")
        print(f"Nombre de traitements TYPO trouves: {len(rows_typo)}")
        print()
        
        # 2. Tester la fonction get_traitement_data_for_controle avec OFFSET FEUILLES
        if rows_offset:
            print("=== TEST OFFSET FEUILLES (Machine d'impression) ===")
            for row in rows_offset[:2]:  # Tester seulement 2
                numero = (row.Numero_COMMANDES or '').strip()
                if not numero:
                    continue
                
                print(f"Test avec numero de commande: {numero}")
                data = get_traitement_data_for_controle(numero)
                
                if data:
                    print(f"  [OK] Donnees recuperees:")
                    if data.get('machine_impression'):
                        print(f"    - Machine impression: {data['machine_impression']}")
                    if data.get('operateurs_impression'):
                        print(f"    - Operateurs impression: {len(data['operateurs_impression'])}")
                        for op in data['operateurs_impression']:
                            print(f"      * {op['nom']} {op['prenom']}")
                    if data.get('machine_decoupe'):
                        print(f"    - Machine decoupe: {data['machine_decoupe']}")
                    if data.get('operateurs_decoupe'):
                        print(f"    - Operateurs decoupe: {len(data['operateurs_decoupe'])}")
                        for op in data['operateurs_decoupe']:
                            print(f"      * {op['nom']} {op['prenom']}")
                else:
                    print(f"  [ATTENTION] Aucune donnee retournee")
                print()
        
        # 3. Tester avec TYPO
        if rows_typo:
            print("=== TEST TYPO (Machine de découpe) ===")
            for row in rows_typo[:2]:  # Tester seulement 2
                numero = (row.Numero_COMMANDES or '').strip()
                if not numero:
                    continue
                
                print(f"Test avec numero de commande: {numero}")
                data = get_traitement_data_for_controle(numero)
                
                if data:
                    print(f"  [OK] Donnees recuperees:")
                    if data.get('machine_impression'):
                        print(f"    - Machine impression: {data['machine_impression']}")
                    if data.get('operateurs_impression'):
                        print(f"    - Operateurs impression: {len(data['operateurs_impression'])}")
                    if data.get('machine_decoupe'):
                        print(f"    - Machine decoupe: {data['machine_decoupe']}")
                    if data.get('operateurs_decoupe'):
                        print(f"    - Operateurs decoupe: {len(data['operateurs_decoupe'])}")
                        for op in data['operateurs_decoupe']:
                            print(f"      * {op['nom']} {op['prenom']}")
                else:
                    print(f"  [ATTENTION] Aucune donnee retournee")
                print()
        
        # 4. Tester avec un numéro qui n'existe pas
        print("=== TEST NUMERO INEXISTANT ===")
        print("Test avec un numero inexistant: 'TEST123'")
        data = get_traitement_data_for_controle('TEST123')
        if data is None:
            print("  [OK] Aucune donnee retournee (comportement attendu)")
        else:
            print(f"  [ATTENTION] Donnees retournees: {data}")
        print()
        
        print("=" * 80)
        print("TEST TERMINE")
        print("=" * 80)
        print()
        print("FONCTIONNALITE:")
        print("  - Lors de la selection d'un numero de commande dans le formulaire")
        print("  - Si un traitement OFFSET FEUILLES existe pour ce numero:")
        print("    * Machine d'impression: PostesReel")
        print("    * Operateur(s) Machine d'impression: Nom_personel + Prenom_personel")
        print("  - Si un traitement TYPO existe pour ce numero:")
        print("    * Machine de decoupe: PostesReel")
        print("    * Operateur(s) Machine de decoupe: Nom_personel + Prenom_personel")
        print("=" * 80)

if __name__ == "__main__":
    test()
