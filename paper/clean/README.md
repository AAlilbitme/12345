# Formal Verification of the Lightning Network in Tamarin: LaTeX source

Build: `pdflatex main.tex` twice (IEEEtran, TeX Live 2023). Output: `main.pdf`
(main body 11.96 pages, then references, Appendix A lemma catalogue, Appendix B model listings).

- `main.tex`, `preamble.tex`, `refs.tex`; `sections/*.tex` (one file per part); `figs/*.pdf`
  (Figs. 1-3 cropped from the authors' draft, Fig. 4 is TikZ in `sections/05b_properties.tex`).
- `tools/check_tex.py`: every Tamarin listing must be verbatim from `tamarin/final/lightning.spthy`
  or `lightning_aux.spthy`. `tools/measure.py`: section lengths and the 12-page check.
  `tools/build_one.sh`: compile one section or the whole paper.
- Open items for the authors are LaTeX comments `% TODO` (reference [9]'s first author and scope,
  the camera-ready artifact URL).
