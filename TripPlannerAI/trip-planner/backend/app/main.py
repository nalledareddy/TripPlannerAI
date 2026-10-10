from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.graph.workflow import run_trip_workflow, stream_trip_workflow
from app.schemas.state import TripRequest, TripResponse, build_initial_state, create_event
from app.utils.memory import get_memory_store


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.frontend_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/generated", StaticFiles(directory=str(settings.generated_dir)), name="generated")


PUBLIC_KEYS = (
    "request",
    "orchestrator_data",
    "weather_data",
    "places_data",
    "transport_data",
    "hotel_data",
    "budget",
    "itinerary",
    "review",
    "pdf",
    "errors",
    "events",
)


def public_state(state: dict[str, Any]) -> dict[str, Any]:
    public = {key: state.get(key) for key in PUBLIC_KEYS if key in state}
    public["orchestrator"] = public.get("orchestrator_data", state.get("orchestrator", {}))
    public["weather"] = public.get("weather_data", state.get("weather", {}))
    public["places"] = public.get("places_data", state.get("places", {}))
    public["transport"] = public.get("transport_data", state.get("transport", {}))
    public["hotel"] = public.get("hotel_data", state.get("hotel", {}))
    return public


def summarized_state_for_logging(state: dict[str, Any]) -> dict[str, Any]:
    summary = public_state(state)
    transport = dict(summary.get("transport_data") or {})
    route_points = transport.get("route_points") or []
    if isinstance(route_points, list):
        transport["route_points_count"] = len(route_points)
        transport["route_points_preview"] = route_points[:5]
        transport.pop("route_points", None)
    summary["transport_data"] = transport
    summary["transport"] = transport
    return summary


def latest_stage(state: dict[str, Any]) -> str:
    events = state.get("events") or []
    if events and isinstance(events[-1], dict):
        return str(events[-1].get("stage", "system"))
    for key in (
        "pdf",
        "review",
        "itinerary",
        "budget",
        "hotel_data",
        "transport_data",
        "places_data",
        "weather_data",
        "orchestrator_data",
    ):
        if state.get(key):
            return key
    return "system"


def build_fallback_response(request_data: TripRequest, error_message: str) -> dict[str, Any]:
    return {
        "request": request_data.model_dump(),
        "review": {
            "status": "approved_with_warnings",
            "message": "Fallback response returned after a workflow error.",
            "warnings": [error_message],
            "retry_issues": [],
            "completeness_score": 50,
        },
        "errors": [error_message],
        "events": [create_event("system", "Fallback response returned.", "warning")],
    }


def prepare_state(request_data: TripRequest) -> dict[str, Any]:
    memory_store = get_memory_store()
    stored_memory = memory_store.load_preferences(request_data.user_id)
    memory_store.save_preferences(
        request_data.user_id,
        {
            "budget": request_data.budget,
            "travel_type": request_data.travel_type,
            "preferences": request_data.preferences,
            "last_destination": request_data.destination,
        },
    )
    return build_initial_state(request_data, stored_memory)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate", response_model=TripResponse)
def generate_trip(request_data: TripRequest) -> TripResponse:
    try:
        final_state = run_trip_workflow(prepare_state(request_data))
        logger.info("Final trip state: %s", json.dumps(summarized_state_for_logging(final_state), default=str))
        return TripResponse(
            success=True,
            message="Trip plan generated successfully.",
            data=public_state(final_state),
        )
    except Exception as exc:
        fallback = build_fallback_response(request_data, str(exc))
        logger.exception("Trip generation failed: %s", exc)
        return TripResponse(
            success=False,
            message="Trip plan returned with fallbacks due to an internal workflow issue.",
            data=fallback,
        )


@app.post("/generate-stream")
def generate_trip_stream(request_data: TripRequest) -> StreamingResponse:
    initial_state = prepare_state(request_data)

    def event_stream():
        try:
            initial_payload = {"type": "update", "stage": "system", "data": public_state(initial_state)}
            yield f"event: update\ndata: {json.dumps(initial_payload)}\n\n"
            last_state: dict[str, Any] = dict(initial_state)
            for state in stream_trip_workflow(initial_state):
                last_state = state
                payload_state = public_state(state)
                if payload_state == initial_payload["data"]:
                    continue
                payload = {
                    "type": "update",
                    "stage": latest_stage(state),
                    "data": payload_state,
                }
                yield f"event: update\ndata: {json.dumps(payload)}\n\n"
            complete_payload = {
                "type": "final",
                "stage": latest_stage(last_state),
                "data": public_state(last_state),
            }
            logger.info(
                "Final streamed trip state: %s",
                json.dumps(summarized_state_for_logging(last_state), default=str),
            )
            yield f"event: final\ndata: {json.dumps(complete_payload)}\n\n"
        except Exception as exc:
            fallback = build_fallback_response(request_data, str(exc))
            logger.exception("Streaming trip generation failed: %s", exc)
            error_payload = {
                "type": "error",
                "stage": "system",
                "data": fallback,
                "message": str(exc),
            }
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
