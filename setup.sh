#!/bin/bash

set -e

echo ""
echo "================================================================"
echo "  Talent Scout Studio - FastAPI Setup"
echo "================================================================"
echo ""

echo "[1/4] Checking Python..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] Python 3.10+ is required."
  exit 1
fi
echo "[OK] $(python3 --version)"

echo ""
echo "[2/4] Checking Ollama..."
if ! command -v ollama >/dev/null 2>&1; then
  echo "[ERROR] Ollama is not installed."
  echo "        Download from: https://ollama.ai"
  exit 1
fi
echo "[OK] Ollama installed"

echo ""
echo "[3/4] Checking Ollama models..."
if ! ollama list | grep -q "tinyllama:latest"; then
  echo "[INFO] Downloading tinyllama:latest..."
  ollama pull tinyllama:latest
fi
echo "[OK] tinyllama:latest available"

if ! ollama list | grep -q "gemma2:2b"; then
  echo "[INFO] Downloading gemma2:2b..."
  ollama pull gemma2:2b
fi
echo "[OK] gemma2:2b available"

if ! ollama list | grep -q "nomic-embed-text"; then
  echo "[INFO] Downloading nomic-embed-text:latest..."
  ollama pull nomic-embed-text:latest
fi
echo "[OK] nomic-embed-text:latest available"

echo ""
echo "[4/4] Installing Python dependencies..."
python3 -m pip install -q -r requirements.txt
echo "[OK] Dependencies installed"

echo ""
echo "================================================================"
echo "  Setup complete."
echo "================================================================"
echo ""
echo "Next steps:"
echo "  1. Start Ollama: ollama serve"
echo "  2. Start the app: uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000"
echo "  3. Open: http://127.0.0.1:8000"
echo ""
