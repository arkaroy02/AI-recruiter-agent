# Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                       TALENT SCOUT AGENT SYSTEM                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

                              INPUT LAYER
                              ===========

┌─────────────────────────────────────────────────────────────────────────┐
│  📋 Job Description (Unstructured Text)                                 │
│  ---                                                                     │
│  "Senior Full Stack Engineer - FinTech Platform                          │
│   • 6+ years experience required                                         │
│   • Python, React, PostgreSQL skills needed                              │
│   • Experience with AWS and Kubernetes                                   │
│   • Leadership and mentoring desired"                                    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
                        PARSING LAYER
                        =============

┌──────────────────────────────────────────────────────────────────────────┐
│  📌 JD Parser (LLM: gemma2:2b)                                      │
│  ───                                                                      │
│  • Extract structured data:                                              │
│    - Role: "Senior Full Stack Engineer"                                  │
│    - Required Skills: [Python, React, PostgreSQL, AWS]                   │
│    - Preferred Skills: [Kubernetes, GraphQL, Docker]                     │
│    - Min Years Exp: 6                                                    │
│    - Seniority: "senior"                                                 │
│    - Domain: "fintech"                                                   │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │
                               ▼
                       DISCOVERY LAYER
                       ===============

        ┌────────────────────────────────────────────────────┐
        │  💾 Candidate Database                             │
        │  ─────────────────────                             │
        │  10 Profiles with:                                 │
        │  • Name, Title, Experience                         │
        │  • Skills, Summary, Openness                       │
        │  • Current Company, Education                      │
        └────────────────────────────────────────────────────┘
                        │
                        ▼
    ┌───────────────────────────────────────────────────────┐
    │  🔍 Semantic Search Engine                            │
    │  ──────────────────                                   │
    │  • Embedding Model: nomic-embed-text:latest           │
    │  • Vector Store: ChromaDB (local)                     │
    │  • Query: JD role + required skills                   │
    │  • Output: Top K candidates (default: 5)              │
    └───────────────────────────────────────────────────────┘
                        │
                        ▼
                    ┌──────────────────────────────────┐
                    │  👥 Top 5 Candidates             │
                    │  ────────────────                │
                    │  • Alice Chen (match: 85%)       │
                    │  • Bob Rodriguez (match: 72%)    │
                    │  • Carol Martinez (match: 68%)   │
                    │  • David Kim (match: 62%)        │
                    │  • Emma Thompson (match: 58%)    │
                    └──────────────────────────────────┘
                               │
                               ▼
                        SCORING LAYER 1
                        ===============

┌─────────────────────────────────────────────────────────────────────────┐
│  📊 Match Scorer (Rule-based + LLM validation)                          │
│  ─────                                                                   │
│  Scoring Formula:                                                        │
│  ┌─────────────────────────────────────────────────────────┐            │
│  │ Match Score = 0-100                                     │            │
│  │ Breakdown:                                              │            │
│  │ • Required Skills Match: 55% weight                     │            │
│  │ • Preferred Skills Match: 25% weight                    │            │
│  │ • Experience Fit: 20% weight                            │            │
│  │                                                         │            │
│  │ Example: Alice Chen                                    │            │
│  │  - Required skills: 5/5 ✅ (100%) → 55 points         │            │
│  │  - Preferred skills: 3/4 (75%) → 19 points            │            │
│  │  - Exp (7 yrs vs 6 req): 1.5 exp bonus → 26 points   │            │
│  │  - Total: 85.0/100                                     │            │
│  └─────────────────────────────────────────────────────────┘            │
│                                                                          │
│  Output: Match scores for all 5 candidates                              │
└───────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                      ENGAGEMENT LAYER
                      =================

┌───────────────────────────────────────────────────────────────────────┐
│  💬 Conversation Simulator                                             │
│  ───────────────────────                                               │
│  Simulates realistic 2-turn recruiter-candidate conversation          │
│                                                                       │
│  Turn 1 (Recruiter):                                                 │
│  "Hi Alice! I saw your work on payment systems. We're building       │
│   something similar at our fintech startup. Are you open?"           │
│                                                                       │
│  Turn 1 (Candidate):                                                 │
│  "Thanks for reaching out! I'm happy where I am, but fintech         │
│   is an area I'm passionate about. Tell me more!"                   │
│                                                                       │
│  Turn 2 (Recruiter):                                                 │
│  "Perfect! We're hiring a Senior Full Stack Engineer for our         │
│   core platform team. Competitive package + equity. Interested?"     │
│                                                                       │
│  Turn 2 (Candidate):                                                 │
│  "Sounds interesting! When could we chat more about this?"           │
│                                                                       │
│  Models: gemma2:2b (both recruiter & candidate personas)         │
│  Output: Full conversation history                                   │
└───────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                        SCORING LAYER 2
                        ===============

┌───────────────────────────────────────────────────────────────────────┐
│  💯 Interest Scorer (LLM: gemma2:2b)                             │
│  ─────────────────                                                    │
│  Analyzes conversation to extract:                                    │
│                                                                       │
│  • Interest Score (0-100):                                            │
│    Genuine enthusiasm detected from language                          │
│    Alice Chen: 92/100 (strong interest)                               │
│                                                                       │
│  • Availability:                                                      │
│    "1-3 months" (open to exploring)                                   │
│                                                                       │
│  • Key Signals:                                                       │
│    ✅ "excited about fintech"                                         │
│    ✅ "impressed with mission"                                        │
│    ✅ "happy to discuss further"                                      │
│                                                                       │
│  • Red Flags:                                                         │
│    ⚠️ "I'm happy where I am" (lower urgency)                          │
│                                                                       │
│  Output: Interest scores for all candidates                           │
└───────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                        RANKING LAYER
                        =============

┌───────────────────────────────────────────────────────────────────────┐
│  🏆 Combined Ranker                                                    │
│  ──────────────────                                                   │
│  Formula:                                                              │
│  ┌─────────────────────────────────────────────────────────┐          │
│  │ Combined Score = (Match Score × 0.60) +                 │          │
│  │                  (Interest Score × 0.40)                │          │
│  │                                                         │          │
│  │ Rationale:                                              │          │
│  │ • 60% weight on technical fit (core requirement)       │          │
│  │ • 40% weight on interest (likelihood to accept)        │          │
│  │                                                         │          │
│  │ Example Rankings:                                       │          │
│  │ 1. Alice Chen:  (85.0 × 0.6) + (92.0 × 0.4) = 87.4 ✅ │          │
│  │ 2. Carol Martinez: (78.0 × 0.6) + (85.0 × 0.4) = 80.8 │          │
│  │ 3. Bob Rodriguez: (72.0 × 0.6) + (78.0 × 0.4) = 74.4   │          │
│  │ 4. David Kim:    (62.0 × 0.6) + (72.0 × 0.4) = 66.0    │          │
│  │ 5. Emma Thompson: (58.0 × 0.6) + (68.0 × 0.4) = 62.0   │          │
│  └─────────────────────────────────────────────────────────┘          │
│                                                                       │
│  Output: Sorted by combined_score (descending)                       │
└───────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                           OUTPUT LAYER
                           ============

┌───────────────────────────────────────────────────────────────────────┐
│  📈 Ranked Shortlist (Ready for Recruiter Action)                      │
│  ────────────────────────────────────────────────                      │
│                                                                        │
│  RANKED CANDIDATES FOR: Senior Full Stack Engineer - FinTech         │
│  ═════════════════════════════════════════════════════════════         │
│                                                                        │
│  🥇 #1 Alice Chen (87.4/100) ⭐ PRIORITY                              │
│     Title: Senior Full Stack Engineer                                 │
│     Company: FinTech Innovations Inc                                  │
│     Experience: 7 years                                               │
│     Match: 85.0 | Interest: 92.0                                      │
│     Availability: 1-3 months                                          │
│     Status: ✅ Warm lead - expressed strong interest                  │
│                                                                        │
│  🥈 #2 Carol Martinez (80.8/100) ⭐ PRIORITY                           │
│     Title: Data Engineer                                              │
│     Company: Analytics Startup Co                                     │
│     Experience: 4 years                                               │
│     Match: 78.0 | Interest: 85.0                                      │
│     Availability: Immediately                                         │
│     Status: ⚠️ Skills gap in frontend (React)                         │
│                                                                        │
│  🥉 #3 Bob Rodriguez (74.4/100)                                        │
│     ... (and so on)                                                   │
│                                                                        │
│  📥 Available Exports:                                                │
│     • JSON: Full detailed results                                     │
│     • CSV: Simplified shortlist for email/tracking                    │
└───────────────────────────────────────────────────────────────────────┘


                         TECHNOLOGY STACK
                         ================

┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  🧠 LLM Layer:                                                       │
│     • gemma2:2b - JD parsing, interest scoring                 │
│     • gemma2:2b - Conversation simulation                        │
│     • Running on: Ollama (local inference)                           │
│                                                                      │
│  🔍 Embedding Layer:                                                 │
│     • nomic-embed-text:latest - Semantic search                      │
│     • Vector DB: ChromaDB (local, persistent)                        │
│                                                                      │
│  🎨 Application Layer:                                               │
│     • Streamlit - Web UI for recruiters                              │
│     • Python 3.10+ - Core orchestration                              │
│     • Pandas - Data manipulation & export                            │
│                                                                      │
│  💾 Data Layer:                                                      │
│     • candidates.json - Profile database                             │
│     • ChromaDB - Vector embeddings (auto-indexed)                    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘


                         COMPONENT BREAKDOWN
                         ===================

agent/
├── jd_parser.py
│   └─ Extracts: role, skills (req/pref), min_exp, seniority, domain
│
├── embedder.py
│   ├─ embed_text() → nomic-embed-text embeddings
│   ├─ index_candidates() → ChromaDB collection
│   └─ find_top_candidates() → semantic search results
│
├── match_scorer.py
│   └─ score_match() → 0-100 technical fit score
│
├── covo_simulator.py
│   └─ simulate_conversation() → realistic candidate engagement
│
├── interest_scorer.py
│   └─ score_interest() → 0-100 enthusiasm + availability + flags
│
├── ranker.py
│   └─ rank_candidates() → combined scoring & sort
│
└── orchestrator.py
    └─ run_full_pipeline() → orchestrates entire flow

app.py
└─ Streamlit UI for interactive recruiter use


                         DATA FLOW SUMMARY
                         =================

JD Text → Parse → Find Candidates → Score Match
              ↓                           ↓
         Engage → Score Interest → Rank → Export

Time Per Candidate: ~6-12 seconds
Total Pipeline: ~30-60 seconds for 5 candidates
```

---

## Key Design Decisions

1. **Local-First Architecture**: All models run locally with Ollama - no cloud dependencies
2. **Dual Scoring Approach**: Technical match + human interest = better predictions
3. **Simulation-Based Engagement**: AI-generated conversations reveal authentic interest
4. **Explainable Scoring**: Every candidate has detailed breakdown of why they scored
5. **Streamlit UI**: Low-friction interface for recruiters - no ML expertise needed

---

## Scalability Notes

- **Current**: 10 candidates, 5 top matches, 3 conversation turns ~ 30-60 seconds
- **Optimizations Available**:
  - Batch process multiple JDs
  - Cache embeddings between runs
  - Reduce conversation turns
  - Use smaller/faster models

---

## Security & Privacy

- All data processed locally - no external API calls
- Candidate profiles stored in local JSON
- Embeddings stored in local ChromaDB
- Conversations are simulated (no real candidates exposed)

