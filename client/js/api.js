/**
 * @file api.js
 * @description Dedicated API layer interacting with the FastAPI backend.
 */

import { API_BASE_URL, WS_BASE_URL } from '../utils/constants.js';

/**
 * Helper to execute standard HTTP requests with error handling.
 * @param {string} endpoint - API route relative to base URL
 * @param {Object} options - Fetch options
 * @returns {Promise<any>} Parsed JSON response object
 */
async function request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = { ...options.headers };

    // If body is JSON object and not FormData, stringify and add Content-Type
    if (options.body && !(options.body instanceof FormData) && typeof options.body === 'object') {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }

    const config = {
        ...options,
        headers
    };

    try {
        const response = await fetch(url, config);
        
        // Handle non-2xx status codes
        if (!response.ok) {
            let errorMsg = `Server error (${response.status})`;
            try {
                const errData = await response.json();
                if (errData && errData.detail) {
                    errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
                }
            } catch (_) {
                const text = await response.text();
                if (text) errorMsg = text;
            }
            throw new Error(errorMsg);
        }

        return await response.json();
    } catch (error) {
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            throw new Error('Network error: Could not connect to the backend server. Please verify FastAPI is running.');
        }
        throw error;
    }
}

export const api = {
    /**
     * Check backend health status.
     * @returns {Promise<{status: string, active_sessions: number}>}
     */
    async checkHealth() {
        return request('/health');
    },

    /**
     * Create a new interview session.
     * @param {string} candidateName - Name of candidate
     * @param {string} role - Target role
     * @returns {Promise<{session_id: string, state: string}>}
     */
    async createSession(candidateName, role) {
        const params = new URLSearchParams({
            candidate_name: candidateName,
            role: role
        });
        return request(`/api/v1/sessions/create?${params.toString()}`, {
            method: 'POST'
        });
    },

    /**
     * Upload resume file (PDF or DOCX).
     * @param {File} file - Resume document
     * @returns {Promise<Object>} CandidateProfile JSON
     */
    async uploadResume(file) {
        const formData = new FormData();
        formData.append('file', file);
        return request('/api/v1/resume/upload', {
            method: 'POST',
            body: formData
        });
    },

    /**
     * Generate interview questions from candidate profile.
     * @param {Object} candidateProfile - CandidateProfile JSON object
     * @returns {Promise<string[]>} List of 10 interview questions
     */
    async generateResumeQuestions(candidateProfile) {
        return request('/api/v1/resume/questions', {
            method: 'POST',
            body: candidateProfile
        });
    },

    /**
     * Generate a coding question based on topic, difficulty, and skills.
     * @param {string} topic - Topic enum value
     * @param {string} difficulty - Difficulty enum value
     * @param {string[]} skills - List of candidate skills
     * @returns {Promise<Object>} CodingQuestion JSON object
     */
    async getCodingQuestion(topic, difficulty, skills = []) {
        const params = new URLSearchParams();
        if (topic) params.append('topic', topic);
        if (difficulty) params.append('difficulty', difficulty);
        skills.forEach(sk => params.append('skills', sk));
        
        return request(`/api/v1/coding/question?${params.toString()}`);
    },

    /**
     * Evaluate candidate verbal explanation for a coding question.
     * @param {Object} question - CodingQuestion object
     * @param {string} explanation - Candidate verbal explanation
     * @returns {Promise<Object>} CodingEvaluation JSON object
     */
    async evaluateCodingAnswer(question, explanation) {
        return request('/api/v1/coding/evaluate', {
            method: 'POST',
            body: {
                question,
                explanation
            }
        });
    },

    /**
     * Send message to Legacy Chat endpoint.
     * @param {string} message - User query
     * @returns {Promise<{response: string}>}
     */
    async chatLegacy(message) {
        const params = new URLSearchParams({ message });
        return request(`/api/v1/chat/chat?${params.toString()}`);
    },

    /**
     * Create interview WebSocket connection.
     * @param {string} sessionId - Active session ID
     * @returns {WebSocket}
     */
    connectInterviewSocket(sessionId) {
        return new WebSocket(`${WS_BASE_URL}/ws/interview/${sessionId}`);
    },

    /**
     * Create vision metrics WebSocket connection.
     * @param {string} sessionId - Active session ID
     * @returns {WebSocket}
     */
    connectVisionSocket(sessionId) {
        return new WebSocket(`${WS_BASE_URL}/ws/vision/${sessionId}`);
    }
};
