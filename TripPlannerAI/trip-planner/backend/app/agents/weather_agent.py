from __future__ import annotations

from app.schemas.state import TripState, create_event
from app.utils.api_clients import TravelApiClient


def run_weather_agent(state: TripState) -> dict[str, object]:
    if not state.get("orchestrator_data", {}).get("run_weather", True):
        return {
            "weather_data": {"status": "skipped", "summary": "Weather agent was skipped by the orchestrator."},
            "events": [create_event("weather", "Weather agent skipped.", "skipped")],
        }

    request_data = state.get("request", {})
    destination = request_data.get("destination", "")
    client = TravelApiClient()

    try:
        destination_geo = client.geocode_location(destination)
        weather = client.get_weather(destination_geo["lat"], destination_geo["lon"], destination_geo["name"])
        weather["coordinates"] = {"lat": destination_geo["lat"], "lon": destination_geo["lon"]}
        weather["location_meta"] = destination_geo
        return {
            "weather_data": weather,
            "events": [create_event("weather", f"Weather prepared for {destination_geo['name']}.")],
        }
    except Exception as exc:
        return {
            "weather_data": {
                "status": "fallback",
                "location": destination,
                "summary": f"Weather fallback used for {destination}.",
                "advice": "Check local conditions shortly before departure.",
            },
            "errors": [f"weather_agent: {exc}"],
            "events": [create_event("weather", "Weather fallback applied.", "warning")],
        }
