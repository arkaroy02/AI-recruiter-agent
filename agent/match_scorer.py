# agent/match_scorer.py

def score_match(candidate: dict, jd: dict) -> dict:
    c_skills = set(s.lower() for s in candidate["skills"])
    req = set(s.lower() for s in jd["required_skills"])
    pref = set(s.lower() for s in jd["preferred_skills"])

    required_hit = len(c_skills & req) / max(len(req), 1)
    preferred_hit = len(c_skills & pref) / max(len(pref), 1)

    exp_gap = candidate["years_exp"] - jd["min_years_exp"]
    exp_score = min(1.0, max(0.0, 0.5 + exp_gap * 0.1))

    match_score = (required_hit * 0.55) + (preferred_hit * 0.25) + (exp_score * 0.20)

    return {
        "match_score": round(match_score * 100, 1),
        "explanation": {
            "required_skills_hit": list(c_skills & req),
            "required_skills_missing": list(req - c_skills),
            "preferred_skills_hit": list(c_skills & pref),
            "exp_delta": exp_gap
        }
    }