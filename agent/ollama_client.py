"""Shared Ollama client factory."""

from __future__ import annotations

import ollama

from config import OLLAMA_HOST


def get_ollama_client() -> ollama.Client:
    if OLLAMA_HOST:
        return ollama.Client(host=OLLAMA_HOST)
    return ollama.Client()
