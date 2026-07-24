#!/usr/bin/env python3
"""
CAMORO PENTEST FRAMEWORK v4.0
Instagram OSINT + Wordlist AI + Brute Force Engine
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class C:
    R = '\033[91m'; G = '\033[92m'; Y = '\033[93m'
    B = '\033[94m'; P = '\033[95m'; C = '\033[96m'
    W = '\033[97m'; BL = '\033[1m'; D = '\033[2m'; RE = '\033[0m'

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def banner():
    clear()
    print(f"""
{C.R}{C.BL}
   ▄████████  ▄▄▄▄███▄▄▄▄    ▄▄▄▄███▄▄▄▄   ▄██████▄   ▄████████    ▄████████
  ███    ███ ▄██▀▀▀███▀▀▀██▄ ▄██▀▀▀███▀▀▀██▄ ███    ███ ███    ███   ███    ███
  ███    █▀  ███   ███   ███ ███   ███   ███ ███    ███ ███    █▀    ███    ███
  ███        ███   ███   ███ ███   ███   ███ ███    ███ ███         ▄███▄▄▄▄██▀
  ███        ███   ███   ███ ███   ███   ███ ███    ███ ███        ▀▀███▀▀▀▀▀
  ███    █▄  ███   ███   ███ ███   ███   ███ ███    ███ ███    █▄  ▀███████████
  ███    ███ ███   ███   ███ ███   ███   ███ ███    ███ ███    ███   ███    ███
  ████████▀   ▀█   ███   █▀   ▀█   ███   █▀   ▀██████▀  ████████▀    ███    ███
{C.RE}
{C.C}{C.BL}     Instagram Pentest Framework  |  AI Powered
{C.RE}{C.W}                    Version 4.0 | Authorized Testing Only
{C.RE}
""")

def menu():
    print(f"""
  {C.P}{C.BL}╔══════════════════════════════════════════════════╗
  ║              CAMORO MODULES                      ║
  ╠══════════════════════════════════════════════════╣
  ║                                                  ║
  ║  {C.G}[1]{C.RE}  {C.W}Instagram OSINT Scanner{C.RE}                    ║
  ║       {C.D}جلب معلومات الملف الشخصي{C.RE}                    ║
  ║                                                  ║
  ║  {C.G}[2]{C.RE}  {C.W}AI Wordlist Generator{C.RE}                     ║
  ║       {C.D}توليد قاموس كلمات مرور ذكي (~18000+){C.RE}        ║
  ║                                                  ║
  ║  {C.G}[3]{C.RE}  {C.W}Brute Force Engine{C.RE}  ⚡                    ║
  ║       {C.D}هجوم كلمات المرور مع تدوير الأجهزة{C.RE}          ║
  ║                                                  ║
  ║  {C.G}[4]{C.RE}  {C.W}Full Attack Chain{C.RE}                          ║
  ║       {C.D}OSINT → Wordlist → Brute Force{C.RE}              ║
  ║                                                  ║
  ║  {C.G}[0]{C.RE}  {C.R}Exit{C.RE}                                       ║
  ║                                                  ║
  ╚══════════════════════════════════════════════════╝
""")

def main():
    while True:
        banner()
        menu()
        choice = input(f"  {C.G}[?]{C.RE} اختر الأداة {C.W}> {C.RE}").strip()

        if choice == '1':
            from modules.instagram_osint import run
            run()
        elif choice == '2':
            from modules.wordlist_gen import run
            run()
        elif choice == '3':
            from modules.brute_force import run
            run()
        elif choice == '4':
            from modules.instagram_osint import run as osint_run
            from modules.wordlist_gen import run as wl_run
            from modules.brute_force import run as bf_run
            print(f"\n  {C.Y}[*] Full Chain: OSINT → Wordlist → Brute{C.RE}\n")
            osint_run()
            wl_run()
            bf_run()
        elif choice == '0':
            print(f"\n  {C.P}👋 Goodbye!{C.RE}\n")
            sys.exit(0)
        else:
            print(f"  {C.R}[!] اختيار غير صحيح{C.RE}")
            input(f"  {C.D}Enter للمتابعة...{C.RE}")

if __name__ == "__main__":
    main()
