import os
import sys

# Détermine le chemin de base de manière robuste pour le développement et pour PyInstaller
if getattr(sys, 'frozen', False):
    # Si l'application est "gelée" (exécutable), le chemin de base est le dossier de l'exécutable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # En mode développement, le chemin de base est le dossier parent de 'scripts'
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Chemins construits à partir de la racine du projet pour être robustes
FACTURES_DIR = os.path.join(BASE_DIR, "factures")
SRC_DIR = os.path.join(BASE_DIR, "src")
FRAIS_DIR = os.path.join(BASE_DIR, "frais")
BUDGET_DIR = os.path.join(BASE_DIR, "budget")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
ATTESTATIONS_DIR = os.path.join(BASE_DIR, "attestations")
AGENDA_DIR = os.path.join(BASE_DIR, "agenda")