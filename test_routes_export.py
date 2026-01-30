#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test si les routes d'export sont bien enregistrées dans Flask"""

from app import app
from flask import url_for

with app.app_context():
    print("=" * 70)
    print("Test des routes d'export")
    print("=" * 70)
    try:
        excel_url = url_for('projet11.export_statistiques_excel')
        pdf_url = url_for('projet11.export_statistiques_pdf')
        print(f"✓ Route Excel: {excel_url}")
        print(f"✓ Route PDF: {pdf_url}")
        print("\nSUCCES: Les routes sont bien enregistrees dans Flask!")
    except Exception as e:
        print(f"\nERREUR: {e}")
        print("\nLes routes ne sont pas encore enregistrees.")
        print("Flask doit etre redemarre pour charger les nouvelles routes.")
