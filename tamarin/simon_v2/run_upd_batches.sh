#!/bin/bash
# Prove lemmas of lightningupd.spthy in batches of 8 (one Tamarin call each, 20 min).
# Usage: run_upd_batches.sh <worker 0|1> [extra flag]
T=/tmp/claude-0/-home-user-12345/b86697a5-7cf6-54b8-baf7-e23643af4bfb/scratchpad/tam/tamarin-prover
cd "$(dirname "$0")"
mapfile -t L < <(grep -h "^lemma" lemmasupd.spthy lightningupd.spthy | sed -E 's/^lemma ([A-Za-z_0-9]+).*/\1/')
OUT=runupd_batch_w$1${2:+_liveness}.txt; : > $OUT
b=0
for ((i=0; i<${#L[@]}; i+=8)); do
  if (( b % 2 == $1 )); then
    batch=("${L[@]:i:8}"); args=(); for x in "${batch[@]}"; do args+=(--prove=$x); done
    res=$(LANG=C.UTF-8 timeout 1200 $T lightningupd.spthy $2 "${args[@]}" --derivcheck-timeout=600 +RTS -M6G -RTS 2>&1 | grep -E "^  [A-Za-z_0-9]+ \((all-traces|exists-trace)\)")
    for x in "${batch[@]}"; do
      line=$(grep -E "^  $x \(" <<<"$res"); echo "${line:-  $x: NO RESULT (batch timed out)}" >> $OUT
    done
  fi
  b=$((b+1))
done
echo done >> $OUT
