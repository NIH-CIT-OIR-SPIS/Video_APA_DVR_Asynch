; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define name "SCORHE Acquisition"
#define version "1.0"
#define publisher "CIT/SPIS"
#define url "https://scorhe.nih.gov"
#define exeName "SCORHE_acquisition.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{39E77EE6-DCC5-4A9E-9181-5A8D91255B06}
AppName={#name}
AppVersion={#version}
;AppVerName={#name} {#version}
AppPublisher={#publisher}
AppPublisherURL={#url}
AppSupportURL={#url}
AppUpdatesURL={#url}
DefaultDirName={pf}\{#name}
DisableProgramGroupPage=yes
OutputBaseFilename=acquisition_setup_admin
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\SCORHE_acquisition\{#exeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\SCORHE_acquisition\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{commonprograms}\{#name}"; Filename: "{app}\{#exeName}"
Name: "{commondesktop}\{#name}"; Filename: "{app}\{#exeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#exeName}"; Description: "{cm:LaunchProgram,{#StringChange(name, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

