# Run every verified experiment and collect all results in one log.
#   make                  -> final model + goal 2, results in results.log
#   make deadline         -> deadline theorem folder (appends to results.log)
#   make TAMARIN=/path/to/tamarin-prover
# make takes about 1.5-2.5 h on a laptop (folder 1 about 20 min, folder 2 about
# 1-2 h). Each folder also writes its own detailed logs.

TAMARIN ?= tamarin-prover
LOG      = results.log

.PHONY: all final htlc deadline clean

all:
	@echo "Verified experiments - started $$(date)" > $(LOG)
	@$(MAKE) --no-print-directory final htlc
	@echo "" >> $(LOG); echo "Finished $$(date)" >> $(LOG)
	@echo ""; echo "All results: $(CURDIR)/$(LOG)"

final:
	@echo "" >> $(LOG); echo "== 1_final_verified_model (safety, then -D=LIVENESS) - $$(date)" | tee -a $(LOG)
	@$(MAKE) --no-print-directory -C 1_final_verified_model verify TAMARIN=$(TAMARIN) 2>&1 | grep -E "verified|falsified|incomplete" | tee -a $(LOG)

htlc:
	@echo "" >> $(LOG); echo "== 2_htlcs_through_channel_updates (goal-2 lemmas, safety lemmas, helpers + formerly timed-out lemmas) - $$(date)" | tee -a $(LOG)
	@$(MAKE) --no-print-directory -C 2_htlcs_through_channel_updates verify TAMARIN=$(TAMARIN) 2>&1 | grep -E "verified|falsified" | tee -a $(LOG)

deadline:
	@echo "" >> $(LOG); echo "== 3_deadline_theorem (controls: \"verified\" = counterexample found) - $$(date)" | tee -a $(LOG)
	@$(MAKE) --no-print-directory -C 3_deadline_theorem verify TAMARIN=$(TAMARIN) 2>&1 | grep -E "verified|falsified" | tee -a $(LOG)

clean:
	rm -f $(LOG)
	$(MAKE) -C 1_final_verified_model clean
	$(MAKE) -C 2_htlcs_through_channel_updates clean
	$(MAKE) -C 3_deadline_theorem clean
