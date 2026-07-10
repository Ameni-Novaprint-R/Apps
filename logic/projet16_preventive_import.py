# -*- coding: utf-8 -*-
"""Import du planning de maintenance préventive depuis Excel (projet 16)."""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

import pandas as pd

from db import get_db_cursor
from logic.projet16 import get_machines_disponibles

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PREVENTIVE_IMPORT_DIR = os.path.join(PROJECT_ROOT, 'imports_projet16', 'preventive')
DEFAULT_EXCEL_FILENAME = 'PLANNING_PREVENTIF.xlsx'

PERIODICITE_MAP = {
    'quotidienne': 'Quotidienne',
    'quotidien': 'Quotidienne',
    'daily': 'Quotidienne',
    'hebdomadaire': 'Hebdomadaire',
    'weekly': 'Hebdomadaire',
    'mensuelle': 'Mensuelle',
    'mensuel': 'Mensuelle',
    'monthly': 'Mensuelle',
    'trimestrielle': 'Trimestrielle',
    'trimestriel': 'Trimestrielle',
    'quarterly': 'Trimestrielle',
    'semestrielle': 'Semestrielle',
    'semestriel': 'Semestrielle',
    'semiannual': 'Semestrielle',
    'annuelle': 'Annuelle',
    'annuel': 'Annuelle',
    'annual': 'Annuelle',
    'yearly': 'Annuelle',
    'tous les 2 ans': 'Tous les 2 ans',
    'tous les 3 ans': 'Tous les 3 ans',
    'tous les 5 ans': 'Tous les 5 ans',
    '2 ans': 'Tous les 2 ans',
    '3 ans': 'Tous les 3 ans',
    '5 ans': 'Tous les 5 ans',
}

VALID_PERIODICITES = {
    'Quotidienne', 'Hebdomadaire', 'Mensuelle', 'Trimestrielle',
    'Semestrielle', 'Annuelle', 'Tous les 2 ans', 'Tous les 3 ans', 'Tous les 5 ans',
}

HEADER_TOKENS = {'tâche', 'tache', 'task', 'description', 'référence', 'reference'}


def ensure_import_directory() -> str:
    os.makedirs(PREVENTIVE_IMPORT_DIR, exist_ok=True)
    return PREVENTIVE_IMPORT_DIR


def _norm_col(value: Any) -> str:
    return str(value or '').strip().lower().replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('à', 'a').replace('â', 'a')


def find_excel_file_in_import_dir() -> str | None:
    ensure_import_directory()
    preferred = os.path.join(PREVENTIVE_IMPORT_DIR, DEFAULT_EXCEL_FILENAME)
    if os.path.isfile(preferred):
        return preferred

    candidates = []
    for name in os.listdir(PREVENTIVE_IMPORT_DIR):
        if name.lower().endswith(('.xlsx', '.xlsm', '.xls')) and not name.startswith('~$'):
            path = os.path.join(PREVENTIVE_IMPORT_DIR, name)
            candidates.append((os.path.getmtime(path), path))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def get_preventive_import_status() -> dict:
    import_dir = ensure_import_directory()
    excel_path = find_excel_file_in_import_dir()
    status = {
        'import_dir': import_dir,
        'expected_filename': DEFAULT_EXCEL_FILENAME,
        'file_found': bool(excel_path),
        'file_path': excel_path,
        'file_name': os.path.basename(excel_path) if excel_path else None,
        'modified_at': None,
        'sheet_names': [],
        'sheet_count': 0,
    }
    if not excel_path:
        return status

    status['modified_at'] = datetime.fromtimestamp(os.path.getmtime(excel_path)).strftime('%Y-%m-%d %H:%M:%S')
    try:
        xl = pd.ExcelFile(excel_path)
        status['sheet_names'] = [str(s) for s in xl.sheet_names]
        status['sheet_count'] = len(xl.sheet_names)
    except Exception as exc:
        status['error'] = str(exc)
    return status


def _normalize_periodicite(raw: str | None) -> str | None:
    if not raw or not str(raw).strip():
        return None
    original = str(raw).strip()
    lower = original.lower()
    if lower in PERIODICITE_MAP:
        return PERIODICITE_MAP[lower]
    if original in VALID_PERIODICITES:
        return original
    for key, value in PERIODICITE_MAP.items():
        if key in lower or lower in key:
            return value

    compact = re.sub(r'\s+', '', lower)
    months_match = re.search(r'(\d+)\s*mois', compact)
    if months_match:
        months = int(months_match.group(1))
        if months == 1:
            return 'Mensuelle'
        if months == 3:
            return 'Trimestrielle'
        if months == 6:
            return 'Semestrielle'
        if months == 12:
            return 'Annuelle'

    years_match = re.search(r'(\d+)\s*an', compact)
    if years_match:
        years = int(years_match.group(1))
        if years == 1:
            return 'Annuelle'
        if years == 2:
            return 'Tous les 2 ans'
        if years == 3:
            return 'Tous les 3 ans'
        if years == 5:
            return 'Tous les 5 ans'

    match = re.search(r'tous?\s*les?\s*(\d+)\s*ans?', lower)
    if match:
        years = int(match.group(1))
        if years == 2:
            return 'Tous les 2 ans'
        if years == 3:
            return 'Tous les 3 ans'
        if years == 5:
            return 'Tous les 5 ans'
    return None


def _cell_str(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text if text and text != '-' else None


def _find_header_row_index(df_raw: pd.DataFrame, max_scan_rows: int = 25) -> int | None:
    """Repère la ligne d'en-tête du tableau (format INS-MAI-04 et variantes)."""
    for i in range(min(max_scan_rows, len(df_raw))):
        row_vals = [_norm_col(v) for v in df_raw.iloc[i].tolist() if pd.notna(v)]
        if not row_vals:
            continue
        joined = ' '.join(row_vals)
        has_description = 'description' in joined or 'mesure' in joined
        has_periodicite = 'periodic' in joined or 'perodic' in joined or 'frequence' in joined
        has_numero = any(
            re.match(r'^n\s*[°º]?\s*$', v) or v in ('no', 'numero', 'num', 'reference', 'ref')
            for v in row_vals
        )
        if has_description and (has_periodicite or has_numero):
            return i
    return None


def _load_sheet_dataframe(path: str, sheet_name: str) -> pd.DataFrame:
    """Charge une feuille en détectant la ligne d'en-tête réelle (pas la ligne 0)."""
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    if raw.empty:
        return raw

    header_idx = _find_header_row_index(raw)
    if header_idx is None:
        return pd.read_excel(path, sheet_name=sheet_name)

    header_vals = []
    for col_idx, value in enumerate(raw.iloc[header_idx].tolist()):
        label = _cell_str(value)
        header_vals.append(label if label else f'col_{col_idx}')

    df = raw.iloc[header_idx + 1:].copy()
    df.columns = header_vals
    df = df.reset_index(drop=True)

    if not df.empty:
        cols = _identify_columns(df)
        first = df.iloc[0]
        ref = _cell_str(first.get(cols['reference'])) if cols['reference'] else None
        tache = _cell_str(first.get(cols['tache'])) if cols['tache'] else None
        if not ref and not tache:
            df = df.iloc[1:].reset_index(drop=True)

    return df


def _identify_columns(df: pd.DataFrame) -> dict[str, Any]:
    cols: dict[str, Any] = {
        'reference': None,
        'tache': None,
        'frequence': None,
        'duree': None,
        'responsable': None,
        'specifications': None,
        'specification_cols': [],
    }
    for col in df.columns:
        col_str = str(col).strip()
        norm = _norm_col(col_str)
        if not col_str or norm in ('', 'nan'):
            if cols['reference'] is None:
                cols['reference'] = col
            continue
        if 'reference' in norm or norm == 'ref':
            cols['reference'] = col
        elif re.match(r'^n\s*[°º]?\s*$', norm) or norm in ('no', 'numero', 'num'):
            cols['reference'] = col
        elif 'tache' in norm or 'task' in norm or 'mesure' in norm or 'description' in norm:
            cols['tache'] = col
        elif 'frequence' in norm or 'periodic' in norm or 'perodic' in norm:
            cols['frequence'] = col
        elif 'duree' in norm or 'duration' in norm:
            cols['duree'] = col
        elif 'responsable' in norm or 'role' in norm or 'personne' in norm or 'charge' in norm:
            cols['responsable'] = col
        elif 'accessoire' in norm or ('petite' in norm and 'maintenance' in norm):
            cols['specification_cols'].append(col)
        elif 'specification' in norm or 'observation' in norm or 'piece' in norm or 'rechange' in norm:
            cols['specifications'] = col
    return cols


def _build_specifications(row: pd.Series, cols: dict[str, Any]) -> str | None:
    parts: list[str] = []
    for spec_col in cols.get('specification_cols') or []:
        value = _cell_str(row.get(spec_col))
        if value:
            parts.append(value)
    if cols.get('specifications'):
        value = _cell_str(row.get(cols['specifications']))
        if value:
            parts.append(value)
    if not parts:
        return None
    return ' | '.join(parts)


def _parse_dataframe_rows(df: pd.DataFrame) -> list[dict]:
    cols = _identify_columns(df)
    if not cols['tache']:
        return []

    rows = []
    for index, row in df.iterrows():
        tache = _cell_str(row.get(cols['tache'])) if cols['tache'] else None
        if not tache or tache.lower() in HEADER_TOKENS:
            continue

        reference = _cell_str(row.get(cols['reference'])) if cols['reference'] else None
        periodicite = _normalize_periodicite(_cell_str(row.get(cols['frequence'])) if cols['frequence'] else None)
        if not periodicite:
            continue

        rows.append({
            'reference': reference,
            'tache': tache,
            'periodicite': periodicite,
            'duree': _cell_str(row.get(cols['duree'])) if cols['duree'] else None,
            'role_requis': _cell_str(row.get(cols['responsable'])) if cols['responsable'] else None,
            'specifications_observations': _build_specifications(row, cols),
            'ordre_affichage': len(rows) + 1,
        })
    return rows


def _build_machine_lookup() -> dict[str, str]:
    lookup = {}
    for machine in get_machines_disponibles():
        nom = (machine.get('nom') or '').strip()
        if nom:
            lookup[nom.lower()] = nom
    return lookup


def resolve_machine_name(sheet_name: str, machine_lookup: dict[str, str] | None = None) -> tuple[str, str | None]:
    """Retourne (nom_machine, avertissement ou None)."""
    sheet_name = (sheet_name or '').strip()
    if not sheet_name:
        return sheet_name, 'Nom de feuille vide'

    lookup = machine_lookup or _build_machine_lookup()
    if sheet_name.lower() in lookup:
        return lookup[sheet_name.lower()], None

    normalized_sheet = re.sub(r'\s+', ' ', sheet_name.lower())
    for key, canonical in lookup.items():
        if key == normalized_sheet or key.replace(' ', '') == normalized_sheet.replace(' ', ''):
            return canonical, None

    return sheet_name, f"Machine « {sheet_name} » absente de GP_POSTES — nom de feuille conservé"


def import_preventive_from_excel(
    excel_file_path: str | None = None,
    *,
    replace_existing: bool = False,
    dry_run: bool = False,
) -> dict:
    path = excel_file_path or find_excel_file_in_import_dir()
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(
            f"Aucun fichier Excel dans {PREVENTIVE_IMPORT_DIR}. "
            f"Déposez {DEFAULT_EXCEL_FILENAME} (ou un autre .xlsx) dans ce dossier."
        )

    xl = pd.ExcelFile(path)
    machine_lookup = _build_machine_lookup()
    summary = {
        'file_path': path,
        'file_name': os.path.basename(path),
        'dry_run': dry_run,
        'replace_existing': replace_existing,
        'imported_total': 0,
        'skipped_total': 0,
        'machines': [],
        'warnings': [],
    }

    with get_db_cursor() as cursor:
        for sheet_name in xl.sheet_names:
            df = _load_sheet_dataframe(path, sheet_name)
            machine_name, warning = resolve_machine_name(sheet_name, machine_lookup)
            if warning:
                summary['warnings'].append(warning)

            parsed_rows = _parse_dataframe_rows(df)
            machine_result = {
                'sheet': sheet_name,
                'machine': machine_name,
                'imported': 0,
                'parsed_rows': len(parsed_rows),
                'skipped': max(0, len(df) - len(parsed_rows)),
                'deleted': 0,
                'skipped_existing': False,
                'existing_count': 0,
                'format_unrecognized': len(parsed_rows) == 0 and len(df) > 0,
            }

            if dry_run:
                machine_result['imported'] = len(parsed_rows)
                summary['imported_total'] += len(parsed_rows)
                summary['skipped_total'] += machine_result['skipped']
                summary['machines'].append(machine_result)
                continue

            # Si la machine a déjà des tâches en base, ne rien modifier (import = uniquement compléter les machines manquantes)
            if machine_name:
                cursor.execute(
                    "SELECT COUNT(*) AS cnt FROM WEB_GMAO_PREVENTIVE WHERE Nom_GP_POSTES = ?",
                    (machine_name,),
                )
                existing_row = cursor.fetchone()
                existing_count = int(existing_row.cnt if existing_row else 0)
                machine_result['existing_count'] = existing_count
                if existing_count > 0 and not replace_existing:
                    machine_result['skipped_existing'] = True
                    summary['machines'].append(machine_result)
                    continue

            if replace_existing and machine_name:
                cursor.execute(
                    "SELECT COUNT(*) AS cnt FROM WEB_GMAO_PREVENTIVE WHERE Nom_GP_POSTES = ?",
                    (machine_name,),
                )
                deleted_row = cursor.fetchone()
                machine_result['deleted'] = int(deleted_row.cnt if deleted_row else 0)
                cursor.execute(
                    "DELETE FROM WEB_GMAO_PREVENTIVE WHERE Nom_GP_POSTES = ?",
                    (machine_name,),
                )

            for row in parsed_rows:
                cursor.execute(
                    """
                    INSERT INTO WEB_GMAO_PREVENTIVE (
                        Nom_GP_POSTES,
                        Reference,
                        Tache,
                        Periodicite,
                        Duree,
                        RoleRequis,
                        SpecificationsObservations,
                        OrdreAffichage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        machine_name,
                        row['reference'],
                        row['tache'],
                        row['periodicite'],
                        row['duree'],
                        row['role_requis'],
                        row['specifications_observations'],
                        row['ordre_affichage'],
                    ),
                )
                machine_result['imported'] += 1

            summary['imported_total'] += machine_result['imported']
            summary['skipped_total'] += machine_result['skipped']
            summary['machines'].append(machine_result)

        if not dry_run:
            cursor.connection.commit()

    return summary
