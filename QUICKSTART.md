# Quickstart

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Start Ollama

```bash
ollama serve
```

## 3. Make sure the models exist

```bash
ollama pull tinyllama:latest
ollama pull gemma2:2b
ollama pull nomic-embed-text:latest
```

## 4. Start the web app

```bash
uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

## 5. Open the browser

`http://127.0.0.1:8000`

## Notes

- Use `Real` mode for the live recruiter interview experience.
- Use `Demo` mode if you want the system to simulate candidate engagement.
- `app.py` is a legacy Streamlit prototype; the primary app is the FastAPI web UI.
