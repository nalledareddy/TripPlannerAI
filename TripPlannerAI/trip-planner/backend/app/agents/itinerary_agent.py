from __future__ import annotations

from app.schemas.state import TripState, create_event
from app.utils.llm import get_llm_client


def _fallback_itinerary(state: TripState) -> dict[str, object]:
    request_data = state.get("request", {})
    destination = request_data.get("destination", "your destination")
    days = max(int(request_data.get("days", 1)), 1)
    places = state.get("places_data", {}).get("results") or []
    weather = state.get("weather_data", {})
    hotel_area = state.get("hotel_data", {}).get("recommended_area", "a central neighborhood")
    daily_budget = state.get("budget", {}).get("daily_budget", 0)

    themed_titles = [
        "Arrival and Orientation",
        "Landmarks and Local Flavors",
        "Relaxed Exploration",
        "Scenic Day Out",
        "Free-Flow Highlights",
        "Culture and Shopping",
        "Leisure Finale",
    ]

    plan_days = []
    for day_number in range(1, days + 1):
        morning_place = places[(day_number - 1) % len(places)]["name"] if places else f"{destination} Old Town"
        afternoon_place = places[day_number % len(places)]["name"] if len(places) > 1 else f"{destination} Waterfront"
        evening_place = places[(day_number + 1) % len(places)]["name"] if len(places) > 2 else f"{destination} Cafe Strip"

        plan_days.append(
            {
                "day": day_number,
                "title": themed_titles[(day_number - 1) % len(themed_titles)],
                "morning": f"Start with breakfast in {hotel_area}, then visit {morning_place}.",
                "afternoon": f"Spend the afternoon around {afternoon_place} and keep time for photos or light activities.",
                "evening": f"Wind down at {evening_place} with a relaxed dinner and local walk.",
                "notes": (
                    f"Weather note: {weather.get('summary', 'Expect generally comfortable sightseeing conditions.')} "
                    f"Daily budget target: {daily_budget}."
                ),
            }
        )

    return {
        "status": "ok",
        "overview": f"A {days}-day itinerary for {destination} balancing sightseeing, downtime, and budget control.",
        "days": plan_days,
        "packing_tips": [
            "Carry comfortable walking footwear.",
            "Keep a light rain layer or sun protection based on the forecast.",
            "Reserve one outfit for a nicer evening meal or sunset outing.",
        ],
        "local_tips": [
            "Start high-demand attractions early in the day.",
            "Keep one flexible slot each day in case weather or traffic shifts the plan.",
        ],
    }


def run_itinerary_agent(state: TripState) -> dict[str, object]:
    fallback = _fallback_itinerary(state)
    llm = get_llm_client()
    request_data = state.get("request", {})
    places = state.get("places_data", {}).get("results") or []
    weather = state.get("weather_data", {})
    hotel = state.get("hotel_data", {})
    budget = state.get("budget", {})
    transport = state.get("transport_data", {})

    itinerary_context = {
        "request": {
            "source": request_data.get("source"),
            "destination": request_data.get("destination"),
            "days": request_data.get("days"),
            "budget": request_data.get("budget"),
            "travel_type": request_data.get("travel_type"),
            "preferences": request_data.get("preferences", []),
        },
        "weather_summary": weather.get("summary"),
        "places": [
            {
                "name": place.get("name"),
                "kind": place.get("kind"),
                "description": place.get("description"),
            }
            for place in places[:5]
        ],
        "hotel_area": hotel.get("recommended_area"),
        "hotel_tier": hotel.get("recommended_tier"),
        "daily_budget": budget.get("daily_budget"),
        "budget_tips": budget.get("tips", []),
        "transport_summary": transport.get("summary"),
    }

    system_prompt = (
        "You are a travel itinerary planner. "
        "Return valid JSON only with keys: status, overview, days, packing_tips, local_tips. "
        "Each day must include day, title, morning, afternoon, evening, notes."
    )
    user_prompt = (
        "Create a detailed trip itinerary based on this state.\n"
        f"{itinerary_context}\n"
        "Use concise, realistic plans and keep the number of days equal to the request."
    )

    generated = llm.ask_for_json(system_prompt, user_prompt, fallback)
    itinerary = generated if isinstance(generated, dict) else fallback
    days = itinerary.get("days")
    if not isinstance(days, list) or len(days) != len(fallback["days"]):
        itinerary = fallback

    return {
        "itinerary": itinerary,
        "events": [create_event("itinerary", "Itinerary drafted successfully.")],
    }
