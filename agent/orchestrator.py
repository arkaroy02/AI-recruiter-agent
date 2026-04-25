# agent/orchestrator.py
"""
Main orchestration logic for the talent agent.
Coordinates JD parsing, candidate discovery, matching, conversations, and scoring.
"""
import json
from typing import List, Dict, Callable, Optional

from jd_parser import parse_jd
from embedder import index_candidates, find_top_candidates
from match_scorer import score_match
from covo_simulator import simulate_conversation
from interest_scorer import score_interest
from ranker import rank_candidates


ProgressCallback = Callable[[str, Dict], None]


def _emit(progress_cb: Optional[ProgressCallback], event: str, payload: Dict) -> None:
    """Emit progress events to UI/consumers when a callback is provided."""
    if progress_cb:
        progress_cb(event, payload)


def load_candidates(data_path: str = "data/candidates.json") -> List[Dict]:
    """Load candidate profiles from JSON file."""
    with open(data_path, 'r') as f:
        return json.load(f)


def initialize_candidate_index(candidates: List[Dict]):
    """Index all candidates for semantic search."""
    print(f"Indexing {len(candidates)} candidates...")
    index_candidates(candidates)
    print("Candidate index ready!")


def process_jd(jd_text: str, progress_cb: Optional[ProgressCallback] = None) -> Dict:
    """Parse job description and extract structured requirements."""
    print("\nParsing Job Description...")
    jd_parsed = parse_jd(jd_text)
    print(f"Role: {jd_parsed.get('role')}")
    print(f"   Required Skills: {', '.join(jd_parsed.get('required_skills', []))}")
    print(f"   Seniority: {jd_parsed.get('seniority')}")
    _emit(progress_cb, "jd_parsed", {"jd_parsed": jd_parsed})
    return jd_parsed


def find_candidates(
    jd_parsed: Dict,
    top_k: int = 5,
    progress_cb: Optional[ProgressCallback] = None
) -> List[Dict]:
    """Find top matching candidates based on JD."""
    print(f"\nFinding top {top_k} candidates...")
    candidates = find_top_candidates(jd_parsed, top_k=top_k)
    print(f"Found {len(candidates)} candidates")
    _emit(progress_cb, "candidates_found", {"count": len(candidates), "candidates": candidates})
    return candidates


def score_candidates(
    candidates: List[Dict],
    jd_parsed: Dict,
    progress_cb: Optional[ProgressCallback] = None
) -> List[Dict]:
    """Score each candidate for role match."""
    print("\nScoring candidate matches...")
    scored = []
    total = max(len(candidates), 1)
    for idx, candidate in enumerate(candidates, 1):
        match_result = score_match(candidate, jd_parsed)
        scored_candidate = {
            **candidate,
            "match_score": match_result["match_score"],
            "match_explanation": match_result["explanation"]
        }
        scored.append(scored_candidate)
        print(f"  {candidate['name']}: {match_result['match_score']}/100")
        _emit(progress_cb, "candidate_match_scored", {
            "index": idx,
            "total": total,
            "candidate": scored_candidate
        })
    return scored


def engage_candidates(
    candidates: List[Dict],
    jd_parsed: Dict,
    progress_cb: Optional[ProgressCallback] = None
) -> List[Dict]:
    """Simulate recruiter conversations with candidates."""
    print("\nSimulating recruiter conversations...")
    with_conversations = []
    
    total = max(len(candidates), 1)
    for idx, candidate in enumerate(candidates, 1):
        print(f"\n  Engaging with {candidate['name']}...")
        _emit(progress_cb, "candidate_interview_start", {
            "index": idx,
            "total": total,
            "candidate": candidate
        })
        conversation = []
        try:
            def _on_turn(message: Dict) -> None:
                _emit(progress_cb, "candidate_interview_turn", {
                    "index": idx,
                    "total": total,
                    "candidate": candidate,
                    "message": message
                })

            conversation = simulate_conversation(
                candidate,
                jd_parsed,
                turns=1,
                on_turn=_on_turn
            )
            interest_result = score_interest(conversation)
        except Exception as e:
            print(f"    Conversation simulation failed: {str(e)}")
            # Fallback: estimate interest based on openness
            openness_map = {"very open": 85, "somewhat open": 65, "passive": 40}
            interest_result = {
                "interest_score": openness_map.get(candidate.get("openness", "passive"), 50),
                "availability": "Unknown",
                "key_signals": [f"Candidate is {candidate.get('openness', 'unknown')} to opportunities"],
                "red_flags": []
            }
        
        enriched_candidate = {
            **candidate,
            "conversation": conversation,
            "interest_score": interest_result.get("interest_score", 0),
            "availability": interest_result.get("availability"),
            "key_signals": interest_result.get("key_signals", []),
            "red_flags": interest_result.get("red_flags", [])
        }
        with_conversations.append(enriched_candidate)
        print(f"    Interest Score: {interest_result.get('interest_score')}/100")
        print(f"    Availability: {interest_result.get('availability')}")
        _emit(progress_cb, "candidate_interest_scored", {
            "index": idx,
            "total": total,
            "candidate": enriched_candidate
        })
    
    return with_conversations


def run_match_only_pipeline(
    jd_text: str,
    candidates_data: List[Dict] = None,
    top_k: int = 5,
    progress_cb: Optional[ProgressCallback] = None
) -> Dict:
    """
    Run pipeline without simulated candidate conversations.
    Useful for "real interview" mode where a human candidate responds live.
    """
    if candidates_data is None:
        candidates_data = load_candidates()

    _emit(progress_cb, "stage_start", {
        "stage": "indexing",
        "message": "Indexing candidate database...",
        "progress": 15
    })
    initialize_candidate_index(candidates_data)

    _emit(progress_cb, "stage_start", {
        "stage": "parsing_jd",
        "message": "Parsing job description...",
        "progress": 35
    })
    jd_parsed = process_jd(jd_text, progress_cb=progress_cb)

    _emit(progress_cb, "stage_start", {
        "stage": "matching",
        "message": f"Finding top {top_k} matching candidates...",
        "progress": 55
    })
    matched_candidates = find_candidates(jd_parsed, top_k=top_k, progress_cb=progress_cb)

    _emit(progress_cb, "stage_start", {
        "stage": "scoring_match",
        "message": "Scoring candidate-role fit...",
        "progress": 80
    })
    match_scored = score_candidates(matched_candidates, jd_parsed, progress_cb=progress_cb)

    ranked = sorted(match_scored, key=lambda item: item.get("match_score", 0), reverse=True)
    real_ready = []
    for candidate in ranked:
        real_ready.append({
            **candidate,
            "conversation": [],
            "interest_score": 0.0,
            "availability": "Pending real interview",
            "key_signals": [],
            "red_flags": [],
            "combined_score": round(float(candidate.get("match_score", 0)), 1)
        })

    results = {
        "jd_parsed": jd_parsed,
        "ranked_candidates": real_ready,
        "total_processed": len(real_ready),
        "pipeline_mode": "real"
    }
    _emit(progress_cb, "pipeline_complete", {"progress": 100, "results": results})
    return results


def run_full_pipeline(
    jd_text: str,
    candidates_data: List[Dict] = None,
    top_k: int = 5,
    progress_cb: Optional[ProgressCallback] = None
):
    """
    Run the complete talent agent pipeline:
    1. Parse JD
    2. Find candidates
    3. Score matches
    4. Simulate conversations
    5. Rank by combined score
    """
    if candidates_data is None:
        candidates_data = load_candidates()
    
    # Initialize candidate index
    _emit(progress_cb, "stage_start", {
        "stage": "indexing",
        "message": "Indexing candidate database...",
        "progress": 10
    })
    initialize_candidate_index(candidates_data)
    
    # Parse JD
    _emit(progress_cb, "stage_start", {
        "stage": "parsing_jd",
        "message": "Parsing job description...",
        "progress": 25
    })
    jd_parsed = process_jd(jd_text, progress_cb=progress_cb)
    
    # Find candidates
    _emit(progress_cb, "stage_start", {
        "stage": "matching",
        "message": f"Finding top {top_k} matching candidates...",
        "progress": 40
    })
    matched_candidates = find_candidates(jd_parsed, top_k=top_k, progress_cb=progress_cb)
    
    # Score matches
    _emit(progress_cb, "stage_start", {
        "stage": "scoring_match",
        "message": "Scoring candidate-role fit...",
        "progress": 55
    })
    match_scored = score_candidates(matched_candidates, jd_parsed, progress_cb=progress_cb)
    
    # Engage candidates
    _emit(progress_cb, "stage_start", {
        "stage": "interview",
        "message": "Simulating recruiter interviews and scoring interest...",
        "progress": 75
    })
    with_interest = engage_candidates(match_scored, jd_parsed, progress_cb=progress_cb)
    
    # Rank by combined score
    _emit(progress_cb, "stage_start", {
        "stage": "ranking",
        "message": "Ranking candidates by combined score...",
        "progress": 90
    })
    ranked = rank_candidates(with_interest)

    results = {
        "jd_parsed": jd_parsed,
        "ranked_candidates": ranked,
        "total_processed": len(ranked)
    }
    _emit(progress_cb, "pipeline_complete", {"progress": 100, "results": results})
    return results


def format_results(results: Dict) -> str:
    """Format results for display."""
    output = []
    output.append("\n" + "="*80)
    output.append("TALENT SCOUT RESULTS")
    output.append("="*80)
    
    output.append(f"\nRole: {results['jd_parsed'].get('role')}")
    output.append(f"Total Candidates Processed: {results['total_processed']}")
    
    output.append("\nTOP RANKED CANDIDATES:\n")
    
    for i, cand in enumerate(results['ranked_candidates'][:5], 1):
        output.append(f"{i}. {cand['name']} ({cand['title']})")
        output.append(f"   Combined Score: {cand.get('combined_score', 0)}/100")
        output.append(f"   Match Score: {cand.get('match_score', 0):.1f} | Interest Score: {cand.get('interest_score', 0)}")
        output.append(f"   Availability: {cand.get('availability', 'Unknown')}")
        output.append(f"   Key Signals: {', '.join(cand.get('key_signals', [])[:2])}")
        output.append("")
    
    output.append("="*80)
    return "\n".join(output)


if __name__ == "__main__":
    # Load sample JD
    with open("tests/sample_jd.txt", "r") as f:
        sample_jd = f.read()
    
    # Run pipeline
    results = run_full_pipeline(sample_jd, top_k=5)
    
    # Display results
    print(format_results(results))
