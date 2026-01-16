"""
Logique pour le Projet 18 - Agenda semainier 2026
"""
from datetime import datetime, timedelta
from calendar import monthrange

# Jours fériés en Tunisie pour 2026
JOURS_FERIES_TUNISIE_2026 = [
    # Jours fériés fixes
    datetime(2026, 1, 1),    # Jour de l'An
    datetime(2026, 3, 20),   # Fête de l'Indépendance
    datetime(2026, 4, 9),    # Journée des Martyrs
    datetime(2026, 5, 1),    # Fête du Travail
    datetime(2026, 7, 25),   # Fête de la République
    datetime(2026, 8, 13),   # Fête de la Femme
    datetime(2026, 10, 15),  # Fête de l'Évacuation
    datetime(2026, 12, 17),  # Fête de la Révolution
    
    # Jours fériés religieux (prévisionnels)
    # Aïd al-Fitr (2 jours)
    datetime(2026, 3, 21),   # Aïd al-Fitr jour 1
    datetime(2026, 3, 22),   # Aïd al-Fitr jour 2
    # Aïd al-Adha (2 jours)
    datetime(2026, 5, 26),   # Aïd al-Adha jour 1
    datetime(2026, 5, 27),   # Aïd al-Adha jour 2
    # Nouvel An hégirien (1 jour)
    datetime(2026, 6, 15),   # Nouvel An hégirien
    # Mouled (1 jour)
    datetime(2026, 8, 24),   # Mouled (Anniversaire du Prophète)
]

def is_jour_ferie(date):
    """Vérifie si une date est un jour férié en Tunisie"""
    if date is None:
        return False
    return date.date() in [jf.date() for jf in JOURS_FERIES_TUNISIE_2026]

def get_nom_jour_ferie(date):
    """Retourne le nom du jour férié si applicable"""
    if date is None:
        return ""
    jours_feries_noms = {
        # Jours fériés fixes
        datetime(2026, 1, 1).date(): "Jour de l'An",
        datetime(2026, 3, 20).date(): "Fête de l'Indépendance",
        datetime(2026, 4, 9).date(): "Journée des Martyrs",
        datetime(2026, 5, 1).date(): "Fête du Travail",
        datetime(2026, 7, 25).date(): "Fête de la République",
        datetime(2026, 8, 13).date(): "Fête de la Femme",
        datetime(2026, 10, 15).date(): "Fête de l'Évacuation",
        datetime(2026, 12, 17).date(): "Fête de la Révolution",
        # Jours fériés religieux
        datetime(2026, 3, 21).date(): "Aïd al-Fitr",
        datetime(2026, 3, 22).date(): "Aïd al-Fitr",
        datetime(2026, 5, 26).date(): "Aïd al-Adha",
        datetime(2026, 5, 27).date(): "Aïd al-Adha",
        datetime(2026, 6, 15).date(): "Nouvel An hégirien",
        datetime(2026, 8, 24).date(): "Mouled",
    }
    return jours_feries_noms.get(date.date(), "")

def get_semaines_2026():
    """
    Génère les semaines 1 à 52 de 2026
    Chaque semaine commence le lundi et se termine le dimanche
    Format standard : Lundi à Dimanche
    La première semaine commence par Lundi 29 décembre 2025
    """
    semaines = []
    
    # Début de l'année 2026
    date_debut_annee = datetime(2026, 1, 1)  # Jeudi 1er janvier 2026
    
    # Trouver le lundi de la semaine contenant le 1er janvier
    # Le 1er janvier 2026 est un jeudi (3), donc on recule de 3 jours pour avoir le lundi
    premier_lundi = date_debut_annee - timedelta(days=3)  # 29 décembre 2025
    
    # Générer 52 semaines à partir du lundi 29 décembre 2025
    date_courante = premier_lundi
    
    for semaine_numero in range(1, 53):
        lundi = date_courante
        mardi = date_courante + timedelta(days=1)
        mercredi = date_courante + timedelta(days=2)
        jeudi = date_courante + timedelta(days=3)
        vendredi = date_courante + timedelta(days=4)
        samedi = date_courante + timedelta(days=5)
        dimanche = date_courante + timedelta(days=6)
        
        # Garder tous les jours (y compris ceux de décembre 2025 pour la première semaine)
        semaine = {
            'numero': semaine_numero,
            'lundi': lundi,
            'mardi': mardi,
            'mercredi': mercredi,
            'jeudi': jeudi,
            'vendredi': vendredi,
            'samedi': samedi,
            'dimanche': dimanche,
        }
        semaines.append(semaine)
        
        date_courante += timedelta(days=7)
        
        # Arrêter si on dépasse 2026
        if date_courante.year > 2026:
            break
    
    return semaines

def get_mois_nom(mois_numero):
    """Retourne le nom du mois en français"""
    mois = {
        1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
        5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
        9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
    }
    return mois.get(mois_numero, "")











