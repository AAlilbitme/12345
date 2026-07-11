"""The rule engine: scrub banned language and score how human text reads.

This runs with or without a model. When a model rewrote the text, we use this
as a safety net and a report card. When there is no model, this is the only
processing available, so it cleans what it mechanically can and tells you
what still needs a human pass.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field

from .prompt import (
    BAN_LIST,
    ROBOTIC_TRANSITIONS,
    SIMPLE_SWAPS,
    SUMMARY_OPENERS,
)

_WORD_RE = re.compile(r"[A-Za-z']+")
# Split on sentence-ending punctuation followed by whitespace.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class RuleReport:
    """A readable report of what the rule engine found and changed."""

    banned_words_found: dict[str, int] = field(default_factory=dict)
    robotic_transitions_found: list[str] = field(default_factory=list)
    summary_opener_found: str | None = None
    swaps_applied: dict[str, int] = field(default_factory=dict)
    sentence_count: int = 0
    sentence_length_stdev: float = 0.0
    paragraph_count: int = 0
    paragraph_length_stdev: float = 0.0
    human_score: int = 0

    def as_text(self) -> str:
        lines: list[str] = []
        lines.append(f"Human score: {self.human_score}/100")
        lines.append("")
        if self.banned_words_found:
            found = ", ".join(
                f"{w} (x{n})" for w, n in sorted(self.banned_words_found.items())
            )
            lines.append(f"Banned words still present: {found}")
        else:
            lines.append("Banned words still present: none")

        if self.robotic_transitions_found:
            lines.append(
                "Robotic sentence openers: "
                + ", ".join(sorted(set(self.robotic_transitions_found)))
            )
        else:
            lines.append("Robotic sentence openers: none")

        if self.summary_opener_found:
            lines.append(
                f"Summary/conclusion opener detected: \"{self.summary_opener_found}\""
            )
        else:
            lines.append("Summary/conclusion opener detected: none")

        if self.swaps_applied:
            swaps = ", ".join(
                f"{w}->{SIMPLE_SWAPS[w]} (x{n})"
                for w, n in sorted(self.swaps_applied.items())
            )
            lines.append(f"Simple-verb swaps applied: {swaps}")

        lines.append("")
        lines.append(
            f"Sentences: {self.sentence_count} | "
            f"length variety (stdev): {self.sentence_length_stdev:.1f}"
        )
        lines.append(
            f"Paragraphs: {self.paragraph_count} | "
            f"length variety (stdev): {self.paragraph_length_stdev:.1f}"
        )
        return "\n".join(lines)


def _match_case(replacement: str, original: str) -> str:
    """Make the replacement follow the capitalization of the original token."""
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def apply_simple_swaps(text: str) -> tuple[str, dict[str, int]]:
    """Replace bureaucratic verbs with plain ones, preserving casing."""
    applied: dict[str, int] = {}

    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        key = token.lower()
        if key in SIMPLE_SWAPS:
            applied[key] = applied.get(key, 0) + 1
            return _match_case(SIMPLE_SWAPS[key], token)
        return token

    pattern = re.compile(
        r"\b(" + "|".join(re.escape(w) for w in SIMPLE_SWAPS) + r")\b",
        re.IGNORECASE,
    )
    return pattern.sub(repl, text), applied


def _count_banned(text: str) -> dict[str, int]:
    lowered = text.lower()
    counts: dict[str, int] = {}
    for word in BAN_LIST:
        n = len(re.findall(rf"\b{re.escape(word)}\b", lowered))
        if n:
            counts[word] = n
    return counts


def _split_sentences(text: str) -> list[str]:
    parts = [s.strip() for s in _SENTENCE_RE.split(text.strip()) if s.strip()]
    return parts


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _find_robotic_openers(sentences: list[str]) -> list[str]:
    found: list[str] = []
    for sentence in sentences:
        first = _WORD_RE.findall(sentence)
        if first and first[0].lower() in ROBOTIC_TRANSITIONS:
            found.append(first[0])
    return found


def _find_summary_opener(paragraphs: list[str]) -> str | None:
    if not paragraphs:
        return None
    last = paragraphs[-1].lower().lstrip("\"'*# ")
    for opener in SUMMARY_OPENERS:
        if last.startswith(opener):
            return opener
    return None


def _score(report: RuleReport) -> int:
    """A rough 0-100 read on how human the text looks. Higher is better."""
    score = 100
    score -= 12 * sum(report.banned_words_found.values())
    score -= 8 * len(report.robotic_transitions_found)
    if report.summary_opener_found:
        score -= 15
    # Reward sentence-length variety (jagged rhythm). Little variety is a tell.
    if report.sentence_count >= 3 and report.sentence_length_stdev < 3:
        score -= 10
    # Reward paragraph-length variety (asymmetrical structure).
    if report.paragraph_count >= 3 and report.paragraph_length_stdev < 5:
        score -= 8
    return max(0, min(100, score))


def analyze(text: str) -> RuleReport:
    """Inspect text against the rules without changing it."""
    sentences = _split_sentences(text)
    paragraphs = _split_paragraphs(text)
    sent_lengths = [_word_count(s) for s in sentences]
    para_lengths = [_word_count(p) for p in paragraphs]

    report = RuleReport(
        banned_words_found=_count_banned(text),
        robotic_transitions_found=_find_robotic_openers(sentences),
        summary_opener_found=_find_summary_opener(paragraphs),
        sentence_count=len(sentences),
        sentence_length_stdev=(
            statistics.pstdev(sent_lengths) if len(sent_lengths) > 1 else 0.0
        ),
        paragraph_count=len(paragraphs),
        paragraph_length_stdev=(
            statistics.pstdev(para_lengths) if len(para_lengths) > 1 else 0.0
        ),
    )
    report.human_score = _score(report)
    return report


def clean(text: str) -> tuple[str, RuleReport]:
    """Apply mechanical fixes (simple swaps) and return cleaned text + report.

    This does not rewrite prose. It only performs safe, deterministic edits
    and then reports what a human still needs to address.
    """
    cleaned, swaps = apply_simple_swaps(text)
    report = analyze(cleaned)
    report.swaps_applied = swaps
    return cleaned, report
