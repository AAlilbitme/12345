Red-pen update of the paper draft Tarmin_LN_7.pdf against the csf_final artefact
(tamarin/final/lightning.spthy, lightning_aux.spthy).

  markup/{A..E,Z}.json   strikes / notes / inserts per page range (A: p.1-5, B: 6-9, C: 10-11,
                         D: 12 + new Sec. VI, PTLC, related work, artifact, limitations,
                         E: 13-17 references + appendix, Z: p.6 fix + liveness-scope insert)
  FACTS.md               ground truth the markup was written and checked against
  tools/build_redpen.py  python3 -I tools/build_redpen.py Tarmin_LN_7.pdf OUT.pdf markup/*.json
  tools/check_verbatim.py  every quoted lemma/rule must occur verbatim in the .spthy files
  tools/resolve.py       locate a phrase span on a page (used for strikes and note anchors)
