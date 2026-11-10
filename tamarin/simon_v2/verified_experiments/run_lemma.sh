#!/usr/bin/env bash
# add: run ONE Tamarin lemma and classify the result, so that a timeout, a
# add: crash or a parse error is never mistaken for a proof.
#
# Usage: run_lemma.sh THEORY LEMMA [extra tamarin flags...]
# Environment: TAMARIN (default tamarin-prover), LIMIT seconds (default 1800),
#              MEM heap limit (default 8G), RESULTS file (default results.tsv),
#              EXPECT (default VERIFIED), RESUME=1 (skip results already recorded
#              for the same lemma, flags AND the same .spthy files)
#
# Prints one line:   RESULT  LEMMA  steps  seconds  peak-memory
# RESULT (exit code first, then Tamarin's own summary line):
#   TIMEOUT             exit 124 (time limit reached)
#   OUT_OF_MEMORY       Tamarin reported "Heap exhausted" (GHC heap limit MEM)
#   KILLED_OOM_SUSPECT  killed by a signal (exit > 128, e.g. 137); memory not confirmed
#   ERROR               any other non-zero exit, or no summary line for the lemma
#   VERIFIED / FALSIFIED / INCOMPLETE   exit 0 and Tamarin's summary line says so
#   WELLFORMEDNESS_WARNING  Tamarin printed a wellformedness warning (its result may be wrong)
# The exit status is 0 only if the result equals EXPECT (default VERIFIED; use
# EXPECT=FALSIFIED for a witness that is meant not to exist). Missing output
# never counts, even with exit 0.
# Full output goes to logs/; one metadata row per run is appended to $RESULTS.

THEORY=$1; LEMMA=$2; shift 2
TAMARIN=${TAMARIN:-tamarin-prover}
LIMIT=${LIMIT:-1800}
MEM=${MEM:-8G}
RESULTS=${RESULTS:-results.tsv}
EXPECT=${EXPECT:-VERIFIED}
# add: checksum of all theory files in this folder, so a recorded result is
# add: only reused (RESUME=1) for exactly the same model.
sha=$(cat ./*.spthy | { sha256sum 2>/dev/null || shasum -a 256; } | cut -c1-12)
mkdir -p logs
LOG="logs/${LEMMA}$(echo "$*" | tr -c 'A-Za-z0-9=' '_' | sed 's/^_*//; s/^\(.\)/_\1/').log"

# add: macOS has no `timeout`; use GNU coreutils' gtimeout there (brew install coreutils)
TIMEOUT=timeout; command -v timeout >/dev/null 2>&1 || TIMEOUT=gtimeout
command -v "$TIMEOUT" >/dev/null 2>&1 || { echo "need timeout (Linux) or gtimeout (macOS: brew install coreutils)"; exit 2; }

# add: RESUME=1 skips a lemma whose expected result is already recorded for the
# add: same flags and the same theory files (to spread a long run over sessions).
if [ "${RESUME:-0}" = 1 ] && [ -f "$RESULTS" ] && awk -F'\t' -v l="$LEMMA" -v f="$*${TAG:+ $TAG}" -v h="$sha" -v e="$EXPECT" \
     '$6==l && $7==f && $16==h && $10==e {ok=1} END {exit !ok}' "$RESULTS"; then
  printf "%-18s %-45s (%s already in %s)\n" SKIPPED "$LEMMA" "$EXPECT" "$RESULTS"; exit 0
fi

start=$(date +%s)
# +RTS -s: GHC prints its memory statistics (incl. peak) at exit.
LANG=C.UTF-8 "$TIMEOUT" "$LIMIT" "$TAMARIN" "$THEORY" --prove="$LEMMA" "$@" \
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
# add: Tamarin still proves lemmas when the theory is not wellformed; such a
# add: result is not trustworthy.
case $res in VERIFIED|FALSIFIED)
  grep -qiE "wellformedness checks? failed" "$LOG" && res=WELLFORMEDNESS_WARNING;;
esac

[ -f "$RESULTS" ] || printf "date\tgit\ttamarin\tmaude\ttheory\tlemma\tflags\tlimit_s\tmem\tresult\tsteps\tseconds\texit\tpeak\tloaded\ttheory_sha\texpected\n" > "$RESULTS"
gitrev=$(git rev-parse --short HEAD 2>/dev/null || echo none)
[ "$gitrev" = none ] || git diff --quiet -- . 2>/dev/null || gitrev="$gitrev+dirty"
tver=$("$TAMARIN" --version 2>/dev/null | head -1 | sed -E 's/.*tamarin-prover ([^ ,]+).*/\1/')
mver=$(maude --version 2>/dev/null | head -1)
printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$(date +%Y-%m-%dT%H:%M:%S%z)" "$gitrev" "$tver" "$mver" "$THEORY" "$LEMMA" "$*${TAG:+ $TAG}" \
    "$LIMIT" "$MEM" "$res" "${steps:--}" "$secs" "$code" "${peak:--}" "$loaded" "$sha" "$EXPECT" >> "$RESULTS"
note=""; [ "$res" = "$EXPECT" ] || note="  <-- expected $EXPECT"
[ "$res" = "$EXPECT" ] && [ "$EXPECT" != VERIFIED ] && note="  (as expected)"
printf "%-18s %-45s %6s steps %6ss %9s%s\n" "$res" "$LEMMA" "${steps:--}" "$secs" "${peak:--}" "$note"
[ "$res" = "$EXPECT" ]
