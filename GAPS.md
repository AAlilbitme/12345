# Security gap review — status

Honest status of the six gaps raised in review of the Lightning Network Tamarin
model. The guiding principle (learned from the rejected "T4" restriction): a
property is only addressed if it is **proven from the protocol's structure**, or
**honestly documented as out of scope / a liveness boundary**. A restriction
that asserts the conclusion is not a proof — a suspiciously short proof is a
warning sign, not a success.

| # | Gap | Status | Where |
|---|-----|--------|-------|
| 1 | Channel-state / post-close coupling | **Proven** | `gaps.spthy` |
| 2 | Replay / freshness | **Proven** | `multihop.spthy` |
| 3 | Payment privacy / unlinkability | **Out of scope (documented)** | this file |
| 4 | Timing / liveness fairness | **Timing proven; liveness boundary documented** | `gaps.spthy` |
| 5 | On-chain enforcement / dispute finality | **Reachability + exclusivity proven; full liveness documented** | `gaps.spthy` |
| 6 | Value / balance conservation | **Proven** | `multihop.spthy` (merged) |

---

## Gap 1 — Channel-state / post-close coupling  (`gaps.spthy`)

**Problem.** In `multihop.spthy` the channel is the *persistent* fact
`!ChannelConnect`, which is never revoked. A persistent fact cannot be consumed,
so that layer alone has no way to say "this channel is closed" — it would permit
an HTLC to be added *after* a close. This was the wall the earlier attempts hit:
you cannot forbid post-close use while the channel is purely persistent.

**Fix.** Model the channel as a **linear** resource with an explicit lifecycle
`Open → (HTLC adds) → Close`. `Close_Channel` consumes the `Channel(...)` token;
`Add_HTLC` requires it. After a close the token is gone, so adding an HTLC is
genuinely unreachable. (Full post-close enforcement lives in `gaps.spthy`, kept
separate because adding it to `multihop.spthy` reintroduces the OOM combination.)

**Proven.** `No_HTLC_After_Close` — every `HTLCAdded(ptr)` strictly precedes any
`ChannelClosed(ptr)`. Supported by `HTLC_Needs_Open_Channel`.

**Update (Stage 1).** `multihop.spthy` now also carries a linear `Free(ptr)`
channel slot for the *HTLC-uniqueness* half of this concern: each output's slot
is consumed on HTLC-add, so "one HTLC per output" is structural there too (this
replaced the old `OneHTLCPerPtr` axiom). The full open→close lifecycle enforcement
still lives in `gaps.spthy`.

## Gap 2 — Replay / freshness  (`multihop.spthy`)

**Problem.** No lemma asserted single-use of an invoice/fulfillment; the fresh
`~x` gave implicit but unproven protection.

**Fix / Proven.** `Invoice_Released_Once`: a receiver releases the preimage for a
given invoice **at most once** (`ReceiverInv` is linear and consumed on
fulfillment, and `~x` is fresh per invoice). So an adversary replaying the public
`fulfill` message cannot make the receiver release the preimage twice, and the
linear `Pending` facts downstream redeem each HTLC at most once. A misbehaving
*sender* re-offering the same invoice is a sender-side concern, not a replay
attack, so it is deliberately not folded into this property.

**Update (Stage 1 hardening).** Replay on the *forwarding* side is now blocked
**structurally**: the linear `Free(ptr)` slot is consumed by each HTLC-add, so a
replayed offer cannot re-fire an honest forward. The double-forward probe
(`AUDIT_Double_Forward_Reachable`) is falsified without any restriction — see
`multihop.spthy`'s header and REPORT2 §11. This superseded the earlier
`OneHTLCPerPtr` axiom.

## Gap 3 — Payment privacy / unlinkability  (out of scope, documented)

**Decision.** This is a **scope exclusion**, stated explicitly rather than
silently omitted. Everything in these models travels in cleartext; there is no
onion-routing layer. Sender–receiver anonymity and path privacy depend on onion
encryption (Sphinx) and are **confidentiality** properties over the routing
metadata — a fundamentally different modelling effort (per-hop encryption,
indistinguishability / observational-equivalence goals) from the
**integrity/safety** properties these theories target.

Modelling it honestly would require: a Sphinx-style layered-encryption rule set,
and `diff`-based observational-equivalence lemmas (Tamarin's `--diff` mode) for
unlinkability. That is a separate work item; we do **not** claim any privacy
guarantee here. The models prove nothing about confidentiality of route or
amounts, and should not be read as if they do.

## Gap 4 — Timing / liveness fairness  (`cltv_blocks.spthy`)

**Problem.** `Intermediary_Never_Loses` falsifies without a time model, and the
earlier T1–T3 (and the rejected T4) tried to rescue it by **asserting** an
ordering between `TimedOut(ptrOut)` and `TimedOut(ptrIn)`. That is circular: T2
is vacuous when `TimedOut(ptrOut)` never fires, and ordering the two timeouts is
the theorem in disguise.

**Fix (the honest part).** Assign every channel a concrete **CLTV expiry block
number** at open. The route enforces the Lightning CLTV-delta invariant
`dOut < dIn` as a real check on those static numbers. Redeem is valid only
at-or-before a deadline; refund only strictly after. The claim window then
**emerges from arithmetic** instead of being asserted:

```
bOut ≤ dOut  <  dIn  <  bRef     ⟹     bOut < bRef
```

**Proven, assumption-free:** `Claim_Window_Exists` (152 steps) — whenever the
downstream HTLC is redeemed (revealing the preimage at block `bOut`) and the
upstream HTLC is later refunded (at block `bRef`), necessarily `bOut < bRef`.
The preimage is *always* revealed while the upstream HTLC is still claimable.
This uses **no liveness restriction and no ordering of timeout events** — it is
derived purely from the per-channel deadlines fixed at setup. This is the real
fix for the timing gap.

**Liveness boundary (documented, not faked).** `Intermediary_Never_Loses` itself
is a **liveness** property ("an honest, online node never loses"), not trace
safety: the trace where the node simply never submits its claim always exists.
We therefore do **not** add a restriction forcing the claim (that would be T4
again). `Loss_Implies_Skipped_Claim` confirms a loss coincides exactly with not
having claimed (claim and refund spend the same output). The residual is pure
liveness — the node being online — which is outside trace-safety and is stated,
not papered over.

## Gap 5 — On-chain enforcement / dispute finality  (`gaps.spthy`)

**Problem.** Off-chain settlement was not coupled to a guarantee that the honest
party can force the correct outcome on-chain.

**Proven.** On the linear-channel scaffold:
- `Outcome_Exclusive` — an HTLC cannot be both claimed and refunded.
- `Redeem_Reachable` / `Refund_Reachable` — both dispute paths (sweep with
  preimage; refund after timeout) are reachable, so an honest party is never
  *structurally* deprived of a resolution path.
- `Resolution_Has_Lock` — every on-chain resolution corresponds to a real HTLC
  that was locked on its channel first.

**Liveness boundary.** "Every pending HTLC *is* eventually resolved" is liveness
(same boundary as Gap 4) and is documented rather than asserted.

## Gap 6 — Value / balance conservation  (`multihop.spthy`, merged)

**Problem.** The model tracked HTLC existence/outcome but no amounts, so "no
money created or destroyed" was unmodelled.

**Fix / Proven.** A **signed** amount `%v` is threaded through the invoice and
every hop with a real fee model (`Eq(%vIn, %vOut %+ %fee)`). Originally a
separate `value_conservation.spthy`; now **merged into `multihop.spthy`** (the
signing + nat combination is tractable once the unbounded clock is absent):
- `EndToEnd_Value_Conservation` — the sender locks the receiver's amount plus a
  strictly positive total fee; no value created or destroyed.
- `Fee_Conservation_Hop1` / `Fee_Conservation_Hop2` — per-hop `%vIn = %vOut %+ %fee`.
- `Fee_Strictly_Positive_Hop1/Hop2` — every hop's fee is `> 0` (structural, from
  the natural-number sort).
- `Receiver_Paid_Invoice_Amount` — the receiver is only ever paid an invoiced amount.

---

## How to reproduce

```
# parse + wellformedness
tamarin-prover <file>.spthy

# prove everything in a file
tamarin-prover <file>.spthy --prove

# prove one lemma
tamarin-prover <file>.spthy --prove=<LemmaName>
```

Run with `LANG=C.utf8 LC_ALL=C.utf8` so Tamarin can pretty-print logical
symbols. The full `multihop.spthy` needs `--derivcheck-timeout=0`; the gap
theories are deliberately small so each proof terminates in under 2 minutes.

## File inventory (compact form)

| File | Covers |
|------|--------|
| `multihop.spthy` | Full channel model + HTLC routing + Gap 2 (replay) + Gap 6 (value/fees, merged) |
| `gaps.spthy` | Gaps 1, 4, 5 (lifecycle + timing + dispute) |
| `cltv_blocks.spthy` | Gap 4 arithmetic (CLTV-delta windows exist) |
| `t2b_attack.spthy` | T2b necessity (early-timeout race without the liveness assumption) |
| `witnesses.spthy` | Finite-clock reachability witnesses |
| `GAPS.md` | This document |

`value_conservation.spthy`, `PaymentChannels.spthy`, and the old
`multihop_no_fees.spthy` are retired to `archive/` (all subsumed by
`multihop.spthy`). `channel_lifecycle.spthy` was consolidated into `gaps.spthy`;
`cltv_blocks.spthy` remains a separate file. The verified suite is driven by
`run.py` (or `make`).
