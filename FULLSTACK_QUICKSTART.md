# Full Frontend Quickstart (FastAPI + JS)

This project now includes a full web frontend (non-Streamlit) in `webapp/`.

## 1) Install dependencies

Use the environment you already use for this project:

```powershell
conda run -n base python -m pip install -r requirements.txt
```

## 2) Start Ollama

```powershell
ollama serve
```

Ensure models exist:

```powershell
ollama pull tinyllama:latest
ollama pull gemma2:2b
ollama pull nomic-embed-text:latest
```

## 3) Run full web app

From repo root:

```powershell
conda run -n base uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

`http://127.0.0.1:8000`

## What is included

- Modern UI with candidate cards and summary metrics
- Demo mode pipeline (AI vs AI interview simulation)
- Real mode interview console:
  - Start/respond/reset per candidate
  - Live transcript thread
  - Re-scoring after each human response
  - Audio upload transcription endpoint

## Optional voice setup

If you want transcription:

```powershell
conda run -n base python -m pip install openai-whisper
conda install -n base -c conda-forge ffmpeg -y
```
