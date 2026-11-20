#!/usr/bin/env python3
"""Lemma audit: for each proved lemma, how big is the proof and which rules does it touch?

  python3 -I analyze.py proofs.spthy [lightning.spthy]

A proof that has few steps and touches at most two protocol rules is flagged as a
"restriction restatement" candidate: it most likely follows from the restrictions
rather than from the protocol.  Mutation tests (removing a rule) confirm or refute this.
"""
import re
import sys

proofs = open(sys.argv[1]).read()
model = open(sys.argv[2] if len(sys.argv) > 2 else '/home/user/12345/tamarin/final/lightning.spthy').read()
RULES = set(re.findall(r'^rule\s+([A-Za-z0-9_]+)', model, flags=re.M))

rows = []
for m in re.finditer(r'^lemma\s+([A-Za-z0-9_]+)(.*?)(?=^lemma\s|^end\s*$|\Z)', proofs, flags=re.M | re.S):
    name, body = m.group(1), m.group(2)
    if 'qed' not in body and 'by contradiction' not in body:
        continue
    steps = len(re.findall(r'^\s*(?:solve|case|by|simplify|induction|next|qed)\b', body, flags=re.M))
    used = sorted({r for r in re.findall(r'case\s+([A-Za-z0-9_]+)', body) if r in RULES})
    rows.append((name, steps, used))

print(f'{"lemma":45s} {"steps":>5s} {"#rules":>6s}  verdict   rules touched')
for name, steps, used in sorted(rows, key=lambda r: (len(r[2]), r[1])):
    verdict = 'RESTATE?' if len(used) <= 2 and steps <= 30 else 'protocol'
    print(f'{name:45s} {steps:5d} {len(used):6d}  {verdict:8s}  {", ".join(used)}')
print(f'\n{len(rows)} proofs; {sum(1 for r in rows if len(r[2]) <= 2 and r[1] <= 30)} restatement candidates')
