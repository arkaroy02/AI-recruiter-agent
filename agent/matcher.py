"""Backwards-compatible matcher API."""

from embedder import embed_text, find_top_candidates, index_candidates
from hf_api_client import rerank_candidates

__all__ = ["embed_text", "index_candidates", "find_top_candidates", "rerank_candidates"]
