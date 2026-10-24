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

## Result on the one-hop core model (deadline_core.spthy) - all gates met
Gate 1 (safety config): Settle_Commit_Correspondence verified (6);
  Delivery_Unique (8027) and Request_Unique (693) verified [reuse helpers];
  Request_Without_Commit verified (13); Commit_Without_Receipt verified (12).
Gate 2 (-D=LIVENESS -D=BOUND -D=GAP2): Deadline_Witness_Concrete verified (49).
  (General Deadline_Witness: timeout; a concrete trace suffices for existence.)
Gate 3 (-D=LIVENESS -D=BOUND -D=GAP2): Deadline_Per_Hop verified (30).
Gate 4: Ablation (-D=LIVENESS -D=GAP2): trace found, concrete (14) and general (27).
        Gap control (-D=LIVENESS -D=BOUND -D=GAP1): trace found, concrete (17)
        and general (31); in Gap_Concrete the upstream settle commits in block 3,
        after the tick past tIn = 2.
No wellformedness warnings. Results in out_core2.txt, out_core3.txt, out_core_bisect.txt.

Claim allowed: conditional, completion-aware per-hop deadline theorem for the
one-hop core model (honest parties, settle path), under bounded responsiveness
(D = 2), receipt/forwarder promptness and the CLTV gap; NowIsLatest is a
modelling restriction. Not claimed: arbitrary routes (composition not done),
the full model (modeldeadline3: witness/controls inconclusive), novelty
(literature comparison pending).
