"""A paid weather API: FastAPI + x402 payments + the Forge SDK.

Run: uvicorn app:app --port 4021 --env-file .env
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from x402 import x402ResourceServer
from x402.extensions.bazaar import OutputConfig, declare_discovery_extension
from x402.http import FacilitatorConfig, HTTPFacilitatorClient
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import PaymentOption, RouteConfig
from x402.mechanisms.evm.exact.server import ExactEvmScheme

from forgeintel import Forge, ForgeMiddleware
from weather import NotFoundError, UpstreamError, current_weather, daily_forecast, find_place

PAY_TO = os.environ.get("PAY_TO")
if not PAY_TO:
    raise RuntimeError("Set PAY_TO to the wallet address that receives payments (see .env.example)")

# Base Sepolia testnet through the public x402.org facilitator by default.
network = os.getenv("NETWORK", "eip155:84532")
facilitator = HTTPFacilitatorClient(
    FacilitatorConfig(url=os.getenv("FACILITATOR_URL", "https://x402.org/facilitator"))
)


@asynccontextmanager
async def lifespan(app):
    yield
    await facilitator.aclose()  # ForgeMiddleware flushes its own events at shutdown.


app = FastAPI(title="Forge Weather Example", version="1.0.0", lifespan=lifespan)


# Your routes, as you would write them without Forge. Declaring the 402 response
# tells Forge (through /openapi.json) which operations are paid.
PAID = {402: {"description": "Payment required"}}


class ForecastInput(BaseModel):
    # Strict on purpose: Forge removes agent_context before this model sees the body.
    model_config = ConfigDict(extra="forbid")
    city: str | None = Field(None, max_length=100, description="City name, e.g. London.")
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    days: int = Field(3, ge=1, le=7)


async def lookup(city: str | None, lat: float | None, lon: float | None) -> dict:
    # x402 only settles 2xx/3xx responses, so a 400 for bad input costs the agent nothing.
    if not city and (lat is None or lon is None):
        raise HTTPException(400, "pass city, or both lat and lon")
    try:
        return await find_place(city, lat, lon)
    except NotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except UpstreamError as error:
        raise HTTPException(502, str(error)) from error


@app.get("/weather", responses=PAID)
async def weather(
    city: str | None = Query(None, max_length=100, description="City name, e.g. London."),
    lat: float | None = Query(None, ge=-90, le=90),
    lon: float | None = Query(None, ge=-180, le=180),
):
    """Current weather for a city or lat/lon: temperature, humidity, wind, conditions."""
    place = await lookup(city, lat, lon)
    try:
        return {"location": place, "current": await current_weather(place)}
    except UpstreamError as error:
        raise HTTPException(502, str(error)) from error


@app.post("/forecast", responses=PAID)
async def forecast(body: ForecastInput):
    """1-7 day forecast for a city or lat/lon: max/min temperature, precipitation, conditions."""
    place = await lookup(body.city, body.lat, body.lon)
    try:
        return {"location": place, "days": await daily_forecast(place, body.days)}
    except UpstreamError as error:
        raise HTTPException(502, str(error)) from error


@app.get("/health")
async def health():
    return {"ok": True, "network": network, "forge": forge.enabled}


location_schema = {
    "city": {"type": "string"},
    "lat": {"type": "number"},
    "lon": {"type": "number"},
}
routes = {
    "GET /weather": RouteConfig(
        accepts=PaymentOption(scheme="exact", pay_to=PAY_TO, price="$0.001", network=network),
        description="Current weather for a city or lat/lon: temperature, humidity, wind, conditions.",
        mime_type="application/json",
        extensions=declare_discovery_extension(
            input={"city": "London"},
            input_schema={"properties": location_schema},
            output=OutputConfig(
                example={
                    "location": {"name": "London", "country": "United Kingdom"},
                    "current": {"temperature_c": 18.4, "condition": "Partly cloudy"},
                }
            ),
        ),
    ),
    "POST /forecast": RouteConfig(
        accepts=PaymentOption(scheme="exact", pay_to=PAY_TO, price="$0.002", network=network),
        description="1-7 day forecast for a city or lat/lon: max/min temperature, precipitation, conditions.",
        mime_type="application/json",
        extensions=declare_discovery_extension(
            body_type="json",
            input={"city": "London", "days": 3},
            input_schema={
                "properties": {
                    **location_schema,
                    "days": {"type": "integer", "minimum": 1, "maximum": 7},
                }
            },
            output=OutputConfig(
                example={
                    "location": {"name": "London", "country": "United Kingdom"},
                    "days": [{"date": "2026-10-01", "temperature_max_c": 17, "condition": "Rain"}],
                }
            ),
        ),
    ),
}
server = x402ResourceServer(facilitator).register(network, ExactEvmScheme())
app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)

# Forge. Without FORGE_API_KEY it logs one warning and stays out of the way.
forge = Forge(
    api_key=os.getenv("FORGE_API_KEY", ""),
    public_url=os.getenv("PUBLIC_URL", ""),  # optional: your public origin, for absolute rating links
)
# Added LAST so Starlette runs it FIRST: before payments and FastAPI's /openapi.json.
app.add_middleware(ForgeMiddleware, forge=forge)
