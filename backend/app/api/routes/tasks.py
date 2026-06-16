"""API routes per task management."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.task_manager import task_manager, TaskStatus, TaskType
from app.core.contact_store import contact_store, Tone

router = APIRouter()


class CreateTaskRequest(BaseModel):
    """Request per creare un task."""
    title: str = Field(..., min_length=1, max_length=200)
    task_type: str = Field(default="note", description="notion, email, outlook, teams, note, widget, reminder")
    contact: str | None = None
    description: str = ""
    priority: int = Field(default=2, ge=1, le=3)
    due_date: str | None = None


class TaskResponse(BaseModel):
    """Response task."""
    id: str
    title: str
    type: str
    contact: str | None
    status: str
    priority: int
    created_at: str


class ListTasksResponse(BaseModel):
    """Response lista task."""
    tasks: list[TaskResponse]
    total: int
    pending: int
    completed: int


class AddContactRequest(BaseModel):
    """Request per aggiungere contatto."""
    name: str = Field(..., min_length=1)
    role: str | None = None
    tone: str = Field(default="semi_formal", description="formal, semi_formal, casual, commercial")
    email: str | None = None
    company: str | None = None
    notes: str = ""


@router.post("/tasks", response_model=TaskResponse)
async def create_task(request: CreateTaskRequest):
    """Crea un nuovo task."""
    task = task_manager.create_task(
        title=request.title,
        task_type=request.task_type,
        contact=request.contact,
        description=request.description,
        priority=request.priority,
        due_date=request.due_date,
    )
    
    # Registra interazione se c'è un contatto
    if request.contact:
        contact_store.record_interaction(request.contact)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        type=task.task_type.value,
        contact=task.contact,
        status=task.status.value,
        priority=task.priority,
        created_at=task.created_at,
    )


@router.get("/tasks", response_model=ListTasksResponse)
async def list_tasks(status: str | None = None, contact: str | None = None):
    """Elenca task con filtri."""
    status_enum = None
    if status:
        try:
            status_enum = TaskStatus(status)
        except ValueError:
            pass
    
    tasks = task_manager.list_tasks(status=status_enum, contact=contact)
    stats = task_manager.get_stats()
    
    return ListTasksResponse(
        tasks=[
            TaskResponse(
                id=t.id,
                title=t.title,
                type=t.task_type.value,
                contact=t.contact,
                status=t.status.value,
                priority=t.priority,
                created_at=t.created_at,
            )
            for t in tasks
        ],
        total=stats["total"],
        pending=stats["pending"],
        completed=stats["completed"],
    )


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    """Segna un task come completato."""
    if task_manager.complete_task(task_id):
        return {"status": "success", "message": f"✅ Task {task_id} completato"}
    return {"status": "error", "message": f"❌ Task {task_id} non trovato"}


@router.get("/tasks/stats")
async def get_task_stats():
    """Statistiche sui task."""
    return task_manager.get_stats()


# Contact management
@router.post("/contacts")
async def add_contact(request: AddContactRequest):
    """Aggiungi un contatto con preferenze di tono."""
    contact = contact_store.add_contact(
        name=request.name,
        role=request.role,
        tone=request.tone,
        email=request.email,
        company=request.company,
        notes=request.notes,
    )
    return {
        "name": contact.name,
        "role": contact.role,
        "tone": contact.tone.value,
        "message": f"✅ Contatto {contact.name} aggiunto con tono {contact.tone.value}",
    }


@router.get("/contacts")
async def list_contacts():
    """Elenca contatti con statistiche."""
    contacts = contact_store.list_contacts()
    return {
        "contacts": [c.to_dict() for c in contacts],
        "stats": contact_store.get_stats(),
    }


@router.get("/contacts/{name}/tone")
async def get_contact_tone(name: str):
    """Recupera il tono suggerito per un contatto."""
    tone = contact_store.get_tone_for_contact(name)
    contact = contact_store.get_contact(name)
    return {
        "name": name,
        "tone": tone.value,
        "found": contact is not None,
        "interactions": contact.interactions_count if contact else 0,
    }
