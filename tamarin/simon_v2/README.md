# Simon's model + fixes

| File | What |
|---|---|
| `model.spthy` | Simon's original model (reference) |
| `modeltagged.spthy` | + `'invoice'` tag (fixes invoice confusion) |
| `modelfixb.spthy` | + tag, linear `FundingUnspent`, pattern-matched publish rules (final) |
| `tactics.spthy` | Simon's tactics + `offer_invoice` |
| `lemmas.spthy` | Simon's lemmas + ADDED: 2 invoice lemmas, `Funding_Spent_Once`, `No_Double_Publish` |
| `lightningfixb.spthy` | Full theory (final model + all lemmas) |
| `bug_double_publish.spthy` | Bug on `modeltagged`: distinct parties double-publish (found, 12 steps) |
| `check_fix.spthy` | On final model: no double publish (108 steps), publishing still reachable |
| `run_fixb.sh`, `runfixb_*.log` | Full run: 51/51 verified, 52/52 with `-D=LIVENESS` |
