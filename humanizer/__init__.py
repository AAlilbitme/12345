"""Text humanizer: turn paragraphs or PDFs into more human-sounding prose.

The package wraps a rewriting model (Ollama / OpenAI / Anthropic) with the
v2.0 "sound-human" prompt, and pairs it with a rule engine that scrubs banned
words, catches robotic transitions, and scores how human the output reads.
"""

__version__ = "0.1.0"
