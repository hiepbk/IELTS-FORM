#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"
BUILD_DIR="$SCRIPT_DIR/build"

APP_ID="ielts-form"
APP_NAME="IELTS Answer Form"
VERSION="${1:-1.0.0}"

echo "Building $APP_ID version $VERSION"
rm -rf "$DIST_DIR" "$BUILD_DIR"
mkdir -p "$DIST_DIR" "$BUILD_DIR"

STAGE_DIR="$BUILD_DIR/${APP_ID}_${VERSION}"
mkdir -p "$STAGE_DIR/DEBIAN"

cat >"$STAGE_DIR/DEBIAN/control" <<EOF
Package: $APP_ID
Version: $VERSION
Section: misc
Priority: optional
Architecture: all
Depends: python3 (>=3.10), python3-gi, gir1.2-gtk-3.0
Maintainer: $USER
Description: IELTS Listening/Reading answer form with auto grading.
 Provides a GTK UI to type answers, paste keys, and check IELTS band scores.
EOF

# App payload
APP_SHARE="$STAGE_DIR/usr/share/$APP_ID"
mkdir -p "$APP_SHARE"
install -m 644 "$PROJECT_ROOT/ielts_form_gtk.py" "$APP_SHARE/"
install -m 644 "$PROJECT_ROOT/ielts_icon.png" "$APP_SHARE/"

# Wrapper script
BIN_DIR="$STAGE_DIR/usr/bin"
mkdir -p "$BIN_DIR"
cat >"$BIN_DIR/$APP_ID" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec python3 /usr/share/ielts-form/ielts_form_gtk.py
EOF
chmod 755 "$BIN_DIR/$APP_ID"

# Desktop entry + icon
mkdir -p "$STAGE_DIR/usr/share/applications"
cat >"$STAGE_DIR/usr/share/applications/${APP_ID}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Exec=/usr/bin/$APP_ID
Icon=$APP_ID
Terminal=false
Categories=Education;
EOF

mkdir -p "$STAGE_DIR/usr/share/icons/hicolor/256x256/apps"
cp "$PROJECT_ROOT/ielts_icon.png" "$STAGE_DIR/usr/share/icons/hicolor/256x256/apps/${APP_ID}.png"

dpkg-deb --build "$STAGE_DIR" "$DIST_DIR/${APP_ID}_${VERSION}_all.deb"
echo "Created package: $DIST_DIR/${APP_ID}_${VERSION}_all.deb"

