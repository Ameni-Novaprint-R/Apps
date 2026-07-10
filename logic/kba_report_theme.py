#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Palette Performance Report Koenig & Bauer — couleurs intenses du rapport de référence.
Utilisée par le PDF et la page web Projet 11.
"""

# Couleurs hex — extraites du PDF Report_383454_2026_06.pdf (zones saturées)
KBA_COLORS = {
    "navy": "#002054",
    "navy_mid": "#1C3868",
    "blue_steel": "#3C587C",
    "blue_mid": "#546C8C",
    "blue_light": "#7C90A8",
    "blue_pale": "#8494AC",
    "red": "#F02C30",
    "red_dark": "#C00000",
    "salmon_brut": "#F47074",
    "grey_standby": "#6E6E6E",
    "grey_brut": "#8494AC",
    "grey_light": "#BDBDBD",
    "text": "#002054",
    "text_muted": "#3C587C",
    "white": "#FFFFFF",
    "bg_page": "#FFFFFF",
    "border_red": "#F02C30",
    "line_red": "#F02C30",
}

# Camemberts (référence screenshot KBA)
PIE_DISPO = ["navy", "red", "grey_standby"]          # production, arrêt, veille
PIE_TEMPS = ["navy", "blue_steel", "blue_light"]     # impression, lavage, chgmt plaques
PIE_VITESSE = ["blue_pale", "blue_light", "blue_steel", "navy"]

# Barres productivité : net = marine, brut (surplus) = gris clair (réf. KBA)
BAR_NET = "navy"
BAR_BRUT = "grey_light"
BAR_PERF_MOY = "navy"
BAR_PERF_MAX = "blue_steel"
BAR_TIRAGE = "navy_mid"
