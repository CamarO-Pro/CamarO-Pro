#!/usr/bin/env python3
"""Camoro Module 1 - Instagram OSINT Scanner"""

import os
import sys
import json
from datetime import datetime

class C:
    R = '\033[91m'; G = '\033[92m'; Y = '\033[93m'
    B = '\033[94m'; P = '\033[95m'; C = '\033[96m'
    W = '\033[97m'; BL = '\033[1m'; D = '\033[2m'; RE = '\033[0m'

def run():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"""
  {C.P}╔══════════════════════════════════════════════╗
  ║         📸 INSTAGRAM OSINT SCANNER            ║
  ╚══════════════════════════════════════════════╝{C.RE}
""")

    username = input(f"  {C.G}[?]{C.RE} Target username {C.W}> {C.RE}").strip().replace('@', '')
    if not username:
        print(f"  {C.R}[!] Username required{C.RE}")
        input(); return

    print(f"\n  {C.C}[*] Fetching @{username}...{C.RE}\n")

    data = None
    try:
        import instaloader
        L = instaloader.Instaloader(
            download_pictures=False, download_videos=False,
            download_comments=False, save_metadata=False, quiet=True
        )
        p = instaloader.Profile.from_username(L.context, username)
        data = {
            'username': p.username,
            'full_name': p.full_name or '',
            'bio': p.biography or '',
            'followers': p.followers,
            'following': p.followees,
            'posts': p.mediacount,
            'is_private': p.is_private,
            'is_verified': p.is_verified,
            'is_business': p.is_business_account,
            'id': str(p.userid),
            'external_url': p.external_url or '',
            'profile_pic': p.profile_pic_url,
        }
    except Exception as e:
        print(f"  {C.R}[✗] Failed: {e}{C.RE}")
        input(f"  {C.D}Enter...{C.RE}")
        return

    priv = f"{C.R}PRIVATE{C.RE}" if data['is_private'] else f"{C.G}PUBLIC{C.RE}"
    print(f"  Status: {priv}")
    print(f"  {C.G}📛 Username{C.RE}:  {data['username']}")
    print(f"  {C.G}👤 Full Name{C.RE}: {data['full_name']}")
    print(f"  {C.G}🆔 User ID{C.RE}:   {data['id']}")
    print(f"  {C.G}👥 Followers{C.RE}:  {data['followers']:,}")
    print(f"  {C.G}🔗 Following{C.RE}:  {data['following']:,}")
    print(f"  {C.G}📸 Posts{C.RE}:      {data['posts']:,}")
    if data['bio']:
        print(f"  {C.G}📝 Bio{C.RE}:       {data['bio']}")
    if data['external_url']:
        print(f"  {C.G}🔗 URL{C.RE}:       {data['external_url']}")

    # حفظ للاستخدام في Wordlist + Brute
    os.makedirs('output', exist_ok=True)
    path = f"output/{username}_osint.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n  {C.G}[✓] Saved: {path}{C.RE}")

    # مفاتيح لإعادة استخدامها في wordlist
    hints_path = f"output/{username}_hints.txt"
    with open(hints_path, 'w', encoding='utf-8') as f:
        f.write(data['username'] + '\n')
        if data['full_name']:
            for part in data['full_name'].replace('.', ' ').split():
                if len(part) > 1:
                    f.write(part + '\n')
        if data['bio']:
            for w in data['bio'].replace('#', ' ').replace('@', ' ').split():
                w = ''.join(c for c in w if c.isalnum())
                if len(w) > 2:
                    f.write(w + '\n')
    print(f"  {C.G}[✓] Hints for wordlist: {hints_path}{C.RE}")

    input(f"\n  {C.D}Enter للرجوع...{C.RE}")
