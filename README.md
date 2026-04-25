# Talent Scout Studio

FastAPI-based talent scouting demo that:

- parses a job description
- ranks candidate profiles or uploaded resume PDFs
- runs either a demo pipeline or a live recruiter interview flow
- updates shortlist scores with interview signals, flags, and recruiter notes

## Primary App

The main app is the FastAPI web UI in `webapp/`, served by:

```bash
uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

`http://127.0.0.1:8000`

## Models

This repo currently uses:

- `tinyllama:latest` for lightweight structured/demo tasks
- `gemma2:2b` for live recruiter interview turns
- `nomic-embed-text:latest` for embeddings

Install them with:

```bash
ollama pull tinyllama:latest
ollama pull gemma2:2b
ollama pull nomic-embed-text:latest
```

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start Ollama:

```bash
ollama serve
```

3. Start the app:

```bash
uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

4. Open the browser:

`http://127.0.0.1:8000`

## Core Folders

```text
agent/      pipeline, parsing, scoring, embeddings, interview logic
webapp/     FastAPI routes, frontend assets, templates, web services
data/       sample candidate dataset
tests/      sample job description
```

## Current Flow

- `Demo` mode runs ranking plus simulated candidate engagement.
- `Real` mode skips the fake candidate conversation and lets you run a live recruiter interview.
- Uploaded PDF resumes override the sample dataset for the current session.
- Candidate cards in the shortlist include recruiter-style recommendations, pros, watchouts, and next steps.

## Deployment

For local or server deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Legacy Note

`app.py` is an older Streamlit prototype kept for reference. The actively maintained app path is `webapp.main:app`.
