# Formal Verification Report — Lightning Network Multi-Hop HTLC Routing (Tamarin 1.8)

The protocol is formalised as a **modular package of theories** rather than one
monolithic file. Each theory proves a distinct aspect; they do not share rules,
so a property proved in one is not silently assumed in another. The split is
deliberate — a single combined theory OOM-kills Tamarin, because the signing
equational theory, natural-number induction, and an unbounded block clock do not
coexist in one tractable search space.

| File | Theory | Aspect | Builtins |
|------|--------|--------|----------|
| `multihop.spthy` | `multihop` | Main protocol: channel lifecycle + HTLC routing + atomicity | hashing, signing |
| `Clock.spthy` | `Clock` | Block-clock lifecycle & CLTV timing safety | natural-numbers |
| `Cltv.spthy` | `cltv_blocks` | Pure CLTV block arithmetic | natural-numbers |
| `timeout.spthy` | `timeout` | Early-timeout race counterexample | — |
| `value_cons.spthy` | `value_conservation` | Value & fee conservation | hashing, signing, natural-numbers |

---

## 1. `multihop.spthy` — main protocol & atomicity

The primary theory. It carries the **full payment-channel lifecycle** and the
**multi-hop HTLC layer** in one model (`Sender → Forward1 → Forward2 → Receiver`).

**Channel-lifecycle part (what used to be the payment-channel layer):**
- Handshake (`A_Send_Proposal` → `B_Recv_Proposal` → `A_Recv_From_B`),
  initial state commitment, fund-locking and channel open
  (`Lock_Funds_And_Open`).
- State update + revocation (`Update_State`, `Revoke_Old_Secret`), on-chain
  publish paths, cooperative close (`Honest_Close`), cheat/punishment
  (`Publish_Revoked_*`, `Punish_*`), and settlement.
- Proves, e.g.: `state_update`, `Funds_Locked_Before_Update`,
  `Update_Requires_Negotiation` (every update was negotiated first),
  `No_Punishment_Without_Cheating` (punishment ⇒ cheat or key compromise),
  `Protocol_execution` / `Cooperative_Close_Execution` (the honest flow runs),
  `delayed_funds` / `instant_funds` / `settlement_is_traceable`.

**HTLC / payment part:**
- Invoice creation, offer, two forwards, receiver fulfil, intermediary settle,
  sender settle, and the timeout/refund rules.
- Proves, e.g.:
  - `Multihop_Payment_Possible` — the full 8-step path settles (exists-trace).
  - `Refund_Possible`, `Distinct_Parties_Configuration` — refund and a clean
    3-party config are reachable.
  - `Forward1_Requires_Offer`, `Forward2_Requires_Forward1`,
    `Fulfill_Requires_Forward2` (+ `_Honest` variants) — each hop requires the
    previous one (or a key compromise).
  - `Preimage_Secret_Until_Released`, `Invoice_Has_Secret_Preimage`,
    `Claim_Requires_Release`, `Settle_Requires_Receiver_Release` — preimage
    secrecy / settlement authentication.
  - `Invoice_Authenticates_Settlement`, `Forged_Invoice_Requires_Key_Compromise`
    — a settlement implies a genuine invoice unless the receiver's key leaked.
  - **`Intermediary_Never_Loses_Under`** — an honest forwarder whose outgoing
    HTLC is redeemed cannot have its incoming HTLC refunded unless its key was
    compromised.
  - **`Payment_Atomicity_Under`** — once the receiver fulfils the final HTLC,
    the sender's HTLC on the same hash cannot be refunded (honest model).
  - **`Timeout_Race_Blocked`** — the early-timeout race is impossible *with* the
    liveness restriction active (the "blocked" side of the certificate, see §4).

**Timing restrictions (T1–T3 + liveness):**
- `RedeemBeforeTimeout` (T1) — redeem only before timeout.
- `ForwardTimeGap` (T2) — outgoing HTLC times out strictly before incoming.
- `IntermediaryMustClaim` (T3) — if the outgoing HTLC is redeemed before the
  incoming timeout, the node sweeps the incoming HTLC.
- **`HonestPartiesActBeforeIncomingTimeout` (T2b)** — the *liveness assumption*:
  every honest party claims within its CLTV window (outgoing times out before
  incoming). The two headline lemmas above are explicitly conditional on this.
  It is an **assumption, not a derived fact** — `Cltv.spthy` proves the windows
  are non-empty, but a trace tool cannot prove parties *act* in time. Without
  T2b the early-timeout race is a genuine counterexample (§4).

---

## 2. `Clock.spthy` — block-clock lifecycle & timing safety

A block clock (`Clock_Tick` increments height, emitting a persistent
`!BlockReached`), a **linear** channel token, and the HTLC state machine with
concrete CLTV deadlines. It proves the lifecycle/timing facts the signing-heavy
main theory cannot safely carry.

**What it proves (9 lemmas, all verified):**
- `HTLC_Needs_Open_Channel`, `No_HTLC_After_Close` — an HTLC only exists on an
  open channel and none can be added after close (the linear channel token is
  the mechanism; induction over the clock).
- `Claim_Window_Exists`, `Transitive_Preimage_Before_Upstream_Deadline` — the
  per-hop and end-to-end CLTV windows are non-empty
  (`bOut ≤ dOut < dMid < dIn`).
- `Loss_Implies_Skipped_Claim` — any loss reduces to a skipped claim (pure
  liveness residual).
- `Outcome_Exclusive` — redeem and refund are mutually exclusive.
- `Redeem_Reachable`, `Refund_Reachable`, `Honest_Flow_Possible` — the honest
  settlement and refund paths are reachable (non-vacuity).

Bulk run: **≈ 147 s, 9/9 verified, no OOM** (the heaviest is
`No_HTLC_After_Close`, a 6044-step induction over the clock).

---

## 3. `Cltv.spthy` — CLTV block arithmetic

The pure-arithmetic side of CLTV staggering. It abstracts away HTLC mechanics
and proves only the block-height invariants that *justify* the T1–T3 timing
restrictions used in `multihop.spthy`.

**What it proves (3 lemmas):**
- `CLTV_Gap_Is_Positive` — `d_out < d_in` (justifies **T2**, ForwardTimeGap).
- `Claim_Window_Nonempty` — `b_fulfill < d_in` (justifies **T1+T2** composed).
- `Staggered_Path_Safe` — for a two-hop chain `d1 < d2 < d3`, a preimage revealed
  at `b ≤ d1` satisfies `b < d2 ∧ b < d3` (justifies **T3**).

This is the assumption-free derivation of *why* T1–T3 are simultaneously
satisfiable: staggered CLTVs make the cascade work. It does **not** claim parties
act in time — that remains T2b in `multihop.spthy`.

---

## 4. `timeout.spthy` — early-timeout race (the attack T2b defends against)

The minimal theory that **exhibits the race**. It contains just enough structure
(forward, timeout, refund, redeem) for Tamarin to construct the attack, and it
**deliberately omits** the T2b restriction.

**What it proves:** `Early_Timeout_Race` (exists-trace) finds a concrete trace
where the incoming channel times out and refunds *before* the outgoing HTLC is
redeemed (`#k < #i`). T3's precondition is then inapplicable, so the intermediary
loses with **no key compromise**.

**Why it must be a separate file:** Tamarin restrictions are *global*. To
*witness* the race you need a world *without* T2b; to prove the race is *blocked*
you need T2b present. You cannot have both in one theory:
- `timeout.spthy` (no T2b) → race **reachable** (`Early_Timeout_Race`).
- `multihop.spthy` (with T2b) → race **blocked** (`Timeout_Race_Blocked`).

Together they form a **two-sided certificate**: the assumption is load-bearing
(remove it → a real attack reappears) and sufficient (add it → the attack
disappears). The corresponding rules are kept, commented out, inside
`multihop.spthy` with a note pointing here.

---

## 5. `value_cons.spthy` — value & fee conservation

Amount/fee conservation in a separate amount-focused abstraction (signing + nat
arithmetic), modelling the per-hop fee structure `vS = vR + fee1 + fee2`.

**What it proves (3 lemmas):**
- `Forwarding_Possible` — a forwarding-with-fee step is reachable (non-vacuity).
- `Fee_Conservation_Per_Hop` — `vIn = vOut + fee` at each hop.
- `Value_Conserved_End_To_End` — `vS = vMid + fee1` and `vMid = vR + fee2`.

Scope is explicit: this proves **amount conservation**, not economic
rationality. Fees are adversarially chosen via `In(%fee)`; `fee > 0` is a
game-theoretic assumption outside symbolic verification.

---

## 6. What we tried first, why it failed, and how we changed it

Each dead-end below shaped the final structure.

**(a) One monolithic theory → OOM.**
*First:* put everything in `multihop.spthy`. *Failed:* signing equational theory
+ nat induction + unbounded clock blow up memory together. *Fix:* split into the
modular package above; each theory carries only the builtins it needs.

**(b) Reachability witnesses under the unbounded clock → OOM.**
*First:* keep the two-hop and timed-refund existence witnesses in `Clock.spthy`
with the unbounded `Clock_Tick`. *Failed:* the solver unifies a needed
`!BlockReached(%d)` against *infinitely many* persistent block facts while
solving the `<<` ordering — `Killed` (OOM), in isolation and in bulk. Bounding
ticks with a `restriction` did **not** help (Tamarin applies the restriction
*after* building the case split). *Fix:* drop those two heavy witnesses from
`Clock.spthy`; the windows themselves are still proved by `Claim_Window_Exists`
and `Transitive_Preimage_Before_Upstream_Deadline`. (If a witness is wanted, it
verifies in <10 steps under a *finite* clock — sound for an existence claim,
since any finite-clock trace is also a trace of the unbounded model.)

**(c) Running a whole file at once → OOM on a normal laptop.**
*First:* `tamarin-prover Clock.spthy --prove` (all lemmas, one process).
*Failed:* `Killed` — too much resident memory at once. *Fix:* prove **one lemma
per invocation**; after (b), the trimmed bulk run fits in memory again.

**(d) `seqdfs` everywhere → some lemmas hang.**
*First:* apply `--stop-on-trace=seqdfs` globally. *Failed:* it *rescues*
`multihop.spthy`'s heavy exists-traces but *hangs* the nat-arithmetic / linear-
token lemmas in `Clock.spthy` and `Cltv.spthy`. *Fix:* per-file strategy —
`seqdfs` only for `multihop.spthy` and `timeout.spthy`, never for the nat
theories.

**(e) Fresh nonces as amounts → vacuously-true security lemmas.**
*First:* in `value_cons.spthy`, model amounts as fresh values `~x` and write
`Eq(~a, ~b %+ ~c)`. *Failed:* fresh is not a subsort of nat, so the equation can
never hold — the forward rules could never fire and every security lemma was
*vacuously* true. *Fix:* make all amounts **nat-typed** (`%vIn`, `%fee`, via
`In(%x)`), seed `%1` so any nat is composable; `%+` is now well-sorted and the
rules fire.

**(f) Three-term AC sum → Tamarin 1.8 crash.**
*First:* state end-to-end conservation as `vS = vR %+ fee1 %+ fee2`. *Failed:*
Tamarin 1.8.0 crashes on a 3-term AC sum in guarded-formula form. *Fix:* split
into two pairwise equalities `vS = vMid %+ fee1` and `vMid = vR %+ fee2`.

**(g) `b ≤ d_out` → sort-inference warning.**
*First:* express "before the deadline" as `b << d_out %+ %1`. *Failed:* Tamarin
1.8 sort inference fails to resolve `d_out` as nat there. *Fix:* use strict
`b << d_out` (excludes same-block fulfilment for a sort-inference reason, not a
modelling one).

**(h) Vacuous balance lemma.**
*First:* a balance lemma required `NewStateBuilt` and `StateUpdate` at the *same*
timestamp, but they fire in different rules — premise never satisfiable.
*Fix:* replaced with `Update_Requires_Negotiation` (every update was negotiated
first), which follows from `Fr(~n_new)` freshness.

**(i) Putting the race in the main theory → falsifies the safety lemmas.**
*First:* keep the timeout-race rules inside `multihop.spthy`. *Failed:* with the
race rules present and T2b active the model is inconsistent to reason about;
without T2b the safety lemmas falsify. *Fix:* move the race to `timeout.spthy`
(no T2b) and keep only `Timeout_Race_Blocked` in `multihop.spthy` (with T2b) —
the two-sided certificate.

**(j) Encoding crash.**
*Symptom:* `commitBuffer: invalid argument (invalid character)`. *Fix:* run with
`LANG=C.utf8 LC_ALL=C.utf8`.

---

## 7. How to reproduce

```bash
export LANG=C.utf8 && export LC_ALL=C.utf8

# nat / arithmetic theories — NO seqdfs
tamarin-prover Cltv.spthy       --derivcheck-timeout=0 --prove
tamarin-prover Clock.spthy      --derivcheck-timeout=0 --prove
tamarin-prover value_cons.spthy --derivcheck-timeout=0 --heuristic=c --prove

# signing / exists-trace theories — WITH seqdfs
tamarin-prover timeout.spthy  --derivcheck-timeout=0 --heuristic=c --stop-on-trace=seqdfs --prove
tamarin-prover multihop.spthy --derivcheck-timeout=0 --heuristic=c --stop-on-trace=seqdfs --prove
```

If a file OOMs in bulk, prove it one lemma at a time:
`tamarin-prover <file> --derivcheck-timeout=0 --prove=<LemmaName>`.
