# agent/jd_parser.py

import re

from json_utils import parse_json_from_text
from hf_api_client import generate_text

PARSE_PROMPT = """
Extract from the job description below a JSON object with these keys:
- role (string)
- required_skills (list of strings)
- preferred_skills (list of strings)
- min_years_exp (integer)
- seniority (junior/mid/senior/lead)
- domain (e.g. "fintech", "healthcare", "saas")

Return ONLY valid JSON, no explanation.

JD:
{jd_text}
"""

SKILL_PATTERNS = [
    "python", "java", "javascript", "typescript", "react", "node.js", "node", "fastapi",
    "django", "flask", "spring", "postgresql", "mysql", "mongodb", "redis", "aws", "gcp",
    "azure", "docker", "kubernetes", "graphql", "kafka", "rabbitmq", "rest", "golang", "go",
    "rust", "spark", "airflow", "terraform", "sql", "system design"
]


def _extract_section(text: str, heading: str) -> str:
    pattern = rf"{heading}\s*:?\s*(.*?)(?:\n[A-Z][A-Za-z /]+:|\Z)"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    seen = set()
    for skill in SKILL_PATTERNS:
        if skill in lowered and skill not in seen:
            seen.add(skill)
            if skill == "node":
                label = "Node.js"
            elif skill == "go":
                label = "Go"
            else:
                label = skill.title()
            found.append(label)
    return found


def _infer_seniority(title: str, text: str) -> str:
    lowered = f"{title} {text}".lower()
    if "lead" in lowered or "staff" in lowered or "principal" in lowered:
        return "lead"
    if "senior" in lowered:
        return "senior"
    if "junior" in lowered or "entry" in lowered:
        return "junior"
    return "mid"


def _infer_domain(text: str) -> str:
    lowered = text.lower()
    for domain in ["fintech", "healthcare", "saas", "ecommerce", "ai", "edtech", "payments"]:
        if domain in lowered:
            return domain
    return "general"


def _fallback_parse_jd(jd_text: str) -> dict:
    lines = [line.strip() for line in jd_text.splitlines() if line.strip()]
    role = lines[0] if lines else "Unknown Role"
    required_text = _extract_section(jd_text, "Required Qualifications") or _extract_section(jd_text, "Requirements")
    preferred_text = _extract_section(jd_text, "Preferred Qualifications") or _extract_section(jd_text, "Nice to Have")

    years_match = re.search(r"(\d{1,2})\+?\s+years", jd_text, flags=re.IGNORECASE)
    min_years = int(years_match.group(1)) if years_match else 0

    required_skills = _extract_skills(required_text) or _extract_skills(jd_text)[:8]
    preferred_skills = _extract_skills(preferred_text)

    return {
        "role": role,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "min_years_exp": min_years,
        "seniority": _infer_seniority(role, jd_text),
        "domain": _infer_domain(jd_text),
    }


def parse_jd(jd_text: str) -> dict:
    try:
        # Use HF API to parse job description
        prompt = PARSE_PROMPT.format(jd_text=jd_text)
        raw = generate_text(prompt, max_length=500)
        parsed = parse_json_from_text(raw)
        return {
            "role": parsed.get("role") or _fallback_parse_jd(jd_text)["role"],
            "required_skills": parsed.get("required_skills") or _fallback_parse_jd(jd_text)["required_skills"],
            "preferred_skills": parsed.get("preferred_skills") or [],
            "min_years_exp": int(parsed.get("min_years_exp", 0) or 0),
            "seniority": parsed.get("seniority") or _infer_seniority(parsed.get("role", ""), jd_text),
            "domain": parsed.get("domain") or _infer_domain(jd_text),
        }
    except Exception:
        return _fallback_parse_jd(jd_text)
