#define MyVer "1.1.3"
[Setup]
AppId={{6F3A2C1E-9B7D-4E21-A5C8-0E1F2A3B4C5D}
AppName=EX WIFI ENHANCE
AppVersion={#MyVer}
AppVerName=EX WIFI ENHANCE {#MyVer}
AppPublisher=EX Inc.
AppPublisherURL=https://github.com/xtremestickman151-ops/ex-wifi-enhance
AppCopyright=©2026 EX Inc.
VersionInfoVersion={#MyVer}.0
VersionInfoCompany=EX Inc.
VersionInfoCopyright=©2026 EX Inc.
VersionInfoProductName=EX WIFI ENHANCE
VersionInfoDescription=EX WIFI ENHANCE Setup
DefaultDirName={localappdata}\Programs\EX WIFI ENHANCE
DefaultGroupName=EX WIFI ENHANCE
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=EX WIFI ENHANCE Setup {#MyVer}
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\EX WIFI ENHANCE.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
; remove any partial/stale runtime from earlier manual updates
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "dist\EX WIFI ENHANCE\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\EX WIFI ENHANCE"; Filename: "{app}\EX WIFI ENHANCE.exe"
Name: "{group}\Uninstall EX WIFI ENHANCE"; Filename: "{uninstallexe}"
Name: "{userdesktop}\EX WIFI ENHANCE"; Filename: "{app}\EX WIFI ENHANCE.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\EX WIFI ENHANCE.exe"; Description: "Launch EX WIFI ENHANCE now"; Flags: nowait postinstall skipifsilent
