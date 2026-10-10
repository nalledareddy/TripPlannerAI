const displayInline = (value, fallback = "Preparing your plan...") => {
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
    const preferred = value.message || value.summary || value.status || value.stage || value.trip_title;
    if (typeof preferred === "string" || typeof preferred === "number" || typeof preferred === "boolean") {
      return String(preferred);
    }
    if (Array.isArray(preferred)) {
      return preferred.map((item) => String(item)).join(", ");
    }
    return fallback;
  }

  return fallback;
};

const humanize = (value) =>
  displayInline(value, "Preparing")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());

function Loader({ stage, events = [] }) {
  const visibleEvents = Array.isArray(events) ? events.slice(-5).reverse() : [];

  return (
    <div className="card-shell space-y-4">
      <div className="flex items-center gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full border border-sky-100 bg-sky-50">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-sky-500 border-t-transparent" />
        </div>
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-sky-700">Live Workflow</p>
          <h3 className="section-title">{humanize(stage)}</h3>
        </div>
      </div>

      <div className="space-y-2">
        {visibleEvents.length ? (
          visibleEvents.map((event, index) => (
            <div
              key={`${displayInline(event?.stage, "system")}-${event?.timestamp ?? index}`}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700"
            >
              <span className="mr-2 font-semibold text-sky-700">{humanize(event?.stage)}</span>
              {displayInline(event?.message)}
            </div>
          ))
        ) : (
          <p className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
            Agent pipeline is warming up and waiting for the first update.
          </p>
        )}
      </div>
    </div>
  );
}

export default Loader;
