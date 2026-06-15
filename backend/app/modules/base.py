"""Contratto base per tutti i moduli funzionali.

Ogni capability (task, writing, excel, ...) implementa BaseModule.
L'orchestratore le registra e le attiva in base all'intent dell'utente.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseModule(ABC):
    """Modulo plug-in: aggiungi una cartella in modules/ e registralo."""

    name: str
    description: str
    phase: int = 1  # 1=MVP, 2=..., 3=...

    @abstractmethod
    async def can_handle(self, intent: str, context: dict[str, Any]) -> float:
        """Ritorna confidence 0.0-1.0 che questo modulo gestisce la richiesta."""

    @abstractmethod
    async def execute(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Esegue l'azione e ritorna il risultato strutturato."""

    @abstractmethod
    def get_commands(self) -> list[str]:
        """Comandi strutturati supportati, es. ['/task add', '/task list']."""
