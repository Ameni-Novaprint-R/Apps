"""
Mapping des projets vers leurs routes Flask
"""
from flask import url_for

# Mapping des numéros de projets vers leurs routes Flask
PROJECT_ROUTES = {
    1: ('projet1.index', 'Planning'),
    2: ('projet2.commandes', 'Commandes'),
    3: ('projet3.page_projet3', 'Suivi BAT'),
    4: ('projet4.rapport_visite', 'Rapport de Visite'),
    5: ('projet5.index', 'Planning Production'),
    6: ('projet6.programme_voyage', 'Voyages'),
    7: ('projet7_bp.import_facture', 'Factures STEG'),
    8: ('projet8.stats_devis_commandes', 'Stats'),
    9: ('projet9.index', 'Performance'),
    10: ('projet10.index', 'Qualité'),
    11: ('projet11.index', 'Traitements'),
    12: ('projet12.projet12', 'NC & Réclamations'),
    13: ('projet13.index', 'Suivi Production'),
    14: ('projet14.index', 'Déchets'),
    15: ('projet15.index', 'Corrélation'),
    16: ('projet16.index', 'GMAO'),
    17: ('projet17.index', 'Fusion HTML'),
    18: ('projet18.index', 'Agenda 2026'),
    19: ('projet19.index', 'Dossiers en Cours'),
    20: ('/projet20/', 'Analyse Dossiers'),
    21: ('/projet21/', 'Sync BDD'),
    22: ('projet22.index', 'Employés et Ateliers'),
    23: ('projet23.index', 'Trésorerie'),
    24: ('projet24.index', 'Formes de Découpe'),
    25: ('projet25.index', 'Congés et autorisations'),
    26: ('projet26.index', 'Gestion des formations'),
    27: ('projet27.index', 'Crédit Leasing'),
    28: ('projet28.index', 'Gestion des codes-barres MP'),
    29: ('/projet29/', 'Suivi des connexions'),
}

# Mapping des numéros de projets vers leurs icônes
PROJECT_ICONS = {
    1: '📋',
    2: '📦',
    3: '🖨️',
    4: '📝',
    5: '📝',
    6: '🚚',
    7: '💡',
    8: '📊',
    9: '📈',
    10: '🔍',
    11: '🔧',
    12: '📋',
    13: '🏭',
    14: '♻️',
    15: '📊',
    16: '🔧',
    17: '📚',
    18: '📅',
    19: '📁',
    20: '🔍',
    21: '🔄',
    22: '👥',
    23: '💰',
    24: '📐',
    25: '📅',
    26: '🎓',
    27: '💳',
    28: '🏷️',
    29: '🟢',
}

def get_project_url(project_num):
    """
    Retourne l'URL d'un projet selon son numéro
    """
    try:
        if project_num in PROJECT_ROUTES:
            route = PROJECT_ROUTES[project_num][0]
            if route.startswith('/'):
                return route
            try:
                return url_for(route)
            except Exception:
                return route
        return None
    except Exception:
        return None

def get_project_name(project_num):
    """
    Retourne le nom d'un projet selon son numéro
    """
    try:
        if project_num in PROJECT_ROUTES:
            return PROJECT_ROUTES[project_num][1]
        return None
    except Exception:
        return None

def get_project_icon(project_num):
    """
    Retourne l'icône d'un projet selon son numéro
    """
    try:
        return PROJECT_ICONS.get(project_num, '📌')
    except Exception:
        return '📌'
