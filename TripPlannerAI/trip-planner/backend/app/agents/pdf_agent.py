from __future__ import annotations

from datetime import datetime
from typing import Any

from fpdf import FPDF

from app.config import get_settings
from app.schemas.state import TripState, create_event


def _safe_text(value: Any) -> str:
    return str(value).encode("latin-1", "replace").decode("latin-1")


def _add_section_title(pdf: FPDF, title: str) -> None:
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, _safe_text(title), ln=True)
    pdf.set_font("Helvetica", "", 11)


def run_pdf_agent(state: TripState) -> dict[str, object]:
    settings = get_settings()
    request_data = state.get("request", {})
    filename = f"trip_{request_data.get('user_id', 'guest')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = settings.generated_dir / filename

    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, _safe_text("AI Multi-Agent Trip Planner"), ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(
            0,
            8,
            _safe_text(
                f"{request_data.get('source', '')} to {request_data.get('destination', '')} | {request_data.get('days', 0)} days"
            ),
            ln=True,
        )
        pdf.ln(4)

        weather = state.get("weather_data", {})
        _add_section_title(pdf, "Weather")
        pdf.multi_cell(0, 7, _safe_text(weather.get("summary", "Weather details unavailable.")))
        pdf.multi_cell(0, 7, _safe_text(f"Advice: {weather.get('advice', 'Pack according to the latest local forecast.')}"))
        pdf.ln(2)

        _add_section_title(pdf, "Places to Visit")
        for index, place in enumerate(state.get("places_data", {}).get("results", [])[:5], start=1):
            pdf.multi_cell(
                0,
                7,
                _safe_text(f"{index}. {place.get('name', 'Place')} - {place.get('description', 'Recommended stop')}"),
            )
        pdf.ln(2)

        _add_section_title(pdf, "Hotel Suggestions")
        for hotel in state.get("hotel_data", {}).get("suggestions", []):
            pdf.multi_cell(
                0,
                7,
                _safe_text(
                    f"{hotel.get('name', 'Hotel')} | {hotel.get('area', 'Area')} | INR {hotel.get('estimated_price_per_night', 0)}/night"
                ),
            )
        pdf.ln(2)

        _add_section_title(pdf, "Budget Breakdown")
        budget = state.get("budget", {})
        pdf.multi_cell(
            0,
            7,
            _safe_text(
                f"Total: {budget.get('total_budget', 0)} | Planned: {budget.get('planned_total', 0)} | Remaining: {budget.get('remaining', 0)}"
            ),
        )
        for item in budget.get("breakdown", []):
            pdf.multi_cell(0, 7, _safe_text(f"{item.get('category', '')}: {item.get('amount', 0)}"))
        pdf.ln(2)

        _add_section_title(pdf, "Itinerary")
        for day in state.get("itinerary", {}).get("days", []):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, _safe_text(f"Day {day.get('day', '')}: {day.get('title', '')}"), ln=True)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 7, _safe_text(f"Morning: {day.get('morning', '')}"))
            pdf.multi_cell(0, 7, _safe_text(f"Afternoon: {day.get('afternoon', '')}"))
            pdf.multi_cell(0, 7, _safe_text(f"Evening: {day.get('evening', '')}"))
            pdf.multi_cell(0, 7, _safe_text(f"Notes: {day.get('notes', '')}"))
            pdf.ln(1)

        pdf.output(str(output_path))
        return {
            "pdf": {
                "status": "ok",
                "filename": filename,
                "path": str(output_path),
                "download_url": f"{settings.public_base_url}/generated/{filename}",
            },
            "events": [create_event("pdf", "Trip PDF generated successfully.")],
        }
    except Exception as exc:
        return {
            "pdf": {
                "status": "error",
                "filename": filename,
                "download_url": "",
            },
            "errors": [f"pdf_agent: {exc}"],
            "events": [create_event("pdf", "PDF generation fallback applied.", "warning")],
        }
