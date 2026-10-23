#!/bin/bash
T=/tmp/claude-0/-home-user-12345/b86697a5-7cf6-54b8-baf7-e23643af4bfb/scratchpad/tam/tamarin-prover
cd "$(dirname "$0")"; OUT=out_dl3.txt
run(){ L=$1; shift; s=$(date +%s); LANG=C.UTF-8 timeout 1800 $T deadline3.spthy "$@" --prove=$L --derivcheck-timeout=600 +RTS -M13G -RTS > dl3_$L${1:+_flags}.log 2>&1; ec=$?; e=$(( $(date +%s)-s ))
  r=$(grep -E "^  $L \(" dl3_$L${1:+_flags}.log); if grep -q "Saturating Sources\] Done" dl3_$L${1:+_flags}.log; then ph="proof search"; else ph="setup"; fi
  grep -q "Heap exhausted" dl3_$L${1:+_flags}.log && r="OUT OF MEMORY during $ph"; [ -z "$r" ] && r="TIMEOUT/exit $ec during $ph"
  echo "$L [flags: ${*:-none}]: $r | -M13G, 1800s | elapsed ${e}s" >> $OUT; }
run Commit_Without_Receipt_Pinned
run Request_Without_Commit_Pinned
run Settle_Commit_Correspondence
run Deadline_Witness -D=LIVENESS -D=BOUND -D=GAP2
run Deadline_Per_Hop -D=LIVENESS -D=BOUND -D=GAP2
echo done >> $OUT
