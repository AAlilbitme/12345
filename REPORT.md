# Formal Verification Report — Lightning Network Multi-Hop HTLC Routing (Tamarin 1.8)

> **Historical note (Report 1.0).** This document reflects the *pre-merge* layout.
> Some filenames below have since changed and some theories were consolidated:
> `Clock.spthy` → `gaps.spthy`, `Cltv.spthy` → `cltv_blocks.spthy`,
> `timeout.spthy` → `t2b_attack.spthy`, and `value_cons.spthy` was **merged into**
> `multihop.spthy` (value/fee conservation now lives there). For the current
> 5-theory structure, lemma counts, and the later results (replay hardening,
> wormhole, griefing, economic soundness, the reusable-channel boundary), see
> **REPORT2.md**. The canonical run configuration is **`run.py`** (or `make`).
> The modelling narrative below remains accurate for the theories as they were.

The protocol is formalised as a **modular package of five theories**. Each proves
a distinct aspect; they do not share rules, so a property proved in one is not
silently assumed in another. The split is deliberate — one combined theory
OOM-kills Tamarin (signing equational theory + nat induction + unbounded clock
cannot coexist in one tractable search space).

For every lemma below we state **what it models** (the slice of protocol
behaviour the rules capture) and **what it proves** (the property the lemma
establishes over that model).

| File | Theory | Aspect | Builtins |
|------|--------|--------|----------|
| `multihop.spthy` | `multihop` | Channel lifecycle + HTLC routing + atomicity | hashing, signing |
| `Clock.spthy` | `Clock` | Block-clock lifecycle & CLTV timing safety | natural-numbers |
| `Cltv.spthy` | `cltv_blocks` | Pure CLTV block arithmetic | natural-numbers |
| `timeout.spthy` | `timeout` | Early-timeout race counterexample | — |
| `value_cons.spthy` | `value_conservation` | Value & fee conservation | hashing, signing, natural-numbers |

---

## 1. `multihop.spthy` — main protocol & atomicity

**Modelled:** the full payment channel from birth to death — signed handshake,
initial state commitment, fund-locking/open, state update with revocation,
on-chain publish paths, cooperative close, cheat + punishment, settlement — plus
the multi-hop HTLC layer `Sender → Forward1 → Forward2 → Receiver` with
invoice, two forwards, receiver fulfil, intermediary/sender settle, and
timeout/refund. Timing is enforced by restrictions T1–T3 and the liveness
assumption T2b.

### Channel-lifecycle lemmas

- **`state_update`** — *Models:* state updates and channel opening. *Proves:* a
  state update can only occur on a channel that was opened earlier (`StateUpdate
  ⇒ earlier ChannelOpen`).
- **`Funds_Locked_Before_Update`** — *Models:* fund-locking vs. update ordering.
  *Proves:* every update is preceded by funds being locked.
- **`Update_Requires_Negotiation`** — *Models:* the two-phase build-then-revoke
  update. *Proves:* every committed update was preceded by a negotiated new state
  (`StateUpdate ⇒ earlier NewStateBuilt`). (Replaced an earlier *vacuous* balance
  lemma — see §6h.)
- **`delayed_funds`** / **`instant_funds`** — *Models:* the two settlement paths
  (CSV-delayed vs. instant). *Proves:* settled funds always trace back to a prior
  on-chain produce event of the matching kind.
- **`settlement_is_traceable`** — *Models:* settlement. *Proves:* every
  `FundsSettled` is accompanied by a concrete settled transaction.
- **`No_Punishment_Without_Cheating`** — *Models:* the revocation/punishment
  game. *Proves:* a party is punished only if it actually cheated (published a
  revoked state) **or** its key was compromised.
- **`Protocol_execution`** — *Models:* open → update → close. *Proves:* the honest
  end-to-end channel run is reachable (exists-trace).
- **`Cooperative_Close_Execution`** — *Models:* cooperative close. *Proves:* a
  channel can open and close cooperatively with no state update in between
  (exists-trace).

### HTLC / payment-layer lemmas

- **`Multihop_Payment_Possible`** — *Models:* the entire 8-step routed payment.
  *Proves:* the full path (invoice → offer → forward1 → forward2 → fulfil →
  claim → claim → settle) executes in order (exists-trace; the headline liveness
  witness).
- **`Refund_Possible`** — *Models:* an offered-but-unfulfilled payment.
  *Proves:* the sender's HTLC can be refunded after timeout when no settlement
  and no key compromise occurs (exists-trace).
- **`Distinct_Parties_Configuration`** — *Models:* a clean 3-hop topology.
  *Proves:* three channels among four distinct honest parties are openable with
  no compromise/update/close/cheat (exists-trace; non-vacuity of the routing
  setup).
- **`Ltk_Known_Implies_Compromised`** — *Models:* key handling + adversary
  knowledge. *Proves:* if the adversary knows a long-term key, that key was
  compromised (no key leaks "for free").
- **`Invoice_Released_Once`** — *Models:* preimage release. *Proves:* a receiver
  releases a given preimage at most once (replay/freshness).
- **`Invoice_Has_Secret_Preimage`** — *Models:* invoice creation. *Proves:* every
  invoice `h(x)` is backed by the receiver actually holding the secret `x`.
- **`Preimage_Secret_Until_Released`** — *Models:* preimage secrecy vs. adversary
  knowledge. *Proves:* the adversary cannot learn `x` before the receiver
  releases it (secrecy until reveal).
- **`HTLC_On_Opened_Channel`** — *Models:* HTLC placement. *Proves:* an HTLC can
  only be added on a previously opened channel.
- **`Settle_Requires_Receiver_Release`** — *Models:* settlement vs. fulfil.
  *Proves:* the sender can settle only after the receiver released the preimage.
- **`Forward1_Requires_Offer`**, **`Forward2_Requires_Forward1`**,
  **`Fulfill_Requires_Forward2`** — *Models:* the forwarding chain. *Proves:*
  each hop requires the previous hop to have happened **or** the relevant key to
  be compromised (causal ordering of the route).
- **`Forward1_Requires_Offer_Honest`**, **`Forward2_Requires_Forward1_Honest`**,
  **`Fulfill_Requires_Forward2_Honest`** — *Models:* same chain, honest world.
  *Proves:* with no key compromise, each hop *strictly* requires the previous one
  (the clean causal chain).
- **`Claim_Requires_Release`** — *Models:* intermediary claim vs. preimage.
  *Proves:* an intermediary claims upstream only after the preimage was released.
- **`Settle_Excludes_Sender_Refund`** — *Models:* settle vs. refund on the same
  hash. *Proves:* a settled sender HTLC can never also be refunded (no
  double-spend of an HTLC).
- **`Invoice_Authenticates_Settlement`** — *Models:* invoice signature.
  *Proves:* a settlement implies a genuine prior invoice from the receiver unless
  the receiver's key was compromised.
- **`Forged_Invoice_Requires_Key_Compromise`** — *Models:* forged settlement.
  *Proves:* a settlement *without* a real invoice is reachable **only** with
  receiver-key compromise (exists-trace; shows the bound above is tight).
- **`Loss_Requires_Inaction`** — *Models:* the forward/redeem/refund interplay.
  *Proves:* if a forwarder is redeemed downstream and refunded upstream, then it
  never claimed upstream (loss ⇒ a skipped claim).
- **`Refund_Requires_Timeout`** — *Models:* refunds. *Proves:* a refund can only
  follow a timeout (no refund without the deadline passing).
- **`Intermediary_Never_Loses_Under`** *(conditional on T2b)* — *Models:* an
  honest routing node forwarding a payment. *Proves:* if its outgoing HTLC is
  redeemed but its incoming HTLC is refunded, then its key was compromised — an
  honest, live intermediary never loses money. **(Core safety result.)**
- **`Payment_Atomicity_Under`** *(conditional on no compromise)* — *Models:* the
  two-forward route with downstream redemption. *Proves:* once the receiver
  fulfils the final HTLC, the sender's HTLC on the same hash cannot be refunded —
  the payment is **atomic** (all-or-nothing). **(Core safety result.)**
- **`Timeout_Race_Blocked`** *(with T2b active)* — *Models:* the early-timeout
  race. *Proves:* with the liveness restriction present, the race
  (incoming refunded before outgoing redeemed) is **impossible** — the "blocked"
  half of the two-sided certificate (see §4).

**Restrictions modelled:** `RedeemBeforeTimeout` (T1), `ForwardTimeGap` (T2),
`IntermediaryMustClaim` (T3), and `HonestPartiesActBeforeIncomingTimeout` (T2b,
the liveness assumption), plus structural ones (`OneOutcomePerHTLC`,
`OneTimeoutPerPtr`, `OneChannelPerPtr`, `Equality`, `Inequality`).

---

## 2. `Clock.spthy` — block-clock lifecycle & timing safety

**Modelled:** a block clock (`Clock_Tick` raises height and emits a persistent
`!BlockReached`), a **linear** channel token (close consumes it), and the HTLC
state machine carrying concrete CLTV deadlines `dIn`, `dMid`, `dOut`. Outcomes
are tagged `RedeemedAt`/`RefundedAt`/`WithinDeadline`/`PastDeadline` for timing
arithmetic.

- **`HTLC_Needs_Open_Channel`** — *Models:* HTLC placement over the clock.
  *Proves:* every `HTLCAdded` is preceded by a `ChannelOpen` (induction).
- **`No_HTLC_After_Close`** — *Models:* the linear channel token. *Proves:* no
  HTLC can be added after the channel is closed (the token is consumed by close;
  6044-step induction — the heaviest lemma).
- **`Claim_Window_Exists`** — *Models:* one hop's redeem and refund blocks.
  *Proves:* `bOut < bRef` — the downstream redeem happens strictly before the
  upstream refund, so the intermediary's claim window is non-empty.
- **`Transitive_Preimage_Before_Upstream_Deadline`** — *Models:* a two-hop
  staggered chain `dOut < dMid < dIn`. *Proves:* a preimage revealed at
  `bOut ≤ dOut` is revealed strictly before the upstream deadline `dIn`
  (end-to-end window propagation).
- **`Loss_Implies_Skipped_Claim`** — *Models:* forward + downstream redeem +
  upstream refund. *Proves:* such a loss implies the intermediary never claimed
  (loss is a pure liveness/skipped-claim residual).
- **`Outcome_Exclusive`** — *Models:* the two HTLC outcomes. *Proves:* redeem and
  refund are mutually exclusive for the same HTLC.
- **`Redeem_Reachable`** / **`Refund_Reachable`** — *Models:* the on-chain
  claim/timeout paths. *Proves:* both the redeem and the refund outcomes are
  reachable (exists-trace; non-vacuity).
- **`Honest_Flow_Possible`** — *Models:* forward + downstream redeem + upstream
  claim. *Proves:* the honest timing flow (redeem downstream, claim upstream) is
  reachable — confirms `Claim_Window_Exists` is non-vacuous.

Bulk run: **≈ 147 s, 9/9 verified, no OOM.**

---

## 3. `Cltv.spthy` — CLTV block arithmetic

**Modelled:** block heights as naturals, a hop registered as
`(ptrOut, ptrIn, d_out, d_in)` with `d_in = d_out + delta` and a positive delta,
and a preimage reveal at a reached block. No HTLC mechanics — pure arithmetic
that *justifies* T1–T3.

- **`CLTV_Gap_Is_Positive`** — *Models:* a registered hop. *Proves:*
  `d_out < d_in` — the outgoing deadline is strictly earlier (**justifies T2**).
- **`Claim_Window_Nonempty`** — *Models:* hop + preimage reveal at block `b`.
  *Proves:* `b < d_in` — the preimage appears before the incoming HTLC times out,
  so the intermediary has time to claim (**justifies T1+T2**).
- **`Staggered_Path_Safe`** — *Models:* a two-hop chain `d1 < d2 < d3` with a
  reveal at `b ≤ d1`. *Proves:* `b < d2 ∧ b < d3` — both intermediaries have
  non-empty claim windows (**justifies T3**; the assumption-free reason the
  cascade works).

---

## 4. `timeout.spthy` — early-timeout race (the attack T2b defends against)

**Modelled:** a *minimal* forwarding world — register a forward, let either
channel time out freely, refund after the incoming timeout, redeem the outgoing
at any time. **T2b is deliberately absent.**

- **`Early_Timeout_Race`** — *Models:* incoming timeout/refund racing the
  outgoing redeem. *Proves:* a concrete trace exists where the incoming channel
  times out and refunds *before* the outgoing HTLC is redeemed (`#k < #i`),
  making T3 inapplicable and the intermediary lose **with no key compromise**
  (exists-trace).

**Why separate:** restrictions are global. Witnessing the race needs a world
*without* T2b (`timeout.spthy`); proving it blocked needs T2b present
(`Timeout_Race_Blocked` in `multihop.spthy`). The pair is a **two-sided
certificate**: T2b is load-bearing (remove → attack returns) and sufficient
(add → attack gone). The race rules are kept commented-out in `multihop.spthy`
with a pointer here.

---

## 5. `value_cons.spthy` — value & fee conservation

**Modelled:** the routed payment with **nat-typed amounts** — receiver invoice
amount `%v`, sender lock `%vS`, per-hop forwarded amount `%vOut` and fee `%fee`,
each forwarder enforcing `Eq(%vIn, %vOut %+ %fee)` under signed offers. `%1` is
seeded so any nat amount is composable.

- **`Forwarding_Possible`** — *Models:* a single forward charging a fee.
  *Proves:* a forwarding-with-fee step is reachable — the forward rules are not
  dead code (exists-trace; non-vacuity).
- **`Fee_Conservation_Per_Hop`** *(no compromise)* — *Models:* one hop's amounts.
  *Proves:* `%vIn = %vOut %+ %fee` — money in equals money out plus the fee at
  every hop.
- **`Value_Conserved_End_To_End`** *(no compromise)* — *Models:* both hops.
  *Proves:* `%vS = %vMid %+ %fee1` and `%vMid = %vR %+ %fee2` — the sender's lock
  equals the receiver's amount plus all hop fees (stated as two pairwise
  equalities; see §6f).

*Scope:* this proves **amount conservation**, not economic rationality — fees are
adversarially chosen via `In(%fee)`; `fee > 0` is a game-theoretic assumption
outside symbolic verification.

---

## 6. What we tried first, why it failed, and how we changed it

**(a) One monolithic theory → OOM.** *First:* everything in `multihop.spthy`.
*Failed:* signing + nat induction + unbounded clock blow up together. *Fix:*
split into the five-theory package; each carries only the builtins it needs.

**(b) Reachability witnesses under the unbounded clock → OOM.** *First:* keep the
two-hop / timed-refund existence witnesses in `Clock.spthy`. *Failed:* the solver
unifies `!BlockReached(%d)` against infinitely many persistent block facts while
solving `<<` — `Killed`. A bounding `restriction` did **not** help (applied after
the case split is built). *Fix:* drop those two heavy witnesses; the windows are
still proved by `Claim_Window_Exists` and
`Transitive_Preimage_Before_Upstream_Deadline`. (A witness, if wanted, verifies
in <10 steps under a *finite* clock — sound for existence.)

**(c) Whole-file `--prove` → OOM on a laptop.** *First:* prove all lemmas in one
process. *Failed:* `Killed` (too much resident memory). *Fix:* prove one lemma
per invocation; after (b) the trimmed bulk run fits again.

**(d) `seqdfs` everywhere → hangs.** *First:* global `--stop-on-trace=seqdfs`.
*Failed:* it rescues `multihop`'s exists-traces but hangs the nat lemmas in
`Clock`/`Cltv`. *Fix:* `seqdfs` only for `multihop.spthy` and `timeout.spthy`.

**(e) Fresh nonces as amounts → vacuous lemmas.** *First:* amounts as `~x` with
`Eq(~a, ~b %+ ~c)`. *Failed:* fresh is not a nat subsort, so the equation never
holds — forward rules never fired and security lemmas were *vacuously* true.
*Fix:* nat-typed amounts (`%vIn`, `%fee` via `In`), seed `%1`.

**(f) Three-term AC sum → Tamarin 1.8 crash.** *First:* `vS = vR %+ fee1 %+ fee2`.
*Failed:* crash on a 3-term AC sum in guarded-formula form. *Fix:* two pairwise
equalities `vS = vMid %+ fee1`, `vMid = vR %+ fee2`.

**(g) `b ≤ d_out` → sort-inference warning.** *First:* `b << d_out %+ %1`.
*Failed:* sort inference can't resolve `d_out` as nat there. *Fix:* strict
`b << d_out`.

**(h) Vacuous balance lemma.** *First:* required `NewStateBuilt` and
`StateUpdate` at the *same* timestamp — they fire in different rules, so the
premise was unsatisfiable. *Fix:* `Update_Requires_Negotiation` instead.

**(i) Race in the main theory → safety lemmas falsify.** *First:* keep the
timeout-race rules in `multihop.spthy`. *Failed:* without T2b the safety lemmas
falsify. *Fix:* move the race to `timeout.spthy`; keep only `Timeout_Race_Blocked`
(with T2b) in `multihop.spthy`.

**(j) Encoding crash.** *Symptom:* `commitBuffer: invalid argument`. *Fix:* run
with `LANG=C.utf8 LC_ALL=C.utf8`.

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
