#!/usr/bin/env python3
"""Build the full paper in a temp dir and report how long each top-level section is.

  python3 -I tools/measure.py            # table of sections with length in columns/pages
Main body = from the title to the start of the References.  Target: <= 12.0 pages.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pymupdf

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP, BOT = 54.0, 738.0          # usable text area of an IEEEtran page (pt)
MID = 306.0


def colpos(page, x, y):
    """Position in columns from the start of the document (0 = top of page 1, left col)."""
    return page * 2 + (1 if x > MID else 0) + min(max((y - TOP) / (BOT - TOP), 0), 1)


def main():
    tmp = tempfile.mkdtemp()
    for f in ('preamble.tex', 'refs.tex', 'main.tex'):
        shutil.copy(os.path.join(HERE, f), tmp)
    for d in ('figs', 'sections'):
        shutil.copytree(os.path.join(HERE, d), os.path.join(tmp, d))
    for _ in range(2):
        r = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'main.tex'], cwd=tmp,
                           capture_output=True, text=True, errors='replace')
    pdf = os.path.join(tmp, 'main.pdf')
    if not os.path.exists(pdf):
        print('BUILD FAILED'); print(r.stdout[-3000:]); sys.exit(1)
    aux = open(os.path.join(tmp, 'main.aux')).read()
    titles = {}
    for m in re.finditer(r'\\newlabel\{(sec:[a-z-]+)\}\{\{([^}]*)\}\{(\d+)\}\{([^}]*)\}\{(section\.\d+)\}', aux):
        titles[m.group(5)] = (m.group(2), m.group(4), m.group(1))
    doc = pymupdf.open(pdf)
    names = doc.resolve_names()
    marks = []
    for dest, (num, title, label) in titles.items():
        if dest in names:
            n = names[dest]
            x, y = n.get('to', (72, 0))
            # PDF destination y is measured from the bottom of the page
            y = doc[n['page']].rect.height - y
            marks.append((colpos(n['page'], x, y), f'{num}. {title}', label))
    # references and appendix start: find the text
    for i, p in enumerate(doc):
        for b in p.get_text('blocks'):
            t = b[4].strip()
            if t in ('References', 'REFERENCES'):
                marks.append((colpos(i, b[0], b[1]), 'References', ''))
            if t.startswith('Appendix') or t.startswith('APPENDIX'):
                marks.append((colpos(i, b[0], b[1]), 'Appendix', ''))
    marks.sort()
    print(f'{"section":45s} {"start":>7s} {"columns":>8s} {"pages":>6s}')
    for (a, name, _), nxt in zip(marks, marks[1:] + [(doc.page_count * 2, 'END', '')]):
        print(f'{name[:45]:45s} {a/2+1:7.2f} {nxt[0]-a:8.2f} {(nxt[0]-a)/2:6.2f}')
    ref = next((a for a, n, _ in marks if n == 'References'), None)
    print(f'\nMAIN BODY (title to References): {ref/2:.2f} pages (target <= 12.00); total {doc.page_count} pages')
    over = [l for l in r.stdout.splitlines() if re.search(r'Overfull \\hbox \((\d+)', l) and float(re.search(r'\(([\d.]+)pt', l).group(1)) > 5]
    undef = sorted(set(re.findall(r"LaTeX Warning: (?:Reference|Citation) `([^']+)' .*undefined", open(os.path.join(tmp, 'main.log'), errors='ignore').read())))
    print(f'overfull > 5pt: {len(over)}; undefined refs/cites: {undef or "none"}')
    shutil.rmtree(tmp)


if __name__ == '__main__':
    main()
