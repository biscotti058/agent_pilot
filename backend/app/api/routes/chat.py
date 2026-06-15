from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agent.orchestrator import orchestrator

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Input naturale o comando strutturato")
    context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    module: str
    confidence: float | None = None
    result: dict[str, Any]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await orchestrator.route(request.message, request.context)
    return ChatResponse(
        module=result.get("module", "unknown"),
        confidence=result.get("confidence"),
        result=result,
    )


@router.get("/modules")
async def list_modules():
    return {"modules": orchestrator.list_modules()}
