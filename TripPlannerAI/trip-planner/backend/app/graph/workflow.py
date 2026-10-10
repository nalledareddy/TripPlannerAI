from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.budget_agent import run_budget_agent
from app.agents.hotel_agent import run_hotel_agent
from app.agents.itinerary_agent import run_itinerary_agent
from app.agents.orchestrator import run_orchestrator
from app.agents.pdf_agent import run_pdf_agent
from app.agents.places_agent import run_places_agent
from app.agents.review_agent import run_review_agent
from app.agents.transport_agent import run_transport_agent
from app.agents.weather_agent import run_weather_agent
from app.schemas.state import TripState


def route_after_review(state: TripState) -> str:
    review = state.get("review", {})
    if review.get("status") == "retry" and int(state.get("review_attempts", 0)) < 2:
        return "itinerary_agent"
    return "pdf_agent"


def _merge_partial_state(base: dict[str, Any], partial: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in partial.items():
        if key in {"errors", "events"}:
            merged[key] = [*(merged.get(key) or []), *(value or [])]
        else:
            merged[key] = value
    return merged


@lru_cache(maxsize=1)
def get_trip_workflow():
    graph = StateGraph(TripState)

    graph.add_node("orchestrator_agent", run_orchestrator)
    graph.add_node("weather_agent", run_weather_agent)
    graph.add_node("places_agent", run_places_agent)
    graph.add_node("transport_agent", run_transport_agent)
    graph.add_node("hotel_agent", run_hotel_agent)
    graph.add_node("budget_agent", run_budget_agent)
    graph.add_node("itinerary_agent", run_itinerary_agent)
    graph.add_node("review_agent", run_review_agent)
    graph.add_node("pdf_agent", run_pdf_agent)

    graph.add_edge(START, "orchestrator_agent")
    graph.add_edge("orchestrator_agent", "weather_agent")
    graph.add_edge("orchestrator_agent", "places_agent")
    graph.add_edge("orchestrator_agent", "transport_agent")
    graph.add_edge("orchestrator_agent", "hotel_agent")

    graph.add_edge("weather_agent", "budget_agent")
    graph.add_edge("places_agent", "budget_agent")
    graph.add_edge("transport_agent", "budget_agent")
    graph.add_edge("hotel_agent", "budget_agent")

    graph.add_edge("budget_agent", "itinerary_agent")
    graph.add_edge("itinerary_agent", "review_agent")
    graph.add_conditional_edges(
        "review_agent",
        route_after_review,
        {
            "itinerary_agent": "itinerary_agent",
            "pdf_agent": "pdf_agent",
        },
    )
    graph.add_edge("pdf_agent", END)

    return graph.compile()


def run_trip_workflow(initial_state: TripState) -> TripState:
    workflow = get_trip_workflow()
    return workflow.invoke(initial_state)


def stream_trip_workflow(initial_state: TripState):
    workflow = get_trip_workflow()
    current_state: dict[str, Any] = dict(initial_state)
    try:
        for state in workflow.stream(initial_state, stream_mode="values"):
            current_state = state
            yield current_state
        return
    except TypeError:
        pass

    for update in workflow.stream(initial_state):
        if isinstance(update, dict):
            for partial in update.values():
                if isinstance(partial, dict):
                    current_state = _merge_partial_state(current_state, partial)
        yield current_state
