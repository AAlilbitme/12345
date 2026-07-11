"""Command-line interface for the text humanizer.

Examples:
    humanize --text "Your paragraph here"
    humanize --pdf report.pdf --audience "busy managers" --tone casual
    humanize --file draft.txt --provider openai --out result.txt
    humanize --text "..." --provider none        # rule engine only
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .inputs import resolve_input
from .providers import DEFAULT_MODELS, ProviderError, rewrite
from .rules import clean


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="humanize",
        description="Turn a paragraph or PDF into more human-sounding text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    src = parser.add_argument_group("input (choose one)")
    src.add_argument("--text", help="Raw text to humanize.")
    src.add_argument("--file", help="Path to a .txt file to humanize.")
    src.add_argument("--pdf", help="Path to a .pdf file to humanize.")

    cfg = parser.add_argument_group("style")
    cfg.add_argument(
        "--audience",
        default="general public",
        help="Who the text is for (default: general public).",
    )
    cfg.add_argument(
        "--tone",
        default="casual, straight-to-the-point",
        help="Desired tone (default: casual, straight-to-the-point).",
    )

    model = parser.add_argument_group("model")
    model.add_argument(
        "--provider",
        choices=["ollama", "openai", "anthropic", "none"],
        default="ollama",
        help="Rewriting backend (default: ollama). 'none' = rule engine only.",
    )
    model.add_argument(
        "--model",
        default=None,
        help="Override the model name for the chosen provider.",
    )
    model.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Model request timeout in seconds (default: 120).",
    )
    model.add_argument(
        "--no-fallback",
        action="store_true",
        help="Fail instead of falling back to the rule engine if the model is unavailable.",
    )

    out = parser.add_argument_group("output")
    out.add_argument("--out", help="Write the result to this file instead of stdout.")
    out.add_argument(
        "--report",
        action="store_true",
        help="Print the rule-engine report (banned words, rhythm, human score).",
    )
    out.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip the deterministic safety scrub of the model output.",
    )
    return parser


def _emit(text: str, out_path: str | None) -> None:
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text.rstrip() + "\n")
        print(f"Wrote humanized text to {out_path}", file=sys.stderr)
    else:
        print(text)


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        source = resolve_input(text=args.text, file=args.file, pdf=args.pdf)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        parser.error(str(exc))
        return 2  # unreachable; parser.error exits

    used_provider = args.provider
    used_model = args.model or DEFAULT_MODELS.get(args.provider)
    rewritten = source

    if args.provider != "none":
        try:
            result = rewrite(
                source,
                audience=args.audience,
                tone=args.tone,
                provider=args.provider,
                model=args.model,
                timeout=args.timeout,
            )
            rewritten = result.text
            used_provider = result.provider
            used_model = result.model
        except ProviderError as exc:
            if args.no_fallback:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            print(
                f"warning: {exc}\n"
                "         Falling back to rule-engine-only mode "
                "(cleaning + report, no rewrite).",
                file=sys.stderr,
            )
            used_provider = "none (fallback)"
            used_model = None

    if args.no_clean and used_provider not in ("none", "none (fallback)"):
        final_text = rewritten
        _, report = clean(rewritten)  # report only, keep model text verbatim
    else:
        final_text, report = clean(rewritten)

    _emit(final_text, args.out)

    if args.report:
        print("", file=sys.stderr)
        print(f"--- report (provider: {used_provider}"
              f"{f', model: {used_model}' if used_model else ''}) ---",
              file=sys.stderr)
        print(report.as_text(), file=sys.stderr)

    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
