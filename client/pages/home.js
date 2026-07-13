/**
 * @file home.js
 * @description Nephele-centered idle view.
 */

import { renderNepheleHead, STATES } from '../components/nephele-head.js';
import { ROUTES } from '../utils/constants.js';

export function renderHome() {
    return `
        <div class="workspace-page h-full w-full flex items-center justify-center p-margin-safe relative" id="page-home">
            <!-- Center Configuration Panel -->
            <div class="glass-panel w-full max-w-[640px] rounded-xl p-md md:p-lg flex flex-col gap-md fade-up-stitch glow-active relative overflow-hidden group">
                <!-- Subtle internal glow -->
                <div class="absolute -top-32 -right-32 w-64 h-64 bg-secondary-container/10 rounded-full blur-[80px] group-hover:bg-secondary-container/20 transition-all duration-700 pointer-events-none"></div>
                <header class="flex flex-col gap-xs mb-sm fade-up-stitch delay-100 relative z-10">
                    <span class="font-label-mono text-label-mono text-on-surface-variant uppercase tracking-widest flex items-center gap-xs">
                        <span class="w-2 h-2 rounded-full bg-secondary-container animate-pulse"></span>
                        INITIALIZATION
                    </span>
                    <h1 class="font-display-lg text-headline-md md:text-[40px] text-primary tracking-tight leading-tight mt-unit">Initialize Interview Session</h1>
                    <p class="font-body-md text-body-md text-on-surface-variant/80 max-w-md mt-unit">Configure operational parameters for the upcoming neural assessment. Precision inputs required.</p>
                </header>
                <form class="flex flex-col gap-sm fade-up-stitch delay-200 relative z-10">
                    <div class="flex flex-col gap-xs group/input">
                        <label class="font-label-mono text-label-mono text-on-surface-variant group-focus-within/input:text-primary transition-colors" for="candidateName">Candidate Name</label>
                        <div class="relative">
                            <span class="material-symbols-outlined absolute left-sm top-1/2 -translate-y-1/2 text-on-surface-variant/50 group-focus-within/input:text-primary transition-colors">person</span>
                            <input class="input-inset w-full rounded p-sm pl-[48px] font-body-md text-body-md text-primary focus:outline-none transition-all placeholder:text-on-surface-variant/30" id="candidateName" placeholder="e.g. Subject Alpha" type="text"/>
                        </div>
                    </div>
                    <div class="flex flex-col gap-xs group/input">
                        <label class="font-label-mono text-label-mono text-on-surface-variant group-focus-within/input:text-primary transition-colors" for="targetRole">Target Role</label>
                        <div class="relative">
                            <span class="material-symbols-outlined absolute left-sm top-1/2 -translate-y-1/2 text-on-surface-variant/50 group-focus-within/input:text-primary transition-colors">work</span>
                            <input class="input-inset w-full rounded p-sm pl-[48px] font-body-md text-body-md text-primary focus:outline-none transition-all placeholder:text-on-surface-variant/30" id="targetRole" placeholder="e.g. Systems Architect" type="text"/>
                        </div>
                    </div>
                    <div class="mt-md fade-up-stitch delay-300">
                        <button id="btn-start-interview" class="w-full bg-primary text-on-primary font-label-mono text-label-mono uppercase tracking-wider py-sm rounded flex items-center justify-center gap-xs hover:bg-white/90 hover:shadow-[0_0_30px_0_rgba(75,142,255,0.3)] transition-all duration-300 active:scale-[0.98]" type="button">
                            <span class="material-symbols-outlined text-[18px]">mic</span>
                            Begin Voice Interview
                        </button>
                    </div>
                </form>
                <!-- Terminal aesthetic footer line -->
                <div class="absolute bottom-sm left-sm right-sm flex justify-between items-center border-t border-white/5 pt-sm fade-up-stitch delay-400">
                    <span class="font-label-mono text-[10px] text-on-surface-variant/50 uppercase">SYS_RDY :: AWAITING_INPUT</span>
                    <span class="font-label-mono text-[10px] text-secondary-container/70 uppercase flex items-center gap-1"><span class="material-symbols-outlined text-[12px]">lock</span> SECURE CHANNEL</span>
                </div>
            </div>

            <!-- Ambient background accents -->
            <div class="absolute top-0 left-1/4 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none"></div>
            <div class="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-cyan-500/5 rounded-full blur-[100px] pointer-events-none"></div>
        </div>
    `;
}
