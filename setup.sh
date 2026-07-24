#!/data/data/com.termux/files/usr/bin/bash
# Camoro setup - Termux / Linux / iSH

set -e

echo "[*] Camoro setup starting..."

if command -v pkg >/dev/null 2>&1; then
  pkg update -y || true
  pkg install -y python git || true
elif command -v apt >/dev/null 2>&1; then
  sudo apt update -y || apt update -y || true
  sudo apt install -y python3 python3-pip git || apt install -y python3 python3-pip git || true
elif command -v apk >/dev/null 2>&1; then
  apk add python3 py3-pip git || true
fi

PYTHON=python3
if ! command -v python3 >/dev/null 2>&1; then
  PYTHON=python
fi

$PYTHON -m pip install --upgrade pip || true
$PYTHON -m pip install -r requirements.txt || pip3 install -r requirements.txt

mkdir -p modules wordlists output
touch modules/__init__.py wordlists/.gitkeep output/.gitkeep
chmod +x camoro.py setup.sh 2>/dev/null || true

echo "[✓] Done"
echo "[*] Run: python3 camoro.py"
echo "[*] Diagnose: choose option [5]"
