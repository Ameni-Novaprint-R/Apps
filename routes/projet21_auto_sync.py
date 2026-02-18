"""
Module de synchronisation automatique pour Projet 21
Gère la planification quotidienne à 05:00 AM et les notifications par email
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

# Configuration email
# Pour configurer le mot de passe SMTP, utiliser la variable d'environnement SMTP_PASSWORD
# ou modifier directement sender_password ci-dessous (non recommandé pour la sécurité)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # À adapter selon votre serveur SMTP (ex: smtp.office365.com pour Outlook)
    'smtp_port': 587,
    'sender_email': 'ameni.compta@novaprint.tn',  # Email expéditeur
    'sender_password': '',  # Mot de passe - Récupéré depuis SMTP_PASSWORD ou à configurer ici
    'recipient_email': 'ameni.compta@novaprint.tn'
}

# Dossier pour stocker les résultats JSON
# Utiliser le répertoire racine du projet (où se trouve app.py)
import sys
import os

# Déterminer le répertoire racine du projet
# Si exécuté depuis routes/, remonter d'un niveau
# Si exécuté depuis la racine, utiliser le répertoire courant
current_file = Path(__file__).resolve()
if current_file.parent.name == 'routes':
    # Le fichier est dans routes/, remonter à la racine
    BASE_DIR = current_file.parent.parent
else:
    # Le fichier est ailleurs, utiliser le répertoire courant
    BASE_DIR = Path.cwd()

# Vérifier si on est dans C:\Apps (structure réelle)
# Si le script est exécuté depuis C:\Apps\routes\, BASE_DIR devrait être C:\Apps
if BASE_DIR.name == 'routes':
    BASE_DIR = BASE_DIR.parent

RESULTS_DIR = BASE_DIR / 'sync_results'
RESULTS_FILE = RESULTS_DIR / 'last_auto_sync_result.json'
CONFIG_FILE = RESULTS_DIR / 'auto_sync_config.json'

# Créer le dossier s'il n'existe pas (avec parents pour créer toute l'arborescence)
try:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Dossier de résultats vérifié/créé: {RESULTS_DIR}")
except Exception as e:
    print(f"⚠️ Erreur lors de la création du dossier de résultats: {e}")
    print(f"   Tentative de création dans: {RESULTS_DIR}")

# Debug: afficher le chemin utilisé
print(f"📁 Dossier de résultats: {RESULTS_DIR}")

def load_auto_sync_config():
    """Charge la configuration de synchronisation automatique"""
    default_config = {
        'enabled': True,
        'last_run': None,
        'last_status': None
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        except Exception as e:
            print(f"Erreur lors du chargement de la config: {e}")
    
    return default_config

def save_auto_sync_config(config):
    """Sauvegarde la configuration de synchronisation automatique"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la config: {e}")

def is_auto_sync_enabled():
    """Vérifie si la synchronisation automatique est activée"""
    config = load_auto_sync_config()
    return config.get('enabled', True)

def set_auto_sync_enabled(enabled):
    """Active ou désactive la synchronisation automatique"""
    config = load_auto_sync_config()
    config['enabled'] = enabled
    save_auto_sync_config(config)
    return config

def save_verification_result(results, sync_success=True):
    """
    Sauvegarde TOUJOURS le résultat de vérification pour l'affichage dans l'interface.
    Retourne True si des problèmes ont été détectés (hors GS_INVENTAIRES) pour l'envoi d'email.
    """
    # Vérifier s'il y a des problèmes (hors GS_INVENTAIRES)
    has_problems = False
    
    # Vérifier les écarts critiques (hors GS_INVENTAIRES)
    ecarts_critiques = results.get('ecarts_critiques', [])
    for item in ecarts_critiques:
        if len(item) >= 1 and item[0] != 'GS_INVENTAIRES':
            has_problems = True
            break
    
    # Vérifier les doublons de PK
    if results.get('doublons_pk'):
        has_problems = True
    
    # Vérifier les tables manquantes dans la cible
    if results.get('manquantes_cible'):
        has_problems = True
    
    # TOUJOURS sauvegarder le résultat pour l'affichage dans l'interface
    result_data = {
        'timestamp': datetime.now().isoformat(),
        'sync_success': sync_success,
        'results': results,
        'has_problems': has_problems
    }
    
    try:
        # S'assurer que le dossier existe
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"📁 Dossier de résultats: {RESULTS_DIR}")
        print(f"📄 Fichier de résultats: {RESULTS_FILE}")
        
        # Sauvegarder le résultat
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Résultat sauvegardé avec succès dans: {RESULTS_FILE}")
        print(f"   Timestamp: {result_data['timestamp']}")
        
        # Mettre à jour la config
        config = load_auto_sync_config()
        config['last_run'] = datetime.now().isoformat()
        config['last_status'] = 'success' if sync_success and not has_problems else 'error'
        save_auto_sync_config(config)
        
        # Retourner True si des problèmes détectés (pour l'envoi d'email)
        return has_problems
    except Exception as e:
        import traceback
        error_msg = f"Erreur lors de la sauvegarde du résultat: {e}"
        print(error_msg)
        print(f"   Dossier attendu: {RESULTS_DIR}")
        print(f"   Fichier attendu: {RESULTS_FILE}")
        print(f"   Traceback: {traceback.format_exc()}")
        # Relancer l'erreur pour qu'elle soit visible dans les logs Task Scheduler
        raise
        return False

def load_last_verification_result():
    """Charge le dernier résultat de vérification automatique"""
    if not RESULTS_FILE.exists():
        return None
    
    try:
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement du dernier résultat: {e}")
        return None

def send_email_notification(subject, body, is_html=False):
    """
    Envoie une notification par email
    Retourne True si l'envoi réussit, False sinon
    """
    try:
        # Si pas de mot de passe configuré, essayer de le récupérer depuis les variables d'environnement
        sender_password = EMAIL_CONFIG['sender_password']
        if not sender_password:
            sender_password = os.environ.get('SMTP_PASSWORD', '')
        
        if not sender_password:
            print("⚠️ ATTENTION: Mot de passe SMTP non configuré. Email non envoyé.")
            print(f"   Pour configurer: définir la variable d'environnement SMTP_PASSWORD")
            print(f"   Ou modifier EMAIL_CONFIG['sender_password'] dans projet21_auto_sync.py")
            return False
        
        print(f"📧 Envoi d'email à {EMAIL_CONFIG['recipient_email']}...")
        print(f"   Sujet: {subject}")
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']
        msg['Subject'] = subject
        
        if is_html:
            msg.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], sender_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email envoyé avec succès à {EMAIL_CONFIG['recipient_email']}")
        return True
    except Exception as e:
        print(f"❌ ERREUR lors de l'envoi de l'email: {e}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"   Traceback: {error_trace}")
        print(f"   Configuration SMTP:")
        print(f"     Serveur: {EMAIL_CONFIG['smtp_server']}")
        print(f"     Port: {EMAIL_CONFIG['smtp_port']}")
        print(f"     Expéditeur: {EMAIL_CONFIG['sender_email']}")
        print(f"     Destinataire: {EMAIL_CONFIG['recipient_email']}")
        print(f"     Mot de passe configuré: {'Oui' if sender_password else 'Non'}")
        return False

def format_verification_email(results, sync_success=True):
    """Formate le résultat de vérification pour l'email"""
    html_body = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background: #2a5298; color: white; padding: 20px; }}
            .content {{ padding: 20px; }}
            .error {{ background: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 10px 0; }}
            .success {{ background: #e8f5e9; border-left: 4px solid #388e3c; padding: 15px; margin: 10px 0; }}
            .warning {{ background: #fff3e0; border-left: 4px solid #f57c00; padding: 15px; margin: 10px 0; }}
            .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #2a5298; color: white; }}
            pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔔 Notification - Synchronisation Automatique Projet 21</h1>
            <p>Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </div>
        <div class="content">
    """
    
    if not sync_success:
        html_body += """
            <div class="error">
                <h2>❌ Échec de la Synchronisation</h2>
                <p>La synchronisation automatique a échoué. Veuillez vérifier les logs pour plus de détails.</p>
            </div>
        """
    else:
        # Analyser les résultats
        ecarts_critiques = results.get('ecarts_critiques', [])
        doublons_pk = results.get('doublons_pk', [])
        manquantes_cible = results.get('manquantes_cible', [])
        
        # Filtrer GS_INVENTAIRES des écarts critiques
        ecarts_critiques_filtered = [e for e in ecarts_critiques if len(e) >= 1 and e[0] != 'GS_INVENTAIRES']
        
        has_problems = len(ecarts_critiques_filtered) > 0 or len(doublons_pk) > 0 or len(manquantes_cible) > 0
        
        if has_problems:
            html_body += """
                <div class="error">
                    <h2>⚠️ Problèmes Détectés lors de la Vérification</h2>
            """
            
            if ecarts_critiques_filtered:
                html_body += f"""
                    <h3>🔴 Tables avec Enregistrements Manquants ({len(ecarts_critiques_filtered)}):</h3>
                    <ul>
                """
                for item in ecarts_critiques_filtered[:10]:  # Limiter à 10
                    table_name = item[0] if len(item) >= 1 else 'Inconnu'
                    missing_count = item[3] if len(item) >= 4 else 0
                    html_body += f"<li><strong>{table_name}</strong>: {missing_count} enregistrements manquants</li>"
                html_body += "</ul>"
            
            if doublons_pk:
                html_body += f"""
                    <h3>⚠️ Tables avec Doublons de PK ({len(doublons_pk)}):</h3>
                    <ul>
                """
                for item in doublons_pk[:10]:
                    table_name = item[0] if len(item) >= 1 else 'Inconnu'
                    dup_count = item[1] if len(item) >= 2 else 0
                    html_body += f"<li><strong>{table_name}</strong>: {dup_count} PK dupliquées</li>"
                html_body += "</ul>"
            
            if manquantes_cible:
                html_body += f"""
                    <h3>✗ Tables Manquantes dans la Cible ({len(manquantes_cible)}):</h3>
                    <ul>
                """
                for table_name, count in manquantes_cible[:10]:
                    html_body += f"<li><strong>{table_name}</strong>: {count} enregistrements</li>"
                html_body += "</ul>"
            
            html_body += """
                </div>
            """
        else:
            html_body += """
                <div class="success">
                    <h2>✅ Synchronisation Réussie</h2>
                    <p>Toutes les tables sont synchronisées correctement (hors GS_INVENTAIRES qui est acceptable).</p>
                </div>
            """
        
        # Résumé
        summary = results.get('summary', {})
        html_body += f"""
            <div class="summary">
                <h3>📊 Résumé de la Vérification</h3>
                <ul>
                    <li>✓ Tables synchronisées: {summary.get('synchronisees', 0)}</li>
                    <li>🔴 Tables avec enregistrements manquants: {summary.get('ecarts_critiques', 0)}</li>
                    <li>🟢 Tables avec données supplémentaires: {summary.get('ecarts_normaux', 0)}</li>
                    <li>⚠️ Tables avec doublons de PK: {summary.get('doublons_pk', 0)}</li>
                    <li>✗ Tables manquantes dans cible: {summary.get('manquantes_cible', 0)}</li>
                </ul>
            </div>
        """
        
        # Détails complets (dans un bloc préformaté)
        html_body += f"""
            <details>
                <summary style="cursor: pointer; font-weight: bold; margin-top: 20px;">Voir les détails complets</summary>
                <pre>{results.get('output', 'Aucun détail disponible')}</pre>
            </details>
        """
    
    html_body += """
        </div>
    </body>
    </html>
    """
    
    return html_body

def run_auto_sync_and_verify():
    """
    Fonction principale pour exécuter la synchronisation automatique et la vérification
    Cette fonction sera appelée par le scheduler à 05:00 AM
    """
    if not is_auto_sync_enabled():
        print("⏸️ Synchronisation automatique désactivée")
        return
    
    print(f"🔄 Démarrage de la synchronisation automatique - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📁 Fichier de résultats: {RESULTS_FILE}")
    
    sync_success = False
    verification_results = None
    
    try:
        # Importer les fonctions de synchronisation et vérification
        from routes.projet21_routes import sync_databases
        from routes.projet21_verification import verify_sync
        
        # Exécuter la synchronisation
        print("📥 Synchronisation en cours...")
        # sync_databases() modifie sync_status globalement
        sync_databases()
        
        # Attendre un peu pour que la synchronisation se termine
        import time
        from routes.projet21_routes import sync_status as sync_status_global
        
        # Attendre jusqu'à 30 minutes maximum
        max_wait = 1800  # 30 minutes en secondes
        wait_time = 0
        while sync_status_global.get('running', False) and wait_time < max_wait:
            time.sleep(5)
            wait_time += 5
        
        sync_success = not sync_status_global.get('running', False)
        error_msg = sync_status_global.get('message', '')
        
        if sync_success and 'Erreur' not in error_msg:
            print("✓ Synchronisation terminée avec succès")
            
            # Exécuter la vérification
            print("🔍 Vérification en cours...")
            verification_results = verify_sync()
            
            # Sauvegarder TOUJOURS le résultat pour l'affichage dans l'interface
            has_problems = save_verification_result(verification_results, sync_success=True)
            print(f"💾 Résultat sauvegardé dans: {RESULTS_FILE}")
            print(f"   Problèmes détectés: {'Oui' if has_problems else 'Non (synchronisation OK)'}")
            
            # Préparer les résultats pour l'email
            summary = {
                'synchronisees': len(verification_results.get('synchronisees', [])),
                'ecarts_critiques': len(verification_results.get('ecarts_critiques', [])),
                'ecarts_normaux': len(verification_results.get('ecarts_normaux', [])),
                'doublons_pk': len(verification_results.get('doublons_pk', [])),
                'manquantes_cible': len(verification_results.get('manquantes_cible', [])),
                'manquantes_source': len(verification_results.get('manquantes_source', []))
            }
            verification_results['summary'] = summary
            
            # Envoyer un email uniquement s'il y a des problèmes détectés (hors GS_INVENTAIRES)
            # has_problems est déjà calculé dans save_verification_result
            if has_problems:
                subject = "⚠️ Projet 21 - Problèmes détectés lors de la synchronisation automatique"
                email_body = format_verification_email(verification_results, sync_success=True)
                email_sent = send_email_notification(subject, email_body, is_html=True)
                if email_sent:
                    print("✅ Email de problèmes détectés envoyé avec succès")
                else:
                    print("⚠️ Échec de l'envoi de l'email de problèmes détectés - vérifiez la configuration SMTP")
        else:
            sync_success = False
            error_msg = sync_status_global.get('message', 'Erreur inconnue')
            print(f"✗ Synchronisation échouée: {error_msg}")
            
            # Sauvegarder quand même le résultat (même en cas d'échec)
            # pour que l'utilisateur puisse voir ce qui s'est passé
            if verification_results is None:
                # Créer un résultat minimal pour indiquer l'échec
                verification_results = {
                    'synchronisees': [],
                    'ecarts_critiques': [],
                    'ecarts_normaux': [],
                    'doublons_pk': [],
                    'manquantes_cible': [],
                    'manquantes_source': [],
                    'output': f"Erreur lors de la synchronisation: {error_msg}"
                }
            
            # Sauvegarder le résultat d'échec
            try:
                save_verification_result(verification_results, sync_success=False)
                print(f"💾 Résultat d'échec sauvegardé dans: {RESULTS_FILE}")
            except Exception as save_err:
                print(f"⚠️ Impossible de sauvegarder le résultat d'échec: {save_err}")
            
            # ENVOYER UN EMAIL D'ERREUR - CRITIQUE
            subject = "❌ Projet 21 - Échec de la synchronisation automatique"
            error_details = '\n'.join(sync_status_global.get('details', []))
            if not error_details:
                error_details = error_msg
            
            error_email_body = f"""
            <html>
            <head><meta charset="utf-8"></head>
            <body>
                <h2>❌ Échec de la synchronisation automatique</h2>
                <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                <p><strong>Message d'erreur:</strong> {error_msg}</p>
                <details>
                    <summary>Détails techniques</summary>
                    <pre>{error_details}</pre>
                </details>
                <p style="margin-top: 20px; color: #666;">
                    Veuillez vérifier la configuration de la synchronisation et consulter les logs dans le Planificateur de tâches Windows.
                </p>
            </body>
            </html>
            """
            
            email_sent = send_email_notification(subject, error_email_body, is_html=True)
            if email_sent:
                print("✅ Email d'erreur envoyé avec succès")
            else:
                print("⚠️ Échec de l'envoi de l'email d'erreur - vérifiez la configuration SMTP")
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        sync_success = False
        error_msg = str(e)
        print(f"✗ Erreur lors de la synchronisation automatique: {error_msg}")
        print(error_trace)
        
        # Sauvegarder quand même un résultat d'erreur pour l'affichage
        try:
            error_results = {
                'synchronisees': [],
                'ecarts_critiques': [],
                'ecarts_normaux': [],
                'doublons_pk': [],
                'manquantes_cible': [],
                'manquantes_source': [],
                'output': f"Erreur lors de l'exécution: {error_msg}\n\n{error_trace}"
            }
            save_verification_result(error_results, sync_success=False)
            print(f"💾 Résultat d'erreur sauvegardé dans: {RESULTS_FILE}")
        except Exception as save_err:
            print(f"⚠️ Impossible de sauvegarder le résultat d'erreur: {save_err}")
        
        # ENVOYER UN EMAIL D'ERREUR - CRITIQUE
        subject = "❌ Projet 21 - Erreur lors de la synchronisation automatique"
        error_email_body = f"""
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <h2>❌ Erreur lors de l'exécution de la synchronisation automatique</h2>
            <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            <p><strong>Type d'erreur:</strong> {type(e).__name__}</p>
            <p><strong>Message:</strong> {error_msg}</p>
            <details>
                <summary>Traceback complet</summary>
                <pre style="background-color: #f5f5f5; padding: 10px; overflow-x: auto;">{error_trace}</pre>
            </details>
            <p style="margin-top: 20px; color: #666;">
                Veuillez vérifier la configuration de la synchronisation et consulter les logs dans le Planificateur de tâches Windows.
            </p>
        </body>
        </html>
        """
        
        email_sent = send_email_notification(subject, error_email_body, is_html=True)
        if email_sent:
            print("✅ Email d'erreur envoyé avec succès")
        else:
            print("⚠️ Échec de l'envoi de l'email d'erreur - vérifiez la configuration SMTP")
    
    print(f"✓ Synchronisation automatique terminée - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
