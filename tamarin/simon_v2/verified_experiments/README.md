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

Lemma counts: `lemmas.spthy` declares 58 lemmas. Some sit in `#ifdef LIVENESS ... #else ... #endif` blocks, so 51 are loaded without flags and 52 with `-D=LIVENESS` (45 in both, 6 only without the flag, 7 only with it). All loaded lemmas verify in each configuration.
| `simon_original_model.spthy` | Simon's original model, for comparison (not included by anything) |

## 2_htlcs_through_channel_updates/  (Simon's goal 2)
| File | What |
|---|---|
| `lightningupd.spthy` | Main file; prove named lemmas only (`--prove=...`), a full `--prove` does not finish |
| `modelupd.spthy` | `modelfixb` + HTLC steps that take effect only after a completed channel update; commit-based liveness restrictions |
| `lemmasupd.spthy` | `lemmas.spthy` without `Payment_Base` |
| `tactics.spthy` | Same as in folder 1 |

Results (Tamarin 1.10, one lemma per call, 12 GB heap; every run is recorded in `results.tsv` with git revision, versions, flags, limits, result, steps, time and peak memory). Nothing is falsified except the gap witness, whose falsification is the expected result.

- **Goal 2, no flags (7/7 verified):** `Settle_Is_Channel_Update` (30 steps), `HTLC_Commit_Correspondence` (10), `Hand_Payment` (83), `Add_Is_Channel_Update` (8), `Fulfil_Needs_Committed_Add` (7), `Fail_Is_Channel_Update` (170), `Refund_Path_Witness` (32, exists-trace, pinned trace).
- **Safety, no flags (50/50 verified)**, plus 5 helper lemmas (all verified, no `--bound`): `Route_Made_Once` (146), `Route_Has_Amount` (74), `Paid_Has_Amount` (6), `Fulfilled_Out_Released` (275), `Release_By_Creator` (11-23). Slowest: `Funding_Spent_Once` (7140 steps, 1-2 h), `Sender_Pays_Invoice_Plus_Fees` (1470). `Fulfilled_Requires_Release` uses the `fulfilled_back` tactic (with `heuristic=S` it runs out of memory).
- **Liveness, `-D=LIVENESS` (all verified):** Simon's 7 (`Cheating_Never_Pays` 102, `Intermediary_Never_Loses_Under_Liveness` 12, `Payment_Atomicity_Under_Liveness` 84, `Timeout_Race_Blocked` 25, `Forwarder_Claims_In_Time` 9, `Forwarder_Refunds_In_Time` 121, `Intermediary_Recovers_Funds` 239), `Hand_Payment` (83: a payment is still possible under the liveness assumptions), two committed-settle versions (`Forwarder_Claims_In_Time_Committed` 7, `Intermediary_Never_Loses_Committed` 12) and 4 helpers that exist only in the LIVENESS block (`Redeem_Refund_Exclusive`, `Settle_From_Redeem`, `Fail_From_Refund`, `Settle_Fail_Exclusive`).
- **`Claim_Gap_Witness`: falsified (9 steps), as expected.** No trace exists in which a downstream settle has started but is not committed before the incoming HTLC expires. This is an assumption, not a result: the liveness restrictions `ForwarderCollectsInTime` / `ForwarderRefundsInTime` force a started settle to complete in time. State it as such in the paper.

All additions are marked `// add`. The model itself only gains the action labels `RouteMade` and `FulfilledOut`. Peak memory is about 8-10 GB per lemma, mostly for loading the model: run one prover at a time.

    make                 # goal2 + helpers + safety, one call per lemma (several hours)
    make liveness        # helpers + liveness lemmas with -D=LIVENESS
    make summary         # counts per result; lists every result that is not the expected one
    make check-count     # lemma lists vs. what Tamarin loads

`make` fails if any lemma does not give its expected result (VERIFIED, or
FALSIFIED for `Claim_Gap_Witness`); a Tamarin wellformedness warning counts as a
failure. `RESUME=1` reuses a recorded result only for the same lemma, flags and
unchanged `.spthy` files (checksum in `results.tsv`).

Limitations of the goal-2 model (state them in the paper):
- **Liveness assumptions exclude closing a channel with an HTLC in flight.**
  `ForwarderRefundsInTime` / `ForwarderCollectsInTime` require a *committed*
  fail or settle before the incoming expiry. A commit needs a channel update,
  which is impossible once the channel is closed, so traces in which a channel
  with a pending forwarded HTLC is closed and time passes the expiry are ruled
  out. The liveness lemmas therefore say nothing about on-chain HTLC resolution,
  and they assume the channel peer cooperates in the update (even a compromised
  one). The final model (folder 1) does not have this restriction.
- **Fixed: commit only while the channel is open.** Without the restriction
  `CommitOnlyWhileOpen` a completed update could be committed after the channel
  was closed (`Commit_After_Close_Witness` found that trace, 23 steps). With the
  restriction the witness is FALSIFIED. Effects of a step committed before the
  close can still happen after it; on-chain HTLC resolution is not modelled.
- **Balances are not linked to HTLC amounts:** `Update_State_HTLC` takes the new
  balances from the network, as `Update_State` does. Goal 2 proves the order
  (an HTLC step takes effect only after a completed update), not that funds move
  by the HTLC amount.
- `Settle_Is_Channel_Update` allows the exception "some party is compromised"
  (any party, any time), which is weaker than "a party on this route, earlier".

Scope: the channel abstraction permits at most one HTLC per payment hash per channel (`Mutex`, `OneHTLCPerHashPerChannel`). The `Mutex` comes from Simon's model; removing it (concurrent HTLCs on one channel) is goal 3. Request identifiers are unnecessary in the current proofs: a channel update is identified by (channel, hash, operation), and `HTLC_Commit_Correspondence` ties each `HTLCCommitted(ptr, op, n)` to the matching `ChannelUpdateFor(ptr, op, n)` and `StateUpdate(..., ptr, n)`. Retries with the same hash or duplicate settle requests would require carrying a unique HTLC/request identifier through `UpdateFor`, `ChannelUpdateFor`, `InFlight` and `HTLCCommitted`. This is a completion-aware core abstraction, not a complete multi-HTLC Lightning implementation.

    tamarin-prover lightningupd.spthy --prove=Settle_Is_Channel_Update --prove=Hand_Payment --derivcheck-timeout=600

## 3_deadline_theorem/  (core models, standalone)
| File | What |
|---|---|
| `deadline_core.spthy` | One hop: theorem, witnesses, ablation and gap controls, invariants |
| `deadline_core2.spthy` | Two forwarders: composable per-hop theorem, end-to-end theorem, witnesses, gap control |

Flags: `-D=LIVENESS -D=BOUND -D=GAP2` (theorem), `-D=LIVENESS -D=GAP2` (ablation), `-D=LIVENESS -D=BOUND -D=GAP1` (gap control); no flags for the safety lemmas.

    tamarin-prover deadline_core.spthy -D=LIVENESS -D=BOUND -D=GAP2 --prove=Deadline_Per_Hop

## Reproduced on a MacBook Air M5 (16 GB), Tamarin 1.12.0 / Maude 3.5.1

- Folder 1: 103/103 VERIFIED (51 without flags, 52 with `-D=LIVENESS`).
- Folder 2 (before `CommitOnlyWhileOpen` was added): 76 VERIFIED + 1 FALSIFIED (`Claim_Gap_Witness`, the expected result):
  62 without flags (7 goal-2, 5 helpers, 50 safety) and 15 with `-D=LIVENESS`.
  Peak memory 10.4 GB (`Funding_Spent_Once`, `Sender_Pays_Invoice_Plus_Fees`).
- The same proofs also verify on Tamarin 1.10 (server runs).

## Running on a Mac (e.g. MacBook Air, 16 GB)

    brew install tamarin-prover/tap/tamarin-prover   # includes Maude
    brew install coreutils                           # gtimeout, used by run_lemma.sh

    cd 2_htlcs_through_channel_updates
    RESUME=1 caffeinate -i make MEM=10G              # goal 2 + helpers + 50 safety lemmas
    RESUME=1 caffeinate -i make liveness MEM=10G
    make summary

`RESUME=1` skips lemmas already VERIFIED/FALSIFIED in `results.tsv`, so the run
can be stopped (Ctrl-C) and continued later. Run one `make` at a time: most
goal-2 lemmas need 8-10 GB. A lemma reported as OUT_OF_MEMORY can be retried
alone with `make lemma L=<name> MEM=12G` (macOS then swaps; slow but works).

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
    make verify                  # goal2 + helpers + safety
    make goal2                   # the 7 goal-2 lemmas
    make safety                  # the 50 safety lemmas, one call each
    make liveness                # -D=LIVENESS lemmas
    make lemma L=Hand_Payment

    # without make:
    tamarin-prover lightningupd.spthy --prove=Settle_Is_Channel_Update --prove=Hand_Payment --derivcheck-timeout=600
    tamarin-prover lightningupd.spthy --prove=Ltk_Known_Implies_Compromised --derivcheck-timeout=600   # one safety lemma

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
