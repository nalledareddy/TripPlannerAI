from __future__ import annotations

from app.schemas.state import TripState, create_event
from app.utils.api_clients import TravelApiClient


def run_places_agent(state: TripState) -> dict[str, object]:
    if not state.get("orchestrator_data", {}).get("run_places", True):
        return {
            "places_data": {"status": "skipped", "results": []},
            "events": [create_event("places", "Places agent skipped.", "skipped")],
        }

    request_data = state.get("request", {})
    destination = request_data.get("destination", "")
    client = TravelApiClient()

    try:
        destination_geo = client.geocode_location(destination)
        places = client.get_places(destination_geo["lat"], destination_geo["lon"], destination_geo["name"])
        results = places.get("results") or []
        if not results:
            places["status"] = "fallback"
            places["results"] = client.build_place_fallback(
                destination_geo["name"], destination_geo["lat"], destination_geo["lon"]
            )
        places["center"] = {"lat": destination_geo["lat"], "lon": destination_geo["lon"]}
        places["destination"] = destination_geo["name"]
        return {
            "places_data": places,
            "events": [create_event("places", f"Top places shortlisted for {destination_geo['name']}.")],
        }
    except Exception as exc:
        return {
            "places_data": {
                "status": "fallback",
                "destination": destination,
                "results": [],
            },
            "errors": [f"places_agent: {exc}"],
            "events": [create_event("places", "Places fallback applied.", "warning")],
        }
