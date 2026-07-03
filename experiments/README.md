# Experiments — generalizing to arbitrary-length routing

These are **prototypes**, not part of the verified model package. They explore
whether the fixed 3-hop chain (Sender → F1 → F2 → Receiver) can be generalized
to an **unbounded number of hops** via a single generic forward rule.

## Files & results

| File | Forwarding encoding | Result |
|------|---------------------|--------|
| `generic_multihop_signed.spthy` | signed `Out`/`In` network messages (one generic rule) | ❌ **breaks Tamarin** — every lemma, incl. bare reachability, OOMs/times out. The recursive `'htlc'` term defeats source analysis. |
| `generic_linearfact_structural.spthy` | linear `Route(prev,me,ptr,y)` fact (one generic rule) | ✅ `Forward_Requires_Incoming` (17 steps), `Claim_Requires_Release` (20 steps). `Two_Hop_Payment_Possible` witness times out. |
| `generic_linearfact_safety.spthy` | linear fact + timeout/refund + T1–T3/T2b restrictions | ✅ `Redeem_Requires_Receiver_Release` (45 steps), **`Intermediary_Never_Loses` (551 steps)** — all over unbounded chain length. |

## Conclusion

Arbitrary-length routing **is feasible for the safety properties** — including the
headline `Intermediary_Never_Loses` — proved by induction over the chain, **if**
forwarding is a linear fact rather than a signed message.

Trade-offs:
- The signed-message version (the intuitive encoding) does not work — even
  reachability is intractable.
- The linear-fact route **weakens the network adversary** on the forwarding hop
  (the HTLC is no longer carried as a signed message the adversary can intercept).
- Exists-trace **witnesses** for a concrete topology still blow up (the generic
  rule gives the forward search too much freedom) — they'd need bounding/an oracle.

Suggested framing: keep the fixed-hop signed-message model as the *strong-adversary*
result, and present the linear-fact model as the *unbounded-length* result, noting
the adversary trade-off.

## Reproduce

```bash
export LANG=C.utf8 && export LC_ALL=C.utf8
tamarin-prover generic_linearfact_structural.spthy --heuristic=c --derivcheck-timeout=0 --prove=Forward_Requires_Incoming
tamarin-prover generic_linearfact_structural.spthy --heuristic=c --derivcheck-timeout=0 --prove=Claim_Requires_Release
tamarin-prover generic_linearfact_safety.spthy     --heuristic=c --derivcheck-timeout=0 --prove=Redeem_Requires_Receiver_Release
tamarin-prover generic_linearfact_safety.spthy     --heuristic=c --derivcheck-timeout=0 --prove=Intermediary_Never_Loses
```
