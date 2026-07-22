# Generalizing to N-hop routing — an idealized-channel abstraction

The main model (`../multihop.spthy`) proves 43 properties over a **fixed 3-hop**
path, with the full Dolev–Yao adversary, signatures, revocation, and on-chain
settlement. A natural question is: *why only 3 hops?*

These files answer it by **logical decomposition**. We isolate the routing logic
from the cryptographic primitives: model the HTLC as a **linear fact on an
idealized channel** (rather than a signed network message), and prove that the
core routing-safety invariants hold for an **arbitrary path length**, by
induction over the chain.

This is a standard, sound proof layering — not a weakened model but a deliberate
abstraction:

> Even with the network/cryptographic layer perfectly abstracted, the protocol's
> state-transition logic alone prevents intermediary loss, independent of the
> number of hops.

## Files (both verify)

| File | Proves (generic over chain length) | Steps |
|------|-------------------------------------|-------|
| `generic_linearfact_structural.spthy` | `Forward_Requires_Incoming` (causality), `Claim_Requires_Release` | 17 / 20 |
| `generic_linearfact_safety.spthy` | `Redeem_Requires_Receiver_Release` (atomicity/authentication), **`Intermediary_Never_Loses`** | 45 / 551 |

`Intermediary_Never_Loses` concludes `==> F` — the Tamarin idiom for "this state
(honest forwarder loses money) is unreachable," for any N.

## Scope — read before citing

1. **Only the safety / all-traces lemmas generalize here.** The crypto-authentication
   results (`Invoice_Authenticates_Settlement`, `Forged_Invoice_Requires_Key_Compromise`)
   are **not** carried by this abstraction — they deliberately depend on signatures,
   which were removed, and remain proved only in the concrete 3-hop model. The
   layering is: *concrete model → authentication + full adversary (3-hop);
   abstraction → routing safety (N-hop).* Not all 43 properties generalize.
2. **Exists-trace witnesses still don't scale.** The `==> F` safety lemmas are
   all-traces and induction handles them; a concrete N-hop *reachability* witness
   needs bounding/an oracle and is not proved here.

## Why not keep it as a signed message?

The intuitive generalization — one generic forward rule that re-signs and forwards
the HTLC as a signed `Out`/`In` message — **breaks Tamarin**: even a one-hop
`Direct_Payment_Possible` witness times out / OOMs. The blocker is the
self-referential *signed* `'htlc'` term (a forward produces a signed message that
another forward consumes), which sends Tamarin's origin analysis into unbounded
recursion. Adding a fresh per-hop `~id` fixes replay but **not** termination —
tested and confirmed. This cryptographic origin-analysis is precisely the
bounding factor that the linear-fact abstraction steps around.

## Reproduce

```bash
export LANG=C.utf8 && export LC_ALL=C.utf8
tamarin-prover generic_linearfact_structural.spthy --heuristic=c --derivcheck-timeout=0 --prove=Forward_Requires_Incoming
tamarin-prover generic_linearfact_structural.spthy --heuristic=c --derivcheck-timeout=0 --prove=Claim_Requires_Release
tamarin-prover generic_linearfact_safety.spthy     --heuristic=c --derivcheck-timeout=0 --prove=Redeem_Requires_Receiver_Release
tamarin-prover generic_linearfact_safety.spthy     --heuristic=c --derivcheck-timeout=0 --prove=Intermediary_Never_Loses
```


## `reusable_channel_stage2.spthy` (SPIKE — not shipped)

Stage 2 of the linear-channel refactor: reusable channels (resolution reproduces
the `Free(ptr)` slot). Documented Tamarin boundary — safety lemmas verify with
`--auto-sources` (~45s each), but exists-trace witnesses and interval lemmas do
not converge (killed 500-700s). See REPORT2.md section 11. Stage 1 (structural
single-HTLC-per-output) is the shipped model in `../multihop.spthy`.

## `bounded_reusable_channel.spthy` (finite balance-coupled refinement)

This standalone theory is the positive, tractable companion to the Stage-2
boundary. It models one channel through two explicit state versions:

```text
Open0 -> Lock0 -> Open1 -> Lock1 -> Open2
```

The same channel pointer carries two sequential unit HTLCs. The first settles,
transferring one unit from payer to payee; the second refunds, restoring its
locked unit. The theory verifies:

- a concrete two-HTLC reuse witness with balances `(3,1) -> (2,2) -> (2,2)`;
- the second add requires an earlier first-HTLC resolution;
- settlement and refund each produce the next resolved channel state.

It is deliberately finite and does **not** claim unbounded reusable channels,
signature authentication, multi-hop routing, CLTV semantics, or a refinement
proof for `multihop.spthy`. Its purpose is to establish a minimal, executable
target semantics for eventual HTLC-bearing channel-state integration.

```bash
tamarin-prover bounded_reusable_channel.spthy --heuristic=c \
  --derivcheck-timeout=0 --prove
```

## Revoked-commitment single-spend audit

`revocation_uniqueness.spthy` preserves the pre-fix model and proves a
54-step duplicate-publication/duplicate-punishment witness: persistent
revocation knowledge could recreate a fresh penalty input repeatedly. The
shipped `../multihop.spthy` now separates persistent `!RevokedSecret`
knowledge from the linear `RevokedCommitmentUnspent(...)` output token. That
change makes the UTXO single-spend resource explicit; a general automatic
uniqueness proof remains a source-search challenge in the full signed model.
