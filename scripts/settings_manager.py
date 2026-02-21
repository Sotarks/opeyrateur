import configparser
import os
import json
from . import config as app_config

CONFIG_FILE = os.path.join(app_config.BASE_DIR, 'settings.ini')

# --- Caches au niveau du module pour éviter les lectures de disque répétées ---
_parser_cache = None
_settings_cache = {}

# Dictionnaire des valeurs par défaut
DEFAULT_SETTINGS = {
    'PDFInfo': {
        'company_name': "Maison du Chemin Vert",
        'address_line1': "67 bis rue du Chemin Vert",
        'address_line2': "62 220 CARVIN",
        'siret': "99944616400017",
        'rpps': "10111668322",
        'practitioner_name': "Alaïs Peyrat",
        'practitioner_title': "Psychologue clinicienne",
        'phone_number': "06.71.58.43.12",
        'email': "",
        'attestation_city': "Carvin",
        'attestation_message': "Je soussignée, {practitioner_name}, {practitioner_title}, atteste avoir reçu {gender} {patient_name} en rendez-vous pour un suivi psychologique, en date du {consultation_date}.",
        'prestations': json.dumps({
            "1ère consultation enfants et adolescents": 75.0,
            "Consultation de suivi enfants": 55.0,
            "Consultation de suivi adolescents": 60.0,
            "Consultation adulte": 60.0,
            "Consultation familiale": 75.0,
            "Consultation de couple": 75.0
        }, indent=4)
    },
    'Expenses': {
        'recurring': json.dumps([
            {"Categorie": "Loyer", "Description": "Loyer / Cabinet", "Montant": 560.0, "ProofPath": ""},
            {"Categorie": "Cotisations", "Description": "Doctolib", "Montant": 149.0, "ProofPath": ""},
            {"Categorie": "Cotisations", "Description": "Responsabilité civile pro", "Montant": 12.5, "ProofPath": ""},
            {"Categorie": "Cotisations", "Description": "Assurance cabinet", "Montant": 11.4, "ProofPath": ""},
            {"Categorie": "Autre", "Description": "Téléphone", "Montant": 1.99, "ProofPath": ""},
            {"Categorie": "Déplacement", "Description": "Essence", "Montant": 120.0, "ProofPath": ""},
            {"Categorie": "Cotisations", "Description": "Mutuelle", "Montant": 5.0, "ProofPath": ""},
            {"Categorie": "Repas (seule)", "Description": "Nourriture", "Montant": 80.0, "ProofPath": ""}
        ])
    }
}

def _get_parser():
    """Lit le fichier de configuration et le retourne, en utilisant un cache."""
    global _parser_cache
    if _parser_cache is None:
        _parser_cache = configparser.ConfigParser()
        _parser_cache.read(CONFIG_FILE, encoding='utf-8')
    return _parser_cache

def _invalidate_caches():
    """Invalide les caches pour forcer une relecture depuis le disque."""
    global _parser_cache, _settings_cache
    _parser_cache = None
    _settings_cache = {}

def setup_default_settings():
    """Crée ou met à jour le fichier de configuration avec les valeurs par défaut si elles manquent."""
    parser = _get_parser()
    needs_saving = False
    for section, defaults in DEFAULT_SETTINGS.items():
        if not parser.has_section(section):
            parser.add_section(section)
            needs_saving = True
        for key, value in defaults.items():
            if not parser.has_option(section, key):
                parser.set(section, key, value)
                needs_saving = True

    if needs_saving:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
            parser.write(configfile)
        _invalidate_caches()

def get_pdf_info():
    """Récupère toutes les informations PDF depuis le fichier de configuration, en utilisant un cache."""
    if 'pdf_info' in _settings_cache:
        return _settings_cache['pdf_info']

    setup_default_settings()
    parser = _get_parser()
    pdf_info = {}
    defaults = DEFAULT_SETTINGS['PDFInfo']
    for key, default_value in defaults.items():
        pdf_info[key] = parser.get('PDFInfo', key, fallback=default_value)
    
    _settings_cache['pdf_info'] = pdf_info
    return pdf_info

def save_pdf_info(data):
    """Sauvegarde les informations PDF dans le fichier de configuration."""
    parser = _get_parser() # Assure que le parser est chargé
    if not parser.has_section('PDFInfo'):
        parser.add_section('PDFInfo')
    for key, value in data.items():
        parser.set('PDFInfo', key, str(value))
    with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
        parser.write(configfile)

    _invalidate_caches()

def get_prestations():
    """Récupère la liste des prestations et prix depuis la configuration."""
    setup_default_settings()
    parser = _get_parser()
    try:
        prestations_str = parser.get('PDFInfo', 'prestations', fallback='{}')
        return json.loads(prestations_str)
    except (json.JSONDecodeError, configparser.Error):
        # En cas d'erreur, retourne le dictionnaire par défaut
        return json.loads(DEFAULT_SETTINGS['PDFInfo']['prestations'])

def get_recurring_expenses():
    """Récupère la liste des frais récurrents."""
    setup_default_settings()
    parser = _get_parser()
    try:
        data_str = parser.get('Expenses', 'recurring', fallback='[]')
        return json.loads(data_str)
    except (json.JSONDecodeError, configparser.Error):
        return json.loads(DEFAULT_SETTINGS['Expenses']['recurring'])

def save_recurring_expenses(data):
    """Sauvegarde la liste des frais récurrents."""
    parser = _get_parser()
    if not parser.has_section('Expenses'):
        parser.add_section('Expenses')
    parser.set('Expenses', 'recurring', json.dumps(data))
    with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
        parser.write(configfile)
    _invalidate_caches()

def get_last_recurring_run():
    """Récupère le mois de la dernière génération automatique (format YYYY-MM)."""
    setup_default_settings()
    parser = _get_parser()
    return parser.get('Expenses', 'last_run', fallback='')

def set_last_recurring_run(date_str):
    """Sauvegarde le mois de la dernière génération automatique."""
    parser = _get_parser()
    if not parser.has_section('Expenses'):
        parser.add_section('Expenses')
    parser.set('Expenses', 'last_run', date_str)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
        parser.write(configfile)
    _invalidate_caches()