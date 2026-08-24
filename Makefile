# Makefile -- thin wrapper around run.py, the single source of truth for which
# theories and lemmas are proved and with which per-file flags (seqdfs, etc.).
# Maintaining a parallel per-lemma list here caused drift, so this now delegates.
#
#   make            prove the whole suite (cltv_blocks, timeout, Clock,
#                   multihop, multihop_nhop) -- see run.py's FILES list
#   make FILE=multihop.spthy    prove a single theory
#   make channels   prove the archived standalone channel-lifecycle demo
#
# Requires: tamarin-prover on PATH, python3.

PY   := python3
LANG := LANG=C.utf8 LC_ALL=C.utf8

.PHONY: all suite channels clean

all: suite

# Full core suite via run.py (handles per-file seqdfs and per-lemma OOM avoidance).
suite:
	$(LANG) $(PY) run.py $(FILE)

# The standalone channel layer is fully subsumed by multihop.spthy's channel
# rules; kept only as a fast isolated demo, so it is proved on request.
channels:
	$(LANG) $(PY) run.py archive/PaymentChannels.spthy

clean:
	@echo "Nothing to clean (Tamarin produces no build artifacts)"
