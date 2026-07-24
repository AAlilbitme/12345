# What the timing theories add (beyond multihop / multihop_nhop)

`multihop.spthy` and `multihop_nhop.spthy` treat time **relationally** — event
orderings only (`TimedOut`, `Redeemed`, `RedeemBeforeTimeout`), no block
numbers. The three small theories below add a **concrete block clock** so the
CLTV timelocks are *derived*, not assumed. They are kept separate because
signing + natural-numbers + an unbounded clock together exhaust the prover.

| File | What it adds that multihop/nhop do not have |
|------|----------------------------------------------|
| `cltv_blocks.spthy` | Pure CLTV block arithmetic: registers hops with numeric deadlines and **proves the delta is positive** (`d_out << d_in`) and that the claim window is non-empty across a staggered path. No protocol, just the timelock inequality the others assume. |
| `Clock.spthy` | A live block clock (`Clock_Tick`) run through the **full forward lifecycle**: derives the actual claim window between hops (`Claim_Window_Exists`, `Transitive_Preimage_Before_Upstream_Deadline`), shows a loss is exactly a *skipped claim*, and adds lifecycle safety (no HTLC after close, outcome-exclusive) + redeem/refund/honest-flow reachability — all at concrete block heights. |
| `timeout.spthy` | The **counterexample**: with the liveness assumption T2b removed, the early-timeout race is reachable (`Early_Timeout_Race`). Pairs with `Timeout_Race_Blocked` in `multihop.spthy` to prove T2b is load-bearing. |

## multihop.spthy vs multihop_nhop.spthy

Both share the **same channel lifecycle** (handshake, state-update,
revocation/punishment with the linear `RevokedCommitmentUnspent` single-spend,
on-chain settlement) and the **same safety lemmas** (atomicity,
intermediary-never-loses, value conservation). They differ only in the HTLC
routing layer:

| | `multihop.spthy` | `multihop_nhop.spthy` |
|--|------------------|------------------------|
| Path | Fixed **3 hops** (S → F1 → F2 → R) | **Any length** N |
| HTLC forward | **Signed message** over `Out`/`In`, full Dolev–Yao adversary | **Generic linear-fact** `Route(prev,me,ptr,y)` (idealised channel) |
| Forward rules | Two hard-coded (`Forward1_HTLC`, `Forward2_HTLC`) | One generic `Forward_HTLC` that fires at every hop |
| Wormhole attack | **Yes** — reachable + fee-quantified (needs the signed network) | **No** — the idealised route removes the collusion side channel |
| Per-hop auth | Machine-checked (`Forward1_Requires_Offer`, `Forward2_Requires_Forward1`) | Abstracted (transferred by the refinement theorem) |
| Boundaries | none (43/43) | 4 `[use_induction]` causality lemmas commented out (don't terminate on the generic chain) |

The two form a **proof layering**: concrete crypto at 3 hops, idealised route
for safety at arbitrary N. The bridge is `paper/nhop_soundness.tex`.

Everything else — fees, value conservation, wormhole, atomicity — is in
`multihop.spthy` and (except the wormhole) carried to arbitrary length in
`multihop_nhop.spthy`.

## Files documented in the paper

All five theories are covered in `paper/verification_report.tex` (81 lemmas):

1. `multihop.spthy` — 43
2. `multihop_nhop.spthy` — 25
3. `Clock.spthy` — 9
4. `cltv_blocks.spthy` — 3
5. `timeout.spthy` — 1

The N-hop refinement theorem is in `paper/nhop_soundness.tex`.
