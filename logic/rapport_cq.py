# -*- coding: utf-8 -*-
"""
Analyse des rapports PDF de la machine de contrôle qualité (Focusight).
Extrait le résumé (page 1) et les défauts (pages 2+) pour génération de graphiques.
"""
import re
from collections import Counter
from typing import Dict, List, Any, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def _parse_summary_table(rows: List[List[Any]]) -> Dict[str, str]:
    """Page 1 : table en paires clé-valeur (Machine, JP0012), (Team, Morning Shift), etc."""
    out = {}
    for row in rows:
        if not row:
            continue
        # 6 colonnes : (k1,v1), (k2,v2), (k3,v3)
        for i in range(0, min(len(row), 6), 2):
            k = (row[i] or "").strip().replace("\n", " ")
            v = (row[i + 1] if i + 1 < len(row) else None) or ""
            v = str(v).strip().replace("\n", " ")
            if k and k != "None":
                # Nettoyer les doublons %% dans PassRate/BadRate
                if k in ("PassRate", "BadRate") and "%%" in v:
                    v = v.replace("%%", "%")
                out[k] = v
    return out


def _parse_int(s: Optional[str]) -> Optional[int]:
    if s is None or s == "":
        return None
    s = str(s).strip().replace(" ", "").replace("%", "")
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def _generer_rapport_texte(summary: Dict[str, str], defect_types: Dict[str, int],
                          by_side: Dict[str, int], by_ipu: Dict[str, int],
                          nb_lignes_defaut: int, nb_sheets_uniques: Optional[int]) -> str:
    """Génère un rapport descriptif en français pour envoi au client."""
    lignes = []
    lignes.append("RAPPORT DE CONTRÔLE QUALITÉ — Synthèse")
    lignes.append("=" * 50)
    lignes.append("")
    if summary.get("Machine"):
        lignes.append("Machine : {}".format(summary["Machine"]))
    if summary.get("BatchCode"):
        lignes.append("Code lot : {}".format(summary["BatchCode"]))
    if summary.get("ModelNam"):
        lignes.append("Modèle : {}".format(summary["ModelNam"]))
    if summary.get("ReportTime"):
        lignes.append("Date du rapport : {}".format(summary["ReportTime"]))
    if summary.get("Team"):
        lignes.append("Équipe : {}".format(summary["Team"]))
    lignes.append("")
    lignes.append("RÉSULTATS GLOBAUX")
    lignes.append("-" * 40)
    total = summary.get("Total", "")
    pass_ = summary.get("Pass", "")
    bad = summary.get("Bad", "")
    pass_rate = summary.get("PassRate", "")
    bad_rate = summary.get("BadRate", "")
    if total:
        lignes.append("Nombre total contrôlé : {}".format(total))
    if pass_:
        lignes.append("Conformes (Pass) : {}".format(pass_))
    if pass_rate:
        lignes.append("Taux de conformité : {}".format(pass_rate))
    if bad:
        lignes.append("Défectueux (Bad) : {}".format(bad))
    if bad_rate:
        lignes.append("Taux de défauts : {}".format(bad_rate))
    lignes.append("")
    if defect_types:
        lignes.append("RÉPARTITION PAR TYPE DE DÉFAUT")
        lignes.append("-" * 40)
        for dt, count in sorted(defect_types.items(), key=lambda x: -x[1]):
            lignes.append("  - {} : {}".format(dt, count))
        lignes.append("  (Total enregistrements de défaut : {})".format(sum(defect_types.values())))
        if nb_sheets_uniques is not None:
            lignes.append("  (Articles défectueux distincts : {})".format(nb_sheets_uniques))
        lignes.append("")
    if by_side:
        lignes.append("RÉPARTITION PAR CÔTÉ / CAMÉRA")
        lignes.append("-" * 40)
        for side, count in sorted(by_side.items(), key=lambda x: -x[1]):
            lignes.append("  - {} : {}".format(side, count))
        lignes.append("")
    if by_ipu:
        lignes.append("RÉPARTITION PAR UNITÉ D'INSPECTION (IPU)")
        lignes.append("-" * 40)
        for ipu, count in sorted(by_ipu.items(), key=lambda x: -x[1]):
            lignes.append("  - IPU {} : {}".format(ipu, count))
        lignes.append("")
    lignes.append("CONCLUSION")
    lignes.append("-" * 40)
    if total and bad and pass_rate:
        lignes.append("Le lot a été contrôlé avec un taux de conformité de {}.".format(pass_rate))
        lignes.append("{} article(s) défectueux ont été détectés et écartés.".format(bad))
    lignes.append("")
    lignes.append("— Rapport généré automatiquement à partir du fichier de la machine de contrôle qualité.")
    return "\n".join(lignes)


def analyser_rapport_cq_pdf(file_path_or_stream) -> Dict[str, Any]:
    """
    Analyse un PDF rapport CQ Focusight.
    file_path_or_stream: chemin (str) ou objet fichier (BytesIO).
    Retourne: summary, defect_types, by_side, by_ipu, nb_lignes_defaut, nb_sheets_uniques, rapport_texte.
    """
    if not pdfplumber:
        return {"error": "pdfplumber non installé"}

    result = {
        "summary": {},
        "defect_types": {},
        "by_side": {},
        "by_ipu": {},
        "nb_lignes_defaut": 0,
        "nb_sheets_uniques": None,
        "rapport_texte": "",
        "error": None,
    }
    result["area_energy"] = None
    header_defect = None
    sheet_nums = set()
    area_energy_by_type = {}
    global_area_sum = 0
    global_area_max = None
    global_energy_sum = 0
    global_energy_max = None
    global_area_energy_count = 0

    try:
        with pdfplumber.open(file_path_or_stream) as pdf:
            if not pdf.pages:
                result["error"] = "PDF vide"
                return result

            # Page 1 : résumé
            page0 = pdf.pages[0]
            tables0 = page0.extract_tables()
            if tables0:
                summary = _parse_summary_table(tables0[0])
                result["summary"] = summary

            defect_types = Counter()
            by_side = Counter()
            by_ipu = Counter()
            nb_lignes = 0

            for page in pdf.pages[1:]:
                tables = page.extract_tables()
                for t in tables or []:
                    if not t or len(t) < 2:
                        continue
                    first_row = [str(c or "").strip() for c in t[0]]
                    if "DefectType" in first_row:
                        header_defect = first_row
                    if header_defect is None:
                        continue
                    idx_sheet = next((i for i, h in enumerate(header_defect) if "SheetNum" in h or "Sheet" in h), 0)
                    idx_side = next((i for i, h in enumerate(header_defect) if h == "Side"), 1)
                    idx_ipu = next((i for i, h in enumerate(header_defect) if h == "IPU"), 2)
                    idx_type = next((i for i, h in enumerate(header_defect) if h == "DefectType"), 3)
                    idx_area = next((i for i, h in enumerate(header_defect) if h == "Area"), 4)
                    idx_energy = next((i for i, h in enumerate(header_defect) if h == "Energy"), 5)
                    has_area_energy = len(header_defect) > max(idx_area, idx_energy)
                    start = 1 if "DefectType" in first_row else 0
                    for row in t[start:]:
                        if not row or len(row) <= max(idx_type, idx_side, idx_ipu):
                            continue
                        v0 = str(row[idx_sheet] or "").strip()
                        if v0 == "DefectType" or v0 == "SheetNum":
                            continue
                        nb_lignes += 1
                        if v0 and v0.isdigit():
                            sheet_nums.add(v0)
                        dt = str(row[idx_type] or "").strip()
                        sd = str(row[idx_side] or "").strip()
                        ip = str(row[idx_ipu] or "").strip()
                        if dt:
                            defect_types[dt] += 1
                        if sd:
                            by_side[sd] += 1
                        if ip:
                            by_ipu[ip] += 1
                        if has_area_energy and dt:
                            area_val = _parse_int(row[idx_area] if idx_area < len(row) else None)
                            energy_val = _parse_int(row[idx_energy] if idx_energy < len(row) else None)
                            if area_val is not None or energy_val is not None:
                                if dt not in area_energy_by_type:
                                    area_energy_by_type[dt] = {"count": 0, "sum_area": 0, "max_area": None, "sum_energy": 0, "max_energy": None}
                                area_energy_by_type[dt]["count"] += 1
                                if area_val is not None:
                                    area_energy_by_type[dt]["sum_area"] += area_val
                                    area_energy_by_type[dt]["max_area"] = max(area_energy_by_type[dt]["max_area"] or 0, area_val)
                                    global_area_sum += area_val
                                    global_area_max = max(global_area_max or 0, area_val)
                                if energy_val is not None:
                                    area_energy_by_type[dt]["sum_energy"] += energy_val
                                    area_energy_by_type[dt]["max_energy"] = max(area_energy_by_type[dt]["max_energy"] or 0, energy_val)
                                    global_energy_sum += energy_val
                                    global_energy_max = max(global_energy_max or 0, energy_val)
                                global_area_energy_count += 1

            result["defect_types"] = dict(defect_types)
            result["by_side"] = dict(by_side)
            result["by_ipu"] = dict(by_ipu)
            result["nb_lignes_defaut"] = nb_lignes
            result["nb_sheets_uniques"] = len(sheet_nums) if sheet_nums else None
            # Formater area_energy pour le frontend
            if global_area_energy_count > 0:
                by_type_out = {}
                for dt, st in area_energy_by_type.items():
                    c = st["count"]
                    by_type_out[dt] = {
                        "count": c,
                        "mean_area": round(st["sum_area"] / c, 1) if c and st["sum_area"] else None,
                        "max_area": st["max_area"],
                        "mean_energy": round(st["sum_energy"] / c, 1) if c and st["sum_energy"] else None,
                        "max_energy": st["max_energy"],
                    }
                result["area_energy"] = {
                    "by_type": by_type_out,
                    "global": {
                        "count": global_area_energy_count,
                        "mean_area": round(global_area_sum / global_area_energy_count, 1) if global_area_energy_count else None,
                        "max_area": global_area_max,
                        "mean_energy": round(global_energy_sum / global_area_energy_count, 1) if global_area_energy_count else None,
                        "max_energy": global_energy_max,
                    },
                }
            result["rapport_texte"] = _generer_rapport_texte(
                result["summary"],
                result["defect_types"],
                result["by_side"],
                result["by_ipu"],
                nb_lignes,
                result["nb_sheets_uniques"],
            )

    except Exception as e:
        result["error"] = str(e)

    return result
