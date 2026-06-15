"""Orchestratore centrale: instrada le richieste al modulo giusto."""

from typing import Any

from app.modules.base import BaseModule
from app.modules.tasks import TasksModule
from app.modules.writing import WritingModule
from app.modules.correction import CorrectionModule
from app.modules.excel_handler import ExcelModule
from app.modules.sanitization import SanitizationModule


class Orchestrator:
    """Router intelligente tra i moduli funzionali."""

    def __init__(self) -> None:
        self._modules: list[BaseModule] = [
            TasksModule(),
            WritingModule(),
            CorrectionModule(),
            ExcelModule(),
            SanitizationModule(),
            # Fase 2+: SearchModule(), CommunicationsModule(), SchedulingModule(), ...
        ]

    def list_modules(self) -> list[dict[str, Any]]:
        return [
            {"name": m.name, "description": m.description, "phase": m.phase}
            for m in self._modules
        ]

    async def route(self, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        scores: list[tuple[BaseModule, float]] = []

        for module in self._modules:
            confidence = await module.can_handle(message, context)
            if confidence > 0:
                scores.append((module, confidence))

        if not scores:
            return {
                "module": "general",
                "message": "Non ho identificato un modulo specifico. Prova con /task, /write, /correct, /excel o /sanitize.",
                "available_modules": self.list_modules(),
            }

        best_module, confidence = max(scores, key=lambda x: x[1])
        result = await best_module.execute(message, context)

        return {
            "module": best_module.name,
            "confidence": confidence,
            **result,
        }


orchestrator = Orchestrator()
