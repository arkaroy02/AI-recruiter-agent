const state = {
  runId: null,
  results: null,
  mode: "demo",
  sessions: {},
  selectedCandidate: null,
  candidateSource: { type: "sample_dataset", count: 0, filenames: [] },
  activeWorkspace: "results",
  pendingAction: "",
  liveMode: false,
  isListening: false,
  isSpeaking: false,
  finalVoiceTimer: null,
  recognition: null,
  browserSpeechSupported: Boolean(window.speechSynthesis),
  browserRecognitionSupported: Boolean(window.SpeechRecognition || window.webkitSpeechRecognition),
};

const el = {
  healthBadge: document.getElementById("healthBadge"),
  statusText: document.getElementById("statusText"),
  runIdText: document.getElementById("runIdText"),

  resumeFileInput: document.getElementById("resumeFileInput"),
  uploadResumesBtn: document.getElementById("uploadResumesBtn"),
  clearResumesBtn: document.getElementById("clearResumesBtn"),
  resumeSourceText: document.getElementById("resumeSourceText"),
  resumeList: document.getElementById("resumeList"),

  jdInput: document.getElementById("jdInput"),
  topKRange: document.getElementById("topKRange"),
  topKValue: document.getElementById("topKValue"),
  modeSelect: document.getElementById("modeSelect"),
  voiceModelSelect: document.getElementById("voiceModelSelect"),

  runBtn: document.getElementById("runBtn"),
  sampleBtn: document.getElementById("sampleBtn"),
  clearBtn: document.getElementById("clearBtn"),

  workspaceTabs: document.getElementById("workspaceTabs"),
  resultsTabBtn: document.getElementById("resultsTabBtn"),
  interviewTabBtn: document.getElementById("interviewTabBtn"),
  openInterviewStudioBtn: document.getElementById("openInterviewStudioBtn"),
  resultsPanel: document.getElementById("resultsPanel"),
  interviewPanel: document.getElementById("interviewPanel"),
  interviewEmptyState: document.getElementById("interviewEmptyState"),

  summarySection: document.getElementById("summarySection"),
  metricRole: document.getElementById("metricRole"),
  metricCount: document.getElementById("metricCount"),
  metricTopScore: document.getElementById("metricTopScore"),
  metricTopCandidate: document.getElementById("metricTopCandidate"),

  resultsSection: document.getElementById("resultsSection"),
  candidateGrid: document.getElementById("candidateGrid"),
  candidateInsightPanel: document.getElementById("candidateInsightPanel"),

  interviewSection: document.getElementById("interviewSection"),
  interviewProgress: document.getElementById("interviewProgress"),
  interviewCandidateSelect: document.getElementById("interviewCandidateSelect"),
  startInterviewBtn: document.getElementById("startInterviewBtn"),
  liveInterviewBtn: document.getElementById("liveInterviewBtn"),
  resetInterviewBtn: document.getElementById("resetInterviewBtn"),
  liveBadge: document.getElementById("liveBadge"),
  thinkingBadge: document.getElementById("thinkingBadge"),
  liveHint: document.getElementById("liveHint"),
  currentQuestionCard: document.getElementById("currentQuestionCard"),
  chatFeed: document.getElementById("chatFeed"),
  responseInput: document.getElementById("responseInput"),
  sendResponseBtn: document.getElementById("sendResponseBtn"),
  audioFileInput: document.getElementById("audioFileInput"),
  transcribeBtn: document.getElementById("transcribeBtn"),
};

function escapeHtml(text) {
  return String(text || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  let payload = {};
  try {
    payload = await response.json();
  } catch (_err) {
    payload = {};
  }
  if (!response.ok) {
    throw new Error(payload.detail || `${response.status} ${response.statusText}`);
  }
  return payload;
}

function setStatus(text, variant = "idle") {
  el.statusText.textContent = text;
  el.statusText.className = `status ${variant}`;
}

function setButtonsDisabled(disabled) {
  el.runBtn.disabled = disabled;
  el.sampleBtn.disabled = disabled;
  el.uploadResumesBtn.disabled = disabled;
  el.clearResumesBtn.disabled = disabled;
}

function setPendingAction(action) {
  state.pendingAction = action || "";
  renderLiveMeta();
}

function topCandidate(results) {
  const list = results?.ranked_candidates || [];
  return list.length ? list[0] : null;
}

function getSelectedSession() {
  return state.selectedCandidate ? getSession(state.selectedCandidate) : { history: [], done: false };
}

function getSelectedCandidateRecord() {
  const candidates = state.results?.ranked_candidates || [];
  return candidates.find((candidate) => candidate.name === state.selectedCandidate) || candidates[0] || null;
}

function getSession(candidateName) {
  if (!state.sessions[candidateName]) {
    state.sessions[candidateName] = { history: [], done: false };
  }
  return state.sessions[candidateName];
}

function nextCandidateNameAfter(currentCandidateName) {
  const candidates = state.results?.ranked_candidates || [];
  if (!candidates.length) {
    return null;
  }

  const currentIndex = candidates.findIndex((candidate) => candidate.name === currentCandidateName);
  const orderedNames = candidates.map((candidate) => candidate.name);
  const fallbackNames = currentIndex >= 0
    ? [...orderedNames.slice(currentIndex + 1), ...orderedNames.slice(0, currentIndex)]
    : orderedNames;

  return fallbackNames.find((candidateName) => {
    const session = state.sessions[candidateName];
    return !session || !session.done;
  }) || null;
}

function latestRecruiterQuestion(history) {
  for (let idx = history.length - 1; idx >= 0; idx -= 1) {
    if (history[idx].speaker === "recruiter") {
      return history[idx].text;
    }
  }
  return "";
}

function canUseInterviewWorkspace() {
  return Boolean(state.results) && state.mode === "real";
}

function setActiveWorkspace(view) {
  if (view === "interview" && !canUseInterviewWorkspace()) {
    state.activeWorkspace = "results";
    return;
  }
  state.activeWorkspace = view;
}

function renderCandidateSource() {
  const source = state.candidateSource || { type: "sample_dataset", count: 0, filenames: [] };
  const isUploaded = source.type === "uploaded_resumes";
  if (isUploaded) {
    el.resumeSourceText.textContent = `Using ${source.count} uploaded PDF resume${source.count === 1 ? "" : "s"} for matching.`;
    el.resumeList.innerHTML = (source.filenames || [])
      .map((filename) => `<div>${escapeHtml(filename)}</div>`)
      .join("");
  } else {
    el.resumeSourceText.textContent = `Using built-in sample candidate dataset (${source.count || 0} profiles).`;
    el.resumeList.innerHTML = `<div>No PDFs uploaded yet.</div>`;
  }
}

function renderWorkspaceTabs() {
  const hasResults = Boolean(state.results);
  const canInterview = canUseInterviewWorkspace();

  el.workspaceTabs.classList.toggle("hidden", !hasResults);
  el.resultsPanel.classList.toggle("hidden", !hasResults || state.activeWorkspace !== "results");
  el.interviewPanel.classList.toggle("hidden", !hasResults || state.activeWorkspace !== "interview");

  el.resultsTabBtn.classList.toggle("active", state.activeWorkspace === "results");
  el.interviewTabBtn.classList.toggle("active", state.activeWorkspace === "interview");
  el.interviewTabBtn.disabled = !canInterview;
  el.openInterviewStudioBtn.classList.toggle("hidden", !canInterview);
  el.interviewEmptyState.classList.toggle("hidden", canInterview);
}

function renderSummary() {
  if (!state.results) {
    el.summarySection.classList.add("hidden");
    return;
  }

  const top = topCandidate(state.results);
  el.metricRole.textContent = state.results.jd_parsed?.role || "-";
  el.metricCount.textContent = String(state.results.total_processed || 0);
  el.metricTopScore.textContent = top ? `${Number(top.combined_score || 0).toFixed(1)}/100` : "-";
  el.metricTopCandidate.textContent = top?.name || "-";

  el.summarySection.classList.remove("hidden");
}

function recommendationLabel(candidate) {
  const combined = Number(candidate?.combined_score || 0);
  const redFlags = candidate?.red_flags || [];
  if (combined >= 75 && redFlags.length === 0) {
    return { text: "Strong follow-up", tone: "strong" };
  }
  if (combined >= 55) {
    return { text: "Worth discussing", tone: "" };
  }
  return { text: "Proceed with caution", tone: "caution" };
}

function candidateStrengths(candidate) {
  const strengths = [];
  const requiredHits = candidate?.match_explanation?.required_skills_hit || [];
  if (requiredHits.length) {
    strengths.push(`Hits core skills: ${requiredHits.slice(0, 4).join(", ")}`);
  }
  if (Number(candidate?.match_score || 0) >= 60) {
    strengths.push(`Solid role fit with a ${Number(candidate.match_score).toFixed(1)} match score`);
  }
  if ((candidate?.key_signals || []).length) {
    strengths.push(...candidate.key_signals.slice(0, 2));
  }
  if (candidate?.availability && candidate.availability !== "Unknown" && candidate.availability !== "Pending real interview") {
    strengths.push(`Availability signal: ${candidate.availability}`);
  }
  if (!strengths.length) {
    strengths.push("Profile looks directionally relevant, but stronger interview evidence is still needed.");
  }
  return strengths.slice(0, 4);
}

function candidateWatchouts(candidate) {
  const watchouts = [];
  const missingSkills = candidate?.match_explanation?.required_skills_missing || [];
  if (missingSkills.length) {
    watchouts.push(`Missing core skills: ${missingSkills.slice(0, 4).join(", ")}`);
  }
  if (Number(candidate?.interest_score || 0) > 0 && Number(candidate?.interest_score || 0) < 45) {
    watchouts.push(`Interest looks weak at ${Number(candidate.interest_score).toFixed(1)}`);
  }
  if ((candidate?.red_flags || []).length) {
    watchouts.push(...candidate.red_flags.slice(0, 3));
  }
  if (!watchouts.length) {
    watchouts.push("No major watchouts captured yet.");
  }
  return watchouts.slice(0, 4);
}

function candidateNextStep(candidate) {
  const recommendation = recommendationLabel(candidate);
  if (recommendation.tone === "strong") {
    return "Good candidate to move into a deeper recruiter or hiring manager conversation.";
  }
  if (recommendation.tone === "caution") {
    return "Use a deeper screen only if the role is flexible on the current gaps or the candidate pool is thin.";
  }
  return "Reasonable shortlist candidate. Use the next conversation to validate the missing pieces.";
}

function candidateCardHtml(candidate, index) {
  const combined = Number(candidate.combined_score || 0);
  const match = Number(candidate.match_score || 0);
  const interest = Number(candidate.interest_score || 0);
  const availability = candidate.availability || "Unknown";
  const active = candidate.name === state.selectedCandidate ? " active" : "";

  return `
    <article class="candidate-card${active}" data-candidate-name="${escapeHtml(candidate.name || "")}">
      <h4>#${index + 1} ${escapeHtml(candidate.name || "Unknown")}</h4>
      <p class="candidate-meta">${escapeHtml(candidate.title || "Unknown title")} - ${escapeHtml(candidate.current_company || "N/A")}</p>

      <div class="score-row"><span>Combined</span><strong>${combined.toFixed(1)}</strong></div>
      <div class="score-bar"><div class="score-fill" style="width:${Math.max(0, Math.min(100, combined))}%"></div></div>

      <div class="score-row"><span>Match</span><span>${match.toFixed(1)}</span></div>
      <div class="score-row"><span>Interest</span><span>${interest.toFixed(1)}</span></div>
      <div class="score-row"><span>Availability</span><span>${escapeHtml(availability)}</span></div>
    </article>
  `;
}

function renderCandidates() {
  if (!state.results) {
    el.resultsSection.classList.add("hidden");
    el.candidateInsightPanel.classList.add("hidden");
    return;
  }
  const list = state.results.ranked_candidates || [];
  if (!state.selectedCandidate && list.length) {
    state.selectedCandidate = list[0].name;
  }
  el.candidateGrid.innerHTML = list.map((candidate, index) => candidateCardHtml(candidate, index)).join("");
  renderCandidateInsight();
  el.resultsSection.classList.remove("hidden");
}

function renderCandidateInsight() {
  const candidate = getSelectedCandidateRecord();
  if (!candidate) {
    el.candidateInsightPanel.classList.add("hidden");
    el.candidateInsightPanel.innerHTML = "";
    return;
  }

  const recommendation = recommendationLabel(candidate);
  const strengths = candidateStrengths(candidate);
  const watchouts = candidateWatchouts(candidate);
  const summary = Number(candidate.interest_score || 0) > 0
    ? `${candidate.name} has now been rescored with live interview feedback. Combined score is ${Number(candidate.combined_score || 0).toFixed(1)} with match ${Number(candidate.match_score || 0).toFixed(1)} and interest ${Number(candidate.interest_score || 0).toFixed(1)}.`
    : `${candidate.name} is shortlisted mainly on profile fit right now. Interview signals will make this recommendation sharper once the conversation is complete.`;

  el.candidateInsightPanel.innerHTML = `
    <div class="candidate-insight-head">
      <div>
        <p class="eyebrow">Recruiter Snapshot</p>
        <h4>${escapeHtml(candidate.name || "Candidate")}</h4>
        <p class="candidate-meta">${escapeHtml(candidate.title || "Unknown title")} - ${escapeHtml(candidate.current_company || "N/A")}</p>
      </div>
      <span class="recommendation-chip ${recommendation.tone}">${escapeHtml(recommendation.text)}</span>
    </div>
    <p class="insight-summary">${escapeHtml(summary)}</p>
    <div class="candidate-insight-grid">
      <div class="insight-block">
        <h5>Pros</h5>
        <ul class="insight-list">${strengths.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
      <div class="insight-block">
        <h5>Watchouts</h5>
        <ul class="insight-list">${watchouts.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
      <div class="insight-block">
        <h5>Suggested Next Step</h5>
        <ul class="insight-list">
          <li>${escapeHtml(candidateNextStep(candidate))}</li>
          <li>Availability: ${escapeHtml(candidate.availability || "Unknown")}</li>
          <li>Education: ${escapeHtml(candidate.education || "Not provided")}</li>
        </ul>
      </div>
    </div>
  `;
  el.candidateInsightPanel.classList.remove("hidden");
}

function renderInterviewProgress() {
  const sessions = Object.values(state.sessions);
  const started = sessions.filter((session) => (session.history || []).length > 0).length;
  const done = sessions.filter((session) => session.done).length;
  const total = (state.results?.ranked_candidates || []).length;
  el.interviewProgress.textContent = `${done}/${total} completed | ${started} started`;
}

function renderInterviewCandidates() {
  const candidates = state.results?.ranked_candidates || [];
  if (!candidates.length) {
    el.interviewCandidateSelect.innerHTML = "";
    state.selectedCandidate = null;
    return;
  }

  const options = candidates
    .map((candidate) => `<option value="${escapeHtml(candidate.name)}">${escapeHtml(candidate.name)}</option>`)
    .join("");
  el.interviewCandidateSelect.innerHTML = options;

  const stillExists = candidates.some((candidate) => candidate.name === state.selectedCandidate);
  if (!stillExists) {
    state.selectedCandidate = candidates[0].name;
  }
  el.interviewCandidateSelect.value = state.selectedCandidate;
}

function renderChat(session) {
  const history = session?.history || [];
  if (!history.length) {
    el.chatFeed.innerHTML = `<p class="small muted">Start the interview to see the transcript. In live mode, the AI can speak the question and listen for the candidate reply.</p>`;
    return;
  }

  const messages = history
    .map((message) => {
      const cls = message.speaker === "recruiter" ? "recruiter" : "candidate";
      return `<div class="chat-msg ${cls}">${escapeHtml(message.text)}</div>`;
    })
    .join("");

  const typing = state.pendingAction
    ? `<div class="typing-indicator">${escapeHtml(state.pendingAction)}</div>`
    : "";

  el.chatFeed.innerHTML = `${messages}${typing}`;
  el.chatFeed.scrollTop = el.chatFeed.scrollHeight;
}

function renderCurrentQuestion(session) {
  const question = latestRecruiterQuestion(session?.history || []);
  if (!question) {
    el.currentQuestionCard.classList.add("hidden");
    el.currentQuestionCard.innerHTML = "";
    return;
  }

  let caption = "Current AI Question";
  if (session?.done) {
    caption = "Interview Wrap-up";
  } else if (state.pendingAction) {
    caption = "Stay with this question while the next step loads";
  }

  el.currentQuestionCard.innerHTML = `<strong>${escapeHtml(caption)}</strong><br>${escapeHtml(question)}`;
  el.currentQuestionCard.classList.remove("hidden");
}

function renderLiveMeta() {
  if (!state.browserSpeechSupported && !state.browserRecognitionSupported) {
    el.liveBadge.textContent = "Voice not supported";
    el.liveBadge.className = "badge muted";
  } else if (state.liveMode) {
    const liveText = state.isListening ? "Listening..." : state.isSpeaking ? "Speaking..." : "Live voice on";
    el.liveBadge.textContent = liveText;
    el.liveBadge.className = `badge ${state.isListening || state.isSpeaking ? "waiting" : "active"}`;
  } else {
    el.liveBadge.textContent = "Live voice off";
    el.liveBadge.className = "badge muted";
  }

  let thinkingText = "Ready";
  let thinkingClass = "badge muted";
  if (state.pendingAction) {
    thinkingText = state.pendingAction;
    thinkingClass = "badge waiting";
  } else if (getSelectedSession().done) {
    thinkingText = "Interview complete";
    thinkingClass = "badge active";
  }
  el.thinkingBadge.textContent = thinkingText;
  el.thinkingBadge.className = thinkingClass;
}

function renderInterviewControls(session) {
  const started = Boolean((session?.history || []).length);
  const done = Boolean(session?.done);
  const busy = Boolean(state.pendingAction);

  el.startInterviewBtn.disabled = started || busy;
  el.liveInterviewBtn.disabled = busy || (!started && !state.runId);
  el.resetInterviewBtn.disabled = busy || !started;
  el.interviewCandidateSelect.disabled = busy;
  el.responseInput.disabled = !started || done || busy;
  el.sendResponseBtn.disabled = !started || done || busy;
  el.transcribeBtn.disabled = !started || done || busy;

  if (state.liveMode && !done) {
    el.liveInterviewBtn.textContent = "Stop Live Voice";
  } else {
    el.liveInterviewBtn.textContent = "Start Live Voice";
  }

  if (done) {
    el.responseInput.placeholder = "Interview completed for this candidate.";
  } else if (state.isListening) {
    el.responseInput.placeholder = "Listening for the candidate response...";
  } else if (state.pendingAction) {
    el.responseInput.placeholder = "The AI is working on the next step...";
  } else {
    el.responseInput.placeholder = "Type candidate response or use live voice...";
  }
}

function renderInterviewSection() {
  const isRealMode = state.mode === "real";
  if (!state.results || !isRealMode) {
    el.interviewSection.classList.add("hidden");
    el.interviewEmptyState.classList.toggle("hidden", !state.results);
    return;
  }

  renderInterviewCandidates();
  renderInterviewProgress();

  const session = getSelectedSession();
  renderChat(session);
  renderCurrentQuestion(session);
  renderInterviewControls(session);
  renderLiveMeta();

  el.liveHint.classList.toggle("hidden", state.browserSpeechSupported || state.browserRecognitionSupported);
  el.interviewEmptyState.classList.add("hidden");
  el.interviewSection.classList.remove("hidden");
}

function renderAll() {
  renderCandidateSource();
  renderWorkspaceTabs();
  renderSummary();
  renderCandidates();
  renderInterviewSection();
  el.runIdText.textContent = state.runId ? `Run ID: ${state.runId}` : "";
}

function stopSpeaking() {
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  state.isSpeaking = false;
  renderLiveMeta();
}

function stopListening() {
  if (state.finalVoiceTimer) {
    clearTimeout(state.finalVoiceTimer);
    state.finalVoiceTimer = null;
  }
  if (state.recognition) {
    try {
      state.recognition.stop();
    } catch (_err) {
      // Browser throws if recognition is not currently active.
    }
  }
  state.isListening = false;
  renderLiveMeta();
}

function stopLiveMode() {
  state.liveMode = false;
  stopSpeaking();
  stopListening();
  renderAll();
}

function clearState() {
  stopLiveMode();
  state.runId = null;
  state.results = null;
  state.mode = el.modeSelect.value;
  state.sessions = {};
  state.selectedCandidate = null;
  state.activeWorkspace = "results";
  state.pendingAction = "";
  el.responseInput.value = "";
  el.audioFileInput.value = "";
  el.resumeFileInput.value = "";
  renderAll();
  setStatus("Idle", "idle");
}

function setRunResults(runId, results) {
  stopLiveMode();
  state.runId = runId;
  state.results = results;
  state.mode = results.pipeline_mode || el.modeSelect.value;
  state.candidateSource = results.candidate_source || state.candidateSource;
  state.sessions = {};
  state.selectedCandidate = null;
  state.activeWorkspace = "results";
  renderAll();
}

function getVoice() {
  const voices = window.speechSynthesis?.getVoices?.() || [];
  return voices.find((voice) => /en/i.test(voice.lang) && /natural|neural|aria|jenny|guy|samantha|google us english/i.test(voice.name))
    || voices.find((voice) => /en/i.test(voice.lang) && /female|zira|samantha|google/i.test(voice.name))
    || voices.find((voice) => /en/i.test(voice.lang))
    || null;
}

function queueVoiceAutoSend() {
  if (!state.liveMode || state.pendingAction) {
    return;
  }
  if (state.finalVoiceTimer) {
    clearTimeout(state.finalVoiceTimer);
  }
  state.finalVoiceTimer = setTimeout(() => {
    state.finalVoiceTimer = null;
    const responseText = el.responseInput.value.trim();
    if (responseText) {
      sendResponse(true);
    }
  }, 1600);
}

function speakQuestion(text) {
  if (!state.liveMode || !state.browserSpeechSupported || !text) {
    return;
  }

  stopSpeaking();
  const utterance = new SpeechSynthesisUtterance(text);
  const voice = getVoice();
  if (voice) {
    utterance.voice = voice;
  }
  utterance.rate = 0.92;
  utterance.pitch = 1.02;
  utterance.volume = 1;
  utterance.onstart = () => {
    state.isSpeaking = true;
    renderLiveMeta();
  };
  utterance.onend = () => {
    state.isSpeaking = false;
    renderLiveMeta();
    startListening();
  };
  utterance.onerror = () => {
    state.isSpeaking = false;
    renderLiveMeta();
  };
  window.speechSynthesis.speak(utterance);
}

function initRecognition() {
  if (state.recognition || !state.browserRecognitionSupported) {
    return state.recognition;
  }

  const RecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new RecognitionCtor();
  recognition.lang = "en-US";
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;
  recognition.continuous = false;

  recognition.onstart = () => {
    state.isListening = true;
    renderAll();
    setStatus("Listening for the candidate response...", "running");
  };

  recognition.onresult = (event) => {
    if (state.finalVoiceTimer) {
      clearTimeout(state.finalVoiceTimer);
      state.finalVoiceTimer = null;
    }
    const transcript = Array.from(event.results)
      .map((result) => result[0]?.transcript || "")
      .join(" ")
      .trim();
    el.responseInput.value = transcript;

    const latest = event.results[event.results.length - 1];
    if (latest?.isFinal && transcript) {
      setStatus("Answer captured. Waiting for a short pause before sending...", "running");
      queueVoiceAutoSend();
    }
  };

  recognition.onerror = (event) => {
    state.isListening = false;
    renderAll();
    setStatus(`Voice input paused: ${event.error || "speech recognition error"}`, "error");
  };

  recognition.onend = () => {
    state.isListening = false;
    renderAll();
    if (state.liveMode && !state.pendingAction && el.responseInput.value.trim()) {
      queueVoiceAutoSend();
    }
  };

  state.recognition = recognition;
  return recognition;
}

function startListening() {
  if (!state.liveMode || !state.browserRecognitionSupported) {
    return;
  }

  const session = getSelectedSession();
  if (session.done || state.pendingAction) {
    return;
  }

  const recognition = initRecognition();
  if (!recognition) {
    return;
  }

  try {
    recognition.start();
  } catch (_err) {
    // Avoid duplicate-start noise if the browser is already listening.
  }
}

function speakLatestQuestion() {
  const session = getSelectedSession();
  if (!session || session.done) {
    return;
  }
  speakQuestion(latestRecruiterQuestion(session.history || []));
}

async function loadHealth() {
  try {
    await api("/api/health");
    el.healthBadge.textContent = "Backend Ready";
    el.healthBadge.classList.remove("muted");
  } catch (_err) {
    el.healthBadge.textContent = "Backend Offline";
  }
}

async function loadCandidateSource() {
  try {
    const data = await api("/api/resumes/status");
    state.candidateSource = data;
    renderCandidateSource();
  } catch (_err) {
    el.resumeSourceText.textContent = "Could not load current resume source.";
  }
}

async function loadSample() {
  setStatus("Loading sample JD...", "running");
  try {
    const data = await api("/api/sample-jd");
    el.jdInput.value = data.text || "";
    setStatus("Sample loaded", "success");
  } catch (err) {
    setStatus(`Sample load failed: ${err.message}`, "error");
  }
}

async function uploadResumes() {
  const files = Array.from(el.resumeFileInput.files || []);
  if (!files.length) {
    setStatus("Choose one or more PDF resumes first.", "error");
    return;
  }

  setButtonsDisabled(true);
  setPendingAction("Extracting text from uploaded resumes and building candidate profiles...");
  setStatus("Uploading and parsing resumes. This may take a bit on local hardware.", "running");
  try {
    const formData = new FormData();
    for (const file of files) {
      formData.append("files", file);
    }
    const data = await api("/api/resumes/upload", {
      method: "POST",
      body: formData,
    });
    state.candidateSource = data.candidate_source || state.candidateSource;
    renderCandidateSource();
    el.resumeFileInput.value = "";
    const errorCount = (data.errors || []).length;
    if (errorCount) {
      setStatus(`Uploaded ${state.candidateSource.count} resume(s). ${errorCount} file(s) could not be parsed.`, "success");
    } else {
      setStatus(`Uploaded ${state.candidateSource.count} resume(s) successfully.`, "success");
    }
  } catch (err) {
    setStatus(`Resume upload failed: ${err.message}`, "error");
  } finally {
    setButtonsDisabled(false);
    setPendingAction("");
    renderAll();
  }
}

async function clearUploadedResumes() {
  setButtonsDisabled(true);
  setPendingAction("Switching back to the sample candidate dataset...");
  setStatus("Restoring sample candidate dataset...", "running");
  try {
    const data = await api("/api/resumes/clear", { method: "POST" });
    state.candidateSource = data;
    state.results = null;
    state.runId = null;
    state.sessions = {};
    state.selectedCandidate = null;
    state.activeWorkspace = "results";
    el.resumeFileInput.value = "";
    renderAll();
    setStatus("Sample candidate dataset restored.", "success");
  } catch (err) {
    setStatus(`Could not clear uploaded resumes: ${err.message}`, "error");
  } finally {
    setButtonsDisabled(false);
    setPendingAction("");
    renderAll();
  }
}

async function runPipeline() {
  const jdText = el.jdInput.value.trim();
  if (!jdText) {
    setStatus("Please paste a job description first.", "error");
    return;
  }

  stopLiveMode();
  setButtonsDisabled(true);
  setPendingAction("Analyzing the job description and ranking candidates...");
  setStatus("Running pipeline. This can take a little time on local hardware.", "running");
  try {
    const payload = {
      jd_text: jdText,
      top_k: Number(el.topKRange.value),
      interview_mode: el.modeSelect.value,
    };
    const data = await api("/api/pipeline/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setRunResults(data.run_id, data.results);
    setStatus("Pipeline completed.", "success");
  } catch (err) {
    setStatus(`Pipeline failed: ${err.message}`, "error");
  } finally {
    setButtonsDisabled(false);
    setPendingAction("");
    renderAll();
  }
}

async function startInterview() {
  if (!state.runId || !state.selectedCandidate) return;

  stopListening();
  setPendingAction("Preparing the recruiter and writing the opening question...");
  setStatus("Starting interview. The first question may take a few seconds.", "running");
  renderAll();
  try {
    const data = await api("/api/interview/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_id: state.runId, candidate_name: state.selectedCandidate }),
    });
    state.sessions[state.selectedCandidate] = data.session;
    state.results.ranked_candidates = data.ranked_candidates;
    renderAll();
    setStatus("Interview started.", "success");
    if (state.liveMode) {
      speakLatestQuestion();
    }
  } catch (err) {
    setStatus(`Interview start failed: ${err.message}`, "error");
    state.liveMode = false;
  } finally {
    setPendingAction("");
    renderAll();
  }
}

async function resetInterview() {
  if (!state.runId || !state.selectedCandidate) return;

  stopLiveMode();
  setPendingAction("Resetting the interview state...");
  setStatus("Resetting interview...", "running");
  try {
    const data = await api("/api/interview/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_id: state.runId, candidate_name: state.selectedCandidate }),
    });
    state.sessions[state.selectedCandidate] = data.session;
    state.results.ranked_candidates = data.ranked_candidates;
    el.responseInput.value = "";
    el.audioFileInput.value = "";
    renderAll();
    setStatus("Interview reset.", "success");
  } catch (err) {
    setStatus(`Reset failed: ${err.message}`, "error");
  } finally {
    setPendingAction("");
    renderAll();
  }
}

async function sendResponse(fromVoice = false) {
  if (!state.runId || !state.selectedCandidate) return;
  const responseText = el.responseInput.value.trim();
  if (!responseText) {
    setStatus("Please type a response before sending.", "error");
    return;
  }

  stopListening();
  setPendingAction(fromVoice ? "The AI is reviewing the spoken answer and writing the next question..." : "The AI is reviewing the answer and writing the next question...");
  setStatus("Processing response. Keeping the last question visible while it thinks.", "running");
  renderAll();
  try {
    const data = await api("/api/interview/respond", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        run_id: state.runId,
        candidate_name: state.selectedCandidate,
        response_text: responseText,
      }),
    });
    state.sessions[state.selectedCandidate] = data.session;
    state.results.ranked_candidates = data.ranked_candidates;
    const completedCandidate = state.selectedCandidate;
    el.responseInput.value = "";
    const nextCandidate = data.session?.done ? nextCandidateNameAfter(completedCandidate) : null;
    if (nextCandidate) {
      state.selectedCandidate = nextCandidate;
    }
    renderAll();
    if (data.session?.done && nextCandidate) {
      setStatus(`Interview completed for ${completedCandidate}. Switched to ${nextCandidate}.`, "success");
    } else if (data.session?.done) {
      setStatus(`Interview completed for ${completedCandidate}.`, "success");
    } else {
      setStatus("Next question ready.", "success");
    }
    if (state.liveMode && !data.session?.done) {
      speakLatestQuestion();
    } else if (state.liveMode && data.session?.done) {
      stopLiveMode();
    }
  } catch (err) {
    setStatus(`Send failed: ${err.message}`, "error");
  } finally {
    setPendingAction("");
    renderAll();
  }
}

async function transcribeAudio() {
  const file = el.audioFileInput.files?.[0];
  if (!file) {
    setStatus("Choose an audio file first.", "error");
    return;
  }

  setPendingAction("Transcribing audio...");
  setStatus("Transcribing audio...", "running");
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", el.voiceModelSelect.value);
    const data = await api("/api/interview/transcribe", {
      method: "POST",
      body: formData,
    });
    el.responseInput.value = data.text || "";
    setStatus("Transcription complete.", "success");
  } catch (err) {
    setStatus(`Transcription failed: ${err.message}`, "error");
  } finally {
    setPendingAction("");
    renderAll();
  }
}

async function toggleLiveInterview() {
  if (!state.browserSpeechSupported && !state.browserRecognitionSupported) {
    setStatus("This browser does not expose voice tools for live mode. Text mode still works.", "error");
    return;
  }

  if (state.liveMode) {
    stopLiveMode();
    setStatus("Live voice stopped.", "idle");
    return;
  }

  state.liveMode = true;
  renderAll();

  const session = getSelectedSession();
  if (!(session.history || []).length) {
    await startInterview();
    return;
  }

  if (!session.done) {
    setStatus("Live voice started.", "success");
    speakLatestQuestion();
  }
}

function wireEvents() {
  el.topKRange.addEventListener("input", () => {
    el.topKValue.textContent = el.topKRange.value;
  });

  el.modeSelect.addEventListener("change", () => {
    stopLiveMode();
    state.mode = el.modeSelect.value;
    if (state.mode !== "real" && state.activeWorkspace === "interview") {
      state.activeWorkspace = "results";
    }
    renderAll();
  });

  el.resultsTabBtn.addEventListener("click", () => {
    setActiveWorkspace("results");
    renderAll();
  });

  el.interviewTabBtn.addEventListener("click", () => {
    setActiveWorkspace("interview");
    renderAll();
  });

  el.openInterviewStudioBtn.addEventListener("click", () => {
    setActiveWorkspace("interview");
    renderAll();
  });

  el.runBtn.addEventListener("click", runPipeline);
  el.sampleBtn.addEventListener("click", loadSample);
  el.clearBtn.addEventListener("click", clearState);
  el.uploadResumesBtn.addEventListener("click", uploadResumes);
  el.clearResumesBtn.addEventListener("click", clearUploadedResumes);

  el.interviewCandidateSelect.addEventListener("change", () => {
    stopLiveMode();
    state.selectedCandidate = el.interviewCandidateSelect.value;
    renderAll();
  });
  el.candidateGrid.addEventListener("click", (event) => {
    const card = event.target.closest(".candidate-card");
    if (!card) {
      return;
    }
    state.selectedCandidate = card.dataset.candidateName || state.selectedCandidate;
    renderAll();
  });
  el.startInterviewBtn.addEventListener("click", startInterview);
  el.liveInterviewBtn.addEventListener("click", toggleLiveInterview);
  el.resetInterviewBtn.addEventListener("click", resetInterview);
  el.sendResponseBtn.addEventListener("click", () => sendResponse(false));
  el.transcribeBtn.addEventListener("click", transcribeAudio);

  if (window.speechSynthesis?.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = () => renderAll();
  }
}

function init() {
  wireEvents();
  loadHealth();
  loadCandidateSource();
  clearState();
}

init();
