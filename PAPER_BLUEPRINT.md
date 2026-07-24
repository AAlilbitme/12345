# Research Paper Blueprint

**Working title:** *Machine-Checked Multi-Hop HTLC Routing in Lightning: A Modular
Tamarin Model, Its Security Findings, and the Prover's Tractability Boundaries*

This blueprint maps each section to the concrete artifacts (theory files, lemmas,
figures) that support it, and flags what to claim, how strongly, and where the
honest caveats go. Everything below is backed by machine-checked results unless
marked *(pen-and-paper)* or *(reported timing)*.

---

## Abstract (write last)

One paragraph. Cover, in order: (1) what — a modular Tamarin 1.8 model of
Lightning multi-hop HTLC routing under a full Dolev–Yao adversary, five theories,
**81 machine-checked lemmas**; (2) safety re-established — payment atomicity,
intermediary safety, value conservation; (3) three findings that are more than
re-verification — the *linear single-spend discipline* (two bugs fixed the same
way), the machine-checked *wormhole* (reachable + fee-quantified), and *assumption
minimality* (T3 is load-bearing, shown by a counterexample); (4) the
*generalisation* — an N-hop abstraction with a refinement theorem transferring
safety to all path lengths; (5) the *methodological* spine — a map of exactly
which ingredient combinations make Tamarin stop scaling. Close on: every positive
and negative result was executed, not assumed.

---

## 1. Introduction

- **Problem.** Lightning routes payments off-chain by chaining HTLCs on one
  payment hash `y = H(x)`; the receiver reveals `x`, which propagates back,
  redeeming each hop. Getting the *safety* of this right (no honest intermediary
  loses money; a payment is atomic; value is conserved) is subtle because it mixes
  cryptography, mutable channel state, and time-locks.
- **Gap.** Prior formal treatments are either composable-crypto proofs
  (Kiayias–Litos, UC) at the channel layer, or informal at the routing layer.
  A *symbolic, fully machine-checked* routing model that also states its own
  tractability limits is missing.
- **Contributions (bulleted, 5):**
  1. A modular, fully machine-checked model — two-party lifecycle + multi-hop
     routing with fees — **81 lemmas over five theories**.
  2. A **linear single-spend discipline**: two independent soundness gaps
     (HTLC output; revoked commitment) were the *same* category error — a
     one-shot on-chain resource modeled as a persistent fact — and both are fixed
     by the same linear-token remedy. Proposed as a reusable modeling invariant.
  3. A machine-checked **wormhole** attack — reachable *and* quantified to the
     exact stolen fees — plus a griefing DoS and economic-soundness theorems.
  4. An empirical **assumption-minimality** result: removing the
     intermediary-claim restriction yields a concrete counterexample.
  5. A **tractability map**: the signing + natural-numbers + unbounded-clock
     OOM triple, signed-message N-hop routing, and reusable channels — the
     boundaries where automated search stops scaling.
- **Scope / non-goals.** Integrity and safety under Dolev–Yao with key
  compromise. *Not* privacy/unlinkability (needs onion routing + observational
  equivalence) — stated as an explicit exclusion.

---

## 2. Background

- Payment channels, commitment transactions, revocation/punishment.
- HTLCs and multi-hop routing; staggered CLTV timelocks (`3t/2t/t`).
- Tamarin essentials the reader needs: multiset-rewrite rules, **linear vs
  persistent facts** (this distinction *is* one of the paper's findings —
  introduce it here carefully), action facts, restrictions vs lemmas,
  all-traces vs exists-trace, `natural-numbers` builtin.
- Threat model: Dolev–Yao network + `Compromise_Ltk` key compromise.

---

## 3. The Model: a Modular Five-Theory Package

*(Figure: `fig_index` — the master map.)*

- **Why modular.** A single monolithic theory is intractable: signing +
  natural-number induction + an unbounded block clock together exhaust memory.
  **Tested, not assumed** — any two of the three are fine; only the full triple
  OOMs. The split guarantees no theory carries all three.
- **Table (from `verification_report.tex`):**

  | File | Aspect | Lemmas | Builtins |
  |------|--------|:-----:|----------|
  | `multihop.spthy` | lifecycle + routing + value/fees + atomicity + wormhole | 43 | hashing, signing, nat |
  | `multihop_nhop.spthy` | N-hop generalisation (generic linear-fact forward) | 25 | hashing, signing, nat |
  | `Clock.spthy` | block-clock lifecycle & staggered-CLTV claim windows | 9 | natural-numbers |
  | `cltv_blocks.spthy` | pure CLTV block arithmetic (delta positivity) | 3 | natural-numbers |
  | `timeout.spthy` | early-timeout race (liveness assumption removed) | 1 | — |
  | **Total** | | **81** | |

- **Relational vs concrete time.** `multihop`/`multihop_nhop` treat time
  relationally (event orderings). The three small theories add a *concrete block
  clock* so the CLTV windows are **derived, not assumed** — this is the payoff of
  isolating the clock from signing.

---

## 4. Core Results: the Concrete Model (`multihop.spthy`)

*(Figures: `fig_4party` routing/value/attack rail; `fig_channel` lifecycle rail.)*

Group the 43 lemmas (use the report's group table):

- **Channel lifecycle:** open, state-update, revocation/punishment, cooperative
  close. Headline: `No_Punishment_Without_Cheating` (punishment ⇒ prior cheat).
- **Invoice / preimage authentication:** `Invoice_Authenticates_Settlement`,
  `Preimage_Secret_Until_Released`, `Forged_Invoice_Requires_Key_Compromise`.
- **Lock/release causality:** `Forward1_Requires_Offer` (266 steps),
  `Forward2_Requires_Forward1` (274 steps), and honest variants — these are the
  **local per-hop authentication** lemmas that the soundness theorem (§7) leans on.
- **Atomicity & intermediary safety:** `Payment_Atomicity_Under_Liveness`,
  `Intermediary_Never_Loses_Under_Liveness`, `Timeout_Race_Blocked`.
- **Value / fees (as lemmas):** `EndToEnd_Value_Conservation`,
  `Fee_Conservation_Hop1/2`, `Fee_Strictly_Positive_Hop1/2`,
  `Receiver_Paid_Invoice_Amount`. *Key point for §6/§8:* here conservation is a
  **machine-checked property**, not just a rule guard.

---

## 5. Security Analysis

### 5.1 The linear single-spend discipline (the paper's strongest original point)
Frame as one principle with two instances (source: `revocation_finding.tex`):

- **Category error.** A one-shot on-chain resource (funding output, HTLC output,
  revoked commitment) modeled as a Tamarin **persistent fact** (`!`, never
  consumed) can license the same rule to fire unboundedly — i.e. the output is
  "spent" more than once.
- **Instance 1 — HTLC output (confirmed).** Forward rules were gated only by a
  public offer message; a replayed offer re-fired an honest forward and locked a
  *second* HTLC on the same output with an adversary-chosen amount
  (machine-checked reachable). Fix: a linear `Free(ptr)` slot, emitted once per
  channel open, consumed by each HTLC-add. "At most one HTLC per output" becomes
  **structural** — one fewer axiom than the earlier `OneHTLCPerPtr` restriction.
- **Instance 2 — revoked commitment (confirmed).** `Publish_Revoked_A/B` were
  gated only by persistent `!RevokedSecret`, so punishment could fire arbitrarily
  many times for one revoked state. Fix: `Revoke_Old_Secret` emits a linear
  `RevokedCommitmentUnspent` token, consumed by `Publish_Revoked`. Persistent
  *knowledge* of the secret is retained; only the one-shot *spend* is made linear.
- **Takeaway (the reusable contribution):** *"every one-shot on-chain output is a
  linear fact"* — a checkable modeling invariant for symbolic PCN analyses.
- **Honesty note:** monotonicity — adding an input fact preserves all-traces
  safety automatically but can break an exists-trace witness, so the theory was
  **fully re-run**, not argued by monotonicity. All 43 re-verify *(reported: 262 s,
  Tamarin 1.8)*. The `AUDIT_Double_Publish_Revoked` probe is expected falsified
  structurally; note its status honestly if you keep it.

### 5.2 Wormhole attack (reachable + quantified)
Source: `multihop.spthy` wormhole lemmas + `malavolta` citation.
- In the symbolic model the Dolev–Yao network *is* the colluders' side channel.
- `Wormhole_Fee_Theft_Reachable` (51 steps): payment settles, middle hop never
  redeemed, no intermediary earns a fee, **no key compromise**.
- `Wormhole_Steals_Exactly_The_Fees` (81 steps): theft is *exactly* the path fees
  `%f1 %+ %f2` — ties the attack to the value layer.
- Frame as: turning "we didn't model it" into "we machine-checked that the model
  exhibits it, and why." Note the known fix (AMHL/PTLCs) is out of scope.

### 5.3 Economic soundness & griefing
`EndToEnd_Value_Conservation`, `Fee_Strictly_Positive_*` (structural — the nat
sort has no `%0`, so a free forward is unreachable), and the reachable
`Honest_Intermediary_Refunds` griefing/capital-lock DoS.

### 5.4 Assumption minimality (T3 is load-bearing)
Remove the intermediary-claim restriction T3 and re-run:
`Intermediary_Never_Loses_Under_Liveness` is **falsified** with a concrete
*(reported: 59-step)* counterexample. T2b orders the timeouts but doesn't force
the node to *sweep* the incoming HTLC; that's exactly what T3 encodes. Hence the
three timing restrictions are minimal — none implied by the others.

---

## 6. Timing Safety with a Concrete Block Clock

*(Figure: `fig_timing`.)* Why a separate layer: to *derive* the CLTV windows the
relational model assumes.

- `cltv_blocks` — proves the delta is positive (`d_out << d_in`) and claim
  windows non-empty (`CLTV_Gap_Is_Positive`, `Claim_Window_Nonempty`,
  `Staggered_Path_Safe`).
- `Clock` — a live clock through the full forward lifecycle:
  `Claim_Window_Exists`, `Transitive_Preimage_Before_Upstream_Deadline`,
  `Loss_Implies_Skipped_Claim`, plus lifecycle safety + reachability.
- `timeout` — the counterexample: `Early_Timeout_Race` reachable once T2b is
  removed. **Two-sided certificate** with `Timeout_Race_Blocked` in
  `multihop.spthy`: the race is reachable without the assumption and blocked with
  it, so the assumption is necessary — not decoration.

---

## 7. Generalisation to N Hops + Soundness Theorem

Source: `multihop_nhop.spthy` + `nhop_soundness.tex`.

- **The two models.** Concrete `C` = `multihop.spthy` (signed HTLC over
  Dolev–Yao, fixed 3 hops). Abstract `A` = `multihop_nhop.spthy` (one generic
  `Forward_HTLC` over a linear `Route(prev,me,ptr,y)` *idealised channel*, any N).
  Same channel lifecycle, same safety lemmas; only the routing layer differs.
- **The trap (state it honestly).** Internalising the network as a trusted
  `Route` fact *removes* Dolev–Yao power — `A` has strictly fewer behaviours than
  `C`, so abstract safety does **not** automatically imply concrete safety. The
  gap is precisely the adversary's ability to forge/replay a forward.
- **How the gap is closed — locality.** The bridge is the local per-hop
  authentication lemma **AUTH**, machine-checked in `C`
  (`Forward1_Requires_Offer`, `Forward2_Requires_Forward1`): each quantifies over
  one adjacent pair and never over the path or N. *Boundary result:* a *generic*
  signed forward rule makes the `'htlc'` term self-referential and Tamarin's
  origin analysis fails to terminate at the sources stage — even a two-hop
  witness OOMs (`experiments/auth_local.spthy`, `auth_local_sources.spthy`). AUTH
  is provable *because*, taken per hop, it is bounded.
- **Refinement theorem *(pen-and-paper)*.** Projection `π` maps a concrete trace
  to an abstract one (keep Σ-actions, delete network/crypto events). Under AUTH,
  every concrete forward has a matching abstract step; by induction on forwarding
  steps, any Σ-violation in `C` projects to one in `A`. Hence safety proved on `A`
  for all N transfers to `C` for all N. State clearly which pieces are
  machine-checked (AUTH; all-N routing safety on `A`) and which is meta
  (simulation + induction) — Tamarin can't quantify over N or relate two theories.
- **N-hop caveats (be explicit):**
  - 25 active lemmas verify *(reported: ~103.5 s, natural-numbers)*.
  - Four `[use_induction]` causality lemmas
    (`Settle_Requires_Receiver_Release`, `Forward_Requires_Incoming`,
    `Claim_Requires_Release`, `Redeem_Requires_Receiver_Release`) are left
    commented as deliberate tractability boundaries.
  - **Fees are enforced structurally, not as lemmas.** The generic rule carries
    `Eq(%vIn, %vOut %+ %fee)` as a firing guard, so conservation holds by
    construction, but (a) a per-hop lemma would merely restate the guard
    (tautological), and (b) end-to-end conservation over N hops is a *sum of N
    fees* — not finitely statable in one Tamarin lemma, and induction over the
    generic chain hits the same non-termination as the four commented lemmas.
    This is the honest reason the fee lemmas live only in `multihop.spthy`.
  - **No wormhole in `A`** — by design: the idealised `Route` removes the
    network side channel the wormhole exploits. It's proved where it's meaningful
    (concrete `C`).

---

## 8. What Failed — the Tractability Boundaries (methodological core)

Present negative results as first-class (source: report §"What failed"):

- **The three-ingredient OOM.** signing + nat-induction + unbounded clock
  together exhaust the prover; any two are fine. This *is* the reason for the
  modular split.
- **Signed-message N-hop routing.** Origin analysis on the self-referential
  `'htlc'` term does not terminate — even for reachability, even with a fresh id.
- **A rejected restriction.** `OneRedeemPerPtr` falsified the honest witness
  `Multihop_Payment_Possible` (the two `Redeemed` events are two endpoints' views
  of one hop, not two spends). The correct guard was `OneHTLCPerPtr`, later made
  structural via `Free(ptr)`.
- **A caught false positive.** An exists-trace sharing only the payment *hash*
  appeared to show "value creation"; tightening to a single *linked* chain
  falsified it — invoice-hash reuse, not a soundness bug. Adversarial-verification
  discipline in action.
- **Reusable channels (boundary).** Stage 1 (single-HTLC-per-output via
  `Free(ptr)`) ships; Stage 2 (return `Free(ptr)` on resolution) is a clean
  boundary — safety lemmas verify with `--auto-sources` (~45 s each), but every
  exists-trace witness fails to converge (killed 500–700 s).

---

## 9. Related Work

- Poon–Dryja (Lightning), Maffei lecture notes (reference model).
- Malavolta et al. NDSS'19 (wormhole; AMHL fix).
- Kiayias–Litos CSF'20 (composable/UC treatment) — position our symbolic routing
  model as *complementary* at a layer their proof doesn't machine-check.
- Tamarin (Meier et al. CAV'13); Dolev–Yao.
- (Add: other symbolic PCN analyses; any Lightning HTLC formalizations.)

---

## 10. Conclusion

Restate the durable contribution: not "Lightning is safe" (expected), but
(1) the **linear single-spend discipline** as a reusable modeling invariant that
caught two real soundness gaps, (2) the **soundness layering** that transfers
routing safety to arbitrary N via a *local* authentication lemma, and (3) the
**tractability map** — what it takes to keep Tamarin scaling on a stateful,
time-locked, arithmetic protocol. Lightning is the validating case study;
the method is the contribution.

---

## Appendices / Artifacts

- **A. Full lemma index** — all 81 by file (see repo `NOTES.md` / lemma list).
- **B. Reproduction** — `python3 run.py` per theory; Tamarin 1.8 + Maude 3.1;
  per-lemma invocation with `--heuristic=c --stop-on-trace=seqdfs
  --derivcheck-timeout=0` (note: `--stop-on-trace` rescues heavy witnesses but
  hangs the nat-arithmetic theories, so it's applied per file).
- **C. Figures** — `fig_index`, `fig_4party`, `fig_channel`, `fig_timing`.

---

## Claim-strength cheat-sheet (keep yourself honest)

| Claim | Status |
|-------|--------|
| 81 lemmas verify | machine-checked (per-theory) |
| Both single-spend bugs reachable pre-fix / gone post-fix | machine-checked |
| Wormhole reachable + fee-exact | machine-checked |
| T3 load-bearing (counterexample) | machine-checked |
| AUTH is local per-hop | machine-checked in `C` |
| All-N routing safety on `A` | machine-checked on abstraction |
| Abstraction soundness (C ⇐ A for all N) | **pen-and-paper** refinement |
| Timings (262 s / 103.5 s / 59-step / etc.) | **reported** from local runs — re-measure before submission |
| `AUDIT_Double_Publish_Revoked` verdict | **pending** a terminating run |

## Open items before submission
- Re-run everything on one machine and record real timings + a stats table.
- Resolve the `AUDIT_Double_Publish_Revoked` verdict (run without `--stop-on-trace`).
- Fix the `Timeout_race_Blocked` vs `Timeout_Race_Blocked` capitalization mismatch.
- Decide whether the reusable-channel Stage-2 spike is an appendix or a forward-ref.
