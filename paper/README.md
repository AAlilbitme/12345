# Verification report (LaTeX)

`verification_report.tex` — a self-contained write-up of the whole model:
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
| `fig_index`   | master map: 5 files -> 4 figures, 81 lemmas |
| `fig_4party`  | multi-hop routing / value / attack lemmas (multihop.spthy) |
| `fig_channel` | Alice<->Bob channel lifecycle lemmas (multihop.spthy) |
| `fig_timing`  | staggered CLTV timing (cltv_blocks, Clock, timeout) |

The five theories are `multihop.spthy` (43), `multihop_nhop.spthy` (25),
`Clock.spthy` (9), `cltv_blocks.spthy` (3), and `timeout.spthy` (1).
