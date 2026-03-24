import configparser
import hashlib
import os
from opeyrateur_app.core import config as app_config

CONFIG_FILE = os.path.join(app_config.BASE_DIR, 'settings.ini')
DEFAULT_PIN = "2808"

def _hash_pin(pin, salt):
    """Hache le code PIN avec le sel donné en utilisant un algorithme robuste."""
    pwd_hash = hashlib.pbkdf2_hmac('sha256', pin.encode('utf-8'), salt, 100000)
    return pwd_hash

def _get_pin_config():
    """Lit la configuration du code PIN depuis le fichier .ini."""
    parser = configparser.ConfigParser()
    parser.read(CONFIG_FILE)
    if 'PIN' in parser:
        stored_hash_hex = parser['PIN'].get('hash')
        salt_hex = parser['PIN'].get('salt')
        if stored_hash_hex and salt_hex:
            return bytes.fromhex(stored_hash_hex), bytes.fromhex(salt_hex)
    return None, None

def _save_pin(pin):
    """Hache et sauvegarde un code PIN dans le fichier de configuration."""
    parser = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        parser.read(CONFIG_FILE, encoding='utf-8')
    
    if not parser.has_section('PIN'):
        parser.add_section('PIN')

    salt = os.urandom(16)
    hashed_pin = _hash_pin(pin, salt)
    
    parser.set('PIN', 'hash', hashed_pin.hex())
    parser.set('PIN', 'salt', salt.hex())
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
        parser.write(configfile)

def setup_pin_if_needed():
    """Crée ou met à jour la section PIN dans le fichier de configuration si elle n'existe pas."""
    parser = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        parser.read(CONFIG_FILE, encoding='utf-8')

    if not parser.has_section('PIN') or not parser.has_option('PIN', 'hash') or not parser.has_option('PIN', 'salt'):
        _save_pin(DEFAULT_PIN)

def verify_pin(pin_attempt):
    """Vérifie le code PIN saisi en comparant les empreintes."""
    stored_hash, salt = _get_pin_config()
    if not stored_hash or not salt:
        # Si le fichier est corrompu, on le réinitialise avec le code par défaut
        setup_pin_if_needed()
        stored_hash, salt = _get_pin_config()

    if not stored_hash or not salt:
        return False

    attempt_hash = _hash_pin(pin_attempt, salt)
    return attempt_hash == stored_hash

def change_pin(current_pin, new_pin, confirm_pin):
    """Tente de changer le code PIN. Retourne un tuple (bool, str) indiquant le succès et un message."""
    if not verify_pin(current_pin):
        return (False, "Le code PIN actuel est incorrect.")
    if not new_pin or len(new_pin) < 4:
        return (False, "Le nouveau code PIN doit contenir au moins 4 chiffres.")
    if new_pin != confirm_pin:
        return (False, "Les nouveaux codes PIN ne correspondent pas.")
    try:
        _save_pin(new_pin)
        return (True, "Le code PIN a été modifié avec succès.")
    except Exception as e:
        return (False, f"Une erreur est survenue lors de la sauvegarde : {e}")