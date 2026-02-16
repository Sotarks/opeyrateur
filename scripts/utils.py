import sys
import os

def resource_path(relative_path):
    """
    Récupère le chemin absolu d'une ressource, pour le développement et pour PyInstaller.
    """
    try:
        # PyInstaller crée un dossier temporaire et stocke son chemin dans _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # En mode développement, la base est la racine du projet (le parent de 'scripts')
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    return os.path.join(base_path, relative_path)