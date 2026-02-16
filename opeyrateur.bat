@echo off
:: On se déplace dans le dossier où se trouve ce fichier .bat
cd /d "%~dp0"

:: --- Verification et installation des dependances ---
echo Lancement de l'application...

:: On lance l'application Python avec pyw (via le lanceur py) pour ne pas avoir de console,
:: et on utilise "start" pour que ce script se ferme juste après le lancement.
:: On lance l'application en tant que module pour que les imports relatifs fonctionnent.
start "Opeyrateur" pyw -m scripts.app