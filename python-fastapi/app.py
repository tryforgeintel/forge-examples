"""A paid weather API: FastAPI + x402 payments + the Forge SDK.

Run: uvicorn app:app --port 4021 --env-file .env
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from cdp_facilitator import cdp_facilitator
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from forgeintel import Forge, ForgeMiddleware
from pydantic import BaseModel, Field
from weather import NotFoundError, UpstreamError, current_weather, daily_forecast, find_place
from x402 import x402ResourceServer
from x402.extensions.bazaar import OutputConfig, declare_discovery_extension
from x402.http import FacilitatorConfig, HTTPFacilitatorClient
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import PaymentOption, RouteConfig
from x402.mechanisms.evm.exact.server import ExactEvmScheme

log = logging.getLogger("uvicorn.error")
PAY_TO = os.environ.get("PAY_TO")
if not PAY_TO:
    raise RuntimeError("Set PAY_TO to the wallet address that receives payments (see .env.example)")

NAME = os.getenv("SERVICE_NAME", "Nimbus")
PUBLIC_URL = os.getenv("PUBLIC_URL", "")  # e.g. https://nimbus.clawca.sh

# Base Sepolia testnet through the public x402.org facilitator by default.
# With CDP API keys set, Coinbase's facilitator on Base mainnet instead.
cdp_key_id, cdp_key_secret = os.getenv("CDP_API_KEY_ID"), os.getenv("CDP_API_KEY_SECRET")
network = os.getenv("NETWORK", "eip155:8453" if cdp_key_id and cdp_key_secret else "eip155:84532")
facilitator = HTTPFacilitatorClient(
    cdp_facilitator(cdp_key_id, cdp_key_secret)
    if cdp_key_id and cdp_key_secret
    else FacilitatorConfig(url=os.getenv("FACILITATOR_URL", "https://x402.org/facilitator"))
)


@asynccontextmanager
async def lifespan(app):
    yield
    await facilitator.aclose()  # ForgeMiddleware flushes its own events at shutdown.


app = FastAPI(
    title=NAME,
    version="1.0.0",
    description="Weather for AI agents: current weather and 1-7 day forecasts, paid per call over x402.",
    lifespan=lifespan,
)

# The free landing page and icons.
PUBLIC = Path(__file__).parent / "public"
network_label = {"eip155:8453": "Base", "eip155:84532": "Base Sepolia (testnet)"}.get(network, network)
LANDING = (
    (PUBLIC / "index.html")
    .read_text()
    .replace("{{name}}", NAME)
    .replace("{{accent}}", "#2563EB")
    .replace("{{stack}}", "Python and FastAPI")
    .replace("{{network}}", network_label)
    .replace("{{source}}", "https://github.com/tryforgeintel/forge-examples/tree/main/python-fastapi")
)


@app.get("/", include_in_schema=False)
async def landing():
    return HTMLResponse(LANDING)


# Your routes, as you would write them without Forge. Declaring the 402 response
# tells Forge (through /openapi.json) which operations are paid.
PAID = {402: {"description": "Payment required"}}


class ForecastInput(BaseModel):
    # Forge removes agent_context before this model sees the body.
    city: str | None = Field(None, max_length=100, description="City name, e.g. London.")
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    days: int = Field(3, ge=1, le=7)


# Response models document the output for agents. Forge adds its forge_feedback
# field to these schemas in /openapi.json.
class Location(BaseModel):
    name: str
    country: str | None
    latitude: float
    longitude: float


class Current(BaseModel):
    time: str
    temperature_c: float
    humidity_pct: float
    wind_speed_kmh: float
    condition: str


class Day(BaseModel):
    date: str
    temperature_max_c: float
    temperature_min_c: float
    precipitation_mm: float | None
    condition: str


class WeatherOutput(BaseModel):
    location: Location
    current: Current


class ForecastOutput(BaseModel):
    location: Location
    days: list[Day]


async def lookup(city: str | None, lat: float | None, lon: float | None) -> dict:
    # x402 only settles 2xx/3xx responses, so a 400 for bad input costs the agent nothing.
    if not city and (lat is None or lon is None):
        raise HTTPException(400, "pass city, or both lat and lon")
    try:
        return await find_place(city, lat, lon)
    except NotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except UpstreamError as error:
        # 503, not 502: proxies like Cloudflare replace 502 bodies with their own error page.
        log.warning("%s", error)
        raise HTTPException(503, str(error)) from error


@app.get("/weather", response_model=WeatherOutput, responses=PAID)
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
        # 503, not 502: proxies like Cloudflare replace 502 bodies with their own error page.
        log.warning("%s", error)
        raise HTTPException(503, str(error)) from error


@app.post("/forecast", response_model=ForecastOutput, responses=PAID)
async def forecast(body: ForecastInput):
    """1-7 day forecast for a city or lat/lon: max/min temperature, precipitation, conditions."""
    place = await lookup(body.city, body.lat, body.lon)
    try:
        return {"location": place, "days": await daily_forecast(place, body.days)}
    except UpstreamError as error:
        # 503, not 502: proxies like Cloudflare replace 502 bodies with their own error page.
        log.warning("%s", error)
        raise HTTPException(503, str(error)) from error


@app.get("/health")
async def health():
    return {"ok": True, "network": network, "forge": forge.enabled}


app.mount("/", StaticFiles(directory=PUBLIC), name="static")  # after the routes: favicon, icons


# How the service is named in Bazaar listings.
listing = {"service_name": NAME, "tags": ["weather", "forecast"]}
if PUBLIC_URL:
    listing["icon_url"] = f"{PUBLIC_URL}/icon.png"
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
        **listing,
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
        **listing,
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
    public_url=PUBLIC_URL,  # optional: your public origin, for absolute rating links
)
# Added LAST so Starlette runs it FIRST: before payments and FastAPI's /openapi.json.
app.add_middleware(ForgeMiddleware, forge=forge)
