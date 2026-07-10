# -*- coding: utf-8 -*-
"""
Projet 28 – Rapport de Visite Client (migration depuis Prinects Projet 4).
"""
from db import get_db_cursor

NUM_PROJ = 28

PROJET28_SECTIONS = [
    'Nouveau rapport',
    'Historique des visites',
    'Tableau de bord',
]

PROJET28_SECTION_KEYS = {
    'Nouveau rapport': 'nouveau',
    'Historique des visites': 'historique',
    'Tableau de bord': 'dashboard',
}


def ensure_projet28_in_web_projets():
    try:
        with get_db_cursor() as cursor:
            cursor.execute('SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = ?', (NUM_PROJ,))
            if cursor.fetchone():
                return
            cursor.execute("""
                INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive)
                VALUES (?, N'Projet 28', N'Rapport de Visite', 0)
            """, (NUM_PROJ,))
            cursor.connection.commit()
            print('[Projet 28] WEB_PROJETS ajouté.')
    except Exception as e:
        print(f'[Projet 28] ensure_projet28_in_web_projets: {e}')


def ensure_projet28_sections():
    try:
        with get_db_cursor() as cursor:
            cursor.execute('SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = ?', (NUM_PROJ,))
            row = cursor.fetchone()
            if not row:
                return
            id_proj = row[0]
            for nom in PROJET28_SECTIONS:
                cursor.execute(
                    'SELECT 1 FROM WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?',
                    (id_proj, nom),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        'INSERT INTO WEB_SECTIONS (ID_Proj, Nom, archive) VALUES (?, ?, 0)',
                        (id_proj, nom),
                    )
            cursor.connection.commit()
    except Exception as e:
        print(f'[Projet 28] ensure_projet28_sections: {e}')


def init_projet28():
    ensure_projet28_in_web_projets()
    ensure_projet28_sections()
