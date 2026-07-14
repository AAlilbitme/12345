# Archive

These two files are **superseded**, kept only as the tested precedent and
for historical reference. Nothing they prove is missing from the current
suite.

- **`multihop_no_fees.spthy`** — the original `multihop.spthy` (fixed 3-hop,
  signed HTLC routing, no invoice amounts). Replaced by the current
  `multihop.spthy`, which merges this file with `value_conservation.spthy`
  and verifies all 39 lemmas (16 channel/structural + 23 HTLC/value).

- **`value_conservation.spthy`** — amount/fee conservation in a separate
  nat-arithmetic abstraction, originally kept apart because combining the
  signing equational theory with nat induction was assumed to OOM Tamarin.
  That assumption was tested, not just asserted, and did not hold once the
  unbounded block clock (the actual third OOM ingredient) was absent. All
  four of its lemmas are ported into the current `multihop.spthy`
  (`Fee_Conservation_Hop1/Hop2`, `Receiver_Paid_Invoice_Amount`,
  `Fees_Charged_On_Path_Possible`).

- **`PaymentChannels.spthy`** — the standalone channel-lifecycle layer,
  rule-for-rule and lemma-for-lemma contained in `multihop.spthy`'s channel
  layer. Kept as a fast-verifying, isolated demo of the handshake →
  state-update → close → punishment flow.

See `multihop.spthy`'s header for the full merge history and the exact
step counts of every lemma when re-verified against the merged file.
