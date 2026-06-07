# AGENTS.md

## Project overview

This repository contains a **Tamarin Prover** formal verification model (`PaymentChannels.spthy`) for a bilateral payment channel protocol. There is no application server, database, or package manager lockfile — development means editing the `.spthy` theory and running Tamarin.

## Cursor Cloud specific instructions

### Required tools

| Tool | Purpose |
|------|---------|
| `tamarin-prover` | Parse theories, prove lemmas, interactive mode |
| `maude` (3.4+ supported) | Tamarin symbolic backend |
| `dot` (GraphViz) | Proof graph rendering |

Install everything with:

```bash
bash scripts/install-dev-tools.sh
export PATH="$HOME/.local/bin:$PATH"
```

Ubuntu's `apt` package `maude` (3.2) triggers Tamarin version warnings; the install script uses Maude 3.4 from the official GitHub release instead.

### Verify the environment

From the repo root:

```bash
# Parse / well-formedness check (~5s)
tamarin-prover PaymentChannels.spthy --derivcheck-timeout=60

# Prove a single lemma (example: ~14s)
tamarin-prover PaymentChannels.spthy --prove=Protocol_execution
```

### Interactive mode (optional)

```bash
tamarin-prover interactive PaymentChannels.spthy
# Open http://localhost:3001 in a browser
```

Use tmux for long-running proof sessions; full `--prove` on all lemmas can take substantial time and may need interactive tactics.

### Lint / tests

There is no separate linter or test suite. Tamarin's well-formedness checks and lemma proofs are the validation workflow.

### Lemmas in `PaymentChannels.spthy`

`state_update`, `delayed_funds`, `instant_funds`, `settlement_is_traceable`, `Protocol_execution`, `No_Punishment_Without_Cheating`, `Balance_Must_Updates`, `Cooperative_Close_Execution`
