#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script rapide pour vérifier le nombre de dossiers insérés"""
from db import get_db_cursor

with get_db_cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM WEB_S_DOS_ENCOURS")
    total = cursor.fetchone()[0]
    print(f"Total de dossiers dans WEB_S_DOS_ENCOURS: {total}")
