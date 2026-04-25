# Deployment

## Local Docker Deployment

This repository includes a Dockerized deployment for the FastAPI app plus Ollama.

Start it with:

```bash
docker compose up --build
```

Open:

`http://localhost:8000`

## What Docker Starts

- `ollama` for local inference
- `ollama_init` to download the required models
- `app` for `webapp.main:app`

## Models Pulled By Compose

- `tinyllama:latest`
- `gemma2:2b`
- `nomic-embed-text:latest`

## VPS Deployment

For a public server:

1. Create an Ubuntu VM with at least `8 GB RAM`
2. Install Docker and Docker Compose
3. Clone this repo
4. Run:

```bash
docker compose up --build -d
```

5. Open port `8000`
6. Visit `http://YOUR_SERVER_IP:8000`

## Security Note

Do not expose Ollama publicly unless you intend to. If you are deploying this on a VPS, consider binding port `11434` to localhost only or removing the host port mapping entirely.

## Main Entry Point

The container runs:

```bash
uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

## Current Public-Host Recommendation

If you want a production-style public deploy:

- keep Docker Compose for the app stack
- add Nginx or Caddy in front
- attach a domain
- enable HTTPS
