/**
 * @file app.js
 * @description Main application orchestrator.
 */

import { store } from './state.js';
import { api } from './api.js';
import { renderRoute } from './router.js';
import { formatTime } from '../utils/helpers.js';
import { validateResumeFile, validateRequiredString } from '../utils/validators.js';

// Components
import { renderModuleRail } from '../components/module-rail.js';
import { renderStatusBar } from '../components/status-bar.js';
import { toast } from '../components/notification.js';
import { updateNepheleState, STATES } from '../components/nephele-head.js';
import { appendTranscriptMessage, renderTranscriptView } from '../components/transcript-view.js';
import { toggleVoiceVisualizer } from '../components/voice-visualizer.js';
import { renderChallengeView } from '../components/challenge-view.js';
import { renderEvaluationCard } from '../components/evaluation-card.js';
import { renderProfileCard } from '../components/profile-card.js';

// Pages
import { renderHome } from '../pages/home.js';
import { renderInterviewWorkspace } from '../pages/interview.js';
import { renderResumeWorkspace } from '../pages/resume.js';
import { renderCodingWorkspace } from '../pages/coding.js';
import { renderSettings } from '../pages/settings.js';
import { LandingPage } from '../pages/landing.js';

let interviewWS = null;
let visionWS = null;
let visionInterval = null;
let sessionStartTime = null;
let timerInterval = null;

/**
 * Initialize the application shell (DOM is constructed ONCE).
 */
function initAppShell() {
    const app = document.getElementById('app');
    const state = store.get();

    app.innerHTML = `
        <!-- Main Layout Container -->
        <div class="flex h-screen w-screen overflow-hidden text-slate-100">
            <!-- Sidebar -->
            ${renderModuleRail(state.activeRoute)}
            
            <!-- Main Content Area -->
            <main class="flex-1 flex flex-col min-w-0 relative">
                
                <!-- Workspaces (Pre-rendered and toggled via CSS) -->
                <div id="workspace-container" class="flex-1 relative overflow-hidden bg-bg-panel/30">
                    ${LandingPage()}
                    ${renderHome()}
                    ${renderInterviewWorkspace(state)}
                    ${renderResumeWorkspace(state)}
                    ${renderCodingWorkspace(state)}
                    ${renderSettings(state)}
                </div>
                
                <!-- Status Bar -->
                <div id="status-bar-container">
                    ${renderStatusBar(state.healthStatus, state.activeSessionId, state.interviewState)}
                </div>
            </main>
        </div>
    `;

    // Apply routing (shows correct page based on hash)
    renderRoute();
    
    // Bind subscriptions and events
    initSubscriptions();
    bindDOMEvents();
    
    // Start health checks
    refreshHealth();
    setInterval(refreshHealth, 30000);
}

/**
 * Granular state subscriptions to update DOM surgically.
 */
function initSubscriptions() {
    // Session state changes
    store.subscribe('interviewState', (newState) => {
        updateNepheleState(newState);
        toggleVoiceVisualizer(newState === STATES.LISTENING);
        
        // Update status bar safely without re-rendering entire shell
        const s = store.get();
        document.getElementById('status-bar-container').innerHTML = 
            renderStatusBar(s.healthStatus, s.activeSessionId, newState);
        rebindStatusEvent();
    });

    store.subscribe('activeSessionId', (id) => {
        const startOverlay = document.getElementById('interview-start-overlay');
        if (startOverlay) {
            if (id) startOverlay.classList.add('hidden');
            else startOverlay.classList.remove('hidden');
        }
        
        // Timer logic
        if (id) {
            sessionStartTime = Date.now();
            timerInterval = setInterval(() => {
                const el = document.getElementById('status-time');
                if (el) el.textContent = formatTime(Math.floor((Date.now() - sessionStartTime) / 1000));
            }, 1000);
        } else {
            clearInterval(timerInterval);
            const el = document.getElementById('status-time');
            if (el) el.textContent = '00:00:00';
        }
    });

    // Vision Metrics
    store.subscribe('visionMetrics', (metrics) => {
        const eye = document.getElementById('bar-eye');
        const eng = document.getElementById('bar-eng');
        if (eye) eye.style.width = `${Math.min(100, Math.max(0, metrics.eyeContact * 100))}%`;
        if (eng) eng.style.width = `${Math.min(100, Math.max(0, metrics.engagement * 100))}%`;
    });

    // Resume Data
    store.subscribe('candidateProfile', (profile) => {
        const c = document.getElementById('resume-profile-container');
        if (c) c.innerHTML = renderProfileCard(profile);
    });

    store.subscribe('resumeQuestions', (qs) => {
        const c = document.getElementById('resume-questions-container');
        if (c && qs && qs.length > 0) {
            c.innerHTML = `
                <div class="card fade-up mt-6">
                    <h3 class="card-title text-base mb-4">Generated Personalized Interview Questions</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        ${qs.map((q, idx) => `
                            <div class="bg-bg-panel p-3.5 rounded-xl border border-border-subtle text-xs text-slate-300 flex items-start gap-2.5">
                                <span class="w-5 h-5 rounded-full bg-indigo-500/10 text-indigo-400 font-bold flex items-center justify-center shrink-0 mt-0.5">${idx + 1}</span>
                                <span class="leading-relaxed">${q.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        } else if (c) {
            c.innerHTML = '';
        }
    });

    // Coding Data
    store.subscribe('currentCodingQuestion', (q) => {
        const c = document.getElementById('coding-question-container');
        if (c) c.innerHTML = renderChallengeView(q);
        
        // Have to rebind evaluate button
        const submitBtn = document.getElementById('btn-submit-explanation');
        if (submitBtn) {
            submitBtn.onclick = handleCodingSubmit;
        }
    });

    store.subscribe('currentCodingEvaluation', (evalData) => {
        if (!evalData) return;
        const c = document.getElementById('coding-question-container');
        if (c) {
            const temp = document.createElement('div');
            temp.innerHTML = renderEvaluationCard(evalData);
            c.appendChild(temp.firstElementChild);
        }
    });
}

/**
 * Fetch health and update store
 */
async function refreshHealth() {
    try {
        const res = await api.checkHealth();
        store.set({ healthStatus: res });
    } catch (e) {
        store.set({ healthStatus: null });
    }
}

function rebindStatusEvent() {
    const healthBtn = document.getElementById('status-health-btn');
    if (healthBtn) {
        healthBtn.onclick = () => {
            refreshHealth();
            toast.show('Checking connection...', 'info', 2000);
        };
    }
}

/**
 * Bind DOM events for static elements
 */
function bindDOMEvents() {
    rebindStatusEvent();

    // 1. Interview Start
    const startBtn = document.getElementById('btn-start-interview');
    if (startBtn) {
        startBtn.onclick = async () => {
            startBtn.disabled = true;
            startBtn.textContent = 'Initializing...';
            try {
                const s = store.get();
                const res = await api.createSession(s.settings.candidateName, s.settings.targetRole);
                const sessionId = res.session_id;
                
                store.set({ activeSessionId: sessionId, interviewState: res.state, interviewMessages: [] });
                document.getElementById('transcript-list').innerHTML = ''; // clear transcript
                connectSockets(sessionId);
                
                toast.show(`Session connected. Fusing telemetry.`, 'success');
            } catch (err) {
                toast.show(err.message || 'Could not start session.', 'error');
                startBtn.disabled = false;
                startBtn.innerHTML = `Begin Voice Interview`;
            }
        };
    }

    // 2. Resume Upload
    const fileInput = document.getElementById('resume-file-input');
    const dropZone = document.getElementById('drop-zone');
    const uploadBtn = document.getElementById('upload-submit-btn');
    const clearBtn = document.getElementById('clear-file-btn');
    const errorBox = document.getElementById('upload-error-box');
    
    let selectedFile = null;

    if (fileInput && dropZone) {
        const updateFile = (file) => {
            selectedFile = file;
            const validation = validateResumeFile(file);
            if (!validation.valid) {
                errorBox.textContent = validation.error;
                uploadBtn.disabled = true;
                return;
            }
            errorBox.textContent = '';
            
            document.getElementById('upload-idle-state').classList.add('hidden');
            document.getElementById('upload-file-state').classList.remove('hidden');
            document.getElementById('upload-file-state').style.display = 'flex';
            
            document.getElementById('selected-file-name').textContent = file.name;
            document.getElementById('selected-file-size').textContent = `${(file.size/(1024*1024)).toFixed(2)} MB`;
            
            uploadBtn.disabled = false;
            clearBtn.classList.remove('hidden');
        };

        fileInput.onchange = e => e.target.files[0] && updateFile(e.target.files[0]);
        dropZone.onclick = () => fileInput.click();
        dropZone.ondragover = e => { e.preventDefault(); dropZone.classList.add('dragover'); };
        dropZone.ondragleave = () => dropZone.classList.remove('dragover');
        dropZone.ondrop = e => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files[0]) updateFile(e.dataTransfer.files[0]);
        };

        clearBtn.onclick = (e) => {
            e.stopPropagation();
            selectedFile = null;
            fileInput.value = '';
            document.getElementById('upload-idle-state').classList.remove('hidden');
            document.getElementById('upload-file-state').classList.add('hidden');
            document.getElementById('upload-file-state').style.display = 'none';
            uploadBtn.disabled = true;
            clearBtn.classList.add('hidden');
            errorBox.textContent = '';
        };

        uploadBtn.onclick = async () => {
            if (!selectedFile) return;
            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Extracting...';
            try {
                const profile = await api.uploadResume(selectedFile);
                store.set({ candidateProfile: profile, resumeQuestions: [] });
                
                // Auto generate questions
                const qs = await api.generateResumeQuestions(profile);
                store.set({ resumeQuestions: qs });
                
                toast.show('Profile extracted & calibrated.', 'success');
            } catch (e) {
                toast.show(e.message, 'error');
            } finally {
                uploadBtn.textContent = 'Extract Profile';
                uploadBtn.disabled = false;
            }
        };
    }

    // 3. Coding Generate
    const genCodingBtn = document.getElementById('btn-generate-coding');
    if (genCodingBtn) {
        genCodingBtn.onclick = async () => {
            const topic = document.getElementById('coding-topic').value;
            const diff = document.getElementById('coding-difficulty').value;
            
            genCodingBtn.disabled = true;
            genCodingBtn.textContent = 'Generating...';
            const errorBox = document.getElementById('coding-gen-error');
            errorBox.textContent = '';
            
            try {
                const q = await api.getCodingQuestion(topic, diff, []);
                store.set({ currentCodingQuestion: q, currentCodingEvaluation: null });
                toast.show('Adaptive challenge generated.', 'success');
            } catch (e) {
                errorBox.textContent = e.message;
            } finally {
                genCodingBtn.disabled = false;
                genCodingBtn.textContent = 'Generate Challenge';
            }
        };
    }
}

// Extracted handler for dynamic eval button
async function handleCodingSubmit() {
    const input = document.getElementById('coding-explanation-input');
    const errorBox = document.getElementById('coding-eval-error');
    const btn = document.getElementById('btn-submit-explanation');
    
    if (!input || !btn) return;
    
    const val = validateRequiredString(input.value, 'Explanation');
    if (!val.valid) {
        errorBox.textContent = val.error;
        return;
    }
    errorBox.textContent = '';
    
    btn.disabled = true;
    btn.textContent = 'Evaluating...';
    
    try {
        const ev = await api.evaluateCodingAnswer(store.get().currentCodingQuestion, input.value);
        store.set({ currentCodingEvaluation: ev });
        toast.show('LLM evaluation completed.', 'success');
    } catch (e) {
        errorBox.textContent = e.message;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Evaluate Approach';
    }
}

/**
 * Connect to Interview & Vision WebSockets
 */
function connectSockets(sessionId) {
    disconnectSockets();

    interviewWS = api.connectInterviewSocket(sessionId);
    interviewWS.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'agent_speech') {
                const newMsg = {
                    role: 'assistant',
                    content: data.text,
                    score: data.fused_confidence
                };
                store.set({ interviewState: data.state || STATES.IDLE });
                appendTranscriptMessage(newMsg);
                
                // Update metrics board
                if (data.fused_confidence !== undefined) {
                    document.getElementById('metric-confidence').innerHTML = `${data.fused_confidence.toFixed(1)}<span class="text-sm opacity-50">/100</span>`;
                }
                if (data.difficulty) {
                    document.getElementById('metric-difficulty').textContent = data.difficulty.toUpperCase();
                }
                if (data.round) {
                    document.getElementById('round-indicator').textContent = `ROUND: ${data.round.toUpperCase()}`;
                }
            } else if (data.type === 'agent_state') {
                store.set({ interviewState: data.state });
            } else if (data.type === 'session_end') {
                toast.show('Session terminated by backend.', 'info');
                store.set({ activeSessionId: null, interviewState: STATES.IDLE });
                disconnectSockets();
            }
        } catch (e) {
            console.error('WS Parse error', e);
        }
    };

    visionWS = api.connectVisionSocket(sessionId);
    visionWS.onopen = () => {
        // Send simulated telemetry payload continuously
        let tick = 0;
        visionInterval = setInterval(() => {
            if (visionWS && visionWS.readyState === WebSocket.OPEN) {
                tick += 0.05;
                // Generate sine wave simulated telemetry to make UI look alive
                const eyeVal = 0.8 + (Math.sin(tick) * 0.15);
                const engVal = 0.85 + (Math.cos(tick * 0.8) * 0.1);
                
                store.set({
                    visionMetrics: { eyeContact: eyeVal, engagement: engVal, faceVisible: true }
                });
                
                visionWS.send(JSON.stringify({
                    eye_contact_score: eyeVal,
                    engagement_score: engVal,
                    yaw: 0, pitch: 0, roll: 0,
                    face_visible: true
                }));
            }
        }, 100);
    };
}

function disconnectSockets() {
    if (visionInterval) { clearInterval(visionInterval); visionInterval = null; }
    if (interviewWS) { interviewWS.close(); interviewWS = null; }
    if (visionWS) { visionWS.close(); visionWS = null; }
}

// --- BOOTSTRAP ---
window.addEventListener('DOMContentLoaded', initAppShell);
window.addEventListener('hashchange', renderRoute);
