"""Task Manager - Gestione task in memoria e persistenza."""

from datetime import datetime
from typing import Any
from uuid import uuid4
from enum import Enum


class TaskStatus(str, Enum):
    """Stati possibili di un task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Tipi di task supportati."""
    NOTION = "notion"
    EMAIL = "email"
    OUTLOOK = "outlook"
    TEAMS = "teams"
    NOTE = "note"
    WIDGET = "widget"
    REMINDER = "reminder"


class Task:
    """Modello di un singolo task."""
    
    def __init__(
        self,
        title: str,
        task_type: TaskType,
        contact: str | None = None,
        description: str = "",
        due_date: str | None = None,
        priority: int = 2,  # 1=low, 2=medium, 3=high
    ):
        self.id = str(uuid4())[:8]
        self.title = title
        self.task_type = task_type
        self.contact = contact
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now().isoformat()
        self.completed_at: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Converti a dizionario."""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.task_type.value,
            "contact": self.contact,
            "description": self.description,
            "due_date": self.due_date,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }
    
    def mark_complete(self) -> None:
        """Segna il task come completato."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()


class TaskManager:
    """Gestione task in memoria (Passo 2)."""
    
    def __init__(self):
        self.tasks: dict[str, Task] = {}
    
    def create_task(
        self,
        title: str,
        task_type: TaskType | str,
        contact: str | None = None,
        description: str = "",
        due_date: str | None = None,
        priority: int = 2,
    ) -> Task:
        """Crea un nuovo task."""
        if isinstance(task_type, str):
            task_type = TaskType(task_type.lower())
        
        task = Task(
            title=title,
            task_type=task_type,
            contact=contact,
            description=description,
            due_date=due_date,
            priority=priority,
        )
        self.tasks[task.id] = task
        return task
    
    def list_tasks(
        self,
        status: TaskStatus | None = None,
        contact: str | None = None,
        task_type: TaskType | None = None,
    ) -> list[Task]:
        """Lista task con filtri opzionali."""
        result = list(self.tasks.values())
        
        if status:
            result = [t for t in result if t.status == status]
        if contact:
            result = [t for t in result if t.contact and contact.lower() in t.contact.lower()]
        if task_type:
            result = [t for t in result if t.task_type == task_type]
        
        # Ordina per priorità (decrescente) e data creazione
        result.sort(key=lambda t: (-t.priority, t.created_at))
        return result
    
    def get_task(self, task_id: str) -> Task | None:
        """Recupera un task per ID."""
        return self.tasks.get(task_id)
    
    def complete_task(self, task_id: str) -> bool:
        """Segna un task come completato."""
        task = self.tasks.get(task_id)
        if task:
            task.mark_complete()
            return True
        return False
    
    def delete_task(self, task_id: str) -> bool:
        """Elimina un task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
    
    def get_stats(self) -> dict[str, Any]:
        """Statistiche sui task."""
        total = len(self.tasks)
        pending = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        completed = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        
        return {
            "total": total,
            "pending": pending,
            "completed": completed,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
        }


# Istanza globale
task_manager = TaskManager()
