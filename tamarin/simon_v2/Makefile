TAMARIN ?= tamarin-prover
THEORY   = lightningfixb.spthy
RTS      = +RTS -M8G -RTS

.PHONY: all verify safety liveness lemma interactive clean

all: safety liveness

verify: all

# All lemmas without the liveness restrictions (50/50 verified).
safety:
	LANG=C.UTF-8 $(TAMARIN) $(THEORY) --prove $(RTS) > safety.log 2>&1
	@grep -E "^  [A-Za-z_]+ \(" safety.log | grep -E "verified|falsified|incomplete"

# All lemmas with -D=LIVENESS (51/51 verified).
liveness:
	LANG=C.UTF-8 $(TAMARIN) $(THEORY) -D=LIVENESS --prove $(RTS) > liveness.log 2>&1
	@grep -E "^  [A-Za-z_]+ \(" liveness.log | grep -E "verified|falsified|incomplete"

# One lemma, e.g. make lemma L=No_Double_Publish
lemma:
	LANG=C.UTF-8 $(TAMARIN) $(THEORY) --prove=$(L) $(RTS) 2>&1 | grep -E "^  $(L) \("

interactive:
	LANG=C.UTF-8 $(TAMARIN) interactive .

clean:
	rm -f safety.log liveness.log
