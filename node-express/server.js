// A paid weather API: Express + x402 payments + the Forge SDK.
import { readFileSync } from "node:fs";
import express from "express";
import { facilitator as cdpFacilitator } from "@coinbase/x402";
import { HTTPFacilitatorClient } from "@x402/core/server";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { declareDiscoveryExtension } from "@x402/extensions/bazaar";
import { paymentMiddleware, x402ResourceServer } from "@x402/express";
import { createForge } from "@forgeintel/sdk";
import { currentWeather, dailyForecast, findPlace, NotFoundError, UpstreamError } from "./weather.js";

const env = process.env;
const port = Number(env.PORT ?? 4021);
if (!env.PAY_TO) throw new Error("Set PAY_TO to the wallet address that receives payments (see .env.example)");
const name = env.SERVICE_NAME ?? "SkyCast";
const publicUrl = env.PUBLIC_URL; // e.g. https://skycast.clawca.sh

// Base Sepolia testnet through the public x402.org facilitator by default.
// With CDP API keys set, Coinbase's facilitator on Base mainnet instead.
const cdp = Boolean(env.CDP_API_KEY_ID && env.CDP_API_KEY_SECRET);
const network = env.NETWORK ?? (cdp ? "eip155:8453" : "eip155:84532");
const facilitator = new HTTPFacilitatorClient(cdp ? cdpFacilitator : { url: env.FACILITATOR_URL ?? "https://x402.org/facilitator" });

// 1. Forge. Without FORGE_API_KEY it logs one warning and stays out of the way.
const forge = createForge({
  apiKey: env.FORGE_API_KEY,
  publicUrl, // optional: your public origin, for absolute rating links
});

// 2. Your x402 routes, as you would write them without Forge.
const place = { city: "London" };
// How the service is named in Bazaar listings.
const listing = { serviceName: name, tags: ["weather", "forecast"], ...(publicUrl ? { iconUrl: `${publicUrl}/icon.png` } : {}) };
const routes = {
  "GET /weather": {
    accepts: { scheme: "exact", price: "$0.001", network, payTo: env.PAY_TO },
    description: "Current weather for a city or lat/lon: temperature, humidity, wind, conditions.",
    mimeType: "application/json",
    ...listing,
    extensions: declareDiscoveryExtension({
      input: place,
      inputSchema: { properties: { city: { type: "string" }, lat: { type: "number" }, lon: { type: "number" } } },
      output: { example: { location: { name: "London", country: "United Kingdom" }, current: { temperature_c: 18.4, condition: "Partly cloudy" } } },
    }),
  },
  "POST /forecast": {
    accepts: { scheme: "exact", price: "$0.002", network, payTo: env.PAY_TO },
    description: "1-7 day forecast for a city or lat/lon: max/min temperature, precipitation, conditions.",
    mimeType: "application/json",
    ...listing,
    extensions: declareDiscoveryExtension({
      bodyType: "json",
      input: { ...place, days: 3 },
      inputSchema: { properties: { city: { type: "string" }, lat: { type: "number" }, lon: { type: "number" }, days: { type: "integer", minimum: 1, maximum: 7 } } },
      output: { example: { location: { name: "London", country: "United Kingdom" }, days: [{ date: "2026-10-01", temperature_max_c: 17, temperature_min_c: 9, condition: "Rain" }] } },
    }),
  },
};

const app = express();
app.set("trust proxy", true); // behind a TLS proxy (Railway, Render, Fly), so resource URLs are https

// 3. Forge first: before payments and your /openapi.json route.
app.use(forge.middleware());
app.use(express.json());

// The free landing page and icons.
const landing = readFileSync(new URL("./public/index.html", import.meta.url), "utf8")
  .replaceAll("{{name}}", name)
  .replaceAll("{{accent}}", "#F04B14")
  .replaceAll("{{stack}}", "Node.js and Express")
  .replaceAll("{{network}}", network === "eip155:8453" ? "Base" : network === "eip155:84532" ? "Base Sepolia (testnet)" : network)
  .replaceAll("{{source}}", "https://github.com/tryforgeintel/forge-examples/tree/main/node-express");
app.get("/", (_req, res) => res.type("html").send(landing));
app.use(express.static(new URL("./public", import.meta.url).pathname, { index: false, maxAge: "1d" }));

// 4. Payments.
app.use(paymentMiddleware(routes, new x402ResourceServer(facilitator).register(network, new ExactEvmScheme())));

// 5. Your handlers. Forge has already removed agent_context from req.query and req.body.
// x402 only settles 2xx/3xx responses, so a 400 for bad input costs the agent nothing.
function location(input) {
  const city = typeof input.city === "string" ? input.city.trim() : "";
  if (city) return city.length <= 100 ? { city } : "city is too long";
  const lat = Number(input.lat);
  const lon = Number(input.lon);
  if (input.lat === undefined || input.lon === undefined) return "pass city, or both lat and lon";
  if (!(lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180)) return "lat must be -90..90 and lon -180..180";
  return { lat, lon };
}

function fail(res, error) {
  if (error instanceof NotFoundError) return res.status(404).json({ error: error.message });
  if (error instanceof UpstreamError) return res.status(502).json({ error: error.message });
  console.error(error);
  res.status(500).json({ error: "internal_error" });
}

app.get("/weather", async (req, res) => {
  const loc = location(req.query);
  if (typeof loc === "string") return res.status(400).json({ error: loc });
  try {
    const where = await findPlace(loc);
    res.json({ location: where, current: await currentWeather(where) });
  } catch (error) {
    fail(res, error);
  }
});

app.post("/forecast", async (req, res) => {
  const body = req.body ?? {};
  const loc = location(body);
  const days = body.days ?? 3;
  if (typeof loc === "string") return res.status(400).json({ error: loc });
  if (!(Number.isInteger(days) && days >= 1 && days <= 7)) return res.status(400).json({ error: "days must be an integer from 1 to 7" });
  try {
    const where = await findPlace(loc);
    res.json({ location: where, days: await dailyForecast(where, days) });
  } catch (error) {
    fail(res, error);
  }
});

app.get("/health", (_req, res) => res.json({ ok: true, network, forge: forge.enabled }));

// Forge enriches this document on the way out: rating fields, feedback routes, agent context.
app.get("/openapi.json", (_req, res) => res.json(openapi));
const locationFields = {
  city: { type: "string", description: "City name, e.g. London. Or pass lat and lon." },
  lat: { type: "number" },
  lon: { type: "number" },
};
const openapi = {
  openapi: "3.1.0",
  info: { title: name, version: "1.0.0", description: "Weather for AI agents: current weather and 1-7 day forecasts, paid per call over x402." },
  paths: {
    "/weather": {
      get: {
        summary: routes["GET /weather"].description,
        parameters: Object.entries(locationFields).map(([name, schema]) => ({ name, in: "query", schema })),
        responses: { 200: { description: "Current weather" }, 402: { description: "Payment required ($0.001)" } },
      },
    },
    "/forecast": {
      post: {
        summary: routes["POST /forecast"].description,
        requestBody: {
          required: true,
          content: { "application/json": { schema: { type: "object", properties: { ...locationFields, days: { type: "integer", minimum: 1, maximum: 7 } } } } },
        },
        responses: { 200: { description: "Daily forecast" }, 402: { description: "Payment required ($0.002)" } },
      },
    },
  },
};

const server = app.listen(port, () => console.log(`${name} on http://localhost:${port} (${network})`));
// Flush Forge's background events on shutdown.
process.on("SIGTERM", () => server.close(() => forge.shutdown()));
