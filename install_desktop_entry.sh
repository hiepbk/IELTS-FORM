#!/usr/bin/env bash
set -euo pipefail

APP_NAME="IELTS Answer Form"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/ielts_form_gtk.py"
ICON_SCRIPT="$SCRIPT_DIR/generate_icon.py"
ICON_PATH="$SCRIPT_DIR/ielts_icon.png"
DESKTOP_FILE="$HOME/.local/share/applications/IELTSAnswerForm.desktop"

if [[ ! -f "$SCRIPT_PATH" ]]; then
  echo "Cannot find $SCRIPT_PATH. Make sure ielts_form_gtk.py is in the same folder."
  exit 1
fi

if [[ -f "$ICON_SCRIPT" ]]; then
  python3 "$ICON_SCRIPT"
else
  echo "Warning: $ICON_SCRIPT missing, skipping icon generation."
fi

mkdir -p "$(dirname "$DESKTOP_FILE")"

cat >"$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Exec=python3 $SCRIPT_PATH
Icon=$ICON_PATH
Terminal=false
StartupWMClass=IELTSAnswerForm
Categories=Education;
EOF

chmod +x "$DESKTOP_FILE"
echo "Desktop entry created at $DESKTOP_FILE"
echo "Use your application launcher to find \"$APP_NAME\"."

