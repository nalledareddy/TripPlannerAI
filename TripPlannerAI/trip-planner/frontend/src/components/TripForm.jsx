import { useState } from "react";
import { Compass, PlaneTakeoff } from "lucide-react";

const defaultForm = {
  user_id: "test",
  source: "Bangalore",
  destination: "Goa",
  budget: 30000,
  days: 5,
  travel_type: "balanced",
  preferences: "beaches, local food, relaxed sightseeing"
};

function TripForm({ onSubmit, loading }) {
  const [formData, setFormData] = useState(defaultForm);

  const updateField = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({
      ...current,
      [name]: value
    }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit({
      user_id: formData.user_id.trim(),
      source: formData.source.trim(),
      destination: formData.destination.trim(),
      budget: Number(formData.budget),
      days: Number(formData.days),
      travel_type: formData.travel_type,
      preferences: formData.preferences
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
    });
  };

  return (
    <div className="card-shell">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-sky-700">Trip Input</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">Plan with multiple AI agents</h2>
        </div>
        <div className="hidden rounded-full border border-sky-100 bg-sky-50 p-3 md:block">
          <Compass className="h-6 w-6 text-sky-700" />
        </div>
      </div>

      <form className="space-y-5" onSubmit={handleSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="user_id">
              User ID
            </label>
            <input
              id="user_id"
              name="user_id"
              className="field-input"
              value={formData.user_id}
              onChange={updateField}
              required
            />
          </div>
          <div>
            <label className="field-label" htmlFor="travel_type">
              Travel Style
            </label>
            <select
              id="travel_type"
              name="travel_type"
              className="field-input"
              value={formData.travel_type}
              onChange={updateField}
            >
              <option value="balanced">Balanced</option>
              <option value="budget">Budget</option>
              <option value="comfort">Comfort</option>
              <option value="adventure">Adventure</option>
            </select>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="source">
              Source
            </label>
            <input
              id="source"
              name="source"
              className="field-input"
              placeholder="Bangalore"
              value={formData.source}
              onChange={updateField}
              required
            />
          </div>
          <div>
            <label className="field-label" htmlFor="destination">
              Destination
            </label>
            <input
              id="destination"
              name="destination"
              className="field-input"
              placeholder="Goa"
              value={formData.destination}
              onChange={updateField}
              required
            />
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="budget">
              Total Budget
            </label>
            <input
              id="budget"
              name="budget"
              type="number"
              min="1"
              className="field-input"
              value={formData.budget}
              onChange={updateField}
              required
            />
          </div>
          <div>
            <label className="field-label" htmlFor="days">
              Trip Days
            </label>
            <input
              id="days"
              name="days"
              type="number"
              min="1"
              max="30"
              className="field-input"
              value={formData.days}
              onChange={updateField}
              required
            />
          </div>
        </div>

        <div>
          <label className="field-label" htmlFor="preferences">
            Preferences
          </label>
          <textarea
            id="preferences"
            name="preferences"
            rows="3"
            className="field-input resize-none"
            placeholder="beaches, local food, slow travel"
            value={formData.preferences}
            onChange={updateField}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-sky-500 to-emerald-400 px-5 py-3 text-base font-semibold text-white transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <PlaneTakeoff className="h-5 w-5" />
          {loading ? "Generating Trip Plan..." : "Generate Trip Plan"}
        </button>
      </form>
    </div>
  );
}

export default TripForm;
