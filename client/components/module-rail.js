/**
 * @file module-rail.js
 * @description Minimal icon sidebar for workspace navigation.
 */

import { ROUTES } from '../utils/constants.js';
import { store } from '../js/state.js';

export function renderModuleRail(activeRoute) {
    const isHome = activeRoute === ROUTES.HOME;
    const isInterview = activeRoute === ROUTES.INTERVIEW;
    const isResume = activeRoute === ROUTES.RESUME;
    const isCoding = activeRoute === ROUTES.CODING;
    const isSettings = activeRoute === ROUTES.SETTINGS;

    return `
        <aside class="module-rail" aria-label="Module Navigation">
            <div class="rail-logo">N</div>

            <nav class="flex flex-col gap-2">
                <a href="${ROUTES.HOME}" class="rail-icon ${isHome ? 'active' : ''}" title="Home" aria-current="${isHome ? 'page' : 'false'}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                </a>
                
                <a href="${ROUTES.INTERVIEW}" class="rail-icon ${isInterview ? 'active' : ''}" title="Live Interview" aria-current="${isInterview ? 'page' : 'false'}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                </a>

                <a href="${ROUTES.RESUME}" class="rail-icon ${isResume ? 'active' : ''}" title="Resume Intelligence" aria-current="${isResume ? 'page' : 'false'}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                </a>

                <a href="${ROUTES.CODING}" class="rail-icon ${isCoding ? 'active' : ''}" title="Coding Challenge" aria-current="${isCoding ? 'page' : 'false'}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                    </svg>
                </a>
            </nav>

            <div class="rail-spacer"></div>

            <a href="${ROUTES.SETTINGS}" class="rail-icon ${isSettings ? 'active' : ''}" title="Settings" aria-current="${isSettings ? 'page' : 'false'}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
            </a>
        </aside>
    `;
}
