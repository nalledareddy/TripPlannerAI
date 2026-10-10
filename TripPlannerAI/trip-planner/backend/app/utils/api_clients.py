from __future__ import annotations

import logging
import math
from typing import Any

import requests

from app.config import get_settings


logger = logging.getLogger(__name__)


DEFAULT_GEOCODES: dict[str, dict[str, Any]] = {
    "bangalore": {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946, "country": "IN"},
    "bengaluru": {"name": "Bengaluru", "lat": 12.9716, "lon": 77.5946, "country": "IN"},
    "goa": {"name": "Goa", "lat": 15.2993, "lon": 74.1240, "country": "IN"},
    "mumbai": {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "country": "IN"},
    "delhi": {"name": "Delhi", "lat": 28.6139, "lon": 77.2090, "country": "IN"},
    "hyderabad": {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "country": "IN"},
    "chennai": {"name": "Chennai", "lat": 13.0827, "lon": 80.2707, "country": "IN"},
    "jaipur": {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873, "country": "IN"},
    "paris": {"name": "Paris", "lat": 48.8566, "lon": 2.3522, "country": "FR"},
    "london": {"name": "London", "lat": 51.5072, "lon": -0.1276, "country": "GB"},
    "new york": {"name": "New York", "lat": 40.7128, "lon": -74.0060, "country": "US"},
    "tokyo": {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "country": "JP"},
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def _should_use_api_geocode(
    fallback: dict[str, Any] | None,
    lat: float,
    lon: float,
    country: str,
) -> bool:
    if not fallback:
        return True
    if fallback.get("country") and country and fallback["country"] != country:
        return False
    distance_from_fallback = haversine_km(
        fallback["lat"],
        fallback["lon"],
        lat,
        lon,
    )
    return distance_from_fallback <= 250


class TravelApiClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()

    def _get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        try:
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=self.settings.request_timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.warning("Travel API GET failed for %s: %s", url, exc)
            return {}

    def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> Any:
        try:
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.settings.request_timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.warning("Travel API POST failed for %s: %s", url, exc)
            return {}

    def geocode_location(self, location: str) -> dict[str, Any]:
        cleaned = location.strip()
        fallback = DEFAULT_GEOCODES.get(cleaned.lower())
        if self.settings.openweather_api_key:
            data = self._get_json(
                "https://api.openweathermap.org/geo/1.0/direct",
                params={"q": cleaned, "limit": 1, "appid": self.settings.openweather_api_key},
            )
            if isinstance(data, list) and data:
                first = data[0]
                if "lat" in first and "lon" in first:
                    api_lat = float(first["lat"])
                    api_lon = float(first["lon"])
                    api_country = first.get("country", "")
                    if not _should_use_api_geocode(fallback, api_lat, api_lon, api_country):
                        logger.info(
                            "Ignoring ambiguous geocode for %s from country %s in favor of local fallback.",
                            cleaned,
                            api_country,
                        )
                    else:
                        return {
                            "query": cleaned,
                            "name": first.get("name", cleaned),
                            "lat": api_lat,
                            "lon": api_lon,
                            "country": api_country,
                            "state": first.get("state", ""),
                            "status": "ok",
                            "source": "openweather",
                        }

        if fallback:
            return {
                "query": cleaned,
                "name": fallback["name"],
                "lat": fallback["lat"],
                "lon": fallback["lon"],
                "country": fallback["country"],
                "state": "",
                "status": "fallback",
                "source": "local-defaults",
            }

        return {
            "query": cleaned,
            "name": cleaned.title(),
            "lat": 20.5937,
            "lon": 78.9629,
            "country": "IN",
            "state": "",
            "status": "fallback",
            "source": "country-center",
        }

    def get_weather(self, lat: float, lon: float, location_name: str) -> dict[str, Any]:
        fallback = {
            "status": "fallback",
            "location": location_name,
            "summary": f"Pleasant travel weather is expected around {location_name}.",
            "temperature_c": 28,
            "feels_like_c": 31,
            "humidity": 65,
            "wind_speed_mps": 4.0,
            "condition": "Partly cloudy",
            "forecast": [
                {"label": "Morning", "condition": "Clear", "temperature_c": 27},
                {"label": "Afternoon", "condition": "Warm", "temperature_c": 30},
                {"label": "Evening", "condition": "Breezy", "temperature_c": 26},
            ],
            "advice": "Carry light layers, sunscreen, and a reusable water bottle.",
        }

        if not self.settings.openweather_api_key:
            return fallback

        current = self._get_json(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": lat,
                "lon": lon,
                "appid": self.settings.openweather_api_key,
                "units": "metric",
            },
        )
        forecast = self._get_json(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={
                "lat": lat,
                "lon": lon,
                "appid": self.settings.openweather_api_key,
                "units": "metric",
                "cnt": 3,
            },
        )

        if not isinstance(current, dict) or "main" not in current:
            return fallback

        weather_items = current.get("weather") or [{}]
        condition = weather_items[0].get("main", fallback["condition"])
        detail = weather_items[0].get("description", condition)

        forecast_items = []
        forecast_list = forecast.get("list") if isinstance(forecast, dict) else None
        if isinstance(forecast_list, list):
            for item in forecast_list[:3]:
                details = item.get("weather") or [{}]
                forecast_items.append(
                    {
                        "label": item.get("dt_txt", "Upcoming"),
                        "condition": details[0].get("main", "Clear"),
                        "temperature_c": _round(item.get("main", {}).get("temp", 28), 1),
                    }
                )

        return {
            "status": "ok",
            "location": location_name,
            "summary": f"{detail.capitalize()} with temperatures around {_round(current['main'].get('temp', 28), 1)}C.",
            "temperature_c": _round(current["main"].get("temp", 28), 1),
            "feels_like_c": _round(current["main"].get("feels_like", 31), 1),
            "humidity": int(current["main"].get("humidity", 65)),
            "wind_speed_mps": _round(current.get("wind", {}).get("speed", 4.0), 1),
            "condition": condition,
            "forecast": forecast_items or fallback["forecast"],
            "advice": "Plan outdoor spots earlier in the day if the afternoon turns warm.",
        }

    def build_place_fallback(self, destination: str, lat: float, lon: float) -> list[dict[str, Any]]:
        if "goa" in destination.lower():
            return [
                {
                    "name": "Baga Beach",
                    "kind": "beach",
                    "description": "A lively shoreline with cafes, water sports, and sunset views.",
                    "distance_m": 1800,
                    "lat": 15.5553,
                    "lon": 73.7517,
                },
                {
                    "name": "Fort Aguada",
                    "kind": "history",
                    "description": "A coastal fort known for panoramic Arabian Sea vistas.",
                    "distance_m": 4200,
                    "lat": 15.4936,
                    "lon": 73.7743,
                },
                {
                    "name": "Fontainhas",
                    "kind": "culture",
                    "description": "The colorful Latin Quarter with artful lanes and local cafes.",
                    "distance_m": 5600,
                    "lat": 15.4989,
                    "lon": 73.8278,
                },
                {
                    "name": "Dona Paula Viewpoint",
                    "kind": "viewpoint",
                    "description": "A breezy lookout for sea views and evening walks.",
                    "distance_m": 6900,
                    "lat": 15.4540,
                    "lon": 73.8058,
                },
                {
                    "name": "Anjuna Flea Market",
                    "kind": "market",
                    "description": "A vibrant stop for handicrafts, music, and local street food.",
                    "distance_m": 8700,
                    "lat": 15.5735,
                    "lon": 73.7408,
                },
            ]

        templates = [
            ("Old Town Walk", "culture", "A relaxed walking circuit through heritage lanes and local cafes."),
            ("Central Market", "market", "A good stop for regional snacks, souvenirs, and local color."),
            ("Riverside Promenade", "viewpoint", "An easy sunset walk with photo-friendly viewpoints."),
            ("City Museum", "history", "A compact cultural stop to get grounded in the destination story."),
            ("Signature Park", "nature", "A low-key green pocket for a slower afternoon."),
        ]
        results = []
        for index, (name, kind, description) in enumerate(templates, start=1):
            results.append(
                {
                    "name": f"{destination} {name}",
                    "kind": kind,
                    "description": description,
                    "distance_m": 1200 * index,
                    "lat": lat + (index * 0.01),
                    "lon": lon + (index * 0.01),
                }
            )
        return results

    def get_places(self, lat: float, lon: float, destination: str) -> dict[str, Any]:
        fallback_results = self.build_place_fallback(destination, lat, lon)

        if not self.settings.opentripmap_api_key:
            return {"status": "fallback", "results": fallback_results}

        raw_places = self._get_json(
            "https://api.opentripmap.com/0.1/en/places/radius",
            params={
                "radius": 8000,
                "lon": lon,
                "lat": lat,
                "limit": 5,
                "format": "json",
                "apikey": self.settings.opentripmap_api_key,
            },
        )

        if not isinstance(raw_places, list) or not raw_places:
            return {"status": "fallback", "results": fallback_results}

        results: list[dict[str, Any]] = []
        for item in raw_places:
            name = item.get("name")
            if not name:
                continue
            xid = item.get("xid", "")
            detail = {}
            if xid:
                detail = self._get_json(
                    f"https://api.opentripmap.com/0.1/en/places/xid/{xid}",
                    params={"apikey": self.settings.opentripmap_api_key},
                )
            point = item.get("point") or detail.get("point") or {"lat": lat, "lon": lon}
            wikipedia = detail.get("wikipedia_extracts", {}) if isinstance(detail, dict) else {}
            results.append(
                {
                    "name": name,
                    "kind": (detail.get("kinds") or item.get("kinds") or "attraction")
                    .split(",")[0]
                    .replace("_", " ")
                    .title(),
                    "description": wikipedia.get("text")
                    or detail.get("info", {}).get("descr")
                    or f"A worthwhile stop in {destination}.",
                    "distance_m": int(item.get("dist", 0)),
                    "lat": float(point.get("lat", lat)),
                    "lon": float(point.get("lon", lon)),
                    "xid": xid,
                }
            )
            if len(results) == 5:
                break

        return {"status": "ok" if results else "fallback", "results": results or fallback_results}

    def get_route(self, source: str, destination: str) -> dict[str, Any]:
        source_geo = self.geocode_location(source)
        destination_geo = self.geocode_location(destination)

        fallback_distance = haversine_km(
            source_geo["lat"],
            source_geo["lon"],
            destination_geo["lat"],
            destination_geo["lon"],
        )
        fallback_points = [
            [source_geo["lat"], source_geo["lon"]],
            [destination_geo["lat"], destination_geo["lon"]],
        ]
        fallback = {
            "status": "fallback",
            "route_available": False,
            "mode": "driving",
            "source": source_geo,
            "destination": destination_geo,
            "distance_km": _round(fallback_distance, 1),
            "duration_hours": _round(max(fallback_distance / 45, 1.5), 1),
            "route_points": fallback_points,
            "summary": f"Estimated road journey from {source_geo['name']} to {destination_geo['name']}.",
        }

        if not self.settings.openrouteservice_api_key:
            return fallback

        route = self._post_json(
            "https://api.openrouteservice.org/v2/directions/driving-car/geojson",
            payload={
                "coordinates": [
                    [source_geo["lon"], source_geo["lat"]],
                    [destination_geo["lon"], destination_geo["lat"]],
                ]
            },
            headers={"Authorization": self.settings.openrouteservice_api_key},
        )

        features = route.get("features") if isinstance(route, dict) else None
        if not isinstance(features, list) or not features:
            return fallback

        feature = features[0]
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        segments = properties.get("segments") or []
        summary = segments[0] if segments else properties.get("summary", {})
        coordinates = geometry.get("coordinates") or []
        if not coordinates:
            return fallback

        route_points = [[float(item[1]), float(item[0])] for item in coordinates if len(item) >= 2]
        distance_m = summary.get("distance") or properties.get("summary", {}).get("distance") or 0
        duration_s = summary.get("duration") or properties.get("summary", {}).get("duration") or 0

        return {
            "status": "ok",
            "route_available": True,
            "mode": "driving",
            "source": source_geo,
            "destination": destination_geo,
            "distance_km": _round(distance_m / 1000, 1) if distance_m else fallback["distance_km"],
            "duration_hours": _round(duration_s / 3600, 1) if duration_s else fallback["duration_hours"],
            "route_points": route_points,
            "summary": f"Driving route prepared from {source_geo['name']} to {destination_geo['name']}.",
        }
