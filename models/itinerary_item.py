"""Modelo de item del itinerario."""

from dataclasses import dataclass
from typing import Optional

from config.settings import ItemStatus, ItemType


@dataclass
class ItineraryItem:
    id: str
    trip_id: str
    name: str
    item_type: str  # ItemType value
    day: int  # Día del viaje (1-based)
    start_time: str  # HH:MM
    end_time: str    # HH:MM
    status: str = ItemStatus.PENDING.value
    location: str = ""
    address: str = ""
    notes: str = ""
    cost_estimated: float = 0.0
    cost_real: float = 0.0
    booking_url: str = ""
    provider: str = ""

    @property
    def type_enum(self) -> ItemType:
        return ItemType(self.item_type)

    @property
    def status_enum(self) -> ItemStatus:
        return ItemStatus(self.status)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "name": self.name,
            "item_type": self.item_type,
            "day": self.day,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "location": self.location,
            "address": self.address,
            "notes": self.notes,
            "cost_estimated": self.cost_estimated,
            "cost_real": self.cost_real,
            "booking_url": self.booking_url,
            "provider": self.provider,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ItineraryItem":
        return cls(
            id=data["id"],
            trip_id=data["trip_id"],
            name=data["name"],
            item_type=data["item_type"],
            day=data["day"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            status=data.get("status", ItemStatus.PENDING.value),
            location=data.get("location", ""),
            address=data.get("address", ""),
            notes=data.get("notes", ""),
            cost_estimated=data.get("cost_estimated", 0.0),
            cost_real=data.get("cost_real", 0.0),
            booking_url=data.get("booking_url", ""),
            provider=data.get("provider", ""),
        )
