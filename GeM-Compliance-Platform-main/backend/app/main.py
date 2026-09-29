"""FastAPI application entry point for the GeM compliance prototype."""

from __future__ import annotations

import os
from typing import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes
from app.api.state import AppState, build_default_state


def create_app(state: AppState | None = None) -> FastAPI:
    """Create the FastAPI application with injectable in-memory state."""

    app_state = state or build_default_state()
    app = FastAPI(
        title="GeM Compliance Platform API",
        version="0.1.0",
        description=(
            "Prototype API for evidence-backed GeM bid compliance verification. "
            "AI interprets unstructured inputs; deterministic backend rules evaluate compliance."
        ),
    )

    origins = [
        value.strip()
        for value in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
        if value.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    dependency: Callable[[], AppState] = lambda: app_state
    # Replace the router dependency function with the application-local state.
    app.dependency_overrides[routes.get_state] = dependency
    app.include_router(routes.router)

    return app


app = create_app()
