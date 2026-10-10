import { useState } from "react";
import { Bot, Sparkles } from "lucide-react";
import { generateTrip, generateTripStream, getApiErrorMessage, normalizeTripData } from "../api";
import Loader from "../components/Loader";
import ResultView from "../components/ResultView";
import TripForm from "../components/TripForm";

const sampleResultState = normalizeTripData({
  request: {
    user_id: "test",
    source: "Bangalore",
    destination: "Goa",
    budget: 30000,
    days: 5
  }
});

function Home() {
  const [tripData, setTripData] = useState(sampleResultState);
  const [activeStage, setActiveStage] = useState("system");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (payload) => {
    setLoading(true);
    setError("");
    setActiveStage("system");
    setTripData(
      normalizeTripData({
        request: payload,
        events: [
          {
            stage: "system",
            message: "Request accepted. Multi-agent workflow is starting."
          }
        ]
      })
    );

    try {
      await generateTripStream(payload, (event) => {
        if (typeof event.stage === "string" && event.stage.trim()) {
          setActiveStage(event.stage);
        }
        if (event.data) {
          setTripData((current) =>
            normalizeTripData({
              ...current,
              ...event.data,
              request: event.data.request ?? current.request,
              events: Array.isArray(event.data.events) && event.data.events.length
                ? event.data.events
                : current.events
            })
          );
        }
        if (event.type === "error") {
          setError(event.message || "Streaming failed while generating the trip plan.");
          setLoading(false);
        }
        if (event.type === "final") {
          setLoading(false);
        }
      });
      setLoading(false);
    } catch (streamError) {
      try {
        const response = await generateTrip(payload);
        setTripData(response.data);
        setActiveStage(response.data?.pdf?.download_url ? "pdf" : "review");
        if (!response.success) {
          setError(response.message);
        } else {
          setError("Streaming fell back to the standard API response.");
        }
      } catch (apiError) {
        setError(getApiErrorMessage(apiError) || getApiErrorMessage(streamError));
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="app-shell min-h-screen px-4 py-8 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="card-shell relative overflow-hidden">
            <div className="absolute inset-x-0 top-0 h-44 bg-gradient-to-r from-sky-300/60 via-emerald-200/55 to-transparent blur-3xl" />
            <div className="relative">
              <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-white/80 px-4 py-2 text-sm text-sky-700">
                <Sparkles className="h-4 w-4" />
                LangGraph Orchestrated Trip Planning
              </div>
              <h1 className="mt-5 max-w-3xl text-4xl font-semibold leading-tight text-slate-900 sm:text-5xl">
                Build a full trip plan with weather, route, budget, hotels, itinerary, and PDF export.
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-7 text-slate-700">
                This workspace coordinates multiple agents behind a single request and streams each
                planning step into the dashboard as it completes.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <span className="metric-pill">FastAPI</span>
                <span className="metric-pill">React + Tailwind</span>
                <span className="metric-pill">LangGraph</span>
                <span className="metric-pill">Live Stream Updates</span>
              </div>
            </div>
          </div>

          <div className="card-shell flex items-center justify-between gap-5">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-sky-700">Agent Status</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">Current stage</h2>
              <p className="mt-3 text-slate-700">
                {loading
                  ? `The workflow is currently running the ${String(activeStage).replace(/_/g, " ")} step.`
                  : "Submit a request to start the multi-agent trip generation flow."}
              </p>
            </div>
            <div className="rounded-[28px] border border-sky-100 bg-gradient-to-br from-sky-100 to-emerald-100 p-5">
              <Bot className="h-12 w-12 text-sky-700" />
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[0.74fr_1.26fr]">
          <div className="space-y-6">
            <TripForm onSubmit={handleSubmit} loading={loading} />
            <Loader stage={activeStage} events={tripData?.events} />
            {error ? (
              <div className="rounded-[28px] border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800">
                {error}
              </div>
            ) : null}
          </div>

          <ResultView data={tripData} />
        </section>
      </div>
    </div>
  );
}

export default Home;
