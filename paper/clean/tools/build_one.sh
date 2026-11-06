#!/usr/bin/env bash
# Compile one section file on its own (in a private temp dir) and report problems.
#   tools/build_one.sh sections/05a_model.tex        -> prints errors, overfull boxes, page count
#   tools/build_one.sh main                          -> full paper build into main.pdf
set -u
HERE=$(cd "$(dirname "$0")/.." && pwd)
TARGET=${1:?usage: build_one.sh sections/XX.tex | main}
TMP=$(mktemp -d)
cp -r "$HERE"/preamble.tex "$HERE"/refs.tex "$HERE"/figs "$HERE"/sections "$TMP"/
if [ "$TARGET" = main ]; then
  cp "$HERE"/main.tex "$TMP"/main.tex
else
  NAME=$(basename "$TARGET" .tex)
  {
    echo '\documentclass[conference]{IEEEtran}'
    echo '\input{preamble}'
    echo '\begin{document}'
    [ "$NAME" = appendix ] && echo '\appendices'
    echo "\\input{sections/$NAME}"
    echo '\input{refs}'
    echo '\end{document}'
  } > "$TMP"/main.tex
fi
cd "$TMP"
for i in 1 2; do pdflatex -interaction=nonstopmode -halt-on-error main.tex > build.log 2>&1 || break; done
if grep -q '^!' main.log 2>/dev/null || [ ! -f main.pdf ]; then
  echo "BUILD FAILED"; grep -n -A6 '^!' main.log | head -40
  rm -rf "$TMP"; exit 1
fi
echo "BUILD OK: $(pdfinfo main.pdf 2>/dev/null | awk '/^Pages/{print $2}') pages"
grep -E 'Overfull \\hbox \(([5-9]|[1-9][0-9]+)\.' main.log | head -20 | sed 's/^/  /'
grep -E "LaTeX Warning: (Reference|Citation) .* undefined" main.log | sort -u | head -20 | sed 's/^/  /'
if [ "$TARGET" = main ]; then cp main.pdf "$HERE"/main.pdf; echo "wrote $HERE/main.pdf"; fi
rm -rf "$TMP"
