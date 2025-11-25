#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$SCRIPT_DIR/build-linux"
INSTALL_DIR="$SCRIPT_DIR/dist-linux"

rm -rf "$BUILD_DIR" "$INSTALL_DIR"
cmake -S "$PROJECT_ROOT/qt_app" -B "$BUILD_DIR" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR"
cmake --build "$BUILD_DIR"
cmake --install "$BUILD_DIR"

echo "Qt binaries installed to $INSTALL_DIR"

