"""FastAPI backend for the full frontend talent scouting app."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import sys
from typing import Dict, List, Literal
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT_DIR / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from orchestrator import load_candidates, run_full_pipeline, run_match_only_pipeline  # noqa: E402
from webapp.services import (  # noqa: E402
    apply_early_exit_signal,
    build_interview_closing,
    candidate_requested_interview_end,
    clean_done_tokens,
    count_candidate_turns,
    extract_candidates_from_resumes,
    generate_recruiter_question,
    get_candidate,
    reset_candidate_real_state,
    should_end_real_interview,
    transcribe_uploaded_audio,
    update_candidate_from_real_interview,
)

app = FastAPI(title="Talent Scout Full Web App", version="1.0.0")
templates = Jinja2Templates(directory=str(ROOT_DIR / "webapp" / "templates"))
app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "webapp" / "static")), name="static")

RUN_STORE: Dict[str, Dict] = {}
RESUME_STORE: Dict[str, List] = {"candidates": [], "filenames": []}


class PipelineRequest(BaseModel):
    jd_text: str = Field(min_length=10)
    top_k: int = Field(default=5, ge=1, le=20)
    interview_mode: Literal["demo", "real"] = "demo"


class InterviewStartRequest(BaseModel):
    run_id: str
    candidate_name: str


class InterviewRespondRequest(BaseModel):
    run_id: str
    candidate_name: str
    response_text: str = Field(min_length=1)


class InterviewResetRequest(BaseModel):
    run_id: str
    candidate_name: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_run_or_404(run_id: str) -> Dict:
    run = RUN_STORE.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return run


def get_active_candidates() -> List[Dict]:
    """Use uploaded resume candidates when present, else fall back to sample JSON data."""
    if RESUME_STORE["candidates"]:
        return RESUME_STORE["candidates"]
    return load_candidates(str(ROOT_DIR / "data" / "candidates.json"))


def candidate_source_meta() -> Dict:
    """Describe the current candidate source for UI display."""
    if RESUME_STORE["candidates"]:
        return {
            "type": "uploaded_resumes",
            "count": len(RESUME_STORE["candidates"]),
            "filenames": RESUME_STORE["filenames"],
        }
    return {
        "type": "sample_dataset",
        "count": len(load_candidates(str(ROOT_DIR / "data" / "candidates.json"))),
        "filenames": [],
    }


def ensure_real_mode_or_400(run: Dict) -> None:
    mode = run.get("results", {}).get("pipeline_mode", "demo")
    if mode != "real":
        raise HTTPException(
            status_code=400, 
            detail="Interview studio requires 'Real' mode. Please run the pipeline with 'Real (AI interviewer + human candidate)' mode selected, or view the simulated conversations in the Results tab for Demo mode."
        )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/api/health")
async def health() -> Dict:
    return {"ok": True, "time": now_iso()}


@app.get("/api/sample-jd")
async def sample_jd() -> Dict:
    sample_path = ROOT_DIR / "tests" / "sample_jd.txt"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample JD not found at {sample_path}")
    return {"text": sample_path.read_text(encoding="utf-8")}


@app.get("/api/resumes/status")
async def resumes_status() -> Dict:
    return candidate_source_meta()


@app.post("/api/resumes/upload")
async def resumes_upload(files: List[UploadFile] = File(...)) -> Dict:
    incoming_files: List[tuple[str, bytes]] = []
    for file in files:
        filename = file.filename or "resume.pdf"
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Only PDF resumes are supported right now: {filename}")
        raw_bytes = await file.read()
        if not raw_bytes:
            raise HTTPException(status_code=400, detail=f"Uploaded file is empty: {filename}")
        incoming_files.append((filename, raw_bytes))

    candidates, errors = extract_candidates_from_resumes(incoming_files)
    if not candidates and errors:
        raise HTTPException(status_code=400, detail=errors[0]["error"])

    RESUME_STORE["candidates"] = candidates
    RESUME_STORE["filenames"] = [candidate.get("source_filename", "resume.pdf") for candidate in candidates]
    return {
        "candidate_source": candidate_source_meta(),
        "candidates": candidates,
        "errors": errors,
    }


@app.post("/api/resumes/clear")
async def resumes_clear() -> Dict:
    RESUME_STORE["candidates"] = []
    RESUME_STORE["filenames"] = []
    return candidate_source_meta()


@app.post("/api/pipeline/run")
async def run_pipeline(payload: PipelineRequest) -> Dict:
    candidates_data = get_active_candidates()

    if payload.interview_mode == "demo":
        results = run_full_pipeline(payload.jd_text, candidates_data, top_k=payload.top_k)
        results["pipeline_mode"] = "demo"
    else:
        results = run_match_only_pipeline(payload.jd_text, candidates_data, top_k=payload.top_k)
        results["pipeline_mode"] = "real"
    results["candidate_source"] = candidate_source_meta()

    run_id = str(uuid4())
    RUN_STORE[run_id] = {
        "run_id": run_id,
        "created_at": now_iso(),
        "results": results,
        "interviews": {},
    }
    return {"run_id": run_id, "results": results}


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str) -> Dict:
    run = get_run_or_404(run_id)
    return {
        "run_id": run["run_id"],
        "created_at": run["created_at"],
        "results": run["results"],
        "interviews": run["interviews"],
    }


@app.post("/api/interview/start")
async def interview_start(payload: InterviewStartRequest) -> Dict:
    run = get_run_or_404(payload.run_id)
    ensure_real_mode_or_400(run)

    results = run["results"]
    candidate = get_candidate(results, payload.candidate_name)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate not found: {payload.candidate_name}")

    interviews = run["interviews"]
    if payload.candidate_name not in interviews:
        interviews[payload.candidate_name] = {"history": [], "done": False, "updated_at": now_iso()}

    session = interviews[payload.candidate_name]
    if not session["history"]:
        question = generate_recruiter_question(results.get("jd_parsed", {}), [], candidate=candidate)
        clean_question = clean_done_tokens(question)
        if clean_question:
            session["history"].append({"speaker": "recruiter", "text": clean_question})
        session["done"] = "RECRUITER_DONE" in question
        session["updated_at"] = now_iso()

    return {
        "candidate_name": payload.candidate_name,
        "session": session,
        "candidate": candidate,
        "ranked_candidates": results.get("ranked_candidates", []),
    }


@app.post("/api/interview/respond")
async def interview_respond(payload: InterviewRespondRequest) -> Dict:
    run = get_run_or_404(payload.run_id)
    ensure_real_mode_or_400(run)
    results = run["results"]

    candidate = get_candidate(results, payload.candidate_name)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate not found: {payload.candidate_name}")

    interviews = run["interviews"]
    if payload.candidate_name not in interviews:
        interviews[payload.candidate_name] = {"history": [], "done": False, "updated_at": now_iso()}
    session = interviews[payload.candidate_name]

    response_text = payload.response_text.strip()
    if not response_text:
        raise HTTPException(status_code=400, detail="Response text is empty.")

    session["history"].append({"speaker": "candidate", "text": response_text})

    try:
        interest_result = update_candidate_from_real_interview(results, payload.candidate_name, session["history"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    ended_by_candidate = candidate_requested_interview_end(response_text)
    if should_end_real_interview(session["history"], response_text):
        if ended_by_candidate:
            apply_early_exit_signal(results, payload.candidate_name)
            interest_result["red_flags"] = list(dict.fromkeys([
                *(interest_result.get("red_flags", []) or []),
                "Candidate asked to end the interview early.",
            ]))
            interest_result["key_signals"] = list(dict.fromkeys([
                *(interest_result.get("key_signals", []) or []),
                "Candidate ended the conversation before the interview fully played out.",
            ]))
            interest_result["interest_score"] = min(float(interest_result.get("interest_score", 0)), 25.0)

        closing = build_interview_closing(ended_by_candidate)
        clean_question = clean_done_tokens(closing)
        if clean_question:
            session["history"].append({"speaker": "recruiter", "text": clean_question})
        session["done"] = True
    else:
        next_question = generate_recruiter_question(
            results.get("jd_parsed", {}),
            session["history"],
            candidate=candidate,
        )
        clean_question = clean_done_tokens(next_question)
        if clean_question:
            session["history"].append({"speaker": "recruiter", "text": clean_question})
        session["done"] = "RECRUITER_DONE" in next_question
    session["updated_at"] = now_iso()

    candidate = get_candidate(results, payload.candidate_name)
    return {
        "candidate_name": payload.candidate_name,
        "session": session,
        "candidate": candidate,
        "interest_result": interest_result,
        "ranked_candidates": results.get("ranked_candidates", []),
        "meta": {
            "candidate_turns": count_candidate_turns(session["history"]),
            "ended_by_candidate": ended_by_candidate,
        },
    }


@app.post("/api/interview/reset")
async def interview_reset(payload: InterviewResetRequest) -> Dict:
    run = get_run_or_404(payload.run_id)
    ensure_real_mode_or_400(run)
    results = run["results"]

    candidate = get_candidate(results, payload.candidate_name)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate not found: {payload.candidate_name}")

    reset_candidate_real_state(results, payload.candidate_name)
    run["interviews"][payload.candidate_name] = {"history": [], "done": False, "updated_at": now_iso()}

    return {
        "candidate_name": payload.candidate_name,
        "session": run["interviews"][payload.candidate_name],
        "candidate": get_candidate(results, payload.candidate_name),
        "ranked_candidates": results.get("ranked_candidates", []),
    }


@app.post("/api/interview/transcribe")
async def interview_transcribe(
    file: UploadFile = File(...),
    model_name: Literal["tiny", "base", "small"] = "tiny",
) -> Dict:
    raw_bytes = await file.read()
    suffix = Path(file.filename or "").suffix or ".wav"

    transcript, error = transcribe_uploaded_audio(raw_bytes, suffix=suffix, model_name=model_name)
    if error:
        raise HTTPException(status_code=400, detail=error)

    return {"text": transcript}


# ============================================================================
# EXPERIMENTAL: Interview Portal & Email Meeting Links
# ============================================================================
from webapp.email_service import (
    generate_meeting_token,
    validate_meeting_token,
    get_meeting_by_token,
    update_meeting_status,
    add_interview_answer,
    send_meeting_email,
)


class ShortlistEmailRequest(BaseModel):
    run_id: str
    candidate_name: str
    candidate_email: str
    company_name: str = "Talent Scout Studio"


class SubmitAnswersRequest(BaseModel):
    token: str
    answers: Dict[str, str]


@app.post("/api/shortlist/send-email")
async def shortlist_send_email(payload: ShortlistEmailRequest) -> Dict:
    """
    Send a meeting link email to a shortlisted candidate.
    Experimental feature for interview portal access.
    """
    run = get_run_or_404(payload.run_id)
    results = run.get("results", {})
    
    # Find the candidate
    candidates = results.get("ranked_candidates", results.get("candidates", []))
    candidate = None
    for c in candidates:
        if c.get("name") == payload.candidate_name:
            candidate = c
            break
    
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate not found: {payload.candidate_name}")
    
    # Generate meeting token
    meeting_token = generate_meeting_token(payload.run_id, payload.candidate_name)
    
    # Send email
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    email_result = send_meeting_email(
        candidate_email=payload.candidate_email,
        candidate_name=payload.candidate_name,
        meeting_token=meeting_token,
        company_name=payload.company_name,
        base_url=base_url
    )
    
    # Store meeting info in run
    if "meetings" not in run:
        run["meetings"] = {}
    run["meetings"][payload.candidate_name] = {
        "token": meeting_token,
        "email": payload.candidate_email,
        "sent_at": now_iso(),
        "status": "pending",
        "email_result": email_result
    }
    
    return {
        "success": email_result.get("success", False),
        "simulated": email_result.get("simulated", True),
        "message": email_result.get("message", ""),
        "meeting_link": email_result.get("meeting_link", ""),
        "token": meeting_token,
        "candidate_name": payload.candidate_name
    }


@app.get("/interview/{token}", response_class=HTMLResponse)
async def interview_portal(request: Request, token: str):
    """Render the interview portal page for candidates."""
    return templates.TemplateResponse(
        request=request,
        name="interview_portal.html",
        context={"token": token}
    )


@app.get("/api/interview/validate/{token}")
async def validate_interview_token(token: str) -> Dict:
    """Validate meeting token and return interview details."""
    meeting = validate_meeting_token(token)
    
    if not meeting:
        return {"valid": False, "error": "Invalid or expired token"}
    
    # Get candidate info from run
    run = RUN_STORE.get(meeting["run_id"])
    candidate_info = {}
    if run:
        results = run.get("results", {})
        candidates = results.get("ranked_candidates", results.get("candidates", []))
        for c in candidates:
            if c.get("name") == meeting["candidate_name"]:
                candidate_info = c
                break
    
    # Generate interview questions based on JD
    questions = [
        "Tell us about yourself and your professional background.",
        "What interests you most about this role and why do you think you'd be a good fit?",
        "Describe a challenging project you worked on and how you overcame obstacles.",
        "What are your salary expectations and availability to start?",
        "Do you have any questions for us about the role or company?"
    ]
    
    # If we have JD info, customize questions
    if run and run.get("results", {}).get("jd_parsed"):
        jd = run["results"]["jd_parsed"]
        role = jd.get("role", "this role")
        skills = jd.get("required_skills", [])
        
        questions = [
            f"Tell us about yourself and why you're interested in the {role} position.",
            f"How does your experience align with the requirements for the {role} role?",
            f"Describe your experience with {', '.join(skills[:3]) if skills else 'relevant technologies'}.",
            "Walk us through a challenging project you worked on and your contributions.",
            "What are your salary expectations and when would you be available to start?",
            "Do you have any questions about the role or our company?"
        ]
    
    return {
        "valid": True,
        "meeting": meeting,
        "candidate": candidate_info,
        "questions": questions
    }


@app.post("/api/interview/join/{token}")
async def join_interview(token: str) -> Dict:
    """Mark candidate as having joined the interview."""
    meeting = get_meeting_by_token(token)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    update_meeting_status(token, "joined", joined_at=now_iso())
    
    return {
        "success": True,
        "status": "joined",
        "joined_at": now_iso()
    }


@app.post("/api/interview/submit/{token}")
async def submit_interview_answers(token: str, payload: SubmitAnswersRequest) -> Dict:
    """Submit interview answers from candidate."""
    meeting = validate_meeting_token(token)
    if not meeting:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Save each answer
    for question, answer in payload.answers.items():
        if answer and answer.strip():
            add_interview_answer(token, question, answer.strip())
    
    # Mark as completed
    update_meeting_status(token, "completed")
    
    # Update run store
    run = RUN_STORE.get(meeting["run_id"])
    if run and "meetings" in run and meeting["candidate_name"] in run["meetings"]:
        run["meetings"][meeting["candidate_name"]]["status"] = "completed"
        run["meetings"][meeting["candidate_name"]]["completed_at"] = now_iso()
    
    return {
        "success": True,
        "message": "Interview submitted successfully",
        "answers_count": len(payload.answers)
    }


@app.get("/api/meetings/{run_id}")
async def get_meetings_for_run(run_id: str) -> Dict:
    """Get all meeting statuses for a run."""
    run = get_run_or_404(run_id)
    meetings = run.get("meetings", {})
    
    return {
        "run_id": run_id,
        "meetings": meetings
    }


@app.get("/api/meeting/{token}")
async def get_meeting_status(token: str) -> Dict:
    """Get meeting status by token."""
    meeting = get_meeting_by_token(token)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return {
        "meeting": meeting
    }
