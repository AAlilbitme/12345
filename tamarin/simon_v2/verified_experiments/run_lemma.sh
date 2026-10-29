#!/usr/bin/env bash
# add: run ONE Tamarin lemma and classify the result, so that a timeout, a
# add: crash or a parse error is never mistaken for a proof.
#
# Usage: run_lemma.sh THEORY LEMMA [extra tamarin flags...]
# Environment: TAMARIN (default tamarin-prover), LIMIT seconds (default 1800),
#              MEM heap limit (default 8G), RESULTS file (default results.tsv)
#
# Prints one line:   RESULT  LEMMA  steps  seconds  peak-memory
# RESULT (exit code first, then Tamarin's own summary line):
#   TIMEOUT             exit 124 (time limit reached)
#   OUT_OF_MEMORY       Tamarin reported "Heap exhausted" (GHC heap limit MEM)
#   KILLED_OOM_SUSPECT  killed by a signal (exit > 128, e.g. 137); memory not confirmed
#   ERROR               any other non-zero exit, or no summary line for the lemma
#   VERIFIED / FALSIFIED / INCOMPLETE   exit 0 and Tamarin's summary line says so
# Only VERIFIED counts as a proof. Missing output never counts, even with exit 0.
# Full output goes to logs/; one metadata row per run is appended to $RESULTS.

THEORY=$1; LEMMA=$2; shift 2
TAMARIN=${TAMARIN:-tamarin-prover}
LIMIT=${LIMIT:-1800}
MEM=${MEM:-8G}
RESULTS=${RESULTS:-results.tsv}
mkdir -p logs
LOG="logs/${LEMMA}$(echo "$*" | tr -c 'A-Za-z0-9=' '_' | sed 's/^_*//; s/^\(.\)/_\1/').log"

start=$(date +%s)
# +RTS -s: GHC prints its memory statistics (incl. peak) at exit.
LANG=C.UTF-8 timeout "$LIMIT" "$TAMARIN" "$THEORY" --prove="$LEMMA" "$@" \
    --derivcheck-timeout=600 +RTS -M"$MEM" -s -RTS > "$LOG" 2>&1
code=$?
secs=$(( $(date +%s) - start ))

# the result line is only taken from Tamarin's final summary section
line=$(sed -n '/^summary of summaries:/,$p' "$LOG" | grep -E "^  $LEMMA \((all-traces|exists-trace)\):" | tail -1)
steps=$(echo "$line" | sed -nE 's/.*\(([0-9]+) steps\).*/\1/p')
peak=$(sed -nE 's/^ *([0-9]+) MiB total memory in use.*/\1MiB/p' "$LOG" | tail -1)
# number of lemmas Tamarin itself loaded (its summary lists every lemma)
loaded=$(sed -n '/^summary of summaries:/,$p' "$LOG" | grep -cE "^  [A-Za-z_0-9]+ \((all-traces|exists-trace)\):")

if   [ "$code" -eq 124 ];                     then res=TIMEOUT
elif grep -q "Heap exhausted" "$LOG";         then res=OUT_OF_MEMORY
elif [ "$code" -gt 128 ];                     then res=KILLED_OOM_SUSPECT
elif [ "$code" -ne 0 ];                       then res=ERROR
elif [ -z "$line" ];                          then res=ERROR
elif echo "$line" | grep -q ": verified";     then res=VERIFIED
elif echo "$line" | grep -q ": falsified";    then res=FALSIFIED
else                                               res=INCOMPLETE
fi

[ -f "$RESULTS" ] || printf "date\tgit\ttamarin\tmaude\ttheory\tlemma\tflags\tlimit_s\tmem\tresult\tsteps\tseconds\texit\tpeak\tloaded\n" > "$RESULTS"
gitrev=${GITREV:-$(git rev-parse --short HEAD 2>/dev/null || echo none)}   # GITREV: set by compare_tactics.sh
[ -n "$GITREV" ] || git diff --quiet -- . 2>/dev/null || gitrev="$gitrev+dirty"
tver=$("$TAMARIN" --version 2>/dev/null | head -1 | sed -E 's/.*tamarin-prover ([^ ,]+).*/\1/')
mver=$(maude --version 2>/dev/null | head -1)
printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$(date -Iseconds)" "$gitrev" "$tver" "$mver" "$THEORY" "$LEMMA" "$*" \
    "$LIMIT" "$MEM" "$res" "${steps:--}" "$secs" "$code" "${peak:--}" "$loaded" >> "$RESULTS"
printf "%-18s %-45s %6s steps %6ss %9s\n" "$res" "$LEMMA" "${steps:--}" "$secs" "${peak:--}"
[ "$res" = VERIFIED ]
