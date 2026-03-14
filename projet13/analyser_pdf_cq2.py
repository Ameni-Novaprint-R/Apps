#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extraction complete des donnees du rapport CQ."""
import pdfplumber
from collections import Counter, defaultdict

path = r'x:\projet13\rapports_controle_qualite_exemples\FAMODINE40MG2_260228002 (3).pdf'
out_path = r'x:\projet13\rapports_controle_qualite_exemples\analyse_complete.txt'

summary = {}
defect_types = Counter()
sides = Counter()
ipu = Counter()

with open(out_path, 'w', encoding='utf-8') as out:
    with pdfplumber.open(path) as pdf:
        # Page 1 - resume
        p0 = pdf.pages[0]
        txt = p0.extract_text() or ''
        t0 = p0.extract_tables()
        if t0:
            for row in t0[0]:
                if row and len(row) >= 2:
                    k, v = str(row[0] or '').strip(), str(row[1] or '').strip()
                    if k and v: summary[k] = v
        out.write('RESUME (page 1):\n')
        for k, v in summary.items():
            out.write(f'  {k}: {v}\n')

        # Pages 2+ - defauts
        for i, page in enumerate(pdf.pages[1:], 2):
            tables = page.extract_tables()
            for t in (tables or []):
                if not t or len(t) < 2: continue
                header = [str(x or '').strip() for x in t[0]]
                if 'DefectType' not in header:
                    continue
                idx_type = header.index('DefectType') if 'DefectType' in header else 3
                idx_side = header.index('Side') if 'Side' in header else 1
                idx_ipu = header.index('IPU') if 'IPU' in header else 2
                for row in t[1:]:
                    if row and len(row) > max(idx_type, idx_side, idx_ipu):
                        dt = str(row[idx_type] or '').strip()
                        sd = str(row[idx_side] or '').strip()
                        ip = str(row[idx_ipu] or '').strip()
                        if dt: defect_types[dt] += 1
                        if sd: sides[sd] += 1
                        if ip: ipu[ip] += 1

    out.write('\nTYPES DE DEFAUT (nombre):\n')
    for dt, cnt in defect_types.most_common():
        out.write(f'  {dt}: {cnt}\n')
    out.write('\nPAR COTE/SIDE:\n')
    for sd, cnt in sides.most_common():
        out.write(f'  {sd}: {cnt}\n')
    out.write('\nPAR IPU:\n')
    for ip, cnt in ipu.most_common():
        out.write(f'  IPU {ip}: {cnt}\n')

print('OK - ecrit dans', out_path)
