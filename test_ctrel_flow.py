"""
Script de test pour vérifier le flux complet de CtRel
Teste chaque étape du processus
"""
import sys
sys.path.insert(0, 'C:\\Apps')

from db import (
    get_commande_by_numero,
    create_web_s_dos_encours,
    get_web_s_dos_encours_by_numero,
    get_web_s_dos_encours
)

def test_ctrel_flow(numero='2025050176'):
    print("="*80)
    print(f"TEST COMPLET DU FLUX CTREL POUR LE DOSSIER {numero}")
    print("="*80)
    
    # Étape 1 : Récupérer les données de la commande
    print("\n[ÉTAPE 1] Récupération des données de la commande...")
    commande = get_commande_by_numero(numero)
    if not commande:
        print(f"[ERREUR] Commande {numero} non trouvee")
        return
    print(f"[OK] Commande trouvee:")
    print(f"   - Quantité (QteComm): {commande.get('quantite')}")
    print(f"   - Prix unitaire: {commande.get('prix_vente_unitaire')}")
    
    # Étape 2 : Simuler la création avec ct_rel
    print("\n[ÉTAPE 2] Création du dossier avec ct_rel...")
    qte_comm = commande.get('quantite', 1000)  # Valeur par défaut
    quantite_app = 500  # Quantité saisie dans l'application
    cout_total = 1000.0  # Coût total calculé
    ct_rel_attendu = (cout_total / qte_comm) * quantite_app
    
    print(f"   - QteComm (base): {qte_comm}")
    print(f"   - Quantité (app): {quantite_app}")
    print(f"   - Coût total: {cout_total}")
    print(f"   - CtRel attendu: {ct_rel_attendu}")
    
    dossier_id = create_web_s_dos_encours(
        numero=numero,
        client=commande.get('client'),
        reference=commande.get('reference'),
        marge=commande.get('marge'),
        avancement='Matière première sortie',
        quantite=quantite_app,
        prix_vente_total=quantite_app * commande.get('prix_vente_unitaire', 0),
        ct_estime=None,
        cout_total=cout_total,
        ct_rel=ct_rel_attendu
    )
    
    if not dossier_id:
        print("[ERREUR] Erreur lors de la creation du dossier")
        return
    
    print(f"[OK] Dossier cree avec ID: {dossier_id}")
    
    # Étape 3 : Vérifier que ct_rel a été enregistré
    print("\n[ÉTAPE 3] Vérification de l'enregistrement de ct_rel...")
    dossier = get_web_s_dos_encours_by_numero(numero)
    if not dossier:
        print("[ERREUR] Dossier non trouve apres creation")
        return
    
    ct_rel_enregistre = dossier.get('ct_rel')
    print(f"   - CtRel enregistre: {ct_rel_enregistre}")
    print(f"   - CtRel attendu: {ct_rel_attendu}")
    
    if ct_rel_enregistre is None:
        print("[PROBLEME] CtRel est NULL dans la base de donnees")
        print("   -> Verifier que la colonne CtRel existe")
        print("   -> Verifier que la valeur a ete passee a create_web_s_dos_encours")
    elif abs(ct_rel_enregistre - ct_rel_attendu) < 0.001:
        print("[OK] CtRel correctement enregistre")
    else:
        print(f"[ATTENTION] CtRel enregistre ({ct_rel_enregistre}) ne correspond pas a l'attendu ({ct_rel_attendu})")
    
    # Étape 4 : Vérifier la récupération depuis get_web_s_dos_encours
    print("\n[ÉTAPE 4] Vérification de la récupération depuis get_web_s_dos_encours...")
    tous_dossiers = get_web_s_dos_encours()
    dossier_trouve = None
    for d in tous_dossiers:
        if d.get('numero') == numero:
            dossier_trouve = d
            break
    
    if dossier_trouve:
        ct_rel_recupere = dossier_trouve.get('ct_rel')
        print(f"   - CtRel récupéré: {ct_rel_recupere}")
        if ct_rel_recupere is None:
            print("[PROBLEME] CtRel est NULL lors de la recuperation")
        elif abs(ct_rel_recupere - ct_rel_attendu) < 0.001:
            print("[OK] CtRel correctement recupere")
        else:
            print(f"[ATTENTION] CtRel recupere ({ct_rel_recupere}) ne correspond pas a l'attendu ({ct_rel_attendu})")
    else:
        print("[ERREUR] Dossier non trouve dans la liste")
    
    print("\n" + "="*80)
    print("TEST TERMINÉ")
    print("="*80)

if __name__ == "__main__":
    import sys
    numero = sys.argv[1] if len(sys.argv) > 1 else '2025050176'
    test_ctrel_flow(numero)
