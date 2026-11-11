# add: attack search on a small model (attack_core.spthy). One lemma per call
# add: through ../run_lemma.sh; each line states the expected result.
#   make            everything below (seconds to minutes)
#   make summary
TAMARIN ?= tamarin-prover
export LIMIT ?= 1800
export MEM   ?= 8G
RUN = TAMARIN=$(TAMARIN) ../run_lemma.sh attack_core.spthy
ALL = -D=PROMPT_REFUND -D=PROMPT_CLAIM -D=GAP
HELPERS = Claimed_Once Refunded_Once Claim_Refund_Exclusive Refund_After_Expiry \
          Claim_Out_Teaches_F Stamp_Has_Tick

.PHONY: all verify witnesses attacks theorem summary clean
all: witnesses attacks theorem
verify: all

# The model can run: payment off-chain, on-chain, and refund (also with all assumptions).
witnesses:
	@fail=0; for L in Pay_Offchain_Witness Pay_Onchain_Witness Refund_Witness; do \
	  $(RUN) $$L || fail=1; $(RUN) $$L $(ALL) || fail=1; done; exit $$fail

# Attack search. VERIFIED = the loss trace exists.
attacks:
	@fail=0; \
	$(RUN) Forwarder_Loss || fail=1; \
	TAG=no-prompt-refund $(RUN) Forwarder_Loss -D=PROMPT_CLAIM -D=GAP || fail=1; \
	TAG=no-prompt-claim  $(RUN) Forwarder_Loss -D=PROMPT_REFUND -D=GAP || fail=1; \
	TAG=no-gap           $(RUN) Forwarder_Loss -D=PROMPT_REFUND -D=PROMPT_CLAIM || fail=1; \
	exit $$fail

# With all three assumptions the loss is impossible.
theorem:
	@fail=0; for L in $(HELPERS); do $(RUN) $$L $(ALL) || fail=1; done; \
	$(RUN) No_Forwarder_Loss $(ALL) || fail=1; \
	EXPECT=FALSIFIED $(RUN) Forwarder_Loss $(ALL) || fail=1; exit $$fail

summary:
	@../summary.sh results.tsv

clean:
	rm -rf logs results.tsv
