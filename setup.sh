#!/bin/bash
echo "[*] Installing Camoro dependencies..."
pip3 install instaloader requests curl_cffi colorama
mkdir -p modules wordlists output
touch modules/__init__.py
chmod +x camoro.py
echo "[✓] Done. Run: python3 camoro.py"
