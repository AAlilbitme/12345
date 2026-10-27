TAMARIN ?= tamarin-prover
RTS      = --derivcheck-timeout=600 +RTS -M8G -RTS

THEOREM  = -D=LIVENESS -D=BOUND -D=GAP2   # all assumptions
ABLATION = -D=LIVENESS -D=GAP2            # without bounded responsiveness
GAPCTRL  = -D=LIVENESS -D=BOUND -D=GAP1   # gap tOut + 1 <= tIn (below D = 2)

# One hop (deadline_core.spthy)
ONE_SAFETY  = Settle_Commit_Correspondence Stamp_Between_Ticks \
              Request_Without_Commit Commit_Without_Receipt
ONE_THEOREM = Deadline_Per_Hop Deadline_Witness_Concrete Deadline_Witness_Consecutive

# Two forwarders (deadline_core2.spthy)
TWO_THEOREM = Deadline_Stamp_Per_Hop End_To_End_Two_Hops Two_Hop_Witness_Pinned Two_Hop_Witness_Consecutive_A

.PHONY: all verify one-hop two-hop one-safety one-theorem one-ablation one-gap \
        two-theorem two-gap clean

all: one-hop two-hop

verify: all

one-hop: one-safety one-theorem one-ablation one-gap

two-hop: two-theorem two-gap

# Correspondence, stamp invariant, request != commit, commit != receipt.
one-safety:
	LANG=C.UTF-8 $(TAMARIN) deadline_core.spthy $(addprefix --prove=,$(ONE_SAFETY)) $(RTS) > one_safety.log 2>&1
	@grep -E "^  [A-Za-z_]+ \(" one_safety.log | grep -E "verified|falsified"

# Per-hop deadline theorem and its witnesses.
one-theorem:
	LANG=C.UTF-8 $(TAMARIN) deadline_core.spthy $(THEOREM) $(addprefix --prove=,$(ONE_THEOREM)) $(RTS) > one_theorem.log 2>&1
	@grep -E "^  [A-Za-z_]+ \(" one_theorem.log | grep -E "verified|falsified"

# Control: without bounded responsiveness a counterexample exists ("verified" = trace found).
one-ablation:
	LANG=C.UTF-8 $(TAMARIN) deadline_core.spthy $(ABLATION) --prove=Ablation_Concrete $(RTS) > one_ablation.log 2>&1
	@grep -E "^  Ablation_Concrete \(" one_ablation.log

# Control: with a gap below D a counterexample exists ("verified" = trace found).
one-gap:
	LANG=C.UTF-8 $(TAMARIN) deadline_core.spthy $(GAPCTRL) --prove=Gap_Concrete $(RTS) > one_gap.log 2>&1
	@grep -E "^  Gap_Concrete \(" one_gap.log

# Composable per-hop theorem, end-to-end theorem over two forwarders, witnesses.
two-theorem:
	LANG=C.UTF-8 $(TAMARIN) deadline_core2.spthy $(THEOREM) $(addprefix --prove=,$(TWO_THEOREM)) $(RTS) > two_theorem.log 2>&1
	@grep -E "^  [A-Za-z_]+ \(" two_theorem.log | grep -E "verified|falsified"

# Control: with gaps below D the end-to-end claim fails ("verified" = trace found).
two-gap:
	LANG=C.UTF-8 $(TAMARIN) deadline_core2.spthy $(GAPCTRL) --prove=Two_Hop_Gap_Pinned $(RTS) > two_gap.log 2>&1
	@grep -E "^  Two_Hop_Gap_Pinned \(" two_gap.log

clean:
	rm -f one_*.log two_*.log
