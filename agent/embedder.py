# agent/embedder.py + matcher.py
from __future__ import annotations

from math import sqrt
from typing import Any

from hf_api_client import embed_text as hf_embed_text, rerank_candidates

_indexed_candidates: list[dict[str, Any]] = []
_indexed_embeddings: list[list[float]] = []

def embed_text(text: str) -> list[float]:
    """Generate embeddings using Hugging Face API."""
    return hf_embed_text(text)

def index_candidates(candidates: list[dict]):
    global _indexed_candidates, _indexed_embeddings
    _indexed_candidates = []
    _indexed_embeddings = []

    for c in candidates:
        text = f"{c['title']} {' '.join(c['skills'])} {c['summary']}"
        _indexed_candidates.append(c)
        _indexed_embeddings.append(embed_text(text))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def find_top_candidates(jd_parsed: dict, top_k=10) -> list[dict]:
    if not _indexed_candidates:
        return []

    query = f"{jd_parsed['role']} {' '.join(jd_parsed['required_skills'])}"
    query_embedding = embed_text(query)

    scored = []
    for candidate, candidate_embedding in zip(_indexed_candidates, _indexed_embeddings):
        score = _cosine_similarity(query_embedding, candidate_embedding)
        scored.append((score, candidate))

    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Get a larger candidate pool for reranking
    # Rerank uses semantic + multi-aspect matching for better results
    rerank_pool_size = min(len(scored), max(top_k * 2, 20))
    candidates_for_rerank = [candidate for _, candidate in scored[:rerank_pool_size]]
    
    # Apply Cohere reranking if we have multiple candidates
    if len(candidates_for_rerank) > top_k:
        reranked = rerank_candidates(query, candidates_for_rerank, top_k)
        return reranked
    
    return candidates_for_rerank[:top_k]
