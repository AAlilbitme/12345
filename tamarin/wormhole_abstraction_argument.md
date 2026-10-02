# Why the wormhole witness in the abstract model is a trace of the full model

Abstract model: `wormhole_clean.spthy`. Full model: `MultiNhop_simon_honest.spthy`.
Witness: `R8_Wormhole_F2_Honest_Unpaid` (verified, 32 steps).

The attack is an *existence* claim, so it is enough to show that every step of the
abstract trace can be replayed in the full model. The abstractions are checked one
by one below.

| Abstraction in `wormhole_clean.spthy` | Why the witness still exists in the full model |
|---|---|
| Channel layer replaced by `Open_Channel` (produces `!ChannelConnect`, `Free`, public `ptr`) | In the full model the same facts are produced by the handshake ending in `Lock_Funds_And_Open`. Every channel open is honest and independent of the HTLC layer; `Distinct_Parties_Configuration` (verified) shows the required three/four channels can be opened between distinct parties. Channel ids are public in both models (`A_Send_Proposal` outputs `~ptr`). |
| Amounts and fees removed from `Forward_HTLC` | In the full model the forwarder reads `%vIn`, `%fee`, `%vOut` from the network with `%vIn = %vOut %+ %fee`. The attacker can always supply e.g. `%fee = 1`, `%vOut = 1`, `%vIn = 1 %+ 1`, so every abstract forward step has a full-model counterpart. Amounts appear in no attack condition. |
| `Free(ptr)` not returned on settle | Returning `Free` only adds behaviour. The witness uses each channel once, so it never needs a returned `Free`. |
| T3 (`IntermediaryMustClaim`) omitted | **Not automatically satisfied.** For F2, T3 is vacuous (`p23` is never redeemed). But F3's outgoing `p3R` is redeemed before its incoming `p23` times out (T1 + T2), so T3 forces F3 to claim `p23` unless F3 was compromised before that timeout. The witness is a full-model trace only if F3 is the compromised endpoint that leaks. This must be checked by running the witness with T3 included (`wormhole_clean_T3.spthy`). |
| Search bounds (one invoice, one offer, one leak, one inject, at most two compromised parties) | Restrictions only remove traces. A trace that satisfies the bounds is a trace of the unbounded model. |
| T1, T2, `OneOutcomePerHTLC`, `OneTimeoutPerPtr`, `RedeemBeforeTimeout` | Identical in both models (T2 honest-only, prefix-closed), so the witness satisfies them in both. |

Conclusion: the 32-step witness maps step by step to a trace of the full model in
which an honest intermediary F2 forwards the payment, is paid on neither hop (`p12`
never redeemed, `p23` refunded), while the sender settles with F1 using the preimage
leaked at F3's channel and injected at F1's channel.

What this argument does *not* claim: that Tamarin verified the attack in the full
model (`Wormhole_Honest_F2_Robbed` gives no result within 10 minutes there).
