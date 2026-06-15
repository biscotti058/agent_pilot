"""Modulo D - Gestione Excel & Dati (MVP Fase 1)."""

from typing import Any

from app.modules.base import BaseModule

EXCEL_KEYWORDS = ["excel", "foglio", "pivot", "csv", "dati", "formula", "grafico", "esporta"]


class ExcelModule(BaseModule):
  name = "excel"
  description = "Compilazione Excel, formule, pivot e export"
  phase = 1

  async def can_handle(self, intent: str, context: dict[str, Any]) -> float:
    text = intent.lower()
    if text.startswith("/excel"):
      return 1.0
    matches = sum(1 for kw in EXCEL_KEYWORDS if kw in text)
    return min(matches * 0.35, 0.9)

  async def execute(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
      "status": "stub",
      "message": "Modulo excel pronto. Prossimo step: upload file + pandas/openpyxl.",
      "intent": intent,
    }

  def get_commands(self) -> list[str]:
    return ["/excel fill", "/excel pivot", "/excel export"]
