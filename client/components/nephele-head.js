/**
 * @file nephele-head.js
 * @description Animated SVG robot head — the visual identity of Nephele.
 * Supports 8 states: idle, listening, thinking, speaking, processing, error, sleeping, greeting.
 */

const STATES = {
    IDLE: 'idle',
    LISTENING: 'listening',
    THINKING: 'thinking',
    SPEAKING: 'speaking',
    PROCESSING: 'processing',
    ERROR: 'error',
    SLEEPING: 'sleeping',
    GREETING: 'greeting'
};

const STATE_LABELS = {
    idle: '',
    listening: 'Listening',
    thinking: 'Processing',
    speaking: 'Speaking',
    processing: 'Analyzing',
    error: 'Connection lost',
    sleeping: '',
    greeting: 'Hello'
};

/**
 * Render the Nephele robot head SVG with state-driven CSS classes.
 * @param {string} state - One of STATES values
 * @param {string} size - 'large' | 'medium' | 'small'
 * @returns {string} HTML markup
 */
export function renderNepheleHead(state = STATES.IDLE, size = 'large') {
    const glowClass = state === STATES.PROCESSING ? 'thinking' : state;
    const ringClass = state === STATES.PROCESSING ? 'thinking' : state;
    const eyeClass = getEyeClass(state);
    const irisClass = state === STATES.PROCESSING || state === STATES.THINKING ? 'spin' : '';
    const mouthClass = state === STATES.SPEAKING || state === STATES.GREETING ? 'speaking' : '';
    const label = STATE_LABELS[state] || '';

    return `
        <div class="nephele-container size-${size}" id="nephele-container">
            <div class="nephele-head" style="animation: headBreathe 5s ease-in-out infinite">
                <!-- Ambient glow -->
                <div class="nephele-glow ${glowClass}" id="nephele-glow"></div>

                <!-- State ring -->
                <div class="nephele-ring ${ringClass}" id="nephele-ring"></div>

                <!-- Face SVG -->
                <svg class="nephele-face" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg" id="nephele-face" role="img" aria-label="Nephele AI Assistant">
                    <!-- Outer shell -->
                    <circle cx="100" cy="100" r="90" fill="#0f1724" stroke="rgba(99,102,241,0.15)" stroke-width="1.5"/>
                    <circle cx="100" cy="100" r="86" fill="#121c2b" stroke="rgba(255,255,255,0.04)" stroke-width="0.5"/>

                    <!-- Inner face plate -->
                    <ellipse cx="100" cy="96" rx="62" ry="58" fill="#141e30" stroke="rgba(99,102,241,0.08)" stroke-width="0.5"/>

                    <!-- Left eye socket -->
                    <g class="nephele-eye ${eyeClass}" id="nephele-eye-left" style="transform-origin: 72px 88px">
                        <ellipse cx="72" cy="88" rx="18" ry="14" fill="#0a101c" stroke="rgba(99,102,241,0.12)" stroke-width="0.5"/>
                        <!-- Iris -->
                        <g class="nephele-iris ${irisClass}" style="transform-origin: 72px 88px">
                            <circle cx="72" cy="88" r="8" fill="${getIrisColor(state)}"/>
                            <circle cx="72" cy="88" r="3.5" fill="${getPupilColor(state)}"/>
                            <!-- Highlight -->
                            <circle cx="68" cy="85" r="2" fill="rgba(255,255,255,0.5)"/>
                        </g>
                    </g>

                    <!-- Right eye socket -->
                    <g class="nephele-eye ${eyeClass}" id="nephele-eye-right" style="transform-origin: 128px 88px">
                        <ellipse cx="128" cy="88" rx="18" ry="14" fill="#0a101c" stroke="rgba(99,102,241,0.12)" stroke-width="0.5"/>
                        <!-- Iris -->
                        <g class="nephele-iris ${irisClass}" style="transform-origin: 128px 88px">
                            <circle cx="128" cy="88" r="8" fill="${getIrisColor(state)}"/>
                            <circle cx="128" cy="88" r="3.5" fill="${getPupilColor(state)}"/>
                            <!-- Highlight -->
                            <circle cx="124" cy="85" r="2" fill="rgba(255,255,255,0.5)"/>
                        </g>
                    </g>

                    <!-- Nose bridge line -->
                    <line x1="100" y1="82" x2="100" y2="102" stroke="rgba(99,102,241,0.06)" stroke-width="0.5"/>

                    <!-- Mouth -->
                    <g class="nephele-mouth ${mouthClass}" id="nephele-mouth" style="transform-origin: 100px 118px">
                        ${renderMouth(state)}
                    </g>

                    <!-- Antenna dot -->
                    <circle cx="100" cy="10" r="4" fill="${getIrisColor(state)}" opacity="0.6"/>
                    <line x1="100" y1="14" x2="100" y2="22" stroke="${getIrisColor(state)}" stroke-width="1" opacity="0.3"/>

                    <!-- Side vents (decorative) -->
                    <g opacity="0.15">
                        <rect x="18" y="80" width="6" height="2" rx="1" fill="${getIrisColor(state)}"/>
                        <rect x="18" y="86" width="6" height="2" rx="1" fill="${getIrisColor(state)}"/>
                        <rect x="18" y="92" width="6" height="2" rx="1" fill="${getIrisColor(state)}"/>
                        <rect x="176" y="80" width="6" height="2" rx="1" fill="${getIrisColor(state)}"/>
                        <rect x="176" y="86" width="6" height="2" rx="1" fill="${getIrisColor(state)}"/>
                        <rect x="176" y="92" width="6" height="2" rx="1" fill="${getIrisColor(state)}"/>
                    </g>
                </svg>
            </div>

            <!-- State label -->
            <div class="nephele-state-label ${state}" id="nephele-state-label">
                ${label}
            </div>
        </div>
    `;
}

function getEyeClass(state) {
    switch (state) {
        case STATES.IDLE: return 'blink';
        case STATES.LISTENING: return 'wide';
        case STATES.THINKING: return 'half';
        case STATES.SPEAKING: return '';
        case STATES.PROCESSING: return 'half';
        case STATES.ERROR: return '';
        case STATES.SLEEPING: return 'closed';
        case STATES.GREETING: return 'wide';
        default: return 'blink';
    }
}

function getIrisColor(state) {
    switch (state) {
        case STATES.IDLE: return '#6366f1';
        case STATES.LISTENING: return '#22d3ee';
        case STATES.THINKING: return '#a78bfa';
        case STATES.SPEAKING: return '#10b981';
        case STATES.PROCESSING: return '#a78bfa';
        case STATES.ERROR: return '#f43f5e';
        case STATES.SLEEPING: return '#334155';
        case STATES.GREETING: return '#6366f1';
        default: return '#6366f1';
    }
}

function getPupilColor(state) {
    switch (state) {
        case STATES.ERROR: return '#7f1d1d';
        case STATES.SLEEPING: return '#1e293b';
        default: return '#020617';
    }
}

function renderMouth(state) {
    switch (state) {
        case STATES.SPEAKING:
        case STATES.GREETING:
            return `<ellipse cx="100" cy="118" rx="12" ry="6" fill="#0a101c" stroke="${getIrisColor(state)}" stroke-width="0.8" opacity="0.8"/>`;
        case STATES.ERROR:
            return `<line x1="88" y1="120" x2="112" y2="120" stroke="#f43f5e" stroke-width="1.5" stroke-linecap="round" opacity="0.6"/>`;
        case STATES.SLEEPING:
            return `<path d="M90 118 Q100 122 110 118" stroke="#334155" stroke-width="1" fill="none" stroke-linecap="round"/>`;
        default:
            // Neutral slight smile
            return `<path d="M90 116 Q100 122 110 116" stroke="${getIrisColor(state)}" stroke-width="1" fill="none" stroke-linecap="round" opacity="0.5"/>`;
    }
}

/**
 * Update an already-rendered Nephele head to a new state without full re-render.
 * @param {string} newState - Target AI state
 */
export function updateNepheleState(newState) {
    const glow = document.getElementById('nephele-glow');
    const ring = document.getElementById('nephele-ring');
    const eyeL = document.getElementById('nephele-eye-left');
    const eyeR = document.getElementById('nephele-eye-right');
    const mouth = document.getElementById('nephele-mouth');
    const label = document.getElementById('nephele-state-label');

    if (!glow) return; // Head not rendered

    const glowState = newState === 'processing' ? 'thinking' : newState;
    const ringState = newState === 'processing' ? 'thinking' : newState;

    glow.className = `nephele-glow ${glowState}`;
    ring.className = `nephele-ring ${ringState}`;

    if (label) {
        label.className = `nephele-state-label ${newState}`;
        label.textContent = STATE_LABELS[newState] || '';
    }

    const eyeClass = getEyeClass(newState);
    if (eyeL) eyeL.className.baseVal = `nephele-eye ${eyeClass}`;
    if (eyeR) eyeR.className.baseVal = `nephele-eye ${eyeClass}`;

    // Update iris classes
    const irisClass = newState === 'processing' || newState === 'thinking' ? 'spin' : '';
    const irises = document.querySelectorAll('.nephele-iris');
    irises.forEach(iris => { iris.className.baseVal = `nephele-iris ${irisClass}`; });

    // Update mouth
    if (mouth) {
        const mouthClass = newState === 'speaking' || newState === 'greeting' ? 'speaking' : '';
        mouth.className.baseVal = `nephele-mouth ${mouthClass}`;
        mouth.innerHTML = renderMouth(newState);
    }

    // Update iris and antenna colors
    const irisColor = getIrisColor(newState);
    const pupilColor = getPupilColor(newState);
    const circles = document.querySelectorAll('.nephele-iris circle');
    circles.forEach((c, i) => {
        if (i % 3 === 0) c.setAttribute('fill', irisColor);
        if (i % 3 === 1) c.setAttribute('fill', pupilColor);
    });
}

export { STATES };
