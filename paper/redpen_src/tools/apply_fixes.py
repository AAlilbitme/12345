#!/usr/bin/env python3
"""Apply critic fixes to the markup files.

  python3 -I apply_fixes.py OUTDIR FINALDIR fixes1.json [fixes2.json ...]

Each fixes file: {fixes:[{section,kind,index,field,old,new,reason}], drop:[{section,kind,index,reason}]}.
A fix is applied only if `old` occurs exactly once in the field; otherwise it is reported and skipped.
Drops are applied last, per array, highest index first, so indices refer to the original files.
"""
import json
import os
import sys

KIND = {'note': 'notes', 'insert': 'inserts', 'strike': 'strikes'}


def main():
    src, dst, fixfiles = sys.argv[1], sys.argv[2], sys.argv[3:]
    os.makedirs(dst, exist_ok=True)
    marks = {s: json.load(open(f'{src}/{s}.json')) for s in 'ABCDEZ'}
    drops = set()
    ok = skipped = 0
    for ff in fixfiles:
        data = json.load(open(ff))
        for f in data.get('fixes', []):
            try:
                item = marks[f['section']][KIND[f['kind']]][f['index']]
                text = item[f['field']]
            except (KeyError, IndexError) as e:
                print(f'SKIP (bad ref {e}): {f["section"]} {f["kind"]}[{f["index"]}] {f["field"]}')
                skipped += 1
                continue
            n = text.count(f['old'])
            if n != 1:
                print(f'SKIP (old occurs {n}x): {f["section"]} {f["kind"]}[{f["index"]}]: {f["old"][:90]!r}')
                skipped += 1
                continue
            item[f['field']] = text.replace(f['old'], f['new'])
            ok += 1
        for d in data.get('drop', []):
            drops.add((d['section'], KIND[d['kind']], d['index']))
    for s, k, i in sorted(drops, key=lambda t: -t[2]):
        try:
            del marks[s][k][i]
            print(f'dropped {s} {k}[{i}]')
        except IndexError:
            print(f'SKIP drop {s} {k}[{i}]')
    for s, m in marks.items():
        json.dump(m, open(f'{dst}/{s}.json', 'w'), indent=1)
    print(f'applied {ok} fixes, skipped {skipped}, dropped {len(drops)}')


if __name__ == '__main__':
    main()
