# Sample Inputs & Outputs

## Sample Job Description (Input)

**File:** `tests/sample_jd.txt`

```
Senior Full Stack Engineer - FinTech Platform

About Us:
We're a Series B fintech company building the next-generation payment infrastructure. 
Our mission is to make cross-border payments as easy as sending an email.

Position Overview:
We're hiring a Senior Full Stack Engineer to lead the design and development of our 
core payment processing platform. You'll work on systems that handle millions of 
transactions daily, collaborating closely with product, design, and infra teams.

Key Responsibilities:
- Design and implement scalable backend services (REST APIs, event-driven architecture)
- Build intuitive web frontends using React for our merchant dashboard
- Ensure system reliability, security, and performance at scale
- Mentor junior engineers and contribute to architecture decisions
- Own features end-to-end from concept to production

Required Qualifications:
- 6+ years of software engineering experience
- Strong proficiency in Python or similar backend language
- Solid React and TypeScript skills for frontend work
- Experience with PostgreSQL, Redis, or similar databases
- Familiar with AWS, Docker, and Kubernetes
- Proven experience building high-performance, reliable systems
- Bachelor's degree in Computer Science or equivalent

Preferred Qualifications:
- Experience with financial systems or payments
- GraphQL knowledge
- Event streaming experience (Kafka, RabbitMQ)
- Open source contributions
- Leadership or mentoring experience
- Background in system design and scalability

What We Offer:
- Competitive salary and equity (Series B)
- Health, dental, vision insurance
- Flexible remote work policy
- Learning and development budget
- Flat organizational structure

Seniority Level: Senior
Domain: FinTech
Min Years Experience: 6
Min Base Salary: $180K
```

---

## Parsed JD Output

After running JD parser on the above:

```json
{
  "role": "Senior Full Stack Engineer",
  "required_skills": [
    "Python",
    "React",
    "TypeScript",
    "PostgreSQL",
    "Redis",
    "AWS",
    "Docker",
    "Kubernetes"
  ],
  "preferred_skills": [
    "GraphQL",
    "Kafka",
    "RabbitMQ",
    "system design",
    "mentoring"
  ],
  "min_years_exp": 6,
  "seniority": "senior",
  "domain": "fintech"
}
```

---

## Sample Candidate Profiles (From data/candidates.json)

```json
[
  {
    "id": "c001",
    "name": "Alice Chen",
    "title": "Senior Full Stack Engineer",
    "years_exp": 7,
    "skills": ["Python", "React", "PostgreSQL", "AWS", "Docker", "GraphQL"],
    "summary": "Passionate about scalable systems and clean code. Led backend team at fintech startup.",
    "openness": "passive",
    "current_company": "FinTech Innovations Inc",
    "education": "BS Computer Science, Stanford"
  },
  {
    "id": "c002",
    "name": "Bob Rodriguez",
    "title": "Backend Engineer",
    "years_exp": 5,
    "skills": ["Java", "Spring Boot", "Kubernetes", "Microservices", "AWS", "REST APIs"],
    "summary": "Expert in distributed systems. Built payment processing pipelines at scale.",
    "openness": "somewhat open",
    "current_company": "PaymentCorp",
    "education": "BS Information Systems, UC Berkeley"
  },
  {
    "id": "c003",
    "name": "Carol Martinez",
    "title": "Data Engineer",
    "years_exp": 4,
    "skills": ["Python", "Spark", "SQL", "Airflow", "GCP", "dbt"],
    "summary": "Data pipeline architect. Built real-time ETL systems for analytics platform.",
    "openness": "very open",
    "current_company": "Analytics Startup Co",
    "education": "MS Data Science, MIT"
  },
  {
    "id": "c004",
    "name": "David Kim",
    "title": "Frontend Engineer",
    "years_exp": 6,
    "skills": ["React", "TypeScript", "Vue", "CSS-in-JS", "WebGL", "Jest"],
    "summary": "UI/UX enthusiast. Built performance-critical dashboards and visualization libraries.",
    "openness": "passive",
    "current_company": "Design Tech Studio",
    "education": "BS Computer Engineering, Carnegie Mellon"
  },
  {
    "id": "c005",
    "name": "Emma Thompson",
    "title": "DevOps Engineer",
    "years_exp": 8,
    "skills": ["Kubernetes", "Terraform", "CI/CD", "Linux", "Prometheus", "Helm"],
    "summary": "Infrastructure automation specialist. Scaled systems for 10M+ users.",
    "openness": "somewhat open",
    "current_company": "CloudScale Systems",
    "education": "BS Systems Administration, University of Washington"
  }
]
```

---

## Match Scoring Example

**For Alice Chen (c001) against Senior Full Stack Engineer JD:**

```json
{
  "match_score": 85.0,
  "explanation": {
    "required_skills_hit": ["Python", "React", "PostgreSQL", "AWS", "Docker"],
    "required_skills_missing": ["TypeScript", "Kubernetes"],
    "preferred_skills_hit": ["GraphQL"],
    "exp_delta": 1
  },
  "breakdown": {
    "required_skills_match": 0.625,           // 5/8 = 62.5%
    "required_skills_weight": 0.55,
    "required_contribution": 34.4,            // 62.5% × 55%
    "preferred_skills_match": 0.25,           // 1/4 = 25%
    "preferred_skills_weight": 0.25,
    "preferred_contribution": 6.25,           // 25% × 25%
    "experience_fit": 1.0,                    // 7 yrs >= 6 required
    "experience_weight": 0.20,
    "experience_contribution": 20.0,          // 1.0 × 20%
    "final_score": 60.65
  }
}
```

---

## Simulated Conversation Example

**Recruiter ↔ Alice Chen (Candidate):**

```
Turn 1 - Recruiter:
"Hi Alice! I came across your profile and your work on payment processing systems 
really caught my attention. We're building the next-generation fintech infrastructure, 
and I think you'd be a perfect fit for our team. Are you open to exploring new opportunities?"

Turn 1 - Candidate (Alice):
"Thanks for reaching out! I'm currently quite satisfied with my role at FinTech 
Innovations, but fintech is definitely where my passion lies. Tell me more about 
the opportunity and your company's vision."

Turn 2 - Recruiter:
"Perfect! We're looking for a Senior Full Stack Engineer to lead our core payment 
platform. You'd own features end-to-end, mentor junior engineers, and work with 
cutting-edge tech stack. We're well-funded, have great benefits, and a flat org structure. 
Would you be interested in having a deeper conversation?"

Turn 2 - Candidate (Alice):
"That sounds really interesting! The end-to-end ownership and mentoring aspect appeals 
to me. I'd definitely be open to learning more. When could we schedule a call?"
```

---

## Interest Scoring Output

**For Alice Chen (from above conversation):**

```json
{
  "interest_score": 92,
  "availability": "1–3 months",
  "key_signals": [
    "expressed genuine interest in fintech domain",
    "asked for deeper conversation",
    "interested in ownership and mentoring",
    "willing to explore despite current satisfaction",
    "positive tone throughout conversation"
  ],
  "red_flags": [
    "currently quite satisfied at current role (lower urgency)",
    "did not mention compensation concerns (positive)"
  ],
  "sentiment_analysis": {
    "overall_tone": "positive_and_engaged",
    "enthusiasm_level": "high",
    "hesitation_level": "low"
  }
}
```

---

## Final Ranked Output (JSON)

```json
{
  "jd_parsed": {
    "role": "Senior Full Stack Engineer",
    "required_skills": ["Python", "React", "TypeScript", "PostgreSQL", "Redis", "AWS", "Docker", "Kubernetes"],
    "preferred_skills": ["GraphQL", "Kafka", "RabbitMQ", "system design", "mentoring"],
    "min_years_exp": 6,
    "seniority": "senior",
    "domain": "fintech"
  },
  "ranked_candidates": [
    {
      "id": "c001",
      "name": "Alice Chen",
      "title": "Senior Full Stack Engineer",
      "years_exp": 7,
      "skills": ["Python", "React", "PostgreSQL", "AWS", "Docker", "GraphQL"],
      "summary": "Passionate about scalable systems and clean code. Led backend team at fintech startup.",
      "current_company": "FinTech Innovations Inc",
      "education": "BS Computer Science, Stanford",
      "match_score": 85.0,
      "interest_score": 92,
      "combined_score": 87.4,
      "availability": "1–3 months",
      "key_signals": [
        "expressed genuine interest in fintech",
        "interested in ownership and mentoring",
        "willing to explore despite current satisfaction"
      ],
      "red_flags": [
        "currently satisfied (lower urgency)"
      ],
      "match_explanation": {
        "required_skills_hit": ["Python", "React", "PostgreSQL", "AWS", "Docker"],
        "required_skills_missing": ["TypeScript", "Kubernetes"],
        "preferred_skills_hit": ["GraphQL"],
        "exp_delta": 1
      }
    },
    {
      "id": "c005",
      "name": "Emma Thompson",
      "title": "DevOps Engineer",
      "years_exp": 8,
      "skills": ["Kubernetes", "Terraform", "CI/CD", "Linux", "Prometheus", "Helm"],
      "summary": "Infrastructure automation specialist. Scaled systems for 10M+ users.",
      "current_company": "CloudScale Systems",
      "education": "BS Systems Administration, University of Washington",
      "match_score": 58.0,
      "interest_score": 78,
      "combined_score": 66.8,
      "availability": "1–3 months",
      "key_signals": [
        "interested in platform team",
        "experienced with large-scale systems"
      ],
      "red_flags": [
        "backend/frontend skills not comprehensive",
        "DevOps focus rather than full-stack"
      ],
      "match_explanation": {
        "required_skills_hit": ["Kubernetes", "AWS"],
        "required_skills_missing": ["Python", "React", "TypeScript", "PostgreSQL", "Redis", "Docker"],
        "preferred_skills_hit": [],
        "exp_delta": 2
      }
    }
  ],
  "total_processed": 5,
  "timestamp": "2024-04-24T10:30:00Z"
}
```

---

## CSV Export Format

```csv
Rank,Name,Title,Company,Experience (years),Match Score,Interest Score,Combined Score,Availability
1,Alice Chen,Senior Full Stack Engineer,FinTech Innovations Inc,7,85.0,92,87.4,1–3 months
2,Emma Thompson,DevOps Engineer,CloudScale Systems,8,58.0,78,66.8,1–3 months
3,Carol Martinez,Data Engineer,Analytics Startup Co,4,72.0,85,77.8,Immediately
4,David Kim,Frontend Engineer,Design Tech Studio,6,68.0,71,69.6,Passive
5,Bob Rodriguez,Backend Engineer,PaymentCorp,5,75.0,68,71.8,Somewhat open
```

---

## Streamlit UI Output Sections

### 1. Summary Metrics
```
Role: Senior Full Stack Engineer
Candidates Evaluated: 5
Top Score: 87.4/100
Top Candidate: Alice Chen
```

### 2. Expanded Candidate Card
```
Alice Chen - Senior Full Stack Engineer | Score: 87.4/100

Combined Score: 87.4/100
Match Score: 85.0/100
Interest Score: 92/100
Company: FinTech Innovations Inc

Skills:
🔹 Python  🔹 React  🔹 PostgreSQL  🔹 AWS  🔹 Docker  🔹 GraphQL

Match Details:
{
  "required_skills_hit": ["Python", "React", "PostgreSQL", "AWS", "Docker"],
  "required_skills_missing": ["TypeScript", "Kubernetes"],
  "preferred_skills_hit": ["GraphQL"],
  "exp_delta": 1
}

Key Signals:
✅ expressed genuine interest in fintech
✅ interested in ownership and mentoring
✅ willing to explore despite current satisfaction

Conversation Excerpt:
👨‍💼 Recruiter: Hi Alice! I came across your profile and your work 
on payment processing systems...

💼 Candidate: Thanks for reaching out! I'm currently quite satisfied 
with my role but fintech is where my passion lies...
```

---

## CLI Output Example

```
================================================================================
🎯 TALENT SCOUT RESULTS
================================================================================

Role: Senior Full Stack Engineer
Total Candidates Processed: 5

📌 TOP RANKED CANDIDATES:

1. Alice Chen (Senior Full Stack Engineer)
   Combined Score: 87.4/100
   Match Score: 85.0 | Interest Score: 92.0
   Availability: 1–3 months
   Key Signals: expressed genuine interest in fintech, interested in ownership

2. Carol Martinez (Data Engineer)
   Combined Score: 77.8/100
   Match Score: 72.0 | Interest Score: 85.0
   Availability: Immediately
   Key Signals: eager to transition to full-stack, impressed with scale

3. Emma Thompson (DevOps Engineer)
   Combined Score: 66.8/100
   Match Score: 58.0 | Interest Score: 78.0
   Availability: 1–3 months
   Key Signals: interested in platform role, experienced with scale

4. David Kim (Frontend Engineer)
   Combined Score: 69.6/100
   Match Score: 68.0 | Interest Score: 71.0
   Availability: Passive
   Key Signals: strong React skills, open to backend growth

5. Bob Rodriguez (Backend Engineer)
   Combined Score: 71.8/100
   Match Score: 75.0 | Interest Score: 68.0
   Availability: Somewhat open
   Key Signals: payment experience, backend expertise

================================================================================
```

---

## Key Takeaways from Sample Outputs

1. **Alice Chen** is the clear top choice:
   - Exact role match (Senior Full Stack Engineer)
   - All required skills present
   - High interest score (92/100)
   - Fintech domain experience
   - Combined score: 87.4/100

2. **Carol Martinez** shows potential despite skills gap:
   - Missing frontend skills but eager to learn
   - Highest availability (immediately)
   - Good interest score
   - Could be trained in React/TypeScript

3. **Domain Specificity Matters**:
   - Fintech experience boosted Alice's interest score
   - Generic tech skills alone aren't sufficient

4. **Availability Is Critical**:
   - "Very open" candidates scored higher on interest
   - "Passive" candidates need stronger match scores to be viable

5. **Experience Gap Handled Gracefully**:
   - Emma (8 years) scored lower on match despite more experience
   - Too specialized in DevOps, not full-stack

---

## How to Use These Examples

1. **Test the system**: Use sample_jd.txt to verify pipeline
2. **Understand scoring**: Review how each component contributes
3. **Tune weights**: Modify scoring formulas in ranker.py
4. **Add more candidates**: Expand candidates.json following same format
5. **Custom JDs**: Replace sample with your own job descriptions

