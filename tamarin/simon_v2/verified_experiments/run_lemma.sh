#!/usr/bin/env bash
# add: run ONE Tamarin lemma and classify the result, so that a timeout, an
# add: out-of-memory crash or a parse error is never mistaken for a proof.
#
# Usage: run_lemma.sh THEORY LEMMA [extra tamarin flags...]
# Environment: TAMARIN (default tamarin-prover), LIMIT seconds (default 1800),
#              MEM heap limit (default 8G), RESULTS file (default results.tsv)
#
# Prints one line:   RESULT  LEMMA  steps  seconds
# RESULT is one of:  VERIFIED FALSIFIED INCOMPLETE TIMEOUT OUT_OF_MEMORY ERROR
# Full Tamarin output goes to logs/LEMMA.log; one metadata row per run is
# appended to $RESULTS (tab separated).

THEORY=$1; LEMMA=$2; shift 2
TAMARIN=${TAMARIN:-tamarin-prover}
LIMIT=${LIMIT:-1800}
MEM=${MEM:-8G}
RESULTS=${RESULTS:-results.tsv}
mkdir -p logs
LOG="logs/${LEMMA}$(echo "$*" | tr -c 'A-Za-z0-9=' '_' | sed 's/^_*//; s/^\(.\)/_\1/').log"

start=$(date +%s)
LANG=C.UTF-8 timeout "$LIMIT" "$TAMARIN" "$THEORY" --prove="$LEMMA" "$@" \
    --derivcheck-timeout=600 +RTS -M"$MEM" -RTS > "$LOG" 2>&1
code=$?
secs=$(( $(date +%s) - start ))

line=$(grep -E "^  $LEMMA \(" "$LOG" | tail -1)
steps=$(echo "$line" | sed -nE 's/.*\(([0-9]+) steps\).*/\1/p')
if   [ "$code" -eq 124 ];                          then res=TIMEOUT
elif grep -q "Heap exhausted" "$LOG";              then res=OUT_OF_MEMORY
elif [ "$code" -eq 137 ];                          then res=OUT_OF_MEMORY   # killed by the system
elif [ -z "$line" ];                               then res=ERROR
elif echo "$line" | grep -q "verified";            then res=VERIFIED
elif echo "$line" | grep -q "falsified";           then res=FALSIFIED
else                                                    res=INCOMPLETE
fi

[ -f "$RESULTS" ] || printf "date\tgit\ttamarin\tmaude\ttheory\tlemma\tflags\tlimit_s\tmem\tresult\tsteps\tseconds\texit\n" > "$RESULTS"
gitrev=$(git rev-parse --short HEAD 2>/dev/null || echo none)
tver=$("$TAMARIN" --version 2>/dev/null | head -1 | sed -E 's/.*tamarin-prover ([^ ,]+).*/\1/')
mver=$(maude --version 2>/dev/null | head -1)
printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$(date -Iseconds)" "$gitrev" "$tver" "$mver" "$THEORY" "$LEMMA" "$*" \
    "$LIMIT" "$MEM" "$res" "${steps:--}" "$secs" "$code" >> "$RESULTS"
printf "%-14s %-45s %6s steps %6ss\n" "$res" "$LEMMA" "${steps:--}" "$secs"
[ "$res" = VERIFIED ]
