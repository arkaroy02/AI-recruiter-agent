# agent/interest_scorer.py

from hf_api_client import generate_text
from json_utils import parse_json_from_text

INTEREST_PROMPT = """
Analyze the following recruiter-candidate conversation and return a JSON object:
- interest_score: 0-100 (genuine enthusiasm for this role)
- availability: "immediately" | "1-3 months" | "passive" | "not interested"
- key_signals: list of phrases from candidate that indicate interest or hesitation
- red_flags: list of any concerns raised

Return ONLY valid JSON.

Conversation:
{conversation_text}
"""


def _fallback_score_interest(conversation: list[dict]) -> dict:
    candidate_lines = [
        (message.get("text") or "").lower()
        for message in conversation
        if message.get("speaker") == "candidate"
    ]
    text = " ".join(candidate_lines)

    interest_score = 55
    availability = "passive"
    key_signals = []
    red_flags = []

    positive_markers = ["interested", "excited", "open to", "sounds good", "would love", "happy to chat"]
    negative_markers = ["not interested", "happy where i am", "not looking", "too early", "busy"]

    if any(marker in text for marker in positive_markers):
        interest_score += 20
        key_signals.append("Candidate expressed interest in continuing the conversation")
    if any(marker in text for marker in negative_markers):
        interest_score -= 20
        red_flags.append("Candidate sounded hesitant about changing roles")

    if "immediately" in text or "right away" in text:
        availability = "immediately"
    elif "month" in text or "notice period" in text:
        availability = "1-3 months"
    elif "not interested" in text:
        availability = "not interested"

    return {
        "interest_score": max(0, min(100, interest_score)),
        "availability": availability,
        "key_signals": key_signals,
        "red_flags": red_flags,
    }


def score_interest(conversation: list[dict]) -> dict:
    convo_text = "\n".join(f"{m['speaker'].upper()}: {m['text']}" for m in conversation)
    try:
        prompt = INTEREST_PROMPT.format(conversation_text=convo_text)
        response = generate_text(prompt, max_length=500)
        return parse_json_from_text(response)
    except Exception:
        return _fallback_score_interest(conversation)
