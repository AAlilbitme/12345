# Goal-2 / deadline status (only completed proofs count; timeouts are inconclusive)

## Safety on modelupd (no -D=LIVENESS)
- Verified: 20 lemmas (see runupd_batch_w0.txt, runupd_batch_w1.txt).
- Falsified: 0.
- Inconclusive (batch timeout): all other safety lemmas, including
  Funding_Spent_Once, No_Double_Publish, Invoice_Signature_Origin,
  Offer_Requires_Invoice.
- Claim allowed: "the goal-2 model preserves the 20 verified safety properties
  under channel-update routing; the rest are pending or inconclusive."

## Deadline model (modeldeadline.spthy / deadline.spthy) - categories
1. Correspondence and clock invariants (safety config):
   Settle_Commit_Correspondence (gate for bounded responsiveness),
   Ticks_Consecutive, Request/Commit/Receipt_Stamp_Is_Current.
2. Satisfiability witness (-D=LIVENESS): Deadline_Witness.
3. Deadline theorem (-D=LIVENESS): Deadline_Per_Hop.
4. Negative controls:
   - ablation: Deadline_Per_Hop with -D=LIVENESS -D=NOBOUND (expect falsified)
   - CLTV gap D-1: -D=LIVENESS -D=SMALLGAP (expect falsified; inspect trace for
     maximum delay and expiry tick before the late commit)
   - Request_Without_Commit, Commit_Without_Receipt (safety config, no
     assumptions active)

The theorem only counts together with a verified Deadline_Witness.
No liveness claim until categories 1-4 complete.
