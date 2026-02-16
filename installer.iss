; Script pour Inno Setup
; Voir https://jrsoftware.org/ishelp/ pour la documentation

[Setup]
; NOTE: Le AppId est un identifiant unique pour votre application.
; Changez-le si vous créez une autre application.
AppId={{F4B6E6B4-6A6E-4A8E-9A8E-6B4E6A6E6B4E}}
AppName=Opeyrateur
AppVersion=1.0
AppPublisher=Alaïs Peyrat
DefaultDirName={userdesktop}\Opeyrateur
DisableProgramGroupPage=yes
; 'OutputBaseFilename' est le nom du fichier d'installation qui sera créé.
OutputBaseFilename=setup-opeyrateur
; 'OutputDir' est l'endroit où le fichier d'installation sera sauvegardé.
OutputDir=.\install
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; NOTE: Le fichier source doit pointer vers l'exécutable que PyInstaller a créé.
Source: "dist\Opeyrateur.exe"; DestDir: "{app}"; Flags: ignoreversion
; TODO: Ajoutez ici d'autres fichiers que vous voudriez distribuer avec votre application

[Icons]
Name: "{autoprograms}\Opeyrateur"; Filename: "{app}\Opeyrateur.exe"
Name: "{autodesktop}\Opeyrateur"; Filename: "{app}\Opeyrateur.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Opeyrateur.exe"; Description: "{cm:LaunchProgram,Opeyrateur}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}/budget"
Type: filesandordirs; Name: "{app}/factures"
Type: filesandordirs; Name: "{app}/frais"
Type: filesandordirs; Name: "{app}/backups"
Type: files; Name: "{app}/settings.ini"