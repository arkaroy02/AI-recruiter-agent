# Quick Reference Guide

## 🚀 Start Here - 3 Options

### Option 1: Fastest (CLI Test)
```bash
python test_demo.py
python agent/orchestrator.py
```
**Time**: 1-2 minutes (validates everything works)

### Option 2: Best UI (Web Dashboard)
```bash
# Terminal 1
ollama serve

# Terminal 2
streamlit run app.py
```
**Time**: 3-5 minutes (open http://localhost:8501)

### Option 3: Docker (For Teams)
```bash
docker-compose up
```
**Time**: 5-10 minutes (auto-downloads models)

---

## 📋 What Each File Does

### Core Application
| File | Purpose |
|------|---------|
| `app.py` | Streamlit web interface for recruiters |
| `requirements.txt` | Python package dependencies |

### Agent Logic (agent/)
| File | Purpose |
|------|---------|
| `jd_parser.py` | Extracts role, skills, seniority from JD |
| `embedder.py` | Creates vector embeddings + semantic search |
| `match_scorer.py` | Scores technical fit (0-100) |
| `covo_simulator.py` | Simulates recruiter-candidate conversations |
| `interest_scorer.py` | Detects genuine interest + availability |
| `ranker.py` | Combines scores (60% match + 40% interest) |
| `orchestrator.py` | Coordinates the full pipeline |

### Data
| File | Purpose |
|------|---------|
| `data/candidates.json` | 10 realistic dummy candidate profiles |
| `tests/sample_jd.txt` | Example job description for testing |

### Documentation
| File | Purpose |
|------|---------|
| `README.md` | Complete project documentation |
| `QUICKSTART.md` | 5-minute setup guide |
| `ARCHITECTURE.md` | System design + diagrams |
| `SAMPLE_IO.md` | Example inputs/outputs |
| `DEPLOYMENT.md` | Production deployment |
| `SETUP_COMPLETED.md` | Project summary |

### Setup & Testing
| File | Purpose |
|------|---------|
| `setup.bat` | Automated Windows setup |
| `setup.sh` | Automated macOS/Linux setup |
| `test_demo.py` | Comprehensive test suite |

### Docker & Deployment
| File | Purpose |
|------|---------|
| `Dockerfile` | Container image definition |
| `docker-compose.yml` | Multi-container orchestration |
| `.gitignore` | Git ignore rules |

---

## 🎯 The Pipeline in 6 Steps

```
INPUT (Job Description)
        ↓
    [1] JD Parser
        ↓
        ✓ Extracts: role, skills, seniority
        ↓
    [2] Embedder
        ↓
        ✓ Finds top K candidates (semantic search)
        ↓
    [3] Match Scorer
        ↓
        ✓ Technical fit: 0-100
        ↓
    [4] Conversation Simulator
        ↓
        ✓ AI recruiter-candidate chat
        ↓
    [5] Interest Scorer
        ↓
        ✓ Genuine interest: 0-100 + signals
        ↓
    [6] Ranker
        ↓
        ✓ Combined: (match × 0.6) + (interest × 0.4)
        ↓
OUTPUT (Ranked shortlist)
```

---

## 🔑 Key Commands

### Check Status
```bash
ollama list                    # Show installed models
python test_demo.py            # Validate everything
```

### Run Application
```bash
streamlit run app.py           # Start web UI
python agent/orchestrator.py   # CLI processing
```

### Download Models
```bash
ollama pull gemma2:2b
ollama pull nomic-embed-text:latest
```

### Using Docker
```bash
docker-compose up              # Start all services
docker-compose down            # Stop all services
docker-compose logs -f app     # View app logs
```

---

## 📊 Scoring Breakdown

```
Match Score (60% weight)
├── Required Skills Match: 55%
│   └─ Skill overlap with job requirements
├── Preferred Skills Match: 25%
│   └─ Bonus for nice-to-have skills
└── Experience Fit: 20%
    └─ Years of experience vs. minimum

Interest Score (40% weight)
├── Enthusiasm: Main factor
├── Availability: When can they start?
└── Red Flags: Concerns detected?

Combined Score = (Match × 0.6) + (Interest × 0.4)
```

---

## ✅ Checklist Before Using

- [ ] Python 3.10+ installed? (`python --version`)
- [ ] Ollama installed? (`ollama --version`)
- [ ] Required models downloaded? (`ollama list`)
- [ ] Dependencies installed? (`pip list | grep streamlit`)
- [ ] Data files present? (`ls data/candidates.json`)
- [ ] Tests pass? (`python test_demo.py`)

---

## 🎬 Demo in 60 Seconds

```
1. Start services:
   ollama serve (Terminal 1)
   streamlit run app.py (Terminal 2)

2. Open browser:
   http://localhost:8501

3. Click "📊 Load Sample JD"

4. Click "🚀 Find Candidates"

5. Wait 30-60 seconds...

6. See ranked candidates with scores!

7. Download results as CSV
```

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" | `ollama serve` in terminal |
| "Model not found" | `ollama pull gemma2:2b` |
| "Out of memory" | Reduce top_k or add RAM |
| "Slow" | Use smaller model or reduce turns |
| Python error | Run `python test_demo.py` |

---

## 📈 Expected Results

### Sample Output
```
Role: Senior Full Stack Engineer

Top 3 Candidates:

1. Alice Chen (87.4/100) ⭐
   - Match: 85 | Interest: 92
   - Availability: 1-3 months

2. Carol Martinez (77.8/100)
   - Match: 72 | Interest: 85
   - Availability: Immediately

3. Emma Thompson (66.8/100)
   - Match: 58 | Interest: 78
   - Availability: 1-3 months
```

---

## 🔌 Integration Options

### As API
```python
from agent.orchestrator import run_full_pipeline

results = run_full_pipeline(jd_text, candidates)
print(results['ranked_candidates'])
```

### In Your App
```python
# Copy agent/ folder to your project
# Import modules as needed
from agent.jd_parser import parse_jd
from agent.match_scorer import score_match
```

### With External Tools
```bash
# Export to CSV for Excel/Salesforce
streamlit run app.py
# Download "Download Shortlist as CSV"

# Or pipe output to other tools
python agent/orchestrator.py | jq '.ranked_candidates'
```

---

## 📚 Documentation Map

```
First Time?
   └─→ QUICKSTART.md

Want to Understand Design?
   └─→ ARCHITECTURE.md

Seeing Examples?
   └─→ SAMPLE_IO.md

Deploying to Production?
   └─→ DEPLOYMENT.md

Full Details?
   └─→ README.md

Need Help?
   └─→ Run: python test_demo.py
```

---

## 🎓 Learn More

### About the Scoring
See **SAMPLE_IO.md** → "Key Takeaways from Sample Outputs"

### About Architecture  
See **ARCHITECTURE.md** → Full system diagram + explanation

### About Deployment
See **DEPLOYMENT.md** → AWS, Docker, Heroku options

### About Configuration
Edit these files:
- **Scoring weights**: `agent/ranker.py`
- **More candidates**: `data/candidates.json`
- **Different models**: `agent/jd_parser.py` (change model name)
- **Conversation depth**: `agent/orchestrator.py` (change turns)

---

## 🚀 Next Steps

1. ✅ Verify Ollama is running
2. ✅ Run `python test_demo.py`
3. ✅ Try `streamlit run app.py`
4. ✅ Load sample JD and process
5. ✅ Download results
6. ✅ Add your own candidates
7. ✅ Deploy using Docker or DEPLOYMENT.md

---

## 💡 Tips & Tricks

### Run Faster
- Use `mistral:latest` instead of `gemma2:2b` (3x faster)
- Reduce top_k from 5 to 3
- Reduce conversation turns from 3 to 2

### Better Results
- Add more candidates to `data/candidates.json`
- Fine-tune scoring weights in `agent/ranker.py`
- Use domain-specific models

### Monitor Performance
- Watch CPU/RAM: `watch 'ps aux | grep ollama'`
- Check Ollama health: `curl http://localhost:11434/api/tags`
- View logs: `tail -f ~/.ollama/ollama.log`

---

## 📞 Support

| Issue | Resource |
|-------|----------|
| Installation | QUICKSTART.md |
| Architecture | ARCHITECTURE.md |
| Examples | SAMPLE_IO.md |
| Production | DEPLOYMENT.md |
| Testing | Run test_demo.py |
| Debugging | Check test output |

---

## ✨ What Makes This Special

✅ **End-to-End**: JD → Ranking in one go  
✅ **Explainable**: Every score has breakdown  
✅ **Local**: No external APIs needed  
✅ **Fast**: 30-60 sec for 5 candidates  
✅ **Easy**: Recruiters need zero ML knowledge  
✅ **Production-Ready**: Deploy immediately  

---

**Ready to go!** 🎉

Choose your start option above and begin!

