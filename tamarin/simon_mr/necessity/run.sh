#!/bin/bash
# For each variant (one liveness restriction removed), try the liveness-dependent lemmas.
# Expected: the lemma tied to the removed restriction is falsified (counterexample).
T=${TAMARIN:-tamarin-prover}
LEMMAS="ForwardTimeGap Timeout_Race_Blocked Intermediary_Never_Loses_Under_Liveness Intermediary_Never_Loses_Strong Payment_Atomicity_Under_Liveness"
for f in no_*.spthy; do for L in $LEMMAS; do
  st=$(date +%s)
  r=$(LANG=C.UTF-8 timeout ${TO:-900} $T $f --prove=$L --quiet +RTS -M${MEM:-6G} -RTS 2>&1 | grep -E "^  $L ")
  echo "$f | $L | ${r:-no result} | $(( $(date +%s)-st ))s"
done; done
