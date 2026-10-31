#!/usr/bin/env python3
"""Check that Tamarin code in \\begin{spthy}...\\end{spthy} blocks is verbatim.

  python3 -I tools/check_tex.py sections/*.tex

Each block is split at elision lines (a line that is only "...", "...," or similar);
every remaining chunk, with // comments and whitespace normalised, must occur in
tamarin/final/lightning.spthy or tamarin/final/lightning_aux.spthy.  Lemma, rule
and restriction names used in the block, and \\code{...} names that look like
lemma/rule names, must exist.
"""
import re
import sys

F = '/home/user/12345/tamarin/final/'
RAW = open(F + 'lightning.spthy').read() + '\n' + open(F + 'lightning_aux.spthy').read()


def norm(s):
    s = re.sub(r'//[^\n]*', '', s)
    return re.sub(r'\s+', ' ', s).strip()


SRC = norm(RAW)
NAMES = set(re.findall(r'\b(?:lemma|rule|restriction)\s+([A-Za-z0-9_]+)', RAW))
FACTS = set(re.findall(r'\b([A-Z][A-Za-z0-9_]*)\(', RAW)) | set(re.findall(r'!([A-Z][A-Za-z0-9_]*)\(', RAW))

bad = blocks = 0
for path in sys.argv[1:]:
    tex = open(path).read()
    for m in re.finditer(r'\\begin\{spthy\}(?:\[[^\]]*\])?\n(.*?)\\end\{spthy\}', tex, flags=re.S):
        blocks += 1
        line = tex[:m.start()].count('\n') + 1
        body = m.group(1)
        chunks = re.split(r'^\s*\.\.\.[\s,\]]*$', body, flags=re.M)
        for c in chunks:
            # also allow an inline "..." elision inside a line
            for piece in re.split(r'\.\.\.', c):
                p = norm(piece)
                if len(p) < 4:
                    continue
                if p not in SRC:
                    bad += 1
                    print(f'{path}:{line}: NOT VERBATIM: {p[:200]}')
        for n in re.findall(r'\b(?:lemma|rule|restriction)\s+([A-Za-z0-9_]+)', body):
            if n not in NAMES:
                bad += 1
                print(f'{path}:{line}: unknown name {n}')
    for n in re.findall(r'\\code\{([A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]*)\}', tex):
        if n not in NAMES and n not in FACTS and not n.startswith(('lightning', 'NO_', 'translation')):
            print(f'{path}: note: \\code{{{n}}} is not a lemma/rule/restriction/fact name in the model files')
print(f'checked {blocks} spthy blocks, {bad} problems')
sys.exit(1 if bad else 0)
