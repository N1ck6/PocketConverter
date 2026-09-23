; PocketConverter installer (Inno Setup 6)
;
; Don't compile this by hand — run build.ps1 (or let CI do it). It:
;   1) builds dist\converter\ with PyInstaller (--onedir)
;   2) regenerates registry_generated.iss from converter_app/formats.py
;   3) compiles this file:  ISCC /DMyAppVersion=x.y.z installer\installer.iss
;
; The installer can install for all users (admin, HKLM) or just the
; current user (no admin, HKCU); registry entries use HKA so they follow
; that choice automatically.

#define MyAppName "PocketConverter"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif
#define MyAppPublisher "N1ck6"
#define MyAppURL "https://github.com/N1ck6/PocketConverter"
#define MyAppExeName "converter.exe"
; Must match APP_ID in converter_app/utils.py — gives notifications the app's name and icon
#define MyAppUserModelID "N1ck6.PocketConverter"

[Setup]
; Same AppId as the 1.x installers, so 2.x upgrades them in place instead of
; installing a second copy. Never change it.
AppId={{4D2FAE62-BEB0-42D7-A1EC-4175D382F64A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog commandline
UsedUserAreasWarning=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
ChangesAssociations=yes
CloseApplications=yes
RestartApplications=no
WizardStyle=modern
SetupIconFile=..\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
OutputDir=output
OutputBaseFilename={#MyAppName}Setup-{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
; Signing is only enabled when build.ps1 passes /DSIGN (i.e. a certificate is configured)
#ifdef SIGN
SignTool=signtoolcli
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
english.ContextMenuTask=Add "Convert to" to the right-click menu in Explorer
russian.ContextMenuTask=Добавить пункт «Convert to» в контекстное меню Проводника
english.ShowHelp=Show how to use {#MyAppName}
russian.ShowHelp=Показать, как пользоваться {#MyAppName}

[Tasks]
Name: "contextmenu"; Description: "{cm:ContextMenuTask}"

[InstallDelete]
; 1.x shipped a single 170 MB self-extracting converter.exe and kept its log
; in Program Files; clear old bundled libraries so upgrades never mix versions.
Type: filesandordirs; Name: "{app}\_internal"
Type: files; Name: "{app}\PocketConverter_log.txt"

[Files]
Source: "..\dist\converter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\small.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\logo.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Opening it shows a short "how to use" window. The AppUserModelID is what
; lets Windows show notifications as "PocketConverter" with its icon.
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; AppUserModelID: "{#MyAppUserModelID}"

[Registry]
Root: HKA; Subkey: "Software\Classes\AppUserModelId\{#MyAppUserModelID}"; ValueType: string; ValueName: "DisplayName"; ValueData: "{#MyAppName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\AppUserModelId\{#MyAppUserModelID}"; ValueType: string; ValueName: "IconUri"; ValueData: "{app}\logo.png"
#include "registry_generated.iss"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:ShowHelp}"; Flags: postinstall nowait skipifsilent unchecked

[UninstallDelete]
; Per-user log and job queue written by the app itself
Type: filesandordirs; Name: "{localappdata}\PocketConverter"
