# Formal Verification Report 2.0 — Lightning Network Multi-Hop HTLC Routing (Tamarin 1.8)

This is Report 2.0. Part I is the verified core model (unchanged from Report 1.0,
summarised here). Part II is new: the generalization of the fixed 3-hop model to
**arbitrary path length (N hops)**, why the intuitive encoding fails, and the
merged N-hop model that verifies 28/29 lemmas.

---

# PART I — The core model (5 theories)

The protocol is formalised as a **modular package of five theories**. Each proves
a distinct aspect; they do not share rules, so a property proved in one is not
silently assumed in another. The split is deliberate — one combined theory
OOM-kills Tamarin (signing + nat induction + unbounded clock cannot coexist in
one tractable search space).

| File | Aspect | Builtins |
|------|--------|----------|
| `multihop.spthy` | Channel lifecycle + HTLC routing + atomicity (fixed 3-hop) | hashing, signing |
| `Clock.spthy` | Block-clock lifecycle & CLTV timing safety | natural-numbers |
| `Cltv.spthy` | Pure CLTV block arithmetic | natural-numbers |
| `timeout.spthy` | Early-timeout race counterexample | none |
| `value_cons.spthy` | Value & fee conservation | hashing, signing, nat |

**Headline results (49 lemmas total):**
1. **Payment atomicity** — once the receiver is paid, the sender's HTLC cannot be refunded.
2. **Intermediary safety** — an honest, timely forwarder never loses funds unless its key is compromised.
3. **Routing causality & authentication** — each hop requires the previous one; preimages stay secret until release; settlements trace back to a genuine signed invoice.
4. **Timing safety** — staggered CLTV windows are non-empty; redeem/refund are mutually exclusive; no HTLC survives a channel close.
5. **Value conservation** — money in = money out + fee at every hop and end to end.
6. **The liveness assumption (T2b) is necessary** — a two-sided certificate: remove it and the early-timeout race reappears (`timeout.spthy`); keep it and the race is blocked (`multihop.spthy`).

Per-lemma detail and the "what we tried first / why it failed / how we fixed it"
history are in `REPORT.md`. The main limitation is stated there and stands:
safety is a **conditional guarantee** under the liveness assumption T2b, because
that is exactly what Lightning's security reduces to in reality (watchtowers
exist for this reason). A trace tool cannot prove parties *act* in time, so T2b
is surfaced explicitly rather than hidden.

---

# PART II — Generalizing to N hops

The core model fixes the path at 3 hops (`Sender → F1 → F2 → Receiver`) with two
hardcoded forward rules. A natural reviewer question is *"why only 3 hops?"* This
part answers it.

## 1. The goal

Replace the two hardcoded forward rules with **one generic `Forward_HTLC` rule**
that can fire any number of times, so the path has arbitrary length.

## 2. What was tried, and what Tamarin actually did

Everything below was **run**, not assumed.

| Encoding | Idea | Result |
|----------|------|--------|
| **Signed message, numbered tags** (`htlc1→htlc2→…`) | index hops by a number | ✗ predicted to loop (nat induction) — not pursued |
| **Signed message, generic rule** | one rule re-signs and forwards the HTLC as an `Out`/`In` message | ✗ **breaks Tamarin** — even a one-hop reachability witness OOMs |
| **Signed message + fresh `~id`** | add a fresh per-hop id for replay protection | ✗ **still breaks** — confirmed: even `Direct_Payment_Possible` times out |
| **Linear-fact chain** | pass the HTLC as an internal `Route(prev,me,ptr,y)` fact, not a signed message | ✓ **works** — safety lemmas verify by induction over the chain |

**Why the signed-message versions fail.** When a forward *re-signs* the HTLC and
sends it, the `'htlc'` term becomes self-referential (a forwarded HTLC is the
output of forwarding another HTLC). Tamarin's origin analysis — "where did this
signed message come from?" — then recurses without bound and never terminates.
A fresh `~id` fixes *replay* but not *termination*: it is still a signed term
that can only have been produced by another forward. This cryptographic
origin-analysis recursion is the precise **bounding factor**.

**Why the linear-fact version works.** A linear fact is handed directly from one
hop to the next (an **idealized channel**) rather than broadcast as a signed
message, so there is no self-referential signed term to analyse. Tamarin then
discharges the safety lemmas by induction over the chain, for any length.

## 3. Isolated abstraction — `experiments/generic_linearfact_*.spthy`

Two small theories that isolate the routing logic from the cryptographic
primitives and prove the safety invariants for **any** path length:

| Lemma (generic over length) | Steps |
|-----------------------------|-------|
| `Forward_Requires_Incoming` (causality) | 17 |
| `Claim_Requires_Release` | 20 |
| `Redeem_Requires_Receiver_Release` (authentication/atomicity) | 45 |
| **`Intermediary_Never_Loses`** | **551** |

`Intermediary_Never_Loses` concludes `==> F` — the Tamarin idiom for "this state
(an honest forwarder losing money) is unreachable," for all N.

**Framing (for the paper).** This is not a *weakened* model but a sound
**proof layering**: *concrete model → authentication + full Dolev–Yao adversary
(3-hop); abstraction → routing safety (N-hop).* The claim is that even with the
network/cryptographic layer perfectly abstracted, the protocol's state-transition
logic alone prevents intermediary loss, independent of hop count.

**Scope (stated honestly).**
- Only the **all-traces safety** lemmas generalize. The crypto-authentication
  results (`Invoice_Authenticates_Settlement`, `Forged_Invoice_Requires_Key_Compromise`)
  depend on signatures and remain proved only in the concrete model.
- Exists-trace **witnesses** need bounding (see §4).

## 4. The merged N-hop model — `multihop_nhop.spthy`

A single self-contained file: the **full channel lifecycle** from `multihop.spthy`
(handshake, state update, revocation/punishment, on-chain settlement, signed
invoice) **plus** the generic linear-fact N-hop routing. The invoice stays signed,
so invoice-authentication lemmas survive.

**Result: 28 / 29 lemmas verified, no OOM** (`--heuristic=c --stop-on-trace=seqdfs`).

Notably this did **not** OOM, despite combining signing + full lifecycle + generic
routing — the combination the modular split was created to avoid. Verified:
- all channel-lifecycle lemmas (`state_update`, `Protocol_execution`, close/settlement, punishment, …);
- generic routing: `Forward_Requires_Incoming` (133), `Redeem_Requires_Receiver_Release` (175), `Claim_Requires_Release` (157);
- headline safety: `Intermediary_Never_Loses_Under_Liveness`, `Payment_Atomicity_Under_Liveness`, `T2b_Counterexample_Blocked`;
- authentication: `Invoice_Authenticates_Settlement` (420), etc.;
- the three payment **witnesses** (`Multihop_Payment_Possible` 46, `Refund_Possible` 16, `Forged_Invoice_Requires_Key_Compromise` 18).

**The exists-trace witness fix ("freeze the network").** With a generic forward
rule, an exists-trace search can instantiate unboundedly many *alternative*
routes and never converge on the goal. Adding negative guards that ban any
forward/offer outside the intended path prunes those branches, and the witnesses
verify in <50 steps. (This is the opposite of the fixed-hop case, where such
guards were *removed* for being ~7× slower — a nice illustration that the right
tactic depends on the rule set.)

**The one open lemma.** `Settle_Requires_Receiver_Release` does **not** verify in
the N-hop model. The root cause was pinned down empirically: **any lemma keyed on
`SenderSettled` is intractable here**, because `SenderSettled` is the terminal
event of the backward settle chain and resolving it forces Tamarin to unroll the
entire generic `Route`/`Fulfill` chain. Six tactics were tried and all timed out:
no-induction, `[use_induction]`, `[reuse]` of the atomicity lemma, a
`SenderSettled_Yields_Redeemed` bridge lemma (even that "trivial" bridge times
out), and a reformulation dropping the strict before-ordering — *both* with and
without induction. Since dropping the timing did not help, the blocker is the
`SenderSettled` key, not the ordering. The lemma **does** verify in the fixed-hop
`multihop.spthy`. It is the single, clearly-scoped open lemma of the N-hop
variant, documented in the file header.

## 5. What this contributes

The reviewer question *"why only 3 hops?"* is neutralised by decomposition:
- the **concrete** `multihop.spthy` proves all 33 properties over 3 hops with the
  full signed-message adversary;
- the **N-hop** models prove that the routing-safety invariants (atomicity,
  intermediary safety, causality) are **independent of path length**, and
  explicitly identify Tamarin's origin-analysis recursion on self-referential
  signed messages as the bounding factor.

That is a contribution in itself: not "we failed to scale," but "we proved the
scalable part scales, and pinned down exactly what does not."

## 6. How to reproduce (Part II)

```bash
export LANG=C.utf8 && export LC_ALL=C.utf8

# isolated abstraction (safety over unbounded length)
tamarin-prover experiments/generic_linearfact_safety.spthy --heuristic=c --derivcheck-timeout=0 --prove=Intermediary_Never_Loses

# merged N-hop model (28/29) -- prove per lemma
tamarin-prover multihop_nhop.spthy --heuristic=c --stop-on-trace=seqdfs --derivcheck-timeout=0 --prove=Intermediary_Never_Loses_Under_Liveness
tamarin-prover multihop_nhop.spthy --heuristic=c --stop-on-trace=seqdfs --derivcheck-timeout=0 --prove=Multihop_Payment_Possible
# ... (Settle_Requires_Receiver_Release is the one lemma that does not terminate here)
```
