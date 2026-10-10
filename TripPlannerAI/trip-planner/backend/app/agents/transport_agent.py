from __future__ import annotations

from app.schemas.state import TripState, create_event
from app.utils.api_clients import TravelApiClient


def _estimate_transport_cost(distance_km: float, budget: float) -> int:
    base_cost = 800 + (distance_km * 7.5)
    cap = max(budget * 0.22, 2000)
    return int(min(max(base_cost, 1500), cap))


def run_transport_agent(state: TripState) -> dict[str, object]:
    if not state.get("orchestrator_data", {}).get("run_transport", True):
        return {
            "transport_data": {"status": "skipped", "summary": "Transport agent was skipped by the orchestrator."},
            "events": [create_event("transport", "Transport agent skipped.", "skipped")],
        }

    request_data = state.get("request", {})
    source = request_data.get("source", "")
    destination = request_data.get("destination", "")
    budget = float(request_data.get("budget", 0))
    client = TravelApiClient()

    try:
        route = client.get_route(source, destination)
        route["estimated_cost_inr"] = _estimate_transport_cost(route.get("distance_km", 0), budget)
        route["travel_note"] = (
            "Start early to avoid traffic and keep at least one fuel or meal stop in the plan."
            if route.get("route_available")
            else "Route geometry is approximate because a fallback route was used."
        )
        return {
            "transport_data": route,
            "events": [create_event("transport", f"Transport route prepared from {source} to {destination}.")],
        }
    except Exception as exc:
        return {
            "transport_data": {
                "status": "fallback",
                "summary": f"Fallback transport estimate created from {source} to {destination}.",
                "route_points": [],
                "distance_km": 0,
                "duration_hours": 0,
                "estimated_cost_inr": int(max(budget * 0.15, 2000)),
            },
            "errors": [f"transport_agent: {exc}"],
            "events": [create_event("transport", "Transport fallback applied.", "warning")],
        }
