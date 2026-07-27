; Less Token Installer
; NSIS Script for Windows

!include "MUI2.nsh"
!include "x64.nsh"

; Basic Settings
Name "Less Token v1.0.2"
OutFile "lesstoken-setup.exe"
InstallDir "$PROGRAMFILES\Less Token"

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
  File "dist\Less Token.exe"

  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\Less Token"
  CreateShortCut "$SMPROGRAMS\Less Token\Less Token.lnk" "$INSTDIR\Less Token.exe"
  CreateShortCut "$SMPROGRAMS\Less Token\Uninstall.lnk" "$INSTDIR\uninstall.exe"

  ; Create Desktop shortcut
  CreateShortCut "$DESKTOP\Less Token.lnk" "$INSTDIR\Less Token.exe"

  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Registry entries for Add/Remove Programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Less Token" \
             "DisplayName" "Less Token"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Less Token" \
             "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Less Token" \
             "DisplayIcon" "$INSTDIR\Less Token.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Less Token" \
             "DisplayVersion" "1.0.0"
SectionEnd

; Uninstaller Section
Section "Uninstall"
  ; Remove files
  Delete "$INSTDIR\Less Token.exe"
  Delete "$INSTDIR\uninstall.exe"

  ; Remove shortcuts
  Delete "$SMPROGRAMS\Less Token\Less Token.lnk"
  Delete "$SMPROGRAMS\Less Token\Uninstall.lnk"
  RMDir "$SMPROGRAMS\Less Token"
  Delete "$DESKTOP\Less Token.lnk"

  ; Remove directory
  RMDir "$INSTDIR"

  ; Remove registry entries
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Less Token"
SectionEnd
