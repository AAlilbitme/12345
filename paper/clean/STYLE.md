# Writing the clean paper: shared contract for all section writers

Goal: turn the draft `Tarmin_LN_7.pdf` (authors: Sana and Simon) plus its verified red-pen
update into a CLEAN, submission-style IEEE paper in LaTeX. Same voice as the draft; all
facts as in the verified artefact. No markup, no TODO boxes, no comments to co-authors in
the visible text.

## Inputs
- Draft body text per page: `/tmp/claude-0/-home-user-12345/b86697a5-7cf6-54b8-baf7-e23643af4bfb/scratchpad/paper/pages/pageNN.txt`
  (rendered pages: Read `/tmp/claude-0/-home-user-12345/b86697a5-7cf6-54b8-baf7-e23643af4bfb/scratchpad/paper/Tarmin_LN_7.pdf` with `pages`).
- Red-pen markup, final and verified: `/home/user/12345/paper/redpen_src/markup/{A,B,C,D,E,Z}.json`
  (A p.1-5, B p.6-9, C p.10-11, D p.12 + new Sec. VI/PTLC/related/limitations/artifact, E p.13-17, Z p.6 fix + liveness-scope insert after p.11).
  `strikes` = text to DROP; `notes` = replacement/added text anchored at a phrase of that page; `inserts` = new material.
  Rendered: `/home/user/12345/paper/Tarmin_LN_7_redpen.pdf`.
- Ground truth: `/home/user/12345/paper/redpen_src/FACTS.md`, `/home/user/12345/tamarin/final/lightning.spthy`,
  `/home/user/12345/tamarin/final/lightning_aux.spthy`, `/home/user/12345/tamarin/final/results.txt`, `/home/user/12345/tamarin/final/Makefile`.

## How to write
1. **Keep the authors' text.** Start from the draft's sentences. Where a sentence is not struck, keep it (fix typos and
   grammar only: "Payements", "honnest", "Howerver", "en efficiently", "restrinctions", "reddeem", "Effectively" etc.).
   Where it is struck, use the note/insert that replaces it. Where a note says "TODO: ..." it is advice: carry it out if you
   can, otherwise leave a LaTeX comment `% TODO: ...` (never visible text).
2. **Voice:** first person plural, present tense, short declarative sentences, concrete Tamarin names in `\code{}`,
   protocol intuition first, then the rule or lemma. British spelling as in the draft (behaviour, modelling, formalisation).
   Emphasis with `\emph{}`. Small caps \tamarin. Do not use em dashes in prose; use commas, colons or parentheses.
3. **Never mention**: csf_final, red pen, agents, AI, Sana's laptop, "markup", "the note at", draft page numbers,
   multihop.spthy, multihop_modified.spthy, Modif.spthy, five theories, HTLCForwarded1/2, Free(ptr), FeeExpected,
   value conservation along the path, "steals exactly the fees". The artefact is `lightning.spthy` + `lightning_aux.spthy` + `Makefile`.
4. **Truth:** every claim about the model or results must match the ground truth files. Copy Tamarin code VERBATIM into
   `\begin{spthy} ... \end{spthy}` (you may drop `//` comments; you may elide with a line containing only `...`).
   Run `python3 -I /home/user/12345/paper/clean/tools/check_tex.py <yourfile>` -- it must report 0 problems.
   Formulas in Tamarin syntax go only in spthy blocks; in prose describe them in words.
5. **Compile:** `bash /home/user/12345/paper/clean/tools/build_one.sh sections/<yourfile>.tex` must print BUILD OK.
   Fix overfull boxes > 5pt (wide listings: they wrap automatically; long `\code{}` names break at underscores).
   Undefined references to labels of OTHER files are expected in the single-file build; your own must resolve.
6. Write ONLY your own file(s) in `/home/user/12345/paper/clean/sections/`. Do not edit preamble.tex, refs.tex, main.tex.

## Macros (preamble.tex)
`\tamarin`, `\proverif`, `\sapic`, `\maude`; `\code{Name_With_Underscores}` for lemma/rule/fact/file names in running text
(use `\texttt{Name\_With\_Underscores}` inside `\caption`, `\section` titles and `\paragraph` titles);
environments `lemma`, `theorem`, `example`, `remark` (italic body, optional `[Name]` argument, as in the draft:
"Lemma 1 (Payment Atomicity). If ..."); `spthy` listing environment; column type `L{width}`.
IEEEtran levels: `\section` (I.), `\subsection` (A.), `\subsubsection` ("1) Title:"), `\paragraph` ("a) Title:").
Figures: `figs/fig1_lifecycle.pdf`, `figs/fig2_transaction.pdf`, `figs/fig3a_payment.pdf`, `figs/fig3b_griefing.pdf`
(cropped from the draft, drawings only: write the captions yourself from the draft's caption text). Fig. 4 is new TikZ.

## Citation keys (refs.tex; numbered in this order)
nakamoto2008 [1], poon2016 [2], oneml2026 [3], bolts [4], tikhomirov2020 [5], malavolta2019 [6], aumayr2021 [7],
grundmann2026 [8], litos2026 [9], dolevyao1983 [10], blanchet2006 [11] (CryptoVerif), barthe2011 [12] (EasyCrypt),
baelde2021 [13] (Squirrel), jeanteur2024 [14] (CryptoVampire), blanchet2001 [15] (ProVerif), meier2013 [16] (Tamarin),
lipp2019 [17] (WireGuard), cremers2017 [18] (TLS 1.3), bip11 [19], bip141 [20], mccorry2019 [21] (Pisa),
smith2022 [22] (agent skipping), backes2017 [23] (liveness/progress, EuroS&P 2017), kiayias2020 [24] (composable Lightning, CSF 2020).
No other references may be cited.

## File plan and labels (use exactly these labels; reference others with `Sec.~\ref{...}`, `Fig.~\ref{...}`, `Table~\ref{...}`, `Lemma~\ref{...}`)
- `00_abstract.tex`: `\begin{abstract}...\end{abstract}` (~200 words) + `\begin{IEEEkeywords}` optional.
- `01_intro.tex`: `\section{Introduction}\label{sec:intro}` with `\paragraph{Payment Channel Networks}`,
  `\paragraph{Protocol Verification}`, `\paragraph{Contributions}` (itemised, each item points to its section) and a one-line paper outline.
- `02_overview.tex`: `\section{Protocol Overview}\label{sec:overview}`;
  `\subsection{Payment Channels}\label{sec:channel}` with `\subsubsection{The Transactions}\label{sec:transactions}`,
  `\subsubsection{The Protocol}\label{sec:protocol}` and `\paragraph{Opening}\label{par:opening}`, Update `par:update`,
  Revocation `par:revocation`, Closing `par:closing`, Punishment `par:punishment`;
  `\subsection{Multi-hop HTLC Routing}\label{sec:routing}`; `example` Path `ex:path`; `remark`s `rmk:claiming`, `rmk:deadlines`;
  Fig. 1 `fig:lifecycle`, Fig. 2 `fig:transaction`, Fig. 3 `fig:inflight` with subfloats `fig:payment`, `fig:griefing`.
- `03_method.tex`: `\section{Symbolic Model and Notation}\label{sec:symbolic}` and
  `\section{Formal Modelling Methodology}\label{sec:method}` with `\subsection{Threat Model}\label{sec:threat}`,
  `\subsection{Liveness Restrictions}\label{sec:restrictions}`, `\subsection{Structural Limitations}\label{sec:structure}`.
- `05a_model.tex`: `\section{Verification of the Model}\label{sec:verification}`; `\subsection{The Core Model}\label{sec:core}`
  (`\subsubsection{Payment Channels}\label{sec:core-channels}`, `\subsubsection{Routing}\label{sec:core-routing}`,
  `\subsubsection{The Wormhole Rule}\label{sec:core-skip}`, `\subsubsection{Amounts and Fees}\label{sec:core-amounts}`);
  `\subsection{Verified Lemmas}\label{sec:verified}` with Table I `tab:results` and the single-spend discipline `par:single-spend`.
- `05b_properties.tex`: `\subsection{Protocol Properties}\label{sec:properties}` with Table II `tab:groups`,
  lemmas `lem:atomicity`, `lem:intermediary`, `lem:intermediary-strong`, `lem:causality`, `lem:fee`, non-vacuity `par:nonvacuity`;
  `\subsection{Timing and Liveness}\label{sec:timing}` with Table III `tab:necessity` and `par:liveness-scope`;
  `\subsection{Griefing and the Wormhole}\label{sec:wormhole}` with Fig. 4 `fig:wormhole` (TikZ, same visual language as Fig. 3a:
  party names in boxes on top, vertical lifelines, HTLC arrows, dashed red arrow for the off-path relay), lemma `lem:skip`.
- `06_bypass.tex`: `\section{Bypass Resistance for Routes of Any Length}\label{sec:bypass}` with subsections
  `sec:bypass-fixed`, `sec:bypass-any` (theorem `thm:anyhop`), `sec:bypass-proof`, `sec:bypass-caveats`,
  `\subsection{Countermeasure: PTLC}\label{sec:ptlc}`.
- `07_related.tex`: `\section{Related Work}\label{sec:related}`, `\section{Limitations}\label{sec:limitations}`,
  `\section{Conclusion}\label{sec:conclusion}` (new, short, in the draft's voice), `\section*{Artifact Availability}`.
- `appendix.tex`: `\section{Lemma Catalogue}\label{app:catalogue}` with one `\subsection` per group (as in the red-pen appendix,
  re-anchored to lightning.spthy; lemma statements verbatim; no file line numbers).

## Decisions already taken (apply them; do not reopen)
- No "first" claim. Position against [8], [9], [24] factually.
- Liveness restrictions are named **T1 = RedeemBeforeTimeout, T2 = OutgoingTimesOutFirst, T3 = IntermediaryMustClaim**
  (the draft's T2b becomes T2; the draft's T2a is now the proven lemma ForwardTimeGap, derived from T2). Use these names everywhere.
- Necessity results (Table III) use columns "T1 removed / T2 removed / T3 removed". `Necessity_OTF_Timeout_Order_Broken` is not mentioned.
- Liveness-as-restriction scope (Z insert) goes into Sec. V-B/Timing (`par:liveness-scope`) and Limitations; Backes et al. [23] is cited there.
- `OneResolutionPerHTLC` is presented as the named interface assumption with its informal justification; no composition theorem is claimed.
- Sec. II stays about the protocol; model-specific sentences move to Sec. IV/V. Simon's duplicated overview paragraphs
  ("Concretely, the two parties open a channel..." and "Channels can be closed either cooperatively...") are merged into the phases (no duplication).
- The wormhole lemma (29 lines) is printed only in the appendix; Sec. V-E describes it in prose and in Fig. 4.
  `Skipped_Requires_Compromise` is printed once, in Sec. V-E. Hop3..Hop6 statements: by name in Sec. VI, verbatim in the appendix.
- `Intermediary_Never_Loses_Strong` is its own lemma right after Lemma 2 (intermediary safety).
- PTLC is Sec. VI-E. Artifact: "available as supplementary material" (anonymous submission); Tamarin 1.10; Maude 3.2 reported unsupported by Tamarin 1.10.
- Reference [9]'s broken first author stays as in the draft (comment only).
- Page budget (two-column): 00+01+02 about 3.5 pages, 03 about 1.5, 05a about 2.5, 05b about 2.5, 06 about 2.5, 07 about 1.5; appendix unlimited.
