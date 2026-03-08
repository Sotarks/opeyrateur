@echo off
title Building Opeyrateur...

echo [0] Tentative de fermeture de l'application si elle est en cours...
:: /F force la fermeture, /IM specifie le nom de l'image (executable)
:: >nul 2>&1 cache les messages de succes ou d'erreur (si le processus n'est pas trouve)
taskkill /F /IM Opeyrateur.exe >nul 2>&1
echo.

echo Choisissez le mode de compilation :
echo  1 - Rapide (Incremental - Garde le cache, ideal pour le dev)
echo  2 - Complet (Clean - Supprime tout, ideal pour une release)
set /p build_mode="Votre choix (1/2) [defaut: 1] : "

echo.
echo [1] Preparation des dossiers...
:: On supprime toujours dist pour eviter les conflits de fichiers finaux
if exist "dist" ( rmdir /s /q "dist" )

:: On ne supprime le dossier build (cache) que si le mode Complet est choisi
if "%build_mode%"=="2" (
    echo Nettoyage du cache de compilation...
    if exist "build" ( rmdir /s /q "build" )
)
echo.

echo [2] Lancement de la creation de l'executable a partir de Opeyrateur.spec...
:: --log-level WARN reduit le texte inutile dans la console et accelere legerement
py -W ignore -m PyInstaller --noconfirm --log-level=WARN Opeyrateur.spec

:: Verifie le code de sortie de la commande precedente
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo == ERREUR !                                               ==
    echo == La creation a echoue. Verifiez les messages ci-dessus. ==
    echo ============================================================
    echo.
    pause
    exit /b %errorlevel%
)

echo.

echo [3] Processus termine.
echo.
echo ============================================================
echo == SUCCES !                                             ==
echo == Votre fichier Opeyrateur.exe est dans le dossier 'dist'. ==
echo ============================================================

echo.
pause