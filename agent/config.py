"""Central config for model settings and API keys."""

from __future__ import annotations

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===== OpenRouter API Configuration =====
# OpenRouter provides access to Claude, GPT-4, Llama, Gemini, and more
OPENROUTER_API_KEY = os.getenv("OPEN_ROUTER_TOKEN") or os.getenv("HF_TOKEN", "")

# Model configuration for OpenRouter
# Affordable, high-quality models (no rate limits like free tier)
# Pricing: https://openrouter.ai/models
HF_CHAT_MODEL = os.getenv("HF_CHAT_MODEL", "deepseek/deepseek-chat")  # $0.14/1M tokens
HF_INTERVIEW_MODEL = os.getenv("HF_INTERVIEW_MODEL", "google/gemini-2.0-flash-001")  # $0.10/1M tokens
HF_EMBED_MODEL = os.getenv("HF_EMBED_MODEL", "local")

# ===== Legacy Compatibility =====
# Keep HF_TOKEN for backward compatibility with existing code
HF_TOKEN = OPENROUTER_API_KEY

# Legacy Ollama names (some older entry points still use these)
CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", HF_CHAT_MODEL)
INTERVIEW_MODEL = os.getenv("OLLAMA_INTERVIEW_MODEL", HF_INTERVIEW_MODEL)
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", HF_EMBED_MODEL)
OLLAMA_HOST = os.getenv("OLLAMA_HOST") or os.getenv("OLLAMA_BASE_URL")
