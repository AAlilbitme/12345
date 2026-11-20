#!/usr/bin/env bash
# add: summarize results.tsv: the latest run of each theory/lemma/flags, counts
# add: per result, and every lemma whose result is not the expected one.
# Exit status 1 if any result is not as expected.
f=${1:-results.tsv}
[ -f "$f" ] || { echo "no $f yet"; exit 1; }
tail -n +2 "$f" | awk -F'\t' '
  { k=$5" "$6" "$7; r[k]=$10; e[k]=($17==""?"VERIFIED":$17) }
  END {
    for (k in r) { c[r[k]]++; if (r[k]!=e[k]) { bad++; b=b "\n    " k ": " r[k] " (expected " e[k] ")" } }
    for (x in c) printf "  %-22s %d\n", x, c[x]
    if (bad) { printf "  NOT AS EXPECTED: %d%s\n", bad, b; exit 1 }
    print "  all results as expected"
  }'
