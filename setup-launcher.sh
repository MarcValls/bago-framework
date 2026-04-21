#!/usr/bin/env bash
# setup-launcher.sh — Registra LaunchBAGO.app para el esquema bago-launch://
# Ejecutar una sola vez. Permite que el botón "Iniciar en Terminal" funcione
# en cualquier navegador (Safari, Chrome, Firefox, etc.)

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$SCRIPT_DIR/LaunchBAGO.app"
APPLESCRIPT_SRC="/tmp/bago_launcher_setup.applescript"
PB=/usr/libexec/PlistBuddy
LSREG="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"

echo "▶ BAGO Launcher setup"
echo "  Directorio: $SCRIPT_DIR"

# ── 1. Compilar app ──────────────────────────────────────────────────────────
cat > "$APPLESCRIPT_SRC" << APPL
on open location theURL
  set bagPath to "$SCRIPT_DIR"
  set cmd to "cd '" & bagPath & "' && bash start-viewer.command"
  tell application "Terminal"
    activate
    do script cmd
  end tell
end open location

on run
  set bagPath to "$SCRIPT_DIR"
  set cmd to "cd '" & bagPath & "' && bash start-viewer.command"
  tell application "Terminal"
    activate
    do script cmd
  end tell
end run
APPL

echo "  Compilando LaunchBAGO.app…"
rm -rf "$APP"
osacompile -o "$APP" "$APPLESCRIPT_SRC"

# ── 2. Registrar URL scheme ──────────────────────────────────────────────────
INFO="$APP/Contents/Info.plist"
$PB -c "Add :CFBundleURLTypes array"            "$INFO"
$PB -c "Add :CFBundleURLTypes:0 dict"           "$INFO"
$PB -c "Add :CFBundleURLTypes:0:CFBundleURLName string BAGO Launcher" "$INFO"
$PB -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes array"             "$INFO"
$PB -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes:0 string bago-launch" "$INFO"
$PB -c "Set :CFBundleName BAGOLauncher" "$INFO"
$PB -c "Add :CFBundleIdentifier string com.bago.launcher" "$INFO" 2>/dev/null || \
$PB -c "Set :CFBundleIdentifier com.bago.launcher" "$INFO"

# ── 3. Registrar con LaunchServices ─────────────────────────────────────────
echo "  Registrando con LaunchServices…"
"$LSREG" -f "$APP"

echo ""
echo "✅ Listo. El botón '⚡ Iniciar en Terminal' funciona en todos los navegadores."
echo "   (bago-launch:// → LaunchBAGO.app → Terminal.app)"
