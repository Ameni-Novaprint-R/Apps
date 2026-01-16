"""
Script pour mettre à jour PrixVenteTotal pour les dossiers existants
Projet 19 - Gestion des Dossiers en Cours
Calcul : PrixVenteUnitaire * QteComm_COMMANDES
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from db import get_db_cursor

def update_existing_prix_vente_total():
    """Met à jour PrixVenteTotal pour les dossiers existants"""
    try:
        with get_db_cursor() as cursor:
            print("=" * 80)
            print("MISE À JOUR DE PrixVenteTotal POUR LES DOSSIERS EXISTANTS")
            print("=" * 80)
            print()
            
            # Vérifier si la colonne PrixVenteTotal existe
            cursor.execute("""
                SELECT COUNT(*) as col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                AND COLUMN_NAME = 'PrixVenteTotal'
            """)
            col_exists = cursor.fetchone().col_exists > 0
            
            if not col_exists:
                print("❌ La colonne PrixVenteTotal n'existe pas dans WEB_S_DOS_ENCOURS")
                print("   Veuillez d'abord exécuter add_prix_vente_total_projet19.py")
                return False
            
            # Compter les dossiers à mettre à jour
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM WEB_S_DOS_ENCOURS
                WHERE PrixVenteUnitaire IS NOT NULL
                AND QteComm_COMMANDES IS NOT NULL
                AND (PrixVenteTotal IS NULL OR PrixVenteTotal = 0)
            """)
            count_to_update = cursor.fetchone().count
            print(f"📊 {count_to_update} dossiers à mettre à jour (PrixVenteTotal NULL ou 0)")
            print()
            
            # Afficher tous les dossiers avec leurs valeurs
            cursor.execute("""
                SELECT ID, Numero_COMMANDES, PrixVenteUnitaire, QteComm_COMMANDES, PrixVenteTotal
                FROM WEB_S_DOS_ENCOURS
                ORDER BY ID
            """)
            all_dossiers = cursor.fetchall()
            print(f"📋 État de tous les dossiers ({len(all_dossiers)} au total):")
            for d in all_dossiers:
                status = "✅" if d.PrixVenteTotal is not None and d.PrixVenteTotal != 0 else "⚠️ NULL"
                print(f"   {status} Dossier {d.Numero_COMMANDES}: PrixUnitaire={d.PrixVenteUnitaire}, Qte={d.QteComm_COMMANDES}, PrixTotal={d.PrixVenteTotal}")
            print()
            
            if count_to_update == 0:
                print("✅ Tous les dossiers ont déjà PrixVenteTotal calculé")
                return True
            
            # Mettre à jour PrixVenteTotal = PrixVenteUnitaire * QteComm_COMMANDES
            print("🔄 Mise à jour en cours...")
            cursor.execute("""
                UPDATE WEB_S_DOS_ENCOURS
                SET PrixVenteTotal = ROUND(PrixVenteUnitaire * QteComm_COMMANDES, 3)
                WHERE PrixVenteUnitaire IS NOT NULL
                AND QteComm_COMMANDES IS NOT NULL
                AND (PrixVenteTotal IS NULL OR PrixVenteTotal = 0)
            """)
            updated_count = cursor.rowcount
            cursor.connection.commit()
            
            print(f"✅ {updated_count} dossiers mis à jour avec succès!")
            print()
            
            # Vérifier après mise à jour
            cursor.execute("""
                SELECT ID, Numero_COMMANDES, PrixVenteUnitaire, QteComm_COMMANDES, PrixVenteTotal
                FROM WEB_S_DOS_ENCOURS
                ORDER BY ID
            """)
            all_dossiers_after = cursor.fetchall()
            print(f"📋 État après mise à jour:")
            for d in all_dossiers_after:
                status = "✅" if d.PrixVenteTotal is not None and d.PrixVenteTotal != 0 else "❌ NULL"
                print(f"   {status} Dossier {d.Numero_COMMANDES}: PrixUnitaire={d.PrixVenteUnitaire}, Qte={d.QteComm_COMMANDES}, PrixTotal={d.PrixVenteTotal}")
            print()
            
            # Afficher quelques exemples
            cursor.execute("""
                SELECT TOP 5
                    ID,
                    Numero_COMMANDES,
                    PrixVenteUnitaire,
                    QteComm_COMMANDES,
                    PrixVenteTotal
                FROM WEB_S_DOS_ENCOURS
                WHERE PrixVenteTotal IS NOT NULL
                ORDER BY ID DESC
            """)
            
            print("📋 Exemples de dossiers mis à jour :")
            for row in cursor.fetchall():
                print(f"   - Dossier {row.Numero_COMMANDES}: {row.PrixVenteUnitaire} × {row.QteComm_COMMANDES} = {row.PrixVenteTotal}")
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
    update_existing_prix_vente_total()
