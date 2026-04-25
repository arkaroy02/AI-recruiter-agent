# OpenRouter Integration Guide

## What Changed

Your talent agent now uses **OpenRouter** instead of Hugging Face for better model access:

### Benefits:
✅ **Better Models** — Access to Claude, GPT-4, Llama, Gemini, Mistral  
✅ **Free Tier** — Llama-3.1-8B, Gemini Flash, and more at no cost  
✅ **Faster Responses** — Optimized routing and infrastructure  
✅ **More Reliable** — Better uptime than HF free tier  

## Setup (2 minutes)

### 1. Get Your Free OpenRouter API Key

1. Visit: **https://openrouter.ai/keys**
2. Sign up (GitHub/Google login available)
3. Click "Create Key"
4. Copy your API key

### 2. Update Your `.env` File

Open `.env` and replace the placeholder:
```bash
HF_TOKEN=sk-or-v1-your-key-here
```

### 3. Test It

```bash
python agent/hf_api_client.py
```

## Available Models

### Free Tier (No Cost)
| Model | Best For | Speed |
|-------|----------|-------|
| `meta-llama/llama-3.1-8b-instruct:free` | General chat, parsing | Fast |
| `google/gemini-flash-1.5` | Conversations, interviews | Very Fast |
| `mistralai/mistral-7b-instruct:free` | Balanced quality/speed | Fast |

### Paid Tier (Better Quality)
| Model | Best For | Cost |
|-------|----------|------|
| `anthropic/claude-3.5-sonnet` | Best quality interviews | ~$3/1M tokens |
| `openai/gpt-4o-mini` | Reasoning, parsing | ~$0.15/1M tokens |
| `meta-llama/llama-3.1-70b-instruct` | Complex tasks | ~$0.9/1M tokens |

## Current Configuration

Your `.env` is set to use:
- **Chat**: `meta-llama/llama-3.1-8b-instruct:free` (free, fast)
- **Interviews**: `google/gemini-flash-1.5` (free, great for conversations)
- **Embeddings**: Local (keyword-based, instant)

## Switching Models

Edit `.env` to change models:

```bash
# For better quality (paid):
HF_CHAT_MODEL=anthropic/claude-3.5-sonnet
HF_INTERVIEW_MODEL=anthropic/claude-3.5-sonnet

# For faster responses (free):
HF_CHAT_MODEL=google/gemini-flash-1.5
HF_INTERVIEW_MODEL=google/gemini-flash-1.5
```

## Pricing

- **Free tier**: ~1000 requests/day with Llama-3.1-8B
- **Paid models**: Pay per token, very affordable
- **Estimate**: $5-10/month for typical usage

## Troubleshooting

### "401 Unauthorized"
- Check your API key in `.env`
- Ensure key starts with `sk-or-v1-`

### "Model not found"
- Check model name at https://openrouter.ai/models
- Ensure model ID includes provider (e.g., `meta-llama/llama-3.1-8b-instruct:free`)

### Slow responses
- Switch to `google/gemini-flash-1.5` (fastest)
- Or use local fallback (automatic)

## Next Steps

1. Get your OpenRouter API key
2. Update `.env` with your key
3. Run: `python agent/hf_api_client.py` to test
4. Start the app: `uvicorn webapp.main:app --reload`

Your talent agent will now use much better AI models! 🚀
