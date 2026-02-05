"""
Logique pour le Projet 12 - Registre de suivi des Produits Non Conformes et des Réclamations Clients
"""
from db import get_db_connection
from datetime import datetime

def generer_reference_fichier(type_registre, cursor):
    """
    Génère automatiquement une référence fichier selon le type
    - RCL XX pour réclamation client
    - NCP XX pour produit non conforme
    Le numéro est séquentiel selon le type
    """
    # Déterminer le préfixe selon le type
    if type_registre == 'REC':
        prefixe = 'RCL'
    else:  # NC
        prefixe = 'NCP'
    
    # Récupérer le nombre d'enregistrements du même type
    cursor.execute("""
        SELECT COUNT(*) 
        FROM WEB_PdtNC_RecClt 
        WHERE TYPE = ?
    """, (type_registre,))
    
    count = cursor.fetchone()[0]
    numero = count + 1
    
    # Générer la référence au format "XXX NN"
    reference = f"{prefixe} {numero:02d}"
    
    return reference

def get_liste_references():
    """
    Récupère la liste des références de commandes
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        SELECT DISTINCT Reference 
        FROM COMMANDES 
        WHERE Reference IS NOT NULL 
        ORDER BY Reference
        """
        cursor.execute(query)
        references = [row.Reference for row in cursor.fetchall()]
        return references
    except Exception as e:
        print(f"Erreur lors de la récupération des références : {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_liste_clients():
    """
    Récupère la liste des clients (RaiSocTri de SOCIETES)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        SELECT DISTINCT RaiSocTri 
        FROM SOCIETES 
        WHERE RaiSocTri IS NOT NULL 
        ORDER BY RaiSocTri
        """
        cursor.execute(query)
        clients = [row.RaiSocTri for row in cursor.fetchall()]
        return clients
    except Exception as e:
        print(f"Erreur lors de la récupération des clients : {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_liste_numeros():
    """
    Récupère la liste des numéros de commandes
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        SELECT DISTINCT Numero 
        FROM COMMANDES 
        WHERE Numero IS NOT NULL 
        ORDER BY Numero
        """
        cursor.execute(query)
        numeros = [row.Numero for row in cursor.fetchall()]
        return numeros
    except Exception as e:
        print(f"Erreur lors de la récupération des numéros : {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_info_commande(numero):
    """
    Récupère les informations d'une commande (client, référence et quantité) à partir du numéro
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Nettoyer le numéro (supprimer les espaces)
        numero_clean = numero.strip() if numero else ''
        
        query = """
        SELECT C.Reference, S.RaiSocTri, C.QteComm
        FROM COMMANDES C
        LEFT JOIN SOCIETES S ON C.ID_SOCIETE = S.ID
        WHERE LTRIM(RTRIM(C.Numero)) = ?
        """
        cursor.execute(query, (numero_clean,))
        row = cursor.fetchone()
        
        if row:
            result = {
                'reference': row.Reference if row.Reference else '',
                'client': row.RaiSocTri if row.RaiSocTri else '',
                'qte_comm': row.QteComm if row.QteComm else 0
            }
            print(f"INFO: Commande {numero_clean} trouvée - Client: {result['client']}, Ref: {result['reference']}, Qté: {result['qte_comm']}")
            return result
        else:
            print(f"AVERTISSEMENT: Commande {numero_clean} non trouvée")
            return None
    except Exception as e:
        print(f"Erreur lors de la récupération des infos de commande : {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()

def ajouter_enregistrement(date_str, type_registre, nc, des_nc, cause, 
                          numero_commandes, reference_commandes, raisoctri_societes,
                          qte_comm_commandes=None, qte_nc=None, carac_nc=None):
    """
    Ajoute un nouvel enregistrement dans la table WEB_PdtNC_RecClt
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Conversion de la date
        date_obj = None
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            except:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    pass
        
        # Générer la référence automatique selon le type
        ref_fich = generer_reference_fichier(type_registre, cursor)
        
        query = """
        INSERT INTO WEB_PdtNC_RecClt 
        (Date, TYPE, NC, DesNC, Cause, Numero_COMMANDES, Reference_COMMANDES, RaiSocTri_SOCIETES, QteComm_COMMANDES, QteNC, CaracNC, RefFich)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            date_obj,
            type_registre,
            nc,
            des_nc,
            cause,
            numero_commandes,
            reference_commandes,
            raisoctri_societes,
            qte_comm_commandes,
            qte_nc,
            carac_nc,
            ref_fich
        ))
        
        conn.commit()
        return True, "Enregistrement ajouté avec succès"
        
    except Exception as e:
        print(f"Erreur lors de l'ajout de l'enregistrement : {e}")
        return False, f"Erreur : {e}"
    finally:
        cursor.close()
        conn.close()

def get_liste_enregistrements(type_registre=None):
    """
    Récupère la liste des enregistrements de WEB_PdtNC_RecClt
    Si type_registre est fourni, filtre par type
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if type_registre:
            query = """
            SELECT ID, Date, TYPE, NC, DesNC, Cause, 
                   Numero_COMMANDES, Reference_COMMANDES, RaiSocTri_SOCIETES,
                   QteComm_COMMANDES, QteNC, CaracNC, RefFich
            FROM WEB_PdtNC_RecClt
            WHERE TYPE = ?
            ORDER BY Date DESC, ID DESC
            """
            cursor.execute(query, (type_registre,))
        else:
            query = """
            SELECT ID, Date, TYPE, NC, DesNC, Cause, 
                   Numero_COMMANDES, Reference_COMMANDES, RaiSocTri_SOCIETES,
                   QteComm_COMMANDES, QteNC, CaracNC, RefFich
            FROM WEB_PdtNC_RecClt
            ORDER BY Date DESC, ID DESC
            """
            cursor.execute(query)
        
        enregistrements = []
        for row in cursor.fetchall():
            # Vérifier si un contrôle qualité existe pour ce numéro
            has_controle_qualite = False
            if row.Numero_COMMANDES:
                numero_clean = row.Numero_COMMANDES.strip() if row.Numero_COMMANDES else ''
                try:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM WEB_CONTROLES_QUALITE 
                        WHERE LTRIM(RTRIM(Numero_COMMANDES)) = ?
                    """, (numero_clean,))
                    count = cursor.fetchone()[0]
                    has_controle_qualite = count > 0
                except:
                    pass
            
            enregistrements.append({
                'ID': row.ID,
                'Date': row.Date.strftime('%d/%m/%Y') if row.Date else '',
                'TYPE': row.TYPE,
                'NC': row.NC,
                'DesNC': row.DesNC,
                'Cause': row.Cause,
                'Numero_COMMANDES': row.Numero_COMMANDES,
                'Reference_COMMANDES': row.Reference_COMMANDES,
                'RaiSocTri_SOCIETES': row.RaiSocTri_SOCIETES,
                'QteComm_COMMANDES': row.QteComm_COMMANDES,
                'QteNC': row.QteNC,
                'CaracNC': row.CaracNC,
                'RefFich': row.RefFich,
                'has_controle_qualite': has_controle_qualite
            })
        
        return enregistrements
        
    except Exception as e:
        print(f"Erreur lors de la récupération des enregistrements : {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def supprimer_enregistrement(id_enregistrement):
    """
    Supprime un enregistrement de la table WEB_PdtNC_RecClt
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "DELETE FROM WEB_PdtNC_RecClt WHERE ID = ?"
        cursor.execute(query, (id_enregistrement,))
        conn.commit()
        return True, "Enregistrement supprimé avec succès"
        
    except Exception as e:
        print(f"Erreur lors de la suppression : {e}")
        return False, f"Erreur : {e}"
    finally:
        cursor.close()
        conn.close()

def modifier_enregistrement(id_enregistrement, date_str, type_registre, nc, des_nc, cause,
                           numero_commandes, reference_commandes, raisoctri_societes,
                           qte_comm_commandes=None, qte_nc=None, carac_nc=None):
    """
    Modifie un enregistrement dans la table WEB_PdtNC_RecClt
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Conversion de la date
        date_obj = None
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            except:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    pass
        
        query = """
        UPDATE WEB_PdtNC_RecClt 
        SET Date = ?, TYPE = ?, NC = ?, DesNC = ?, Cause = ?, 
            Numero_COMMANDES = ?, Reference_COMMANDES = ?, RaiSocTri_SOCIETES = ?,
            QteComm_COMMANDES = ?, QteNC = ?, CaracNC = ?
        WHERE ID = ?
        """
        
        cursor.execute(query, (
            date_obj,
            type_registre,
            nc,
            des_nc,
            cause,
            numero_commandes,
            reference_commandes,
            raisoctri_societes,
            qte_comm_commandes,
            qte_nc,
            carac_nc,
            id_enregistrement
        ))
        
        conn.commit()
        return True, "Enregistrement modifié avec succès"
        
    except Exception as e:
        print(f"Erreur lors de la modification : {e}")
        return False, f"Erreur : {e}"
    finally:
        cursor.close()
        conn.close()

def get_enregistrement_par_id(id_enregistrement):
    """
    Récupère un enregistrement spécifique par son ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        SELECT ID, Date, TYPE, NC, DesNC, Cause, 
               Numero_COMMANDES, Reference_COMMANDES, RaiSocTri_SOCIETES,
               QteComm_COMMANDES, QteNC, CaracNC, RefFich
        FROM WEB_PdtNC_RecClt
        WHERE ID = ?
        """
        cursor.execute(query, (id_enregistrement,))
        row = cursor.fetchone()
        
        if row:
            return {
                'ID': row.ID,
                'Date': row.Date.strftime('%d/%m/%Y') if row.Date else '',
                'TYPE': row.TYPE,
                'NC': row.NC,
                'DesNC': row.DesNC,
                'Cause': row.Cause,
                'Numero_COMMANDES': row.Numero_COMMANDES,
                'Reference_COMMANDES': row.Reference_COMMANDES,
                'RaiSocTri_SOCIETES': row.RaiSocTri_SOCIETES,
                'QteComm_COMMANDES': row.QteComm_COMMANDES,
                'QteNC': row.QteNC,
                'CaracNC': row.CaracNC,
                'RefFich': row.RefFich
            }
        else:
            return None
            
    except Exception as e:
        print(f"Erreur lors de la récupération de l'enregistrement : {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def generer_pdf_fiche(id_enregistrement):
    """
    Génère un PDF pour une fiche d'enregistrement
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from io import BytesIO
        
        # Récupérer l'enregistrement
        enreg = get_enregistrement_par_id(id_enregistrement)
        if not enreg:
            return None, None
        
        # Créer le buffer PDF
        buffer = BytesIO()
        
        # Créer le document
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10
        )
        
        # Titre
        type_label = "Produit Non Conforme" if enreg['TYPE'] == 'NC' else "Réclamation Client"
        type_emoji = "🔴" if enreg['TYPE'] == 'NC' else "📞"
        title = Paragraph(f"Fiche {type_label}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        # Informations de base
        carac_display = ''
        if enreg['CaracNC']:
            carac_display = 'Majeur' if enreg['CaracNC'] == 'Majeur' else 'Mineur'
        
        data = [
            ['N° Enregistrement:', str(enreg['ID'])],
            ['Date:', enreg['Date'] or '-'],
            ['Référence Fichier:', enreg['RefFich'] or '-'],
            ['N° de Dossier:', enreg['Numero_COMMANDES'] or '-'],
            ['Client:', enreg['RaiSocTri_SOCIETES'] or '-'],
            ['Référence:', enreg['Reference_COMMANDES'] or '-'],
            ['Quantité Commande:', str(enreg['QteComm_COMMANDES']) if enreg['QteComm_COMMANDES'] else '-'],
            ['Quantité NC:', str(enreg['QteNC']) if enreg['QteNC'] else '-'],
            ['Caractéristique NC:', carac_display or '-'],
        ]
        
        table = Table(data, colWidths=[5*cm, 12*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7'))
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 1*cm))
        
        # NC
        if enreg['NC']:
            elements.append(Paragraph('<b>NC:</b>', header_style))
            elements.append(Paragraph(enreg['NC'], styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))
        
        # Description
        if enreg['DesNC']:
            elements.append(Paragraph('<b>Description de la NC:</b>', header_style))
            elements.append(Paragraph(enreg['DesNC'], styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))
        
        # Cause
        if enreg['Cause']:
            elements.append(Paragraph('<b>Cause:</b>', header_style))
            elements.append(Paragraph(enreg['Cause'], styles['Normal']))
        
        # Générer le PDF
        doc.build(elements)
        
        # Récupérer le contenu
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Nom du fichier
        filename = f"Fiche_{enreg['TYPE']}_{enreg['ID']}_{enreg['Date'].replace('/', '-')}.pdf"
        
        return pdf_content, filename
        
    except ImportError:
        print("ERREUR: reportlab n'est pas installé. Installez-le avec 'pip install reportlab'")
        return None, None
    except Exception as e:
        print(f"Erreur lors de la génération du PDF : {e}")
        import traceback
        traceback.print_exc()
        return None, None

# ============================================================================
# FONCTIONS STATISTIQUES
# ============================================================================

def get_statistiques_kpi(date_debut=None, date_fin=None):
    """
    Récupère les indicateurs clés (KPI) pour les cartes résumé
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Construire la clause WHERE pour les dates
        where_clause = "WHERE 1=1"
        params = []
        
        if date_debut:
            where_clause += " AND Date >= ?"
            params.append(date_debut)
        if date_fin:
            where_clause += " AND Date <= ?"
            params.append(date_fin)
        
        # Requête pour les KPI actuels
        query = f"""
        SELECT 
            COUNT(CASE WHEN TYPE = 'NC' THEN 1 END) as nb_nc,
            COUNT(CASE WHEN TYPE = 'REC' THEN 1 END) as nb_rec,
            COUNT(*) as total,
            COUNT(CASE WHEN CaracNC = 'Majeur' THEN 1 END) as nb_majeurs,
            COUNT(CASE WHEN CaracNC = 'Mineur' THEN 1 END) as nb_mineurs,
            SUM(CAST(QteNC AS FLOAT)) as qte_nc_total,
            SUM(CAST(QteComm_COMMANDES AS FLOAT)) as qte_comm_total
        FROM WEB_PdtNC_RecClt
        {where_clause}
        """
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        # Calculer le taux de NC
        taux_nc = 0
        if row.qte_nc_total and row.qte_comm_total and row.qte_comm_total > 0:
            taux_nc = (row.qte_nc_total / row.qte_comm_total) * 100
        
        # Calculer les KPI de la période précédente pour comparaison
        if date_debut and date_fin:
            from datetime import datetime, timedelta
            debut = datetime.strptime(date_debut, '%Y-%m-%d')
            fin = datetime.strptime(date_fin, '%Y-%m-%d')
            duree = (fin - debut).days
            
            date_debut_prev = (debut - timedelta(days=duree)).strftime('%Y-%m-%d')
            date_fin_prev = (debut - timedelta(days=1)).strftime('%Y-%m-%d')
            
            query_prev = """
            SELECT 
                COUNT(CASE WHEN TYPE = 'NC' THEN 1 END) as nb_nc,
                COUNT(CASE WHEN TYPE = 'REC' THEN 1 END) as nb_rec,
                SUM(CAST(QteNC AS FLOAT)) as qte_nc_total,
                SUM(CAST(QteComm_COMMANDES AS FLOAT)) as qte_comm_total
            FROM WEB_PdtNC_RecClt
            WHERE Date >= ? AND Date <= ?
            """
            
            cursor.execute(query_prev, (date_debut_prev, date_fin_prev))
            row_prev = cursor.fetchone()
            
            # Calculer les évolutions
            evol_nc = 0
            evol_rec = 0
            evol_taux = 0
            
            if row_prev.nb_nc and row_prev.nb_nc > 0:
                evol_nc = ((row.nb_nc - row_prev.nb_nc) / row_prev.nb_nc) * 100
            
            if row_prev.nb_rec and row_prev.nb_rec > 0:
                evol_rec = ((row.nb_rec - row_prev.nb_rec) / row_prev.nb_rec) * 100
            
            taux_nc_prev = 0
            if row_prev.qte_nc_total and row_prev.qte_comm_total and row_prev.qte_comm_total > 0:
                taux_nc_prev = (row_prev.qte_nc_total / row_prev.qte_comm_total) * 100
                if taux_nc_prev > 0:
                    evol_taux = ((taux_nc - taux_nc_prev) / taux_nc_prev) * 100
        else:
            evol_nc = 0
            evol_rec = 0
            evol_taux = 0
        
        return {
            'nb_nc': row.nb_nc or 0,
            'nb_rec': row.nb_rec or 0,
            'total': row.total or 0,
            'nb_majeurs': row.nb_majeurs or 0,
            'nb_mineurs': row.nb_mineurs or 0,
            'taux_nc': round(taux_nc, 2),
            'evol_nc': round(evol_nc, 1),
            'evol_rec': round(evol_rec, 1),
            'evol_taux': round(evol_taux, 1)
        }
        
    except Exception as e:
        print(f"Erreur lors de la récupération des KPI : {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()

def get_evolution_temporelle(nb_mois=6):
    """
    Récupère l'évolution du nombre de NC et réclamations sur les N derniers mois
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        SELECT 
            FORMAT(Date, 'yyyy-MM') as Mois,
            COUNT(CASE WHEN TYPE = 'NC' THEN 1 END) as NombreNC,
            COUNT(CASE WHEN TYPE = 'REC' THEN 1 END) as NombreREC,
            SUM(CAST(QteNC AS FLOAT)) as QteNC,
            SUM(CAST(QteComm_COMMANDES AS FLOAT)) as QteComm
        FROM WEB_PdtNC_RecClt
        WHERE Date >= DATEADD(MONTH, -?, GETDATE())
        GROUP BY FORMAT(Date, 'yyyy-MM')
        ORDER BY Mois
        """
        
        cursor.execute(query, (nb_mois,))
        
        resultats = []
        for row in cursor.fetchall():
            taux_nc = 0
            if row.QteNC and row.QteComm and row.QteComm > 0:
                taux_nc = (row.QteNC / row.QteComm) * 100
            
            resultats.append({
                'mois': row.Mois,
                'nb_nc': row.NombreNC or 0,
                'nb_rec': row.NombreREC or 0,
                'taux_nc': round(taux_nc, 2)
            })
        
        return resultats
        
    except Exception as e:
        print(f"Erreur lors de la récupération de l'évolution : {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        cursor.close()
        conn.close()

def get_top_clients(limit=10, date_debut=None, date_fin=None):
    """
    Récupère le top N des clients avec le plus de NC/REC
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        where_clause = "WHERE RaiSocTri_SOCIETES IS NOT NULL"
        params = []
        
        if date_debut:
            where_clause += " AND Date >= ?"
            params.append(date_debut)
        if date_fin:
            where_clause += " AND Date <= ?"
            params.append(date_fin)
        
        params.append(limit)
        
        query = f"""
        SELECT TOP (?)
            RaiSocTri_SOCIETES as Client,
            COUNT(CASE WHEN TYPE = 'NC' THEN 1 END) as NombreNC,
            COUNT(CASE WHEN TYPE = 'REC' THEN 1 END) as NombreREC,
            COUNT(*) as Total,
            SUM(CAST(QteNC AS FLOAT)) as QteNCTotal,
            SUM(CAST(QteComm_COMMANDES AS FLOAT)) as QteCommTotal
        FROM WEB_PdtNC_RecClt
        {where_clause}
        GROUP BY RaiSocTri_SOCIETES
        ORDER BY Total DESC
        """
        
        # Déplacer limit au début des params
        params_ordered = [params[-1]] + params[:-1]
        cursor.execute(query, params_ordered)
        
        resultats = []
        for row in cursor.fetchall():
            taux_nc = 0
            if row.QteNCTotal and row.QteCommTotal and row.QteCommTotal > 0:
                taux_nc = (row.QteNCTotal / row.QteCommTotal) * 100
            
            resultats.append({
                'client': row.Client,
                'nb_nc': row.NombreNC or 0,
                'nb_rec': row.NombreREC or 0,
                'total': row.Total or 0,
                'taux_nc': round(taux_nc, 2)
            })
        
        return resultats
        
    except Exception as e:
        print(f"Erreur lors de la récupération du top clients : {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        cursor.close()
        conn.close()

def get_analyse_causes(limit=10, date_debut=None, date_fin=None):
    """
    Récupère les principales causes de NC
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        where_clause = "WHERE TYPE = 'NC' AND Cause IS NOT NULL AND Cause != ''"
        params = []
        
        if date_debut:
            where_clause += " AND Date >= ?"
            params.append(date_debut)
        if date_fin:
            where_clause += " AND Date <= ?"
            params.append(date_fin)
        
        params.append(limit)
        
        query = f"""
        SELECT TOP (?)
            Cause,
            COUNT(*) as Nombre
        FROM WEB_PdtNC_RecClt
        {where_clause}
        GROUP BY Cause
        ORDER BY Nombre DESC
        """
        
        # Déplacer limit au début des params
        params_ordered = [params[-1]] + params[:-1]
        cursor.execute(query, params_ordered)
        
        resultats = []
        total = 0
        
        for row in cursor.fetchall():
            resultats.append({
                'cause': row.Cause,
                'nombre': row.Nombre
            })
            total += row.Nombre
        
        # Calculer les pourcentages
        for item in resultats:
            if total > 0:
                item['pourcentage'] = round((item['nombre'] / total) * 100, 1)
            else:
                item['pourcentage'] = 0
        
        return resultats
        
    except Exception as e:
        print(f"Erreur lors de l'analyse des causes : {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        cursor.close()
        conn.close()

def get_comparaison_periodes(date_debut_1, date_fin_1, date_debut_2, date_fin_2):
    """
    Compare deux périodes distinctes
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        SELECT 
            COUNT(CASE WHEN TYPE = 'NC' THEN 1 END) as nb_nc,
            COUNT(CASE WHEN TYPE = 'REC' THEN 1 END) as nb_rec,
            COUNT(CASE WHEN CaracNC = 'Majeur' THEN 1 END) as nb_majeurs,
            SUM(CAST(QteNC AS FLOAT)) as qte_nc_total,
            SUM(CAST(QteComm_COMMANDES AS FLOAT)) as qte_comm_total
        FROM WEB_PdtNC_RecClt
        WHERE Date >= ? AND Date <= ?
        """
        
        # Période 1
        cursor.execute(query, (date_debut_1, date_fin_1))
        row1 = cursor.fetchone()
        
        taux_nc_1 = 0
        if row1.qte_nc_total and row1.qte_comm_total and row1.qte_comm_total > 0:
            taux_nc_1 = (row1.qte_nc_total / row1.qte_comm_total) * 100
        
        # Période 2
        cursor.execute(query, (date_debut_2, date_fin_2))
        row2 = cursor.fetchone()
        
        taux_nc_2 = 0
        if row2.qte_nc_total and row2.qte_comm_total and row2.qte_comm_total > 0:
            taux_nc_2 = (row2.qte_nc_total / row2.qte_comm_total) * 100
        
        # Calcul des évolutions
        evol_nc = 0
        evol_rec = 0
        evol_majeurs = 0
        evol_taux = 0
        
        if row2.nb_nc and row2.nb_nc > 0:
            evol_nc = ((row1.nb_nc - row2.nb_nc) / row2.nb_nc) * 100
        
        if row2.nb_rec and row2.nb_rec > 0:
            evol_rec = ((row1.nb_rec - row2.nb_rec) / row2.nb_rec) * 100
        
        if row2.nb_majeurs and row2.nb_majeurs > 0:
            evol_majeurs = ((row1.nb_majeurs - row2.nb_majeurs) / row2.nb_majeurs) * 100
        
        if taux_nc_2 > 0:
            evol_taux = ((taux_nc_1 - taux_nc_2) / taux_nc_2) * 100
        
        return {
            'periode_1': {
                'nb_nc': row1.nb_nc or 0,
                'nb_rec': row1.nb_rec or 0,
                'nb_majeurs': row1.nb_majeurs or 0,
                'taux_nc': round(taux_nc_1, 2)
            },
            'periode_2': {
                'nb_nc': row2.nb_nc or 0,
                'nb_rec': row2.nb_rec or 0,
                'nb_majeurs': row2.nb_majeurs or 0,
                'taux_nc': round(taux_nc_2, 2)
            },
            'evolutions': {
                'evol_nc': round(evol_nc, 1),
                'evol_rec': round(evol_rec, 1),
                'evol_majeurs': round(evol_majeurs, 1),
                'evol_taux': round(evol_taux, 1)
            }
        }
        
    except Exception as e:
        print(f"Erreur lors de la comparaison des périodes : {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()

