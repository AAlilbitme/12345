# Related work check for the deadline result (draft; from search snippets/abstracts)

Caveat: full texts were not read (fetch to arxiv/kit failed); rows marked (K) are
from background knowledge and need confirmation before citing.

| Work | Tool | Scope | Properties | Liveness/timing | Mechanized |
|---|---|---|---|---|---|
| Grundmann & Hartenstein, TLA+ Lightning (arXiv 2307.02342; 2505.15568; Springer 2025; KIT 1000160211) | TLA+/TLC, refinement | single + multi-hop (bounded) | balance security | time abstracted; no deadline theorem found | partly |
| Fabianski, Stefanski, Thyfronitis Litos, "A Formally Verified Lightning Network" (arXiv 2503.07200) | Why3 | single channel | honest funds safe | no | yes |
| Weintraub et al., Payout Races (arXiv 2405.02147) | Spin | single hop | attacks found | no deadline proof | yes |
| Boyd et al., Tamarin HTLC, FMBC 2020 (OASIcs.FMBC.2020.5) | Tamarin | cross-chain HTLC (not LN) | HTLC security | chain-growth condition | yes |
| Kiayias & Thyfronitis Litos, UC Lightning, CSF 2020 (eprint 2019/778) | UC (paper) | multi-hop | balance security | timelock/delay parameters | no |
| Malavolta et al. AMHL; Aumayr et al.; Dziembowski et al.; Elmo/Daric (K) | UC (paper) | multi-hop/virtual | balance security | Delta-bounded timelocks | no |
| Flood & Loot; time-dilation attacks | attacks | multi-hop | break bounded delay | yes (empirically) | no |

Already known: the CLTV-delta condition itself (BOLT folklore; UC proofs need it
under synchrony); that the delay bound is load-bearing (Flood & Loot, time
dilation); mechanized multi-hop safety (TLA+); Tamarin for HTLC timing (FMBC 2020).

Candidate novelty (to confirm by reading Grundmann-Hartenstein timelock section):
mechanized, completion-aware per-hop deadline theorem (operation counts only after
update/revoke/commit), composed over two forwarders, with satisfiability witness
and tightness counterexamples (gap D-1 fails; no bound fails).

Suggested framing: a mechanized, tight, completion-aware verification of the
known CLTV-delta design condition, not a new protocol insight.
