# add: every lemma runs in its own Tamarin call through ../run_lemma.sh, which
# add: classifies the result (VERIFIED, FALSIFIED, INCOMPLETE, TIMEOUT,
# add: OUT_OF_MEMORY, ERROR) and appends a row with git revision, tool
# add: versions, flags, limits and result to results.tsv. Full logs: logs/.
# add: The lemma lists are read from lemmas.spthy (../list_lemmas.sh), so no
# add: count is hard-coded: `make count` prints them.
#
#   make                 both configurations, lemma by lemma
#   make regression      one --prove over the whole theory, both configurations
#   make summary         counts per result from results.tsv
#   make lemma L=No_Double_Publish [FLAGS=-D=LIVENESS]

TAMARIN ?= tamarin-prover
THEORY   = lightningfixb.spthy
RUN      = TAMARIN=$(TAMARIN) ../run_lemma.sh $(THEORY)
export LIMIT ?= 1800
export MEM   ?= 8G

SAFETY_LEMMAS   = $(shell ../list_lemmas.sh lemmas.spthy)
LIVENESS_LEMMAS = $(shell FLAG=LIVENESS ../list_lemmas.sh lemmas.spthy)

.PHONY: all verify safety liveness count regression lemma summary interactive clean

all: safety liveness
verify: all

count:
	@echo "declared in lemmas.spthy: $$(grep -c '^lemma' lemmas.spthy)"
	@echo "loaded without flags:     $(words $(SAFETY_LEMMAS))"
	@echo "loaded with -D=LIVENESS:  $(words $(LIVENESS_LEMMAS))"

safety:
	-@for L in $(SAFETY_LEMMAS); do $(RUN) $$L; done

liveness:
	-@for L in $(LIVENESS_LEMMAS); do $(RUN) $$L -D=LIVENESS; done

# Final regression check only: the whole theory in one call per configuration.
regression:
	LANG=C.UTF-8 $(TAMARIN) $(THEORY) --prove --derivcheck-timeout=600 +RTS -M$(MEM) -RTS > regression.log 2>&1; echo "exit $$?" >> regression.log
	LANG=C.UTF-8 $(TAMARIN) $(THEORY) -D=LIVENESS --prove --derivcheck-timeout=600 +RTS -M$(MEM) -RTS > regression_liveness.log 2>&1; echo "exit $$?" >> regression_liveness.log
	@for f in regression.log regression_liveness.log; do echo "$$f: $$(grep -cE '^  [A-Za-z_0-9]+ \(.*verified' $$f) verified, $$(grep -cE '^  [A-Za-z_0-9]+ \(.*(falsified|incomplete)' $$f) not verified, $$(tail -1 $$f)"; done

lemma:
	-@$(RUN) $(L) $(FLAGS)

summary:
	@tail -n +2 results.tsv | awk -F'\t' '{k=$$6" "$$7; r[k]=$$10} END {for (k in r) c[r[k]]++; for (x in c) printf "  %-14s %d\n", x, c[x]}'

interactive:
	LANG=C.UTF-8 $(TAMARIN) interactive .

clean:
	rm -rf logs results.tsv regression.log regression_liveness.log
