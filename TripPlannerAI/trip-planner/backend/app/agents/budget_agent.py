from __future__ import annotations

from app.config import get_settings
from app.schemas.state import TripState, create_event


def _scaled_amounts(values: dict[str, float], target_total: float) -> dict[str, float]:
    current_total = sum(values.values())
    if current_total <= 0:
        return values
    if current_total <= target_total:
        return values
    scale = target_total / current_total
    return {key: round(value * scale, 2) for key, value in values.items()}


def run_budget_agent(state: TripState) -> dict[str, object]:
    request_data = state.get("request", {})
    total_budget = float(request_data.get("budget", 0))
    days = max(int(request_data.get("days", 1)), 1)
    hotel = state.get("hotel_data", {})
    transport = state.get("transport_data", {})
    places = state.get("places_data", {})

    hotel_total = float(hotel.get("average_nightly_price", max(total_budget * 0.35 / days, 1800))) * days
    transport_cost = float(transport.get("estimated_cost_inr", max(total_budget * 0.15, 2000)))
    food_cost = max(total_budget * 0.18, days * 1100)
    local_transport = max(total_budget * 0.08, days * 450)
    activities = max((len(places.get("results") or []) * 350), total_budget * 0.1)
    contingency = max(total_budget * 0.07, 1200)

    allocations = _scaled_amounts(
        {
            "Hotels": hotel_total,
            "Intercity transport": transport_cost,
            "Food": food_cost,
            "Local transport": local_transport,
            "Activities": activities,
            "Contingency": contingency,
        },
        total_budget,
    )

    planned_total = round(sum(allocations.values()), 2)
    remaining = round(max(total_budget - planned_total, 0), 2)
    daily_budget = round(planned_total / days, 2)
    breakdown = [
        {
            "category": category,
            "amount": round(amount, 2),
            "notes": {
                "Hotels": "Stay near the activity zone to reduce local commute costs.",
                "Intercity transport": "Road-trip estimate with buffer for tolls and breaks.",
                "Food": "Mix two local meals with one premium cafe or restaurant stop per day.",
                "Local transport": "Covers cabs, rentals, or last-mile transfers inside the destination.",
                "Activities": "Entry tickets and one or two paid experiences.",
                "Contingency": "Reserve for weather changes, late check-outs, or surge pricing.",
            }[category],
        }
        for category, amount in allocations.items()
    ]

    return {
        "budget": {
            "status": "ok",
            "currency": get_settings().default_currency,
            "total_budget": total_budget,
            "planned_total": planned_total,
            "remaining": remaining,
            "daily_budget": daily_budget,
            "breakdown": breakdown,
            "tips": [
                "Book transport and stay first, then spread the rest across food and activities.",
                "Keep the contingency untouched until the final day if possible.",
            ],
        },
        "events": [create_event("budget", "Budget breakdown completed.")],
    }
