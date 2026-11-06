#!/usr/bin/env python3
"""Check that every lemma/rule/restriction quoted in <pre> blocks of the markup JSONs
appears verbatim (modulo whitespace) in lightning.spthy or lightning_aux.spthy.

  python3 -I check_verbatim.py markup1.json [...]
"""
import html
import json
import re
import sys

F = '/home/user/12345/tamarin/final/'
SRC = re.sub(r'\s+', ' ', re.sub(r'//[^\n]*', '', open(F + 'lightning.spthy').read() + '\n' + open(F + 'lightning_aux.spthy').read()))
NAMES = set(re.findall(r'\b(?:lemma|rule|restriction)\s+([A-Za-z0-9_]+)', SRC))


def norm(s):
    s = re.sub(r'//[^\n]*', '', s)             # drop line comments
    s = re.sub(r'^\s*\d+\s', ' ', s, flags=re.M)  # drop listing line numbers
    return re.sub(r'\s+', ' ', s).strip()


bad = 0
total = 0
for path in sys.argv[1:]:
    m = json.load(open(path))
    items = [(f"note p{n['page']} @{n['anchor'][:30]!r}", n['html']) for n in m['notes']] + \
            [(f"insert after p{i['after_page']} {i['title'][:30]!r}", i['html']) for i in m['inserts']]
    for where, h in items:
        for pre in re.findall(r'<pre>(.*?)</pre>', h, flags=re.S):
            text = html.unescape(re.sub(r'<[^>]+>', '', pre))
            for name in re.findall(r'\b(?:lemma|rule|restriction)\s+([A-Za-z0-9_]+)', text):
                if name not in NAMES:
                    bad += 1
                    print(f'[{m["section"]}] {where}: UNKNOWN NAME {name}')
            # check each quoted formula "..." and each rule body verbatim
            for q in re.findall(r'"([^"]{20,})"', text):
                total += 1
                if norm(q) not in SRC:
                    bad += 1
                    print(f'[{m["section"]}] {where}: formula NOT verbatim:\n    {norm(q)[:300]}')
            for r in re.findall(r'(rule\s+[A-Za-z0-9_]+\s*:.*?\]\s*(?=$|\n\s*\n|rule\s))', text, flags=re.S):
                total += 1
                if norm(r) not in SRC:
                    bad += 1
                    print(f'[{m["section"]}] {where}: rule NOT verbatim:\n    {norm(r)[:300]}')
        # names cited in <code> must exist (lemma-like identifiers only)
        for c in re.findall(r'<code>([A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+)</code>', h):
            if c not in NAMES and not c.startswith(('lightning', 'NO_', 'Tarmin')):
                print(f'[{m["section"]}] {where}: code name not a lemma/rule/restriction: {c}')
print(f'checked {total} quoted formulas/rules, {bad} problems')
