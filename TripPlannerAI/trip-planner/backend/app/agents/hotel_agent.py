from __future__ import annotations

from statistics import mean

from app.schemas.state import TripState, create_event


def _tier_from_budget(per_night_budget: float) -> tuple[str, tuple[int, int]]:
    if per_night_budget < 2200:
        return "smart-budget", (1600, 2200)
    if per_night_budget < 4200:
        return "comfort", (2800, 4200)
    return "premium-comfort", (4500, 7000)


def run_hotel_agent(state: TripState) -> dict[str, object]:
    if not state.get("orchestrator_data", {}).get("run_hotel", True):
        return {
            "hotel_data": {"status": "skipped", "suggestions": []},
            "events": [create_event("hotel", "Hotel agent skipped.", "skipped")],
        }

    request_data = state.get("request", {})
    destination = request_data.get("destination", "Destination")
    budget = float(request_data.get("budget", 0))
    days = max(int(request_data.get("days", 1)), 1)
    travel_type = state.get("orchestrator_data", {}).get("travel_type", "balanced")
    nightly_budget = max((budget * 0.35) / days, 1500)
    tier, price_range = _tier_from_budget(nightly_budget)
    low, high = price_range

    suggestions = [
        {
            "name": f"{destination} Seabreeze Stay",
            "area": "Central hub",
            "estimated_price_per_night": low,
            "rating": 4.2,
            "amenities": ["Wi-Fi", "Breakfast", "AC"],
        },
        {
            "name": f"{destination} Palm Residency",
            "area": "Walkable neighborhood",
            "estimated_price_per_night": int((low + high) / 2),
            "rating": 4.4,
            "amenities": ["Wi-Fi", "Pool", "Airport transfer"],
        },
        {
            "name": f"{destination} Horizon Retreat",
            "area": "Scenic edge",
            "estimated_price_per_night": high,
            "rating": 4.6,
            "amenities": ["Wi-Fi", "Breakfast", "Scenic views"],
        },
    ]

    return {
        "hotel_data": {
            "status": "ok",
            "travel_type": travel_type,
            "recommended_tier": tier,
            "recommended_area": "Near the main attractions with easy evening access",
            "nightly_budget": int(nightly_budget),
            "average_nightly_price": int(mean(item["estimated_price_per_night"] for item in suggestions)),
            "suggestions": suggestions,
        },
        "events": [create_event("hotel", f"Hotel suggestions prepared for {destination}.")],
    }
