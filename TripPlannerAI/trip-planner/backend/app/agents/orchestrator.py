from __future__ import annotations

from typing import Any

from app.schemas.state import TripState, create_event
from app.utils.llm import get_llm_client


def _fallback_decision(request_data: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    travel_type = request_data.get("travel_type") or memory.get("travel_type") or "balanced"
    return {
        "run_weather": True,
        "run_places": True,
        "run_transport": bool(request_data.get("source") and request_data.get("destination")),
        "run_hotel": True,
        "travel_type": travel_type,
        "priority": "value-first" if float(request_data.get("budget", 0)) < 20000 else "balanced-comfort",
        "reasoning": "Weather, places, transport, and hotels are all needed for a complete trip plan.",
    }


def _normalize_decision(raw: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    decision = dict(fallback)
    for key in ("run_weather", "run_places", "run_transport", "run_hotel"):
        decision[key] = bool(raw.get(key, fallback[key]))
    decision["travel_type"] = str(raw.get("travel_type", fallback["travel_type"])).strip() or fallback["travel_type"]
    decision["priority"] = str(raw.get("priority", fallback["priority"])).strip() or fallback["priority"]
    decision["reasoning"] = str(raw.get("reasoning", fallback["reasoning"])).strip() or fallback["reasoning"]
    return decision


def run_orchestrator(state: TripState) -> dict[str, Any]:
    request_data = state.get("request", {})
    memory = state.get("memory", {})
    fallback = _fallback_decision(request_data, memory)

    system_prompt = (
        "You are an orchestration planner for a travel application. "
        "Return valid JSON only with keys: run_weather, run_places, run_transport, "
        "run_hotel, travel_type, priority, reasoning."
    )
    user_prompt = (
        "Create an execution plan for this trip request.\n"
        f"Request: {request_data}\n"
        f"Stored preferences: {memory}\n"
        "Keep all required travel-planning agents enabled when possible."
    )

    llm = get_llm_client()
    raw_plan = llm.ask_for_json(system_prompt, user_prompt, fallback)
    decision = _normalize_decision(raw_plan if isinstance(raw_plan, dict) else {}, fallback)

    return {
        "orchestrator_data": decision,
        "events": [
            create_event(
                "orchestrator",
                f"Execution plan ready with travel style '{decision['travel_type']}'.",
            )
        ],
    }
