TAMARIN ?= tamarin-prover
THEORY   = lightningupd.spthy
RTS      = --derivcheck-timeout=600 +RTS -M8G -RTS

# Goal 2: HTLC steps take effect only after a completed channel update.
GOAL2  = Settle_Is_Channel_Update HTLC_Commit_Correspondence Hand_Payment

# Simon's safety lemmas (and ours) that verify on this model: 42 of 50. The
# other 8 time out, so a full --prove does not finish.
SAFETY = state_update delayed_funds instant_funds settlement_is_traceable \
         No_Punishment_Without_Cheating Funds_Locked_Before_Update \
         Update_Requires_Negotiation OneOutcomePerHTLC \
         Ltk_Known_Implies_Compromised Invoice_Released_Once \
         Preimage_Secret_Until_Released Invoice_Has_Secret_Preimage \
         HTLC_On_Opened_Channel Fulfilled_Requires_Release \
         Settle_Requires_Outgoing_Redeemed Fee_Only_On_Successful_Forward \
         Claim_Excludes_Refund Redeem_Excludes_Refund \
         Receiver_Paid_Invoice_Amount ForwardTimeGap Claim_Requires_Release \
         Redeem_Requires_Receiver_Release Invoice_Authenticates_Settlement \
         Refund_Requires_Timeout Forward_Expiry_From_Upstream \
         Fee_Requires_Forward Loss_Requires_Inaction \
         Forward_Amount_From_Upstream Expiry_Unique \
         Amount_Decreases_Along_Route Fee_Is_Amount_Difference \
         Offer_Precedes_Forwards Redeem_Reveals Expiry_Below_First_Hop \
         Incoming_Resolved_By_Claim_Or_Timeout Outgoing_Preimage_Kept \
         Collect_Enabled Refund_Enabled Invoice_Signature_Origin \
         Punish_Enabled Offer_Requires_Invoice No_Double_Publish

# add: helper lemmas (in lightningupd.spthy) and the five lemmas that used to
# add: time out (Funding_Spent_Once takes 1-2 h); run one by one. Route_Made_Once needs --bound=6.
HELPERS = Release_By_Creator Fulfilled_Out_Released Paid_Has_Amount Route_Has_Amount
FIXED   = Funding_Spent_Once Forward_Requires_Incoming Settle_Requires_Receiver_Release \
          Hop_Forwarded_Once Forward_Excludes_Fulfill Receiver_Paid_At_Most_Offered \
          Settle_Excludes_Sender_Refund Sender_Pays_Invoice_Plus_Fees

.PHONY: all verify goal2 safety fixed each lemma clean

all: goal2 safety fixed

# add: helpers, then the five formerly timed-out lemmas, one call each.
fixed:
	@LANG=C.UTF-8 $(TAMARIN) $(THEORY) --prove=Route_Made_Once --bound=6 $(RTS) 2>&1 | grep -E "^  Route_Made_Once \("
	@for L in $(HELPERS) $(FIXED); do \
	  LANG=C.UTF-8 $(TAMARIN) $(THEORY) --prove=$$L $(RTS) 2>&1 | grep -E "^  $$L \("; \
	done

verify: all

# The goal-2 lemmas (3/3 verified).
goal2:
	LANG=C.UTF-8 $(TAMARIN) $(THEORY) $(addprefix --prove=,$(GOAL2)) $(RTS) > goal2.log 2>&1
	@grep -E "^  [A-Za-z_]+ \(" goal2.log | grep -E "verified|falsified"

# The 42 safety lemmas that verify on this model.
safety:
	LANG=C.UTF-8 $(TAMARIN) $(THEORY) $(addprefix --prove=,$(SAFETY)) $(RTS) > safety.log 2>&1
	@grep -E "^  [A-Za-z_]+ \(" safety.log | grep -E "verified|falsified"

# Every lemma of the theory, one Tamarin call each, with a time limit per lemma
# (LIMIT seconds, default 900). Results are collected in each.txt as
# verified / falsified / TIMEOUT. Takes hours: about 60 lemmas.
LIMIT ?= 900
each:
	@: > each.txt
	@for L in $$(grep -h "^lemma" $(THEORY) lemmasupd.spthy | sed -E 's/^lemma ([A-Za-z_0-9]+).*/\1/'); do \
	  r=$$(LANG=C.UTF-8 timeout $(LIMIT) $(TAMARIN) $(THEORY) --prove=$$L $(RTS) 2>&1 | grep -E "^  $$L \("); \
	  echo "$${r:-  $$L: TIMEOUT ($(LIMIT)s)}" | tee -a each.txt; \
	done

# One lemma, e.g. make lemma L=Hand_Payment
lemma:
	LANG=C.UTF-8 $(TAMARIN) $(THEORY) --prove=$(L) $(RTS) 2>&1 | grep -E "^  $(L) \("

clean:
	rm -f goal2.log safety.log each.txt
