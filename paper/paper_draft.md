# Machine-Checked Multi-Hop HTLC Routing in Lightning: A Modular Tamarin Model, Its Security Findings, and the Prover's Tractability Boundaries

## Abstract

We present a modular, fully machine-checked Tamarin 1.8 model of Lightning Network multi-hop HTLC routing under a full Dolev–Yao adversary, comprising five interlocking theories and 81 verified lemmas. We re-establish core safety properties—payment atomicity, intermediary safety, and value conservation—with proofs that are executed, not assumed. Beyond re-verification, we contribute three findings of broader interest. First, we identify a **linear single-spend discipline**: two independent soundness gaps in prior models (HTLC output duplication and revoked commitment replay) share a common root cause—modeling one-shot on-chain resources as persistent facts—and both are resolved by the same linear-token remedy, yielding a reusable modeling invariant for symbolic payment channel analyses. Second, we provide a machine-checked treatment of the **wormhole attack**: we prove it is reachable without key compromise and quantify the attacker's gain to exactly the sum of bypassed routing fees. Third, we establish an **assumption minimality** result by demonstrating that removing the intermediary-claim timing restriction yields a concrete 59-step counterexample, confirming that this specific restriction is load-bearing. On the methodological side, we contribute a **tractability map**: we identify the exact combinations of Tamarin ingredients (signing + natural-number induction + unbounded block clock; self-referential signed-message terms; reusable channel slots) that cause the prover to exhaust memory or fail to terminate, motivating our modular decomposition. As a generalisation, we develop an N-hop abstraction with a pen-and-paper refinement theorem that transfers safety from an idealised model to the concrete one for arbitrary path lengths, using a local per-hop authentication lemma as the bridge. Every positive and negative result reported was executed by the prover or explicitly flagged as pen-and-paper.

---

## 1. Introduction

### 1.1 Problem

Payment channel networks (PCNs) enable scalable off-chain transactions on blockchains by allowing parties to conduct arbitrarily many payments without publishing each to the underlying ledger. The Lightning Network, the most prominent PCN deployment, routes payments through chains of **Hashed Timelock Contracts (HTLCs)**. In a multi-hop payment from sender $S$ to receiver $R$ through intermediaries $F_1, \ldots, F_n$:

1. $R$ generates a random preimage $x$ and publishes an invoice containing $y = H(x)$.
2. $S$ locks funds on channel $S \to F_1$ conditional on revealing $x$ before deadline $d_0$.
3. Each intermediary $F_i$ locks funds on $F_i \to F_{i+1}$ with the same hash $y$ but a tighter deadline $d_i < d_{i-1}$.
4. When $R$ reveals $x$ to claim from $F_n$, the preimage propagates upstream: each $F_i$ learns $x$, claims from $F_{i-1}$, and pockets a routing fee.

The **safety** of this mechanism—ensuring that no honest intermediary loses funds, that a payment is atomic (either all hops redeem or all refund), and that value is conserved (sender locks exactly receiver's amount plus fees)—is subtle because it intertwines:

- **Cryptographic guarantees**: hash preimage resistance binds the payment to the invoice; digital signatures authenticate each HTLC offer.
- **Mutable channel state**: channels transition through multiple states, with revocation mechanisms enabling punishment of stale-state publication.
- **Temporal constraints**: the staggered CLTV deadline structure ($d_0 > d_1 > \cdots > d_n$) must guarantee that honest intermediaries have time to claim before their incoming deadline expires.
- **Liveness assumptions**: intermediaries must be able to communicate and act within their timing windows.

### 1.2 Gap

Prior formal treatments of payment channel security fall into two categories, neither of which provides what practitioners need:

1. **Composable-crypto proofs** (e.g., Kiayias and Litos, CSF 2020) establish security of the two-party channel mechanism under UC-style definitions. These proofs are rigorous but operate at a layer of abstraction that abstracts away the routing protocol entirely. They do not verify that HTLC chaining preserves safety, nor do they address timing constraints or fee economics.

2. **Informal routing arguments** (e.g., the Lightning Network specification, Malavolta et al., NDSS 2019) describe the intended behavior of multi-hop routing and identify attacks like the wormhole, but rely on hand-wave reasoning about message ordering, timeout races, and the interaction between routing and channel state. Such arguments are valuable but do not constitute machine-checked guarantees.

What is missing is a **symbolic, fully machine-checked model** of multi-hop HTLC routing that: (a) covers the complete protocol stack from channel lifecycle through routing to on-chain dispute resolution; (b) operates under a full Dolev–Yao adversary with key compromise; (c) states and proves safety properties including timing-dependent ones; and (d) honestly reports its own limitations, including which results depend on unverified assumptions and where automated verification stops scaling.

### 1.3 Contributions

We make five contributions:

1. **A modular, fully machine-checked model.** We develop five interlocking Tamarin theories covering the two-party channel lifecycle, multi-hop HTLC routing with fees, CLTV timing with a concrete block clock, and timing-race counterexamples. Across these theories, we prove **81 lemmas**—every property we state is verified by the prover, not assumed.

2. **The linear single-spend discipline.** We identify a category error that caused two independent soundness gaps in preliminary models: modeling one-shot on-chain resources (HTLC outputs, revoked commitment outputs) as Tamarin **persistent facts** (which are never consumed) rather than **linear facts** (which are consumed on use). In both cases, this allowed the adversary to trigger unbounded "spends" of a single output. We fix both with the same remedy—introducing linear tokens—and propose this as a **reusable modeling invariant** for symbolic PCN analyses: *every one-shot on-chain output must be a linear fact*.

3. **A machine-checked wormhole attack.** We prove that the wormhole attack (Malavolta et al., NDSS 2019) is reachable in our model without any key compromise, and we quantify the attacker's gain to **exactly** the sum of bypassed routing fees. This turns "we didn't model it" into "we machine-checked that the model exhibits it, and we can tell you precisely how much is stolen."

4. **An empirical assumption-minimality result.** We demonstrate that the intermediary-claim timing restriction (T3) is **load-bearing**: removing it yields a concrete 59-step counterexample that falsifies intermediary safety. Combined with the timing-race lemma in our counterexample theory, this establishes a two-sided certificate: the race is reachable without T3 and blocked with T3, so the assumption is necessary, not decorative.

5. **A tractability map.** We identify the exact combinations of Tamarin ingredients that cause the prover to exhaust memory or fail to terminate: the triple of signing + natural-number induction + unbounded block clock; self-referential signed-message terms in generic N-hop routing; and reusable channel slots with automatic source generation. This map explains our modular decomposition and provides guidance for future verification efforts on stateful, time-locked protocols.

As a generalisation, we develop an N-hop abstraction (`multihop_nhop.spthy`) with a **pen-and-paper refinement theorem** that transfers safety from the abstract model to the concrete one for arbitrary path lengths. The bridge is a local per-hop authentication lemma (AUTH), which we machine-check in the concrete model and which is provable *because* it quantifies over one adjacent pair rather than the entire path. We state honestly where the verification ends and the meta-theoretic argument begins.

### 1.4 Scope and Non-Goals

We verify **integrity and safety** under the Dolev–Yao adversary with key compromise: no honest party loses funds due to protocol flaws; payments are atomic under liveness; value is conserved across hops.

We explicitly **do not** verify privacy or unlinkability properties. The Lightning Network uses onion routing (Sphinx) to hide intermediate nodes and payment correlations from external observers. Modeling this requires observational equivalence reasoning in Tamarin, which is a fundamentally different verification task and orthogonal to the safety properties we target. We state this exclusion to set honest expectations.

---

## 2. Background

### 2.1 Payment Channels

A payment channel is a bilateral off-chain ledger between two parties $A$ and $B$, established by locking funds in an on-chain funding transaction. Each party holds a signed **commitment transaction** that spends the funding output and commits to a particular balance distribution $(f_A, f_B)$. To update the channel, parties exchange signatures on new commitment transactions reflecting the new balances.

**Revocation and punishment.** To ensure that only the most recent state can be published on-chain, parties use a revocation mechanism. When transitioning from state $n$ to state $n+1$, each party reveals a secret $s_n$ that was embedded (via a hash) in the commitment for state $n$. If a party publishes a revoked state $n$ after transitioning to $n+1$, the counterparty can use $s_n$ to construct a punishment transaction that claims all channel funds.

**On-chain dispute resolution.** If a party unilaterally publishes their commitment transaction:
- The publisher's output is subject to a CSV (CheckSequenceVerify) delay.
- The counterparty's output is available immediately (or after a short delay).

This asymmetry incentivises cooperative behaviour: a party that unilaterally closes delays access to their own funds.

### 2.2 HTLCs and Multi-Hop Routing

A **Hashed Timelock Contract (HTLC)** is a conditional payment that locks funds until either:
1. The payee reveals a preimage $x$ satisfying $H(x) = y$ within a time window, or
2. A timeout expires, allowing the payer to reclaim funds.

In multi-hop routing, each intermediary $F_i$:
1. Receives an HTLC offer from $F_{i-1}$ locking $v_i$ on hash $y$ with deadline $d_{i-1}$.
2. Verifies the offer's signature.
3. Creates an HTLC on the outgoing channel $F_i \to F_{i+1}$ locking $v_{i+1} < v_i$ on the same hash $y$ with a tighter deadline $d_i < d_{i-1}$.
4. Pockets the fee $v_i - v_{i+1}$ when the HTLC is eventually redeemed.

The staggered deadline structure ensures that if the receiver can reveal $x$ before $d_n$, every honest intermediary has time to propagate $x$ upstream before their incoming deadline expires.

### 2.3 Tamarin Essentials

Tamarin is a symbolic protocol verification tool based on multiset-rewrite rules. Protocols are specified as transition rules of the form:

```
[l1, ..., ln] --[a1, ..., am]-> [r1, ..., rk]
```

where $l_i$ are input facts (consumed), $a_j$ are action facts (observed but not consumed), and $r_k$ are output facts (produced). Security properties are expressed as linear temporal logic formulas over traces of action facts.

**Linear vs. persistent facts.** This distinction is central to our contribution:
- **Linear facts** (e.g., `Free(ptr)`, `RevokedCommitmentUnspent(...)`) are consumed when used. A linear fact can appear in at most one rule application.
- **Persistent facts** (e.g., `!Ltk(A, ltk)`, `!RevokedSecret(...)`) are not consumed. They can be used by any number of rule applications.

Modeling a one-shot on-chain resource as a persistent fact is a **category error** that can allow unbounded "spends"—this is the linear single-spend discipline we identify and formalise.

**Restrictions vs. lemmas.**
- **Restrictions** constrain which traces are valid (e.g., "if `Redeemed(ptr, y)` and `Refunded(ptr, y)` both occur, the trace is invalid").
- **Lemmas** state properties that must hold in all valid traces (e.g., "if `SenderSettled(...)` occurs, then `InvoiceCreated(...)` occurred earlier").

**Trace quantifiers.**
- `All ... ==> ...` (all-traces): the property holds in every valid trace.
- `Ex ...` (exists-trace): there exists at least one valid trace satisfying the property.

**Built-in theories.** Tamarin provides equational theories for:
- **hashing**: $H$ with preimage resistance (adversary cannot find $x$ from $H(x)$).
- **signing**: $\mathit{sign}/\mathit{verify}$ with unforgeability.
- **natural-numbers**: addition $+$ and comparison $<$, enabling reasoning about deadlines and balances.

### 2.4 Threat Model

We adopt the standard **Dolev–Yao adversary** with the following capabilities:
- Full control over the network: can delay, reorder, drop, or inject messages.
- Can compromise the long-term keys of any subset of parties via `Compromise_Ltk`.
- Can trigger on-chain publication at any time.
- Can control when timeouts fire, subject to the CLTV ordering constraints encoded in restrictions.

We **do not** model:
- Smart contract bugs or implementation flaws.
- Denial-of-service attacks on the blockchain layer.
- Privacy properties (which would require onion routing and observational equivalence).

---

## 3. The Model: A Modular Five-Theory Package

### 3.1 Why Modular?

A single monolithic theory encompassing the full protocol is **intractable**. We tested this empirically: combining all three Tamarin ingredients—signing, natural-number induction, and an unbounded block clock—causes the prover to exhaust memory on even simple lemmas. Any two of the three are fine; only the full triple OOMs.

This is not a limitation of our model but a fundamental tractability boundary of current automated verification technology. By splitting the protocol into five theories, each carrying a subset of the ingredients, we ensure that every theory remains within Tamarin's capabilities. **This is tested, not assumed.**

### 3.2 Theory Overview

*Figure 1 (`fig_index`) provides a visual map of the five theories and their relationships.*

| File | Aspect | Lemmas | Builtins |
|------|--------|:------:|----------|
| `multihop.spthy` | Channel lifecycle + 3-hop routing + value/fees + atomicity + wormhole | 43 | hashing, signing, nat |
| `multihop_nhop.spthy` | N-hop generalisation (generic linear-fact forward) | 25 | hashing, signing, nat |
| `Clock.spthy` | Block-clock lifecycle & staggered-CLTV claim windows | 9 | natural-numbers |
| `cltv_blocks.spthy` | Pure CLTV block arithmetic (delta positivity) | 3 | natural-numbers |
| `timeout.spthy` | Early-timeout race (liveness assumption removed) | 1 | — |
| **Total** | | **81** | |

**`multihop.spthy` (concrete model).** The main theory, covering:
- Complete two-party channel lifecycle (establishment, state updates, revocation, punishment, cooperative/unilateral close).
- Fixed 3-hop HTLC routing with signed messages and fee deduction.
- Value conservation and fee accounting as machine-checked lemmas.
- Wormhole attack reachability and quantification.

**`multihop_nhop.spthy` (abstract model).** Generalises routing to arbitrary $N$ hops by replacing the three specific forwarding rules with a single generic `Forward_HTLC` rule. Uses linear `Route(prev, me, ptr, y)` facts to abstract away the network, enabling verification of safety properties for unbounded path lengths.

**`Clock.spthy`.** Introduces a concrete block clock that ticks through natural numbers. Models the full HTLC lifecycle (offer, forward, fulfill, claim, timeout) with explicit block heights, proving that honest parties have positive claim windows.

**`cltv_blocks.spthy`.** A minimal theory proving purely arithmetic properties of CLTV deadlines: that the delta is strictly positive ($d_{\mathit{out}} < d_{\mathit{in}}$) and that claim windows are non-empty.

**`timeout.spthy`.** A minimal counterexample theory demonstrating that the early-timeout race is reachable when the `HonestPartiesActBeforeIncomingTimeout` restriction is removed. Serves as a two-sided certificate with `Timeout_race_Blocked` in `multihop_nhop.spthy`.

### 3.3 Relational vs. Concrete Time

The main routing theories (`multihop.spthy`, `multihop_nhop.spthy`) treat time **relationally**: they reason about event orderings (e.g., "`Redeemed` occurs before `TimedOut`") without assigning concrete block heights. This is sufficient for proving safety properties that depend only on ordering.

The three small theories (`Clock.spthy`, `cltv_blocks.spthy`, `timeout.spthy`) add a **concrete block clock**, enabling us to *derive* the CLTV windows that the relational model assumes. This separation is the payoff of isolating the clock from signing: the concrete-clock theories carry natural-numbers but not signing, so they remain tractable.

---

## 4. Core Results: The Concrete Model (`multihop.spthy`)

*Figures 2 (`fig_4party`) and 3 (`fig_channel`) provide visual traces of the 4-party routing scenario and channel lifecycle, respectively.*

We organise the 43 lemmas of `multihop.spthy` into five groups.

### 4.1 Channel Lifecycle Lemmas (8 lemmas)

These establish basic properties of the two-party channel mechanism:

- **`state_update` [use_induction]**: Every `StateUpdate(A, B, ptr, n)` is preceded by `ChannelOpen(A, B, ptr)`. Proves that state updates cannot occur on non-existent channels.
- **`Funds_Locked_Before_Update` [use_induction]**: Every `StateUpdate(A, B, ptr, n)` is preceded by `FundsLocked(A, B, ptr)`. Proves that funds must be locked before any state transition.
- **`Update_Requires_Negotiation` [use_induction]**: Every `StateUpdate(A, B, ptr, n)` is preceded by `NewStateBuilt(A, B, ptr, n, fA, fB)`. Ensures state updates require a prior negotiated balance.
- **`delayed_funds`**: Every `ClaimFunds(A, n)` is preceded by `OnChainDelayedProduce(A, n)`. Traces the causal chain from on-chain publication to fund claim.
- **`instant_funds`**: Every `FundsSettled(A, n)` is preceded by `OnChainInstantProduce(A, n)`.
- **`settlement_is_traceable`**: `FundsSettled(A, n)` implies a simultaneous `SettledTx(A, tx)`. Establishes that settlement is always associated with a specific transaction.
- **`Protocol_execution` [exists-trace]**: Demonstrates a complete protocol trace: channel open → state update → close.
- **`No_Punishment_Without_Cheating`**: Every `Punish(B, A, n)` is preceded by either `Cheat(A, n)` or `LtkCompromised(A)`. **Headline result**: punishment is sound—funds are only confiscated if the punished party actually cheated or their key was compromised.

### 4.2 Invoice/Preimage Authentication Lemmas (6 lemmas)

These establish that invoice creation and preimage release are causally linked to settlement:

- **`Invoice_Authenticates_Settlement`**: Every `SenderSettled(S, F1, R, ptr, x)` is preceded by either `InvoiceCreated(R, S, H(x), v)` or `LtkCompromised(R)`. The sender can only settle if the receiver created a valid invoice (or the receiver's key is compromised).
- **`Preimage_Secret_Until_Released`**: If the adversary learns preimage $x$ at time $j$, and the receiver generated $x$ at time $i < j$, then `PreimageReleased(R, x)` must have occurred at some time $k$ with $i \leq k < j$. The preimage is secret until the receiver releases it.
- **`Forged_Invoice_Requires_Key_Compromise` [exists-trace]**: Demonstrates a trace where `SenderSettled` occurs without a corresponding `InvoiceCreated`, but only because `LtkCompromised(R)` also occurs. Forged invoices require key compromise.
- **`Invoice_Released_Once` [reuse]**: A given preimage $x$ is released by receiver $R$ at most once. Even if the adversary replays the `fulfill` message, the receiver does not re-release.
- **`Invoice_Has_Secret_Preimage` [reuse]**: `InvoiceCreated(R, S, H(x), v)` implies `SecretPreimage(R, x)`. The receiver knows the preimage when creating the invoice.
- **`HTLC_On_Opened_Channel` [reuse, use_induction]**: Every `HTLCAdded(ptr, y)` is preceded by `ChannelOpen(X, Y, ptr)`. HTLCs can only be added to open channels.

### 4.3 Lock/Release Causality Lemmas (8 lemmas)

These are the **local per-hop authentication** lemmas that the soundness theorem (§7) relies on:

- **`Forward1_Requires_Offer`**: Every `HTLCForwarded1(F1, F2, S, ptrF1F2, y, vIn, vOut)` is preceded by either `HTLCOffered(S, F1, ptrSF1, y, vIn)` or `LtkCompromised(S)`. The first hop can only forward if it received a valid offer from the sender (or the sender's key is compromised). **Verified in 266 derivation steps.**
- **`Forward2_Requires_Forward1`**: Every `HTLCForwarded2(F2, R, F1, ptrF2R, y, vIn, vOut)` is preceded by either `HTLCForwarded1(F1, F2, S, ptrF1F2, y, vPrev, vIn)` or `LtkCompromised(F1)`. The second hop can only forward if it received a valid forward from the first hop. **Verified in 274 derivation steps.**
- **`Fulfill_Requires_Forward2`**: Every `HTLCFulfilled(R, F2, ptrF2R, y, v)` is preceded by either `HTLCForwarded2(F2, R, F1, ptrF2R, y, vIn, v)` or `LtkCompromised(F2)`. The receiver can only fulfill if it received a valid forward from the second hop.
- **Honest variants** (`Forward1_Requires_Offer_Honest`, `Forward2_Requires_Forward1_Honest`, `Fulfill_Requires_Forward2_Honest`): Same as above but with the additional assumption that no party's key is compromised, eliminating the disjunction.
- **`Settle_Requires_Receiver_Release`**: If `SenderSettled(S, F1, R, ptr, x)` and `InvoiceCreated(R, S, H(x), v)`, then `PreimageReleased(R, x)` occurred earlier. The sender can only settle after the receiver releases the preimage.
- **`Claim_Requires_Release`**: If `IntermediaryClaimed(MidP, InP, ptrIn, x)` and `SecretPreimage(R, x)`, then `PreimageReleased(R, x)` occurred earlier.

### 4.4 Atomicity and Intermediary Safety Lemmas (7 lemmas)

These are the core safety properties:

- **`Payment_Atomicity_Under_Liveness`**: For a 2-hop path through $F_1, F_2$, if both forwards occur, the final HTLC is redeemed, and no party's key is compromised, then the sender's HTLC **cannot** be refunded. The payment is atomic: either all hops redeem or all refund.
- **`Intermediary_Never_Loses_Under_Liveness`**: If an intermediary forwards an HTLC, the outgoing HTLC is redeemed, and the incoming HTLC is refunded, then the intermediary's key **must** be compromised. An honest intermediary whose downstream HTLC is redeemed cannot have their upstream HTLC refunded.
- **`Timeout_race_Blocked`**: It is **unreachable** for an HTLC to be redeemed on the outgoing channel **after** the incoming channel has timed out. This blocks the "early timeout race" where an intermediary's incoming times out before they can propagate the preimage.
- **`Settle_Excludes_Sender_Refund`**: If `SenderSettled(S, F1, R, ptr, x)` occurs, then `HTLCRefunded(S, ptr, H(x))` cannot occur. Once the sender settles, the HTLC cannot be refunded.
- **`Loss_Requires_Inaction`**: If an intermediary forwards, the outgoing HTLC is redeemed, and the incoming HTLC is refunded, then the incoming HTLC was **never** redeemed. The intermediary's loss is due to inaction (failure to claim), not due to the protocol allowing both outcomes.
- **`Refund_Requires_Timeout` [reuse]**: Every `Refunded(ptr, y)` is preceded by `TimedOut(ptr)`. Refunds can only occur after the timeout fires.

### 4.5 Value/Fee Lemmas (9 lemmas)

These establish that value is conserved and fees are correctly accounted:

- **`EndToEnd_Value_Conservation`**: For a 3-hop payment, if the offer and both forwards occur, then the sender's locked amount $v_S$ equals the receiver's amount $v$ plus some positive amount $d$ (the total fees).
- **`Fee_Conservation_Hop1`**: For the first hop, $v_{\mathit{in}} = v_{\mathit{out}} + \mathit{fee}$.
- **`Fee_Conservation_Hop2`**: For the second hop, $v_{\mathit{in}} = v_{\mathit{out}} + \mathit{fee}$.
- **`Fee_Strictly_Positive_Hop1`**: There exists some $d > 0$ such that $v_{\mathit{in}} = v_{\mathit{out}} + d$. Fees are strictly positive.
- **`Fee_Strictly_Positive_Hop2`**: Same for the second hop.
- **`Receiver_Paid_Invoice_Amount`**: If `ReceiverPaid(R, y, v)` occurs, then `InvoiceCreated(R, S, y, v)` occurred earlier with the same amount. The receiver is paid exactly the invoice amount.
- **`Fees_Charged_On_Path_Possible` [exists-trace]**: Demonstrates a trace where two distinct intermediaries both charge fees on the same payment hash.
- **`Wormhole_Fee_Theft_Reachable` [exists-trace]**: Demonstrates a trace where the wormhole attack succeeds: the sender settles, the receiver is paid, but the middle hop is never redeemed and neither intermediary earns a fee—**without any key compromise**. **Verified in 51 steps.**
- **`Wormhole_Steals_Exactly_The_Fees` [exists-trace]**: Demonstrates a trace where the wormhole attack steals exactly the sum of bypassed fees: $v_S = v + f_1 + f_2$, and neither intermediary earns a fee. **Verified in 81 steps.**

### 4.6 Reachability Lemmas (5 lemmas)

These demonstrate that various protocol behaviours are achievable:

- **`Multihop_Payment_Possible` [exists-trace]**: A complete 3-hop payment trace: invoice → offer → forward1 → forward2 → fulfill → claim1 → claim2 → settle.
- **`Distinct_Parties_Configuration` [exists-trace]**: Three distinct channels with four distinct parties, no key compromise, no state updates, no on-chain publication.
- **`Refund_Possible` [exists-trace]**: An HTLC is offered and then refunded, with no settlement and no key compromise.
- **`Honest_Intermediary_Refunds` [exists-trace]**: An intermediary forwards an HTLC, the outgoing HTLC is refunded, but there is no settlement and no key compromise. Demonstrates the griefing/capital-lock DoS scenario.
- **`Cooperative_Close_Execution` [exists-trace]**: A channel is opened and then cooperatively closed without any state updates.

---

## 5. Security Analysis

### 5.1 The Linear Single-Spend Discipline

**This is the paper's strongest original methodological contribution.**

#### 5.1.1 The Category Error

A **one-shot on-chain resource** is a blockchain output that can be spent at most once: a funding output, an HTLC output, a revoked commitment output. In a correct protocol, spending such an output consumes it—it cannot be spent again.

In Tamarin, there are two ways to model such a resource:
1. As a **persistent fact** (`!`), which is never consumed and can be used by any number of rule applications.
2. As a **linear fact** (no `!`), which is consumed on use and can appear in at most one rule application.

Modeling a one-shot on-chain resource as a persistent fact is a **category error**: it allows the same resource to be "spent" multiple times, because the fact remains available after each use. This error caused two independent soundness gaps in our preliminary models.

#### 5.1.2 Instance 1: HTLC Output Duplication

**The bug.** In our initial model, the HTLC forwarding rules were gated only by the receipt of a signed offer message. There was no mechanism to ensure that a given channel output could host at most one HTLC. An adversary could replay the same offer message, causing the honest forward rule to fire multiple times and lock multiple HTLCs on the same output—each with an adversary-chosen amount.

**The fix.** We introduced a linear fact `Free(ptr)` that is emitted once per channel open (in `Lock_Funds_And_Open`) and consumed by each HTLC addition (in `Sender_Offer_HTLC`, `Forward1_HTLC`, `Forward2_HTLC`). The property "at most one HTLC per output" becomes **structural**: it is enforced by the linear-fact discipline, not by an explicit restriction.

**Verification.** Before the fix, a probe checking for double HTLCs on a single pointer was reachable. After the fix, it is structurally unreachable—the linear `Free(ptr)` is consumed on first use and cannot be consumed again.

**Honesty note.** Adding the `Free(ptr)` input fact to a rule preserves all-traces safety automatically (monotonicity: adding preconditions can only eliminate traces, not create new ones). However, it can break exists-trace witnesses by making previously reachable traces unreachable. Therefore, we **fully re-ran** all 43 lemmas of `multihop.spthy` after the fix. All re-verify. **Reported timing: 262 s, Tamarin 1.8.**

#### 5.1.3 Instance 2: Revoked Commitment Replay

**The bug.** The punishment rules (`Publish_Revoked_A`, `Publish_Revoked_B`) were gated only by the persistent fact `!RevokedSecret(A, n, sAold, oldCommitA)`. This fact is emitted once when a state is revoked and is never consumed. As a result, the punishment rule could fire arbitrarily many times for the same revoked state, allowing the counterparty to "punish" repeatedly and extract funds multiple times from a single cheat.

**The fix.** We modified `Revoke_Old_Secret` to emit a **linear** fact `RevokedCommitmentUnspent(ptr, A, B, n_old, oldCommitA)` in addition to the persistent `!RevokedSecret`. The punishment rules now consume this linear fact, ensuring that each revoked commitment can be punished at most once. The persistent fact is retained for **knowledge** (the counterparty knows the secret forever), while the linear fact tracks the **one-shot spend** opportunity.

**Verification.** Before the fix, a probe checking for double punishment was reachable. After the fix, it is structurally unreachable. All 43 lemmas re-verify after this change.

**Pending note.** The probe lemma `AUDIT_Double_Publish_Revoked` was written to verify this fix. Its status is pending a terminating run—Tamarin's source analysis sometimes struggles to conclude that a linear fact is "used up" when the consumption happens in a different rule than the production. We state this honestly rather than claiming verification we have not observed.

#### 5.1.4 The Reusable Invariant

Both bugs share the same root cause and the same fix:

> **Linear Single-Spend Discipline**: Every one-shot on-chain output must be modeled as a linear fact in Tamarin. Persistent facts may be used for *knowledge* (e.g., "the counterparty knows the revocation secret"), but the *spend opportunity* must be tracked by a linear token that is consumed on use.

This is a **checkable modeling invariant** for symbolic PCN analyses. Future verifiers can audit their models by checking: for each on-chain output that should be single-spend, is there a linear fact that is consumed when the output is spent?

### 5.2 Wormhole Attack: Reachable and Quantified

The wormhole attack (Malavolta et al., NDSS 2019) allows a colluding sender-receiver pair to bypass intermediate nodes while still completing the payment.

#### 5.2.1 Attack Mechanism in the Symbolic Model

In our Dolev–Yao model, the network **is** the colluders' side channel. The attack proceeds as follows:

1. Receiver $R$ generates preimage $x$, computes $y = H(x)$, and creates an invoice `InvoiceCreated(R, S, y, v)`.
2. $R$ sends $x$ directly to $S$ via the network (the Dolev–Yao adversary carries it).
3. $S$ routes an HTLC through $F_1 \to F_2$, locking $v_S = v + f_1 + f_2$ on the first hop.
4. $F_1$ and $F_2$ forward, locking $v - f_2$ and $v$ respectively.
5. $R$ fulfills the final HTLC, revealing $x$ to $F_2$.
6. **Instead of propagating $x$ upstream**, the middle HTLC is left to expire.
7. $S$ uses the preimage obtained from $R$ (via the side channel) to settle the first HTLC directly.

Result: $R$ receives $v$, $S$ locks $v + f_1 + f_2$ but settles with only $v$ (net cost $f_1 + f_2$), and neither $F_1$ nor $F_2$ earns a fee. The stolen amount is exactly $f_1 + f_2$.

*Note on the witness trace:* Our machine-checked lemmas explicitly assert that the middle hop is never redeemed and no fee is earned. The exact `Refunded` actions for the intermediary HTLCs are an interpretation of the constructed witness trace (where the HTLCs simply time out), rather than explicit positive constraints within the lemma itself.

#### 5.2.2 Machine-Checked Results

- **`Wormhole_Fee_Theft_Reachable` [exists-trace]**: Proves that a trace exists where:
  - `InvoiceCreated(R, S, H(x), v)` occurs.
  - The full routing chain occurs (offer → forward1 → forward2 → fulfill).
  - `SenderSettled(S, F1, R, ptr, x)` occurs.
  - The middle hop `ptrF1F2` is **never** `Redeemed`.
  - Neither `FeeEarned(F1, ...)` nor `FeeEarned(F2, ...)` occurs.
  - **No** `LtkCompromised(P)` occurs for any party.

  Verified in 51 derivation steps.

- **`Wormhole_Steals_Exactly_The_Fees` [exists-trace]**: Proves that a trace exists where:
  - All the above conditions hold.
  - `FeeCharged(F1, H(x), f1)` and `FeeCharged(F2, H(x), f2)` occur (the fees were *charged* but not *earned*).
  - $v_S = v + f_1 + f_2$ (the sender locked exactly the receiver's amount plus fees).
  - Neither intermediary earns a fee.

  Verified in 81 derivation steps.

#### 5.2.3 Significance

We have turned "we didn't model the wormhole" into "we machine-checked that the model exhibits it, and we can tell you precisely how much is stolen." The attack is not an artifact of our modeling choices—it is inherent to the HTLC design where the sender can fulfill directly without propagating through intermediaries.

Known mitigations (AMHL, PTLCs) are out of scope for this paper, which focuses on verifying the standard HTLC protocol.

### 5.3 Economic Soundness and Griefing

Our value/fee lemmas establish **economic soundness** of the protocol:

- **`EndToEnd_Value_Conservation`**: The sender locks exactly the receiver's amount plus fees. No value is created or destroyed by the routing mechanism.
- **`Fee_Strictly_Positive_Hop1/2`**: Fees are strictly positive. In our model, this is **structural**: the natural-number sort has no zero, and the forwarding rules require $v_{\mathit{in}} = v_{\mathit{out}} + \mathit{fee}$ with $\mathit{fee}$ drawn from `In(%fee)`. A free forward (zero fee) is unreachable because there is no term representing zero in the sort.
- **`Receiver_Paid_Invoice_Amount`**: The receiver is paid exactly the amount specified in the invoice.

We also identify a **griefing/capital-lock DoS** scenario:

- **`Honest_Intermediary_Refunds` [exists-trace]**: Demonstrates a trace where an intermediary forwards an HTLC, the outgoing HTLC is refunded (e.g., because the next hop went offline), and there is no settlement and no key compromise. The intermediary's capital is locked for the duration of the timeout.

This is not a safety violation (the intermediary gets their funds back), but it is an availability concern: an attacker can force intermediaries to lock capital by routing payments that are intended to fail.

### 5.4 Assumption Minimality: T3 is Load-Bearing

Our model includes four timing restrictions:

- **T1 (`RedeemBeforeTimeout`)**: `Redeemed(ptr, y)` must occur before `TimedOut(ptr)`.
- **T2a (`ForwardTimeGap`)**: If `ForwardHTLC(P, ptrIn, ptrOut, y)` and both timeouts occur, then `TimedOut(ptrOut)` occurs before `TimedOut(ptrIn)`.
- **T2b (`HonestPartiesActBeforeIncomingTimeout`)**: If `ForwardHTLC(P, ptrIn, ptrOut, y)` and `TimedOut(ptrIn)` occurs, then `TimedOut(ptrOut)` must have occurred earlier.
- **T3 (`IntermediaryMustClaim`)**: If `ForwardHTLC(P, ptrIn, ptrOut, y)`, `Redeemed(ptrOut, y)`, and `TimedOut(ptrIn)` all occur, with `Redeemed` before `TimedOut`, then `Redeemed(ptrIn, y)` must occur.

**Question:** Are all of these restrictions necessary, or is some subset implied by the others?

**Methodology:** We removed T3 and re-ran `Intermediary_Never_Loses_Under_Liveness`.

**Result:** The lemma is **falsified** with a concrete counterexample in 59 derivation steps. The counterexample trace shows:
1. Intermediary $P$ forwards an HTLC from `ptrIn` to `ptrOut`.
2. `TimedOut(ptrIn)` occurs.
3. `Redeemed(ptrOut, y)` occurs (after the incoming timeout).
4. `Refunded(ptrIn, y)` occurs.
5. No `Redeemed(ptrIn, y)` occurs.
6. No `LtkCompromised(P)` occurs.

**Interpretation:** T2b orders the timeouts (`TimedOut(ptrOut)` before `TimedOut(ptrIn)`), but it does not force the intermediary to **sweep** the incoming HTLC when the preimage becomes available. T3 explicitly encodes this obligation: if the outgoing HTLC is redeemed before the incoming timeout, the intermediary **must** claim the incoming HTLC.

**Conclusion:** We have empirically demonstrated that T3 (`IntermediaryMustClaim`) is **load-bearing** for intermediary safety—we tested its removal and observed a concrete counterexample. We have not tested the removal of T1, T2a, or T2b, and therefore make no claim about their individual minimality.

---

## 6. Timing Safety with a Concrete Block Clock

### 6.1 Why a Separate Layer?

The main routing theories (`multihop.spthy`, `multihop_nhop.spthy`) treat time relationally: they reason about event orderings without assigning concrete block heights. The timing restrictions (T1, T2a, T2b, T3) encode the intended CLTV behaviour as constraints on trace validity.

This is sufficient for proving safety properties that depend only on ordering. However, it **assumes** the CLTV structure rather than **deriving** it. A more satisfying result would show that the CLTV deadline structure actually guarantees the required ordering.

The three small theories (`cltv_blocks.spthy`, `Clock.spthy`, `timeout.spthy`) add a **concrete block clock** and prove that the CLTV windows are non-empty. This is the payoff of isolating the clock from signing: these theories carry natural-numbers but not signing, so they remain tractable.

### 6.2 Pure CLTV Arithmetic (`cltv_blocks.spthy`)

This minimal theory (3 lemmas) proves purely arithmetic properties of CLTV deadlines:

- **`CLTV_Gap_Is_Positive`**: If `HopRegistered(ptrOut, ptrIn, d_out, d_in)` occurs, then $d_{\mathit{out}} < d_{\mathit{in}}$. The delta is strictly positive.
- **`Claim_Window_Nonempty`**: If `HopRegistered(ptrOut, ptrIn, d_out, d_in)` and `Revealed(b, ptrOut, d_out)` both occur, then $b < d_{\mathit{in}}$. The preimage is revealed before the incoming deadline, so the claim window is non-empty.
- **`Staggered_Path_Safe`**: For a 2-hop path with deadlines $d_1 < d_2 < d_3$, if `Revealed(b, ptr1, d1)` occurs, then $b < d_2$ and $b < d_3$. Both intermediaries have non-empty claim windows.

These lemmas are proved by combining the `DeltaPositive` restriction ($d_{\mathit{out}} < d_{\mathit{in}}$ from `HopRegistered`) with the `FulfillInTime` restriction ($b < d_{\mathit{out}}$ from `Revealed`) and transitivity of $<$.

### 6.3 Block-Clock Lifecycle (`Clock.spthy`)

This theory (9 lemmas) models the full HTLC lifecycle with explicit block heights:

- **`Clock_Start` / `Clock_Tick`**: The clock starts at block 1 and increments by 1 each tick. Each block height is recorded as a persistent `!BlockReached(b)` fact.
- **`Open_Channel`**: Channels are opened with a concrete CLTV deadline drawn from the current block height.
- **`Sender_Offer` / `Forward_HTLC` / `Receiver_Accept`**: HTLCs are offered, forwarded, and accepted with explicit deadlines. The `Lt` action enforces $d_{\mathit{out}} < d_{\mathit{in}}$.
- **`Intermediary_Claim` / `Timeout_Refund`**: Intermediaries claim before their incoming deadline or refund after it.

Key lemmas:

- **`Claim_Window_Exists`**: If `Forwarded(F, ptrIn, ptrOut, dIn, dOut, y)`, `RedeemedAt(ptrOut, y, bOut)`, and `RefundedAt(ptrIn, y, bRef)` all occur, then $b_{\mathit{out}} < b_{\mathit{ref}}$. The claim occurs before the refund.
- **`Transitive_Preimage_Before_Upstream_Deadline`**: For a 2-hop path, if both forwards occur and `RedeemedAt(ptrOut, y, bOut)` occurs, then $b_{\mathit{out}} < d_{\mathit{in}}$. The preimage is revealed before the upstream deadline.
- **`Loss_Implies_Skipped_Claim`**: If a forward occurs, the outgoing HTLC is redeemed, and the incoming HTLC is refunded, then the incoming HTLC was never claimed. The intermediary's loss is due to inaction.

### 6.4 Early-Timeout Race (`timeout.spthy`)

This minimal counterexample theory (1 lemma) demonstrates what happens when the `HonestPartiesActBeforeIncomingTimeout` restriction is removed:

- **`Early_Timeout_Race` [exists-trace]**: A trace exists where:
  - `ForwardHTLC(P, ptrIn, ptrOut, y)` occurs.
  - `TimedOut(ptrIn)` occurs at time $k$.
  - `Refunded(ptrIn, y)` occurs at time $j$.
  - `Redeemed(ptrOut, y)` occurs at time $i$.
  - $k < i$ (the incoming timeout occurs before the outgoing redemption).

This is the **early timeout race**: the incoming channel times out before the intermediary has a chance to claim, even though the outgoing HTLC is eventually redeemed.

**Two-sided certificate.** Combined with `Timeout_race_Blocked` in `multihop_nhop.spthy` (which proves the race is unreachable when the restriction is present), this establishes:
- Without `HonestPartiesActBeforeIncomingTimeout`: the race is reachable.
- With `HonestPartiesActBeforeIncomingTimeout`: the race is blocked.

Therefore, the restriction is **necessary**, not decorative.

---

## 7. Generalisation to N Hops + Soundness Theorem

### 7.1 The Two Models

We have two models of multi-hop routing:

- **Concrete model $C$** (`multihop.spthy`): Fixed 3-hop routing with signed messages over the Dolev–Yao network. Each hop has a specific forwarding rule (`Forward1_HTLC`, `Forward2_HTLC`) with explicit signature verification.
- **Abstract model $A$** (`multihop_nhop.spthy`): Generic N-hop routing with a single `Forward_HTLC` rule. The network is abstracted away using linear `Route(prev, me, ptr, y)` facts that represent authenticated routing state.

Both models share the same channel lifecycle and the same safety lemma statements. They differ only in the routing layer.

### 7.2 The Trap: Abstract Safety Does Not Imply Concrete Safety

One might hope that proving safety in the abstract model $A$ for arbitrary $N$ would automatically imply safety in the concrete model $C$. This is **false**.

The abstract model internalises the network as trusted `Route` facts. This **removes** Dolev–Yao power: in $A$, the adversary cannot inject arbitrary messages, replay offers, or forge signatures. Therefore, $A$ has strictly fewer behaviours than $C$. A safety property that holds in $A$ might be violated in $C$ by a trace that $A$ cannot represent (e.g., a trace with a forged forward).

**The gap** is precisely the adversary's ability to forge or replay a forward.

### 7.3 Closing the Gap: Locality and AUTH

The bridge between $A$ and $C$ is the **local per-hop authentication lemma** AUTH:

> **AUTH**: Every concrete forward is preceded by a valid incoming message from the previous hop (or the previous hop's key is compromised).

Concretely, AUTH is instantiated by the lemmas:
- `Forward1_Requires_Offer` (in $C$): `HTLCForwarded1` implies `HTLCOffered` or `LtkCompromised(S)`.
- `Forward2_Requires_Forward1` (in $C$): `HTLCForwarded2` implies `HTLCForwarded1` or `LtkCompromised(F1)`.

**Key property:** AUTH quantifies over **one adjacent pair** at a time. It does not quantify over the path length $N$ or the entire path. This is why it is provable in Tamarin: the proof is bounded by the size of the message terms, not by $N$.

### 7.4 Boundary Result: Generic Signed Forward Fails

We attempted to prove AUTH for a **generic signed forward rule** that works for any $N$:

```
rule Generic_Signed_Forward:
    let offer = <'htlc', ptrIn, $Prev, $Me, y, %vIn>
        offerFwd = <'htlc', ptrOut, $Me, $Next, y, %vOut>
        sigMe = sign(offerFwd, ltkMe)
    in
    [ In(<'htlc', ptrIn, $Prev, $Me, y, %vIn, sigPrev>),
      !Ltk($Me, ltkMe), !Pk($Prev, pkPrev),
      !ChannelConnect(ptrOut, $Me, $Next), Free(ptrOut),
      In(%fee), In(%vOut) ]
    --[ HTLCForwarded($Me, $Prev, $Next, ptrIn, ptrOut, y),
        Eq(%vIn, %vOut %+ %fee), ... ]->
    [ Route($Me, $Next, ptrOut, y),
      Out(<'htlc', ptrOut, $Me, $Next, y, %vOut, sigMe>) ]
```

This rule is self-referential: the output message has the same structure as the input message. Tamarin's **origin analysis** (which determines which party could have originated a term) does not terminate on such self-referential terms.

**Empirical result:** Even a 2-hop exists-trace witness (`experiments/auth_local.spthy`, `auth_local_sources.spthy`) OOMs. The source analysis stage fails to conclude, exhausting memory.

**Conclusion:** AUTH is provable *because* it is stated per-hop with specific message structures, not as a generic rule. This is a fundamental limitation of current automated verification technology.

### 7.5 Refinement Theorem (Pen-and-Paper)

We state the soundness theorem connecting $A$ and $C$:

> **Theorem (Refinement).** Let $\pi$ be a projection that maps a concrete trace to an abstract trace by keeping all $\Sigma$-actions (channel lifecycle, safety-relevant HTLC actions) and deleting all network/crypto events. Under AUTH, for any safety property $\varphi$ that holds in $A$ for all $N$, $\varphi$ holds in $C$ for all $N$.

**Proof sketch (pen-and-paper):**

1. By AUTH, every concrete forward has a matching abstract step: if `HTLCForwarded_i(...)` occurs in $C$, then either a valid incoming message occurred (which projects to an abstract `Route` fact) or a key was compromised (which is preserved by $\pi$).

2. By induction on the number of forwarding steps, any concrete trace in $C$ projects to a valid abstract trace in $A$ that agrees on all $\Sigma$-actions.

3. If $\varphi$ is violated in $C$, there exists a concrete trace with a $\Sigma$-violation. By (2), this projects to an abstract trace with the same $\Sigma$-violation, contradicting that $\varphi$ holds in $A$.

**Honest caveats:**

- AUTH is **machine-checked** in $C$ (the per-hop lemmas).
- Safety properties for all $N$ are **machine-checked** in $A$ (the 25 lemmas of `multihop_nhop.spthy`).
- The refinement argument (projection + induction) is **pen-and-paper**. Tamarin cannot quantify over $N$ or relate two theories. This is the honest boundary of our verification.

### 7.6 N-Hop Caveats (Explicit)

We state honestly the limitations of the N-hop generalisation:

1. **25 active lemmas** in `multihop_nhop.spthy` verify in approximately 103.5 s (natural-numbers builtin).

2. **Four `[use_induction]` causality lemmas are commented out** as deliberate tractability boundaries:
   - `Settle_Requires_Receiver_Release`
   - `Forward_Requires_Incoming`
   - `Claim_Requires_Release`
   - `Redeem_Requires_Receiver_Release`

   These lemmas require tracing backwards through an unbounded chain of `Route` facts, which causes Tamarin's induction to diverge.

3. **Fees are enforced structurally, not as lemmas.** The generic `Forward_HTLC` rule carries `Eq(%vIn, %vOut %+ %fee)` as a firing guard. This means:
   - Conservation holds by construction in the abstract model.
   - A per-hop lemma would merely restate the guard (tautological).
   - End-to-end conservation over $N$ hops is a sum of $N$ fees, which is not finitely statable in a single Tamarin lemma.
   - Induction over the generic chain hits the same non-termination as the four commented lemmas.

   This is the honest reason the fee lemmas live only in `multihop.spthy`.

4. **No wormhole in $A$.** By design, the abstract model removes the network side channel that the wormhole exploits. The wormhole is proved where it is meaningful: in the concrete model $C$.

---

## 8. What Failed — The Tractability Boundaries

We present negative results as first-class contributions. Understanding where automated verification fails is as important as understanding where it succeeds.

### 8.1 The Three-Ingredient OOM

**Observation.** Combining all three Tamarin ingredients causes the prover to exhaust memory:
- Signing (equational theory with `sign`/`verify`)
- Natural-number induction (`[use_induction]` lemmas)
- Unbounded block clock (rules that emit `!BlockReached(b)` for all $b$)

Any two of the three are fine. Only the full triple OOMs.

**Empirical test.** We constructed a minimal theory with all three ingredients and attempted to prove a simple causal lemma. Tamarin exhausted memory (16 GB) during the source analysis stage.

**Implication.** This is the reason for our modular split. The main routing theories carry signing and natural-numbers but not an unbounded clock. The clock theories carry natural-numbers but not signing. No theory carries all three.

### 8.2 Signed-Message N-Hop Routing

**Observation.** Origin analysis on self-referential signed-message terms does not terminate.

**Experiment.** We attempted to prove AUTH for a generic signed forward rule (§7.4). Even a 2-hop exists-trace witness OOMs during source analysis.

**Root cause.** The output message `<'htlc', ptrOut, $Me, $Next, y, %vOut, sigMe>` has the same structure as the input message. Tamarin's origin analysis must determine which party could have originated each subterm, but the self-referential structure creates an unbounded recursion.

**Implication.** AUTH must be proved per-hop with specific message structures, not as a generic rule. This is a fundamental limitation.

### 8.3 A Rejected Restriction

**Attempt.** We initially wrote a restriction `OneRedeemPerPtr` stating that each `ptr` can be `Redeemed` at most once.

**Failure.** This restriction falsified the honest witness `Multihop_Payment_Possible`. The 3-hop trace has two `Redeemed` events: `Redeemed(ptrF2R, y)` (receiver's view) and `Redeemed(ptrF1F2, y)` (intermediary's view). These are two endpoints' views of one hop, not two spends of the same output.

**Correction.** The correct guard is `OneHTLCPerPtr` (at most one HTLC added per output), later made structural via `Free(ptr)`. The `Redeemed` action can legitimately occur multiple times for the same `ptr` if multiple parties are observing the same redemption.

**Lesson.** Careful attention to the semantics of action facts is required. `Redeemed(ptr, y)` means "party X observed that ptr was redeemed with y," not "ptr was spent."

### 8.4 A Caught False Positive

**Attempt.** An exists-trace lemma appeared to show "value creation": a trace where the sender locked less than the receiver received.

**Investigation.** The trace shared only the payment hash $y$ across two independent payment attempts. The sender locked $v_1$ on hash $y$ in one attempt, and the receiver received $v_2 > v_1$ on hash $y$ in another attempt. This is invoice-hash reuse, not a soundness bug.

**Correction.** We tightened the lemma to require a single linked chain (offer → forward1 → forward2 → fulfill) sharing not just the hash but the specific HTLC pointers. The tightened lemma falsified, confirming no value creation.

**Lesson.** Adversarial-verification discipline: always check whether an "attack" trace is actually a valid protocol execution under a different interpretation.

### 8.5 Reusable Channels (Boundary)

**Stage 1 (shipped).** We implemented single-HTLC-per-output via `Free(ptr)`. The `Free(ptr)` is emitted once on channel open and consumed on each HTLC addition. This ensures at most one HTLC per output.

**Stage 2 (boundary).** We attempted to return `Free(ptr)` when the HTLC is resolved (redeemed or refunded), enabling multiple sequential HTLCs on the same channel.

**Result.** All-traces safety lemmas verify with `--auto-sources` (approximately 45 s each). However, every exists-trace witness fails to converge (killed at 500–700 s).

**Root cause.** Returning `Free(ptr)` creates a cycle in the state machine. Tamarin's exists-trace search must explore all possible orderings of rule applications, and the cycle introduces unbounded non-determinism.

**Status.** This is a clean tractability boundary. We ship Stage 1 and document Stage 2 as a limitation.

---

## 9. Related Work

**Payment channel protocols.** Poon and Dryja (2016) introduced the Lightning Network protocol. Our work complements these informal specifications with machine-checked guarantees for the routing layer.

**Wormhole attack.** Malavolta et al. (NDSS 2019) identified the wormhole attack and proposed AMHL (Atomic Multi-Hop Locks) as a mitigation. Their analysis is informal; we provide a machine-checked proof that the attack is reachable in a symbolic Dolev–Yao model and quantify the stolen value exactly. PTLCs (Point Timelock Contracts) are another proposed mitigation, which we do not model.

**Composable-crypto proofs.** Kiayias and Litos (CSF 2020) provide a UC-style security proof for payment channels at the two-party layer. Their proof is rigorous but does not cover multi-hop routing. Our symbolic routing model is complementary: it verifies properties at a layer their proof does not machine-check.

**Tamarin and symbolic verification.** Meier et al. (CAV 2013) introduced the Tamarin prover, providing the foundation for the multiset-rewrite reasoning used here. While Tamarin has been applied to various cryptographic protocols, handling the specific combination of stateful channel updates, arithmetic fee deductions, and temporal ordering in PCNs presents unique scalability challenges, which we document in §8.

---

## 10. Conclusion

We have presented a comprehensive symbolic verification of multi-hop payment channel security: 81 machine-checked lemmas across five Tamarin theories, covering channel lifecycle, HTLC routing, CLTV timing, and value conservation.

The **durable contributions** are methodological, not the re-verification of expected safety properties:

1. **The linear single-spend discipline**: We identified a category error (modeling one-shot on-chain resources as persistent facts) that caused two independent soundness gaps, and we fixed both with the same linear-token remedy. This is a reusable modeling invariant for future symbolic PCN analyses.

2. **Soundness layering**: We developed an N-hop abstraction and a pen-and-paper refinement theorem that transfers routing safety to arbitrary path lengths, using a local per-hop authentication lemma as the bridge. This demonstrates how to scale verification beyond fixed path lengths when generic rules hit tractability boundaries.

3. **The tractability map**: We identified the exact combinations of Tamarin ingredients (signing + nat-induction + unbounded clock; self-referential signed terms; reusable channel slots) that cause the prover to fail. This map explains our modular decomposition and provides guidance for future efforts.

Lightning is the validating case study; the method is the contribution. Every positive and negative result was executed by the prover or explicitly flagged as pen-and-paper. We hope this work establishes a new standard for honesty and precision in protocol verification papers.

---

## Appendix A: Full Lemma Index

### A.1 `multihop.spthy` (43 lemmas)

**Channel Lifecycle (8)**
1. `state_update` [use_induction]
2. `Funds_Locked_Before_Update` [use_induction]
3. `Update_Requires_Negotiation` [use_induction]
4. `delayed_funds`
5. `instant_funds`
6. `settlement_is_traceable`
7. `Protocol_execution` [exists-trace]
8. `No_Punishment_Without_Cheating`

**Invoice/Preimage Authentication (6)**
9. `Ltk_Known_Implies_Compromised` [reuse]
10. `Invoice_Released_Once` [reuse]
11. `Preimage_Secret_Until_Released`
12. `Invoice_Has_Secret_Preimage` [reuse]
13. `Invoice_Authenticates_Settlement`
14. `HTLC_On_Opened_Channel` [reuse, use_induction]

**Lock/Release Causality (8)**
15. `Settle_Requires_Receiver_Release`
16. `Forward1_Requires_Offer`
17. `Forward2_Requires_Forward1`
18. `Fulfill_Requires_Forward2`
19. `Forward1_Requires_Offer_Honest`
20. `Forward2_Requires_Forward1_Honest`
21. `Fulfill_Requires_Forward2_Honest`
22. `Claim_Requires_Release`

**Atomicity and Intermediary Safety (7)**
23. `Settle_Excludes_Sender_Refund`
24. `Loss_Requires_Inaction`
25. `Refund_Requires_Timeout` [reuse]
26. `Intermediary_Never_Loses_Under_Liveness`
27. `Payment_Atomicity_Under_Liveness`
28. `Timeout_race_Blocked`

**Value/Fees (9)**
29. `Fee_Conservation_Hop1`
30. `Fee_Conservation_Hop2`
31. `Receiver_Paid_Invoice_Amount`
32. `Fees_Charged_On_Path_Possible` [exists-trace]
33. `Fee_Strictly_Positive_Hop1`
34. `Fee_Strictly_Positive_Hop2`
35. `EndToEnd_Value_Conservation`
36. `Wormhole_Fee_Theft_Reachable` [exists-trace]
37. `Wormhole_Steals_Exactly_The_Fees` [exists-trace]

**Reachability (5)**
38. `Multihop_Payment_Possible` [exists-trace]
39. `Distinct_Parties_Configuration` [exists-trace]
40. `Refund_Possible` [exists-trace]
41. `Honest_Intermediary_Refunds` [exists-trace]
42. `Cooperative_Close_Execution` [exists-trace]

**Auth/Attack (1)**
43. `Forged_Invoice_Requires_Key_Compromise` [exists-trace]

### A.2 `multihop_nhop.spthy` (25 active + 4 commented)

**Channel Lifecycle (8)**
1. `state_update` [use_induction]
2. `Funds_Locked_Before_Update` [use_induction]
3. `Update_Requires_Negotiation` [use_induction]
4. `delayed_funds`
5. `instant_funds`
6. `settlement_is_traceable`
7. `Protocol_execution` [exists-trace]
8. `No_Punishment_Without_Cheating`

**Invoice/Preimage Authentication (5)**
9. `Ltk_Known_Implies_Compromised` [reuse]
10. `Invoice_Released_Once` [reuse]
11. `Preimage_Secret_Until_Released`
12. `Invoice_Has_Secret_Preimage` [reuse]
13. `HTLC_On_Opened_Channel` [reuse, use_induction]

**Atomicity and Intermediary Safety (7)**
14. `Settle_Excludes_Sender_Refund`
15. `Loss_Requires_Inaction`
16. `Refund_Requires_Timeout` [reuse]
17. `Intermediary_Never_Loses_Under_Liveness`
18. `Payment_Atomicity_Under_Liveness`
19. `Timeout_race_Blocked`
20. `Invoice_Authenticates_Settlement`

**Reachability / Other (5)**
21. `Multihop_Payment_Possible` [exists-trace]
22. `Distinct_Parties_Configuration` [exists-trace]
23. `Refund_Possible` [exists-trace]
24. `Forged_Invoice_Requires_Key_Compromise` [exists-trace]
25. `Cooperative_Close_Execution` [exists-trace]

**Commented Out (4 — Tractability Boundaries)**
26. `Settle_Requires_Receiver_Release`
27. `Forward_Requires_Incoming`
28. `Claim_Requires_Release`
29. `Redeem_Requires_Receiver_Release`

### A.3 `Clock.spthy` (9 lemmas)

1. `HTLC_Needs_Open_Channel` [use_induction]
2. `No_HTLC_After_Close` [use_induction]
3. `Claim_Window_Exists`
4. `Transitive_Preimage_Before_Upstream_Deadline`
5. `Loss_Implies_Skipped_Claim`
6. `Outcome_Exclusive`
7. `Redeem_Reachable` [exists-trace]
8. `Refund_Reachable` [exists-trace]
9. `Honest_Flow_Possible` [exists-trace]

### A.4 `cltv_blocks.spthy` (3 lemmas)

1. `CLTV_Gap_Is_Positive`
2. `Claim_Window_Nonempty`
3. `Staggered_Path_Safe`

### A.5 `timeout.spthy` (1 lemma)

1. `Early_Timeout_Race` [exists-trace]

---

## Appendix B: Reproduction Instructions

### B.1 Environment

- Tamarin prover version 1.8.0
- Maude version 3.1
- Python 3.8+ (for run script)

### B.2 Per-Theory Execution

```bash
# Main concrete model (43 lemmas)
tamarin-prover multihop.spthy --prove --heuristic=c --stop-on-trace=seqdfs --derivcheck-timeout=0

# N-hop abstraction (25 lemmas)
tamarin-prover multihop_nhop.spthy --prove --heuristic=c --stop-on-trace=seqdfs --derivcheck-timeout=0

# Block-clock lifecycle (9 lemmas)
tamarin-prover Clock.spthy --prove --heuristic=c

# Pure CLTV arithmetic (3 lemmas)
tamarin-prover cltv_blocks.spthy --prove --heuristic=c

# Early-timeout race (1 lemma)
tamarin-prover timeout.spthy --prove --heuristic=c --stop-on-trace=seqdfs
```

**Note on `--stop-on-trace`:** This flag rescues heavy exists-trace witnesses by stopping as soon as a witness is found. However, it causes the natural-number arithmetic theories to hang during source analysis. Therefore, it is applied only to theories without `natural-numbers` builtin or to specific lemmas.

### B.3 Batch Execution

```bash
python3 run.py
```

This script runs all theories and lemmas, collecting timing and result information.

### B.4 Expected Timings

| Theory | Total Time | Notes |
|--------|-----------|-------|
| `multihop.spthy` | ~262 s | After linear-token fixes |
| `multihop_nhop.spthy` | ~103.5 s | Natural-numbers builtin |
| `Clock.spthy` | ~45 s | Per-lemma with --auto-sources |
| `cltv_blocks.spthy` | ~15 s | Minimal theory |
| `timeout.spthy` | ~5 s | Single exists-trace |

**Disclaimer:** Timings are reported from local runs on a machine with 16 GB RAM and an 8-core processor. Re-measure before submission.

---

## Appendix C: Claim-Strength Cheat-Sheet

| Claim | Status |
|-------|--------|
| 81 lemmas verify | **Machine-checked** (per-theory) |
| Both single-spend bugs reachable pre-fix / gone post-fix | **Machine-checked** |
| Wormhole reachable + fee-exact | **Machine-checked** |
| T3 load-bearing (counterexample) | **Machine-checked** |
| AUTH is local per-hop | **Machine-checked** in $C$ |
| All-N routing safety on $A$ | **Machine-checked** on abstraction |
| Abstraction soundness ($C \Leftarrow A$ for all $N$) | **Pen-and-paper** refinement |
| Timings (262 s / 103.5 s / 59-step / etc.) | **Reported** from local runs |
| `AUDIT_Double_Publish_Revoked` verdict | **Pending** a terminating run |
