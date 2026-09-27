// The OpenAPI document served at /openapi.json. Forge adds its fields on the way out.
// x-payment-info marks an operation as paid for agent wallets (AgentCash, x402scan); the 402
// response tells Forge the same. security: [] says no API key or login: x402 payment is not OpenAPI auth.
const PUBLIC_URL = process.env.PUBLIC_URL;

const paid = (amount) => ({ price: { mode: "fixed", currency: "USD", amount }, protocols: [{ x402: {} }] });
const noAuth = [];

const location = {
  city: { type: "string", maxLength: 100, description: "City name, e.g. London. Or pass lat and lon." },
  lat: { type: "number", minimum: -90, maximum: 90, description: "Latitude, with lon, instead of city." },
  lon: { type: "number", minimum: -180, maximum: 180, description: "Longitude, with lat, instead of city." },
};

const errors = {
  400: { description: "Invalid input. Not charged.", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
  404: { description: "City not found. Not charged.", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
  503: { description: "Weather provider unavailable. Not charged; retry later.", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
};

const json = (ref) => ({ "application/json": { schema: { $ref: `#/components/schemas/${ref}` } } });

export const openapi = {
  openapi: "3.1.0",
  info: {
    title: process.env.SERVICE_NAME ?? "SkyCast",
    version: "1.0.0",
    description: "Weather for AI agents: current weather and 1-7 day forecasts, paid per call over x402.",
    contact: { name: "Forge examples", url: "https://github.com/tryforgeintel/forge-examples" },
    license: { name: "MIT", identifier: "MIT" },
    // How to use the API, for agents. Forge appends its rating ask to this.
    "x-guidance":
      'Weather for any city. GET /weather?city=London for current conditions ($0.001); POST /forecast with {"city": "London", "days": 3} for a 1-7 day forecast ($0.002). Pass city, or lat and lon. Error responses are never charged.',
  },
  ...(PUBLIC_URL ? { servers: [{ url: PUBLIC_URL }] } : {}),
  tags: [{ name: "weather", description: "Paid weather data, per call over x402." }],
  paths: {
    "/weather": {
      get: {
        operationId: "getWeather",
        tags: ["weather"],
        summary: "Current weather for a city or lat/lon: temperature, humidity, wind, conditions.",
        description: "Current conditions for one place, from Open-Meteo. Pass city, or lat and lon. $0.001 per call over x402.",
        security: noAuth,
        "x-payment-info": paid("0.001"),
        parameters: Object.entries(location).map(([name, { description, ...schema }]) => ({ name, in: "query", description, schema })),
        responses: {
          200: { description: "Current weather", content: json("WeatherResult") },
          ...errors,
          402: { description: "Payment required ($0.001)" },
        },
      },
    },
    "/forecast": {
      post: {
        operationId: "getForecast",
        tags: ["weather"],
        summary: "1-7 day forecast for a city or lat/lon: max/min temperature, precipitation, conditions.",
        description: "Daily forecast for one place, from Open-Meteo. Pass city, or lat and lon, and days (default 3). $0.002 per call over x402.",
        security: noAuth,
        "x-payment-info": paid("0.002"),
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: { ...location, days: { type: "integer", minimum: 1, maximum: 7, default: 3, description: "Number of days, 1-7." } },
              },
              example: { city: "London", days: 3 },
            },
          },
        },
        responses: {
          200: { description: "Daily forecast", content: json("ForecastResult") },
          ...errors,
          402: { description: "Payment required ($0.002)" },
        },
      },
    },
    "/health": {
      get: {
        operationId: "health",
        summary: "Service health",
        security: noAuth,
        responses: { 200: { description: "OK", content: { "application/json": { schema: { type: "object", properties: { ok: { type: "boolean" } } } } } } },
      },
    },
  },
  components: {
    schemas: {
      Location: {
        type: "object",
        required: ["name", "country", "latitude", "longitude"],
        properties: {
          name: { type: "string" },
          country: { type: ["string", "null"] },
          latitude: { type: "number" },
          longitude: { type: "number" },
        },
      },
      WeatherResult: {
        type: "object",
        required: ["location", "current"],
        properties: {
          location: { $ref: "#/components/schemas/Location" },
          current: {
            type: "object",
            required: ["time", "temperature_c", "humidity_pct", "wind_speed_kmh", "condition"],
            properties: {
              time: { type: "string", description: "Local time, ISO 8601." },
              temperature_c: { type: "number" },
              humidity_pct: { type: "number" },
              wind_speed_kmh: { type: "number" },
              condition: { type: "string", examples: ["Overcast"] },
            },
          },
        },
      },
      ForecastResult: {
        type: "object",
        required: ["location", "days"],
        properties: {
          location: { $ref: "#/components/schemas/Location" },
          days: {
            type: "array",
            items: {
              type: "object",
              required: ["date", "temperature_max_c", "temperature_min_c", "precipitation_mm", "condition"],
              properties: {
                date: { type: "string", format: "date" },
                temperature_max_c: { type: "number" },
                temperature_min_c: { type: "number" },
                precipitation_mm: { type: ["number", "null"] },
                condition: { type: "string" },
              },
            },
          },
        },
      },
      Error: { type: "object", required: ["error"], properties: { error: { type: "string" } } },
    },
  },
};
