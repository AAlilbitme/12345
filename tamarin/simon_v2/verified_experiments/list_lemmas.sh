#!/usr/bin/env bash
# add: list the lemma names Tamarin loads from the given files, for one flag
# add: configuration: FLAG=LIVENESS (with -D=LIVENESS) or empty (no flags).
# add: Handles flat "#ifdef X / #else / #endif" blocks (no nesting).
# Usage: FLAG=LIVENESS list_lemmas.sh file1.spthy file2.spthy ...
awk -v flag="$FLAG" '
  /^#ifdef/ { inblk=1; on=($2==flag); next }
  /^#else/  { on=!on; next }
  /^#endif/ { inblk=0; next }
  /^lemma / { if (!inblk || on) { n=$2; sub(/[:\[].*/, "", n); print n } }
' "$@"
