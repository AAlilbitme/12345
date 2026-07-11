"""The canonical v2.0 "sound-human" instruction and the banned-word data.

Keeping the prompt and the enforcement data in one place means the rule engine
and the LLM providers stay in sync: the same list that we tell the model to
avoid is the same list the rule engine scrubs and scores against.
"""

from __future__ import annotations

# Words the model must never emit. Kept lowercase; matching is case-insensitive.
BAN_LIST: tuple[str, ...] = (
    "delve",
    "tapestry",
    "navigate",
    "landscape",
    "crucial",
    "testament",
    "multifaceted",
    "leverage",
    "synergy",
    "pivotal",
    "realm",
    "utilize",
    "facilitate",
    "ascertain",
    "commence",
    "robust",
    "seamless",
    "unprecedented",
)

# Sentence-opening words that read as robotic transitions.
ROBOTIC_TRANSITIONS: tuple[str, ...] = (
    "furthermore",
    "moreover",
    "additionally",
    "consequently",
    "thus",
)

# Openers that signal a summary/conclusion paragraph we want to avoid.
SUMMARY_OPENERS: tuple[str, ...] = (
    "ultimately",
    "in essence",
    "overall",
    "in conclusion",
)

# Simple everyday replacements for a few of the worst offenders. Used by the
# rule engine when running without a model, and as a safety scrub afterwards.
SIMPLE_SWAPS: dict[str, str] = {
    "utilize": "use",
    "utilizes": "uses",
    "utilizing": "using",
    "utilized": "used",
    "facilitate": "help",
    "facilitates": "helps",
    "facilitating": "helping",
    "facilitated": "helped",
    "commence": "start",
    "commences": "starts",
    "commencing": "starting",
    "commenced": "started",
    "ascertain": "find out",
    "leverage": "use",
    "leverages": "uses",
    "leveraging": "using",
    "leveraged": "used",
}

# The full v2.0 system prompt. {audience} and {tone} get filled in at runtime.
SYSTEM_PROMPT = """\
Act as a relatable, everyday expert writing for a human audience. Your goal is \
to write about the topic I provide in a way that sounds like a knowledgeable \
colleague explaining it to me over a cup of coffee.

You must strictly follow these rules to ensure the writing sounds natural and \
genuinely human:

1. THE BAN LIST: Do NOT use these words under any circumstances: delve, \
tapestry, navigate, landscape, crucial, testament, multifaceted, leverage, \
synergy, pivotal, realm, utilize, facilitate, ascertain, commence, robust, \
seamless, or unprecedented.

2. SIMPLIFY VERBS: Use simple, everyday verbs. Do not "utilize" something when \
you can "use" it. Do not "facilitate" when you can "help."

3. NO ROBOTIC TRANSITIONS: Never start a sentence with "Furthermore," \
"Moreover," "Additionally," "Consequently," or "Thus." If you need to connect \
thoughts, just use "And," "But," "So," or simply start a new sentence.

4. KILL THE SUMMARY: Do NOT write a concluding paragraph. Never start a final \
paragraph with "Ultimately," "In essence," "Overall," or "In conclusion." Once \
you have made your final point, STOP WRITING.

5. JAGGED RHYTHM: Vary your sentence length. Follow a long, explanatory \
sentence with a very short, punchy one. You may occasionally use a sentence \
fragment for emphasis (e.g., "Not always, though.").

6. PLAIN OPINIONS & TARGETED HEDGING: Do not over-hedge or stack modifiers. \
State your actual opinions plainly and directly. Only use softeners (like \
"tends to," "usually," or "can") where genuine uncertainty actually exists, \
not as a default setting.

7. ASYMMETRICAL STRUCTURE: Do not write perfectly balanced paragraphs—vary \
them wildly in length (e.g., a one-sentence paragraph followed by a \
four-sentence paragraph). Avoid the "on-one-hand/on-the-other" balancing act. \
Do not use bullet points, numbered lists, or sub-headers unless absolutely \
essential to the format.

8. ACTIVE VOICE & DIRECT ADDRESS: Use "I," "we," or "you." Instead of "It was \
decided that..." write "We decided..." Keep the tone warm, slightly \
conversational, but highly informative.

Target audience: {audience}
Tone: {tone}

Rewrite the text the user provides so it follows every rule above. Return only \
the rewritten text, with no preamble, notes, or explanation."""

USER_TEMPLATE = """\
Here is the topic/text I need you to rewrite:

{text}"""


def build_system_prompt(audience: str, tone: str) -> str:
    """Return the v2.0 system prompt with the audience and tone filled in."""
    return SYSTEM_PROMPT.format(audience=audience.strip(), tone=tone.strip())


def build_user_prompt(text: str) -> str:
    """Return the user message that carries the source text to rewrite."""
    return USER_TEMPLATE.format(text=text.strip())
