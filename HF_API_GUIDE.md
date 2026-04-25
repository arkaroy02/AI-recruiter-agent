# Using Hugging Face API Instead of Ollama

## 1. Setup
Your `.env` file already has:
```
HF_TOKEN=your_huggingface_api_key_here
```

Make sure you add your actual HF token there.

## 2. Available Free Models

| Task | Model | Speed | Quality |
|------|-------|-------|---------|
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | Fast | Good |
| **Text Generation** | `google/flan-t5-base` | Very Fast | Good |
| **Chat/QA** | `mistralai/Mistral-7B-Instruct-v0.1` | Medium | Excellent |
| **Sentiment** | `distilbert-base-uncased-finetuned-sst-2-english` | Fast | Good |
| **Q&A Extraction** | `deepset/roberta-base-squad2` | Fast | Excellent |

## 3. Quick Start Examples

### Replace Embedder (embedder.py)

**Current (Ollama):**
```python
from ollama_client import get_ollama_client
from config import EMBED_MODEL

def embed_text(text: str):
    ollama_client = get_ollama_client()
    r = ollama_client.embeddings(model=EMBED_MODEL, prompt=text)
    return r["embedding"]
```

**New (Hugging Face API):**
```python
from hf_api_client import embed_text

# That's it! Same function name, uses HF API instead
embedding = embed_text("candidate summary text")
```

### Replace Chat/Generation (interest_scorer.py)

**Current (Ollama):**
```python
from ollama_client import get_ollama_client
from config import CHAT_MODEL

def score_interest():
    client = get_ollama_client()
    response = client.generate(model=CHAT_MODEL, prompt=prompt)
    return response["response"]
```

**New (Hugging Face API):**
```python
from hf_api_client import generate_text

# Generate interest scoring response
response = generate_text(prompt, max_length=500)
```

## 4. Full Integration Example

Replace `embedder.py` usage:
```python
# OLD
from ollama_client import get_ollama_client
from config import EMBED_MODEL

def embed_text(text):
    client = get_ollama_client()
    r = client.embeddings(model=EMBED_MODEL, prompt=text)
    return r["embedding"]

# NEW
from hf_api_client import embed_text
# No changes needed to function calls!
```

## 5. Features of hf_api_client.py

✅ **Automatic Retries** - Handles timeouts and rate limits  
✅ **Model Loading Waits** - Auto-waits if model is loading  
✅ **Error Handling** - Clear error messages  
✅ **Rate Limit Smart Waiting** - Respects 429 responses  

## 6. Usage Options

### Option A: Gradual Migration (Recommended)
Keep both Ollama + HF API, use HF API only where needed:
- Use HF embeddings for matching
- Use Ollama for interviews (keep conversational flow)

### Option B: Full Migration
Replace all Ollama calls with HF API:
- Update `embedder.py` → use `hf_api_client.embed_text()`
- Update `interest_scorer.py` → use `hf_api_client.generate_text()`
- Update `orchestrator.py` → use HF models

### Option C: Fallback Strategy
Keep Ollama as backup, try HF first:
```python
from hf_api_client import embed_text as hf_embed
from embedder import embed_text as ollama_embed

def embed_with_fallback(text):
    try:
        return hf_embed(text)
    except Exception as e:
        print(f"HF API failed: {e}, falling back to Ollama")
        return ollama_embed(text)
```

## 7. Test It

```bash
# Test the HF API client
python agent/hf_api_client.py
```

## 8. Important Notes

⚠️ **Free Tier Limitations:**
- 30,000 requests/month
- Shared infrastructure (slower during peak)
- Models may need to load first time (~30s)

💡 **Tips:**
- Cache embeddings to avoid re-computing
- Use `google/flan-t5-base` for faster responses
- Use `mistralai/Mistral-7B` for better quality (slower)

Which integration would you like me to implement?
