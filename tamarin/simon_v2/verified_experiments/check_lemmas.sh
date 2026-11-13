#!/usr/bin/env bash
# add: compare the lemma list from list_lemmas.sh with the lemmas Tamarin itself
# add: loads (no proving, just loading), for one flag configuration.
# Usage: FLAG=LIVENESS check_lemmas.sh THEORY file1.spthy ...   (FLAG empty = no flags)
THEORY=$1; shift
TAMARIN=${TAMARIN:-tamarin-prover}
here=$(dirname "$0")
flags=""; [ -n "$FLAG" ] && flags="-D=$FLAG"
ours=$(FLAG=$FLAG "$here/list_lemmas.sh" "$@" | sort)
theirs=$(LANG=C.UTF-8 "$TAMARIN" "$THEORY" $flags --derivcheck-timeout=600 2>/dev/null \
         | sed -n '/^summary of summaries:/,$p' \
         | sed -nE 's/^  ([A-Za-z_0-9]+) \((all-traces|exists-trace)\):.*/\1/p' | sort)
if [ "$ours" = "$theirs" ]; then
  echo "config '${FLAG:-none}': $(echo "$ours" | wc -l) lemmas, list matches Tamarin"
else
  echo "config '${FLAG:-none}': MISMATCH (< list_lemmas.sh, > Tamarin)"
  diff <(echo "$ours") <(echo "$theirs")
  exit 1
fi
