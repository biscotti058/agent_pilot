"""Modulo A - Gestione Task & To-Do (MVP Fase 1)."""

from typing import Any

from app.modules.base import BaseModule

TASK_KEYWORDS = ["task", "to-do", "todo", "aggiungi", "scadenza", "reminder", "attività"]


class TasksModule(BaseModule):
  name = "tasks"
  description = "Gestione task, priorità, reminder e storico"
  phase = 1

  async def can_handle(self, intent: str, context: dict[str, Any]) -> float:
    text = intent.lower()
    if text.startswith("/task"):
      return 1.0
    matches = sum(1 for kw in TASK_KEYWORDS if kw in text)
    return min(matches * 0.35, 0.9)

  async def execute(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
    # TODO: persistenza su Postgres + reminder via worker
    return {
      "status": "stub",
      "message": "Modulo task pronto. Prossimo step: CRUD su database + widget.",
      "intent": intent,
    }

  def get_commands(self) -> list[str]:
    return ["/task add", "/task list", "/task done", "/task due"]
