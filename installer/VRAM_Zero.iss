; VRAM Zero - script Inno Setup (a ouvrir avec Inno Setup Compiler, puis F9)
#define AppName    "VRAM Zero"
#define AppVersion "2.0.1"
#define AppPublisher "MEXAGORA"
#define AppExe     "VRAM Zero.exe"

[Setup]
AppId={{1EBFD4FB-E59C-49B4-A1DA-7C5D77CD1380}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
SetupIconFile=..\assets\vram_zero.ico
UninstallDisplayIcon={app}\{#AppExe}
OutputDir=Output
OutputBaseFilename=VRAM_Zero_Setup_{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
WizardImageFile=..\assets\wizard_large.bmp
WizardSmallImageFile=..\assets\wizard_small.bmp
AppPublisherURL=https://github.com/graphixxgeek-boop/VRAM-Zero-by-MEXAGORA
AppSupportURL=https://github.com/graphixxgeek-boop/VRAM-Zero-by-MEXAGORA/issues
VersionInfoVersion={#AppVersion}.0.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} - installeur
VersionInfoProductName={#AppName}
VersionInfoCopyright=Copyright (c) 2026 MEXAGORA
; Signature du code (a activer une fois le certificat obtenu, voir GUIDE_PUBLICATION.md) :
; SignTool=signtool
; SignedUninstaller=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\VRAM Zero\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\vram_zero_popart.png"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

