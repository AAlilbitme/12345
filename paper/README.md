# Verification report (LaTeX)

`verification_report.tex` — a self-contained write-up of the modular model:
what we modelled, what we proved, what failed, per-lemma statistics, and the
four figures.

## Build
```bash
cd paper
pdflatex verification_report.tex
pdflatex verification_report.tex   # second pass for the ToC / cross-refs
```
Requires a TeX distribution (TeX Live / MiKTeX). No exotic packages —
`article`, `graphicx`, `booktabs`, `listings`, `hyperref`, `underscore`, `xcolor`.

## Figures
`figures/*.pdf` are embedded by the document; `figures/*.svg` are the editable
sources. To regenerate the PDFs from the SVGs:
```bash
pip install cairosvg
python3 - <<'PY'
import cairosvg
for s,d in [("figure_index","fig_index"),("figure_channel","fig_channel"),
            ("figure_4party","fig_4party"),("figure_timing","fig_timing")]:
    cairosvg.svg2pdf(url=f"figures/{s}.svg", write_to=f"figures/{d}.pdf")
PY
```

| Figure | Covers |
|--------|--------|
| `fig_index`   | master map: 5 core files -> 3 protocol views (+ map), 58 lemmas |
| `fig_4party`  | multi-hop routing / value / attack lemmas (multihop.spthy) |
| `fig_channel` | Alice<->Bob channel lifecycle lemmas (multihop.spthy) |
| `fig_timing`  | staggered CLTV timing (cltv_blocks, gaps, t2b_attack) |

## Verification

Run from the repository root:

```bash
python3 run.py                  # 58-lemma core package
make nhop                      # 31-lemma idealised N-hop fee abstraction
```

The paper distinguishes machine-checked lemmas, consequences of explicit trace
restrictions, reachability witnesses, and bounded timeout observations. The
separate theories are not connected by a machine-checked refinement proof.
