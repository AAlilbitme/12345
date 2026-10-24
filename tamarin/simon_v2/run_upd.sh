#!/bin/bash
# Prove every lemma of lightningupd.spthy separately (10 min each); $1 = extra flag.
T=/tmp/claude-0/-home-user-12345/b86697a5-7cf6-54b8-baf7-e23643af4bfb/scratchpad/tam/tamarin-prover
cd "$(dirname "$0")"
OUT=runupd${1:+_liveness}.txt; : > $OUT
for L in $(grep -h "^lemma" lemmasupd.spthy lightningupd.spthy | sed -E 's/^lemma ([A-Za-z_0-9]+).*/\1/'); do
  r=$(LANG=C.UTF-8 timeout 600 $T lightningupd.spthy $1 --prove=$L --derivcheck-timeout=600 +RTS -M3G -RTS 2>&1 | grep -E "^  $L \(")
  echo "${r:-  $L: timeout/not in config}" >> $OUT
done
echo done >> $OUT
