# Nephele — Frontend

<div align="center">
  <p><strong>Landing page and documentation site for the Nephele AI robotic assistant.</strong></p>
</div>

---

## About

This repository contains the **frontend landing page and docs interface** for [Nephele](https://nephele-production.vercel.app/), an intelligent robotic operating system. It is a standalone React application that showcases the project's capabilities, architecture, and provides the entry point for the live production app.

> **Note:** The production backend (FastAPI orchestrator, WebSocket services, LLM integration, etc.) lives in a separate repository and is **not** included here.

---

## Pages

| Route | Description |
|---|---|
| `/` | **Landing Page** — Hero section with interactive 3D robot head (Three.js), capabilities showcase, architecture overview, and footer. |
| `/home` | **Session Initialization** — Configuration panel for setting up an interview session (connects to the production backend). |
| `/interview` | **Live Interview** — Real-time voice interview interface with WebSocket streaming (requires running backend). |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | React 19 + Vite 8 |
| **Styling** | TailwindCSS 3 (PostCSS) |
| **Routing** | React Router v7 |
| **State** | Zustand |
| **Animation** | Framer Motion |
| **3D** | Three.js (custom robot head renderer) |
| **Fonts** | Geist, Inter, JetBrains Mono (Google Fonts) |
| **Icons** | Material Symbols Outlined |

---

## Project Structure

```
frontend/
├── public/               # Static assets (favicon, images)
├── src/
│   ├── api/              # API client (proxied to backend)
│   ├── assets/           # Embedded assets
│   ├── components/
│   │   └── layout/       # AppShell (sidebar + top bar wrapper)
│   ├── pages/
│   │   ├── Landing.jsx   # Marketing landing page
│   │   ├── Home.jsx      # Interview session setup
│   │   └── LiveInterview.jsx  # Real-time interview UI
│   ├── store/            # Zustand state management
│   ├── utils/            # Three.js robot head, audio streamer
│   ├── App.jsx           # Root router
│   ├── main.jsx          # Entry point
│   ├── App.css           # App-level styles
│   └── index.css         # Global styles & design tokens
├── tailwind.config.js    # Custom theme (design system)
├── vite.config.js        # Dev server + backend proxy config
└── package.json
```

---

## Getting Started

### Prerequisites

- **Node.js** 18+

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The dev server starts at `http://localhost:5173`. API and WebSocket calls are proxied to `http://localhost:8000` (the backend) via Vite's built-in proxy.

### Build

```bash
npm run build
npm run preview   # Preview the production build locally
```

### Lint

```bash
npm run lint      # Runs oxlint
```

---

## Deployment

The landing page is deployed at **[nephele-production.vercel.app](https://nephele-production.vercel.app/)**.

---

## License

© 2024 Nephele OS. All rights reserved.
