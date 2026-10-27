# Verified experiments: Lightning models in Tamarin

Each numbered folder is self-contained: `cd` into it and run its main file.

## 1_final_verified_model/  (Simon's model + fixes)
| File | What |
|---|---|
| `lightningfixb.spthy` | Main file (includes the three below) |
| `modelfixb.spthy` | Simon's model + `'invoice'` tag, linear `FundingUnspent`, `<'commit', ptr, ...>` pattern in the publish rules |
| `tactics.spthy` | Simon's tactics + `offer_invoice` |
| `lemmas.spthy` | Simon's lemmas + 5 added (invoice origin, offer requires invoice, funding spent once, no double publish, `Payment_Base`) |
| `Makefile` | `make verify`: 51/51 verified, 52/52 with `-D=LIVENESS` |
| `simon_original_model.spthy` | Simon's original model, for comparison (not included by anything) |

## 2_htlcs_through_channel_updates/  (Simon's goal 2)
| File | What |
|---|---|
| `lightningupd.spthy` | Main file; prove named lemmas only (`--prove=...`), a full `--prove` does not finish |
| `modelupd.spthy` | `modelfixb` + HTLC steps that take effect only after a completed channel update; commit-based liveness restrictions |
| `lemmasupd.spthy` | `lemmas.spthy` without `Payment_Base` |
| `tactics.spthy` | Same as in folder 1 |

Verified: `Settle_Is_Channel_Update` (30 steps), `Hand_Payment` (83 steps), and 20 of Simon's safety lemmas (list in `notes/deadline_status.md`).

    tamarin-prover lightningupd.spthy --prove=Settle_Is_Channel_Update --prove=Hand_Payment --derivcheck-timeout=600

## 3_deadline_theorem/  (core models, standalone)
| File | What |
|---|---|
| `deadline_core.spthy` | One hop: theorem, witnesses, ablation and gap controls, invariants |
| `deadline_core2.spthy` | Two forwarders: composable per-hop theorem, end-to-end theorem, witnesses, gap control |

Flags: `-D=LIVENESS -D=BOUND -D=GAP2` (theorem), `-D=LIVENESS -D=GAP2` (ablation), `-D=LIVENESS -D=BOUND -D=GAP1` (gap control); no flags for the safety lemmas.

    tamarin-prover deadline_core.spthy -D=LIVENESS -D=BOUND -D=GAP2 --prove=Deadline_Per_Hop

## How to run

Requirements: Tamarin 1.10 and Maude. Always run from inside the folder.
`--derivcheck-timeout=600` avoids a spurious wellformedness warning (the
default 5 s derivation check times out on these models). Add
`+RTS -M8G -RTS` if Tamarin runs out of memory.

### 1_final_verified_model
    cd 1_final_verified_model
    make verify                  # both configurations (about 17 min on a laptop)
    make safety                  # without liveness: 51/51 verified
    make liveness                # with -D=LIVENESS: 52/52 verified
    make lemma L=No_Double_Publish

    # without make:
    tamarin-prover lightningfixb.spthy --prove --derivcheck-timeout=600
    tamarin-prover lightningfixb.spthy -D=LIVENESS --prove --derivcheck-timeout=600

### 2_htlcs_through_channel_updates
Prove named lemmas only; a full `--prove` does not finish.

    cd 2_htlcs_through_channel_updates
    make verify                  # goal-2 lemmas + the 20 verified safety lemmas
    make goal2                   # Settle_Is_Channel_Update, Hand_Payment
    make safety                  # the 20 safety lemmas that verify on this model
    make lemma L=Hand_Payment

    # without make:
    tamarin-prover lightningupd.spthy --prove=Settle_Is_Channel_Update --prove=Hand_Payment --derivcheck-timeout=600
    tamarin-prover lightningupd.spthy --prove=Ltk_Known_Implies_Compromised --derivcheck-timeout=600   # one of the 20 safety lemmas

### 3_deadline_theorem
    cd 3_deadline_theorem
    make verify                  # everything below
    make one-hop                 # one-safety, one-theorem, one-ablation, one-gap
    make two-hop                 # two-theorem, two-gap
    # controls print "verified" when the counterexample trace is found

    # without make:
    # one hop - safety (no flags)
    tamarin-prover deadline_core.spthy --prove=Settle_Commit_Correspondence --prove=Stamp_Between_Ticks --prove=Request_Without_Commit --prove=Commit_Without_Receipt
    # one hop - theorem and witnesses
    tamarin-prover deadline_core.spthy -D=LIVENESS -D=BOUND -D=GAP2 --prove=Deadline_Per_Hop --prove=Deadline_Witness_Concrete --prove=Deadline_Witness_Consecutive
    # one hop - controls (expected: trace found)
    tamarin-prover deadline_core.spthy -D=LIVENESS -D=GAP2 --prove=Ablation_Concrete
    tamarin-prover deadline_core.spthy -D=LIVENESS -D=BOUND -D=GAP1 --prove=Gap_Concrete

    # two hops - theorem and witnesses
    tamarin-prover deadline_core2.spthy -D=LIVENESS -D=BOUND -D=GAP2 --prove=End_To_End_Two_Hops --prove=Two_Hop_Witness_Pinned --prove=Two_Hop_Witness_Consecutive_A
    # two hops - gap control (expected: trace found)
    tamarin-prover deadline_core2.spthy -D=LIVENESS -D=BOUND -D=GAP1 --prove=Two_Hop_Gap_Pinned

Some of these take several minutes; run them one at a time.

## notes/
- `deadline_status.md`: all results, the agreed paper scope and its limitations.
- `related_work.md`: comparison with prior work and the claim wording.

Intermediate models, check theories, run scripts and logs are in the git history.
