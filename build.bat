@echo off
title Building Opeyrateur...

echo [1] Nettoyage des anciens fichiers de compilation...
:: Supprime les dossiers et fichiers de la compilation precedente pour eviter les erreurs
if exist "dist" ( rmdir /s /q "dist" )
if exist "build" ( rmdir /s /q "build" )
if exist "Opeyrateur.spec" ( del "Opeyrateur.spec" )
echo.

echo [2] Lancement de la creation de l'executable...
:: Lance PyInstaller avec toutes les options necessaires
py -m PyInstaller --name "Opeyrateur" --onefile --windowed --add-data "src;src" --icon="src/logo.ico" main.py
echo.

echo [3] Processus termine.
if exist "dist\Opeyrateur.exe" (
    echo.
    echo ============================================================
    echo == SUCCES !                                             ==
    echo == Votre fichier Opeyrateur.exe est dans le dossier 'dist'. ==
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo == ERREUR !                                               ==
    echo == La creation a echoue. Verifiez les messages ci-dessus. ==
    echo ============================================================
)

echo.
pause