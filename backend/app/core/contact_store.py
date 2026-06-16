"""Contact Store - Raccolta contatti con tono e preferenze per learning."""

import json
from pathlib import Path
from typing import Any
from enum import Enum


class Tone(str, Enum):
    """Tonalità di comunicazione."""
    FORMAL = "formal"          # Per manager, clienti importanti
    SEMI_FORMAL = "semi_formal"  # Per colleghi professionali
    CASUAL = "casual"          # Per team interno
    COMMERCIAL = "commercial"   # Per clienti potenziali


class Contact:
    """Modello di un contatto con preferenze."""
    
    def __init__(
        self,
        name: str,
        role: str | None = None,
        tone: Tone = Tone.SEMI_FORMAL,
        email: str | None = None,
        company: str | None = None,
        notes: str = "",
    ):
        self.name = name
        self.role = role  # "manager", "cliente", "collega", ecc
        self.tone = tone
        self.email = email
        self.company = company
        self.notes = notes
        self.interactions_count = 0  # Learning: quante volte interagisco
        self.last_interaction = None
    
    def to_dict(self) -> dict[str, Any]:
        """Converti a dizionario."""
        return {
            "name": self.name,
            "role": self.role,
            "tone": self.tone.value,
            "email": self.email,
            "company": self.company,
            "notes": self.notes,
            "interactions_count": self.interactions_count,
            "last_interaction": self.last_interaction,
        }
    
    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Contact":
        """Crea da dizionario."""
        contact = Contact(
            name=data["name"],
            role=data.get("role"),
            tone=Tone(data.get("tone", "semi_formal")),
            email=data.get("email"),
            company=data.get("company"),
            notes=data.get("notes", ""),
        )
        contact.interactions_count = data.get("interactions_count", 0)
        contact.last_interaction = data.get("last_interaction")
        return contact


class ContactStore:
    """Negozio contatti con persistenza JSON (Passo 2)."""
    
    def __init__(self, storage_path: str = "data/contacts.json"):
        self.storage_path = Path(storage_path)
        self.contacts: dict[str, Contact] = {}
        self.load()
    
    def load(self) -> None:
        """Carica contatti da file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.contacts = {
                        name: Contact.from_dict(contact_data)
                        for name, contact_data in data.items()
                    }
            except (json.JSONDecodeError, IOError):
                self.contacts = {}
        else:
            self.contacts = {}
    
    def save(self) -> None:
        """Salva contatti su file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(
                {name: contact.to_dict() for name, contact in self.contacts.items()},
                f,
                indent=2,
                ensure_ascii=False,
            )
    
    def add_contact(
        self,
        name: str,
        role: str | None = None,
        tone: Tone | str = Tone.SEMI_FORMAL,
        email: str | None = None,
        company: str | None = None,
        notes: str = "",
    ) -> Contact:
        """Aggiungi un contatto."""
        if isinstance(tone, str):
            tone = Tone(tone)
        
        contact = Contact(
            name=name,
            role=role,
            tone=tone,
            email=email,
            company=company,
            notes=notes,
        )
        self.contacts[name.lower()] = contact
        self.save()
        return contact
    
    def get_contact(self, name: str) -> Contact | None:
        """Recupera contatto per nome (case-insensitive)."""
        return self.contacts.get(name.lower())
    
    def record_interaction(self, name: str) -> None:
        """Registra un'interazione con un contatto (per learning)."""
        contact = self.get_contact(name)
        if contact:
            contact.interactions_count += 1
            contact.last_interaction = json.dumps(
                {"timestamp": __import__("datetime").datetime.now().isoformat()}
            )
            self.save()
    
    def list_contacts(self, role: str | None = None) -> list[Contact]:
        """Lista contatti con filtri opzionali."""
        result = list(self.contacts.values())
        if role:
            result = [c for c in result if c.role and role.lower() in c.role.lower()]
        return sorted(result, key=lambda c: -c.interactions_count)
    
    def get_tone_for_contact(self, name: str) -> Tone:
        """Recupera il tono suggerito per un contatto."""
        contact = self.get_contact(name)
        return contact.tone if contact else Tone.SEMI_FORMAL
    
    def infer_contact_from_message(self, message: str) -> Contact | None:
        """Cerca di dedurre il contatto dal messaggio (pattern matching)."""
        message_lower = message.lower()
        
        # Cerco contatti per nome o email
        for contact in self.contacts.values():
            if contact.name.lower() in message_lower:
                return contact
            if contact.email and contact.email.lower() in message_lower:
                return contact
        
        return None
    
    def get_stats(self) -> dict[str, Any]:
        """Statistiche contatti."""
        return {
            "total_contacts": len(self.contacts),
            "by_role": self._count_by_role(),
            "by_tone": self._count_by_tone(),
            "most_active": [
                c.name for c in sorted(
                    self.contacts.values(),
                    key=lambda c: -c.interactions_count
                )[:5]
            ],
        }
    
    def _count_by_role(self) -> dict[str, int]:
        """Conta contatti per ruolo."""
        counts = {}
        for contact in self.contacts.values():
            role = contact.role or "unknown"
            counts[role] = counts.get(role, 0) + 1
        return counts
    
    def _count_by_tone(self) -> dict[str, int]:
        """Conta contatti per tono."""
        counts = {}
        for contact in self.contacts.values():
            tone = contact.tone.value
            counts[tone] = counts.get(tone, 0) + 1
        return counts


# Istanza globale
contact_store = ContactStore()
