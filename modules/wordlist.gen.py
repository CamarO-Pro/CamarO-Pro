#!/usr/bin/env python3
"""
Camoro Module 2 - AI Wordlist Generator
يسأل عن معلومات شخصية ويولّد قاموس كلمات مرور ضخم
"""

import os
import itertools
import re
from datetime import datetime

class C:
    R = '\033[91m'; G = '\033[92m'; Y = '\033[93m'
    B = '\033[94m'; P = '\033[95m'; C = '\033[96m'
    W = '\033[97m'; BL = '\033[1m'; D = '\033[2m'; RE = '\033[0m'

# رموز واستبدالات شائعة
LEET = {
    'a': ['a', 'A', '4', '@'],
    'e': ['e', 'E', '3'],
    'i': ['i', 'I', '1', '!'],
    'o': ['o', 'O', '0'],
    's': ['s', 'S', '5', '$'],
    't': ['t', 'T', '7'],
    'b': ['b', 'B', '8'],
    'g': ['g', 'G', '9'],
}

COMMON_SUFFIXES = [
    '', '1', '12', '123', '1234', '12345', '123456',
    '!', '!!', '@', '#', '*', '!!',
    '01', '02', '07', '10', '11', '22', '69',
    '00', '99', '007', '2000', '2001', '2002', '2003', '2004',
    '2005', '2006', '2007', '2008', '2009', '2010',
    '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022',
    '2023', '2024', '2025', '2026',
    'qwerty', 'pass', 'password', 'admin', 'instagram', 'insta',
    'ig', 'love', 'Life', 'loveu', 'xxx',
]

COMMON_PREFIXES = ['', '!', '@', '#', 'x', 'xx', 'the']

YEARS = [str(y) for y in range(1980, 2027)]
MONTHS = [f'{m:02d}' for m in range(1, 13)]
DAYS = [f'{d:02d}' for d in range(1, 32)]

SPECIALS = ['!', '@', '#', '$', '%', '&', '*', '_', '.', '']


def ask(prompt, default=''):
    val = input(f"  {C.G}[?]{C.RE} {prompt} {C.D}[{default}]{C.RE} {C.W}> {C.RE}").strip()
    return val if val else default


def yes_no(prompt, default=True):
    d = 'Y/n' if default else 'y/N'
    val = input(f"  {C.G}[?]{C.RE} {prompt} ({d}) {C.W}> {C.RE}").strip().lower()
    if not val:
        return default
    return val in ('y', 'yes', 'نعم', 'o', 'oui')


def clean(s):
    return re.sub(r'[^a-zA-Z0-9á-úà-ùä-ü]', '', s) if s else ''


def variants_case(word):
    if not word or len(word) > 20:
        return {word} if word else set()
    return {
        word.lower(),
        word.upper(),
        word.capitalize(),
        word.title(),
        word.swapcase(),
    }


def leet_variants(word, max_variants=40):
    """توليد استبدالات leetspeak محدودة"""
    word = word.lower()
    results = {word}
    if len(word) > 12:
        return results

    # استبدال حرف واحد فقط في كل مرة + بعض الثنائيات
    for i, ch in enumerate(word):
        if ch in LEET:
            for rep in LEET[ch]:
                if rep != ch:
                    results.add(word[:i] + rep + word[i+1:])
                    if len(results) >= max_variants:
                        return results
    return results


def combine_bases(bases):
    """دمج الكلمات الاساسية: name+year, name+name2, ..."""
    out = set()
    bases = [b for b in bases if b and len(b) >= 2]

    for b in bases:
        out.add(b)

    # ثنائيات
    for a, b in itertools.permutations(bases, 2):
        if len(a) + len(b) <= 20:
            out.add(a + b)
            out.add(a + '_' + b)
            out.add(a + '.' + b)

    return out


def generate_wordlist(info, target_count=18000):
    """محرك توليد الكلمات الذكي"""
    passwords = set()

    # جمع القواعد
    base_words = []
    for key in [
        'username', 'first_name', 'last_name', 'nickname',
        'partner', 'father', 'mother', 'child', 'friend',
        'pet', 'city', 'country', 'school', 'team',
        'job', 'keyword1', 'keyword2', 'keyword3', 'keyword4',
        'keyword5', 'company', 'hobby'
    ]:
        v = clean(info.get(key, ''))
        if v:
            base_words.append(v)
            base_words.extend(list(variants_case(v)))

    # تاريخ الميلاد ومكونات
    day = info.get('birth_day', '')
    month = info.get('birth_month', '')
    year = info.get('birth_year', '')
    phone = re.sub(r'\D', '', info.get('phone', ''))
    plate = clean(info.get('plate', ''))

    number_bits = []
    if day: number_bits.append(day.zfill(2))
    if month: number_bits.append(month.zfill(2))
    if year:
        number_bits.append(year)
        number_bits.append(year[-2:])
    if day and month:
        number_bits.append(day.zfill(2) + month.zfill(2))
        number_bits.append(month.zfill(2) + day.zfill(2))
    if day and month and year:
        number_bits.extend([
            day.zfill(2) + month.zfill(2) + year,
            day.zfill(2) + month.zfill(2) + year[-2:],
            year + month.zfill(2) + day.zfill(2),
        ])
    if phone:
        number_bits.append(phone)
        if len(phone) >= 4:
            number_bits.append(phone[-4:])
            number_bits.append(phone[-6:])
        if len(phone) >= 8:
            number_bits.append(phone[:8])
    if plate:
        number_bits.append(plate)

    number_bits.extend(['123', '1234', '12345', '123456', '111', '000', '007', '69', '99', '100'])
    number_bits.extend(YEARS[-30:])  # آخر 30 سنة

    # 1) كلمات + suffixes
    print(f"  {C.C}[*] Stage 1: base + suffixes...{C.RE}")
    unique_bases = list(set(b.lower() for b in base_words if 2 <= len(b) <= 16))

    for base in unique_bases:
        for case_v in variants_case(base):
            for suf in COMMON_SUFFIXES:
                passwords.add(case_v + suf)
            for pre in COMMON_PREFIXES:
                passwords.add(pre + case_v)
            for n in number_bits:
                passwords.add(case_v + n)
                passwords.add(case_v + '_' + n)
                passwords.add(n + case_v)

    # 2) leet speak
    print(f"  {C.C}[*] Stage 2: leetspeak...{C.RE}")
    for base in unique_bases[:15]:
        for lv in leet_variants(base):
            passwords.add(lv)
            for n in number_bits[:20]:
                passwords.add(lv + n)
            for s in SPECIALS:
                passwords.add(lv + s)
                passwords.add(lv + n if n else lv) if False else None
            for suf in ['123', '1234', '!', '@', '2020', '2024', '2025', '2026']:
                passwords.add(lv + suf)

    # 3) دمج اسمين
    print(f"  {C.C}[*] Stage 3: name combinations...{C.RE}")
    primary = [clean(info.get(k, '')).lower() for k in
               ['first_name', 'last_name', 'nickname', 'partner', 'pet', 'username'] if info.get(k)]
    primary = [p for p in primary if len(p) >= 2][:6]

    for a, b in itertools.permutations(primary, 2):
        for sep in ['', '_', '.', '']:
            combo = a + sep + b
            if len(combo) <= 20:
                passwords.add(combo)
                for n in number_bits[:25]:
                    passwords.add(combo + n)
                for s in ['!', '123', '1234', '2024', '2025', '2026']:
                    passwords.add(combo + s)

    # 4) أنماط إنستقرام شائعة
    print(f"  {C.C}[*] Stage 4: Instagram patterns...{C.RE}")
    ig_patterns = ['ig', 'insta', 'instagram', 'ig_', '_ig', 'official', 'real', 'its']
    for base in unique_bases[:10]:
        for p in ig_patterns:
            passwords.add(p + base)
            passwords.add(base + p)
            passwords.add(base + '_' + p)

    # 5) لوحة المفاتيح وأنماط
    print(f"  {C.C}[*] Stage 5: keyboard & common patterns...{C.RE}")
    keyboard = [
        'qwerty', 'qwertyuiop', 'asdfgh', 'zxcvbn', 'qazwsx',
        'password', 'password1', 'Password1', 'Password123',
        'iloveyou', 'welcome', 'monkey', 'dragon', 'master',
        'letmein', 'football', 'baseball', 'sunshine', 'princess',
        'admin123', 'root', 'toor', 'passw0rd', 'p@ssw0rd',
        'abc123', 'abcd1234', 'aaa111', 'xyz123',
    ]
    for k in keyboard:
        passwords.add(k)
        for n in number_bits[:10]:
            passwords.add(k + n)

    # 6) توسعة للوصول لـ ~18000
    print(f"  {C.C}[*] Stage 6: expansion to ~{target_count}...{C.RE}")
    base_snapshot = list(passwords)[:3000]
    extra_nums = [str(i) for i in range(0, 100)] + [f'{i:02d}' for i in range(0, 100)]
    extra_suf = ['!', '!!', '!!!', '@', '@@', '#', '##', '*', '**', '.', '_',
                 'x', 'xx', 'xxx', '1!', '12!', '123!', 'a', 'z',
                 '00', '01', '10', '11', '22', '88', '99']

    for pw in base_snapshot:
        if len(passwords) >= target_count:
            break
        if 4 <= len(pw) <= 14:
            for s in extra_suf:
                passwords.add(pw + s)
                if len(passwords) >= target_count:
                    break
            for n in extra_nums:
                passwords.add(pw + n)
                if len(passwords) >= target_count:
                    break

    # تصفية: فقط كلمات 4-30 حرف
    final = sorted(
        {p for p in passwords if 4 <= len(p) <= 30 and p.strip()},
        key=lambda x: (len(x), x)
    )

    return final[:max(target_count, len(final))]


def collect_info():
    """أسئلة جمع المعلومات"""
    print(f"""
  {C.P}╔══════════════════════════════════════════════════╗
  ║       🧠 AI WORDLIST GENERATOR                   ║
  ║   أجب على الأسئلة لتوليد قاموس ذكي                ║
  ╚══════════════════════════════════════════════════╝{C.RE}
""")
    info = {}

    print(f"  {C.Y}── معلومات الحساب ──{C.RE}")
    info['username'] = ask('اسم المستخدم (Username)')
    info['nickname'] = ask('لقب / Nickname')

    print(f"\n  {C.Y}── المعلومات الشخصية ──{C.RE}")
    info['first_name'] = ask('الاسم الحقيقي (First name)')
    info['last_name'] = ask('اسم العائلة (Last name)')
    info['birth_day'] = ask('يوم الميلاد (01-31)', '')
    info['birth_month'] = ask('شهر الميلاد (01-12)', '')
    info['birth_year'] = ask('سنة الميلاد (YYYY)', '')
    info['phone'] = ask('رقم الهاتف (اختياري)', '')
    info['city'] = ask('المدينة', '')
    info['country'] = ask('البلد', '')

    print(f"\n  {C.Y}── العائلة والعلاقات ──{C.RE}")
    info['partner'] = ask('اسم الشريك / الحبيب(ة)', '')
    info['father'] = ask('اسم الأب', '')
    info['mother'] = ask('اسم الأم', '')
    info['child'] = ask('اسم الابن/الابنة', '')
    info['friend'] = ask('اسم صديق مقرب', '')
    info['pet'] = ask('اسم الحيوانات الأليفة', '')

    print(f"\n  {C.Y}── اهتمامات ──{C.RE}")
    info['school'] = ask('المدرسة / الجامعة', '')
    info['team'] = ask('فريق كرة / نادي', '')
    info['job'] = ask('المهنة', '')
    info['company'] = ask('اسم الشركة', '')
    info['hobby'] = ask('هواية', '')
    info['plate'] = ask('رقم لوحة سيارة', '')

    print(f"\n  {C.Y}── كلمات مفتاحية إضافية ──{C.RE}")
    info['keyword1'] = ask('كلمة مفتاحية 1', '')
    info['keyword2'] = ask('كلمة مفتاحية 2', '')
    info['keyword3'] = ask('كلمة مفتاحية 3', '')
    info['keyword4'] = ask('كلمة مفتاحية 4', '')
    info['keyword5'] = ask('كلمة مفتاحية 5', '')

    # دمج hints من OSINT إن وجدت
    if info['username']:
        hints = f"output/{info['username']}_hints.txt"
        if os.path.exists(hints):
            if yes_no(f'استخدام hints من OSINT ({hints})؟', True):
                with open(hints, encoding='utf-8') as f:
                    extras = [l.strip() for l in f if l.strip()]
                for i, w in enumerate(extras[:5]):
                    key = f'keyword{i+1}'
                    if not info.get(key):
                        info[key] = w
                print(f"  {C.G}[✓] Merged {len(extras)} OSINT hints{C.RE}")

    return info


def run():
    os.system('clear' if os.name == 'posix' else 'cls')
    info = collect_info()

    target = ask('عدد كلمات المرور المطلوبة', '18000')
    try:
        target = int(target)
    except ValueError:
        target = 18000

    print(f"\n  {C.C}[*] Generating smart wordlist...{C.RE}")
    passwords = generate_wordlist(info, target_count=target)
    print(f"  {C.G}[✓] Generated: {len(passwords):,} passwords{C.RE}")

    os.makedirs('wordlists', exist_ok=True)
    os.makedirs('output', exist_ok=True)

    uname = info.get('username') or 'target'
    out_path = f"wordlists/{uname}_wordlist.txt"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(passwords))

    # أيضاً نسخة في output
    out2 = f"output/{uname}_wordlist.txt"
    with open(out2, 'w', encoding='utf-8') as f:
        f.write('\n'.join(passwords))

    print(f"\n  {C.G}[✓] Saved: {out_path}{C.RE}")
    print(f"  {C.G}[✓] Saved: {out2}{C.RE}")
    print(f"  {C.Y}[*] Sample (first 15):{C.RE}")
    for p in passwords[:15]:
        print(f"      {C.W}{p}{C.RE}")

    input(f"\n  {C.D}Enter للرجوع...{C.RE}")
    return out_path
