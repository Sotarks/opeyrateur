@echo off
:: On se déplace dans le dossier où se trouve ce fichier .bat
cd /d "%~dp0"

:: --- Verification et installation des dependances ---

:: --- MODE DEBUG ---
::echo Lancement de l'application en mode DEBUG...
::echo Si une erreur survient, elle s'affichera ci-dessous.
::echo.

:: On utilise "py" (et non "pyw") pour voir la console et les erreurs
py -m scripts.app

echo.
echo ============================================================
echo Le script est termine.
echo S'il y a une erreur ci-dessus, copiez-la ou faites une capture d'ecran.
echo ============================================================
pause