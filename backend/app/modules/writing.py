"""Modulo B - Redazione & Scrittura (MVP Fase 1)."""

from typing import Any

from app.modules.base import BaseModule

WRITING_KEYWORDS = ["scrivi", "mail", "email", "messaggio", "slack", "teams", "nota", "memo", "risposta"]


class WritingModule(BaseModule):
  name = "writing"
  description = "Redazione mail, messaggi chat, note e template"
  phase = 1

  async def can_handle(self, intent: str, context: dict[str, Any]) -> float:
    text = intent.lower()
    if text.startswith("/write"):
      return 1.0
    matches = sum(1 for kw in WRITING_KEYWORDS if kw in text)
    return min(matches * 0.35, 0.9)

  async def execute(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
    # TODO: chiamata LLM con template e tono
    return {
      "status": "stub",
      "message": "Modulo writing pronto. Prossimo step: integrazione OpenAI + template.",
      "intent": intent,
    }

  def get_commands(self) -> list[str]:
    return ["/write mail", "/write slack", "/write template"]
