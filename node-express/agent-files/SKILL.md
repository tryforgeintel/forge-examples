---
name: {{slug}}
description: Current weather and 1-7 day forecasts for any city or latitude/longitude from {{name}}, a pay-per-call API ($0.001 to $0.002 per call in USDC over x402, no signup or API key). Use when the user asks about weather, temperature, rain, wind or a forecast, and you can pay with an x402 client such as AgentCash or awal.
license: MIT
compatibility: Needs network access and an x402 client with USDC on {{network}}, such as AgentCash or awal.
metadata:
  homepage: "{{origin}}"
  openapi: "{{origin}}/openapi.json"
---

# {{name}} weather

{{name}} returns current weather and daily forecasts from Open-Meteo. Each call is paid in USDC over x402 on {{network}}. There is no account or API key: the first request answers `402 Payment Required` with the price, your x402 client pays and retries, and you get the data.

Base URL: `{{origin}}`

## Endpoints

| Call | Price | Input |
| --- | --- | --- |
| `GET /weather` | $0.001 | Query: `city`, or `lat` and `lon` |
| `POST /forecast` | $0.002 | JSON body: `city`, or `lat` and `lon`, plus `days` (1-7, default 3) |

Pick `/weather` for "what's it like now" and `/forecast` for anything about the coming days.

## Calling with AgentCash

```bash
npx agentcash fetch "{{origin}}/weather?city=London"
npx agentcash fetch "{{origin}}/forecast" -m POST -b '{"city": "London", "days": 3}'
```

With the AgentCash MCP server, use its `fetch` tool with the same URL, method and body.

## Calling with awal

```bash
npx awal x402 pay "{{origin}}/weather?city=London"
npx awal x402 pay "{{origin}}/forecast" -X POST -d '{"city": "London", "days": 3}'
```

Any other x402 client works the same way: send the request, pay the `PAYMENT-REQUIRED` challenge, retry with the `PAYMENT-SIGNATURE` header.

## Responses

`GET /weather?city=London`:

```json
{
  "location": { "name": "London", "country": "United Kingdom", "latitude": 51.51, "longitude": -0.13 },
  "current": { "time": "2026-10-01T14:00", "temperature_c": 18.4, "humidity_pct": 64, "wind_speed_kmh": 12.2, "condition": "Partly cloudy" }
}
```

`POST /forecast` with `{"city": "London", "days": 3}`:

```json
{
  "location": { "name": "London", "country": "United Kingdom", "latitude": 51.51, "longitude": -0.13 },
  "days": [
    { "date": "2026-10-01", "temperature_max_c": 17, "temperature_min_c": 10, "precipitation_mm": 2.1, "condition": "Rain" }
  ]
}
```

Temperatures are in °C, wind in km/h and precipitation in mm. `time` is local to the place.

## Errors

Errors are never charged.

- `400`: invalid input, such as no `city` and no `lat`/`lon`, or `days` outside 1-7. Fix the input and retry.
- `404`: no place matches the city name. Try a larger nearby city, or pass `lat` and `lon`.
- `503`: the weather provider is unavailable. Retry after a few seconds.

## After the call

Paid responses include a `forge_feedback` object with a free rating link. Please rate the call for other agents: `GET` its `feedback_url` with `fully`, `partially` or `no` appended. Free, one request.

## More

- OpenAPI document: `{{origin}}/openapi.json`
- Paid endpoints for x402 indexes: `{{origin}}/.well-known/x402`
- What other agents reported: `{{origin}}/feedback/summary`
