"""
Legacy Streamlit prototype for Talent Scout Studio.

The primary maintained application is the FastAPI web UI served by:
`uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000`
"""
import json
from datetime import datetime
from pathlib import Path
import sys
import tempfile

from dotenv import load_dotenv
import pandas as pd
import streamlit as st

# Load environment variables from .env file
load_dotenv()

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent / "agent"))

from orchestrator import load_candidates, run_full_pipeline, run_match_only_pipeline
from config import CHAT_MODEL, EMBED_MODEL
from interest_scorer import score_interest
from ollama_client import get_ollama_client

try:
    from streamlit_webrtc import WebRtcMode, webrtc_streamer
    WEBRTC_AVAILABLE = True
except Exception:
    WEBRTC_AVAILABLE = False


def recommend_next_step(candidate: dict) -> str:
    """Simple action recommendation to help recruiters move faster."""
    score = candidate.get("combined_score", 0)
    red_flags = candidate.get("red_flags", [])
    availability = (candidate.get("availability") or "").lower()

    if red_flags:
        return "Review risk signals before moving forward"
    if score >= 80 and "2" in availability:
        return "Prioritize for immediate interview"
    if score >= 70:
        return "Schedule screening call this week"
    if score >= 60:
        return "Keep warm, request more details"
    return "Hold for later batch"


def _clean_done_tokens(text: str) -> str:
    cleaned = text.replace("RECRUITER_DONE", "").replace("CANDIDATE_DONE", "").strip()
    return cleaned


def generate_recruiter_question(jd_parsed: dict, conversation: list[dict]) -> str:
    """Generate exactly one recruiter question for real interview mode."""
    prompt = f"""
You are a warm professional recruiter interviewing a real human candidate for:
Role: {jd_parsed.get("role", "this role")}

Ask exactly one concise next question.
If enough info has been collected, end with RECRUITER_DONE.
Do not answer as the candidate.
"""
    messages = [{"role": "system", "content": prompt}]
    for msg in conversation:
        role = "assistant" if msg.get("speaker") == "recruiter" else "user"
        messages.append({"role": role, "content": msg.get("text", "")})

    client = get_ollama_client()
    response = client.chat(model=CHAT_MODEL, messages=messages)
    return response["message"]["content"]


def update_candidate_from_real_interview(results: dict, candidate_name: str, conversation: list[dict]) -> None:
    """Update one candidate in results with live interest scoring from human interview."""
    interest_result = score_interest(conversation)

    for candidate in results.get("ranked_candidates", []):
        if candidate.get("name") != candidate_name:
            continue
        candidate["conversation"] = conversation
        candidate["interest_score"] = float(interest_result.get("interest_score", 0))
        candidate["availability"] = interest_result.get("availability", "Unknown")
        candidate["key_signals"] = interest_result.get("key_signals", [])
        candidate["red_flags"] = interest_result.get("red_flags", [])
        candidate["combined_score"] = round(
            float(candidate.get("match_score", 0)) * 0.60 +
            float(candidate.get("interest_score", 0)) * 0.40,
            1
        )
        break

    results["ranked_candidates"] = sorted(
        results.get("ranked_candidates", []),
        key=lambda item: item.get("combined_score", 0),
        reverse=True
    )


@st.cache_resource(show_spinner=False)
def _load_whisper_model(model_name: str):
    import whisper
    return whisper.load_model(model_name)


def transcribe_audio_to_text(audio_blob, model_name: str = "tiny") -> tuple[str, str]:
    """
    Transcribe recorded audio to text.
    Returns (text, error_message). Exactly one will be non-empty.
    """
    if audio_blob is None:
        return "", "No audio recorded yet."

    temp_path = ""
    try:
        model = _load_whisper_model(model_name)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_blob.getvalue())
            temp_path = tmp_file.name
        result = model.transcribe(
            temp_path,
            fp16=False,
            temperature=0,
            best_of=1,
            beam_size=1,
            language="en",
            condition_on_previous_text=False
        )
        transcript = (result.get("text") or "").strip()
        if not transcript:
            return "", "Could not detect speech in audio."
        return transcript, ""
    except ImportError:
        return "", "Voice transcription needs the `whisper` package. Install with: pip install openai-whisper"
    except Exception as exc:
        return "", f"Voice transcription failed: {str(exc)}"
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass


def get_latest_recruiter_question(history: list[dict]) -> str:
    """Get the last recruiter message from conversation history."""
    for msg in reversed(history):
        if msg.get("speaker") == "recruiter":
            return msg.get("text", "")
    return ""


def render_interview_chat(history: list[dict]) -> None:
    """Render transcript as chat bubbles for smoother interview UX."""
    for msg in history:
        speaker = msg.get("speaker")
        role = "assistant" if speaker == "recruiter" else "user"
        with st.chat_message(role):
            st.markdown(msg.get("text", ""))


def render_live_video_panel(selected_candidate: str) -> None:
    """Render optional live video feed for real interview mode."""
    st.markdown("**Live Video Interview**")
    if not WEBRTC_AVAILABLE:
        st.info(
            "Live video requires `streamlit-webrtc`. Install with: "
            "`conda run -n base python -m pip install streamlit-webrtc`"
        )
        return

    webrtc_streamer(
        key=f"video_interview_{selected_candidate.lower().replace(' ', '_')}",
        mode=WebRtcMode.SENDRECV,
        media_stream_constraints={"video": True, "audio": True},
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        },
        async_processing=True
    )


st.set_page_config(
    page_title="Talent Scout Agent",
    page_icon="TS",
    layout="wide"
)

if "jd_input" not in st.session_state:
    st.session_state.jd_input = ""
if "real_sessions" not in st.session_state:
    st.session_state.real_sessions = {}

st.title("AI-Powered Talent Scouting and Engagement Agent")
st.markdown(
    """
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
.app-subtitle {font-size: 1.0rem; color: #4c647a; margin-bottom: .4rem;}
.soft-card {
  border: 1px solid #d6e3f0;
  border-radius: 14px;
  padding: 14px 16px;
  background: linear-gradient(180deg, #f8fbff 0%, #eef6ff 100%);
}
</style>
""",
    unsafe_allow_html=True
)

st.markdown(
    """
### Recruit Smarter, Faster
Paste a job description and the app will:
1. Parse the role and required skills
2. Find matching candidates from the database
3. Score fit and interview interest
4. Rank candidates with combined scoring
"""
)

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    top_k = st.slider("Top candidates to evaluate", 3, 10, 5)
    live_mode = st.toggle("Live pipeline mode", value=True)
    whisper_speed_mode = st.selectbox(
        "Voice transcription speed",
        options=["Fastest (tiny)", "Balanced (base)", "Better quality (small)"],
        index=0
    )
    whisper_model_name = {
        "Fastest (tiny)": "tiny",
        "Balanced (base)": "base",
        "Better quality (small)": "small"
    }[whisper_speed_mode]
    interview_mode = st.radio(
        "Interview Mode",
        ["Demo (AI vs AI)", "Real (AI interviewer + human candidate)"],
        index=0
    )
    is_real_mode = interview_mode.startswith("Real")
    st.caption(f"Chat model: {CHAT_MODEL}")
    st.caption(f"Embedding model: {EMBED_MODEL}")

    st.markdown("---")
    st.markdown("### Scoring Weights")
    st.markdown("Match Score: 60%")
    st.markdown("Interest Score: 40%")

# Main content
jd_input_container = st.container()

col1, col2, col3 = st.columns(3)

with col1:
    run_clicked = st.button("Find Candidates", width="stretch")

with col2:
    load_sample_clicked = st.button("Load Sample JD", width="stretch")

with col3:
    clear_clicked = st.button("Clear", width="stretch")

if load_sample_clicked:
    try:
        sample_jd_path = Path(__file__).parent / "tests" / "sample_jd.txt"
        with open(sample_jd_path, "r", encoding="utf-8") as file:
            st.session_state.jd_input = file.read()
        st.success("Sample JD loaded")
        st.rerun()
    except Exception as exc:
        st.error(f"Sample JD not found at {sample_jd_path}: {exc}")

if clear_clicked:
    st.session_state.pop("results", None)
    st.session_state.pop("last_run_at", None)
    st.session_state.pop("live_events", None)
    st.session_state.real_sessions = {}
    st.session_state.jd_input = ""
    st.rerun()

with jd_input_container:
    st.text_area(
        "Paste Job Description",
        height=220,
        key="jd_input",
        placeholder="Senior Full Stack Engineer - FinTech Platform\n\nAbout Us:\n..."
    )

if run_clicked:
    jd_text = st.session_state.jd_input.strip()
    if not jd_text:
        st.error("Please paste a job description first.")
    else:
        live_section = st.container()
        with live_section:
            st.subheader("Live Pipeline")
            status_box = st.empty()
            progress_bar = st.progress(0)
            leaderboard_box = st.empty()
            interview_box = st.empty()
            events_box = st.empty()

        live_state = {
            "events": [],
            "match_scores": {},
            "interest_scores": {},
            "candidate_meta": {},
            "current_candidate": "",
            "interview_transcripts": {}
        }

        def render_live_views() -> None:
            rows = []
            for name, match in live_state["match_scores"].items():
                interest = live_state["interest_scores"].get(name, 0.0)
                meta = live_state["candidate_meta"].get(name, {})
                combined_live = (0.6 * float(match)) + (0.4 * float(interest))
                rows.append(
                    {
                        "Candidate": name,
                        "Title": meta.get("title", "N/A"),
                        "Match": round(float(match), 1),
                        "Interest": round(float(interest), 1),
                        "Live Combined": round(combined_live, 1)
                    }
                )

            if rows:
                df = pd.DataFrame(rows).sort_values("Live Combined", ascending=False)
                leaderboard_box.dataframe(df, width="stretch", hide_index=True)

            if live_state["current_candidate"]:
                name = live_state["current_candidate"]
                transcript = live_state["interview_transcripts"].get(name, [])
                interview_lines = [f"Current candidate: {name}", ""]
                if transcript:
                    for msg in transcript:
                        speaker = "Recruiter" if msg.get("speaker") == "recruiter" else "Candidate"
                        interview_lines.append(f"{speaker}: {msg.get('text', '')[:220]}")
                else:
                    interview_lines.append("Interview in progress...")
                interview_box.code("\n".join(interview_lines), language="text")

            event_text = "\n".join(live_state["events"][-8:])
            if event_text:
                events_box.code(event_text, language="text")

        def progress_cb(event: str, payload: dict) -> None:
            if event == "stage_start":
                status_box.info(payload.get("message", "Working..."))
                progress_bar.progress(int(payload.get("progress", 0)))
                live_state["events"].append(f"Stage: {payload.get('stage', 'unknown')}")

            elif event == "candidate_match_scored":
                candidate = payload.get("candidate", {})
                name = candidate.get("name", "Unknown")
                live_state["match_scores"][name] = float(candidate.get("match_score", 0))
                live_state["candidate_meta"][name] = {"title": candidate.get("title", "N/A")}
                idx = payload.get("index", 0)
                total = payload.get("total", 1)
                live_state["events"].append(f"Match scored ({idx}/{total}): {name}")

            elif event == "candidate_interview_start":
                candidate = payload.get("candidate", {})
                name = candidate.get("name", "Unknown")
                idx = payload.get("index", 0)
                total = payload.get("total", 1)
                live_state["current_candidate"] = name
                live_state["interview_transcripts"][name] = []
                live_state["events"].append(f"Interview started ({idx}/{total}): {name}")

            elif event == "candidate_interview_turn":
                candidate = payload.get("candidate", {})
                name = candidate.get("name", "Unknown")
                message = payload.get("message", {})
                live_state["current_candidate"] = name
                if name not in live_state["interview_transcripts"]:
                    live_state["interview_transcripts"][name] = []
                live_state["interview_transcripts"][name].append({
                    "speaker": message.get("speaker", "candidate"),
                    "text": _clean_done_tokens(message.get("text", ""))
                })
                speaker = message.get("speaker", "candidate")
                live_state["events"].append(f"Turn update: {name} ({speaker})")

            elif event == "candidate_interest_scored":
                candidate = payload.get("candidate", {})
                name = candidate.get("name", "Unknown")
                live_state["interest_scores"][name] = float(candidate.get("interest_score", 0))
                live_state["candidate_meta"][name] = {"title": candidate.get("title", "N/A")}
                live_state["interview_transcripts"][name] = [
                    {
                        "speaker": msg.get("speaker", "candidate"),
                        "text": _clean_done_tokens(msg.get("text", ""))
                    }
                    for msg in candidate.get("conversation", [])
                ]
                idx = payload.get("index", 0)
                total = payload.get("total", 1)
                live_state["events"].append(f"Interview scored ({idx}/{total}): {name}")

            elif event == "pipeline_complete":
                progress_bar.progress(100)
                status_box.success("Pipeline completed successfully.")
                live_state["current_candidate"] = ""
                live_state["events"].append("Pipeline complete")

            render_live_views()

        with st.spinner("Running talent scout pipeline..."):
            try:
                candidates_data = load_candidates("data/candidates.json")
                if is_real_mode:
                    results = run_match_only_pipeline(
                        jd_text,
                        candidates_data,
                        top_k=top_k,
                        progress_cb=progress_cb if live_mode else None
                    )
                    st.session_state.real_sessions = {}
                else:
                    results = run_full_pipeline(
                        jd_text,
                        candidates_data,
                        top_k=top_k,
                        progress_cb=progress_cb if live_mode else None
                    )

                st.session_state.results = results
                st.session_state.live_events = live_state["events"]
                st.session_state.last_run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success("Pipeline completed.")
            except Exception as exc:
                st.error(f"Error: {str(exc)}")

# Display results
if "results" in st.session_state:
    results = st.session_state.results

    st.markdown("---")
    st.header("Results")
    if "last_run_at" in st.session_state:
        st.caption(f"Last run: {st.session_state.last_run_at}")

    ranked_candidates = results.get("ranked_candidates", [])

    # Summary metrics
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.metric("Role", results["jd_parsed"].get("role", "N/A"))
    with mcol2:
        st.metric("Candidates Evaluated", results.get("total_processed", 0))
    with mcol3:
        top_score = ranked_candidates[0].get("combined_score", 0) if ranked_candidates else 0
        st.metric("Top Score", f"{top_score:.1f}/100")
    with mcol4:
        top_name = ranked_candidates[0].get("name", "N/A") if ranked_candidates else "N/A"
        st.metric("Top Candidate", top_name)

    results_mode = results.get("pipeline_mode", "demo")
    if results_mode == "real" and ranked_candidates:
        st.markdown("---")
        st.subheader("Real Interview Console")
        st.caption("AI asks one question at a time, candidate responds, score updates, then AI asks next.")

        interviewed_count = sum(
            1 for sess in st.session_state.real_sessions.values() if sess.get("history")
        )
        done_count = sum(
            1 for sess in st.session_state.real_sessions.values() if sess.get("done")
        )

        hcol1, hcol2, hcol3 = st.columns([2, 1, 1])
        with hcol1:
            candidate_options = [c.get("name", "Unknown") for c in ranked_candidates]
            selected_candidate = st.selectbox(
                "Candidate for live interview",
                options=candidate_options,
                key="real_candidate_select"
            )
        with hcol2:
            st.metric("Started", f"{interviewed_count}/{len(ranked_candidates)}")
        with hcol3:
            st.metric("Completed", f"{done_count}/{len(ranked_candidates)}")

        if selected_candidate not in st.session_state.real_sessions:
            st.session_state.real_sessions[selected_candidate] = {"history": [], "done": False}

        session = st.session_state.real_sessions[selected_candidate]
        response_key = f"real_human_response_{selected_candidate.lower().replace(' ', '_')}"
        pending_response_key = f"{response_key}_pending"
        if response_key not in st.session_state:
            st.session_state[response_key] = ""
        if pending_response_key in st.session_state:
            st.session_state[response_key] = st.session_state.pop(pending_response_key)

        ctrl1, ctrl2 = st.columns(2)
        with ctrl1:
            start_clicked = st.button(
                "Start Interview",
                width="stretch",
                disabled=bool(session.get("history"))
            )
        with ctrl2:
            reset_clicked = st.button("Reset This Candidate", width="stretch")

        if reset_clicked:
            st.session_state.real_sessions[selected_candidate] = {"history": [], "done": False}
            st.session_state[response_key] = ""
            st.session_state.pop(pending_response_key, None)
            st.rerun()

        if start_clicked and not session.get("history"):
            with st.spinner("Generating first interviewer question..."):
                question = generate_recruiter_question(results.get("jd_parsed", {}), [])
                clean_question = _clean_done_tokens(question)
                if clean_question:
                    st.session_state.real_sessions[selected_candidate]["history"].append(
                        {"speaker": "recruiter", "text": clean_question}
                    )
                st.session_state.real_sessions[selected_candidate]["done"] = "RECRUITER_DONE" in question
            st.rerun()

        enable_video = st.toggle(
            "Enable live video interview",
            key=f"video_toggle_{selected_candidate}",
            value=True
        )
        if enable_video:
            with st.container(border=True):
                render_live_video_panel(selected_candidate)

        with st.container(border=True):
            st.markdown("**Live Transcript**")
            if session.get("history"):
                render_interview_chat(session.get("history", []))
            else:
                st.info("Click `Start Interview` to begin.")

        latest_question = get_latest_recruiter_question(session.get("history", []))
        if latest_question and not session.get("done"):
            st.markdown(
                f"<div class='soft-card'><strong>Current AI Question</strong><br>{latest_question}</div>",
                unsafe_allow_html=True
            )

        if not session.get("done"):
            incol1, incol2 = st.columns([2, 1])
            with incol1:
                with st.form(f"response_form_{selected_candidate}", clear_on_submit=False):
                    st.text_area(
                        "Candidate response (text)",
                        key=response_key,
                        height=120,
                        placeholder="Type candidate response here or use voice transcription on the right."
                    )
                    submit_response = st.form_submit_button("Send Response and Get Next Question")

            with incol2:
                audio_blob = None
                if hasattr(st, "audio_input"):
                    audio_blob = st.audio_input("Voice response")
                    st.caption("First run of each model may download once.")
                    transcribe_clicked = st.button(
                        "Transcribe to Draft",
                        key=f"transcribe_{selected_candidate}",
                        width="stretch"
                    )
                    if transcribe_clicked:
                        with st.spinner("Transcribing audio..."):
                            transcript, error = transcribe_audio_to_text(
                                audio_blob,
                                model_name=whisper_model_name
                            )
                        if error:
                            st.warning(error)
                        else:
                            st.session_state[pending_response_key] = transcript
                            st.rerun()
                else:
                    st.caption("Voice capture requires newer Streamlit.")

            if submit_response:
                response_text = st.session_state.get(response_key, "").strip()
                if not response_text:
                    st.warning("Please enter candidate response before submitting.")
                else:
                    with st.spinner("Scoring response and preparing next question..."):
                        st.session_state.real_sessions[selected_candidate]["history"].append(
                            {"speaker": "candidate", "text": response_text}
                        )
                        convo = st.session_state.real_sessions[selected_candidate]["history"]
                        try:
                            update_candidate_from_real_interview(results, selected_candidate, convo)
                        except Exception as exc:
                            st.warning(f"Live scoring error: {str(exc)}")

                        next_question = generate_recruiter_question(results.get("jd_parsed", {}), convo)
                        clean_question = _clean_done_tokens(next_question)
                        if clean_question:
                            st.session_state.real_sessions[selected_candidate]["history"].append(
                                {"speaker": "recruiter", "text": clean_question}
                            )
                        st.session_state.real_sessions[selected_candidate]["done"] = "RECRUITER_DONE" in next_question
                        st.session_state.results = results
                        st.session_state[pending_response_key] = ""
                    st.rerun()
        else:
            st.success("Interview completed for this candidate.")

    st.markdown("---")
    st.subheader("Shortlist Controls")
    fcol1, fcol2 = st.columns(2)

    with fcol1:
        min_combined = st.slider("Minimum combined score", 0, 100, 0)

    with fcol2:
        availability_options = sorted(
            {
                c.get("availability", "Unknown")
                for c in ranked_candidates
                if c.get("availability")
            }
        )
        selected_availability = st.multiselect(
            "Availability filter",
            options=availability_options,
            default=availability_options
        )

    filtered = []
    for candidate in ranked_candidates:
        score_ok = candidate.get("combined_score", 0) >= min_combined
        availability = candidate.get("availability")
        availability_ok = (
            True
            if not availability_options
            else availability in selected_availability
        )
        if score_ok and availability_ok:
            filtered.append(candidate)

    st.subheader("Ranked Shortlist")
    st.caption(f"Showing {len(filtered)} of {len(ranked_candidates)} candidates")

    for i, candidate in enumerate(filtered[:10], 1):
        title = candidate.get("title", "Unknown Title")
        score = candidate.get("combined_score", 0)
        with st.expander(
            f"#{i} {candidate.get('name', 'Unknown')} - {title} | Score: {score:.1f}/100",
            expanded=(i == 1)
        ):
            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric("Combined Score", f"{candidate.get('combined_score', 0):.1f}")
                st.metric("Match Score", f"{candidate.get('match_score', 0):.1f}")

            with c2:
                st.metric("Interest Score", f"{candidate.get('interest_score', 0):.1f}")
                st.metric("Availability", candidate.get("availability", "Unknown"))

            with c3:
                st.metric("Company", candidate.get("current_company", "N/A"))
                st.metric("Experience", f"{candidate.get('years_exp', 0)} years")

            st.info(f"Recommended next step: {recommend_next_step(candidate)}")

            if candidate.get("skills"):
                st.markdown("**Skills:** " + ", ".join(candidate.get("skills", [])))

            if candidate.get("match_explanation"):
                st.markdown("**Match Details:**")
                st.json(candidate.get("match_explanation"))

            if candidate.get("key_signals"):
                st.markdown("**Key Signals:**")
                for signal in candidate.get("key_signals", []):
                    st.write(f"- {signal}")

            if candidate.get("red_flags"):
                st.warning("Red Flags")
                for flag in candidate.get("red_flags", []):
                    st.write(f"- {flag}")

            if candidate.get("conversation"):
                st.markdown("**Conversation Excerpt:**")
                for msg in candidate.get("conversation", [])[:4]:
                    speaker = "Recruiter" if msg.get("speaker") == "recruiter" else "Candidate"
                    text = msg.get("text", "")
                    st.write(f"{speaker}: {text[:220]}")

    # Export functionality
    st.markdown("---")
    st.subheader("Export Results")

    results_json = json.dumps(results, indent=2, default=str)
    st.download_button(
        label="Download Results as JSON",
        data=results_json,
        file_name="talent_scout_results.json",
        mime="application/json"
    )

    shortlist_df = pd.DataFrame(
        [
            {
                "Rank": i,
                "Name": c.get("name"),
                "Title": c.get("title"),
                "Company": c.get("current_company"),
                "Experience (years)": c.get("years_exp"),
                "Match Score": c.get("match_score"),
                "Interest Score": c.get("interest_score"),
                "Combined Score": c.get("combined_score"),
                "Availability": c.get("availability"),
                "Recommended Action": recommend_next_step(c)
            }
            for i, c in enumerate(filtered[:10], 1)
        ]
    )

    csv_data = shortlist_df.to_csv(index=False)
    st.download_button(
        label="Download Shortlist as CSV",
        data=csv_data,
        file_name="talent_shortlist.csv",
        mime="text/csv"
    )

else:
    st.info("Paste a job description and click 'Find Candidates' to get started.")
