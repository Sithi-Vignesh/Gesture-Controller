; ============================================================
;  Gesture Controller - NSIS Installer Script
;  NSIS v3.12
;  Output: GestureController_Setup.exe
; ============================================================

!define APP_NAME        "GestureController"
!define APP_DISPLAY     "Gesture Controller"
!define APP_VERSION     "1.2.1"
!define APP_PUBLISHER   "Sithi Vignesh"
!define APP_EXE         "GestureController.exe"
!define INSTALL_DIR     "$PROGRAMFILES64\${APP_NAME}"
!define UNINSTALL_KEY   "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
!define LDPLAYER_EXE    "C:\LDPlayer\LDPlayer9\dnplayer.exe"

; ── Output ──────────────────────────────────────────────────
OutFile "GestureController_Setup.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "${UNINSTALL_KEY}" "InstallLocation"

; ── General ─────────────────────────────────────────────────
Name "${APP_DISPLAY} ${APP_VERSION}"
Caption "${APP_DISPLAY} Setup"
BrandingText "${APP_DISPLAY} v${APP_VERSION} by ${APP_PUBLISHER}"

RequestExecutionLevel admin

; Modern UI
!include "MUI2.nsh"

!define MUI_ICON   "icon.ico"
!define MUI_UNICON "icon.ico"
!define MUI_HEADERIMAGE
!define MUI_ABORTWARNING

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; ── LDPlayer Check ──────────────────────────────────────────
Function .onInit
    IfFileExists "${LDPLAYER_EXE}" continue 0
        MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
            "LDPlayer 9 does not appear to be installed.$\n$\nGesture Controller requires LDPlayer 9 to function.$\n$\nDownload it from: https://www.ldplayer.net$\n$\nContinue installing anyway?" \
            IDOK continue
        Abort
    continue:
FunctionEnd

; ── Install Section ─────────────────────────────────────────
Section "MainSection" SEC01
    SetOutPath "${INSTALL_DIR}"

    ; Copy everything from dist/GestureController/
    File /r "dist\GestureController\*.*"

    ; Write uninstaller
    WriteUninstaller "${INSTALL_DIR}\Uninstall.exe"

    ; Registry: Add/Remove Programs entry
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "DisplayName"      "${APP_DISPLAY}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "DisplayVersion"   "${APP_VERSION}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "Publisher"        "${APP_PUBLISHER}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "InstallLocation"  "${INSTALL_DIR}"
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "UninstallString"  '"${INSTALL_DIR}\Uninstall.exe"'
    WriteRegStr   HKLM "${UNINSTALL_KEY}" "DisplayIcon"      '"${INSTALL_DIR}\${APP_EXE}"'
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoModify"         1
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoRepair"         1

    ; Start Menu shortcut
    CreateDirectory "$SMPROGRAMS\${APP_DISPLAY}"
    CreateShortcut  "$SMPROGRAMS\${APP_DISPLAY}\${APP_DISPLAY}.lnk" \
                    "${INSTALL_DIR}\${APP_EXE}" "" \
                    "${INSTALL_DIR}\${APP_EXE}" 0
    CreateShortcut  "$SMPROGRAMS\${APP_DISPLAY}\Uninstall ${APP_DISPLAY}.lnk" \
                    "${INSTALL_DIR}\Uninstall.exe"

    ; Desktop shortcut
    CreateShortcut  "$DESKTOP\${APP_DISPLAY}.lnk" \
                    "${INSTALL_DIR}\${APP_EXE}" "" \
                    "${INSTALL_DIR}\${APP_EXE}" 0
SectionEnd

; ── Uninstall Section ────────────────────────────────────────
Section "Uninstall"
    ; Remove installed files
    RMDir /r "${INSTALL_DIR}"

    ; Remove Start Menu folder
    RMDir /r "$SMPROGRAMS\${APP_DISPLAY}"

    ; Remove Desktop shortcut
    Delete "$DESKTOP\${APP_DISPLAY}.lnk"

    ; Remove registry entries
    DeleteRegKey HKLM "${UNINSTALL_KEY}"
SectionEnd
