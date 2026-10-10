import axios from "axios";

export const API_BASE_URL = "http://127.0.0.1:8000";

export const normalizeTripData = (payload = {}) => {
  const safePayload =
    payload && typeof payload === "object" && !Array.isArray(payload) ? payload : {};
  const orchestratorData = safePayload.orchestrator_data ?? safePayload.orchestrator ?? {};
  const weatherData = safePayload.weather_data ?? safePayload.weather ?? {};
  const placesData = safePayload.places_data ?? safePayload.places ?? {};
  const transportData = safePayload.transport_data ?? safePayload.transport ?? {};
  const hotelData = safePayload.hotel_data ?? safePayload.hotel ?? {};

  return {
    ...safePayload,
    orchestrator_data: orchestratorData,
    weather_data: weatherData,
    places_data: placesData,
    transport_data: transportData,
    hotel_data: hotelData,
    orchestrator: orchestratorData,
    weather: weatherData,
    places: placesData,
    transport: transportData,
    hotel: hotelData,
    budget: safePayload.budget ?? {},
    itinerary: safePayload.itinerary ?? {},
    review: safePayload.review ?? {},
    pdf: safePayload.pdf ?? {},
    errors: Array.isArray(safePayload.errors) ? safePayload.errors : [],
    events: Array.isArray(safePayload.events) ? safePayload.events : []
  };
};

export const generateTrip = async (payload) => {
  const response = await axios.post(`${API_BASE_URL}/generate`, payload, {
    headers: {
      "Content-Type": "application/json"
    }
  });

  return {
    ...response.data,
    data: normalizeTripData(response.data?.data)
  };
};

const emitBufferEvents = (buffer, onEvent) => {
  const normalized = buffer.replace(/\r\n/g, "\n");
  const chunks = normalized.split("\n\n");
  const pending = chunks.pop() ?? "";

  chunks.forEach((chunk) => {
    const lines = chunk.split("\n");
    let eventName = "message";
    const dataLines = [];

    lines.forEach((line) => {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    });

    if (!dataLines.length) {
      return;
    }

    const raw = dataLines.join("\n");
    try {
      const parsed = JSON.parse(raw);
      onEvent({
        ...parsed,
        data: parsed.data !== undefined ? normalizeTripData(parsed.data) : undefined,
        sseEvent: eventName
      });
    } catch (error) {
      if (import.meta.env.DEV) {
        console.warn("Skipping malformed streamed event.", { error, raw, sseEvent: eventName });
      }
    }
  });

  return pending;
};

export const generateTripStream = async (payload, onEvent) => {
  const response = await fetch(`${API_BASE_URL}/generate-stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok || !response.body) {
    throw new Error("Streaming endpoint is unavailable.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    buffer = emitBufferEvents(buffer, onEvent);
  }

  const trailing = buffer.trim();
  if (trailing) {
    emitBufferEvents(`${trailing}\n\n`, onEvent);
  }
};

export const getApiErrorMessage = (error) => {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.message || error.message;
  }
  return error instanceof Error ? error.message : "Something went wrong.";
};
