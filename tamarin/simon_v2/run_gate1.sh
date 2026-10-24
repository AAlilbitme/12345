#!/bin/bash
# Gate 1: each lemma separately; log command, memory limit, elapsed time, phase.
T=/tmp/claude-0/-home-user-12345/b86697a5-7cf6-54b8-baf7-e23643af4bfb/scratchpad/tam/tamarin-prover
cd "$(dirname "$0")"; OUT=out_g1.txt; : > $OUT
for L in Settle_Commit_Correspondence Ticks_Consecutive Commit_Stamp_Is_Current Request_Stamp_Is_Current Receipt_Stamp_Is_Current Commit_Without_Receipt Request_Without_Commit; do
  CMD="tamarin-prover deadline.spthy --prove=$L --derivcheck-timeout=600 +RTS -M12G -RTS (timeout 900s)"
  s=$(date +%s)
  LANG=C.UTF-8 timeout 900 $T deadline.spthy --prove=$L --derivcheck-timeout=600 +RTS -M12G -RTS > g1_$L.log 2>&1; ec=$?
  e=$(( $(date +%s) - s ))
  res=$(grep -E "^  $L \(" g1_$L.log | head -1)
  if grep -q "Saturating Sources\] Done" g1_$L.log; then phase="proof search"; else phase="setup"; fi
  if [ -n "$res" ]; then status="$res"
  elif grep -q "Heap exhausted" g1_$L.log; then status="OUT OF MEMORY during $phase"
  elif [ $ec -eq 124 ]; then status="TIMEOUT during $phase"
  else status="ERROR exit $ec during $phase"; fi
  printf '%s\n    cmd: %s\n    elapsed: %ss\n' "$L: $status" "$CMD" "$e" >> $OUT
done
echo done >> $OUT
