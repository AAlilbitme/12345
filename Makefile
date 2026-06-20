TAMARIN   := tamarin-prover
TFLAGS    := --heuristic=c --derivcheck-timeout=0
LANG      := LANG=C.utf8 LC_ALL=C.utf8

.PHONY: all gaps value_conservation payment_channels clean

all: gaps value_conservation payment_channels

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

clean:
	@echo "Nothing to clean (Tamarin produces no build artifacts)"
