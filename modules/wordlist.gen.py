#!/usr/bin/env python3
"""Camoro Module 2 - AI Wordlist Generator (~18000 passwords)."""

from __future__ import annotations

import itertools
import os
import re
from typing import Dict, List, Set

class C:
    R = "\033[91m"
    G = "\033[92m"
    Y = "\033[93m"
    C = "\033[96m"
    W = "\033[97m"
    D = "\033[2m"
    P = "\033[95m"
    BL = "\033[1m"
    RE = "\033[0m"


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


def clean(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"[^0-9A-Za-z\u0600-\u06FF]", "", s)


def variants_case(word: str) -> List[str]:
    if not word:
        return []
    return list(
        dict.fromkeys(
            [
                word,
                word.lower(),
                word.upper(),
                word.capitalize(),
                word.title(),
            ]
        )
    )


def leet_simple(word: str) -> List[str]:
    table = str.maketrans({"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"})
    low = word.lower()
    out = {low, low.translate(table)}
    # single replacements
    reps = {"a": "@", "i": "!", "s": "$"}
    for i, ch in enumerate(low):
        if ch in reps:
            out.add(low[:i] + reps[ch] + low[i + 1 :])
    return list(out)


def generate_wordlist(info: Dict[str, str], target_count: int = 18000) -> List[str]:
    passwords: Set[str] = set()

    base_keys = [
        "username",
        "first_name",
        "last_name",
        "nickname",
        "partner",
        "father",
        "mother",
        "child",
        "friend",
        "pet",
        "city",
        "country",
        "school",
        "team",
        "job",
        "company",
        "hobby",
        "keyword1",
        "keyword2",
        "keyword3",
        "keyword4",
        "keyword5",
    ]

    bases: List[str] = []
    for k in base_keys:
        w = clean(info.get(k, ""))
        if len(w) >= 2:
            bases.extend(variants_case(w))

    # OSINT hints
    uname = clean(info.get("username", "")) or "target"
    hints_path = f"output/{uname}_hints.txt"
    if os.path.isfile(hints_path):
        try:
            with open(hints_path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    w = clean(line.strip())
                    if len(w) >= 2:
                        bases.append(w.lower())
        except Exception:
            pass

    bases = list(dict.fromkeys([b for b in bases if 2 <= len(b) <= 20]))

    day = (info.get("birth_day") or "").strip()
    month = (info.get("birth_month") or "").strip()
    year = (info.get("birth_year") or "").strip()
    phone = re.sub(r"\D", "", info.get("phone") or "")
    plate = clean(info.get("plate") or "")

    nums: List[str] = [
        "",
        "1",
        "12",
        "123",
        "1234",
        "12345",
        "123456",
        "!",
        "!!",
        "@",
        "#",
        "*",
        "00",
        "01",
        "07",
        "10",
        "11",
        "22",
        "69",
        "99",
        "007",
    ]
    nums.extend([str(y) for y in range(1990, 2027)])
    if day:
        nums.append(day.zfill(2))
    if month:
        nums.append(month.zfill(2))
    if year:
        nums.append(year)
        if len(year) >= 2:
            nums.append(year[-2:])
    if day and month:
        nums.append(day.zfill(2) + month.zfill(2))
        nums.append(month.zfill(2) + day.zfill(2))
    if day and month and year:
        nums.extend(
            [
                day.zfill(2) + month.zfill(2) + year,
                day.zfill(2) + month.zfill(2) + year[-2:],
                year + month.zfill(2) + day.zfill(2),
            ]
        )
    if phone:
        nums.append(phone)
        if len(phone) >= 4:
            nums.append(phone[-4:])
        if len(phone) >= 6:
            nums.append(phone[-6:])
    if plate:
        nums.append(plate)

    nums = list(dict.fromkeys(nums))

    print(f"  {C.C}[*] Stage 1: bases + numbers...{C.RE}")
    for b in bases:
        for n in nums:
            passwords.add(b + n)
            if n:
                passwords.add(b + "_" + n)
                passwords.add(b + "." + n)
                passwords.add(n + b)
        for pre in ("", "!", "@", "x", "the"):
            passwords.add(pre + b)
        for suf in ("ig", "insta", "instagram", "_ig", "official", "real"):
            passwords.add(b + suf)
            passwords.add(suf + b)

    print(f"  {C.C}[*] Stage 2: leet...{C.RE}")
    for b in bases[:20]:
        for lv in leet_simple(b):
            passwords.add(lv)
            for n in nums[:40]:
                passwords.add(lv + n)

    print(f"  {C.C}[*] Stage 3: name pairs...{C.RE}")
    primary = []
    for k in ("first_name", "last_name", "nickname", "partner", "pet", "username"):
        w = clean(info.get(k, "")).lower()
        if len(w) >= 2:
            primary.append(w)
    primary = list(dict.fromkeys(primary))[:8]
    for a, b in itertools.permutations(primary, 2):
        if len(a) + len(b) <= 18:
            for sep in ("", "_", "."):
                combo = a + sep + b
                passwords.add(combo)
                for n in nums[:30]:
                    passwords.add(combo + n)

    print(f"  {C.C}[*] Stage 4: commons...{C.RE}")
    commons = [
        "password",
        "Password1",
        "password123",
        "qwerty",
        "qwerty123",
        "iloveyou",
        "admin123",
        "welcome",
        "monkey",
        "dragon",
        "abc123",
        "insta",
        "instagram",
        "passw0rd",
        "p@ssw0rd",
    ]
    passwords.update(commons)
    if uname:
        passwords.update([uname + "123", uname + "2024", uname + "2025", uname + "2026"])

    print(f"  {C.C}[*] Stage 5: expand to ~{target_count}...{C.RE}")
    snap = list(passwords)[:3000]
    extra_s = ["!", "!!", "1", "12", "123", "1234", "2024", "2025", "2026", "x", "xx", "xxx", "00", "99"]
    for p in snap:
        if len(passwords) >= target_count + 500:
            break
        if 4 <= len(p) <= 16:
            for s in extra_s:
                passwords.add(p + s)

    final = sorted({p for p in passwords if 4 <= len(p) <= 30}, key=lambda x: (len(x), x))
    return final[: max(target_count, min(len(final), target_count))]


def collect_info() -> Dict[str, str]:
    print(
        f"""
  {C.P}╔══════════════════════════════════════════════════╗
  ║       AI WORDLIST GENERATOR                      ║
  ║   أجب على الأسئلة لتوليد قاموس ذكي                ║
  ╚══════════════════════════════════════════════════╝{C.RE}
"""
    )
    info: Dict[str, str] = {}
    print(f"  {C.Y}-- Account --{C.RE}")
    info["username"] = ask("Username / target", "target")
    info["nickname"] = ask("Nickname")

    print(f"\n  {C.Y}-- Personal --{C.RE}")
    info["first_name"] = ask("First name")
    info["last_name"] = ask("Last name")
    info["birth_day"] = ask("Birth day DD")
    info["birth_month"] = ask("Birth month MM")
    info["birth_year"] = ask("Birth year YYYY")
    info["phone"] = ask("Phone")
    info["city"] = ask("City")
    info["country"] = ask("Country")

    print(f"\n  {C.Y}-- Relations --{C.RE}")
    info["partner"] = ask("Partner name")
    info["father"] = ask("Father name")
    info["mother"] = ask("Mother name")
    info["child"] = ask("Child name")
    info["friend"] = ask("Friend name")
    info["pet"] = ask("Pet name")

    print(f"\n  {C.Y}-- Extra --{C.RE}")
    info["school"] = ask("School / University")
    info["team"] = ask("Team / Club")
    info["job"] = ask("Job")
    info["company"] = ask("Company")
    info["hobby"] = ask("Hobby")
    info["plate"] = ask("Car plate")
    info["keyword1"] = ask("Keyword 1")
    info["keyword2"] = ask("Keyword 2")
    info["keyword3"] = ask("Keyword 3")
    info["keyword4"] = ask("Keyword 4")
    info["keyword5"] = ask("Keyword 5")
    return info


def run() -> None:
    clear()
    info = collect_info()

    raw = ask("Password count", "18000")
    try:
        target = int(raw)
        if target < 100:
            target = 100
        if target > 200000:
            target = 200000
    except Exception:
        target = 18000

    print(f"\n  {C.C}[*] Generating smart wordlist...{C.RE}")
    try:
        passwords = generate_wordlist(info, target_count=target)
    except Exception as e:
        print(f"  {C.R}[✗] Generate failed: {e}{C.RE}")
        pause()
        return

    uname = clean(info.get("username") or "target") or "target"
    try:
        os.makedirs("wordlists", exist_ok=True)
        os.makedirs("output", exist_ok=True)
    except Exception as e:
        print(f"  {C.R}[!] mkdir failed: {e}{C.RE}")
        pause()
        return

    path = f"wordlists/{uname}_wordlist.txt"
    path2 = f"output/{uname}_wordlist.txt"
    text = "\n".join(passwords)

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        with open(path2, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        print(f"  {C.R}[✗] Save failed: {e}{C.RE}")
        pause()
        return

    print(f"  {C.G}[✓] Generated: {len(passwords):,} passwords{C.RE}")
    print(f"  {C.G}[✓] Saved: {path}{C.RE}")
    print(f"  {C.G}[✓] Saved: {path2}{C.RE}")
    print(f"  {C.Y}Sample:{C.RE}")
    for p in passwords[:15]:
        print(f"    {C.W}{p}{C.RE}")
    pause()


if __name__ == "__main__":
    run()
