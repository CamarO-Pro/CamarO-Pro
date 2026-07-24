#!/usr/bin/env python3
"""
Camoro v4.1 - Instagram Pentest Framework
OSINT + AI Wordlist + Brute Force Engine
"""

from __future__ import annotations

import os
import sys
import traceback

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
if BASE not in sys.path:
    sys.path.insert(0, BASE)


class C:
    R = "\033[91m"
    G = "\033[92m"
    Y = "\033[93m"
    B = "\033[94m"
    P = "\033[95m"
    C = "\033[96m"
    W = "\033[97m"
    BL = "\033[1m"
    D = "\033[2m"
    RE = "\033[0m"


def clear() -> None:
    try:
        os.system("clear 2>/dev/null || cls 2>/dev/null || true")
    except Exception:
        print("\n" * 3)


def ensure_dirs() -> None:
    for d in ("modules", "wordlists", "output"):
        try:
            os.makedirs(os.path.join(BASE, d), exist_ok=True)
        except Exception as e:
            print(f"{C.Y}[!] mkdir {d}: {e}{C.RE}")
    init_py = os.path.join(BASE, "modules", "__init__.py")
    if not os.path.exists(init_py):
        try:
            with open(init_py, "w", encoding="utf-8") as f:
                f.write("# Camoro modules\n")
        except Exception:
            pass


def banner() -> None:
    clear()
    print(
        f"""
{C.R}{C.BL}
   ██████╗ █████╗ ███╗   ███╗ ██████╗ ██████╗  ██████╗
  ██╔════╝██╔══██╗████╗ ████║██╔═══██╗██╔══██╗██╔═══██╗
  ██║     ███████║██╔████╔██║██║   ██║██████╔╝██║   ██║
  ██║     ██╔══██║██║╚██╔╝██║██║   ██║██╔══██╗██║   ██║
  ╚██████╗██║  ██║██║ ╚═╝ ██║╚██████╔╝██║  ██║╚██████╔╝
   ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝
{C.RE}
{C.C}{C.BL}     Instagram Pentest Framework  |  v4.1
{C.RE}{C.W}          OSINT · Wordlist AI · Brute Engine
{C.RE}{C.D}          Authorized testing only
{C.RE}
"""
    )


def check_modules() -> bool:
    ok_all = True
    print(f"  {C.D}Path: {BASE}{C.RE}")
    for name, rel in (
        ("OSINT", "modules/instagram_osint.py"),
        ("Wordlist", "modules/wordlist_gen.py"),
        ("Brute", "modules/brute_force.py"),
    ):
        path = os.path.join(BASE, rel)
        exists = os.path.isfile(path)
        ok_all = ok_all and exists
        icon = f"{C.G}OK{C.RE}" if exists else f"{C.R}MISSING{C.RE}"
        print(f"  [{icon}] {name:10} → {rel}")
    print()
    return ok_all


def load_run(module_name: str) -> None:
    try:
        mod = __import__(f"modules.{module_name}", fromlist=["run"])
    except Exception as e:
        print(f"\n  {C.R}[✗] Import failed: modules.{module_name}{C.RE}")
        print(f"  {C.Y}{type(e).__name__}: {e}{C.RE}")
        print(f"  {C.W}Expected file: modules/{module_name}.py{C.RE}")
        input(f"\n  {C.D}Enter...{C.RE}")
        return

    if not hasattr(mod, "run") or not callable(getattr(mod, "run")):
        print(f"  {C.R}[✗] modules.{module_name} has no callable run(){C.RE}")
        input(f"  {C.D}Enter...{C.RE}")
        return

    try:
        mod.run()
    except KeyboardInterrupt:
        print(f"\n  {C.Y}[!] Interrupted{C.RE}")
        input(f"  {C.D}Enter...{C.RE}")
    except Exception as e:
        print(f"\n  {C.R}[✗] Runtime error in {module_name}:{C.RE}")
        print(f"  {C.Y}{type(e).__name__}: {e}{C.RE}")
        traceback.print_exc()
        input(f"\n  {C.D}Enter...{C.RE}")


def menu() -> None:
    print(
        f"""
  {C.P}{C.BL}╔══════════════════════════════════════════════════╗
  ║              CAMORO MODULES                      ║
  ╠══════════════════════════════════════════════════╣
  ║  {C.G}[1]{C.RE}  Instagram OSINT Scanner                    ║
  ║  {C.G}[2]{C.RE}  AI Wordlist Generator                     ║
  ║  {C.G}[3]{C.RE}  Brute Force Engine                        ║
  ║  {C.G}[4]{C.RE}  Full Attack Chain                          ║
  ║  {C.G}[5]{C.RE}  Diagnose                                   ║
  ║  {C.G}[0]{C.RE}  Exit                                       ║
  ╚══════════════════════════════════════════════════╝
"""
    )


def diagnose() -> None:
    print(f"\n  {C.C}=== DIAGNOSE ==={C.RE}")
    check_modules()
    for m in ("instagram_osint", "wordlist_gen", "brute_force"):
        try:
            __import__(f"modules.{m}")
            print(f"  {C.G}[OK]{C.RE} import modules.{m}")
        except Exception as e:
            print(f"  {C.R}[FAIL]{C.RE} modules.{m} → {type(e).__name__}: {e}")

    for pkg in ("requests", "instaloader", "curl_cffi"):
        try:
            __import__(pkg)
            print(f"  {C.G}[OK]{C.RE} package {pkg}")
        except Exception:
            print(f"  {C.Y}[!]{C.RE} package {pkg} not installed")

    input(f"\n  {C.D}Enter...{C.RE}")


def main() -> None:
    ensure_dirs()
    while True:
        try:
            banner()
            check_modules()
            menu()
            choice = input(f"  {C.G}[?]{C.RE} اختر {C.W}> {C.RE}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {C.P}👋 Bye{C.RE}\n")
            sys.exit(0)

        if choice == "1":
            load_run("instagram_osint")
        elif choice == "2":
            load_run("wordlist_gen")
        elif choice == "3":
            load_run("brute_force")
        elif choice == "4":
            load_run("instagram_osint")
            load_run("wordlist_gen")
            load_run("brute_force")
        elif choice == "5":
            diagnose()
        elif choice == "0":
            print(f"\n  {C.P}👋 Bye{C.RE}\n")
            sys.exit(0)
        else:
            print(f"  {C.R}[!] اختيار غير صحيح{C.RE}")
            try:
                input(f"  {C.D}Enter...{C.RE}")
            except (EOFError, KeyboardInterrupt):
                pass


if __name__ == "__main__":
    main()
