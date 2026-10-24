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

## Composition on the two-forwarder core model (deadline_core2.spthy)
Route S -p0-> F1 -p1-> F2 -p2-> R, expiries t0 > t1 > t2.
Helpers (safety config, [reuse], valid in every config): Delivery_Unique,
  Request_Unique, Commit_Unique, Request_Unique_Channel, Commit_Unique_Channel.
Under -D=LIVENESS -D=BOUND -D=GAP2:
  Deadline_Stamp_Per_Hop (composable: downstream commit stamp <= tOut and a tick
    past tIn => upstream commit stamp <= tIn, before that tick): verified (124).
  End_To_End_Two_Hops (receiver settle on p2 by t2, tick past t0 => settle on
    p0 by t0): verified (80).
  Two_Hop_Witness_Pinned: verified (48) - assumptions jointly satisfiable.
Under -D=LIVENESS -D=BOUND -D=GAP1:
  Two_Hop_Gap_Pinned: verified (37) - with gaps of 1 the settle on p0 commits
    only after a tick past t0.
Lemma-setup bug found and fixed on the way: Deadline_Stamp_Per_Hop was marked
[reuse] in every configuration; it is now only present under GAP2 and after the
existence lemmas (a reused lemma applies only to later ones).

Claim allowed: two-hop composition mechanically checked. Arbitrary finite routes
follow by induction on route length because Deadline_Stamp_Per_Hop has the same
premise/conclusion form at every hop (paper argument, not a Tamarin proof).
Not done: a two-hop ablation (the one-hop ablation already shows the bound is
needed), the deadline result on the full model, the literature comparison.

## Review P1 (clock abstraction) - results
- Stamp_Between_Ticks (Now(b) is emitted by every request, receipt and commit
  rule, and by no other rule): verified in deadline_core (23) and
  deadline_core2 (27). Every stamped event lies after Tick(b) and before any
  tick with a larger value.
- One hop: Deadline_Witness_Consecutive (ticks 1,2,3,4, no tick skipped or
  added; -D=LIVENESS -D=BOUND -D=GAP2) verified (20), after adding the
  channel-level helpers (Request_Unique_Channel 751, Commit_Unique_Channel 251,
  Commit_Unique 2) to deadline_core.
- Two hops: Two_Hop_Witness_Consecutive (ticks 1..6) TIMEOUT (45 min). Only the
  skipping-clock witness Two_Hop_Witness_Pinned (ticks 1,3,5,6) is verified.

Agreed wording: the theorem holds for every trace satisfying the clock and
liveness restrictions, including traces with skipped ticks. For one hop, a
consecutive-tick witness shows the restrictions are satisfiable under ordinary
unit-step block progression; for two hops, satisfiability is shown only with a
skipping clock. The theorem stays conditional on NowIsLatest and the three
assumptions. Novelty: "to our knowledge" (see related_work.md).

## Update: two-hop consecutive witness
Two_Hop_Witness_Consecutive_A (ticks 1..6, no tick skipped or added;
-D=LIVENESS -D=BOUND -D=GAP2) verified (35 steps, 10 s) with the tactic
facts_first (solve protocol facts first; assumption case splits and KU goals
last). Without the tactic: timeout at 45 min. (Variant B, splits_first, was
stopped after A succeeded; no result.)

Updated wording: the theorem holds for every trace satisfying the clock and
liveness restrictions, including traces with skipped ticks. Consecutive-tick
witnesses for one hop and for two hops show that the restrictions are
satisfiable under ordinary unit-step block progression.
