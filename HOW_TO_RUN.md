# How To Run

## Local Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start Ollama:

```bash
ollama serve
```

3. Download the required models if needed:

```bash
ollama pull tinyllama:latest
ollama pull gemma2:2b
ollama pull nomic-embed-text:latest
```

4. Start the FastAPI app:

```bash
uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

5. Open:

`http://127.0.0.1:8000`

## What To Expect

- `Shortlist View` shows the ranked candidates and recruiter insight panel.
- `Interview Studio` appears when you run the pipeline in `Real` mode.
- Resume uploads support text-based PDFs.
- Live voice works best in Chrome or Edge.

## Useful Commands

Run the smoke test script:

```bash
python test_demo.py
```

Run the orchestration pipeline directly:

```bash
python agent/orchestrator.py
```

## Legacy Note

The repository still contains `app.py`, which is an older Streamlit prototype. The current maintained entry point is `webapp.main:app`.
