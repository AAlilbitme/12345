#!/usr/bin/env python3
"""Build the red-pen version of the paper.

  python3 -I build_redpen.py IN.pdf OUT.pdf markup1.json [markup2.json ...]

Each markup JSON: {section, strikes:[{page,start,end,why}], notes:[{page,anchor,html}],
inserts:[{after_page,title,html}], open_questions:[...]}.

On the original pages: struck spans get a red line through every line of text and
a red [Sn] tag; each note anchor gets a red [Rn] tag.  After every page that has
markup, red "updates" pages carry the note texts, the strike reasons and the
inserted material.  A red cover page (legend + open questions) goes first.
"""
import html as htmlmod
import io
import json
import os
import re
import sys

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resolve import resolve  # noqa: E402

RED = (0.78, 0, 0)
CSS = """
* { color: #c00000; font-family: sans-serif; }
body { font-size: 9pt; line-height: 1.25; }
h2 { font-size: 13pt; margin: 0 0 6pt 0; }
h3 { font-size: 11pt; margin: 8pt 0 4pt 0; }
h4 { font-size: 10pt; margin: 8pt 0 3pt 0; }
p { margin: 0 0 4pt 0; }
pre, code { font-family: monospace; }
pre { font-size: 7pt; margin: 2pt 0 5pt 8pt; }
table { border-collapse: collapse; margin: 3pt 0 6pt 0; }
td, th { border: 0.5pt solid #c00000; padding: 1.5pt 3pt; font-size: 8pt; vertical-align: top; }
.tag { font-weight: bold; }
.where { font-style: italic; font-size: 8pt; }
.box { margin: 0 0 7pt 0; }
"""


def lines_of(span):
    """Group word tuples by (block, line) -> list of rects."""
    groups = {}
    for w in span:
        key = (w[5], w[6])
        r = pymupdf.Rect(w[:4])
        groups[key] = groups[key] | r if key in groups else r
    return list(groups.values())


def tag(page, word, text):
    x, y = word[2] + 0.6, word[1] + 4.2
    page.insert_text((x, y), text, fontsize=6.2, fontname='hebo', color=RED)


def story_pages(body_html, rect):
    """Render HTML with a Story; return a PDF document (bytes-backed)."""
    buf = io.BytesIO()
    writer = pymupdf.DocumentWriter(buf)
    story = pymupdf.Story(html=body_html, user_css=CSS)
    where = rect + (48, 46, -48, -46)
    more = True
    while more:
        dev = writer.begin_page(rect)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()
    return pymupdf.open('pdf', buf.getvalue())


def esc(s):
    return htmlmod.escape(s, quote=False)


ALLOWED = r'(?:p|b|i|code|pre|ul|li|table|tr|th|td|br|h3|h4|div|span)'


def clean(h):
    """Accept agent HTML: undo whole-fragment escaping, escape stray '<' (e.g. h(<s,t>))."""
    if h.lstrip().startswith('&lt;') and '<' not in h:
        h = htmlmod.unescape(h)
    return re.sub(r'<(?!/?' + ALLOWED + r'\b)', '&lt;', h)


def main():
    src, dst, markups = sys.argv[1], sys.argv[2], sys.argv[3:]
    doc = pymupdf.open(src)
    rect = doc[0].rect
    strikes, notes, inserts, questions = [], [], [], []
    for path in markups:
        m = json.load(open(path))
        sec = m.get('section', os.path.basename(path))
        strikes += [dict(s, sec=sec) for s in m.get('strikes', [])]
        notes += [dict(n, sec=sec) for n in m.get('notes', [])]
        inserts += [dict(i, sec=sec) for i in m.get('inserts', [])]
        questions += [(sec, q) for q in m.get('open_questions', [])]

    # resolve everything first, numbering in page / reading order
    problems = []
    per_page = {p: {'strikes': [], 'notes': [], 'inserts': []} for p in range(1, doc.page_count + 1)}
    for s in strikes:
        try:
            span = resolve(doc[s['page'] - 1], s['start'], s.get('end') or None)
            per_page[s['page']]['strikes'].append((span[0][5], span[0][6], span[0][7], s, span))
        except Exception as e:  # noqa: BLE001
            problems.append(f"strike p{s['page']} [{s['sec']}] {s['start']!r}: {e}")
    for n in notes:
        try:
            span = resolve(doc[n['page'] - 1], n['anchor'])
            per_page[n['page']]['notes'].append((span[-1][5], span[-1][6], span[-1][7], n, span))
        except Exception as e:  # noqa: BLE001
            problems.append(f"note p{n['page']} [{n['sec']}] {n['anchor']!r}: {e}")
    for i in inserts:
        per_page[min(max(int(i['after_page']), 1), doc.page_count)]['inserts'].append(i)
    if problems:
        print('UNRESOLVED (skipped):\n  ' + '\n  '.join(problems))

    sn = rn = 0
    update_docs = {}
    for p in range(1, doc.page_count + 1):
        page = doc[p - 1]
        d = per_page[p]
        d['strikes'].sort(key=lambda t: t[:3])
        d['notes'].sort(key=lambda t: t[:3])
        parts = []
        for *_, s, span in d['strikes']:
            sn += 1
            for r in lines_of(span):
                y = (r.y0 + r.y1) / 2
                page.draw_line((r.x0, y), (r.x1, y), color=RED, width=0.9)
            tag(page, span[-1], f'[S{sn}]')
            frm = ' '.join(w[4] for w in span[:6]) + (' ... ' + ' '.join(w[4] for w in span[-5:]) if len(span) > 11 else ' '.join(w[4] for w in span[6:]))
            parts.append(f'<div class="box"><p><span class="tag">[S{sn}] struck</span> '
                         f'<span class="where">"{esc(frm)}"</span></p><p>{esc(s["why"])}</p></div>')
        for *_, n, span in d['notes']:
            rn += 1
            tag(page, span[-1], f'[R{rn}]')
            parts.append(f'<div class="box"><p><span class="tag">[R{rn}]</span> '
                         f'<span class="where">at "{esc(n["anchor"])}"</span></p>{clean(n["html"])}</div>')
        for i in d['inserts']:
            parts.append(f'<h3>{esc(i["title"])}</h3>{clean(i["html"])}')
        if parts:
            body = f'<h2>Red updates for page {p}</h2>' + ''.join(parts)
            update_docs[p] = story_pages(body, rect)

    # cover page
    q = ''.join(f'<li>[{esc(s)}] {esc(t)}</li>' for s, t in questions) or '<li>none</li>'
    cover = story_pages(
        '<h2>Red-pen update of Tarmin_LN_7 against csf_final</h2>'
        '<p><b>Red text</b> = our corrections and additions, collected on the red pages after each page '
        '(tags <b>[Rn]</b> on the original page show where each one goes).</p>'
        '<p><b>Red line through text</b> = proposed deletion; tag <b>[Sn]</b> gives the reason on the red page after it.</p>'
        '<p>Basis: the csf_final artefact (lightning.spthy, lightning_aux.spthy, Makefile), all results reproduced on '
        "Sana's laptop with Tamarin 1.10: make verify 55/55, make general 24/24, make aux 21/21, make necessity "
        '(T3 counterexample verified, 28 steps). Co-authors\' margin comments are left untouched.</p>'
        f'<h3>Open questions for Sana and Simon</h3><ul>{q}</ul>', rect)

    out = pymupdf.open()
    out.insert_pdf(cover)
    for p in range(1, doc.page_count + 1):
        out.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
        if p in update_docs:
            out.insert_pdf(update_docs[p])
    out.save(dst, garbage=3, deflate=True)
    print(f'{dst}: {out.page_count} pages, {sn} strikes, {rn} notes, '
          f'{sum(len(v["inserts"]) for v in per_page.values())} inserts, {len(problems)} unresolved')


if __name__ == '__main__':
    main()
