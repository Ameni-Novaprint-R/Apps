"""
Catégories métier de la page d'accueil du portail Novaprint.

Pour changer une icône de catégorie, modifier CATEGORY_DEFINITIONS ci-dessous.
"""

from logic.project_routes import get_project_icon, get_project_url

# NumProj -> slug de catégorie (Projet 13 archivé exclu)
PROJECT_TO_CATEGORY = {
    1: 'production-exploitation',
    2: 'production-exploitation',
    3: 'commercial',
    4: 'commercial',
    5: 'production-exploitation',
    6: 'commercial',
    7: 'finance-pilotage',
    8: 'commercial',
    9: 'commercial',
    10: 'qualite',
    11: 'production-exploitation',
    12: 'qualite',
    14: 'qualite',
    15: 'qualite',
    16: 'gmao',
    17: 'systemes-support',
    18: 'commercial',
    19: 'finance-pilotage',
    20: 'commercial',
    21: 'systemes-support',
    22: 'rh-organisation',
    23: 'finance-pilotage',
    24: 'production-exploitation',
    25: 'rh-organisation',
    26: 'rh-organisation',
    27: 'finance-pilotage',
    28: 'production-exploitation',
    29: 'systemes-support',
}

CATEGORY_DEFINITIONS = [
    {
        'slug': 'production-exploitation',
        'name': 'Production & Exploitation',
        'icon': '🏭',
        'description': 'Planning, traitements, formes de découpe et suivi opérationnel.',
    },
    {
        'slug': 'gmao',
        'name': 'GMAO',
        'icon': '🛠️',
        'description': 'Gestion de la maintenance et des équipements.',
    },
    {
        'slug': 'qualite',
        'name': 'Qualité',
        'icon': '🔬',
        'description': 'Contrôle qualité, non-conformités et suivi environnemental.',
    },
    {
        'slug': 'commercial',
        'name': 'Commercial',
        'icon': '🤝',
        'description': 'Commandes, clients, BAT, performance et analyse commerciale.',
    },
    {
        'slug': 'finance-pilotage',
        'name': 'Finance & Pilotage',
        'icon': '📈',
        'description': 'Trésorerie, facturation, dossiers et pilotage financier.',
    },
    {
        'slug': 'rh-organisation',
        'name': 'RH & Organisation interne',
        'icon': '👥',
        'description': 'Employés, ateliers, congés et formations.',
    },
    {
        'slug': 'systemes-support',
        'name': 'Systèmes & Support digital',
        'icon': '💻',
        'description': 'Outils digitaux, bases de données et support technique.',
    },
]

CATEGORY_BY_SLUG = {c['slug']: c for c in CATEGORY_DEFINITIONS}


def normalize_project_display_name(num, nom):
    """Libellés affichés sur l'accueil (alignés avec le menu navigation)."""
    overrides = {
        23: 'Tableau de bord de la situation de la trésorerie',
        24: 'Formes de Découpe',
        25: 'Gestion des congés et autorisations de sortie',
        26: 'Gestion des formations',
        27: 'Crédit Leasing',
        28: 'Gestion des codes-barres MP',
        29: 'Suivi des connexions',
        4: 'Rapport de Visite',
    }
    return overrides.get(num, nom or '')


def enrich_project(project):
    """Ajoute url, icône et libellé à un projet utilisateur."""
    num = project.get('num') or project.get('NumProj')
    nom = normalize_project_display_name(num, project.get('nom') or project.get('Nom', ''))
    url = get_project_url(num) if num else None
    return {
        **project,
        'num': num,
        'nom': nom,
        'code': project.get('code') or project.get('CodeProj') or (f'Projet {num}' if num else ''),
        'url': url or (f'/projet{num}/' if num else '#'),
        'icon': get_project_icon(num) if num else '📌',
        'category_slug': PROJECT_TO_CATEGORY.get(num),
    }


def group_projects_by_category(user_projects, hide_empty=True):
    """
    Regroupe les projets accessibles par catégorie métier.
    hide_empty=True : ne retourne que les catégories contenant au moins un projet.
    """
    buckets = {c['slug']: [] for c in CATEGORY_DEFINITIONS}
    uncategorized = []

    for raw in user_projects or []:
        project = enrich_project(raw)
        slug = project.get('category_slug')
        if slug and slug in buckets:
            buckets[slug].append(project)
        elif slug is None:
            uncategorized.append(project)

    categories = []
    for definition in CATEGORY_DEFINITIONS:
        projects = sorted(buckets[definition['slug']], key=lambda p: p.get('num') or 0)
        if hide_empty and not projects:
            continue
        categories.append({
            **definition,
            'projects': projects,
            'count': len(projects),
        })

    return categories, uncategorized


def get_category_page(slug, user_projects):
    """Retourne une catégorie et ses projets, ou None si slug inconnu ou vide."""
    if slug not in CATEGORY_BY_SLUG:
        return None
    categories, _ = group_projects_by_category(user_projects, hide_empty=True)
    for category in categories:
        if category['slug'] == slug:
            return category
    return None
