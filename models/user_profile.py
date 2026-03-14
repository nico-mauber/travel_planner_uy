"""Modelo de perfil de usuario."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class UserProfile:
    accommodation_types: List[str] = field(default_factory=list)
    food_restrictions: List[str] = field(default_factory=list)
    allergies: str = ""
    travel_styles: List[str] = field(default_factory=list)
    daily_budget: float = 0.0
    preferred_airlines: str = ""
    preferred_hotel_chains: str = ""

    def to_dict(self) -> dict:
        return {
            "accommodation_types": self.accommodation_types,
            "food_restrictions": self.food_restrictions,
            "allergies": self.allergies,
            "travel_styles": self.travel_styles,
            "daily_budget": self.daily_budget,
            "preferred_airlines": self.preferred_airlines,
            "preferred_hotel_chains": self.preferred_hotel_chains,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        return cls(
            accommodation_types=data.get("accommodation_types", []),
            food_restrictions=data.get("food_restrictions", []),
            allergies=data.get("allergies", ""),
            travel_styles=data.get("travel_styles", []),
            daily_budget=data.get("daily_budget", 0.0),
            preferred_airlines=data.get("preferred_airlines", ""),
            preferred_hotel_chains=data.get("preferred_hotel_chains", ""),
        )
