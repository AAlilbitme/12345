TAMARIN   := tamarin-prover
TFLAGS    := --heuristic=c --derivcheck-timeout=0
LANG      := LANG=C.utf8 LC_ALL=C.utf8

.PHONY: all gaps value_conservation payment_channels multihop clean

all: gaps value_conservation payment_channels multihop t2b_attack cltv_blocks

# ---------------------------------------------------------------------------
# gaps.spthy -- 11 lemmas, proved sequentially to avoid OOM
# ---------------------------------------------------------------------------
gaps:
	@echo "=== gaps.spthy ==="
	$(LANG) $(TAMARIN) gaps.spthy --prove=HTLC_Needs_Open_Channel          $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) gaps.spthy --prove=No_HTLC_After_Close               $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) gaps.spthy --prove=Claim_Window_Exists               $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) gaps.spthy --prove=Transitive_Preimage_Before_Upstream_Deadline $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) gaps.spthy --prove=Two_Hop_Flow_Possible             $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) gaps.spthy --prove=Loss_Implies_Skipped_Claim        $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) gaps.spthy --prove=Outcome_Exclusive                 $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) gaps.spthy --prove=Redeem_Reachable                  $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) gaps.spthy --prove=Refund_Reachable                  $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) gaps.spthy --prove=Honest_Flow_Possible              $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) gaps.spthy --prove=Timed_Refund_Reachable            $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"

# ---------------------------------------------------------------------------
# value_conservation.spthy -- 3 lemmas, proved sequentially to avoid OOM
# ---------------------------------------------------------------------------
value_conservation:
	@echo "=== value_conservation.spthy ==="
	$(LANG) $(TAMARIN) value_conservation.spthy --prove=Forwarding_Possible        $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) value_conservation.spthy --prove=Fee_Conservation_Per_Hop   $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) value_conservation.spthy --prove=Value_Conserved_End_To_End $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"

# ---------------------------------------------------------------------------
# PaymentChannels.spthy -- 8 lemmas, can run all at once
# ---------------------------------------------------------------------------
payment_channels:
	@echo "=== PaymentChannels.spthy ==="
	$(LANG) $(TAMARIN) PaymentChannels.spthy --prove $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"

# ---------------------------------------------------------------------------
# multihop.spthy -- 28 lemmas, proved sequentially to avoid OOM
# ---------------------------------------------------------------------------
multihop:
	@echo "=== multihop.spthy ==="
	$(LANG) $(TAMARIN) multihop.spthy --prove=state_update                    $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=delayed_funds                   $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=instant_funds                   $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=settlement_is_traceable         $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Protocol_execution              $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=No_Punishment_Without_Cheating  $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Cooperative_Close_Execution     $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Funds_Locked_Before_Update      $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Update_Requires_Negotiation     $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Ltk_Known_Implies_Compromised   $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Invoice_Released_Once           $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Multihop_Payment_Possible       $(TFLAGS) --stop-on-trace=SEQDFS 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Distinct_Parties_Configuration  $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Refund_Possible                 $(TFLAGS) --stop-on-trace=SEQDFS 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Preimage_Secret_Until_Released  $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Invoice_Has_Secret_Preimage     $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=HTLC_On_Opened_Channel          $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Settle_Requires_Receiver_Release $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Forward1_Requires_Offer         $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Forward2_Requires_Forward1      $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Fulfill_Requires_Forward2       $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Claim_Requires_Release          $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Settle_Excludes_Sender_Refund   $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Invoice_Authenticates_Settlement $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Forged_Invoice_Requires_Key_Compromise $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Loss_Requires_Inaction          $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Refund_Requires_Timeout         $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Not_Refunded_If_Redeemed         $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Intermediary_Never_Loses_Under_Liveness $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Forward1_Requires_Offer_Honest        $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Forward2_Requires_Forward1_Honest     $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Fulfill_Requires_Forward2_Honest      $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=Payment_Atomicity_Under_Liveness      $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) multihop.spthy --prove=T2b_Counterexample_Blocked           $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"

# ---------------------------------------------------------------------------
# t2b_attack.spthy -- counterexample theory showing T2b is load-bearing
# ---------------------------------------------------------------------------
t2b_attack:
	@echo "=== t2b_attack.spthy ==="
	$(LANG) $(TAMARIN) t2b_attack.spthy --prove=Early_Timeout_Race $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"

# ---------------------------------------------------------------------------
# cltv_blocks.spthy -- 3 lemmas proving CLTV-delta inequality from block arithmetic
# ---------------------------------------------------------------------------
cltv_blocks:
	@echo "=== cltv_blocks.spthy ==="
	$(LANG) $(TAMARIN) cltv_blocks.spthy --prove=CLTV_Gap_Is_Positive    $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) cltv_blocks.spthy --prove=Claim_Window_Nonempty   $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"
	$(LANG) $(TAMARIN) cltv_blocks.spthy --prove=Staggered_Path_Safe     $(TFLAGS) 2>&1 | grep -E "verified|falsified|incomplete"

clean:
	@echo "Nothing to clean (Tamarin produces no build artifacts)"
