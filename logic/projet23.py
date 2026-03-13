# -*- coding: utf-8 -*-
"""
Projet 23 - Situation de la Trésorerie
Extraction et analyse des PDFs XRT (solde trésorerie, lignes de financement).
Accepte chemin fichier ou flux (BytesIO) pour l'upload.
"""
import io
import json
import re
from pathlib import Path
from typing import Optional, Union

def _parse_num_fr(s: str) -> Optional[float]:
    """Parse un nombre français (espaces comme séparateur de milliers, virgule décimale)."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip().replace(' ', '').replace('\xa0', '')
    s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


def extraire_solde_tresorerie(pdf_source: Union[str, io.BytesIO], filename: Optional[str] = None) -> dict:
    """
    Extrait les données de solde de trésorerie d'un PDF XRT.
    pdf_source: chemin (str) ou flux BytesIO.
    filename: nom du fichier (pour affichage source), utilisé si pdf_source est un flux.
    Retourne: { success, dates, soldes, source, texte_lecture, texte_interpretation, texte_conclusion, error }
    """
    import pdfplumber
    result = {
        'success': False,
        'dates': [],
        'soldes': [],
        'source': '',
        'texte_lecture': '',
        'texte_interpretation': '',
        'texte_conclusion': '',
        'error': None
    }
    try:
        if isinstance(pdf_source, str):
            path = Path(pdf_source)
            if not path.exists():
                result['error'] = f'Fichier non trouvé: {pdf_source}'
                return result
            source_name = path.name
            pdf_obj = path
        else:
            source_name = filename or 'Document PDF'
            pdf_obj = pdf_source

        with pdfplumber.open(pdf_obj) as pdf:
            if not pdf.pages:
                result['error'] = 'PDF vide'
                return result

            text = ''
            for page in pdf.pages:
                text += (page.extract_text() or '') + '\n'

        # Extraire la source (nom du fichier ou titre du document)
        result['source'] = f'« {source_name} »' if source_name else 'Document PDF'

        # Extraire les dates depuis la LIGNE D'AXE du graphique uniquement (ordre chronologique)
        # La ligne d'axe contient une série de dates: "25/02/2026 26/02/2026 ... 05/03/2026"
        # On évite les dates du filtre (Date Début egal "25/02/2026" et Date Fin egal "05/03/2026")
        date_pattern = r'\d{2}/\d{2}/\d{4}'
        dates = []
        for line in text.splitlines():
            line_dates = re.findall(date_pattern, line)
            # La ligne d'axe du graphique contient typiquement 5 à 15 dates consécutives
            if len(line_dates) >= 5 and 'Date Début' not in line and 'Date Fin' not in line and 'egal' not in line.lower():
                dates = line_dates
                break

        # Fallback: extraire toutes les dates, exclure les lignes de filtre, trier chronologiquement
        if not dates:
            lines_with_dates = [line for line in text.splitlines() if re.search(date_pattern, line)]
            for line in lines_with_dates:
                if 'Filtre' in line or 'egal' in line or 'Date Début' in line or 'Date Fin' in line or 'Created by' in line:
                    continue
                line_dates = re.findall(date_pattern, line)
                if len(line_dates) >= 3:
                    dates = line_dates
                    break
        if not dates:
            all_dates = re.findall(date_pattern, text)
            def _sort_key(d):
                p = d.split('/')
                return (int(p[2]), int(p[1]), int(p[0]))
            dates = sorted(set(all_dates), key=_sort_key)

        # Extraire les soldes (nombres négatifs avec format -XXX XXX,XX ou -XXXXXX,XX)
        solde_pattern = r'-\s*[\d\s]+,\d{2}'
        soldes_str = re.findall(solde_pattern, text)
        soldes = []
        for s in soldes_str:
            v = _parse_num_fr(s.strip())
            if v is not None:
                soldes.append(v)

        # Exclure les valeurs d'échelle d'axe (arrondies à 50000 ou 100000)
        soldes_filtres = [
            x for x in soldes
            if abs(x) >= 1000 and (abs(x) % 1000 != 0 or abs(x) > 1e6)
        ]
        if not soldes_filtres:
            soldes_filtres = [x for x in soldes if abs(x) >= 1000]

        # Ordre chronologique: s'assurer qu'on a une paire (date, solde) par point
        if len(dates) >= len(soldes_filtres):
            dates = dates[:len(soldes_filtres)]
        else:
            soldes_filtres = soldes_filtres[:len(dates)]

        result['dates'] = dates
        result['soldes'] = soldes_filtres

        if not dates or not soldes_filtres:
            result['error'] = 'Impossible d\'extraire les dates et soldes du PDF'
            return result

        # Générer les textes explicatifs
        solde_min = min(soldes_filtres)
        solde_max = max(soldes_filtres)
        idx_min = soldes_filtres.index(solde_min)
        date_min = dates[idx_min] if idx_min < len(dates) else dates[-1]

        def fmt_k(x):
            return f'{int(round(x/1000))} K'

        result['texte_lecture'] = (
            f'La trésorerie est {"négative" if solde_max < 0 else "positive"} sur toute la période, '
            f'entre environ **{fmt_k(solde_max)} TND** et **{fmt_k(solde_min)} TND**.'
        )
        result['texte_interpretation'] = (
            'On observe une **détérioration progressive** du solde, ce qui traduit soit des décaissements '
            'supérieurs aux encaissements, soit un décalage entre flux bancaires et flux comptables.'
            if solde_min < solde_max else
            'Le solde reste stable ou s\'améliore sur la période.'
        )
        result['texte_conclusion'] = (
            f'Le point le plus bas est atteint autour du **{date_min}** (environ {fmt_k(solde_min)} TND), '
            'ce qui peut constituer un **niveau d\'alerte à suivre** dans les prochains jours.'
            if solde_min < 0 else
            'La trésorerie est globalement saine sur la période analysée.'
        )
        result['success'] = True

    except Exception as e:
        result['error'] = str(e)
        import traceback
        traceback.print_exc()

    return result


def extraire_lignes_financement(pdf_source: Union[str, io.BytesIO], filename: Optional[str] = None) -> dict:
    """
    Extrait les données d'utilisation des lignes de financement d'un PDF XRT.
    pdf_source: chemin (str) ou flux BytesIO.
    filename: nom du fichier (pour affichage source), utilisé si pdf_source est un flux.
    Retourne: { success, autorisation, utilisation, disponible, source, texte_lecture, ... }
    """
    import pdfplumber
    result = {
        'success': False,
        'autorisation': 0,
        'utilisation': 0,
        'disponible': 0,
        'source': '',
        'texte_lecture': '',
        'texte_interpretation': '',
        'texte_conclusion': '',
        'error': None
    }
    try:
        if isinstance(pdf_source, str):
            path = Path(pdf_source)
            if not path.exists():
                result['error'] = f'Fichier non trouvé: {pdf_source}'
                return result
            source_name = path.name
            pdf_obj = path
        else:
            source_name = filename or 'Document PDF'
            pdf_obj = pdf_source

        with pdfplumber.open(pdf_obj) as pdf:
            if not pdf.pages:
                result['error'] = 'PDF vide'
                return result

            text = ''
            for page in pdf.pages:
                text += (page.extract_text() or '') + '\n'

        result['source'] = f'« {source_name} »' if source_name else 'Document PDF'

        # Chercher la ligne "Financement" suivie de 3 montants
        # Ex: "Financement 5 300 000,00 3 892 321,46 1 407 678,54"
        m = re.search(
            r'Financement\s+([\d\s]+,\d{2})\s+([\d\s]+,\d{2})\s+([\d\s]+,\d{2})',
            text,
            re.IGNORECASE
        )
        if m:
            result['autorisation'] = _parse_num_fr(m.group(1)) or 0
            result['utilisation'] = _parse_num_fr(m.group(2)) or 0
            result['disponible'] = _parse_num_fr(m.group(3)) or 0
        else:
            # Fallback: chercher des montants avec "Autorisation" "Utilisation" "Disponible"
            # Ou pattern plus générique
            nums = re.findall(r'[\d\s]{3,},\d{2}', text.replace('\xa0', ' '))
            # Filtrer les nombres plausibles (montants en millions ou centaines de milliers)
            vals = []
            for n in nums:
                v = _parse_num_fr(n)
                if v and v > 1000:
                    vals.append(v)
            if len(vals) >= 3:
                result['autorisation'] = max(vals)
                result['utilisation'] = sorted(vals)[-2]
                result['disponible'] = result['autorisation'] - result['utilisation']
            else:
                result['error'] = 'Impossible d\'extraire autorisation, utilisation et disponible'
                return result

        if result['autorisation'] <= 0:
            result['error'] = 'Autorisation non trouvée ou invalide'
            return result

        taux = (result['utilisation'] / result['autorisation'] * 100) if result['autorisation'] else 0

        def fmt_m(x):
            return f'{x/1e6:.2f} M'.replace('.', ',')

        result['texte_lecture'] = (
            f'Autorisation globale des lignes : **{fmt_m(result["autorisation"])} TND**.\n'
            f'Utilisation : **{fmt_m(result["utilisation"])} TND**, soit un taux d\'emploi d\'environ **{int(round(taux))} %**.\n'
            f'Marge de manœuvre disponible : **{fmt_m(result["disponible"])} TND** pour couvrir les besoins de trésorerie ou financer de nouveaux besoins à court terme.'
        )
        result['texte_interpretation'] = ''
        result['texte_conclusion'] = (
            'Avec une trésorerie potentiellement négative, cette marge doit être **surveillée régulièrement** '
            'pour éviter un dépassement des autorisations.'
        )
        result['success'] = True

    except Exception as e:
        result['error'] = str(e)
        import traceback
        traceback.print_exc()

    return result


def lister_pdfs_solde_tresorerie() -> list:
    """Liste les PDFs dans le dossier solde_tresorerie."""
    base = Path(r'x:\projet23\donnees_a_analyser\solde_tresorerie')
    if not base.exists():
        return []
    return [str(f) for f in base.glob('*.pdf')]


def lister_pdfs_lignes_financement() -> list:
    """Liste les PDFs dans le dossier lignes_financement."""
    base = Path(r'x:\projet23\donnees_a_analyser\lignes_financement')
    if not base.exists():
        return []
    return [str(f) for f in base.glob('*.pdf')]


def save_synthese(solde_data: dict, lignes_data: dict, enregistre_par: str = None) -> bool:
    """
    Enregistre la synthèse trésorerie (remplace la précédente).
    solde_data: { dates, soldes, source, texte_lecture, texte_interpretation, texte_conclusion }
    lignes_data: { autorisation, utilisation, disponible, source, texte_lecture, texte_conclusion }
    """
    from db import get_db_cursor
    try:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM WEB_PROJET23_SYNTHESE")
            cursor.execute(
                """INSERT INTO WEB_PROJET23_SYNTHESE (SoldeData, LignesData, EnregistrePar)
                   VALUES (?, ?, ?)""",
                (json.dumps(solde_data, ensure_ascii=False),
                 json.dumps(lignes_data, ensure_ascii=False),
                 enregistre_par or '')
            )
            cursor.connection.commit()
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False


def get_latest_synthese() -> dict:
    """
    Récupère la dernière synthèse enregistrée.
    Retourne { solde: {...}, lignes: {...} } ou { solde: None, lignes: None } si vide.
    """
    from db import get_db_cursor
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """SELECT TOP 1 SoldeData, LignesData FROM WEB_PROJET23_SYNTHESE
                   ORDER BY DateMaj DESC"""
            )
            row = cursor.fetchone()
            if not row or not row.SoldeData or not row.LignesData:
                return {'solde': None, 'lignes': None}
            return {
                'solde': json.loads(row.SoldeData) if row.SoldeData else None,
                'lignes': json.loads(row.LignesData) if row.LignesData else None,
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'solde': None, 'lignes': None}
