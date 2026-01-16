"""
Routes pour le Projet 17 - Fusion de fichiers HTML
"""
from flask import Blueprint, render_template, send_from_directory, abort, make_response
from pathlib import Path
from logic.projet17 import get_merged_html_content, get_all_html_files
from datetime import datetime

projet17_bp = Blueprint('projet17', __name__, url_prefix='/projet17')

@projet17_bp.route('/')
def index():
    """Page principale affichant le contenu fusionné de tous les fichiers HTML"""
    merged_content, file_count = get_merged_html_content()
    html_files = get_all_html_files()
    
    return render_template(
        'projet17.html',
        merged_content=merged_content,
        file_count=file_count,
        html_files=html_files
    )

@projet17_bp.route('/export-pdf')
def export_pdf():
    """Exporte l'intégralité du contenu fusionné en PDF"""
    from io import BytesIO
    import json
    import traceback
    import html as html_module
    import os
    import shutil
    
    log_path = Path(__file__).parent.parent / '.cursor' / 'debug.log'
    
    # #region agent log
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "export-pdf-1",
                "hypothesisId": "A",
                "location": "routes/projet17_routes.py:export_pdf",
                "message": "Debut export PDF",
                "data": {"timestamp": datetime.now().isoformat()},
                "timestamp": int(datetime.now().timestamp() * 1000)
            }) + '\n')
    except:
        pass
    # #endregion
    
    # Essayer d'abord pdfkit (plus adapté pour HTML volumineux)
    pdfkit_available = False
    config = None
    wkhtmltopdf_path = None
    
    try:
        import pdfkit
        # Chercher wkhtmltopdf dans plusieurs emplacements possibles
        possible_paths = [
            r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
            r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
            r"C:\wkhtmltopdf\bin\wkhtmltopdf.exe",
            shutil.which("wkhtmltopdf.exe") or shutil.which("wkhtmltopdf"),
        ]
        
        # #region agent log
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "export-pdf-1",
                    "hypothesisId": "A",
                    "location": "routes/projet17_routes.py:export_pdf",
                    "message": "Recherche wkhtmltopdf",
                    "data": {"possible_paths": possible_paths},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + '\n')
        except:
            pass
        # #endregion
        
        for path in possible_paths:
            if path and os.path.exists(path):
                try:
                    config = pdfkit.configuration(wkhtmltopdf=path)
                    pdfkit_available = True
                    wkhtmltopdf_path = path
                    # #region agent log
                    try:
                        with open(log_path, 'a', encoding='utf-8') as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "export-pdf-1",
                                "hypothesisId": "A",
                                "location": "routes/projet17_routes.py:export_pdf",
                                "message": "wkhtmltopdf trouve",
                                "data": {"path": path},
                                "timestamp": int(datetime.now().timestamp() * 1000)
                            }) + '\n')
                    except:
                        pass
                    # #endregion
                    break
                except Exception as e:
                    # #region agent log
                    try:
                        with open(log_path, 'a', encoding='utf-8') as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "export-pdf-1",
                                "hypothesisId": "A",
                                "location": "routes/projet17_routes.py:export_pdf",
                                "message": "Erreur config pdfkit",
                                "data": {"path": path, "error": str(e)},
                                "timestamp": int(datetime.now().timestamp() * 1000)
                            }) + '\n')
                    except:
                        pass
                    # #endregion
                    continue
    except ImportError:
        # #region agent log
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "export-pdf-1",
                    "hypothesisId": "A",
                    "location": "routes/projet17_routes.py:export_pdf",
                    "message": "pdfkit non importe",
                    "data": {},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + '\n')
        except:
            pass
        # #endregion
        pdfkit_available = False
    
    # #region agent log
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "export-pdf-1",
                "hypothesisId": "B",
                "location": "routes/projet17_routes.py:export_pdf",
                "message": "Avant get_merged_html_content",
                "data": {},
                "timestamp": int(datetime.now().timestamp() * 1000)
            }) + '\n')
    except:
        pass
    # #endregion
    
    try:
        merged_content, file_count = get_merged_html_content()
        html_files = get_all_html_files()
        
        # #region agent log
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "export-pdf-1",
                    "hypothesisId": "B",
                    "location": "routes/projet17_routes.py:export_pdf",
                    "message": "Apres get_merged_html_content",
                    "data": {"file_count": file_count, "merged_content_length": len(merged_content) if merged_content else 0},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + '\n')
        except:
            pass
        # #endregion
    except Exception as e:
        # #region agent log
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "export-pdf-1",
                    "hypothesisId": "B",
                    "location": "routes/projet17_routes.py:export_pdf",
                    "message": "Erreur get_merged_html_content",
                    "data": {"error": str(e), "traceback": traceback.format_exc()},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + '\n')
        except:
            pass
        # #endregion
        return f"Erreur lors de la récupération du contenu: {str(e)}", 500
    
    # Créer le HTML complet pour le PDF
    html_for_pdf = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Projet 17 - Fusion de fichiers HTML</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: Arial, sans-serif;
                font-size: 10pt;
                line-height: 1.4;
                color: #333;
            }}
            .pdf-header {{
                background: #667eea;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .pdf-header h1 {{
                margin: 0;
                font-size: 24pt;
            }}
            .pdf-header .file-count {{
                margin-top: 10px;
                font-size: 12pt;
                opacity: 0.9;
            }}
            .file-header {{
                background: #667eea;
                color: white;
                padding: 12px 15px;
                margin: 30px 0 15px 0;
                border-radius: 6px;
                page-break-inside: avoid;
            }}
            .file-title {{
                margin: 0;
                font-size: 14pt;
                font-weight: bold;
            }}
            .file-number {{
                background-color: rgba(255, 255, 255, 0.3);
                padding: 4px 10px;
                border-radius: 4px;
                margin-right: 10px;
            }}
            .file-content {{
                padding: 15px;
                margin-bottom: 25px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #fafafa;
                page-break-inside: avoid;
            }}
            .file-content img {{
                max-width: 100%;
                height: auto;
            }}
            .file-content table {{
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
                font-size: 9pt;
            }}
            .file-content table td,
            .file-content table th {{
                border: 1px solid #ddd;
                padding: 6px;
            }}
            .stats {{
                background-color: #e8f5e9;
                padding: 12px;
                border-radius: 4px;
                margin-bottom: 20px;
                text-align: center;
                font-size: 11pt;
            }}
        </style>
    </head>
    <body>
        <div class="pdf-header">
            <h1>Projet 17 - Fusion de fichiers HTML</h1>
            <div class="file-count">Total: {file_count} fichiers HTML fusionnés</div>
        </div>
        
        <div class="stats">
            <strong>Statistiques:</strong> 
            {file_count} fichier(s) HTML trouvé(s) et affiché(s) intégralement
            <br>
            <small>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</small>
        </div>
        
        {merged_content}
    </body>
    </html>
    """
    
    try:
        # Pour les fichiers très volumineux (>10MB), utiliser reportlab directement
        # car pdfkit peut bloquer ou timeout
        html_size_mb = len(html_for_pdf) / (1024 * 1024)
        
        # #region agent log
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "export-pdf-1",
                    "hypothesisId": "C",
                    "location": "routes/projet17_routes.py:export_pdf",
                    "message": "Decision methode PDF",
                    "data": {"html_size_mb": round(html_size_mb, 2), "pdfkit_available": pdfkit_available},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + '\n')
        except:
            pass
        # #endregion
        
        # Si le HTML est trop volumineux (>10MB), utiliser reportlab directement
        if html_size_mb > 10:
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "export-pdf-1",
                        "hypothesisId": "C",
                        "location": "routes/projet17_routes.py:export_pdf",
                        "message": "HTML trop volumineux, utilisation reportlab",
                        "data": {"html_size_mb": round(html_size_mb, 2)},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + '\n')
            except:
                pass
            # #endregion
            pdfkit_available = False  # Forcer l'utilisation de reportlab
        
        if pdfkit_available and config:
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "export-pdf-1",
                        "hypothesisId": "C",
                        "location": "routes/projet17_routes.py:export_pdf",
                        "message": "Utilisation pdfkit",
                        "data": {"wkhtmltopdf_path": wkhtmltopdf_path},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + '\n')
            except:
                pass
            # #endregion
            
            # Utiliser pdfkit pour générer le PDF
            options = {
                'page-size': 'A4',
                'margin-top': '2cm',
                'margin-right': '2cm',
                'margin-bottom': '2cm',
                'margin-left': '2cm',
                'encoding': "UTF-8",
                'enable-local-file-access': None,
                'quiet': ''
            }
            
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "export-pdf-1",
                        "hypothesisId": "C",
                        "location": "routes/projet17_routes.py:export_pdf",
                        "message": "Avant pdfkit.from_string",
                        "data": {"html_length": len(html_for_pdf)},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + '\n')
            except:
                pass
            # #endregion
            
            try:
                import signal
                import threading
                
                pdf_bytes = None
                pdfkit_error = None
                
                def generate_pdf():
                    nonlocal pdf_bytes, pdfkit_error
                    try:
                        pdf_bytes = pdfkit.from_string(html_for_pdf, False, configuration=config, options=options)
                        # #region agent log
                        try:
                            with open(log_path, 'a', encoding='utf-8') as f:
                                f.write(json.dumps({
                                    "sessionId": "debug-session",
                                    "runId": "export-pdf-1",
                                    "hypothesisId": "C",
                                    "location": "routes/projet17_routes.py:export_pdf",
                                    "message": "PDF genere avec pdfkit",
                                    "data": {"pdf_size": len(pdf_bytes) if pdf_bytes else 0},
                                    "timestamp": int(datetime.now().timestamp() * 1000)
                                }) + '\n')
                        except:
                            pass
                        # #endregion
                    except Exception as e:
                        pdfkit_error = e
                        # #region agent log
                        try:
                            with open(log_path, 'a', encoding='utf-8') as f:
                                f.write(json.dumps({
                                    "sessionId": "debug-session",
                                    "runId": "export-pdf-1",
                                    "hypothesisId": "C",
                                    "location": "routes/projet17_routes.py:export_pdf",
                                    "message": "Erreur pdfkit.from_string",
                                    "data": {"error": str(e), "error_type": type(e).__name__, "traceback": traceback.format_exc()},
                                    "timestamp": int(datetime.now().timestamp() * 1000)
                                }) + '\n')
                        except:
                            pass
                        # #endregion
                
                # Exécuter dans un thread avec timeout
                pdf_thread = threading.Thread(target=generate_pdf)
                pdf_thread.daemon = True
                pdf_thread.start()
                pdf_thread.join(timeout=300)  # Timeout de 5 minutes
                
                if pdf_thread.is_alive():
                    # Le thread est toujours en cours, cela signifie timeout
                    # #region agent log
                    try:
                        with open(log_path, 'a', encoding='utf-8') as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "export-pdf-1",
                                "hypothesisId": "C",
                                "location": "routes/projet17_routes.py:export_pdf",
                                "message": "Timeout pdfkit.from_string",
                                "data": {"html_length": len(html_for_pdf)},
                                "timestamp": int(datetime.now().timestamp() * 1000)
                            }) + '\n')
                    except:
                        pass
                    # #endregion
                    raise TimeoutError("La génération du PDF prend trop de temps (>5 minutes). Le fichier HTML est trop volumineux (21MB).")
                
                if pdfkit_error:
                    raise pdfkit_error
                    
                if pdf_bytes is None:
                    raise Exception("La génération du PDF a échoué sans erreur explicite")
                    
            except TimeoutError:
                raise
            except Exception as e:
                # #region agent log
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "export-pdf-1",
                            "hypothesisId": "C",
                            "location": "routes/projet17_routes.py:export_pdf",
                            "message": "Exception dans pdfkit",
                            "data": {"error": str(e), "error_type": type(e).__name__, "traceback": traceback.format_exc()},
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }) + '\n')
                except:
                    pass
                # #endregion
                raise
            
            response = make_response(pdf_bytes)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=projet17_fusion_complete_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            
            return response
        else:
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "export-pdf-1",
                        "hypothesisId": "D",
                        "location": "routes/projet17_routes.py:export_pdf",
                        "message": "pdfkit non disponible, essai reportlab",
                        "data": {},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + '\n')
            except:
                pass
            # #endregion
            
            # Alternative avec reportlab si pdfkit n'est pas disponible
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import cm
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
                from reportlab.lib import colors
                from reportlab.lib.enums import TA_LEFT, TA_CENTER
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                import re
                from html.parser import HTMLParser
                
                # #region agent log
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "export-pdf-1",
                            "hypothesisId": "D",
                            "location": "routes/projet17_routes.py:export_pdf",
                            "message": "reportlab importe OK",
                            "data": {},
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }) + '\n')
                except:
                    pass
                # #endregion
                
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                      rightMargin=2*cm, leftMargin=2*cm,
                                      topMargin=2*cm, bottomMargin=2*cm)
                
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                           fontSize=18, textColor=colors.HexColor('#667eea'),
                                           spaceAfter=20, alignment=TA_CENTER)
                normal_style = ParagraphStyle('Normal', parent=styles['Normal'],
                                            fontSize=9, leading=12)
                file_header_style = ParagraphStyle('FileHeader', parent=styles['Heading2'],
                                                 fontSize=12, textColor=colors.white,
                                                 backColor=colors.HexColor('#667eea'),
                                                 spaceAfter=10, spaceBefore=20,
                                                 leftIndent=0, rightIndent=0)
                
                elements = []
                
                # En-tête
                elements.append(Paragraph("Projet 17 - Fusion de fichiers HTML", title_style))
                elements.append(Paragraph(f"Total: {file_count} fichiers HTML fusionnés", normal_style))
                elements.append(Spacer(1, 1*cm))
                
                # Statistiques
                stats_text = f"Statistiques: {file_count} fichier(s) HTML trouvé(s) et affiché(s) intégralement<br/>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}"
                elements.append(Paragraph(stats_text, normal_style))
                elements.append(Spacer(1, 1*cm))
                
                # Parser le contenu HTML et le convertir en éléments ReportLab
                # Extraire les fichiers du contenu fusionné
                file_pattern = r'<div class="file-header"[^>]*id="file-(\d+)"[^>]*>.*?<span class="file-name">(.*?)</span>.*?<div class="file-content"[^>]*>(.*?)</div>'
                files = re.findall(file_pattern, merged_content, re.DOTALL | re.IGNORECASE)
                
                # #region agent log
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "export-pdf-1",
                            "hypothesisId": "D",
                            "location": "routes/projet17_routes.py:export_pdf",
                            "message": "Fichiers extraits",
                            "data": {"file_count": len(files)},
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }) + '\n')
                except:
                    pass
                # #endregion
                
                for idx, (file_num, file_name, file_content) in enumerate(files):
                    if idx > 0:
                        elements.append(PageBreak())
                    
                    # En-tête du fichier
                    header_text = f"Fichier {file_num}: {html_module.unescape(file_name)}"
                    elements.append(Paragraph(header_text, file_header_style))
                    elements.append(Spacer(1, 0.5*cm))
                    
                    # Nettoyer le HTML pour ReportLab
                    clean_content = re.sub(r'<script[^>]*>.*?</script>', '', file_content, flags=re.DOTALL | re.IGNORECASE)
                    clean_content = re.sub(r'<style[^>]*>.*?</style>', '', clean_content, flags=re.DOTALL | re.IGNORECASE)
                    clean_content = html_module.unescape(clean_content)
                    
                    # Convertir les balises HTML simples en format ReportLab
                    clean_content = re.sub(r'<br\s*/?>', '<br/>', clean_content, flags=re.IGNORECASE)
                    clean_content = re.sub(r'<p[^>]*>', '<br/>', clean_content, flags=re.IGNORECASE)
                    clean_content = re.sub(r'</p>', '<br/>', clean_content, flags=re.IGNORECASE)
                    clean_content = re.sub(r'<[^>]+>', '', clean_content)  # Retirer toutes les autres balises
                    
                    # Limiter la longueur pour éviter les problèmes de mémoire
                    if len(clean_content) > 100000:
                        clean_content = clean_content[:100000] + "... [contenu tronqué pour raison de taille]"
                    
                    try:
                        elements.append(Paragraph(clean_content, normal_style))
                    except Exception as e:
                        # Si le contenu contient des caractères problématiques, le nettoyer davantage
                        clean_content = clean_content.encode('ascii', 'ignore').decode('ascii')
                        elements.append(Paragraph(clean_content[:50000] + "... [contenu tronqué]", normal_style))
                
                # #region agent log
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "export-pdf-1",
                            "hypothesisId": "D",
                            "location": "routes/projet17_routes.py:export_pdf",
                            "message": "Avant doc.build",
                            "data": {"elements_count": len(elements)},
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }) + '\n')
                except:
                    pass
                # #endregion
                
                doc.build(elements)
                buffer.seek(0)
                
                # #region agent log
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "export-pdf-1",
                            "hypothesisId": "D",
                            "location": "routes/projet17_routes.py:export_pdf",
                            "message": "PDF genere avec reportlab",
                            "data": {"pdf_size": buffer.tell()},
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }) + '\n')
                except:
                    pass
                # #endregion
                
                response = make_response(buffer.read())
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename=projet17_fusion_complete_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
                
                return response
                
            except ImportError:
                # #region agent log
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "export-pdf-1",
                            "hypothesisId": "D",
                            "location": "routes/projet17_routes.py:export_pdf",
                            "message": "reportlab non disponible",
                            "data": {},
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }) + '\n')
                except:
                    pass
                # #endregion
                
                # Si reportlab n'est pas disponible non plus, retourner un message d'erreur clair
                error_message = """
                <html>
                <head><title>Erreur - Export PDF</title></head>
                <body style="font-family: Arial; padding: 40px; text-align: center;">
                    <h1 style="color: #d32f2f;">Erreur : Export PDF non disponible</h1>
                    <p style="font-size: 16px; margin: 20px 0;">
                        Pour générer le PDF, vous devez installer <strong>wkhtmltopdf</strong> ou <strong>reportlab</strong>.
                    </p>
                    <p style="font-size: 14px; color: #666;">
                        Option 1: Téléchargez et installez wkhtmltopdf depuis :<br/>
                        <a href="https://wkhtmltopdf.org/downloads.html" target="_blank" style="color: #667eea;">
                            https://wkhtmltopdf.org/downloads.html
                        </a>
                    </p>
                    <p style="font-size: 14px; color: #666;">
                        Option 2: Installez reportlab avec :<br/>
                        <code style="background: #f5f5f5; padding: 5px; border-radius: 3px;">pip install reportlab</code>
                    </p>
                    <p style="font-size: 12px; color: #999; margin-top: 30px;">
                        Après l'installation, redémarrez le serveur Flask.
                    </p>
                </body>
                </html>
                """
                return error_message, 500
            
    except Exception as e:
        import traceback
        # #region agent log
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "export-pdf-1",
                    "hypothesisId": "E",
                    "location": "routes/projet17_routes.py:export_pdf",
                    "message": "Erreur generation PDF",
                    "data": {"error": str(e), "error_type": type(e).__name__, "traceback": traceback.format_exc()},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + '\n')
        except:
            pass
        # #endregion
        error_msg = f"Erreur lors de la génération du PDF: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return error_msg, 500

@projet17_bp.route('/<path:resource_path>')
def serve_static_resource(resource_path):
    """Sert les ressources statiques (CSS, JS, images) depuis html_sources si elles existent"""
    html_sources_dir = Path(__file__).parent.parent / 'projet17' / 'html_sources'
    resource_file = html_sources_dir / resource_path
    
    # Vérifier que le fichier existe et est dans le dossier html_sources (sécurité)
    if resource_file.exists() and resource_file.is_file() and html_sources_dir in resource_file.parents:
        return send_from_directory(str(html_sources_dir), resource_path)
    else:
        # Retourner une réponse vide pour éviter les erreurs 404
        return '', 204











