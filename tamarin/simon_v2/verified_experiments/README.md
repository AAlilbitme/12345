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

## notes/
- `deadline_status.md`: all results, the agreed paper scope and its limitations.
- `related_work.md`: comparison with prior work and the claim wording.

Intermediate models, check theories, run scripts and logs are in the git history.
