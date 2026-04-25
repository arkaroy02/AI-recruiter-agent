# agent/convo_simulator.py
from typing import Callable, Optional

from hf_api_client import generate_text

RECRUITER_SYSTEM = """
You are a warm, professional recruiter reaching out to a candidate about a {role} role.
Ask 1 or 2 targeted questions in one short turn:
1. Confirm current situation and openness to change
2. Probe specific interest in this role or domain
Be concise. End with: "RECRUITER_DONE"
"""

CANDIDATE_SYSTEM = """
You are {name}, a {title} with {years_exp} years of experience in {skills}.
You are {openness} to new opportunities. Respond realistically to recruiter outreach.
Reveal your genuine interest level naturally over the conversation.
End your final message with: "CANDIDATE_DONE"
"""

TurnCallback = Callable[[dict], None]


def simulate_conversation(
    candidate: dict,
    jd: dict,
    turns: int = 2,
    on_turn: Optional[TurnCallback] = None
) -> list[dict]:
    """Simulate conversation between recruiter and candidate using HF API."""
    history = []
    recruiter_ctx = {"role": jd["role"]}
    candidate_ctx = {**candidate, "openness": candidate.get("openness", "somewhat open")}

    for _ in range(turns):
        # Recruiter turn
        recruiter_system = RECRUITER_SYSTEM.format(**recruiter_ctx)
        history_text = "\n".join([f"{m['speaker'].upper()}: {m['text']}" for m in history])
        recruiter_prompt = f"{recruiter_system}\n\nHistory:\n{history_text}" if history_text else recruiter_system
        recruiter_msg = generate_text(recruiter_prompt, max_length=300)
        history.append({"speaker": "recruiter", "text": recruiter_msg})
        if on_turn:
            on_turn(history[-1])

        if "RECRUITER_DONE" in recruiter_msg:
            break

        # Candidate turn
        candidate_system = CANDIDATE_SYSTEM.format(**candidate_ctx)
        history_text = "\n".join([f"{m['speaker'].upper()}: {m['text']}" for m in history])
        candidate_prompt = f"{candidate_system}\n\nHistory:\n{history_text}"
        candidate_msg = generate_text(candidate_prompt, max_length=300)
        history.append({"speaker": "candidate", "text": candidate_msg})
        if on_turn:
            on_turn(history[-1])

        if "CANDIDATE_DONE" in candidate_msg:
            break

    return history
