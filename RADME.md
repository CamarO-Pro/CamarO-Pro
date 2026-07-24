# Camoro v4.1

Instagram OSINT · AI Wordlist Generator · Brute Force Engine

Authorized penetration testing framework only.

## Modules

1. **Instagram OSINT** – public profile info (multi-method, 403-aware)
2. **AI Wordlist** – personal-intel password dictionary (~18000)
3. **Brute Force Engine** – CSRF, 3–5s delays, device rotate every 20s, progress, resume
4. **Full chain** – 1 → 2 → 3
5. **Diagnose** – file/import health check

## Install

```bash
git clone https://github.com/YOUR_USERNAME/camoro.git
cd camoro
bash setup.sh
python3 camoro.py
