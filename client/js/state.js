/**
 * @file state.js
 * @description Centralized, reactive state store using ES6 Modules and EventTarget pattern.
 * Enhanced with granular key-level subscriptions for surgical DOM updates.
 */

class AppStore extends EventTarget {
    constructor() {
        super();
        this._state = {
            activeRoute: '#/',
            healthStatus: null,
            candidateProfile: null,
            resumeQuestions: [],
            currentCodingQuestion: null,
            currentCodingEvaluation: null,
            activeSessionId: null,
            interviewState: 'IDLE', // AI states: IDLE, LISTENING, THINKING, SPEAKING, ERROR
            interviewMessages: [],
            visionMetrics: {
                eyeContact: 0,
                engagement: 0,
                yaw: 0,
                pitch: 0,
                roll: 0,
                faceVisible: false
            },
            settings: {
                candidateName: 'Candidate',
                targetRole: 'Senior Software Engineer'
            }
        };
    }

    /**
     * Get a snapshot of current state.
     * @returns {Object} State copy
     */
    get() {
        return { ...this._state };
    }

    /**
     * Update partial state and notify subscribers.
     * @param {Object} partialState - Partial state update object
     */
    set(partialState) {
        const changedKeys = [];
        for (const [key, value] of Object.entries(partialState)) {
            if (this._state[key] !== value) {
                this._state[key] = value;
                changedKeys.push(key);
            }
        }
        
        if (changedKeys.length > 0) {
            // Notify global subscribers
            this.dispatchEvent(new CustomEvent('stateChange', { detail: this.get() }));
            
            // Notify key-specific subscribers
            changedKeys.forEach(key => {
                this.dispatchEvent(new CustomEvent(`stateChange:${key}`, { detail: this._state[key] }));
            });
        }
    }

    /**
     * Subscribe to state updates.
     * @param {string|Function} arg1 - State key to watch, or global callback
     * @param {Function} [arg2] - Callback if arg1 is key
     * @returns {Function} Unsubscribe function
     */
    subscribe(arg1, arg2) {
        const isKeySub = typeof arg1 === 'string';
        const eventName = isKeySub ? `stateChange:${arg1}` : 'stateChange';
        const callback = isKeySub ? arg2 : arg1;
        
        const handler = (e) => callback(e.detail);
        this.addEventListener(eventName, handler);
        return () => this.removeEventListener(eventName, handler);
    }
}

export const store = new AppStore();
