# agent/ranker.py
def rank_candidates(scored_list: list[dict]) -> list[dict]:
    for c in scored_list:
        c["combined_score"] = round(
            c["match_score"] * 0.60 + c["interest_score"] * 0.40, 1
        )
    return sorted(scored_list, key=lambda x: x["combined_score"], reverse=True)