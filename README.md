You are an advanced formal verification AI co-pilot specializing in the Tamarin Prover. Your purpose is to assist in developing logically sound, syntax-compliant, and mathematically verifiable protocol theories (.spthy files).

MANDATORY INSTRUCTIONS FOR GENERATION:
1. CONSULT THE MANUAL: Before drafting or modifying complex theories, explicitly consult the indexed @Tamarin Manual framework to cross-reference keyword usage, builtin definitions (e.g., diffie-hellman, bilinear-pairings), and restriction syntaxes.
2. MULTISET REWRITING VALIDATION: Ensure every transition state rule follows the strict structure: `rule Name: [ l ] --[ a ]-> [ r ]`. Ensure persistent facts (!) and linear facts are managed correctly without accidental duplication.
3. LOGICAL SOUNDNESS & VERIFIABILITY: 
   - All lemmas must use mathematically precise temporal logic operators (==>, &, |, not, @).
   - Quantifiers must declare timepoints strictly (e.g., `All x #t. ...`).
   - If a lemma risks non-termination or proof loops (such as open sources or structural invariant issues), prioritize writing discrete tracking restrictions or auxiliary lemmas over breaking the main security goal.
4. EXACT SYNTAX: Do not invent pseudo-code. Use exact Tamarin syntax primitives.

When writing or debugging, explicitly output a brief design thought explaining how your rule maps cleanly to a valid labeled transition system.

---

# Lightning-style Payment Channels in Tamarin

## Project layout

| File | Description |
| --- | --- |
| `splib/paymentchannel.splib` | Shared library (included via Tamarin's integrated preprocessor `#include`): PKI, funding, signed channel-opening handshake, revocable commitment states, off-chain updates with revocation, cooperative/unilateral close, cheat-and-punish, settlement, and the shared restrictions. Not a standalone theory. |
| `TwoPartyChannel.spthy` | Two-party payment channel theory. Pulls the whole transition system from the splib and states the single-channel security lemmas (state updates require an open channel, settlement traceability, punishment only after cheating or key compromise, executability of update/close flows). |
| `multihop.spthy` | Lightning-style 3-hop payment following the lecture slides (`Alice <-ptrAB-> Bob <-ptrBC-> Carol <-ptrCD-> Dave`), built on top of the same splib. Adds the HTLC layer (invoice with payment hash `h(x)`, same hash locked on every hop, `update_add_htlc`-style offers, preimage release, backwards redeem propagation, timeout refunds with one-outcome-per-HTLC exclusivity) and proves executability of the lock/release rounds and the refund branch, hash-lock secrecy, proof-of-payment, per-hop authenticity for all three hops, intermediary atomicity, and redeem/refund exclusivity. |
| `PaymentChannels.spthy` | Original monolithic two-party model, kept for reference. Superseded by `splib/paymentchannel.splib` + `TwoPartyChannel.spthy`. |

The connection between the files is the preprocessor include (see the
Tamarin manual, "Integrated Preprocessor"):

```
#include "splib/paymentchannel.splib"
```

Both theories share one definition of the two-party channel; the
multi-hop theory only becomes executable after two channels were opened
by the shared two-party protocol (via the persistent `!ChannelPeers`
facts produced on funding).

## Verification

Tested with Tamarin 1.12.0 / Maude 3.5. All lemmas of both theories
verify automatically:

```sh
tamarin-prover --prove TwoPartyChannel.spthy   # 8 lemmas, ~10 s
tamarin-prover --prove multihop.spthy          # 12 lemmas, ~60 s
```

Notes on proof termination (avoiding loops):

- `multihop.spthy` carries `configuration: "--stop-on-trace=seqdfs"` in
  its theory header: the witness search for the exists-trace sanity
  lemmas needs sequential depth-first search; the default BFS exhausts
  memory on the interleavings of the channel openings.
- The HTLC hops use distinct message tags (`'htlc1'`, `'htlc2'`,
  `'htlc3'`); a single shared tag lets a forwarded HTLC be re-parsed as
  a fresh offer, which both violates hop authenticity and makes
  backward search loop through an unbounded forward chain.
- The auxiliary `[reuse]` lemmas (`Preimage_Secret_Until_Released`,
  `Offer_Requires_Invoice`, `Invoice_Has_Secret_Preimage`,
  `Forward1_Requires_Offer`, `Forward2_Requires_Forward1`) let the
  final atomicity proof compose the per-hop arguments instead of
  re-deriving the whole three-hop chain (which times out otherwise),
  and `state_update` uses `[use_induction]` to cut the off-chain
  update loop.
- The executability of the full payment pipeline and of the
  four-distinct-parties topology are checked as two separate
  exists-trace lemmas: their conjunction in a single witness (40+ rule
  instances) exceeds the automated witness search.

## Relation to the lecture slides (Maffei, "Scalability")

- Channel open via mutually signed funding, revocable commitments with
  per-state hash secrets, punishment for publishing revoked states,
  CSV-style delayed vs instant settlement, cooperative close: in the
  splib / `TwoPartyChannel.spthy`.
- Multi-hop scenario Alice -> Bob -> Carol -> Dave (slides 19-27):
  invoice (`y = h(x)`), lock round with the same hash on every hop,
  release round propagating the preimage backwards, timeout refund
  branch: in `multihop.spthy`.
- Abstractions: Tamarin has no quantitative time, so the staggered
  timelocks (3t > 2t > t) are abstracted to the OneOutcomePerHTLC
  exclusivity (an HTLC is redeemed or refunded, never both); amounts
  and fees are not modelled (no arithmetic in the term algebra); the
  invoice is signed (BOLT 11) to make proof-of-payment provable.
