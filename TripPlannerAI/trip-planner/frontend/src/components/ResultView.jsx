import {
  CloudSun,
  Download,
  Hotel,
  IndianRupee,
  ListChecks,
  MapPinned,
  Route
} from "lucide-react";
import MapView from "./MapView";

const formatCurrency = (amount, currency = "INR") => {
  const numeric = Number(amount);
  if (!Number.isFinite(numeric)) {
    return "Budget pending";
  }

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 0
  }).format(numeric);
};

const isPrimitive = (value) =>
  typeof value === "string" || typeof value === "number" || typeof value === "boolean";

const isPlainObject = (value) => Boolean(value) && typeof value === "object" && !Array.isArray(value);

const formatLabel = (value) =>
  String(value)
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());

const toDisplayString = (value, fallback = "No data available") => {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  if (isPrimitive(value)) {
    return String(value);
  }

  if (Array.isArray(value)) {
    if (!value.length) {
      return fallback;
    }

    if (value.every((item) => isPrimitive(item))) {
      return value.map((item) => String(item)).join(", ");
    }

    return `${value.length} item${value.length === 1 ? "" : "s"}`;
  }

  if (isPlainObject(value)) {
    const preferredKeys = [
      "summary",
      "message",
      "title",
      "name",
      "status",
      "trip_title",
      "duration",
      "budget",
      "weather"
    ];

    for (const key of preferredKeys) {
      const candidate = value[key];
      if (candidate !== null && candidate !== undefined && candidate !== "") {
        if (isPrimitive(candidate)) {
          return String(candidate);
        }
        if (Array.isArray(candidate) && candidate.every((item) => isPrimitive(item))) {
          return candidate.map((item) => String(item)).join(", ");
        }
      }
    }

    return JSON.stringify(value, null, 2);
  }

  return fallback;
};

function ValueBlock({ value, emptyText = "No data available", level = 0 }) {
  if (value === null || value === undefined || value === "") {
    return <p className="text-sm text-slate-500">{emptyText}</p>;
  }

  if (isPrimitive(value)) {
    return <p className="text-sm leading-6 text-slate-700">{String(value)}</p>;
  }

  if (Array.isArray(value)) {
    if (!value.length) {
      return <p className="text-sm text-slate-500">{emptyText}</p>;
    }

    if (value.every((item) => isPrimitive(item))) {
      return <p className="text-sm leading-6 text-slate-700">{value.map((item) => String(item)).join(", ")}</p>;
    }

    return (
      <div className="space-y-3">
        {value.map((item, index) => (
          <div
            key={`${level}-${index}`}
            className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3"
          >
            <ValueBlock value={item} emptyText={emptyText} level={level + 1} />
          </div>
        ))}
      </div>
    );
  }

  if (isPlainObject(value)) {
    const entries = Object.entries(value).filter(
      ([, nestedValue]) => nestedValue !== null && nestedValue !== undefined && nestedValue !== ""
    );

    if (!entries.length) {
      return <p className="text-sm text-slate-500">{emptyText}</p>;
    }

    return (
      <div className="space-y-2">
        {entries.map(([key, nestedValue]) => (
          <div
            key={`${level}-${key}`}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm"
          >
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-sky-700">
              {formatLabel(key)}
            </p>
            <div className="mt-2">
              <ValueBlock value={nestedValue} emptyText={emptyText} level={level + 1} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return <p className="text-sm text-slate-500">{emptyText}</p>;
}

function InfoCard({ title, icon: Icon, children, badge }) {
  const hasBadge = badge !== null && badge !== undefined && badge !== "";

  return (
    <div className="card-shell">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl border border-sky-100 bg-sky-50 p-3">
            <Icon className="h-5 w-5 text-sky-700" />
          </div>
          <h3 className="section-title">{toDisplayString(title, "Untitled section")}</h3>
        </div>
        {hasBadge ? <span className="metric-pill">{toDisplayString(badge)}</span> : null}
      </div>
      {children}
    </div>
  );
}

function EmptyState({ message }) {
  return (
    <p className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
      {toDisplayString(message)}
    </p>
  );
}

function ResultView({ data }) {
  if (!data) {
    return null;
  }

  const weather = isPlainObject(data.weather_data) ? data.weather_data : isPlainObject(data.weather) ? data.weather : {};
  const places = isPlainObject(data.places_data) ? data.places_data : isPlainObject(data.places) ? data.places : {};
  const hotels = isPlainObject(data.hotel_data) ? data.hotel_data : isPlainObject(data.hotel) ? data.hotel : {};
  const budget = isPlainObject(data.budget) ? data.budget : {};
  const itinerary = isPlainObject(data.itinerary) ? data.itinerary : {};
  const transport = isPlainObject(data.transport_data)
    ? data.transport_data
    : isPlainObject(data.transport)
      ? data.transport
      : {};
  const review = isPlainObject(data.review) ? data.review : {};
  const pdf = isPlainObject(data.pdf) ? data.pdf : {};
  const errors = Array.isArray(data.errors) ? data.errors : [];
  const currency = typeof budget.currency === "string" ? budget.currency : "INR";

  const totalBudget = budget.total_budget ?? budget.total;
  const plannedBudget = budget.planned_total ?? budget.planned;
  const dailyBudget = budget.daily_budget ?? budget.per_day;

  const budgetBreakdown = Array.isArray(budget.breakdown)
    ? budget.breakdown
    : isPlainObject(budget.breakdown)
      ? Object.entries(budget.breakdown).map(([category, amount]) =>
          isPlainObject(amount) ? { category, ...amount } : { category, amount }
        )
      : [];

  const placeResults = Array.isArray(places.results)
    ? places.results
    : Array.isArray(places.items)
      ? places.items
      : [];

  const hotelSuggestions = Array.isArray(hotels.suggestions)
    ? hotels.suggestions
    : Array.isArray(hotels.options)
      ? hotels.options
      : [];

  const itineraryDays = Array.isArray(itinerary.days) ? itinerary.days : [];
  const reviewWarnings = Array.isArray(review.warnings) ? review.warnings : [];
  const reviewErrors = Array.isArray(review.errors) ? review.errors : [];
  const pdfUrl = pdf.download_url || pdf.url;

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-2">
        <InfoCard title="Weather" icon={CloudSun} badge={weather.status || "pending"}>
          <div className="text-base text-slate-900">
            <ValueBlock
              value={weather.summary ?? weather}
              emptyText="Weather details will appear here once the weather agent completes."
            />
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="metric-pill">
              {weather.temperature_c !== undefined && weather.temperature_c !== null
                ? `${toDisplayString(weather.temperature_c)}C`
                : "Temp pending"}
            </span>
            <span className="metric-pill">
              {weather.humidity !== undefined && weather.humidity !== null
                ? `${toDisplayString(weather.humidity)}% humidity`
                : "Humidity pending"}
            </span>
            <span className="metric-pill">{toDisplayString(weather.condition, "Condition pending")}</span>
          </div>
          <div className="mt-4">
            <ValueBlock value={weather.advice} emptyText="Packing advice will show here." />
          </div>
        </InfoCard>

        <InfoCard title="Budget" icon={IndianRupee} badge={budget.status || "pending"}>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="soft-panel">
              <p className="text-xs uppercase tracking-[0.25em] text-sky-700">Total</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{formatCurrency(totalBudget, currency)}</p>
            </div>
            <div className="soft-panel">
              <p className="text-xs uppercase tracking-[0.25em] text-sky-700">Planned</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{formatCurrency(plannedBudget, currency)}</p>
            </div>
            <div className="soft-panel">
              <p className="text-xs uppercase tracking-[0.25em] text-sky-700">Per Day</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{formatCurrency(dailyBudget, currency)}</p>
            </div>
          </div>
          <div className="mt-4 space-y-3">
            {budgetBreakdown.length ? (
              budgetBreakdown.map((item, index) => {
                const entry = isPlainObject(item) ? item : { category: `Item ${index + 1}`, amount: item };
                return (
                  <div key={`${toDisplayString(entry.category, "item")}-${index}`} className="soft-panel">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium text-slate-900">{toDisplayString(entry.category, `Item ${index + 1}`)}</p>
                      <p className="text-sm text-emerald-700">{formatCurrency(entry.amount, currency)}</p>
                    </div>
                    <div className="mt-2">
                      <ValueBlock value={entry.notes} emptyText="Allocation details will appear here." />
                    </div>
                  </div>
                );
              })
            ) : (
              <EmptyState message="Budget allocation will appear here once the budget agent completes." />
            )}
          </div>
        </InfoCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <InfoCard title="Places" icon={MapPinned} badge={places.status || "pending"}>
          <div className="space-y-3">
            {placeResults.length ? (
              placeResults.map((place, index) => {
                const item = isPlainObject(place) ? place : { name: place };
                return (
                  <div key={`${toDisplayString(item.name, "place")}-${index}`} className="soft-panel">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium text-slate-900">{toDisplayString(item.name, "Recommended stop")}</p>
                      <span className="text-xs uppercase tracking-[0.2em] text-emerald-700">
                        {toDisplayString(item.kind, "Highlight")}
                      </span>
                    </div>
                    <div className="mt-2">
                      <ValueBlock value={item.description ?? item.details} emptyText="Place details will appear here." />
                    </div>
                  </div>
                );
              })
            ) : (
              <ValueBlock
                value={places}
                emptyText="Recommended places will appear here once the places agent completes."
              />
            )}
          </div>
        </InfoCard>

        <InfoCard title="Hotels" icon={Hotel} badge={hotels.recommended_tier || hotels.status || "pending"}>
          <div className="space-y-3">
            {hotelSuggestions.length ? (
              hotelSuggestions.map((hotel, index) => {
                const item = isPlainObject(hotel) ? hotel : { name: hotel };
                return (
                  <div key={`${toDisplayString(item.name, "hotel")}-${index}`} className="soft-panel">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium text-slate-900">{toDisplayString(item.name, "Hotel suggestion")}</p>
                      <p className="text-sm text-emerald-700">
                        {formatCurrency(item.estimated_price_per_night ?? item.nightly_rate, currency)}/night
                      </p>
                    </div>
                    <p className="mt-1 text-sm text-slate-600">{toDisplayString(item.area, "Recommended area")}</p>
                    <p className="mt-2 text-xs text-slate-500">
                      {toDisplayString(item.amenities, "Amenities pending")} | Rating {toDisplayString(item.rating, "N/A")}
                    </p>
                  </div>
                );
              })
            ) : (
              <ValueBlock
                value={hotels}
                emptyText="Hotel suggestions will appear here once the stay agent completes."
              />
            )}
          </div>
        </InfoCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <InfoCard title="Itinerary" icon={ListChecks} badge={review.status || itinerary.status || "draft"}>
          <div className="text-base text-slate-900">
            <ValueBlock
              value={itinerary.overview}
              emptyText="The itinerary agent is still assembling the day-by-day plan."
            />
          </div>
          <div className="mt-4 space-y-4">
            {itineraryDays.length ? (
              itineraryDays.map((dayPlan, index) => {
                const item = isPlainObject(dayPlan) ? dayPlan : { day: index + 1, title: dayPlan };
                return (
                  <div key={`day-${toDisplayString(item.day, index + 1)}-${index}`} className="soft-panel">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-base font-semibold text-slate-900">
                        Day {toDisplayString(item.day, index + 1)}: {toDisplayString(item.title, "Plan")}
                      </p>
                      <span className="metric-pill">Plan</span>
                    </div>
                    <div className="mt-3 space-y-3 text-sm text-slate-600">
                      <div>
                        <span className="font-medium text-slate-900">Morning:</span>
                        <div className="mt-1">
                          <ValueBlock value={item.morning} emptyText="Morning plan pending." />
                        </div>
                      </div>
                      <div>
                        <span className="font-medium text-slate-900">Afternoon:</span>
                        <div className="mt-1">
                          <ValueBlock value={item.afternoon} emptyText="Afternoon plan pending." />
                        </div>
                      </div>
                      <div>
                        <span className="font-medium text-slate-900">Evening:</span>
                        <div className="mt-1">
                          <ValueBlock value={item.evening} emptyText="Evening plan pending." />
                        </div>
                      </div>
                      <div>
                        <span className="font-medium text-slate-900">Notes:</span>
                        <div className="mt-1">
                          <ValueBlock value={item.notes} emptyText="Additional notes will appear here." />
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <ValueBlock
                value={itinerary}
                emptyText="The itinerary will appear here as soon as the itinerary agent returns structured days."
              />
            )}
          </div>
        </InfoCard>

        <div className="space-y-6">
          <InfoCard title="Review Status" icon={Route} badge={`${toDisplayString(review.completeness_score, 0)}%`}>
            <div className="text-slate-900">
              <ValueBlock
                value={review.message ?? review}
                emptyText="Review agent is waiting for itinerary output."
              />
            </div>
            {reviewWarnings.length ? (
              <div className="mt-4 space-y-2">
                {reviewWarnings.map((warning, index) => (
                  <p
                    key={`warning-${index}`}
                    className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
                  >
                    {toDisplayString(warning)}
                  </p>
                ))}
              </div>
            ) : null}
            {reviewErrors.length ? (
              <div className="mt-4 space-y-2">
                {reviewErrors.map((error, index) => (
                  <p
                    key={`review-error-${index}`}
                    className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
                  >
                    {toDisplayString(error)}
                  </p>
                ))}
              </div>
            ) : null}
            {errors.length ? (
              <div className="mt-4 space-y-2">
                {errors.map((error, index) => (
                  <p
                    key={`error-${index}`}
                    className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
                  >
                    {toDisplayString(error)}
                  </p>
                ))}
              </div>
            ) : null}
          </InfoCard>

          <InfoCard title="Download PDF" icon={Download} badge={pdf.status || "pending"}>
            <p className="text-sm text-slate-600">
              The final trip plan is packaged as a PDF once the workflow reaches the export step.
            </p>
            {pdfUrl ? (
              <a
                href={pdfUrl}
                target="_blank"
                rel="noreferrer"
                className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-sky-500 to-emerald-400 px-4 py-3 font-semibold text-white transition hover:brightness-105"
              >
                <Download className="h-4 w-4" />
                Download Trip PDF
              </a>
            ) : (
              <ValueBlock value={pdf} emptyText="The PDF download link will appear here after the PDF agent finishes." />
            )}
          </InfoCard>
        </div>
      </div>

      <MapView transport={transport} places={places} />
    </div>
  );
}

export default ResultView;
