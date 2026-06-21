"""Main FastAPI application configuration and startup handlers."""

from __future__ import annotations

import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes.interview import router as interview_router
from app.routes.health import router as health_router
from app.routes.observability import router as obs_router, setup_structured_logging
from app.routes.reports import router as reports_router
from app.routes.analytics import router as analytics_router
from app.routes.admin import router as admin_router
from app.routes.security import rate_limiter

# 1. Initialize structured logging
setup_structured_logging()

app = FastAPI(
    title="Nephele Interview Intelligence Platform",
    description="Production technical interview runtime, knowledge graphs, analytics and observability logs.",
    version="1.0.0"
)

# 2. Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Include API Routers
# Enforce rate limiter on all core API routers
app.include_router(interview_router, dependencies=[Depends(rate_limiter)])
app.include_router(reports_router, dependencies=[Depends(rate_limiter)])
app.include_router(analytics_router, dependencies=[Depends(rate_limiter)])
app.include_router(admin_router, dependencies=[Depends(rate_limiter)])
app.include_router(obs_router)
app.include_router(health_router)

# 4. Create directories and mount static files for front-end dashboards
os.makedirs("analytics/dashboard", exist_ok=True)
os.makedirs("admin", exist_ok=True)

app.mount("/analytics", StaticFiles(directory="analytics/dashboard", html=True), name="analytics")
app.mount("/admin", StaticFiles(directory="admin", html=True), name="admin")


@app.get("/")
def redirect_to_admin() -> dict:
    """Index redirect to administration panel status overview."""
    return {
        "message": "Welcome to Nephele. Admin dashboard is available at /admin, Analytics at /analytics.",
        "health": "/api/health"
    }
