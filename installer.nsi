; LessToken Installer
; NSIS Script for Windows

!include "MUI2.nsh"
!include "x64.nsh"

; Basic Settings
Name "LessToken v1.0.5"
OutFile "lesstoken-setup.exe"
InstallDir "$PROGRAMFILES\LessToken"

; MUI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Turkish"

; Installer Sections
Section "Install"
  SetOutPath "$INSTDIR"

  ; Copy executable
  File "dist\LessToken.exe"

  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\LessToken"
  CreateShortCut "$SMPROGRAMS\LessToken\LessToken.lnk" "$INSTDIR\LessToken.exe"
  CreateShortCut "$SMPROGRAMS\LessToken\Uninstall.lnk" "$INSTDIR\uninstall.exe"

  ; Create Desktop shortcut
  CreateShortCut "$DESKTOP\LessToken.lnk" "$INSTDIR\LessToken.exe"

  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Registry entries for Add/Remove Programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LessToken" \
             "DisplayName" "LessToken"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LessToken" \
             "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LessToken" \
             "DisplayIcon" "$INSTDIR\LessToken.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LessToken" \
             "DisplayVersion" "1.0.5"
SectionEnd

; Uninstaller Section
Section "Uninstall"
  ; Remove files
  Delete "$INSTDIR\LessToken.exe"
  Delete "$INSTDIR\uninstall.exe"

  ; Remove shortcuts
  Delete "$SMPROGRAMS\LessToken\LessToken.lnk"
  Delete "$SMPROGRAMS\LessToken\Uninstall.lnk"
  RMDir "$SMPROGRAMS\LessToken"
  Delete "$DESKTOP\LessToken.lnk"

  ; Remove directory
  RMDir "$INSTDIR"

  ; Remove registry entries
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LessToken"
SectionEnd
