#!/usr/bin/env bash
# add: controlled tactic comparison for the goal-2 model. For each lemma it runs
# add: (1) the committed theory and (2) the same theory with only that lemma's
# add: heuristic switched to the reviewer-proposed tactic "upd_events", one
# add: after the other, at the same git revision, time limit, memory limit and
# add: tool versions. Rows go to compare.tsv (same columns as results.tsv;
# add: column "flags" is "tactic=current" or "tactic=upd_events").
#
# Usage (from 2_htlcs_through_channel_updates/):
#   TAMARIN=... LIMIT=1800 MEM=8G ../compare_tactics.sh Lemma1 Lemma2 ...

set -e
here=$(cd "$(dirname "$0")" && pwd)
folder=$(pwd)
rev=$(git rev-parse --short HEAD)
git diff --quiet -- . || { echo "commit your changes first (comparison must be at one revision)"; exit 1; }
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/current" "$work/variant"
git archive HEAD . | tar -x -C "$work/current"
git archive HEAD . | tar -x -C "$work/variant"

# The proposed tactic: update events first, channel history and KU last.
cat >> "$work/variant/tactics.spthy" <<'EOF'

tactic: upd_events
presort: s
prio:
    regex "ChannelUpdateFor[(]"
prio:
    regex "StateUpdate[(]"
prio:
    regex "HTLCCommitted[(]"
prio:
    regex "^\s*Committed[(]"
prio:
    regex "^\s*InFlight[(]"
prio:
    regex "!UpdateDone[(]"
deprio:
    regex "KU[(]" | regex "Pending[AB][(]" | regex "State[AB][(]" | regex "ChannelConnect" | regex "Wallet" | regex "Mutex"
EOF

export RESULTS="$folder/compare.tsv" GITREV="$rev"
set +e
for L in "$@"; do
  for f in "$work/variant/lightningupd.spthy" "$work/variant/lemmasupd.spthy"; do
    # switch only this lemma's heuristic (replace it, or add one)
    sed -i -E "/^lemma $L( |\[|:)/{ s/heuristic=(\{[^}]*\}|[A-Za-z]+)/heuristic={upd_events}/; t; s/^lemma $L \[/lemma $L [heuristic={upd_events}, /; t; s/^lemma $L:/lemma $L [heuristic={upd_events}]:/ }" "$f"
  done
  for v in current variant; do
    t=$([ $v = current ] && echo current || echo upd_events)
    (cd "$work/$v" && TAG="tactic=$t" "$here/run_lemma.sh" lightningupd.spthy "$L" | sed "s/^/$t: /")
  done
done
