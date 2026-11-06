# Makefile -- thin wrapper around run.py, the single source of truth for which
# theories and lemmas are proved and with which per-file flags (seqdfs, etc.).
# Maintaining a parallel per-lemma list here caused drift, so this now delegates.
#
#   make            prove the whole suite (Cltv, timeout, Clock,
#                   multihop, Modif) -- see run.py's FILES list
#   make FILE=multihop.spthy    prove a single theory
#   make channels   prove the standalone channel-lifecycle demo
#
# Requires: tamarin-prover on PATH, python3.

PY   := python3
LANG := LANG=C.utf8 LC_ALL=C.utf8

.PHONY: all suite channels clean

all: suite

# Full core suite via run.py (handles per-file seqdfs and per-lemma OOM avoidance).
suite:
	$(LANG) $(PY) run.py $(FILE)

# payment_channels.spthy's channel layer is fully subsumed by multihop.spthy's;
# kept as a fast isolated demo (and as the pre-fix exhibit for the revoked-
# commitment single-spend finding), so it is proved on request rather than
# in the default suite.
channels:
	$(LANG) $(PY) run.py payment_channels.spthy

clean:
	@echo "Nothing to clean (Tamarin produces no build artifacts)"
