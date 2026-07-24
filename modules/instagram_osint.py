#!/usr/bin/env python3
"""
Camoro Module 1 - Instagram OSINT Scanner (FIXED)
- Method A: i.instagram.com web_profile_info (الأفضل على Termux)
- Method B: www.instagram.com web_profile_info
- Method C: instaloader (قد يفشل بـ 403)
- لا يقول "does not exist" عند 403
"""

import os
import sys
import json
import re
from datetime import datetime

class C:
    R = '\033[91m'; G = '\033[92m'; Y = '\033[93m'
    B = '\033[94m'; P = '\033[95m'; C = '\033[96m'
    W = '\033[97m'; BL = '\033[1m'; D = '\033[2m'; RE = '\033[0m'

IG_APP_ID = "936619743392459"
IPHONE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 "
    "Mobile/15E148 Safari/604.1"
)


def clear():
    try:
        os.system('clear' if os.name == 'posix' else 'cls')
    except Exception:
        print('\n' * 3)


def get_requests():
    try:
        from curl_cffi import requests as r
        return r, True
    except Exception:
        import requests as r
        return r, False


def safe_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
        if cur is default:
            return default
    return cur


def parse_user(user):
    followers = (
        user.get('follower_count')
        or safe_get(user, 'edge_followed_by', 'count', default=0)
        or 0
    )
    following = (
        user.get('following_count')
        or safe_get(user, 'edge_follow', 'count', default=0)
        or 0
    )
    posts = (
        user.get('media_count')
        or safe_get(user, 'edge_owner_to_timeline_media', 'count', default=0)
        or 0
    )
    pp = user.get('profile_pic_url_hd') or user.get('profile_pic_url') or ''
    ext = user.get('external_url') or ''
    if not ext:
        links = user.get('bio_links') or []
        if links and isinstance(links, list):
            ext = links[0].get('url', '') if isinstance(links[0], dict) else ''

    return {
        'username': user.get('username', 'N/A'),
        'full_name': user.get('full_name') or '',
        'bio': user.get('biography') or user.get('bio') or '',
        'followers': int(followers or 0),
        'following': int(following or 0),
        'posts': int(posts or 0),
        'is_private': bool(user.get('is_private', False)),
        'is_verified': bool(user.get('is_verified', False)),
        'is_business': bool(user.get('is_business_account', user.get('is_business', False))),
        'id': str(user.get('id') or user.get('pk') or 'N/A'),
        'external_url': ext,
        'profile_pic': pp,
        'category': user.get('category_name') or user.get('category') or 'N/A',
        'highlight_reel_count': int(user.get('highlight_reel_count') or 0),
    }


def fetch_via_api(username):
    """الطريقة التي اشتغلت معك سابقاً"""
    req, has_cffi = get_requests()
    print(f"  {C.C}[*] Method A: web_profile_info API"
          f"{' (curl_cffi)' if has_cffi else ' (requests)'}{C.RE}")

    session = req.Session()
    session.headers.update({
        'User-Agent': IPHONE_UA,
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
    })

    # Warmup cookies
    try:
        session.get('https://www.instagram.com/', timeout=20)
    except Exception as e:
        print(f"  {C.Y}[!] Warmup warn: {str(e)[:60]}{C.RE}")

    domains = [
        f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}',
        f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}',
    ]

    for url in domains:
        try:
            headers = {
                'x-ig-app-id': IG_APP_ID,
                'x-requested-with': 'XMLHttpRequest',
                'Origin': 'https://www.instagram.com',
                'Referer': f'https://www.instagram.com/{username}/',
                'Sec-Fetch-Site': 'same-site',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
            }
            r = session.get(url, headers=headers, timeout=25)
            print(f"  {C.D}    {url.split('/')[2]} → HTTP {r.status_code}{C.RE}")

            if r.status_code == 404:
                return None, 'not_found'
            if r.status_code == 403:
                print(f"  {C.Y}[!] 403 Forbidden — IP/device blocked on this endpoint{C.RE}")
                continue
            if r.status_code != 200:
                continue

            data = r.json()
            user = safe_get(data, 'data', 'user')
            if user:
                out = parse_user(user)
                out['_source'] = url.split('/')[2]
                return out, 'ok'
        except Exception as e:
            print(f"  {C.Y}[!] API error: {str(e)[:80]}{C.RE}")

    return None, 'blocked'


def fetch_via_html(username):
    print(f"  {C.C}[*] Method B: HTML / LD+JSON scrape{C.RE}")
    req, _ = get_requests()
    try:
        r = req.get(
            f'https://www.instagram.com/{username}/',
            headers={'User-Agent': IPHONE_UA, 'Accept': 'text/html'},
            timeout=25,
            allow_redirects=True,
        )
        if r.status_code == 404:
            return None, 'not_found'
        if r.status_code != 200:
            print(f"  {C.Y}[!] HTML HTTP {r.status_code}{C.RE}")
            return None, 'blocked'

        html = r.text

        # login wall?
        if 'loginForm' in html and 'ProfilePage' not in html and len(html) < 50000:
            print(f"  {C.Y}[!] Login wall detected{C.RE}")

        patterns = [
            r'window\.__additionalDataLoaded\(\s*[\'"][^\'"]*[\'"]\s*,\s*({.*?})\s*\)\s*;',
            r'window\._sharedData\s*=\s*({.*?});\s*</script>',
        ]
        for pat in patterns:
            m = re.search(pat, html, re.DOTALL)
            if not m:
                continue
            try:
                blob = json.loads(m.group(1))
                user = safe_get(blob, 'graphql', 'user')
                if not user:
                    pages = safe_get(blob, 'entry_data', 'ProfilePage', default=[]) or []
                    if pages:
                        user = safe_get(pages[0], 'graphql', 'user')
                if user:
                    out = parse_user(user)
                    out['_source'] = 'html'
                    return out, 'ok'
            except Exception:
                continue

        # LD+JSON
        m = re.search(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.DOTALL)
        if m:
            try:
                ld = json.loads(m.group(1))
                if ld.get('@type') == 'Person':
                    out = {
                        'username': ld.get('alternateName', username),
                        'full_name': ld.get('name') or '',
                        'bio': ld.get('description') or '',
                        'followers': 0,
                        'following': 0,
                        'posts': 0,
                        'is_private': False,
                        'is_verified': False,
                        'is_business': False,
                        'id': str(ld.get('identifier') or 'N/A'),
                        'external_url': ld.get('url') or '',
                        'profile_pic': ld.get('image') if isinstance(ld.get('image'), str) else '',
                        'category': 'N/A',
                        'highlight_reel_count': 0,
                        '_source': 'ldjson',
                    }
                    # interaction stats
                    for st in ld.get('interactionStatistic') or ld.get('InteractionStatistic') or []:
                        name = (st.get('name') or '').lower()
                        cnt = st.get('userInteractionCount') or 0
                        try:
                            cnt = int(cnt)
                        except Exception:
                            cnt = 0
                        if 'follow' in name and 'ing' not in name:
                            out['followers'] = cnt
                    return out, 'ok'
            except Exception:
                pass

    except Exception as e:
        print(f"  {C.Y}[!] HTML error: {str(e)[:80]}{C.RE}")

    return None, 'blocked'


def fetch_via_instaloader(username):
    print(f"  {C.C}[*] Method C: instaloader{C.RE}")
    try:
        import instaloader
    except ImportError:
        print(f"  {C.Y}[!] instaloader not installed{C.RE}")
        return None, 'no_lib'

    try:
        L = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_comments=False,
            save_metadata=False,
            quiet=True,
            user_agent=IPHONE_UA,
        )

        # optional session file
        session_file = os.path.expanduser('~/.config/camoro/ig_session')
        if os.path.exists(session_file + username if False else ''):
            pass
        # try generic saved session
        conf = os.path.expanduser('~/.config/instaloader/session-camoro')
        # login optional via env
        ig_user = os.environ.get('IG_USER')
        ig_pass = os.environ.get('IG_PASS')
        if ig_user and ig_pass:
            try:
                print(f"  {C.C}[*] Logging in as {ig_user}...{C.RE}")
                L.login(ig_user, ig_pass)
            except Exception as e:
                print(f"  {C.Y}[!] Login failed: {e}{C.RE}")

        profile = instaloader.Profile.from_username(L.context, username)
        out = {
            'username': profile.username,
            'full_name': profile.full_name or '',
            'bio': profile.biography or '',
            'followers': profile.followers,
            'following': profile.followees,
            'posts': profile.mediacount,
            'is_private': profile.is_private,
            'is_verified': profile.is_verified,
            'is_business': profile.is_business_account,
            'id': str(profile.userid),
            'external_url': profile.external_url or '',
            'profile_pic': profile.profile_pic_url,
            'category': profile.business_category_name or 'N/A',
            'highlight_reel_count': 0,
            '_source': 'instaloader',
        }
        return out, 'ok'

    except Exception as e:
        msg = str(e)
        print(f"  {C.Y}[!] instaloader: {msg[:100]}{C.RE}")
        low = msg.lower()
        if '403' in msg or 'forbidden' in low or 'login' in low:
            return None, 'blocked'
        if 'not exist' in low or 'not found' in low or '404' in msg:
            # قد تكون كذبة بسبب 403 — نتحقق لاحقاً
            return None, 'maybe_not_found'
        return None, 'error'


def display(data):
    priv = f"{C.R}PRIVATE{C.RE}" if data['is_private'] else f"{C.G}PUBLIC{C.RE}"
    print(f"\n  Status: {priv}", end='')
    if data.get('is_verified'):
        print(f" | {C.B}VERIFIED{C.RE}", end='')
    if data.get('is_business'):
        print(f" | {C.Y}BUSINESS{C.RE}", end='')
    if data.get('_source'):
        print(f" | {C.D}[{data['_source']}]{C.RE}", end='')
    print()

    rows = [
        ('📛 Username', data['username']),
        ('👤 Full Name', data['full_name'] or '—'),
        ('🆔 User ID', data['id']),
        ('📂 Category', data.get('category') or 'N/A'),
        ('👥 Followers', f"{data['followers']:,}"),
        ('🔗 Following', f"{data['following']:,}"),
        ('📸 Posts', f"{data['posts']:,}"),
    ]
    for k, v in rows:
        print(f"  {C.G}{k}{C.RE}: {C.W}{v}{C.RE}")

    if data.get('bio'):
        print(f"  {C.G}📝 Bio{C.RE}: {C.W}{data['bio']}{C.RE}")
    if data.get('external_url'):
        print(f"  {C.G}🔗 URL{C.RE}: {C.W}{data['external_url']}{C.RE}")
    if data.get('profile_pic'):
        print(f"  {C.G}🖼️  Pic{C.RE}: {C.D}{data['profile_pic'][:70]}...{C.RE}")


def save_results(data, username):
    os.makedirs('output', exist_ok=True)
    path = f'output/{username}_osint.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n  {C.G}[✓] Saved: {path}{C.RE}")

    hints = f'output/{username}_hints.txt'
    words = set()
    words.add(username)
    if data.get('full_name'):
        for p in re.split(r'[\s._-]+', data['full_name']):
            p = re.sub(r'[^0-9A-Za-z\u0600-\u06FF]', '', p)
            if len(p) > 1:
                words.add(p)
    if data.get('bio'):
        for w in re.split(r'\s+', data['bio'].replace('#', ' ').replace('@', ' ')):
            w = re.sub(r'[^0-9A-Za-z\u0600-\u06FF]', '', w)
            if len(w) > 2:
                words.add(w)
    with open(hints, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(words, key=str.lower)))
    print(f"  {C.G}[✓] Hints: {hints}{C.RE}")


def run():
    clear()
    print(f"""
  {C.P}╔══════════════════════════════════════════════╗
  ║       📸 INSTAGRAM OSINT SCANNER              ║
  ║              (multi-method)                   ║
  ╚══════════════════════════════════════════════╝{C.RE}
""")

    username = input(f"  {C.G}[?]{C.RE} Target username {C.W}> {C.RE}").strip().replace('@', '')
    if not username:
        print(f"  {C.R}[!] Username required{C.RE}")
        input(f"  {C.D}Enter...{C.RE}")
        return

    print(f"\n  {C.C}[*] Fetching @{username} ...{C.RE}\n")

    data = None
    statuses = []

    # A: API (الأفضل)
    d, st = fetch_via_api(username)
    statuses.append(('api', st))
    if d:
        data = d

    # B: HTML
    if not data:
        d, st = fetch_via_html(username)
        statuses.append(('html', st))
        if d:
            data = d

    # C: instaloader
    if not data:
        d, st = fetch_via_instaloader(username)
        statuses.append(('instaloader', st))
        if d:
            data = d

    if data:
        display(data)
        save_results(data, username)
        input(f"\n  {C.D}Enter للرجوع...{C.RE}")
        return

    # فشل الكل — تشخيص صحيح
    print(f"\n  {C.R}[✗] Failed to fetch @{username}{C.RE}")
    print(f"  {C.Y}Methods tried: {statuses}{C.RE}\n")

    if any(s == 'not_found' for _, s in statuses) and not any(s == 'blocked' for _, s in statuses):
        print(f"  {C.R}→ الحساب غالباً غير موجود.{C.RE}")
    elif any(s == 'blocked' for _, s in statuses):
        print(f"  {C.Y}→ إنستقرام حاجب الطلبات (403) — الحساب قد يكون موجوداً!{C.RE}")
        print(f"  {C.W}الحلول:{C.RE}")
        print(f"    1. pip3 install -U curl_cffi instaloader requests")
        print(f"    2. فعّل VPN (IP مختلف)")
        print(f"    3. سجّل دخول Instaloader (أقوى):")
        print(f"         export IG_USER='your_ig_user'")
        print(f"         export IG_PASS='your_ig_pass'")
        print(f"         python3 camoro.py")
        print(f"    4. تأكد أن الحساب موجود من المتصفح: instagram.com/{username}")
    else:
        print(f"  {C.Y}→ خطأ شبكة / غير معروف. جرب VPN ثم أعد المحاولة.{C.RE}")

    input(f"\n  {C.D}Enter...{C.RE}")


if __name__ == '__main__':
    run()
