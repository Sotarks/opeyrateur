import urllib.request
import urllib.error
import json
import os
import sys
import webbrowser
from tkinter import messagebox
import customtkinter as ctk
import threading
import subprocess
from packaging.version import parse as parse_version
import ssl

# --- Configuration ---
# Cette version doit être mise à jour manuellement à chaque nouvelle release.
APP_VERSION = "1.1.2" 
GITHUB_REPO = "Sotarks/opeyrateur"
API_HEADERS = {
    'User-Agent': 'Opeyrateur-App-Updater/1.0',
    'Accept': 'application/vnd.github.v3+json',
}

def get_executable_name():
    """Récupère le nom de l'exécutable en cours d'exécution."""
    if getattr(sys, 'frozen', False):
        return os.path.basename(sys.executable)
    return None 

def check_for_updates(app_instance):
    """
    Vérifie les nouvelles releases sur GitHub dans un thread séparé.
    Si une mise à jour est trouvée, une notification est affichée.
    """
    def _worker():
        try:
            releases_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
            req = urllib.request.Request(releases_url, headers=API_HEADERS)
            # Utilisation d'un contexte SSL non vérifié pour éviter les erreurs de certificats locaux manquants
            with urllib.request.urlopen(req, timeout=10, context=ssl._create_unverified_context()) as response:
                releases = json.loads(response.read().decode("utf-8"))

            if not releases:
                print("Vérification de mise à jour : Aucune release trouvée.")
                return

            # La première release de la liste est la plus récente
            latest_release = releases[0]
            
            # On nettoie le 'v' du tag pour la comparaison
            latest_version_str = latest_release.get("tag_name", "0.0.0").lstrip('v')
            
            try:
                if parse_version(latest_version_str) > parse_version(APP_VERSION):
                    if app_instance.winfo_exists():
                        app_instance.after(0, lambda: prompt_update(app_instance, latest_release))
            except parse_version.InvalidVersion:
                print(f"Tag de release invalide sur GitHub : '{latest_version_str}'. La comparaison de version est impossible.")

        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"Erreur 404 lors de la vérification auto : Dépôt '{GITHUB_REPO}' introuvable ou privé.")
            else:
                print(f"Erreur HTTP lors de la vérification de mise à jour : {e}")
        except urllib.error.URLError as e:
            print(f"La vérification de mise à jour a échoué : {e}")  # Log silencieux
        except Exception as e:
            print(f"Erreur lors du traitement des données de mise à jour : {e}")

    threading.Thread(target=_worker, daemon=True).start()

def manual_check_for_updates(app_instance, parent_window):
    """
    Vérifie manuellement les mises à jour et affiche un message à l'utilisateur.
    Exécuté dans un thread pour ne pas bloquer l'interface.
    """
    parent_window.configure(cursor="watch")
    app_instance.update_idletasks()

    def _worker():
        try:
            # --- MODE TEST LOCAL ---
            # Mettez à True pour tester. Assurez-vous que TEST_PATH pointe vers un .exe valide.
            TEST_MODE = False
            TEST_PATH = r"C:\REPO\opeyrateur\dist\Opeyrateur.exe" 

            if TEST_MODE:
                import pathlib
                releases = [{
                    "tag_name": "v9.9.9", # Version fictive supérieure
                    "body": "Test de mise à jour locale.\nCeci est une simulation.",
                    "assets": [{
                        "name": get_executable_name(), # Le nom doit correspondre à l'exe actuel
                        "browser_download_url": pathlib.Path(TEST_PATH).as_uri()
                    }]
                }]
            else:
                releases_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
                req = urllib.request.Request(releases_url, headers=API_HEADERS)
                with urllib.request.urlopen(req, timeout=10, context=ssl._create_unverified_context()) as response:
                    releases = json.loads(response.read().decode("utf-8"))

            if not releases:
                if app_instance.winfo_exists():
                    app_instance.after(0, lambda: messagebox.showinfo(
                        "Mise à jour", 
                        "Aucune release n'a été trouvée sur le dépôt GitHub.", 
                        parent=parent_window
                    ))
                return

            latest_release = releases[0]
            
            latest_version_str = latest_release.get("tag_name", "0.0.0").lstrip('v')
            
            try:
                is_newer = parse_version(latest_version_str) > parse_version(APP_VERSION)
            except parse_version.InvalidVersion:
                if app_instance.winfo_exists():
                    app_instance.after(0, lambda: messagebox.showerror(
                        "Erreur de mise à jour",
                        f"Le tag de la dernière release sur GitHub ('{latest_release.get('tag_name')}') n'est pas une version valide.\n\n"
                        f"Veuillez utiliser un tag au format 'vX.Y.Z' (ex: v{APP_VERSION}).",
                        parent=parent_window
                    ))
                return

            if is_newer:
                if app_instance.winfo_exists():
                    app_instance.after(0, lambda: prompt_update(app_instance, latest_release))
            else:
                if app_instance.winfo_exists():
                    app_instance.after(0, lambda: messagebox.showinfo("Mise à jour", "Vous utilisez déjà la version la plus récente.", parent=parent_window))
        
        except urllib.error.HTTPError as e:
            if e.code == 404:
                error_message = (
                    "La ressource est introuvable (Erreur 404).\n\n"
                    "Causes possibles :\n"
                    f"1. Le nom du dépôt GitHub ('{GITHUB_REPO}') est incorrect.\n"
                    "2. Le dépôt GitHub est privé.\n"
                    "3. Un pare-feu ou un proxy bloque la connexion."
                )
                if app_instance.winfo_exists():
                    app_instance.after(0, lambda: messagebox.showerror("Erreur de mise à jour", error_message, parent=parent_window))
            else:
                if app_instance.winfo_exists():
                    app_instance.after(0, lambda e=e: messagebox.showerror(
                        "Erreur de mise à jour", f"Impossible de vérifier les mises à jour (Erreur HTTP) :\n{e}", parent=parent_window
                    ))
        except urllib.error.URLError as e:
            if app_instance.winfo_exists():
                app_instance.after(0, lambda e=e: messagebox.showerror(
                    "Erreur de mise à jour", f"Impossible de vérifier les mises à jour :\n{e}", parent=parent_window
                ))
        except Exception as e:
            if app_instance.winfo_exists():
                app_instance.after(0, lambda e=e: messagebox.showerror(
                    "Erreur inattendue", f"Une erreur est survenue lors de la vérification :\n{e}", parent=parent_window
                ))
        finally:
            if parent_window.winfo_exists():
                app_instance.after(0, lambda: parent_window.configure(cursor=""))

    threading.Thread(target=_worker, daemon=True).start()

def prompt_update(app_instance, release_info):
    """
    Affiche une boîte de dialogue demandant à l'utilisateur de mettre à jour.
    """
    latest_version = release_info.get("tag_name", "v?.?.?")
    release_notes = release_info.get("body", "Pas de notes de version disponibles.")
    
    dialog = ctk.CTkToplevel(app_instance)
    dialog.title("Mise à jour disponible")
    dialog.geometry("500x400")
    dialog.transient(app_instance)
    dialog.grab_set()

    ctk.CTkLabel(dialog, text=f"Une nouvelle version ({latest_version}) est disponible !", font=app_instance.font_large).pack(pady=15)
    
    notes_frame = ctk.CTkScrollableFrame(dialog, label_text="Notes de version")
    notes_frame.pack(fill="both", expand=True, padx=15, pady=10)
    ctk.CTkLabel(notes_frame, text=release_notes, justify="left", wraplength=450, anchor="w").pack(fill="x")

    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(pady=15, fill="x", padx=15)
    btn_frame.grid_columnconfigure((0, 1), weight=1)

    ctk.CTkButton(btn_frame, text="Plus tard", command=dialog.destroy, fg_color="gray50").grid(row=0, column=0, padx=(0, 5), sticky="ew")
    ctk.CTkButton(btn_frame, text="Installer maintenant", command=lambda: start_update(app_instance, release_info, dialog)).grid(row=0, column=1, padx=(5, 0), sticky="ew")

def start_update(app_instance, release_info, parent_dialog):
    """
    Trouve le bon asset, le télécharge, et exécute le script de mise à jour.
    """
    executable_name = get_executable_name()
    if not executable_name:
        messagebox.showerror("Erreur", "La mise à jour automatique ne fonctionne qu'avec la version compilée (.exe) de l'application.", parent=parent_dialog)
        return

    assets = release_info.get("assets", [])
    download_url = None
    for asset in assets:
        if asset.get("name") == executable_name:
            download_url = asset.get("browser_download_url")
            break
    
    if not download_url:
        messagebox.showerror("Erreur de mise à jour", f"Impossible de trouver l'exécutable '{executable_name}' dans la dernière release.", parent=parent_dialog)
        return

    parent_dialog.destroy()

    progress_win = ctk.CTkToplevel(app_instance)
    progress_win.title("Mise à jour en cours...")
    progress_win.geometry("400x180")
    progress_win.transient(app_instance)
    progress_win.grab_set()
    progress_win.protocol("WM_DELETE_WINDOW", lambda: None)

    ctk.CTkLabel(progress_win, text="Téléchargement de la mise à jour...").pack(pady=20)
    progress_bar = ctk.CTkProgressBar(progress_win, width=300, mode="determinate")
    progress_bar.pack(pady=10)
    progress_bar.set(0)

    progress_label = ctk.CTkLabel(progress_win, text="0% (0.0 / 0.0 MB)")
    progress_label.pack(pady=5)
    
    app_instance.withdraw()

    def _download_worker():
        try:
            req = urllib.request.Request(download_url, headers={'User-Agent': API_HEADERS['User-Agent']})
            response = urllib.request.urlopen(req, timeout=60, context=ssl._create_unverified_context())
            total_length = response.getheader('Content-Length')

            if total_length is None: # Pas d'en-tête content-length
                progress_bar.configure(mode="indeterminate")
                progress_bar.start()
                progress_label.configure(text="Taille inconnue, téléchargement en cours...")
            else:
                total_length = int(total_length)

            downloaded_length = 0
            new_exe_path = os.path.join(os.path.dirname(sys.executable), f"new_{executable_name}")

            def update_progress(progress, downloaded_mb, total_mb):
                """Met à jour l'UI de progression depuis le thread principal."""
                if progress_win.winfo_exists():
                    progress_bar.set(progress)
                    progress_label.configure(text=f"{int(progress * 100)}% ({downloaded_mb:.1f} / {total_mb:.1f} MB)")

            with open(new_exe_path, "wb") as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    downloaded_length += len(chunk)
                    f.write(chunk)
                    if total_length:
                        progress = downloaded_length / total_length
                        downloaded_mb = downloaded_length / (1024 * 1024)
                        total_mb = total_length / (1024 * 1024)
                        # Planifie la mise à jour de l'UI dans le thread principal
                        app_instance.after(0, lambda p=progress, d_mb=downloaded_mb, t_mb=total_mb: update_progress(p, d_mb, t_mb))
            
            response.close()
            
            if progress_win.winfo_exists():
                app_instance.after(0, lambda: (
                    progress_label.configure(text="Installation en cours..."),
                    progress_bar.set(1)
                ))

            updater_script_path = os.path.join(os.path.dirname(sys.executable), "updater.bat")
            
            with open(updater_script_path, "w", encoding="utf-8") as f:
                f.write(f'@echo off\n')
                f.write(f'echo Attente de la fermeture de l\'application...\n')
                f.write(f'taskkill /F /IM "{executable_name}" > nul\n')
                f.write(f'timeout /t 2 /nobreak > nul\n')
                f.write(f'echo Remplacement des fichiers...\n')
                f.write(f'move /Y "{new_exe_path}" "{sys.executable}"\n')
                f.write(f'echo Lancement de la nouvelle version...\n')
                f.write(f'set _MEIPASS2=\n')
                f.write(f'start "" "{sys.executable}"\n')
                f.write(f'(goto) 2>nul & del "%~f0"\n') # Auto-suppression

            subprocess.Popen(updater_script_path, shell=True)
            sys.exit(0)

        except Exception as e:
            if progress_win.winfo_exists():
                progress_win.destroy()
            messagebox.showerror("Erreur de mise à jour", f"Le téléchargement a échoué : {e}")
            app_instance.deiconify()

    threading.Thread(target=_download_worker, daemon=True).start()