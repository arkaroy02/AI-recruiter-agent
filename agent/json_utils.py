"""Utilities to robustly parse JSON from model output."""

from __future__ import annotations

import json
import re
import ast
from typing import Any


def parse_json_from_text(text: str) -> Any:
    text = (text or "").strip()

    # Case 1: direct JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Case 2: fenced code block
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        block = fenced.group(1).strip()
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            pass

    # Case 3: first JSON object in raw text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        # Try strict parse first.
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass

        # Repair common LLM JSON issues (smart quotes, trailing commas).
        cleaned = (
            snippet.replace("“", '"')
            .replace("”", '"')
            .replace("’", "'")
            .replace("‘", "'")
        )
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Last fallback: python-literal style output.
        py_like = cleaned.replace("null", "None").replace("true", "True").replace("false", "False")
        return ast.literal_eval(py_like)

    raise json.JSONDecodeError("No valid JSON found in model output", text, 0)
