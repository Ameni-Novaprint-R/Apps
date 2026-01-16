"""Test du projet 18"""
from logic.projet18 import get_semaines_2026, is_jour_ferie, get_nom_jour_ferie

semaines = get_semaines_2026()
print(f"Nombre de semaines: {len(semaines)}")
print(f"Première semaine - Lundi: {semaines[0]['lundi']}")
print(f"Dernière semaine - Dimanche: {semaines[-1]['dimanche']}")

# Tester quelques jours fériés
test_dates = [
    (2026, 1, 1),
    (2026, 1, 14),
    (2026, 3, 20),
    (2026, 5, 1),
]
print("\nTest des jours fériés:")
for year, month, day in test_dates:
    from datetime import datetime
    date = datetime(year, month, day)
    ferie = is_jour_ferie(date)
    nom = get_nom_jour_ferie(date) if ferie else ""
    print(f"{date.strftime('%d/%m/%Y')}: {'FERIÉ - ' + nom if ferie else 'Jour normal'}")











