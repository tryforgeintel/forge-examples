"""Nimbus: a paid weather API with FastAPI, x402 payments and the Forge SDK.

  forge.py           the Forge setup and its switches
  payments.py        x402 payments (prices, facilitator, Bazaar listing)
  models.py          request and response models (the API description agents read)
  weather.py         weather data from Open-Meteo
  pages.py           landing page and icons
  agents.py          llms.txt, the agent skill (SKILL.md), robots.txt and sitemap.xml

Run: uvicorn app:app --port 4021 --env-file .env
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from forgeintel import ForgeMiddleware
from x402.http.middleware.fastapi import PaymentMiddlewareASGI

from agents import add_agent_files
from forge import forge
from models import Error, ForecastInput, ForecastOutput, WeatherOutput
from pages import add_pages
from payments import SERVICE_NAME, facilitator, network, routes, server
from weather import (
    InvalidLocation,
    NotFoundError,
    UpstreamError,
    current_weather,
    daily_forecast,
    find_place,
)


@asynccontextmanager
async def lifespan(app):
    yield
    await facilitator.aclose()  # ForgeMiddleware sends its queued events on shutdown by itself


app = FastAPI(
    title=SERVICE_NAME,
    version="1.0.0",
    description="Weather for AI agents: current weather and 1-7 day forecasts, paid per call over x402.",
    contact={"name": "Forge examples", "url": "https://github.com/tryforgeintel/forge-examples"},
    license_info={"name": "MIT", "identifier": "MIT"},
    servers=[{"url": os.environ["PUBLIC_URL"]}] if os.getenv("PUBLIC_URL") else None,
    openapi_tags=[{"name": "weather", "description": "Paid weather data, per call over x402."}],
    lifespan=lifespan,
)


def paid(amount: str) -> dict:
    """The 402 tells Forge the route is paid; x-payment-info tells agent wallets (AgentCash, x402scan) the price.
    security: [] says no API key or login: x402 payment is not OpenAPI auth."""
    return {
        "responses": {
            400: {"model": Error, "description": "Invalid input. Not charged."},
            402: {"description": f"Payment required (${amount})"},
            404: {"model": Error, "description": "City not found. Not charged."},
            503: {"model": Error, "description": "Weather provider unavailable. Not charged; retry later."},
        },
        "openapi_extra": {
            "security": [],
            "x-payment-info": {"price": {"mode": "fixed", "currency": "USD", "amount": amount}, "protocols": [{"x402": {}}]}
        },
        "tags": ["weather"],
    }


# Your routes. Forge has already removed agent_context from the query and body.
@app.get(
    "/weather",
    response_model=WeatherOutput,
    operation_id="getWeather",
    summary="Current weather for a city or lat/lon: temperature, humidity, wind, conditions.",
    **paid("0.001"),
)
async def weather(
    city: str | None = Query(None, max_length=100, description="City name, e.g. London. Or pass lat and lon."),
    lat: float | None = Query(None, ge=-90, le=90, description="Latitude, with lon, instead of city."),
    lon: float | None = Query(None, ge=-180, le=180, description="Longitude, with lat, instead of city."),
):
    """Current conditions for one place, from Open-Meteo. Pass city, or lat and lon. $0.001 per call over x402."""
    place = await find_place(city, lat, lon)
    return {"location": place, "current": await current_weather(place)}


@app.post(
    "/forecast",
    response_model=ForecastOutput,
    operation_id="getForecast",
    summary="1-7 day forecast for a city or lat/lon: max/min temperature, precipitation, conditions.",
    **paid("0.002"),
)
async def forecast(body: ForecastInput):
    """Daily forecast for one place, from Open-Meteo. Pass city, or lat and lon, and days (default 3). $0.002 per call over x402."""
    place = await find_place(body.city, body.lat, body.lon)
    return {"location": place, "days": await daily_forecast(place, body.days)}


@app.get("/health", operation_id="health", summary="Service health", openapi_extra={"security": []})
async def health():
    return {"ok": True, "network": network, "forge": forge.enabled}


# x402 only charges for 2xx/3xx responses, so errors cost the agent nothing.
# 503, not 502: proxies like Cloudflare replace 502 bodies with their own error page.
for error, status in {InvalidLocation: 400, NotFoundError: 404, UpstreamError: 503}.items():
    app.add_exception_handler(
        error, lambda _request, exc, status=status: JSONResponse({"detail": str(exc)}, status)
    )

add_agent_files(app)
add_pages(app)

# How to use the API, for agents, in /openapi.json. Forge appends its rating ask to this.
GUIDANCE = (
    'Weather for any city. GET /weather?city=London for current conditions ($0.001); POST /forecast with {"city": "London", "days": 3} for a 1-7 day forecast ($0.002). '
    "Pass city, or lat and lon. Error responses are never charged."
)
fastapi_openapi = app.openapi


def openapi_with_guidance():
    schema = fastapi_openapi()  # FastAPI builds it once and caches it
    schema["info"]["x-guidance"] = GUIDANCE
    return schema


app.openapi = openapi_with_guidance

# Starlette runs the last added middleware first: Forge, then payments, then your routes.
app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)
app.add_middleware(ForgeMiddleware, forge=forge)
