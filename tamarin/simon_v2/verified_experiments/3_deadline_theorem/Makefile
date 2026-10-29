# add: every lemma runs in its own Tamarin call through ../run_lemma.sh (result
# add: classification + metadata in results.tsv, full logs in logs/).
# add: Three kinds of runs, kept apart:
# add:   theorem  - universal lemmas, never bounded
# add:   witness  - exists-trace lemmas showing the assumptions are satisfiable
# add:   control  - exists-trace counterexamples: VERIFIED here means the
# add:              counterexample trace WAS found (the property fails without
# add:              the assumption), as intended.
#
#   make                 one-hop then two-hop
#   make summary         counts per result from results.tsv

TAMARIN ?= tamarin-prover
export LIMIT ?= 1800
export MEM   ?= 8G
RUN1 = TAMARIN=$(TAMARIN) ../run_lemma.sh deadline_core.spthy
RUN2 = TAMARIN=$(TAMARIN) ../run_lemma.sh deadline_core2.spthy

THEOREM  = -D=LIVENESS -D=BOUND -D=GAP2   # all assumptions
ABLATION = -D=LIVENESS -D=GAP2            # without bounded responsiveness
GAPCTRL  = -D=LIVENESS -D=BOUND -D=GAP1   # gap tOut + 1 <= tIn (below D = 2)

# One hop (deadline_core.spthy)
ONE_SAFETY  = Settle_Commit_Correspondence Stamp_Between_Ticks \
              Request_Without_Commit Commit_Without_Receipt
ONE_THEOREM = Deadline_Per_Hop
ONE_WITNESS = Deadline_Witness_Concrete Deadline_Witness_Consecutive

# Two forwarders (deadline_core2.spthy)
TWO_THEOREM = Deadline_Stamp_Per_Hop End_To_End_Two_Hops
TWO_WITNESS = Two_Hop_Witness_Pinned Two_Hop_Witness_Consecutive_A

.PHONY: all verify one-hop two-hop lemma summary clean

all: one-hop two-hop
verify: all

one-hop:
	-@for L in $(ONE_SAFETY); do $(RUN1) $$L; done
	-@for L in $(ONE_THEOREM) $(ONE_WITNESS); do $(RUN1) $$L $(THEOREM); done
	-@$(RUN1) Ablation_Concrete $(ABLATION)
	-@$(RUN1) Gap_Concrete $(GAPCTRL)

# add: the two-hop composition is run only after the one-hop theorem verified
# add: at the SAME revision (no uncommitted changes) and with the same flags.
REV = $(shell git rev-parse --short HEAD)$(shell git diff --quiet -- . || echo +dirty)
two-hop:
	@awk -F'\t' -v rev="$(REV)" -v fl="$(strip $(THEOREM))" '$$2==rev && $$6=="Deadline_Per_Hop" && $$7==fl && $$10=="VERIFIED" {ok=1} END {exit !ok}' results.tsv 2>/dev/null \
	  || { echo "Deadline_Per_Hop not VERIFIED at revision $(REV) with $(strip $(THEOREM)): run make one-hop first"; exit 1; }
	-@for L in $(TWO_THEOREM) $(TWO_WITNESS); do $(RUN2) $$L $(THEOREM); done
	-@$(RUN2) Two_Hop_Gap_Pinned $(GAPCTRL)

# One lemma, e.g. make lemma F=deadline_core.spthy L=Deadline_Per_Hop FLAGS="-D=LIVENESS -D=BOUND -D=GAP2"
lemma:
	-@TAMARIN=$(TAMARIN) ../run_lemma.sh $(F) $(L) $(FLAGS)

summary:
	@tail -n +2 results.tsv | awk -F'\t' '{k=$$5" "$$6" "$$7; r[k]=$$10} END {for (k in r) c[r[k]]++; for (x in c) printf "  %-14s %d\n", x, c[x]}'

clean:
	rm -rf logs results.tsv
