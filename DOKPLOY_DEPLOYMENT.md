# Dokploy Deployment Guide

## Prerequisites
- GitHub repository: https://github.com/arkaroy02/AI-recruiter-agent
- OpenRouter API key (get free at https://openrouter.ai/keys)

## Deployment Steps

### Step 1: Push Latest Code to GitHub
```bash
git add .
git commit -m "Add production deployment files"
git push origin main
```

### Step 2: Create Application in Dokploy

1. Go to your Dokploy dashboard
2. Navigate to your project
3. Click **Applications** → **Create Application**

### Step 3: Configure General Settings

| Setting | Value |
|---------|-------|
| **Name** | `talent-scout` |
| **Description** | AI-powered talent scouting application |
| **Source** | GitHub |
| **Repository** | `arkaroy02/AI-recruiter-agent` |
| **Branch** | `main` |
| **Build Type** | `Dockerfile` |
| **Dockerfile Path** | `Dockerfile.prod` |

### Step 4: Configure Environment Variables

Go to **Environment** tab and add:

```
OPEN_ROUTER_TOKEN=your_openrouter_api_key_here
HF_CHAT_MODEL=meta-llama/llama-3.1-8b-instruct:free
HF_INTERVIEW_MODEL=google/gemini-flash-1.5
HF_EMBED_MODEL=local
```

**Important:** Replace `your_openrouter_api_key_here` with your actual OpenRouter API key.

### Step 5: Configure Domain

Go to **Domains** tab:

**Option A: Custom Domain**
- Domain: `talent-scout.yourdomain.com`
- Port: `8000`
- HTTPS: Enable (recommended)

**Option B: Generated Domain**
- Click "Generate Domain" for a free `traefik.me` subdomain

### Step 6: Deploy

1. Click **Deploy** button
2. Wait for build to complete (2-3 minutes)
3. Check **Logs** tab for any errors

### Step 7: Verify Deployment

1. Open your domain in browser
2. Test the application:
   - Enter a job description
   - Click "Run Pipeline"
   - Verify candidates are ranked

## Troubleshooting

### Build Fails
- Check **Logs** tab for error details
- Verify `Dockerfile.prod` exists in repository
- Ensure all files are committed to GitHub

### Application Won't Start
- Check environment variables are set correctly
- Verify `OPEN_ROUTER_TOKEN` is valid
- Check logs for API connection errors

### API Errors
- Verify OpenRouter API key is active
- Check API rate limits at https://openrouter.ai/
- Try a different model if current one is unavailable

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPEN_ROUTER_TOKEN` | Yes | - | Your OpenRouter API key |
| `HF_CHAT_MODEL` | No | `meta-llama/llama-3.1-8b-instruct:free` | Model for JD parsing & matching |
| `HF_INTERVIEW_MODEL` | No | `google/gemini-flash-1.5` | Model for interview simulation |
| `HF_EMBED_MODEL` | No | `local` | Embedding model (local = keyword-based) |

## Available Free Models on OpenRouter

- `meta-llama/llama-3.1-8b-instruct:free` - Good for general tasks
- `google/gemini-flash-1.5` - Fast and capable
- `qwen/qwen-2-7b-instruct:free` - Alternative option

See all models: https://openrouter.ai/models

## Auto-Deploy Setup

To automatically deploy on git push:

1. Go to **Deployments** tab
2. Copy the webhook URL
3. In GitHub repo → Settings → Webhooks → Add webhook
4. Paste the webhook URL
5. Select "Just the push event"
6. Click "Add webhook"

Now every push to `main` will trigger automatic deployment!
