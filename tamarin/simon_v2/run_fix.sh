cd /home/user/12345/tamarin/simon_v2
T=/tmp/claude-0/-home-user-12345/b86697a5-7cf6-54b8-baf7-e23643af4bfb/scratchpad/tam/tamarin-prover
echo "== double publish / sanity"
LANG=C.UTF-8 timeout 1800 $T checkfix.spthy --prove +RTS -M6G -RTS 2>&1 | grep -E "^  [A-Za-z_]+ \(|unexpected"
echo "== all lemmas without -D=LIVENESS"
LANG=C.UTF-8 timeout 5400 $T lightningfix.spthy --prove +RTS -M8G -RTS > runfix_noliveness.log 2>&1; echo "exit $?"
grep -E "^  [A-Za-z_]+ \((all|exists)" runfix_noliveness.log
echo "== all lemmas with -D=LIVENESS"
LANG=C.UTF-8 timeout 5400 $T lightningfix.spthy -D=LIVENESS --prove +RTS -M8G -RTS > runfix_liveness.log 2>&1; echo "exit $?"
grep -E "^  [A-Za-z_]+ \((all|exists)" runfix_liveness.log
