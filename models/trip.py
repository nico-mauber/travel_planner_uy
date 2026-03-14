"""Modelo de viaje."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from config.settings import TripStatus


@dataclass
class Trip:
    id: str
    name: str
    destination: str
    start_date: str  # ISO format YYYY-MM-DD
    end_date: str    # ISO format YYYY-MM-DD
    status: str = TripStatus.PLANNING.value
    budget_total: float = 0.0
    items: list = field(default_factory=list)
    notes: str = ""

    @property
    def start(self) -> date:
        return date.fromisoformat(self.start_date)

    @property
    def end(self) -> date:
        return date.fromisoformat(self.end_date)

    @property
    def duration_days(self) -> int:
        return (self.end - self.start).days + 1

    @property
    def days_until(self) -> int:
        return (self.start - date.today()).days

    @property
    def status_enum(self) -> TripStatus:
        return TripStatus(self.status)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "destination": self.destination,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "budget_total": self.budget_total,
            "items": self.items,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Trip":
        return cls(
            id=data["id"],
            name=data["name"],
            destination=data["destination"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            status=data.get("status", TripStatus.PLANNING.value),
            budget_total=data.get("budget_total", 0.0),
            items=data.get("items", []),
            notes=data.get("notes", ""),
        )
