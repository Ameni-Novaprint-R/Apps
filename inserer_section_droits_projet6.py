# -*- coding: utf-8 -*-
"""Insère les sections du Projet 6 et les droits d'accès pour le matricule 145."""
from db import get_db_cursor

SECTIONS = [
    'Nouveau voyage',
    'Liste des voyages',
    'Gestion des véhicules',
]
ACTION_NOM = 'Accès'
MATRICULES = [145]


def ensure_section_action_droits(cursor, pid, code_proj, section_nom):
    cursor.execute(
        'SELECT ID FROM WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?',
        (pid, section_nom),
    )
    sec = cursor.fetchone()
    if not sec:
        cursor.execute(
            'INSERT INTO WEB_SECTIONS (ID_Proj, Nom, archive) VALUES (?, ?, 0)',
            (pid, section_nom),
        )
        cursor.execute(
            'SELECT ID FROM WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?',
            (pid, section_nom),
        )
        sec = cursor.fetchone()
        print(f'  + Section "{section_nom}" (ID={sec.ID})')
    else:
        print(f'  (existe) Section "{section_nom}" (ID={sec.ID})')
    id_section = sec.ID

    cursor.execute(
        'SELECT ID FROM WEB_ACTIONS WHERE ID_Section = ? AND Action = ?',
        (id_section, ACTION_NOM),
    )
    act = cursor.fetchone()
    if not act:
        cursor.execute(
            '''INSERT INTO WEB_ACTIONS (ID_Section, Action, archive, CodeProj, Nom_SECTIONS)
               VALUES (?, ?, 0, ?, ?)''',
            (id_section, ACTION_NOM, code_proj, section_nom),
        )
        cursor.execute(
            'SELECT ID FROM WEB_ACTIONS WHERE ID_Section = ? AND Action = ?',
            (id_section, ACTION_NOM),
        )
        act = cursor.fetchone()
        print(f'  + Action "{ACTION_NOM}" (ID={act.ID})')
    else:
        print(f'  (existe) Action "{ACTION_NOM}" (ID={act.ID})')
    id_action = act.ID

    for mat in MATRICULES:
        cursor.execute(
            'SELECT ID, Autorise FROM WEB_DROITS_ACCES WHERE Matricule = ? AND ID_Action = ?',
            (mat, id_action),
        )
        droit = cursor.fetchone()
        if not droit:
            cursor.execute(
                'INSERT INTO WEB_DROITS_ACCES (Matricule, ID_Action, Autorise) VALUES (?, ?, 1)',
                (mat, id_action),
            )
            print(f'  + Droit Matricule={mat} -> Action {id_action}')
        else:
            if not droit.Autorise:
                cursor.execute(
                    'UPDATE WEB_DROITS_ACCES SET Autorise = 1 WHERE ID = ?',
                    (droit.ID,),
                )
                print(f'  ~ Droit Matricule={mat} reactive (ID={droit.ID})')
            else:
                print(f'  (existe) Droit Matricule={mat} (ID={droit.ID})')


def main():
    with get_db_cursor() as cursor:
        cursor.execute('SELECT ID, CodeProj FROM WEB_PROJETS WHERE NumProj = 6')
        row = cursor.fetchone()
        if not row:
            print('Projet 6 introuvable dans WEB_PROJETS')
            return
        pid = row.ID
        code_proj = row.CodeProj or 'Projet 6'
        print(f'Projet 6 ID={pid} CodeProj={code_proj}')

        cursor.execute(
            "UPDATE WEB_PROJETS SET Nom = ? WHERE NumProj = 6",
            ('Transport & Logistique',),
        )
        print('  ~ Nom projet 6 -> Transport & Logistique')

        for nom in SECTIONS:
            ensure_section_action_droits(cursor, pid, code_proj, nom)

        cursor.connection.commit()

        print('\n--- Verification matricule 145 (projet 6) ---')
        cursor.execute('''
            SELECT WP.NumProj, WS.Nom AS Section, WA.Action, WDA.Autorise
            FROM WEB_DROITS_ACCES WDA
            JOIN WEB_ACTIONS WA ON WA.ID = WDA.ID_Action
            JOIN WEB_SECTIONS WS ON WS.ID = WA.ID_Section
            JOIN WEB_PROJETS WP ON WP.ID = WS.ID_Proj
            WHERE WDA.Matricule = 145 AND WP.NumProj = 6
            ORDER BY WS.Nom
        ''')
        for r in cursor.fetchall():
            print(f'  Projet {r.NumProj} | {r.Section} | {r.Action} | Autorise={r.Autorise}')


if __name__ == '__main__':
    main()
