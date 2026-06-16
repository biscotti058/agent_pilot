"""Modulo A - Gestione Task & To-Do (MVP Fase 2)."""

import re
from typing import Any

from app.modules.base import BaseModule
from app.core.task_manager import TaskManager, TaskType, TaskStatus, task_manager
from app.core.contact_store import ContactStore, contact_store

TASK_KEYWORDS = [
    "task", "to-do", "todo", "aggiungi", "scadenza", "reminder", 
    "attività", "nota", "notion", "email", "outlook", "teams", "widget"
]


class TasksModule(BaseModule):
    """Modulo Task - Crea, lista e gestisce task."""
    
    name = "tasks"
    description = "Gestione task, priorità, reminder e storico con learning"
    phase = 1
    
    def __init__(self):
        self.task_manager = task_manager
        self.contact_store = contact_store
    
    async def can_handle(self, intent: str, context: dict[str, Any]) -> float:
        """Valuta confidenza che questo modulo gestisca la richiesta."""
        text = intent.lower()
        
        # Comandi espliciti
        if text.startswith("/task"):
            return 1.0
        
        # Pattern: "aggiungi a notion...", "email a...", "to-do...", ecc
        if any(f"a {task_type.value}" in text for task_type in TaskType):
            return 0.95
        
        # Keyword matching
        matches = sum(1 for kw in TASK_KEYWORDS if kw in text)
        confidence = min(matches * 0.35, 0.9)
        
        return confidence
    
    async def execute(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Esegui l'azione del task."""
        text = intent.lower()
        
        # Estrai il comando
        if text.startswith("/task"):
            return await self._handle_command(intent, payload)
        
        # Estrai da intent naturale
        return await self._extract_and_create_task(intent, payload)
    
    async def _handle_command(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Gestisci comandi strutturati /task ..."""
        parts = intent.split()
        
        if len(parts) < 2:
            return {"status": "error", "message": "Comando non valido. Usa /task add, /task list, /task done"}
        
        command = parts[1].lower()
        
        if command == "add":
            title = " ".join(parts[2:]) if len(parts) > 2 else "Task senza titolo"
            task = self.task_manager.create_task(
                title=title,
                task_type=TaskType.NOTE,
            )
            return {
                "status": "success",
                "message": f"✅ Task creato: {task.title}",
                "task": task.to_dict(),
            }
        
        elif command == "list":
            tasks = self.task_manager.list_tasks(status=TaskStatus.PENDING)
            return {
                "status": "success",
                "message": f"📋 {len(tasks)} task in sospeso",
                "tasks": [t.to_dict() for t in tasks],
                "stats": self.task_manager.get_stats(),
            }
        
        elif command == "done" and len(parts) > 2:
            task_id = parts[2]
            if self.task_manager.complete_task(task_id):
                return {
                    "status": "success",
                    "message": f"✅ Task completato!",
                }
            else:
                return {
                    "status": "error",
                    "message": f"❌ Task {task_id} non trovato",
                }
        
        return {"status": "error", "message": "Comando non riconosciuto"}
    
    async def _extract_and_create_task(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Estrai tipo, contatto e titolo da un messaggio naturale."""
        text = intent.lower()
        
        # Identifica il tipo di task
        task_type = self._extract_task_type(text)
        
        # Identifica il contatto
        contact_name = self._extract_contact(text, payload)
        if contact_name:
            self.contact_store.record_interaction(contact_name)
        
        # Estrai il titolo (tutto quello che non è keyword)
        title = self._extract_title(intent, task_type, contact_name)
        
        # Crea il task
        task = self.task_manager.create_task(
            title=title or f"Task relativo a {contact_name or task_type.value}",
            task_type=task_type,
            contact=contact_name,
        )
        
        # Suggerisci il tono se c'è un contatto
        tone_suggestion = ""
        if contact_name:
            tone = self.contact_store.get_tone_for_contact(contact_name)
            tone_suggestion = f" (tono suggerito: {tone.value})"
        
        return {
            "status": "success",
            "message": f"✅ Task creato: {task.title}{tone_suggestion}",
            "task": task.to_dict(),
            "contact": contact_name,
            "type": task_type.value,
        }
    
    def _extract_task_type(self, text: str) -> TaskType:
        """Estrai il tipo di task dal testo."""
        for task_type in TaskType:
            if task_type.value in text:
                return task_type
        return TaskType.NOTE
    
    def _extract_contact(self, text: str, payload: dict[str, Any]) -> str | None:
        """Estrai il contatto dal messaggio."""
        # Cerca pattern "a <nome>" o "per <nome>"
        match = re.search(r"(?:a|per|al|da)\s+([a-zA-Z]+)", text)
        if match:
            name = match.group(1)
            contact = self.contact_store.get_contact(name)
            if contact:
                return contact.name
            return name
        
        # Cerca nel context payload
        if "contact" in payload:
            return payload["contact"]
        
        return None
    
    def _extract_title(self, intent: str, task_type: TaskType, contact: str | None) -> str:
        """Estrai il titolo dal messaggio."""
        # Rimuovi prefissi comuni
        text = intent.lower()
        
        prefixes = [
            "aggiungi a", "crea su", "fammi una", "ricordami",
            f"a {contact}" if contact else None,
            task_type.value,
        ]
        
        title = intent
        for prefix in prefixes:
            if prefix and title.lower().startswith(prefix.lower()):
                title = title[len(prefix):].strip()
        
        # Rimuovi il tipo di task dal titolo
        title = re.sub(f"\\b{task_type.value}\\b", "", title, flags=re.IGNORECASE).strip()
        
        return title[:100]  # Max 100 char
    
    def get_commands(self) -> list[str]:
        """Comandi supportati."""
        return [
            "/task add <titolo>",
            "/task list",
            "/task done <id>",
            "aggiungi a notion: <testo>",
            "email a <contatto>: <testo>",
            "ricordami: <testo>",
        ]
