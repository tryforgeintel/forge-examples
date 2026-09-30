// SkyCast: a paid weather API with Express, x402 payments and the Forge SDK.
//
//   forge.js     the Forge setup and its switches
//   payments.js  x402 payments (prices, facilitator, Bazaar listing)
//   openapi.js   the API description agents read
//   weather.js   weather data from Open-Meteo
//   site.js      landing page and icons
//   agents.js    llms.txt and the agent skill (SKILL.md)
import express from "express";
import { agents } from "./agents.js";
import { forge } from "./forge.js";
import { openapi } from "./openapi.js";
import { network, payments } from "./payments.js";
import { site } from "./site.js";
import { currentWeather, dailyForecast, findPlace, parseLocation, NotFoundError, UpstreamError } from "./weather.js";

const app = express();
app.set("trust proxy", true); // behind a TLS proxy, so payment resource URLs are https

app.use(forge.middleware()); // Forge first: before payments and /openapi.json
app.use(express.json());
app.use(payments);
app.use(site);
app.use(agents);

// Your routes. Forge has already removed agent_context from req.query and req.body.
// x402 only charges for 2xx/3xx responses, so a 400 for bad input costs the agent nothing.
app.get("/weather", async (req, res) => {
  const place = parseLocation(req.query);
  if (typeof place === "string") return res.status(400).json({ error: place });
  try {
    const location = await findPlace(place);
    res.json({ location, current: await currentWeather(location) });
  } catch (error) {
    fail(res, error);
  }
});

app.post("/forecast", async (req, res) => {
  const { days = 3, ...input } = req.body ?? {};
  const place = parseLocation(input);
  if (typeof place === "string") return res.status(400).json({ error: place });
  if (!(Number.isInteger(days) && days >= 1 && days <= 7)) return res.status(400).json({ error: "days must be an integer from 1 to 7" });
  try {
    const location = await findPlace(place);
    res.json({ location, days: await dailyForecast(location, days) });
  } catch (error) {
    fail(res, error);
  }
});

app.get("/openapi.json", (_req, res) => res.json(openapi));
app.get("/health", (_req, res) => res.json({ ok: true, network, forge: forge.enabled }));

function fail(res, error) {
  if (error instanceof NotFoundError) return res.status(404).json({ error: error.message });
  // 503, not 502: proxies like Cloudflare replace 502 bodies with their own error page.
  if (error instanceof UpstreamError) return res.status(503).json({ error: error.message });
  console.error(error);
  res.status(500).json({ error: "internal_error" });
}

const port = Number(process.env.PORT ?? 4021);
const server = app.listen(port, () => console.log(`${openapi.info.title} on http://localhost:${port} (${network})`));
process.on("SIGTERM", () => server.close(() => forge.shutdown())); // send Forge's queued events before exiting
