from __future__ import annotations

from app.schemas.state import TripState, create_event


def run_review_agent(state: TripState) -> dict[str, object]:
    request_data = state.get("request", {})
    days_requested = int(request_data.get("days", 1))
    itinerary = state.get("itinerary", {})
    attempts = int(state.get("review_attempts", 0))

    retry_issues: list[str] = []
    warnings: list[str] = []
    weather = state.get("weather_data", {})
    places = state.get("places_data", {})
    transport = state.get("transport_data", {})
    hotels = state.get("hotel_data", {})

    if weather.get("status") == "fallback":
        warnings.append("Weather details are using fallback data because the live API was unavailable.")
    if not weather.get("summary"):
        warnings.append("Weather details are using a limited fallback.")
    if places.get("status") == "fallback":
        warnings.append("Places are using fallback recommendations because the live API was unavailable.")
    if not (places.get("results") or []):
        warnings.append("No places were returned, so generic attraction recommendations were used.")
    if transport.get("status") == "fallback":
        warnings.append("Transport guidance is using fallback routing because the live API was unavailable.")
    if not transport.get("summary"):
        warnings.append("Transport guidance is limited.")
    if not (hotels.get("suggestions") or []):
        warnings.append("Hotel suggestions are limited.")
    if not itinerary.get("overview"):
        retry_issues.append("Missing itinerary overview.")
    itinerary_days = itinerary.get("days") or []
    if len(itinerary_days) != days_requested:
        retry_issues.append("Itinerary day count does not match the request.")

    if retry_issues and attempts < 1:
        status = "retry"
        message = "Review requested one itinerary retry to fill missing structure."
        next_attempts = attempts + 1
    elif warnings:
        status = "approved_with_warnings"
        message = "Trip plan approved with fallback warnings."
        next_attempts = attempts
    else:
        status = "approved"
        message = "Trip plan approved."
        next_attempts = attempts

    completeness_score = max(0, 100 - (len(retry_issues) * 20) - (len(warnings) * 5))

    return {
        "review": {
            "status": status,
            "message": message,
            "retry_issues": retry_issues,
            "warnings": warnings,
            "completeness_score": completeness_score,
        },
        "review_attempts": next_attempts,
        "events": [create_event("review", message, "warning" if warnings or retry_issues else "ok")],
    }
