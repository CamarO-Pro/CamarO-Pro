#!/usr/bin/env python3
"""Camoro Module 1 - Instagram OSINT Scanner (multi-method, fixed errors)."""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Dict, Optional, Tuple

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

IG_APP_ID = "936619743392459"
IPHONE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 "
    "Mobile/15E148 Safari/604.1"
)


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


def get_requests():
    try:
        from curl_cffi import requests as r  # type: ignore

        return r, True
    except Exception:
        try:
            import requests as r  # type: ignore

            return r, False
        except Exception as e:
            raise RuntimeError("Install requests or curl_cffi: pip3 install requests curl_cffi") from e


def safe_get(d: Any, *keys: str, default: Any = None) -> Any:
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
        if cur is default:
            return default
    return cur


def parse_user(user: Dict[str, Any]) -> Dict[str, Any]:
    followers = (
        user.get("follower_count")
        or safe_get(user, "edge_followed_by", "count", default=0)
        or 0
    )
    following = (
        user.get("following_count")
        or safe_get(user, "edge_follow", "count", default=0)
        or 0
    )
    posts = (
        user.get("media_count")
        or safe_get(user, "edge_owner_to_timeline_media", "count", default=0)
        or 0
    )
    pp = user.get("profile_pic_url_hd") or user.get("profile_pic_url") or ""
    ext = user.get("external_url") or ""
    if not ext:
        links = user.get("bio_links") or []
        if isinstance(links, list) and links and isinstance(links[0], dict):
            ext = links[0].get("url") or ""

    try:
        followers_i = int(followers or 0)
    except Exception:
        followers_i = 0
    try:
        following_i = int(following or 0)
    except Exception:
        following_i = 0
    try:
        posts_i = int(posts or 0)
    except Exception:
        posts_i = 0

    return {
        "username": user.get("username") or "N/A",
        "full_name": user.get("full_name") or "",
        "bio": user.get("biography") or user.get("bio") or "",
        "followers": followers_i,
        "following": following_i,
        "posts": posts_i,
        "is_private": bool(user.get("is_private", False)),
        "is_verified": bool(user.get("is_verified", False)),
        "is_business": bool(user.get("is_business_account", user.get("is_business", False))),
        "id": str(user.get("id") or user.get("pk") or "N/A"),
        "external_url": ext,
        "profile_pic": pp,
        "category": user.get("category_name") or user.get("category") or "N/A",
        "highlight_reel_count": int(user.get("highlight_reel_count") or 0),
    }


def fetch_via_api(username: str) -> Tuple[Optional[Dict[str, Any]], str]:
    try:
        req, has_cffi = get_requests()
    except Exception as e:
        print(f"  {C.R}[!] {e}{C.RE}")
        return None, "no_lib"

    print(
        f"  {C.C}[*] Method A: web_profile_info API"
        f"{' (curl_cffi)' if has_cffi else ' (requests)'}{C.RE}"
    )

    try:
        session = req.Session()
        session.headers.update(
            {
                "User-Agent": IPHONE_UA,
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
            }
        )
    except Exception as e:
        print(f"  {C.Y}[!] Session error: {e}{C.RE}")
        return None, "error"

    try:
        session.get("https://www.instagram.com/", timeout=20)
    except Exception as e:
        print(f"  {C.Y}[!] Warmup warn: {str(e)[:70]}{C.RE}")

    urls = [
        f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}",
        f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}",
    ]

    blocked = False
    for url in urls:
        try:
            headers = {
                "x-ig-app-id": IG_APP_ID,
                "x-requested-with": "XMLHttpRequest",
                "Origin": "https://www.instagram.com",
                "Referer": f"https://www.instagram.com/{username}/",
                "Sec-Fetch-Site": "same-site",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
            }
            r = session.get(url, headers=headers, timeout=25)
            host = url.split("/")[2]
            print(f"  {C.D}    {host} → HTTP {r.status_code}{C.RE}")

            if r.status_code == 404:
                return None, "not_found"
            if r.status_code == 403:
                blocked = True
                print(f"  {C.Y}[!] 403 Forbidden on {host}{C.RE}")
                continue
            if r.status_code != 200:
                continue

            try:
                data = r.json()
            except Exception:
                continue

            user = safe_get(data, "data", "user")
            if user and isinstance(user, dict):
                out = parse_user(user)
                out["_source"] = host
                return out, "ok"
        except Exception as e:
            print(f"  {C.Y}[!] API error: {str(e)[:80]}{C.RE}")

    return None, "blocked" if blocked else "error"


def fetch_via_html(username: str) -> Tuple[Optional[Dict[str, Any]], str]:
    print(f"  {C.C}[*] Method B: HTML / LD+JSON{C.RE}")
    try:
        req, _ = get_requests()
    except Exception as e:
        print(f"  {C.R}[!] {e}{C.RE}")
        return None, "no_lib"

    try:
        r = req.get(
            f"https://www.instagram.com/{username}/",
            headers={"User-Agent": IPHONE_UA, "Accept": "text/html"},
            timeout=25,
            allow_redirects=True,
        )
    except Exception as e:
        print(f"  {C.Y}[!] HTML request error: {str(e)[:80]}{C.RE}")
        return None, "error"

    if r.status_code == 404:
        return None, "not_found"
    if r.status_code == 403:
        print(f"  {C.Y}[!] HTML 403 Forbidden{C.RE}")
        return None, "blocked"
    if r.status_code != 200:
        print(f"  {C.Y}[!] HTML HTTP {r.status_code}{C.RE}")
        return None, "blocked"

    html = r.text or ""

    patterns = [
        r"window\.__additionalDataLoaded\(\s*['\"][^'\"]*['\"]\s*,\s*({.*?})\s*\)\s*;",
        r"window\._sharedData\s*=\s*({.*?});\s*</script>",
    ]
    for pat in patterns:
        m = re.search(pat, html, re.DOTALL)
        if not m:
            continue
        try:
            blob = json.loads(m.group(1))
            user = safe_get(blob, "graphql", "user")
            if not user:
                pages = safe_get(blob, "entry_data", "ProfilePage", default=[]) or []
                if pages and isinstance(pages, list):
                    user = safe_get(pages[0], "graphql", "user")
            if user and isinstance(user, dict):
                out = parse_user(user)
                out["_source"] = "html"
                return out, "ok"
        except Exception:
            continue

    m = re.search(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        html,
        re.DOTALL,
    )
    if m:
        try:
            ld = json.loads(m.group(1))
            if isinstance(ld, dict) and ld.get("@type") == "Person":
                img = ld.get("image")
                if isinstance(img, dict):
                    img = img.get("url") or ""
                out = {
                    "username": ld.get("alternateName") or username,
                    "full_name": ld.get("name") or "",
                    "bio": ld.get("description") or "",
                    "followers": 0,
                    "following": 0,
                    "posts": 0,
                    "is_private": False,
                    "is_verified": False,
                    "is_business": False,
                    "id": str(ld.get("identifier") or "N/A"),
                    "external_url": ld.get("url") or "",
                    "profile_pic": img if isinstance(img, str) else "",
                    "category": "N/A",
                    "highlight_reel_count": 0,
                    "_source": "ldjson",
                }
                stats = ld.get("interactionStatistic") or ld.get("InteractionStatistic") or []
                if isinstance(stats, list):
                    for st in stats:
                        if not isinstance(st, dict):
                            continue
                        name = (st.get("name") or "").lower()
                        try:
                            cnt = int(st.get("userInteractionCount") or 0)
                        except Exception:
                            cnt = 0
                        if "follow" in name and "ing" not in name:
                            out["followers"] = cnt
                return out, "ok"
        except Exception:
            pass

    return None, "blocked"


def fetch_via_instaloader(username: str) -> Tuple[Optional[Dict[str, Any]], str]:
    print(f"  {C.C}[*] Method C: instaloader{C.RE}")
    try:
        import instaloader  # type: ignore
    except Exception:
        print(f"  {C.Y}[!] instaloader not installed{C.RE}")
        return None, "no_lib"

    try:
        L = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_comments=False,
            save_metadata=False,
            quiet=True,
            user_agent=IPHONE_UA,
        )

        ig_user = os.environ.get("IG_USER")
        ig_pass = os.environ.get("IG_PASS")
        if ig_user and ig_pass:
            try:
                print(f"  {C.C}[*] Login as {ig_user}...{C.RE}")
                L.login(ig_user, ig_pass)
            except Exception as e:
                print(f"  {C.Y}[!] Login failed: {e}{C.RE}")

        profile = instaloader.Profile.from_username(L.context, username)
        out = {
            "username": profile.username,
            "full_name": profile.full_name or "",
            "bio": profile.biography or "",
            "followers": int(profile.followers or 0),
            "following": int(profile.followees or 0),
            "posts": int(profile.mediacount or 0),
            "is_private": bool(profile.is_private),
            "is_verified": bool(profile.is_verified),
            "is_business": bool(profile.is_business_account),
            "id": str(profile.userid),
            "external_url": profile.external_url or "",
            "profile_pic": profile.profile_pic_url or "",
            "category": profile.business_category_name or "N/A",
            "highlight_reel_count": 0,
            "_source": "instaloader",
        }
        return out, "ok"
    except Exception as e:
        msg = str(e)
        print(f"  {C.Y}[!] instaloader: {msg[:100]}{C.RE}")
        low = msg.lower()
        if "403" in msg or "forbidden" in low or "login" in low:
            return None, "blocked"
        if "not exist" in low or "not found" in low or "404" in msg:
            return None, "maybe_not_found"
        return None, "error"


def display(data: Dict[str, Any]) -> None:
    priv = f"{C.R}PRIVATE{C.RE}" if data.get("is_private") else f"{C.G}PUBLIC{C.RE}"
    line = f"  Status: {priv}"
    if data.get("is_verified"):
        line += f" | {C.B}VERIFIED{C.RE}"
    if data.get("is_business"):
        line += f" | {C.Y}BUSINESS{C.RE}"
    if data.get("_source"):
        line += f" | {C.D}[{data['_source']}]{C.RE}"
    print("\n" + line)

    rows = [
        ("Username", data.get("username")),
        ("Full Name", data.get("full_name") or "—"),
        ("User ID", data.get("id")),
        ("Category", data.get("category") or "N/A"),
        ("Followers", f"{int(data.get('followers') or 0):,}"),
        ("Following", f"{int(data.get('following') or 0):,}"),
        ("Posts", f"{int(data.get('posts') or 0):,}"),
    ]
    for k, v in rows:
        print(f"  {C.G}{k}{C.RE}: {C.W}{v}{C.RE}")

    if data.get("bio"):
        print(f"  {C.G}Bio{C.RE}: {C.W}{data['bio']}{C.RE}")
    if data.get("external_url"):
        print(f"  {C.G}URL{C.RE}: {C.W}{data['external_url']}{C.RE}")
    if data.get("profile_pic"):
        pic = str(data["profile_pic"])
        print(f"  {C.G}Pic{C.RE}: {C.D}{pic[:70]}{'...' if len(pic) > 70 else ''}{C.RE}")


def save_results(data: Dict[str, Any], username: str) -> None:
    try:
        os.makedirs("output", exist_ok=True)
    except Exception as e:
        print(f"  {C.Y}[!] cannot create output/: {e}{C.RE}")
        return

    path = f"output/{username}_osint.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n  {C.G}[✓] Saved: {path}{C.RE}")
    except Exception as e:
        print(f"  {C.R}[!] Save JSON failed: {e}{C.RE}")

    words = set()
    words.add(username)
    if data.get("full_name"):
        for p in re.split(r"[\s._-]+", str(data["full_name"])):
            p = re.sub(r"[^0-9A-Za-z\u0600-\u06FF]", "", p)
            if len(p) > 1:
                words.add(p)
    if data.get("bio"):
        bio = str(data["bio"]).replace("#", " ").replace("@", " ")
        for w in re.split(r"\s+", bio):
            w = re.sub(r"[^0-9A-Za-z\u0600-\u06FF]", "", w)
            if len(w) > 2:
                words.add(w)

    hints = f"output/{username}_hints.txt"
    try:
        with open(hints, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(words, key=str.lower)))
        print(f"  {C.G}[✓] Hints: {hints}{C.RE}")
    except Exception as e:
        print(f"  {C.Y}[!] Save hints failed: {e}{C.RE}")


def run() -> None:
    clear()
    print(
        f"""
  {C.P}╔══════════════════════════════════════════════╗
  ║       INSTAGRAM OSINT SCANNER                 ║
  ║              (multi-method)                   ║
  ╚══════════════════════════════════════════════╝{C.RE}
"""
    )

    try:
        username = input(f"  {C.G}[?]{C.RE} Target username {C.W}> {C.RE}").strip().replace("@", "")
    except (EOFError, KeyboardInterrupt):
        return

    if not username:
        print(f"  {C.R}[!] Username required{C.RE}")
        pause()
        return

    print(f"\n  {C.C}[*] Fetching @{username} ...{C.RE}\n")

    data: Optional[Dict[str, Any]] = None
    statuses = []

    for fn, label in (
        (fetch_via_api, "api"),
        (fetch_via_html, "html"),
        (fetch_via_instaloader, "instaloader"),
    ):
        if data:
            break
        try:
            d, st = fn(username)
            statuses.append((label, st))
            if d:
                data = d
        except Exception as e:
            statuses.append((label, f"exc:{e}"))
            print(f"  {C.Y}[!] {label} exception: {e}{C.RE}")

    if data:
        display(data)
        save_results(data, username)
        pause()
        return

    print(f"\n  {C.R}[✗] Failed to fetch @{username}{C.RE}")
    print(f"  {C.Y}Methods: {statuses}{C.RE}\n")

    only_not_found = any(s == "not_found" for _, s in statuses) and not any(
        s == "blocked" for _, s in statuses
    )
    if only_not_found:
        print(f"  {C.R}→ Profile likely does not exist.{C.RE}")
    elif any(s == "blocked" for _, s in statuses) or any(s == "maybe_not_found" for _, s in statuses):
        print(f"  {C.Y}→ Instagram blocked requests (403). Profile may still exist.{C.RE}")
        print(f"  {C.W}Try:{C.RE}")
        print("    1) pip3 install -U curl_cffi instaloader requests")
        print("    2) Enable VPN")
        print("    3) export IG_USER='user' && export IG_PASS='pass'")
        print(f"    4) Open in browser: https://www.instagram.com/{username}/")
    else:
        print(f"  {C.Y}→ Network/unknown error. Retry with VPN.{C.RE}")

    pause()


if __name__ == "__main__":
    run()
