# Text Humanizer

Turn a paragraph or a PDF into text that reads like a person wrote it, not a
model. It runs your source text through the **v2.0 "sound-human" prompt** (the
ban list, jagged rhythm, no-summary, asymmetrical-structure rules) and then a
**rule engine** double-checks the result: it scrubs leftover banned words, swaps
bureaucratic verbs for plain ones, flags robotic transitions, and scores how
human the text reads.

It's built as a hybrid on purpose. The model does the real rewrite; the rule
engine is the safety net and the report card. This matches the honest framing:
you get a strong first draft, and the last mile still wants a human pass.

## Install

The core tool uses only the Python standard library. PDF input needs one extra
package.

```bash
pip install -r requirements.txt   # installs pypdf, for --pdf
```

Run it as a module from the repository root:

```bash
python3 -m humanizer --help
```

Or install it as a `humanize` command:

```bash
pip install ./humanizer
humanize --help
```

## Usage

```bash
# A pasted paragraph, rewritten by a local Ollama model (default)
python3 -m humanizer --text "Your paragraph here"

# A PDF, aimed at a specific audience and tone
python3 -m humanizer --pdf report.pdf --audience "busy managers" --tone casual

# A text file, using OpenAI, written to a file, with the report shown
python3 -m humanizer --file draft.txt --provider openai --out result.txt --report

# No model at all: just clean + report (deterministic, offline, free)
python3 -m humanizer --text "We utilize robust synergy." --provider none --report
```

### Input (choose one)

| Flag | Meaning |
| --- | --- |
| `--text "..."` | Raw text to humanize |
| `--file path.txt` | A plain-text file |
| `--pdf path.pdf` | A PDF (text is extracted and cleaned) |

### Style

| Flag | Default |
| --- | --- |
| `--audience` | `general public` |
| `--tone` | `casual, straight-to-the-point` |

### Model backends

| Provider | Needs | Notes |
| --- | --- | --- |
| `ollama` (default) | Ollama running locally | No API key. Set `OLLAMA_HOST` to change the URL. |
| `openai` | `OPENAI_API_KEY` | Optional `OPENAI_BASE_URL`. |
| `anthropic` | `ANTHROPIC_API_KEY` | Optional `ANTHROPIC_BASE_URL`. |
| `none` | nothing | Rule engine only: cleans + reports, no rewrite. |

Override the model name with `--model`, e.g.
`--provider openai --model gpt-4o`.

If the chosen model can't be reached, the tool prints a warning and falls back
to rule-engine-only mode so it still returns something useful. Pass
`--no-fallback` to make it fail instead.

### Output

| Flag | Meaning |
| --- | --- |
| `--out path` | Write the result to a file instead of stdout |
| `--report` | Print the rule report (banned words, rhythm, human score) to stderr |
| `--no-clean` | Keep the model's text verbatim (skip the deterministic scrub) |

## The report

`--report` shows what the rule engine found:

```
Human score: 20/100

Banned words still present: crucial (x1), robust (x1), synergy (x1)
Robotic sentence openers: Furthermore
Summary/conclusion opener detected: none
Simple-verb swaps applied: leverage->use (x1), utilize->use (x1)

Sentences: 2 | length variety (stdev): 0.5
Paragraphs: 1 | length variety (stdev): 0.0
```

The **human score** is a rough 0–100 heuristic. It drops for banned words,
robotic transitions, summary openers, and for low sentence/paragraph length
variety (uniform rhythm and perfectly balanced paragraphs are the tells your
v2.0 prompt targets).

## How it fits together

```
input (--text / --file / --pdf)
        │
        ▼
  inputs.py        clean/extract source text
        │
        ▼
  providers.py     rewrite with ollama / openai / anthropic  (skipped for --provider none)
        │
        ▼
  rules.py         scrub banned verbs, then analyze + score
        │
        ▼
  output (+ optional --report)
```

## Limitations

- Without a model (`--provider none` or a fallback), the tool **cleans and
  scores** but does not rewrite. Real rewriting needs a model.
- PDF extraction can't read scanned/image-only PDFs; those need OCR first.
- The human score is a heuristic, not a detector. Use it as a checklist, not a
  guarantee.
