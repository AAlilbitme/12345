# Ground truth for the red-pen update of the paper draft (Tarmin_LN_7.pdf)

## The decision
The paper is re-anchored to the **csf_final** artefact, which Sana (co-author, the
person we work for) has verified on their own laptop.  Paper text that describes an
older model lineage must be corrected in red or struck through.

csf_final files (read them; they are the ONLY source of truth for model claims):
- /home/user/12345/tamarin/final/lightning.spthy      main model (channel layer + multi-hop routing + wormhole)
- /home/user/12345/tamarin/final/lightning_aux.spthy  five small auxiliary models, one per flag:
  -D=PTLC (countermeasure), -D=HTLC (baseline), -D=CLOCK, -D=CLTV, -D=TIMEOUT
- /home/user/12345/tamarin/final/Makefile             `make all` = verify + general + aux + necessity
- /home/user/12345/tamarin/final/results.txt
- Convenience extracts (same content, proofs omitted):
  scratchpad/paper/csf_final_lemmas.txt (all restriction + lemma statements, with #ifdef guards)
  scratchpad/paper/csf_final_rules.txt  (all 37 rules of lightning.spthy, exact text)

Older lineage described by the draft (NOT csf_final): multihop.spthy / multihop_modified.spthy
(3 fixed hops, HTLCForwarded1/HTLCForwarded2, Free(ptr), amounts chained hop to hop) and
Modif.spthy (abstract N-hop theory).  The orange "AI:" boxes in the draft describe yet another
merge ("Lightning.spthy" with TickOnce / TicksInOrder / ExpiryBlockReached /
ForwarderResolvesInTime, "46 all-traces + 8 exists-trace") which is ALSO not csf_final.

## Verified results (Tamarin 1.10; all reproduced on Sana's laptop, MEM=6G)
- `make verify` (lightning.spthy, full model): ALL 55 lemmas verified
  = 32 all-traces safety lemmas + 13 hop-bypass lemmas (First_Hop / Second_Hop /
  Hop3..Hop6_Skip_Requires_Compromise + 7 helpers) + 9 exists-trace lemmas (found automatically)
  + 1 exists-trace lemma replayed from a saved proof (Wormhole_Fee_Theft_Reachable, 116-step proof).
- `make general` (lightning.spthy -D=GENERAL -D=NO_IMC -D=NO_OTF -D=NO_RBT -D=NECESSITY): 24/24 verified,
  ending with Any_Hop_Skip_Requires_Compromise (7 steps).  Proven with the three liveness
  restrictions removed; removing restrictions only adds traces, so the all-traces statement
  also holds in the full model (trace inclusion).  Every [reuse] lemma it uses is re-proved in that mode.
- `make aux` (lightning_aux.spthy): 21/21 verified
  PTLC: Honest_Payment_Completes (E,10), Colluders_Present_Payment_Completes (E,14),
        No_Wormhole_Around_Honest_Hop (A,25), Control_Refund_Of_H2_Outgoing (E,6),
        Control_Wormhole_If_H2_Compromised (E,18)
  HTLC baseline: Honest_Payment_Completes (E,10), Colluders_Present_Payment_Completes (E,8),
        Wormhole_Around_Honest_Hop (E,12)  -- attack reachable without PTLC
  CLOCK: HTLC_Needs_Open_Channel (A,36), No_HTLC_After_Close (A,367), Claim_Window_Exists (A,79),
        Transitive_Preimage_Before_Upstream_Deadline (A,187), Loss_Implies_Skipped_Claim (A,861),
        Outcome_Exclusive (A,2), Redeem_Reachable (E,7), Refund_Reachable (E,7), Honest_Flow_Possible (E,14)
  CLTV: CLTV_Gap_Is_Positive (A,2), Claim_Window_Nonempty (A,2), Staggered_Path_Safe (A,2)
  TIMEOUT: Early_Timeout_Race (E,6)
  (A = all-traces, E = exists-trace, number = proof steps)
- `make necessity` (one liveness restriction removed per row; 600 s limit per check):
                     ForwardTimeGap  Timeout_Race_Blocked  INL_Under_Liveness  INL_Strong  Payment_Atomicity
     no T3 (IMC)     verified(6)     verified(4)           no result           no result   no result
     no T2b (OTF)    no result       verified(4)           verified(4)         verified(4) no result
     no T1 (RBT)     verified(6)     verified(4)           verified(4)         verified(4) verified(10)
  plus Necessity_IMC_Honest_Intermediary_Loses (exists-trace, -D=NO_IMC): verified (28 steps)
  = a concrete trace where an honest intermediary loses money once T3 is removed.
  Conclusions allowed: T3 is necessary for intermediary safety (counterexample).  T1 is not
  needed by any of these five liveness lemmas.  T2b is not needed for intermediary safety.
  "no result" means neither proof nor attack within 600 s: claim NOTHING from those cells.
- Caveats that must be stated: Tamarin 1.10 reports Maude 3.2 as unsupported (results were
  obtained with it); the general theorem assumes one offer per payment hash; the general
  theorem's conclusion says SOME party's key was compromised (it does not say which, or when).

## Key model facts of csf_final (check against the files before using)
- One theory for channel layer + routing.  Channel layer as in the draft: Update_State,
  Revoke_Old_Secret (persistent !RevokedSecret + linear RevokedCommitmentUnspent),
  Publish_Current_A/B, Claim_Funds_A/B, Publish_Revoked_A/B, Punish_A/B, Honest_Close, ...
- Routing: Sender_Offer_HTLC, Forward_HTLC (ONE generic rule for every hop, any route length),
  Receiver_Create_Invoice, Receiver_Fulfill_HTLC, Intermediary_Settle, Sender_Settle,
  Open_Timeout, Sender_Timeout_Refund, Intermediary_Timeout_Refund, AttackerSkip, Compromise_Ltk.
- Per-channel slot is `Mutex(ptr)` (draft says Free(ptr)); it is consumed when an HTLC is
  added and given back when that HTLC resolves (settle or refund), so channels are reusable.
- Action fact is `HTLCForwarded(Me, Prev, Next, ptrIn, ptrOut, y)` (draft: HTLCForwarded1/2, ForwardHTLC).
  Refunds: `Refunded(Up, ptr, y)`.  Invoice is tagged `<'invoice', R, S, y>` and InvoiceCreated(R, S, y) has NO amount.
- Amounts: Forward_HTLC reads In(%vIn), In(%fee), In(%vOut) and enforces Eq(%vIn, %vOut %+ %fee)
  per hop.  Sender_Offer_HTLC, the invoice and Route carry NO amount, so amounts are NOT chained
  along the path.  Therefore these draft lemmas do NOT exist in csf_final and their claims must be
  struck or reworded: Fee_Conservation_Hop1/2, Fee_Strictly_Positive_Hop1/2,
  EndToEnd_Value_Conservation, Receiver_Paid_Invoice_Amount, Fees_Charged_On_Path_Possible,
  Wormhole_Steals_Exactly_The_Fees, Honest_Intermediary_Refunds (csf_final has Refund_Possible,
  a different statement), Forward1_Requires_Offer / Forward2_Requires_Forward1 /
  Fulfill_Requires_Forward2 (+ _Honest variants), Multihop_Payment_Possible.
  Per-hop "incoming = outgoing + fee" is still true by construction (Eq restriction in Forward_HTLC).
- Replacements in csf_final: Forward_Requires_Incoming (any hop), Redeemed_Source, Fulfilled_Source,
  Multihop_Routing_Reachable, Sanity_Atomic_Payment_Completes, Sanity_Honest_Payment_Completes,
  Fee_Only_On_Successful_Forward, Intermediary_Never_Loses_Strong.
- Same names, changed statement shape (copy the csf_final statement): Payment_Atomicity_Under_Liveness,
  Intermediary_Never_Loses_Under_Liveness, Invoice_Authenticates_Settlement, Preimage_Secret_Until_Released,
  Forged_Invoice_Requires_Key_Compromise, Invoice_Released_Once, HTLC_On_Opened_Channel,
  Claim_Requires_Release, Settle_Requires_Receiver_Release, Settle_Excludes_Sender_Refund,
  Refund_Requires_Timeout, Loss_Requires_Inaction, Timeout_Race_Blocked, Wormhole_Fee_Theft_Reachable.
- Restrictions (9): Equality, Inequality, OneResolutionPerHTLC, OneHTLCPerHashPerChannel,
  OneTimeoutPerPtr, OneChannelPerPtr, and the three liveness ones mapping to the draft's names:
  T1 = RedeemBeforeTimeout, T2b = OutgoingTimesOutFirst, T3 = IntermediaryMustClaim.
  T2a (ForwardTimeGap) is NOT a restriction in csf_final: it is a proven lemma (derived from T2b).
  This answers Simon's margin question on page 6 ("Can't it simply be proven from T2b?") -- yes.
- Wormhole: AttackerSkip lets two compromised parties (ExitAtt, EntryAtt) on the same payment
  relay the preimage x around the parties between them.  Wormhole_Fee_Theft_Reachable is a
  5-party trace Alice -> Att1 -> Indiana -> Att2 -> Bob: Alice and Bob and Indiana are not
  compromised, Indiana (honest) forwards, is refunded on its outgoing channel and earns no fee,
  while Alice settles and Bob is paid.  (Draft Fig. 4 shows a 4-party, 3-hop version with Alice/Carol colluding.)
- New results the draft does not mention (the CSF contribution):
  Skipped_Requires_Compromise; First_Hop / Second_Hop / Hop3..Hop6_Skip_Requires_Compromise
  (no single-offer premise); Any_Hop_Skip_Requires_Compromise (any route length; single-offer
  premise; helper chain Forward_Parent, Hop_Redeem_Propagates, Sender_Channel_Redeemed, Root_First,
  Next_Is_Child, Route_Redeemed_Gen, Route_Redeemed_No_Compromise); ForwardTimeGap as a lemma;
  Necessity_IMC_Honest_Intermediary_Loses; PTLC No_Wormhole_Around_Honest_Hop vs HTLC
  Wormhole_Around_Honest_Hop.
- PTLC model (lightning_aux.spthy -D=PTLC): fixed route S -> H1 -> H2 -> H3 -> R; each hop's lock
  is derived from the next one by a hash chain s_in = h(<s_out, t>) with a per-hop fresh tweak t
  (symbolic stand-in for adaptor-signature points, Malavolta et al. NDSS 2019 [6]).  Read the file.
- Related work to add (real papers, safe to cite): A. Kiayias and O. S. T. Litos, "A Composable
  Security Treatment of the Lightning Network", IEEE CSF 2020 (same venue: must be positioned
  against); G. Malavolta et al., NDSS 2019 (already [6]: source of the wormhole attack and of the
  PTLC/AMHL fix).  Do not invent any other citation.

## Who is who
Sana = the user (co-author).  Simon = co-author (green margin comments).  Sana's comments are blue.
Orange "AI:" boxes = earlier AI suggestions inside the draft.  Do not strike co-author margin comments.
