# Makefile -- thin wrapper around run.py, the single source of truth for which
# theories and lemmas are proved and with which per-file flags (seqdfs, etc.).
# Maintaining a parallel per-lemma list here caused drift, so this now delegates.
#
#   make            prove the whole suite (cltv_blocks, gaps, witnesses,
#                   t2b_attack, multihop) -- see run.py's FILES list
#   make FILE=multihop.spthy    prove a single theory
#   make nhop       prove the N-hop extension (not in run.py's default list)
#
# Requires: tamarin-prover on PATH, python3.

PY   := python3
LANG := LANG=C.utf8 LC_ALL=C.utf8

.PHONY: all suite nhop clean

all: suite

# Full core suite via run.py (handles per-file seqdfs and per-lemma OOM avoidance).
suite:
	$(LANG) $(PY) run.py $(FILE)

# The arbitrary-length extension is proved separately (not part of the core list).
nhop:
	$(LANG) $(PY) run.py multihop_nhop_fees.spthy

clean:
	@echo "Nothing to clean (Tamarin produces no build artifacts)"
