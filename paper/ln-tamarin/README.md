# Formal Verification of the Lightning Network in Tamarin — paper source

Complete paper source. Build with:

    pdflatex main && bibtex main && pdflatex main && pdflatex main

Compiles clean: 0 errors, 0 undefined references, 10 pages.

## Layout

| File | Contents |
|---|---|
| `main.tex` | document skeleton, `\input`s everything else |
| `macros.tex` | preamble: packages, colour palette, `tamarin` listings language, theorem environments |
| `fig.tex` | the annotated multi-hop sequence diagram (`fig:multihop`) |
| `bibliography.bib` | references |
| `sections/*.tex` | one file per section |

## Numbers in the text

Every figure quoted in the paper traces to a verification run recorded in the
repo root:

- 87 lemma checks / 61 distinct properties across five theories
- `multihop.spthy` 43 lemmas, 353.31 s · `Modif.spthy` 31, 134.39 s ·
  `Clock.spthy` 9, 54.37 s · `Cltv.spthy` 3, 0.23 s · `timeout.spthy` 1, 0.06 s
- total 542.36 s, Tamarin 1.10.0 / Maude 3.1
- `Wormhole_Fee_Theft_Reachable` 51 steps, `Wormhole_Steals_Exactly_The_Fees`
  81 steps (see `REPORT2.md` §9)
- T3-removal counterexample 59 steps (see `REPORT2.md` §8)

## Before submission

Two citations were added because the text needs them and are **not** verified:

- `smith2022modelling` — the agent-skipping paper the wormhole quantification
  is positioned against. Author list and venue are placeholders.
- `mccorry2019pisa` — the watchtower citation. Details believed correct but
  unchecked.

`\Cref{thm:refinement}` is a pen-and-paper argument; the paper says so, but the
full induction referenced as "given in the artifact" still needs writing up.
