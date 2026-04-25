"""
OpenRouter client for chat generation and semantic embeddings.

Chat uses OpenRouter API for access to best-in-class models (Claude, GPT-4, Llama, etc).
Embeddings use a lightweight local vector when remote models are unavailable.
"""

from __future__ import annotations

import re
import time

import requests

from config import OPENROUTER_API_KEY, EMBED_MODEL  # Updated to use OpenRouter key


# OpenRouter API endpoints
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_EMBED_URL = "https://openrouter.ai/api/v1/embeddings"
OPENROUTER_RERANK_URL = "https://openrouter.ai/api/v1/rerank"

# Best affordable models on OpenRouter
# See pricing at: https://openrouter.ai/models
# All models below are high quality with minimal cost
CHAT_MODELS = {
    "default": "deepseek/deepseek-chat",  # $0.14/1M tokens - Excellent quality/price
    "fast": "google/gemini-flash-1.5",  # $0.075/1M tokens - Fast & capable
    "quality": "anthropic/claude-3.5-sonnet",  # $3/1M tokens - Best quality
    "interview": "google/gemini-flash-1.5",  # $0.075/1M tokens - Great for interviews
    "reasoning": "deepseek/deepseek-reasoner",  # $0.55/1M tokens - Deep reasoning
}

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/talent-agent",  # Optional, for rankings
    "X-Title": "Talent Agent",  # Optional, for rankings
}


def _simple_embedding(text: str) -> list[float]:
    """
    Lightweight fallback embedding using skill keywords and text features.
    This is only used when the configured HF embedding model is unavailable.
    """
    words = re.findall(r"\b\w+\b", text.lower())
    embedding = [0.0] * 384
    skills = {
        "python": 0, "javascript": 1, "java": 2, "c": 3, "rust": 4,
        "react": 10, "vue": 11, "angular": 12, "nodejs": 13, "express": 14,
        "aws": 20, "azure": 21, "gcp": 22, "kubernetes": 23, "docker": 24,
        "sql": 30, "mongodb": 31, "postgres": 32, "mysql": 33,
        "machine": 40, "learning": 41, "ai": 42, "deep": 43, "neural": 44,
        "devops": 50, "ci": 51, "cd": 52, "git": 53, "jenkins": 54,
        "years": 60, "experience": 61, "senior": 62, "junior": 63, "lead": 64,
    }

    normalized_words = [word.replace("++", "") for word in words]
    for word in normalized_words:
        if word in skills:
            embedding[skills[word]] = 1.0

    embedding[100] = len(words) / 100.0
    embedding[101] = normalized_words.count("senior")
    embedding[102] = normalized_words.count("junior")

    magnitude = sum(value**2 for value in embedding) ** 0.5
    if magnitude > 0:
        embedding = [value / magnitude for value in embedding]
    return embedding


def _mean_pool_embedding(payload: object) -> list[float]:
    if not isinstance(payload, list) or not payload:
        return []

    if all(isinstance(value, (int, float)) for value in payload):
        return [float(value) for value in payload]

    if len(payload) == 1 and isinstance(payload[0], list):
        first = payload[0]
        if all(isinstance(value, (int, float)) for value in first):
            return [float(value) for value in first]
        token_vectors = first
    else:
        token_vectors = payload

    vectors = [
        [float(value) for value in vector]
        for vector in token_vectors
        if isinstance(vector, list) and vector and all(isinstance(value, (int, float)) for value in vector)
    ]
    if not vectors:
        return []

    dimensions = len(vectors[0])
    same_size_vectors = [vector for vector in vectors if len(vector) == dimensions]
    pooled = [sum(vector[idx] for vector in same_size_vectors) / len(same_size_vectors) for idx in range(dimensions)]
    magnitude = sum(value**2 for value in pooled) ** 0.5
    if magnitude > 0:
        pooled = [value / magnitude for value in pooled]
    return pooled


def embed_text(text: str) -> list[float]:
    """
    Generate embeddings using local fallback (OpenRouter doesn't support embeddings).
    Uses simple keyword-based embeddings for candidate matching.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return _simple_embedding("")
    
    # Always use local embeddings (OpenRouter doesn't provide embedding API)
    return _simple_embedding(cleaned)


def _simple_text_generation(prompt: str, max_length: int = 200) -> str:
    lowered = (prompt or "").lower()
    if "interest" in lowered and "score" in lowered:
        return """
{
  "interest_score": 72,
  "availability": "1-3 months",
  "key_signals": ["expressed enthusiasm for the role", "mentioned alignment with company mission"],
  "red_flags": ["concerned about salary", "has notice period"]
}
        """
    if "interview" in lowered or "question" in lowered:
        return "Thanks for joining today. Could you walk me through a recent project that best shows your fit for this role?"
    if "generate" in lowered and ("question" in lowered or "ask" in lowered):
        return "What attracted you to this role, and how does it fit with the kind of work you want to do next?"
    return "Based on your background, this could be a good opportunity. Let me know your thoughts."


def _resolve_model(model: str | None, prompt: str) -> str:
    if model:
        return model
    lowered = prompt.lower()
    if "interview" in lowered or "recruiter" in lowered or "candidate" in lowered:
        return "interview"
    return "default"


def _model_candidates(model: str) -> list[str]:
    candidates = [model]
    if model in {"interview", "quality"}:
        candidates.extend(["default", "fast"])
    elif model == "default":
        candidates.append("fast")
    return list(dict.fromkeys(candidates))


def generate_text(
    prompt: str,
    model: str = None,
    max_length: int = 150,
    temperature: float = 0.7,
) -> str:
    """
    Generate text with OpenRouter models (Llama, Claude, GPT-4, Gemini, etc).
    Falls back through quality models to fast models to local rule-based responses.
    """
    if prompt is None:
        prompt = ""
    model = _resolve_model(model, prompt)

    if not OPENROUTER_API_KEY:
        print("OPENROUTER_API_KEY not set, using simple text generation")
        return _simple_text_generation(prompt, max_length)

    for model_key in _model_candidates(model):
        model_id = CHAT_MODELS.get(model_key, CHAT_MODELS["default"])
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": model_id,
            "temperature": temperature,
            "max_tokens": max_length,
        }

        for attempt in range(2):
            try:
                print(f"📤 Sending to OpenRouter: {model_id}...")
                response = requests.post(OPENROUTER_API_URL, headers=HEADERS, json=payload, timeout=30)

                if response.status_code != 200:
                    print(f"⚠️ HTTP {response.status_code}: {response.text}")
                    if response.status_code == 429 and attempt == 0:
                        print("Rate limited, retrying...")
                        time.sleep(5)
                        continue
                    break

                result = response.json()
                if "error" in result:
                    print(f"⚠️ API Error: {result['error']}")
                    if attempt == 0:
                        time.sleep(3)
                        continue
                    break

                choices = result.get("choices") or []
                if choices:
                    generated = (choices[0].get("message") or {}).get("content", "")
                    if generated:
                        print(f"✅ Generated: {generated[:100]}...")
                        return generated

                print("⚠️ Unexpected response format")
                break
            except requests.exceptions.Timeout:
                print(f"⏱️ Timeout on attempt {attempt + 1}/2")
                if attempt == 0:
                    time.sleep(3)
                else:
                    break
            except requests.exceptions.ConnectionError as exc:
                print(f"⚠️ Connection Error: {exc}")
                break
            except Exception as exc:
                print(f"⚠️ Error: {exc}")
                break

    print("Failed to generate text via API, using fallback")
    return _simple_text_generation(prompt, max_length)


def rerank_candidates(query: str, candidates: list[dict], top_k: int = 10) -> list[dict]:
    """
    Rerank candidates using Cohere Rerank v3.5 for improved relevance.
    
    Takes a JD query and list of candidates, returns top_k reranked by relevance.
    Falls back to original order if reranking fails.
    """
    if not candidates or not query:
        return candidates[:top_k]
    
    # Return early if we don't have more candidates than requested
    if len(candidates) <= top_k:
        return candidates
    
    if not OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY not set, skipping reranking")
        return candidates[:top_k]
    
    # Build document strings for reranking
    documents = []
    for c in candidates:
        doc_text = f"{c.get('title', '')} {' '.join(c.get('skills', []))} {c.get('summary', '')}"
        documents.append(doc_text.strip())
    
    payload = {
        "model": "cohere/rerank-v3.5",
        "query": query,
        "documents": documents,
        "top_n": top_k,
    }
    
    try:
        print(f"📤 Reranking {len(candidates)} candidates with Cohere...")
        response = requests.post(OPENROUTER_RERANK_URL, headers=HEADERS, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"⚠️ Rerank API HTTP {response.status_code}: {response.text}")
            return candidates[:top_k]
        
        result = response.json()
        if "error" in result:
            print(f"⚠️ Rerank API Error: {result['error']}")
            return candidates[:top_k]
        
        # Extract reranked indices
        results = result.get("results", [])
        if results:
            # Reorder candidates based on rerank results
            reranked = []
            for res in results:
                idx = res.get("index")
                if idx is not None and 0 <= idx < len(candidates):
                    reranked.append(candidates[idx])
            return reranked[:top_k] if reranked else candidates[:top_k]
        
        return candidates[:top_k]
    except Exception as e:
        print(f"⚠️ Reranking failed: {e}, using original order")
        return candidates[:top_k]


if __name__ == "__main__":
    print("🧪 Testing OpenRouter client...")
    embedding = embed_text("I am a Python developer with 5 years experience")
    print(f"✅ Got embedding of length: {len(embedding)}")
    response = generate_text("Generate an interview question for a Python backend engineer:", max_length=100)
    print(f"✅ Generated: {response}")
