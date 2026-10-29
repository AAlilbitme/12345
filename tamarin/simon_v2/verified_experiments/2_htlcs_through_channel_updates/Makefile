# add: every lemma runs in its own Tamarin call through ../run_lemma.sh, which
# add: classifies the result (VERIFIED, FALSIFIED, INCOMPLETE, TIMEOUT,
# add: OUT_OF_MEMORY, ERROR) and appends a row with git revision, tool
# add: versions, flags, limits and result to results.tsv. Full logs: logs/.
#
#   make                 goal2 + helpers + safety (no flags)
#   make liveness        lemmas that exist only with -D=LIVENESS
#   make summary         counts per result from results.tsv
#   make lemma L=Hand_Payment [FLAGS=-D=LIVENESS]
#   LIMIT=3600 MEM=12G make ...   change time / memory limit per lemma

TAMARIN ?= tamarin-prover
THEORY   = lightningupd.spthy
RUN      = TAMARIN=$(TAMARIN) ../run_lemma.sh $(THEORY)
export LIMIT ?= 1800
export MEM   ?= 8G

# Goal 2: HTLC steps take effect only after a completed channel update.
# add: the last four are new (Add/Fulfil/Fail through channel updates, refund witness).
GOAL2  = Settle_Is_Channel_Update HTLC_Commit_Correspondence Hand_Payment \
         Add_Is_Channel_Update Fulfil_Needs_Committed_Add \
         Fail_Is_Channel_Update Refund_Path_Witness

# add: helper lemmas for the safety lemmas below (proof aids, not results).
HELPERS = Route_Made_Once Route_Has_Amount Paid_Has_Amount \
          Fulfilled_Out_Released Release_By_Creator

# Simon's safety lemmas (and ours), 50 in the configuration without flags.
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
         Punish_Enabled Offer_Requires_Invoice No_Double_Publish \
         Funding_Spent_Once Forward_Requires_Incoming \
         Settle_Requires_Receiver_Release Hop_Forwarded_Once \
         Forward_Excludes_Fulfill Receiver_Paid_At_Most_Offered \
         Settle_Excludes_Sender_Refund Sender_Pays_Invoice_Plus_Fees

# Lemmas that exist only with -D=LIVENESS.
LIVENESS = Cheating_Never_Pays Intermediary_Never_Loses_Under_Liveness \
           Payment_Atomicity_Under_Liveness Timeout_Race_Blocked \
           Forwarder_Claims_In_Time Forwarder_Refunds_In_Time \
           Intermediary_Recovers_Funds \
           Forwarder_Claims_In_Time_Committed Intermediary_Never_Loses_Committed \
           Claim_Gap_Witness   # add: goal-2 versions and the gap witness

.PHONY: all verify goal2 helpers safety liveness lemma summary check-count clean
SHELL = /bin/bash

all: goal2 helpers safety
verify: all

goal2:
	-@for L in $(GOAL2); do $(RUN) $$L; done

helpers:
	-@for L in $(HELPERS); do $(RUN) $$L; done

safety:
	-@for L in $(SAFETY); do $(RUN) $$L; done

# add: Hand_Payment first: it shows the liveness restrictions still allow a payment.
liveness:
	-@for L in Hand_Payment $(LIVENESS); do $(RUN) $$L -D=LIVENESS; done

lemma:
	-@$(RUN) $(L) $(FLAGS)

# add: check that GOAL2 + HELPERS + SAFETY is exactly what Tamarin loads
# add: without flags, and LIVENESS what it adds with -D=LIVENESS.
check-count:
	@diff <(echo $(GOAL2) $(HELPERS) $(SAFETY) | tr ' ' '\n' | sort) <(../list_lemmas.sh $(THEORY) lemmasupd.spthy | sort) && echo "Makefile lists match the theory (no flags)"
	@TAMARIN=$(TAMARIN) ../check_lemmas.sh $(THEORY) $(THEORY) lemmasupd.spthy
	@FLAG=LIVENESS TAMARIN=$(TAMARIN) ../check_lemmas.sh $(THEORY) $(THEORY) lemmasupd.spthy

summary:
	@echo "results.tsv (latest run of each lemma/flags):"
	@tail -n +2 results.tsv | awk -F'\t' '{k=$$6" "$$7; r[k]=$$10} END {for (k in r) c[r[k]]++; for (x in c) printf "  %-14s %d\n", x, c[x]}'

clean:
	rm -rf logs results.tsv
