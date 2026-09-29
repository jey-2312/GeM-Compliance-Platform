"""FastAPI application entry point for the GeM compliance prototype."""

from __future__ import annotations

import os
from typing import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.api import routes
from app.api.state import AppState, build_default_state


class SimpleRateLimitMiddleware:
    """Small in-memory per-IP limiter for public LLM-costing endpoints."""
    def __init__(self, app, limit: int = 30):
        self.app = app
        self.limit = limit
        self.hits: dict[tuple[str, str], list[float]] = {}

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        protected = path.endswith("/tenders/TND-001/extract") or path.endswith("/tenders/TND-002/extract") or path.endswith("/ai/explain-contradiction") or path.endswith("/ai/draft-clarification")
        if not protected:
            await self.app(scope, receive, send)
            return
        import time
        now = time.monotonic()
        client = scope.get("client") or ("unknown", 0)
        key = (str(client[0]), path)
        recent = [stamp for stamp in self.hits.get(key, []) if now - stamp < 60]
        if len(recent) >= self.limit:
            response = JSONResponse({"detail": "Rate limit exceeded. Try again shortly."}, status_code=429)
            await response(scope, receive, send)
            return
        recent.append(now)
        self.hits[key] = recent
        await self.app(scope, receive, send)


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
    app.add_middleware(SimpleRateLimitMiddleware, limit=int(os.getenv("RATE_LIMIT_PER_MINUTE", "30")))
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
