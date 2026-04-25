"""Shared service helpers for the FastAPI web UI."""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
import re
import sys
import tempfile
from typing import Dict, List, Tuple
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT_DIR / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from config import HF_TOKEN  # noqa: E402
from hf_api_client import generate_text  # noqa: E402
from interest_scorer import score_interest  # noqa: E402
from json_utils import parse_json_from_text  # noqa: E402


RESUME_PARSE_PROMPT = """
Extract a structured candidate profile from the resume text below.

Return ONLY valid JSON with exactly these keys:
- name (string)
- title (string)
- years_exp (integer)
- skills (list of strings)
- summary (string)
- current_company (string)
- education (string)
- openness (string: one of "very open", "somewhat open", "passive")

Rules:
- Use only information supported by the resume text when possible.
- If something is unclear, make a conservative best effort.
- If the resume does not state openness, default to "somewhat open".
- Keep `summary` to 1 or 2 sentences.
- Keep `skills` to the most relevant 6 to 12 skills.
- `years_exp` must be a non-negative integer.

Resume text:
{resume_text}
"""

SKILL_HINTS = [
    "python", "java", "javascript", "typescript", "react", "node", "node.js", "django",
    "flask", "fastapi", "spring", "spring boot", "postgresql", "mysql", "mongodb",
    "redis", "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "sql",
    "spark", "airflow", "dbt", "tableau", "power bi", "pytorch", "tensorflow",
    "scikit-learn", "machine learning", "nlp", "rest", "graphql", "microservices",
    "go", "golang", "rust", "c++", "c#", "linux", "git", "ci/cd"
]

MAX_REAL_INTERVIEW_CANDIDATE_TURNS = 4


def clean_done_tokens(text: str) -> str:
    """Remove control tokens from recruiter/candidate utterances."""
    return (text or "").replace("RECRUITER_DONE", "").replace("CANDIDATE_DONE", "").strip()


def count_candidate_turns(conversation: List[Dict]) -> int:
    """Count how many times the human candidate has responded in the session."""
    return sum(1 for message in conversation if message.get("speaker") == "candidate")


def candidate_requested_interview_end(text: str) -> bool:
    """Detect explicit signals that the candidate wants to end the interview now."""
    lowered = clean_done_tokens(text).strip().lower()
    end_markers = [
        "end this interview",
        "end the interview",
        "stop the interview",
        "let's end the interview",
        "i want to end this interview",
        "i want to stop",
        "we can stop here",
        "let's stop here",
        "that's all from me",
        "no more questions",
        "move on to the next person",
        "move to the next person",
        "next candidate",
    ]
    return any(marker in lowered for marker in end_markers)


def should_end_real_interview(conversation: List[Dict], latest_candidate_text: str) -> bool:
    """End real interviews on explicit request or after a reasonable number of turns."""
    if candidate_requested_interview_end(latest_candidate_text):
        return True
    return count_candidate_turns(conversation) >= MAX_REAL_INTERVIEW_CANDIDATE_TURNS


def build_interview_closing(candidate_requested_end: bool) -> str:
    """Create a short recruiter wrap-up when the interview ends outside model control."""
    if candidate_requested_end:
        return "Thanks for your time today. We can wrap up here, and I'll move on to the next candidate. RECRUITER_DONE"
    return "Thanks, this gives me enough to wrap up the interview for now. I'll move on to the next candidate. RECRUITER_DONE"


def _looks_like_candidate_answer(text: str) -> bool:
    """Detect when the interviewer accidentally responds like the candidate."""
    lowered = clean_done_tokens(text).strip().lower()
    candidate_markers = [
        "i am",
        "i'm",
        "my experience",
        "i have worked",
        "i worked",
        "i have been",
        "i'm currently",
        "my background",
        "i would be interested",
        "thank you for having me",
    ]
    return any(marker in lowered for marker in candidate_markers) and "?" not in lowered


def generate_recruiter_question(jd_parsed: Dict, conversation: List[Dict], candidate: Dict | None = None) -> str:
    """Generate one recruiter turn for real interview mode."""
    candidate_name = (candidate or {}).get("name", "the candidate")
    candidate_title = (candidate or {}).get("title", "their current role")
    required_skills = ", ".join(jd_parsed.get("required_skills", [])[:6]) or "the core skills for this role"
    prompt = f"""
You are a warm, emotionally intelligent recruiter interviewing a real human candidate live.

Hiring context:
- Role: {jd_parsed.get("role", "this role")}
- Seniority: {jd_parsed.get("seniority", "not specified")}
- Key skills: {required_skills}

Candidate context:
- Name: {candidate_name}
- Current title: {candidate_title}

Interview style rules:
- Sound like a thoughtful human interviewer, not a bot.
- Ask exactly one question at a time.
- Keep it concise: usually 1 to 2 sentences.
- For the first turn, briefly welcome the candidate before the first question.
- After the candidate answers, briefly acknowledge something specific they said, then ask the next question.
- Focus on experience, problem-solving, motivations, availability, and fit for the role.
- Avoid repeating earlier questions or listing multiple questions together.
- If you already have enough information after a few turns, write a short warm wrap-up and include RECRUITER_DONE.
- You are the recruiter only.
- Never answer on behalf of the candidate.
- Never say things like "I worked", "my background", or "I am interested" unless quoting the candidate.
- Your reply should almost always end with a question mark unless you are wrapping up with RECRUITER_DONE.
"""
    messages = [{"role": "system", "content": prompt}]
    for message in conversation:
        role = "assistant" if message.get("speaker") == "recruiter" else "user"
        messages.append({"role": role, "content": message.get("text", "")})

    # Build full context for HF API
    conversation_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
    full_prompt = f"{prompt}\n\nConversation so far:\n{conversation_text}"
    
    content = generate_text(full_prompt, max_length=300)

    if _looks_like_candidate_answer(content):
        retry_prompt = f"{prompt}\n\nThat response sounded like the candidate speaking. Rewrite it as the recruiter only. Ask exactly one concise interviewer question.\n\nConversation:\n{conversation_text}\nLast response:\n{content}"
        content = generate_text(retry_prompt, max_length=300)

    return content


def _clean_resume_text(text: str) -> str:
    lines = [line.strip() for line in (text or "").splitlines()]
    cleaned = [line for line in lines if line]
    return "\n".join(cleaned)


def _guess_name_from_filename(filename: str) -> str:
    stem = Path(filename or "Candidate").stem
    stem = re.sub(r"[_\-]+", " ", stem).strip()
    words = [word.capitalize() for word in stem.split() if word]
    return " ".join(words[:4]) or "Candidate"


def _fallback_years_exp(text: str) -> int:
    patterns = [
        r"(\d{1,2})\+?\s+years(?:\s+of)?\s+experience",
        r"experience\s*[:\-]?\s*(\d{1,2})\+?\s+years",
    ]
    lowered = text.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            return max(0, int(match.group(1)))
    return 0


def _fallback_skills(text: str) -> List[str]:
    lowered = text.lower()
    skills = []
    seen = set()
    for skill in SKILL_HINTS:
        if skill in lowered and skill not in seen:
            seen.add(skill)
            if skill == "node.js":
                skills.append("Node.js")
            elif skill == "ci/cd":
                skills.append("CI/CD")
            else:
                skills.append(skill.title())
    return skills[:12]


def _fallback_candidate_from_text(resume_text: str, filename: str) -> Dict:
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    name = _guess_name_from_filename(filename)
    title = "Candidate"
    if lines:
        if len(lines[0].split()) <= 5 and not any(char.isdigit() for char in lines[0]):
            name = lines[0]
        if len(lines) > 1 and len(lines[1]) <= 80:
            title = lines[1]

    return {
        "id": f"resume-{uuid4().hex[:8]}",
        "name": name,
        "title": title,
        "years_exp": _fallback_years_exp(resume_text),
        "skills": _fallback_skills(resume_text),
        "summary": "Resume uploaded and partially parsed from PDF text.",
        "current_company": "Unknown",
        "education": "Not provided",
        "openness": "somewhat open",
        "source_filename": filename,
        "resume_text": resume_text,
    }


def normalize_candidate_profile(profile: Dict, filename: str, resume_text: str) -> Dict:
    """Normalize parsed resume data into the candidate schema used by the pipeline."""
    skills = profile.get("skills", [])
    if not isinstance(skills, list):
        skills = []
    normalized_skills = []
    seen = set()
    for skill in skills:
        skill_text = str(skill).strip()
        lowered = skill_text.lower()
        if skill_text and lowered not in seen:
            seen.add(lowered)
            normalized_skills.append(skill_text)

    openness = str(profile.get("openness") or "somewhat open").strip().lower()
    if openness not in {"very open", "somewhat open", "passive"}:
        openness = "somewhat open"

    years_exp_raw = profile.get("years_exp", 0)
    try:
        years_exp = max(0, int(float(years_exp_raw)))
    except (TypeError, ValueError):
        years_exp = _fallback_years_exp(resume_text)

    candidate = {
        "id": str(profile.get("id") or f"resume-{uuid4().hex[:8]}"),
        "name": str(profile.get("name") or _guess_name_from_filename(filename)).strip(),
        "title": str(profile.get("title") or "Candidate").strip(),
        "years_exp": years_exp,
        "skills": normalized_skills or _fallback_skills(resume_text) or ["Generalist"],
        "summary": str(profile.get("summary") or "Resume uploaded from PDF.").strip(),
        "openness": openness,
        "current_company": str(profile.get("current_company") or "Unknown").strip(),
        "education": str(profile.get("education") or "Not provided").strip(),
        "source_filename": filename,
        "resume_text": resume_text,
    }
    return candidate


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, str]:
    """Extract text from a PDF byte stream."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return "", "PDF parsing dependency is missing. Install with: pip install pypdf"

    try:
        reader = PdfReader(BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
        text = _clean_resume_text("\n".join(text_parts))
        if not text:
            return "", "Could not extract text from this PDF. It may be scanned or image-only."
        return text, ""
    except Exception as exc:
        return "", f"Failed to read PDF: {exc}"


def parse_resume_to_candidate(resume_text: str, filename: str) -> Tuple[Dict, str]:
    """Convert extracted resume text into the candidate schema used by the matcher."""
    cleaned_text = _clean_resume_text(resume_text)
    if not cleaned_text:
        return {}, "Resume text is empty after extraction."

    prompt = RESUME_PARSE_PROMPT.format(resume_text=cleaned_text[:12000])
    try:
        response_text = generate_text(prompt, max_length=800)
        parsed = parse_json_from_text(response_text)
        return normalize_candidate_profile(parsed, filename, cleaned_text), ""
    except Exception:
        # Fall back to a heuristic parser so resume upload still works if the model output is noisy.
        return _fallback_candidate_from_text(cleaned_text, filename), ""


def extract_candidates_from_resumes(files: List[Tuple[str, bytes]]) -> Tuple[List[Dict], List[Dict]]:
    """Extract and parse uploaded PDF resumes into candidate profiles."""
    candidates: List[Dict] = []
    errors: List[Dict] = []

    for filename, file_bytes in files:
        resume_text, extract_error = extract_text_from_pdf(file_bytes)
        if extract_error:
            errors.append({"filename": filename, "error": extract_error})
            continue

        candidate, parse_error = parse_resume_to_candidate(resume_text, filename)
        if parse_error:
            errors.append({"filename": filename, "error": parse_error})
            continue

        candidates.append(candidate)

    return candidates, errors


def get_candidate(results: Dict, candidate_name: str) -> Dict | None:
    """Find candidate by name inside results payload."""
    for candidate in results.get("ranked_candidates", []):
        if candidate.get("name") == candidate_name:
            return candidate
    return None


def rerank_real_candidates(results: Dict) -> None:
    """Sort real-mode candidates by combined score after updates."""
    results["ranked_candidates"] = sorted(
        results.get("ranked_candidates", []),
        key=lambda item: item.get("combined_score", 0),
        reverse=True
    )


def reset_candidate_real_state(results: Dict, candidate_name: str) -> None:
    """Reset one candidate's interview state in real mode."""
    candidate = get_candidate(results, candidate_name)
    if not candidate:
        return

    candidate["conversation"] = []
    candidate["interest_score"] = 0.0
    candidate["availability"] = "Pending real interview"
    candidate["key_signals"] = []
    candidate["red_flags"] = []
    candidate["combined_score"] = round(float(candidate.get("match_score", 0)), 1)
    rerank_real_candidates(results)


def update_candidate_from_real_interview(
    results: Dict,
    candidate_name: str,
    conversation: List[Dict]
) -> Dict:
    """Score interest from human interview and update one candidate in results."""
    interest_result = score_interest(conversation)

    candidate = get_candidate(results, candidate_name)
    if not candidate:
        raise ValueError(f"Candidate not found: {candidate_name}")

    candidate["conversation"] = conversation
    candidate["interest_score"] = float(interest_result.get("interest_score", 0))
    candidate["availability"] = interest_result.get("availability", "Unknown")
    candidate["key_signals"] = interest_result.get("key_signals", [])
    candidate["red_flags"] = interest_result.get("red_flags", [])
    candidate["combined_score"] = round(
        float(candidate.get("match_score", 0)) * 0.60 + float(candidate.get("interest_score", 0)) * 0.40,
        1
    )
    rerank_real_candidates(results)
    return interest_result


def apply_early_exit_signal(results: Dict, candidate_name: str) -> Dict | None:
    """Mark an interview that ended early as a cautionary signal on the candidate profile."""
    candidate = get_candidate(results, candidate_name)
    if not candidate:
        return None

    red_flags = list(candidate.get("red_flags", []))
    key_signals = list(candidate.get("key_signals", []))

    early_exit_flag = "Candidate asked to end the interview early."
    if early_exit_flag not in red_flags:
        red_flags.append(early_exit_flag)

    early_exit_signal = "Candidate ended the conversation before the interview fully played out."
    if early_exit_signal not in key_signals:
        key_signals.append(early_exit_signal)

    candidate["red_flags"] = red_flags
    candidate["key_signals"] = key_signals
    candidate["availability"] = candidate.get("availability") or "passive"
    candidate["interest_score"] = min(float(candidate.get("interest_score", 0)), 25.0)
    candidate["combined_score"] = round(
        float(candidate.get("match_score", 0)) * 0.60 + float(candidate.get("interest_score", 0)) * 0.40,
        1
    )
    rerank_real_candidates(results)
    return candidate


@lru_cache(maxsize=3)
def load_whisper_model(model_name: str):
    """Lazy-load and cache whisper model by name."""
    import whisper

    return whisper.load_model(model_name)


def transcribe_uploaded_audio(file_bytes: bytes, suffix: str, model_name: str = "tiny") -> Tuple[str, str]:
    """
    Transcribe uploaded audio bytes with whisper.
    Returns (transcript, error).
    """
    tmp_path = ""
    try:
        model = load_whisper_model(model_name)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".wav") as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        result = model.transcribe(
            tmp_path,
            fp16=False,
            temperature=0,
            best_of=1,
            beam_size=1,
            language="en",
            condition_on_previous_text=False
        )
        transcript = (result.get("text") or "").strip()
        if not transcript:
            return "", "Could not detect speech in audio."
        return transcript, ""
    except ImportError:
        return "", "Whisper is not installed. Install with: pip install openai-whisper"
    except Exception as exc:
        return "", f"Voice transcription failed: {str(exc)}"
    finally:
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
