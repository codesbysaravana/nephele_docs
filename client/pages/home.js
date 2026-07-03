/**
 * @file home.js
 * @description Nephele-centered idle view.
 */

import { renderNepheleHead, STATES } from '../components/nephele-head.js';
import { ROUTES } from '../utils/constants.js';

export function renderHome() {
    return `
        <div class="workspace-page" id="page-home">
            <div class="flex-1 flex flex-col items-center justify-center p-8 text-center relative z-10 fade-up">
                
                ${renderNepheleHead(STATES.IDLE, 'large')}
                
                <div class="mt-12 space-y-3 max-w-lg">
                    <h1 class="text-3xl font-semibold tracking-tight text-white drop-shadow-md">
                        I am <span class="text-indigo-400">Nephele</span>.
                    </h1>
                    <p class="text-slate-400 text-sm leading-relaxed">
                        Your AI-powered robotic assistant and interview orchestrator.
                        I fuse real-time voice, vision, and language models to evaluate performance dynamically.
                    </p>
                </div>
                
                <div class="mt-10 flex gap-4">
                    <a href="${ROUTES.INTERVIEW}" class="btn btn-primary px-8">
                        Wake Nephele
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                    </a>
                </div>
            </div>
            
            <!-- Ambient background accents -->
            <div class="absolute top-0 left-1/4 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none"></div>
            <div class="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-cyan-500/5 rounded-full blur-[100px] pointer-events-none"></div>
        </div>
    `;
}
