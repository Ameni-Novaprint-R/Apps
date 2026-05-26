# -*- coding: utf-8 -*-
"""Envoi d'e-mails Projet 25 (congés / autorisations). Configuration via variables d'environnement."""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def _smtp_configured():
    return bool(os.environ.get('SMTP_HOST') and os.environ.get('SMTP_FROM'))


def send_email(to_addresses, subject, body_html, body_text=None):
    """
    Envoie un e-mail. Retourne True si envoyé, False si SMTP non configuré ou erreur.
    Variables : SMTP_HOST, SMTP_PORT (587), SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_TLS (1)
    """
    if not to_addresses:
        return False
    if isinstance(to_addresses, str):
        to_addresses = [a.strip() for a in to_addresses.split(',') if a.strip()]
    to_addresses = [a for a in to_addresses if a]
    if not to_addresses:
        return False
    if not _smtp_configured():
        print('[Projet25 email] SMTP non configuré (SMTP_HOST / SMTP_FROM)')
        return False
    try:
        host = os.environ['SMTP_HOST']
        port = int(os.environ.get('SMTP_PORT', '587'))
        user = os.environ.get('SMTP_USER') or ''
        password = os.environ.get('SMTP_PASSWORD') or ''
        from_addr = os.environ['SMTP_FROM']
        use_tls = os.environ.get('SMTP_TLS', '1') != '0'

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addresses)
        if body_text:
            msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(body_html or body_text or '', 'html', 'utf-8'))

        with smtplib.SMTP(host, port, timeout=15) as server:
            if use_tls:
                server.starttls()
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, to_addresses, msg.as_string())
        return True
    except Exception as e:
        print(f'[Projet25 email] Erreur envoi: {e}')
        return False
