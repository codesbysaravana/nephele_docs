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
        <div class="workspace-page w-full h-full p-margin-safe lg:p-lg grid grid-cols-1 lg:grid-cols-12 gap-lg relative" id="page-interview">
            <!-- Left Column: 3D AI Presence (40% - 5 cols) -->
            <div class="col-span-1 lg:col-span-5 flex flex-col items-center justify-center relative min-h-[512px] lg:min-h-0 animate-fade-up-stitch" style="animation-delay: 0.1s;">
                <!-- Ambient Backlight -->
                <div class="absolute inset-0 bg-secondary-fixed/5 rounded-full blur-[100px] pointer-events-none"></div>
                <!-- 3D Scene Container -->
                <div class="relative w-full aspect-square max-w-[400px] mx-auto z-10 flex flex-col items-center justify-center">
                    ${renderNepheleHead(state.interviewState || STATES.IDLE, 'medium')}
                    <div class="absolute bottom-4 z-10 w-full flex justify-center">
                        ${renderVoiceVisualizer(state.interviewState === STATES.LISTENING)}
                    </div>
                </div>
                <!-- Status Capsule -->
                <div class="mt-lg glass-panel px-md py-xs rounded-full flex items-center gap-sm shadow-[0_0_60px_-15px_rgba(173,198,255,0.15)] z-20">
                    <div class="w-2 h-2 rounded-full bg-secondary-container animate-pulse-glow"></div>
                    <span class="font-label-mono text-label-mono text-secondary-fixed tracking-widest uppercase" id="nephele-state-label">${state.interviewState || 'IDLE'}</span>
                </div>
            </div>
            
            <!-- Right Column: Telemetry & Transcript (60% - 7 cols) -->
            <div class="col-span-1 lg:col-span-7 flex flex-col gap-md h-full lg:max-h-[calc(100vh-96px)]">
                <!-- Top Row: Metrics & Vision -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-md flex-shrink-0 animate-fade-up-stitch" style="animation-delay: 0.2s;">
                    <!-- SESSION METRICS Card -->
                    <div class="glass-panel rounded-xl p-md flex flex-col justify-between">
                        <h2 class="font-label-mono text-label-mono text-on-surface-variant uppercase mb-md">SESSION METRICS</h2>
                        <div class="mb-md">
                            <span class="font-label-mono text-[10px] text-on-surface-variant uppercase block mb-xs">Fused Confidence</span>
                            <div class="flex items-baseline gap-xs">
                                <span class="font-display-lg-mobile text-display-lg-mobile lg:font-display-lg lg:text-display-lg text-[#10b981] font-light leading-none tracking-tighter" id="metric-confidence">0.0</span>
                                <span class="font-label-mono text-label-mono text-on-surface-variant">/ 100</span>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-sm">
                            <div class="border-t border-white/5 pt-xs">
                                <span class="font-label-mono text-[10px] text-on-surface-variant uppercase block">Difficulty</span>
                                <span class="font-body-md text-body-md text-amber-400" id="metric-difficulty">MEDIUM</span>
                            </div>
                            <div class="border-t border-white/5 pt-xs">
                                <span class="font-label-mono text-[10px] text-on-surface-variant uppercase block">Round</span>
                                <span class="font-body-md text-body-md text-primary" id="round-indicator">HR</span>
                            </div>
                            <div class="border-t border-white/5 pt-xs">
                                <span class="font-label-mono text-[10px] text-on-surface-variant uppercase block">Quality</span>
                                <span class="font-body-md text-body-md text-primary">HD 1080p</span>
                            </div>
                            <div class="border-t border-white/5 pt-xs">
                                <span class="font-label-mono text-[10px] text-on-surface-variant uppercase block">Latency</span>
                                <span class="font-body-md text-body-md text-primary">42ms</span>
                            </div>
                        </div>
                    </div>
                    <!-- VISION TELEMETRY Card -->
                    <div class="glass-panel rounded-xl p-md flex flex-col">
                        <h2 class="font-label-mono text-label-mono text-on-surface-variant uppercase mb-md">VISION TELEMETRY</h2>
                        <div class="flex items-center gap-sm mb-lg">
                            <div class="w-3 h-3 rounded-full border border-[#10b981]/30 bg-[#10b981]/10 flex items-center justify-center">
                                <div class="w-1.5 h-1.5 rounded-full ${state.visionMetrics?.faceVisible ? 'bg-[#10b981]' : 'bg-rose-500'}" id="vision-face-dot"></div>
                            </div>
                            <span class="font-body-md text-body-md text-primary">Face Visible</span>
                        </div>
                        <div class="space-y-md mt-auto">
                            <!-- Progress 1 -->
                            <div>
                                <div class="flex justify-between items-end mb-xs">
                                    <span class="font-label-mono text-[10px] text-on-surface-variant uppercase">Eye Contact</span>
                                </div>
                                <div class="w-full h-[2px] bg-white/5 rounded-full overflow-hidden relative">
                                    <div class="absolute top-0 left-0 h-full progress-bar-fill transition-all duration-1000" style="width: ${state.visionMetrics?.eyeContact || 0}%" id="bar-eye"></div>
                                </div>
                            </div>
                            <!-- Progress 2 -->
                            <div>
                                <div class="flex justify-between items-end mb-xs">
                                    <span class="font-label-mono text-[10px] text-on-surface-variant uppercase">Engagement</span>
                                </div>
                                <div class="w-full h-[2px] bg-white/5 rounded-full overflow-hidden relative">
                                    <div class="absolute top-0 left-0 h-full progress-bar-fill transition-all duration-1000 delay-300" style="width: ${state.visionMetrics?.engagement || 0}%" id="bar-eng"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Bottom Row: LIVE TRANSCRIPT (Scrollable) -->
                <div class="glass-panel rounded-xl p-md flex-1 flex flex-col min-h-[400px] lg:min-h-0 animate-fade-up-stitch" style="animation-delay: 0.3s;">
                    <div class="flex justify-between items-center mb-md border-b border-white/5 pb-sm flex-shrink-0">
                        <h2 class="font-label-mono text-label-mono text-on-surface-variant uppercase">LIVE TRANSCRIPT</h2>
                        <span class="material-symbols-outlined text-[16px] text-on-surface-variant">more_horiz</span>
                    </div>
                    
                    ${renderTranscriptView(state.interviewMessages)}
                </div>
            </div>
        </div>
    `;
}
