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

## Update: Grundmann & Hartenstein (arXiv 2505.15568) checked by the author
- They model blockchain time and HTLC timelocks; time may advance by arbitrary
  amounts, justified by a time-abstract bisimulation (Sec. VI-A) that preserves
  which actions become enabled at timelock boundaries.
- They model multi-hop fulfillment and timeout, including a grace period.
- Verified property: honest users eventually recover the correct balance
  (balance security), by finite-state model checking up to four hops.
- Not proved: that a forwarder's channel update completes before the incoming
  CLTV deadline. "Assuming honest and cooperating users and timely delivery of
  messages, payments are guaranteed to succeed" is listed as future work
  (Sec. V, VIII-B).

Differences to our work:
| | Grundmann & Hartenstein | Ours |
|---|---|---|
| Property | balance security | conditional deadline liveness |
| Channel transitions | idealized steps | request, update, state update, commit, receipt |
| Method | finite-state model checking (<= 4 hops) | symbolic Tamarin; 2-hop mechanized composition + induction argument |
| Time | skipping justified by bisimulation | NowIsLatest clock abstraction (stamp invariant proven; consecutive-tick witnesses) |

Safe claim: a symbolic, completion-aware verification of the known CLTV-delta
condition, where completion means the required channel update actually commits,
with explicit receipt and forwarding assumptions, satisfiability witnesses and
tight counterexamples.
Strongest wording: "To our knowledge, this is the first symbolic proof that
relates a forwarder's CLTV gap to the completion of channel updates, rather than
merely to a requested or abstract payment action." Keep "to our knowledge"
until their timelock section and artifacts are compared in detail.

Do NOT claim: first formal treatment of Lightning timelocks; first multi-hop
timing model; first use of time abstraction; a proof that the complete Lightning
protocol guarantees liveness.
