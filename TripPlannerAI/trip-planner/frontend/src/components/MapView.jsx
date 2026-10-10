import { useEffect } from "react";
import L from "leaflet";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow
});

const displayText = (value, fallback) => {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value.length ? value.map((item) => String(item)).join(", ") : fallback;
  }

  if (typeof value === "object") {
    const preferred = value.summary || value.message || value.title || value.name || value.status;
    if (typeof preferred === "string" || typeof preferred === "number" || typeof preferred === "boolean") {
      return String(preferred);
    }
    if (Array.isArray(preferred)) {
      return preferred.map((item) => String(item)).join(", ");
    }
    return JSON.stringify(value, null, 2);
  }

  return fallback;
};

function FitBounds({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!points.length) {
      return;
    }
    map.fitBounds(points, { padding: [28, 28] });
  }, [map, points]);

  return null;
}

function MapView({ transport = {}, places = {} }) {
  const routePoints = Array.isArray(transport.route_points) ? transport.route_points : [];
  const center =
    routePoints[0] || (places.center ? [places.center.lat, places.center.lon] : [20.5937, 78.9629]);
  const source = transport.source;
  const destination = transport.destination;
  const hasSourceMarker = source?.lat !== undefined && source?.lon !== undefined;
  const hasDestinationMarker = destination?.lat !== undefined && destination?.lon !== undefined;

  return (
    <div className="card-shell space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-sky-700">Route Map</p>
          <h3 className="section-title">Transport path</h3>
        </div>
        <span className="metric-pill">{displayText(transport.mode, "Driving Route")}</span>
      </div>

      <div className="h-[340px] overflow-hidden rounded-[24px] border border-sky-100">
        <MapContainer center={center} zoom={7} className="h-full w-full" scrollWheelZoom>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {routePoints.length ? (
            <Polyline positions={routePoints} pathOptions={{ color: "#0ea5e9", weight: 5 }} />
          ) : null}
          {routePoints.length ? <FitBounds points={routePoints} /> : null}
          {hasSourceMarker ? (
            <Marker position={[source.lat, source.lon]}>
              <Popup>{displayText(source.name, "Source")}</Popup>
            </Marker>
          ) : null}
          {hasDestinationMarker ? (
            <Marker position={[destination.lat, destination.lon]}>
              <Popup>{displayText(destination.name, "Destination")}</Popup>
            </Marker>
          ) : null}
        </MapContainer>
      </div>

      <p className="text-sm text-slate-600">
        {displayText(transport.summary, "A map preview will appear here when route data is available.")}
      </p>
    </div>
  );
}

export default MapView;
