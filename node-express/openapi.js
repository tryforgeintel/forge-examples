// The OpenAPI document served at /openapi.json. Forge adds its fields on the way out.
// The 402 responses tell Forge which operations are paid.
const location = {
  city: { type: "string", description: "City name, e.g. London. Or pass lat and lon." },
  lat: { type: "number" },
  lon: { type: "number" },
};

export const openapi = {
  openapi: "3.1.0",
  info: {
    title: process.env.SERVICE_NAME ?? "SkyCast",
    version: "1.0.0",
    description: "Weather for AI agents: current weather and 1-7 day forecasts, paid per call over x402.",
    // How to use the API, for agents. Forge appends its rating ask to this.
    "x-guidance":
      'Weather for any city. GET /weather?city=London for current conditions ($0.001); POST /forecast with {"city": "London", "days": 3} for a 1-7 day forecast ($0.002). Pass city, or lat and lon. Error responses are never charged.',
  },
  paths: {
    "/weather": {
      get: {
        summary: "Current weather for a city or lat/lon: temperature, humidity, wind, conditions.",
        parameters: Object.entries(location).map(([name, schema]) => ({ name, in: "query", schema })),
        responses: { 200: { description: "Current weather" }, 402: { description: "Payment required ($0.001)" } },
      },
    },
    "/forecast": {
      post: {
        summary: "1-7 day forecast for a city or lat/lon: max/min temperature, precipitation, conditions.",
        requestBody: {
          required: true,
          content: { "application/json": { schema: { type: "object", properties: { ...location, days: { type: "integer", minimum: 1, maximum: 7 } } } } },
        },
        responses: { 200: { description: "Daily forecast" }, 402: { description: "Payment required ($0.002)" } },
      },
    },
  },
};
