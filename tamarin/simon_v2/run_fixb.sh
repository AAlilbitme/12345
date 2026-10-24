#!/bin/sh
T=/tmp/claude-0/-home-user-12345/b86697a5-7cf6-54b8-baf7-e23643af4bfb/scratchpad/tam/tamarin-prover
cd "$(dirname "$0")"
LANG=C.UTF-8 timeout 5400 $T lightningfixb.spthy --prove +RTS -M6G -RTS > runfixb_noliveness.log 2>&1; echo "noliveness exit $?"
LANG=C.UTF-8 timeout 5400 $T lightningfixb.spthy -D=LIVENESS --prove +RTS -M6G -RTS > runfixb_liveness.log 2>&1; echo "liveness exit $?"
for f in runfixb_noliveness.log runfixb_liveness.log; do echo "== $f"; grep -cE "^  [A-Za-z_]+ \(.*verified" $f; grep -E "^  [A-Za-z_]+ \(" $f | grep -v verified; done
