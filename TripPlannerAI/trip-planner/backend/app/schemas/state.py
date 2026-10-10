from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict

from pydantic import BaseModel, Field, field_validator


def merge_lists(left: list[Any] | None, right: list[Any] | None) -> list[Any]:
    return [*(left or []), *(right or [])]


def create_event(stage: str, message: str, status: str = "ok") -> dict[str, Any]:
    return {
        "stage": stage,
        "message": message,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class TripRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    budget: float = Field(..., gt=0)
    days: int = Field(..., ge=1, le=30)
    travel_type: str = Field(default="balanced")
    preferences: list[str] = Field(default_factory=list)

    @field_validator("user_id", "source", "destination", "travel_type")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("preferences")
    @classmethod
    def normalize_preferences(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()]


class TripResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, Any]


class TripState(TypedDict, total=False):
    request: dict[str, Any]
    memory: dict[str, Any]
    orchestrator_data: dict[str, Any]
    weather_data: dict[str, Any]
    places_data: dict[str, Any]
    transport_data: dict[str, Any]
    hotel_data: dict[str, Any]
    budget: dict[str, Any]
    itinerary: dict[str, Any]
    review: dict[str, Any]
    pdf: dict[str, Any]
    errors: Annotated[list[str], merge_lists]
    events: Annotated[list[dict[str, Any]], merge_lists]
    review_attempts: int


def build_initial_state(request: TripRequest, memory: dict[str, Any] | None = None) -> TripState:
    return TripState(
        request=request.model_dump(),
        memory=memory or {},
        errors=[],
        events=[create_event("system", "Trip generation started.", "running")],
        review_attempts=0,
    )
