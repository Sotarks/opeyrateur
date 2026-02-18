@echo off
title Building Opeyrateur...

echo [0] Tentative de fermeture de l'application si elle est en cours...
:: /F force la fermeture, /IM specifie le nom de l'image (executable)
:: >nul 2>&1 cache les messages de succes ou d'erreur (si le processus n'est pas trouve)
taskkill /F /IM Opeyrateur.exe >nul 2>&1
echo.

echo [1] Nettoyage des anciens fichiers de compilation...
:: Supprime les dossiers et fichiers de la compilation precedente pour eviter les erreurs
if exist "dist" ( rmdir /s /q "dist" )
if exist "build" ( rmdir /s /q "build" )
echo.

echo [2] Lancement de la creation de l'executable a partir de Opeyrateur.spec...
:: Lance PyInstaller en utilisant le fichier de configuration .spec.
py -m PyInstaller --noconfirm Opeyrateur.spec

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