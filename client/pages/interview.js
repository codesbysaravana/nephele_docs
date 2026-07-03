/**
 * @file interview.js
 * @description Live interview workspace. Fuses real-time speech and vision telemetry.
 */

import { renderNepheleHead, STATES } from '../components/nephele-head.js';
import { renderTranscriptView } from '../components/transcript-view.js';
import { renderVoiceVisualizer } from '../components/voice-visualizer.js';

export function renderInterviewWorkspace(state) {
    const isSessionActive = !!state.activeSessionId;
    
    return `
        <div class="workspace-page" id="page-interview">
            <div class="workspace-header">
                <h2>Live Interview Orchestrator</h2>
                <p>Bi-directional WebSocket loop with real-time speech and vision telemetry fusion.</p>
            </div>
            
            <div class="workspace-scroll flex">
                <!-- Left panel: Nephele & Audio -->
                <div class="flex-1 flex flex-col items-center justify-center p-8 relative min-h-[400px]">
                    <div id="interview-head-container">
                        ${renderNepheleHead(state.interviewState || STATES.IDLE, 'medium')}
                    </div>
                    
                    <div class="absolute bottom-10">
                        ${renderVoiceVisualizer(state.interviewState === STATES.LISTENING)}
                    </div>
                    
                    ${!isSessionActive ? `
                        <div class="absolute inset-0 flex items-center justify-center bg-bg-deep/80 backdrop-blur-sm z-10 fade-up" id="interview-start-overlay">
                            <button class="btn btn-primary px-8 py-3 text-sm" id="btn-start-interview">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 00-3 3v7a3 3 0 006 0V5a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8"/></svg>
                                Begin Voice Interview
                            </button>
                        </div>
                    ` : ''}
                </div>
                
                <!-- Right panel: Context & Transcript -->
                <div class="w-[400px] border-l border-border-subtle bg-bg-panel/30 flex flex-col p-6 gap-6 overflow-hidden relative">
                    <!-- Session Metrics (Top) -->
                    <div class="card p-4 bg-bg-surface/50 border-border-subtle flex gap-4 text-xs font-mono">
                        <div class="flex-1">
                            <div class="text-slate-500 mb-1">FUSED CONFIDENCE</div>
                            <div class="text-2xl text-emerald-400 font-bold" id="metric-confidence">0.0<span class="text-sm text-emerald-500/50">/100</span></div>
                        </div>
                        <div class="w-px bg-border-subtle"></div>
                        <div class="flex-1">
                            <div class="text-slate-500 mb-1">DIFFICULTY</div>
                            <div class="text-sm text-amber-400 font-bold mt-1.5" id="metric-difficulty">MEDIUM</div>
                        </div>
                    </div>
                    
                    <!-- Vision Telemetry (Middle) -->
                    <div class="card p-4 bg-bg-surface/50 border-border-subtle text-xs">
                        <div class="text-slate-500 mb-3 font-mono flex items-center gap-2">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                            VISION TELEMETRY
                            <span class="ml-auto w-2 h-2 rounded-full ${state.visionMetrics?.faceVisible ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-rose-500'}"></span>
                        </div>
                        <div class="grid grid-cols-2 gap-y-3 gap-x-4 font-mono text-[10px]">
                            <div>
                                <div class="text-slate-500 mb-1">EYE CONTACT</div>
                                <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                                    <div class="bg-cyan-400 h-full" style="width: ${state.visionMetrics?.eyeContact || 0}%" id="bar-eye"></div>
                                </div>
                            </div>
                            <div>
                                <div class="text-slate-500 mb-1">ENGAGEMENT</div>
                                <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                                    <div class="bg-indigo-400 h-full" style="width: ${state.visionMetrics?.engagement || 0}%" id="bar-eng"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Live Transcript (Bottom) -->
                    <div class="flex-1 flex flex-col bg-bg-surface border border-border-subtle rounded-xl p-4 overflow-hidden relative">
                        <div class="text-slate-500 mb-3 font-mono text-xs flex justify-between">
                            <span>TRANSCRIPT LOG</span>
                            <span class="text-indigo-400" id="round-indicator">ROUND: HR</span>
                        </div>
                        
                        <div class="flex-1 overflow-hidden flex flex-col">
                            ${renderTranscriptView(state.interviewMessages)}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}
