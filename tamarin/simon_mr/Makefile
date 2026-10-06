# Tamarin verification for multiN_modified_extended.spthy
#
# Simon's MR model + tagged invoice + sanity lemmas + Skip_Requires_Compromise,
# Intermediary_Never_Loses_Strong, Offer_Requires_Invoice.
#
# Three groups:
#   * ALL_TRACES_LEMMAS : safety lemmas, proven automatically (--prove)
#   * AUTO_EXISTS_LEMMAS: exists-trace lemmas that --prove finds on its own
#   * REPLAY_LEMMAS     : exists-trace lemmas that need hand-saved proof scripts,
#                         replayed with --lemma (the file must contain the scripts)
#
# Each invocation re-runs source saturation (~90 s).  Groups are run in one
# invocation each to save time.  If your machine runs out of memory, use
# `make verify-one` instead (one lemma per run, capped memory).

TAMARIN    ?= tamarin-prover
FILE       ?= multiN_modified_extended.spthy
MEM        ?= 6G
# NB: no --derivcheck-timeout=0 -- the derivation checks then run unbounded
# and can exhaust memory; the default timeout is harmless.
FLAGS      := --quiet +RTS -M$(MEM) -RTS
LOG        := .tamarin-verify.log
export LANG := C.UTF-8

ALL_TRACES_LEMMAS := \
	state_update delayed_funds instant_funds settlement_is_traceable \
	No_Punishment_Without_Cheating Funds_Locked_Before_Update \
	Update_Requires_Negotiation Ltk_Known_Implies_Compromised \
	Invoice_Released_Once Preimage_Secret_Until_Released \
	Invoice_Has_Secret_Preimage HTLC_On_Opened_Channel \
	Fulfilled_Requires_Release Settle_Requires_Receiver_Release \
	Claim_Requires_Release Forward_Requires_Incoming \
	Redeem_Requires_Receiver_Release \
	Settle_Excludes_Sender_Refund Invoice_Authenticates_Settlement \
	Loss_Requires_Inaction Refund_Requires_Timeout \
	Intermediary_Never_Loses_Under_Liveness Payment_Atomicity_Under_Liveness \
	Timeout_Race_Blocked ForwardTimeGap OneOutcomePerHTLC \
	Fee_Only_On_Successful_Forward \
	Intermediary_Never_Loses_Strong \
	Offer_Requires_Invoice

AUTO_EXISTS_LEMMAS := \
	Protocol_execution Cooperative_Close_Execution \
	Distinct_Parties_Configuration Refund_Possible \
	Forged_Invoice_Requires_Key_Compromise \
	Sanity_Honest_Payment_Completes Sanity_Compromised_Intermediary_Can_Lose \
	Sanity_Atomic_Payment_Completes Multihop_Payment_Possible

REPLAY_LEMMAS := \
	Wormhole_Fee_Theft_Reachable

PROVE_ALL    := $(addprefix --prove=,$(ALL_TRACES_LEMMAS))
PROVE_EXISTS := $(addprefix --prove=,$(AUTO_EXISTS_LEMMAS))
LEMMA_REPLAY := $(addprefix --lemma=,$(REPLAY_LEMMAS))

# Exact match on Tamarin's summary line ("  <Lemma> (...): verified"), so that
# e.g. Intermediary_Never_Loses_Strong is not matched by a prefix.
define check
	@set -e; for L in $(1); do \
		grep -qE "^  $$L \(.*\): verified" $(LOG) \
			|| { echo "FAILED: $$L"; grep -E "^  $$L " $(LOG); exit 1; }; \
	done
endef

.PHONY: verify verify-all-traces verify-auto-exists verify-replay verify-one clean help

verify: verify-all-traces verify-auto-exists verify-replay
	@echo "==> All lemmas verified."

verify-all-traces:
	@echo "==> Proving $(words $(ALL_TRACES_LEMMAS)) all-traces lemmas (single run)"
	$(TAMARIN) $(FILE) $(PROVE_ALL) $(FLAGS) > $(LOG) 2>&1
	$(call check,$(ALL_TRACES_LEMMAS))
	@echo "==> All all-traces lemmas verified."

verify-auto-exists:
	@echo "==> Proving $(words $(AUTO_EXISTS_LEMMAS)) exists-trace lemmas (single run)"
	$(TAMARIN) $(FILE) $(PROVE_EXISTS) $(FLAGS) > $(LOG) 2>&1
	$(call check,$(AUTO_EXISTS_LEMMAS))
	@echo "==> All automatic exists-trace lemmas verified."

verify-replay:
	@echo "==> Replaying $(words $(REPLAY_LEMMAS)) saved exists-trace proofs (single run)"
	$(TAMARIN) $(FILE) $(LEMMA_REPLAY) $(FLAGS) < /dev/null > $(LOG) 2>&1
	$(call check,$(REPLAY_LEMMAS))
	@echo "==> All replayed exists-trace lemmas verified."

# Low-memory alternative: one lemma per invocation, 15 min each.
verify-one:
	@for L in $(ALL_TRACES_LEMMAS) $(AUTO_EXISTS_LEMMAS); do \
		r=$$(timeout 900 $(TAMARIN) $(FILE) --prove=$$L $(FLAGS) 2>&1 | grep -E "^  $$L "); \
		echo "$$L | $${r:-no result in 900 s}"; \
	done
	@for L in $(REPLAY_LEMMAS); do \
		r=$$($(TAMARIN) $(FILE) --lemma=$$L $(FLAGS) < /dev/null 2>&1 | grep -E "^  $$L "); \
		echo "$$L | $${r:-no result}"; \
	done

clean:
	rm -f $(LOG)

help:
	@echo "make verify            all three groups (default)"
	@echo "make verify-all-traces  $(words $(ALL_TRACES_LEMMAS)) safety lemmas"
	@echo "make verify-auto-exists $(words $(AUTO_EXISTS_LEMMAS)) exists-trace lemmas found by --prove"
	@echo "make verify-replay      $(words $(REPLAY_LEMMAS)) exists-trace lemmas with saved proofs"
	@echo "make verify-one         one lemma per run (use if memory runs out)"
	@echo "Options: FILE=..., MEM=4G"
