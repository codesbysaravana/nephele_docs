import { create } from 'zustand'

export const useAppStore = create((set) => ({
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
  },
  
  // Actions
  setHealthStatus: (status) => set({ healthStatus: status }),
  setActiveSessionId: (id) => set({ activeSessionId: id }),
  setInterviewState: (state) => set({ interviewState: state }),
  addInterviewMessage: (msg) => set((state) => ({ 
    interviewMessages: [...state.interviewMessages, msg] 
  })),
  clearInterviewMessages: () => set({ interviewMessages: [] }),
  updateVisionMetrics: (metrics) => set((state) => ({ 
    visionMetrics: { ...state.visionMetrics, ...metrics } 
  })),
  setSettings: (settings) => set((state) => ({
    settings: { ...state.settings, ...settings }
  }))
}))
