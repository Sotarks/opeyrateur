import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from . import settings_manager

def send_email_with_attachments(recipient_email, subject, body, attachment_paths):
    """Envoie un email avec une pièce jointe via le serveur SMTP configuré."""
    config = settings_manager.get_email_config()
    sender_email = config.get('sender_email')
    sender_password = config.get('sender_password')
    smtp_server = config.get('smtp_server')
    try:
        smtp_port = int(config.get('smtp_port', 587))
    except ValueError:
        smtp_port = 587

    if not sender_email or not sender_password:
        return False, "L'adresse email ou le mot de passe d'application n'est pas configuré dans les réglages."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachment_paths:
        for path in attachment_paths:
            if path and os.path.exists(path):
                try:
                    with open(path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
                    msg.attach(part)
                except Exception as e:
                    return False, f"Erreur lors de la lecture de la pièce jointe {os.path.basename(path)} : {e}"
            # On ignore silencieusement les fichiers introuvables s'il y en a d'autres valides, ou on pourrait lever une erreur.

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, "Email envoyé avec succès."
    except smtplib.SMTPAuthenticationError:
        return False, "Erreur d'authentification. Vérifiez votre mot de passe d'application (pas votre mot de passe habituel)."
    except Exception as e:
        return False, f"Erreur lors de l'envoi : {e}"

def send_email_with_attachment(recipient_email, subject, body, attachment_path):
    """Wrapper pour compatibilité."""
    return send_email_with_attachments(recipient_email, subject, body, [attachment_path])
