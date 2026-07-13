const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || `ws://${window.location.host}`;

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = { ...options.headers };

  if (options.body && !(options.body instanceof FormData) && typeof options.body === 'object') {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }

  const config = { ...options, headers };

  try {
    const response = await fetch(url, config);
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
  async checkHealth() {
    return request('/health');
  },
  async createSession(candidateName, role) {
    const params = new URLSearchParams({ candidate_name: candidateName, role });
    return request(`/api/v1/sessions/create?${params.toString()}`, { method: 'POST' });
  },
  async uploadResume(file) {
    const formData = new FormData();
    formData.append('file', file);
    return request('/api/v1/resume/upload', { method: 'POST', body: formData });
  },
  async generateResumeQuestions(candidateProfile) {
    return request('/api/v1/resume/questions', { method: 'POST', body: candidateProfile });
  },
  async getCodingQuestion(topic, difficulty, skills = []) {
    const params = new URLSearchParams();
    if (topic) params.append('topic', topic);
    if (difficulty) params.append('difficulty', difficulty);
    skills.forEach(sk => params.append('skills', sk));
    return request(`/api/v1/coding/question?${params.toString()}`);
  },
  async evaluateCodingAnswer(question, explanation) {
    return request('/api/v1/coding/evaluate', {
      method: 'POST',
      body: { question, explanation }
    });
  },

  connectInterviewSocket(sessionId) {
    return new WebSocket(`${WS_BASE_URL}/ws/interview/${sessionId}`);
  },
  connectVisionSocket(sessionId) {
    return new WebSocket(`${WS_BASE_URL}/ws/vision/${sessionId}`);
  }
};
