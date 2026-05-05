from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from apollo.router import Router


app = FastAPI(title="Apollo Tool Router", version="0.1.0")
_router: Router | None = None


def _get_router() -> Router:
    global _router
    if _router is None:
        embedding = os.getenv("APOLLO_EMBEDDING", "bge")
        llm = os.getenv("APOLLO_LLM_MODE", "openai")
        _router = Router.for_modes(embedding=embedding, llm=llm)
    return _router


class RouteRequest(BaseModel):
    query: str


class RouteResponse(BaseModel):
    is_instruction: bool
    tool_code: str
    intent: str
    arguments: dict[str, Any]
    missing_required_arguments: list[str]
    confidence: float
    reason: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/route", response_model=RouteResponse)
def route(request: RouteRequest) -> RouteResponse:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")
    result = _get_router().route(request.query)
    return RouteResponse(**result.to_dict())
