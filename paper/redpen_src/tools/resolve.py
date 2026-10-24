#!/usr/bin/env python3
"""Locate a phrase span on a PDF page.

  python3 -I resolve.py PDF PAGE "start phrase" ["end phrase"]

PAGE is 1-based.  Matching is on normalised words (NFKC, lower case, only
letters/digits kept, empty tokens dropped), in PyMuPDF word order, so a phrase
copied from `page.get_text()` output (pages/pageNN.txt) matches even across line
breaks.  Without an end phrase the span is the start phrase itself.
Prints the matched text, or ERROR (exit 1) if the span is missing or ambiguous.
"""
import re
import sys
import unicodedata

import pymupdf


def norm(w):
    w = unicodedata.normalize('NFKC', w).lower()
    return re.sub(r'[^0-9a-z]', '', w)


def tokens(text):
    return [t for t in (norm(w) for w in text.split()) if t]


def in_body(w):
    """Exclude the reviewers' margin comments (left x0 < 34, right x0 >= 572)."""
    return 34 <= w[0] < 572


def page_words(page):
    """[(norm_token, word_tuple)] with empty tokens dropped, margins excluded."""
    out = []
    for w in page.get_text('words', sort=False):
        if not in_body(w):
            continue
        for piece in w[4].split():
            t = norm(piece)
            if t:
                out.append((t, w))
    return out


def find_all(seq, pat):
    n = len(pat)
    return [i for i in range(len(seq) - n + 1) if seq[i:i + n] == pat]


def resolve(page, start, end=None):
    pw = page_words(page)
    toks = [t for t, _ in pw]
    s = tokens(start)
    if not s:
        raise ValueError('empty start phrase')
    starts = find_all(toks, s)
    if not starts:
        raise ValueError(f'start phrase not found: {start!r}')
    if len(starts) > 1:
        raise ValueError(f'start phrase ambiguous ({len(starts)} matches): {start!r}')
    i = starts[0]
    if end:
        e = tokens(end)
        ends = [j for j in find_all(toks, e) if j >= i]
        if not ends:
            raise ValueError(f'end phrase not found after start: {end!r}')
        j = ends[0] + len(e) - 1
    else:
        j = i + len(s) - 1
    # distinct word tuples, in order
    span, seen = [], set()
    for _, w in pw[i:j + 1]:
        if id(w) not in seen:
            seen.add(id(w))
            span.append(w)
    return span


def main():
    pdf, pno, start = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    end = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None
    doc = pymupdf.open(pdf)
    try:
        span = resolve(doc[pno - 1], start, end)
    except ValueError as e:
        print('ERROR:', e)
        sys.exit(1)
    print(f'OK ({len(span)} words): ' + ' '.join(w[4] for w in span))


if __name__ == '__main__':
    main()
