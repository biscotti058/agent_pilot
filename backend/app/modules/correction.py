"""Modulo C - Correzione & Ottimizzazione (MVP Fase 1)."""

from typing import Any

from app.modules.base import BaseModule

CORRECTION_KEYWORDS = ["correggi", "ortografia", "grammatica", "formale", "semplifica", "migliora", "revisiona"]


class CorrectionModule(BaseModule):
  name = "correction"
  description = "Correzione ortografica, grammaticale e ottimizzazione stile"
  phase = 1

  async def can_handle(self, intent: str, context: dict[str, Any]) -> float:
    text = intent.lower()
    if text.startswith("/correct"):
      return 1.0
    matches = sum(1 for kw in CORRECTION_KEYWORDS if kw in text)
    return min(matches * 0.35, 0.9)

  async def execute(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
      "status": "stub",
      "message": "Modulo correction pronto. Prossimo step: pipeline LLM con diff originale/corretto.",
      "intent": intent,
    }

  def get_commands(self) -> list[str]:
    return ["/correct", "/correct formal", "/correct simplify"]
