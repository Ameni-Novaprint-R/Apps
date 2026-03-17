#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Insère le Projet 24 – Formes de Découpe dans WEB_PROJETS si absent.
À exécuter une fois sur l'environnement 192.168.10.225 pour que le projet
apparaisse dans le menu (pour les super-utilisateurs ; pour les autres utilisateurs,
ajouter une section + actions + droits via l'admin ou les scripts de droits).
"""
from db import get_db_cursor

NUM_PROJ = 24
CODE_PROJ = 'Projet 24'
NOM = 'Formes de Découpe'
ARCHIVE = 0


def main():
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT ID, NumProj, Nom FROM dbo.WEB_PROJETS WHERE NumProj = ?",
                (NUM_PROJ,)
            )
            row = cursor.fetchone()
            if row:
                print(f"[OK] Le projet 24 existe déjà (ID={row.ID}, Nom={row.Nom}).")
                return True
            cursor.execute("""
                INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive)
                VALUES (?, ?, ?, ?)
            """, (NUM_PROJ, CODE_PROJ, NOM, ARCHIVE))
            cursor.connection.commit()
            print(f"[OK] Projet 24 inséré : {CODE_PROJ} – {NOM}.")
            return True
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    main()
