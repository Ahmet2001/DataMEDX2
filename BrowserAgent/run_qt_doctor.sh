#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip >/dev/null
python -m pip install -q -r requirements.txt
python -m pip install -q -r requirements-qt.txt

check_qt_xcb_runtime() {
  if [ "${QT_QPA_PLATFORM:-}" = "offscreen" ]; then
    return 0
  fi

  if [ -z "${DISPLAY:-}" ] || [ "${XDG_SESSION_TYPE:-}" = "wayland" ]; then
    return 0
  fi

  local xcb_plugin
  xcb_plugin="$(python - <<'PY'
from pathlib import Path
for path in Path(".venv").glob("lib/python*/site-packages/PySide6/Qt/plugins/platforms/libqxcb.so"):
    print(path)
    break
PY
)"

  if [ -n "$xcb_plugin" ] && ldd "$xcb_plugin" 2>/dev/null | grep -q "libxcb-cursor.so.0 => not found"; then
    cat <<'EOF'

Qt pencere eklentisi icin sistem paketi eksik:
  libxcb-cursor.so.0

Ubuntu/Debian icin bir kez sunu calistir:
  sudo apt update
  sudo apt install -y libxcb-cursor0

Sonra tekrar:
  ./run_qt_doctor.sh

Not: Bu Python paketi degil, isletim sistemi paketi.
EOF
    exit 1
  fi
}

check_qt_xcb_runtime

python -m MarketingApp.qt_doctor_panel
