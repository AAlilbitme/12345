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
| Boundaries | none (43/43) | one `[use_induction]` lemma commented out, `Settle_Requires_Receiver_Release` (does not terminate on the generic chain) — 31/31 otherwise |

The two form a **proof layering**: concrete crypto at 3 hops, idealised route
for safety at arbitrary N. The bridge is `paper/nhop_soundness.tex`.

Everything else — fees, value conservation, wormhole, atomicity — is in
`multihop.spthy` and (except the wormhole) carried to arbitrary length in
`multihop_nhop.spthy`.

## Files documented in the paper

All five theories are covered in `paper/verification_report.tex`. Every one
of them now verifies with no un-re-run lemmas. Final campaign, Tamarin
1.10.0 / Maude 3.1, one machine, one sitting:

| Theory | Lemmas | Time | Result |
|--------|-------:|-----:|--------|
| `multihop.spthy` | 43 | 353.31 s | 43/43 |
| `multihop_nhop.spthy` | 31 | 134.39 s | 31/31 |
| `Clock.spthy` | 9 | 54.37 s | 9/9 |
| `cltv_blocks.spthy` | 3 | 0.23 s | 3/3 |
| `timeout.spthy` | 1 | 0.06 s | 1/1 |
| **total** | **87** | **542.36 s** | **87/87** |

87 lemma checks over **61 distinct properties**: 26 of the N-hop theory's 31
lemmas are name-for-name re-proofs of `multihop.spthy` lemmas against the
generic routing layer, not new properties (43 + 9 + 3 + 1 = 56 distinct,
plus 5). The 5 genuinely new at that layer are `Forward_Requires_Incoming`
(279 steps), `Amount_Strictly_Decreases_Per_Hop`,
`Fee_Only_On_Successful_Forward`, `Multihop_Payment_With_Fees_Possible`,
and `Redeem_Requires_Receiver_Release`.

`archive/PaymentChannels.spthy` (8 lemmas, 18.83 s, 8/8) is *not* counted:
it is rule-for-rule contained in `multihop.spthy`'s channel layer. It is
worth keeping as an exhibit for the single-spend finding, though — its
`Publish_Revoked_A` is gated only by the persistent `!RevokedSecret`, i.e.
it is the *pre-fix* state of Instance 2 of the pathology, and the fix that
`multihop.spthy` applies (the linear `RevokedCommitmentUnspent` token) is
exactly the delta between the two files.

### Why `Clock.spthy` needed fixing

It previously did not terminate. Three causes, all resolved:

1. `Clock_Start` had **empty premises**, so it could fire unboundedly often,
   spawning independent block chains. Fixed with `Fr(~init)` plus a
   `restriction OneClock` forcing a single `ClockStart()` timepoint.
2. `Sender_Offer` and the forward rules re-produced `Channel(...)` without
   consuming anything one-shot, so HTLCs could be re-offered on the same
   output forever. Fixed by adding the linear `Free(~ptr)` token to
   `Open_Channel` and consuming it in `Sender_Offer`, `Forward_HTLC`,
   `Forward_Hop1`, `Forward_Hop2` — the same single-spend discipline the
   paper's main finding is about, applied here for termination rather than
   for soundness.

Result: hangs indefinitely → 9/9 in 54.37 s.

The N-hop refinement theorem is in `paper/nhop_soundness.tex`.
