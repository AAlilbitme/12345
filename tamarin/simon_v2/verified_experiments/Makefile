# Run the verified experiments, one Tamarin call per lemma.
#   make                  final model + goal 2, summary in results.log
#   make deadline         deadline theorem folder (appends to results.log)
#   make TAMARIN=/path/to/tamarin-prover LIMIT=3600 MEM=12G
# add: each folder keeps results.tsv (one row per lemma run: git revision, tool
# add: versions, flags, limits, result) and full logs in logs/. A lemma counts
# add: only if its result is VERIFIED; TIMEOUT / OUT_OF_MEMORY / ERROR are
# add: reported as such, never as proofs.

TAMARIN ?= tamarin-prover
export LIMIT ?= 1800
export MEM   ?= 8G
LOG      = results.log

.PHONY: all final htlc deadline clean

all:
	@echo "Verified experiments - started $$(date)" > $(LOG)
	@$(MAKE) --no-print-directory final htlc
	@echo "" >> $(LOG); echo "Finished $$(date)" >> $(LOG)
	@echo ""; echo "All results: $(CURDIR)/$(LOG)"

final:
	@echo "" >> $(LOG); echo "== 1_final_verified_model - $$(date)" | tee -a $(LOG)
	@$(MAKE) --no-print-directory -C 1_final_verified_model count verify summary TAMARIN=$(TAMARIN) 2>&1 | tee -a $(LOG)

htlc:
	@echo "" >> $(LOG); echo "== 2_htlcs_through_channel_updates - $$(date)" | tee -a $(LOG)
	@$(MAKE) --no-print-directory -C 2_htlcs_through_channel_updates verify liveness summary TAMARIN=$(TAMARIN) 2>&1 | tee -a $(LOG)

deadline:
	@echo "" >> $(LOG); echo "== 3_deadline_theorem (controls: VERIFIED = counterexample found) - $$(date)" | tee -a $(LOG)
	@$(MAKE) --no-print-directory -C 3_deadline_theorem verify summary TAMARIN=$(TAMARIN) 2>&1 | tee -a $(LOG)

clean:
	rm -f $(LOG)
	$(MAKE) -C 1_final_verified_model clean
	$(MAKE) -C 2_htlcs_through_channel_updates clean
	$(MAKE) -C 3_deadline_theorem clean
