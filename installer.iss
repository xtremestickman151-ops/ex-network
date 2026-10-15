#define MyVer "1.2.0"
[Setup]
AppId={{6F3A2C1E-9B7D-4E21-A5C8-0E1F2A3B4C5D}
AppName=EX NETWORK
AppVersion={#MyVer}
AppVerName=EX NETWORK {#MyVer}
AppPublisher=EX Inc.
AppPublisherURL=https://github.com/xtremestickman151-ops/ex-network
AppCopyright=©2026 EX Inc.
VersionInfoVersion={#MyVer}.0
VersionInfoCompany=EX Inc.
VersionInfoCopyright=©2026 EX Inc.
VersionInfoProductName=EX NETWORK
VersionInfoDescription=EX NETWORK Setup
DefaultDirName={localappdata}\Programs\EX NETWORK
DefaultGroupName=EX NETWORK
DisableProgramGroupPage=yes
UsePreviousAppDir=no
UsePreviousGroup=no
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=EX NETWORK Setup {#MyVer}
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\EX NETWORK.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
; migration from the old name "EX WIFI ENHANCE" (same AppId, new folder)
Type: filesandordirs; Name: "{localappdata}\Programs\EX WIFI ENHANCE"
Type: filesandordirs; Name: "{userprograms}\EX WIFI ENHANCE"
Type: files; Name: "{userdesktop}\EX WIFI ENHANCE.lnk"
; remove any partial/stale runtime from earlier manual updates
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "dist\EX NETWORK\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\EX NETWORK"; Filename: "{app}\EX NETWORK.exe"
Name: "{group}\Uninstall EX NETWORK"; Filename: "{uninstallexe}"
Name: "{userdesktop}\EX NETWORK"; Filename: "{app}\EX NETWORK.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\EX NETWORK.exe"; Description: "Launch EX NETWORK now"; Flags: nowait postinstall skipifsilent

[Code]
// Close a running old-named app so its folder can be removed.
procedure CurStepChanged(CurStep: TSetupStep);
var R: Integer;
begin
  if CurStep = ssInstall then
    Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM "EX WIFI ENHANCE.exe"', '', SW_HIDE, ewWaitUntilTerminated, R);
end;
