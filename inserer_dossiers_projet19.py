#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour insérer automatiquement les dossiers dans WEB_S_DOS_ENCOURS pour le projet 19
Les données de base (client, référence, marge) sont récupérées automatiquement depuis COMMANDES et SOCIETES
Les autres champs (avancement, quantité, prix, etc.) restent NULL et seront complétés par l'utilisateur final
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from db import create_web_s_dos_encours

# Liste des numéros de dossiers à insérer
NUMEROS_DOSSIERS = [
    '2025050036',
    '2025050105',
    '2025050111',
    '2025050144',
    '2025050145',
    '2025050146',
    '2025050165',
    '2025060006',
    '2025080010',
    '2025080076',
    '2025090017',
    '2025090024',
    '2025090025',
    '2025090074',
    '2025090089',
    '2025100070',
    '2025100094',
    '2025110035',
    '2025110044',
    '2025110051',
    '2025110086',
    '2025110108',
    '2025110111',
    '2025110112',
    '2025110126',
    '2025110127',
    '2025120005',
    '2025120009',
    '2025120010',
    '2025120016',
    '2025120020',
    '2025120022',
    '2025120025',
    '2025120038',
    '2025120063',
    '2025120064',
    '2025120066',
    '2025120070',
    '2025120071',
    '2025120073',
    '2025120076',
    '2025120079',
    '2025120080',
    '2025120082',
    '2025120084',
    '2025120085',
    '2025120086',
    '2025120087',
    '2025120088',
    '2025120089',
    '2025120093',
    '2025120094',
    '2025120102',
    '2025120103',
    '2025120104',
    '2025120105',
    '2025120109',
    '2025120110',
    '2025120113',
    '2025120115',
    '2025120122',
    '2025120124',
    '2025120125',
    '2025120126',
    '2025120127',
    '2025120132',
    '2025120133',
    '2025120137',
    '2025120150',
    '2025120158',
    '2025120161',
    '2025120162',
    '2025120172'
]

def calculer_valeurs_dossier(numero):
    """
    Récupère les données depuis COMMANDES et calcule les valeurs nécessaires
    Retourne un dictionnaire avec toutes les valeurs calculées
    """
    from db import get_db_cursor
    
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                C.Numero,
                C.QteComm,
                C.PrxVteReel,
                C.ID_DEVIS,
                DC.CoefInt AS MargeCoefInt
            FROM COMMANDES C
            LEFT JOIN DEV_COUTS DC ON DC.ID_DEVIS = C.ID_DEVIS
            WHERE LTRIM(RTRIM(C.Numero)) = ?
        """, (numero.strip(),))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # Quantité par défaut = QteComm de COMMANDES
        quantite = int(row.QteComm) if row.QteComm is not None else None
        
        # Prix unitaire = PrxVteReel / QteComm
        prix_vente_unitaire = None
        if row.PrxVteReel is not None and row.QteComm is not None and row.QteComm > 0:
            prix_vente_unitaire = float(row.PrxVteReel) / float(row.QteComm)
        
        # Prix de vente total = Prix unitaire * Quantité
        prix_vente_total = None
        if prix_vente_unitaire is not None and quantite is not None and quantite > 0:
            prix_vente_total = round(prix_vente_unitaire * quantite, 3)
        
        # Marge (en pourcentage, ex: 45.9)
        marge = None
        if hasattr(row, 'MargeCoefInt') and row.MargeCoefInt is not None:
            try:
                marge = round(float(row.MargeCoefInt), 3)
            except (ValueError, TypeError):
                marge = None
        
        # Coût total estimé = Prix de vente total / (1 + Marge/100)
        ct_estime = None
        if prix_vente_total is not None and marge is not None and marge > 0:
            marge_decimal = marge / 100.0
            ct_estime = round(prix_vente_total / (1 + marge_decimal), 3)
        
        # Coût total et CtRel restent NULL car ils dépendent de l'avancement
        # qui sera défini par l'utilisateur final
        
        return {
            'quantite': quantite,
            'prix_vente_unitaire': prix_vente_unitaire,
            'prix_vente_total': prix_vente_total,
            'marge': marge,
            'ct_estime': ct_estime,
            'cout_total': None,  # Dépend de l'avancement
            'ct_rel': None  # Dépend de l'avancement et du coût total
        }

def inserer_dossiers():
    """Insère tous les dossiers dans WEB_S_DOS_ENCOURS"""
    
    print("=" * 80)
    print("INSERTION DES DOSSIERS DANS WEB_S_DOS_ENCOURS - PROJET 19")
    print("=" * 80)
    print()
    print(f"Nombre de dossiers à insérer: {len(NUMEROS_DOSSIERS)}")
    print()
    
    succes = []
    echecs = []
    
    for idx, numero in enumerate(NUMEROS_DOSSIERS, 1):
        numero_clean = numero.strip()
        print(f"[{idx}/{len(NUMEROS_DOSSIERS)}] Traitement du dossier: {numero_clean}...", end=' ')
        
        try:
            # Calculer les valeurs automatiquement
            valeurs = calculer_valeurs_dossier(numero_clean)
            
            if valeurs is None:
                print(f"✗ ERREUR: Dossier non trouvé dans COMMANDES")
                echecs.append((numero_clean, "Dossier non trouvé dans COMMANDES"))
                continue
            
            # Appeler create_web_s_dos_encours avec les valeurs calculées
            dossier_id = create_web_s_dos_encours(
                numero=numero_clean,
                client=None,  # Sera récupéré depuis COMMANDES/SOCIETES
                reference=None,  # Sera récupéré depuis COMMANDES
                marge=None,  # Sera récupéré depuis DEV_COUTS
                avancement=None,  # À compléter par l'utilisateur final
                quantite=valeurs['quantite'],  # QteComm de COMMANDES par défaut
                prix_vente_total=valeurs['prix_vente_total'],  # Calculé automatiquement
                ct_estime=valeurs['ct_estime'],  # Calculé automatiquement
                cout_total=valeurs['cout_total'],  # NULL - dépend de l'avancement
                ct_rel=valeurs['ct_rel']  # NULL - dépend de l'avancement
            )
            
            if dossier_id:
                print(f"✓ OK (ID: {dossier_id})")
                succes.append((numero_clean, dossier_id))
            else:
                print(f"✗ ÉCHEC - Aucun ID retourné")
                echecs.append((numero_clean, "Aucun ID retourné"))
                
        except Exception as e:
            print(f"✗ ERREUR: {str(e)}")
            echecs.append((numero_clean, str(e)))
    
    print()
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"Total de dossiers traités: {len(NUMEROS_DOSSIERS)}")
    print(f"✓ Succès: {len(succes)}")
    print(f"✗ Échecs: {len(echecs)}")
    print()
    
    if succes:
        print("Dossiers insérés avec succès:")
        for numero, dossier_id in succes:
            print(f"  - {numero} (ID: {dossier_id})")
        print()
    
    if echecs:
        print("Dossiers en échec:")
        for numero, erreur in echecs:
            print(f"  - {numero}: {erreur}")
        print()
    
    print("=" * 80)
    if len(echecs) == 0:
        print("[OK] Tous les dossiers ont été insérés avec succès !")
        print()
        print("[INFO] Valeurs calculées automatiquement pour chaque dossier :")
        print("       ✓ Quantité : QteComm de COMMANDES (modifiable par l'utilisateur)")
        print("       ✓ Prix de vente total : Prix unitaire × Quantité")
        print("       ✓ Coût total estimé : Prix de vente total / (1 + Marge)")
        print()
        print("[INFO] Champs à compléter par l'utilisateur final via l'interface web :")
        print("       - Avancement (Nom_GP_SERVICES)")
        print("       - Coût total (calculé automatiquement selon l'avancement)")
        print("       - Coût total réel (calculé automatiquement)")
    else:
        print("[ATTENTION] Certains dossiers n'ont pas pu être insérés.")
        print("            Vérifiez les erreurs ci-dessus.")
    print("=" * 80)

if __name__ == "__main__":
    inserer_dossiers()
