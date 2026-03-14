"""Modelo de retroalimentación post-viaje."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ItemFeedback:
    item_id: str
    item_name: str
    rating: int = 3  # 1-5
    comment: str = ""

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "item_name": self.item_name,
            "rating": self.rating,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ItemFeedback":
        return cls(
            item_id=data["item_id"],
            item_name=data["item_name"],
            rating=data.get("rating", 3),
            comment=data.get("comment", ""),
        )


@dataclass
class TripFeedback:
    trip_id: str
    overall_rating: int = 3  # 1-5
    comment: str = ""
    item_feedbacks: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "trip_id": self.trip_id,
            "overall_rating": self.overall_rating,
            "comment": self.comment,
            "item_feedbacks": self.item_feedbacks,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TripFeedback":
        return cls(
            trip_id=data["trip_id"],
            overall_rating=data.get("overall_rating", 3),
            comment=data.get("comment", ""),
            item_feedbacks=data.get("item_feedbacks", []),
        )
