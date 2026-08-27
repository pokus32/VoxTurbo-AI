; Inno Setup Script for VoxTurbo AI Windows Installer
#define MyAppName "VoxTurbo AI"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Titan Automation / VoxTurbo"
#define MyAppURL "https://github.com/pokus32/VoxTurbo-AI"
#define MyAppExeName "VoxTurbo.exe"

[Setup]
AppId={{C585DF57-A2D4-46F1-BA57-648566192421}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
PrivilegesRequired=lowest
OutputDir=..\dist_installer
OutputBaseFilename=VoxTurbo-Setup-x64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Запускать автоматически при входе в Windows"; GroupDescription: "Автозагрузка:"; Flags: unchecked

[Files]
Source: "..\dist\VoxTurbo\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
