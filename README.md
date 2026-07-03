# Nephele AI 

<div align="center">
  <p><strong>A highly-modular, multi-modal AI orchestration interface built for real-time robotic interaction.</strong></p>
</div>

---

## Situation
The goal of Nephele is to create a seamless, low-latency operating interface for an AI robotic assistant. Traditional web interfaces and chatbots lack the real-time telemetry fusing (like continuous computer vision streams) and the instantaneous duplex communication required for a physical or simulated robot.

## Task
Build a complete end-to-end system consisting of:
1. A **high-performance backend orchestrator** capable of managing real-time websocket streams, processing computer vision telemetry, and integrating rapidly with LLMs.
2. A **framework-agnostic Single Page Application (SPA)** that feels like a futuristic robotic control panel, operating entirely without heavy frontend frameworks (no React, Vue, or Webpack).

## Action (Architecture & Implementation)

Nephele is composed of two primary layers, implementing exactly what is required for production-grade interaction:

### 1. The FastAPI Orchestrator (Backend)
Built entirely in Python using FastAPI, providing robust async state management and API routes.
- **WebSocket Streaming**: Full-duplex channels for live voice/text interaction (`/ws/interview`) and real-time edge telemetry ingestion (`/ws/vision`).
- **Cognitive Engine**: Integrates with Groq's high-speed inference APIs (Llama3-8b/70b) to process multi-modal context (vision metrics + conversation history) with near-zero latency.
- **Professional Services Module**:
  - **Resume Analyzer**: Parses PDF documents (`PyMuPDF`) and uses LLMs to extract structured JSON profiles and generate targeted interview questions.
  - **Coding Engine**: Generates adaptive algorithmic challenges and evaluates human responses.

### 2. The Neural Interface (Frontend)
A surgical, dependency-free Vanilla JavaScript SPA driven by a TailwindCSS (CDN) design system.
- **State Management**: Uses a custom, lightweight reactive store (`state.js`) to surgically update DOM nodes without virtual DOM diffing.
- **3D Telemetry**: Integrates `Three.js` for a live, interactive 3D robot head that visually responds to user engagement.
- **Routing**: Client-side hash-based router that avoids page reloads and instantly toggles workspace visibility.

## Result (Current State)
The system is fully operational as a foundation. It successfully ingests simulated vision telemetry, orchestrates live mock interviews via LLMs, parses resumes, evaluates coding challenges, and renders a stunning UI layout.

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js (Optional, for serving frontend if you don't use Python's HTTP server)
- A Groq API Key

### Installation

**1. Clone the repository and setup the Backend Environment**
```bash
# Navigate to the project root
cd nephele

# Create and activate a virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows

# Install Python dependencies
pip install -r requirements.txt
```

**2. Configure Environment Variables**
Create a `.env` file in the root directory and add your Groq API key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### Running the Application

Nephele requires both the backend and frontend servers to be running simultaneously.

**1. Start the FastAPI Backend**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*The backend API will be available at `http://localhost:8000`*

**2. Start the Frontend Server**
In a new terminal window, serve the static `client` directory:
```bash
cd client
python -m http.server 3001
```
*The web interface will be accessible at `http://localhost:3001`*

---

## Core Technologies
- **Python / FastAPI**: Core routing and async logic.
- **Groq API**: High-speed LLM inference.
- **Vanilla JS / ES6 Modules**: Zero-build frontend architecture.
- **TailwindCSS**: Utility-first CSS styling (CDN implementation).
- **Three.js**: 3D rendering engine.
- **WebSockets**: Bi-directional real-time communication.
