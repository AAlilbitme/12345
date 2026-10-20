cd /home/user/12345/tamarin/simon_v2
T=/tmp/claude-0/-home-user-12345/b86697a5-7cf6-54b8-baf7-e23643af4bfb/scratchpad/tam/tamarin-prover
echo "== without -D=LIVENESS"
LANG=C.UTF-8 timeout 5400 $T lightningtagged.spthy --prove +RTS -M8G -RTS > run_noliveness.log 2>&1; echo "exit $?"
grep -E "^  [A-Za-z_]+ \((all|exists)" run_noliveness.log
echo "== with -D=LIVENESS"
LANG=C.UTF-8 timeout 5400 $T lightningtagged.spthy -D=LIVENESS --prove +RTS -M8G -RTS > run_liveness.log 2>&1; echo "exit $?"
grep -E "^  [A-Za-z_]+ \((all|exists)" run_liveness.log
