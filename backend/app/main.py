"""WorkFlow Assistant API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.orchestrator import orchestrator
from app.api.routes import chat, health, sanitize
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Agente AI per gestione operativa — task, scrittura, excel, automazioni",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(sanitize.router, prefix="/api/v1", tags=["sanitization"])


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "modules": orchestrator.list_modules(),
        "docs": "/docs",
    }
