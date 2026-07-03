/**
 * @file state-indicator.js
 * @description Subtle text + glow showing current AI state.
 * Currently merged into nephele-head.js directly for better component cohesion,
 * but exporting a helper function here for decoupled state text generation if needed.
 */

import { STATES } from './nephele-head.js';

export function getStateDisplayText(state) {
    switch (state) {
        case STATES.IDLE: return '';
        case STATES.LISTENING: return 'Listening...';
        case STATES.THINKING: return 'Processing...';
        case STATES.SPEAKING: return 'Speaking...';
        case STATES.PROCESSING: return 'Analyzing...';
        case STATES.ERROR: return 'Connection lost';
        case STATES.SLEEPING: return '';
        case STATES.GREETING: return 'Hello';
        default: return '';
    }
}
