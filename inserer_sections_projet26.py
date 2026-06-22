# -*- coding: utf-8 -*-
"""Insère les sections du Projet 26 dans WEB_SECTIONS."""
from db import get_db_cursor
from logic.projet26 import ensure_projet26_in_web_projets

SECTIONS = [
    'Demande de formation',
    'Évaluation de formation',
    'Liste des formations',
]


def main():
    ensure_projet26_in_web_projets()
    with get_db_cursor() as cursor:
        cursor.execute('SELECT ID FROM WEB_PROJETS WHERE NumProj = 26')
        row = cursor.fetchone()
        if not row:
            print('Projet 26 introuvable dans WEB_PROJETS')
            return
        pid = row.ID
        for nom in SECTIONS:
            cursor.execute(
                'SELECT 1 FROM WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?',
                (pid, nom),
            )
            if not cursor.fetchone():
                cursor.execute(
                    'INSERT INTO WEB_SECTIONS (ID_Proj, Nom, archive) VALUES (?, ?, 0)',
                    (pid, nom),
                )
                print(f'  + {nom}')
            else:
                print(f'  (existe) {nom}')
        cursor.connection.commit()
        cursor.execute('SELECT ID, Nom FROM WEB_SECTIONS WHERE ID_Proj = ? ORDER BY ID', (pid,))
        for r in cursor.fetchall():
            print(f'    {r.ID}: {r.Nom}')


if __name__ == '__main__':
    main()
