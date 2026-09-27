"""x402 payments, as you would set them up without Forge."""

import os

from x402 import x402ResourceServer
from x402.extensions.bazaar import OutputConfig, declare_discovery_extension
from x402.http import FacilitatorConfig, HTTPFacilitatorClient
from x402.http.types import PaymentOption, RouteConfig
from x402.mechanisms.evm.exact.server import ExactEvmScheme

from cdp_facilitator import cdp_facilitator

PAY_TO = os.getenv("PAY_TO")
if not PAY_TO:
    raise RuntimeError("Set PAY_TO to the wallet address that receives payments (see .env.example)")
SERVICE_NAME = os.getenv("SERVICE_NAME", "Nimbus")

# Base Sepolia testnet through the public x402.org facilitator by default.
# With CDP API keys set, Coinbase's facilitator on Base mainnet instead.
key_id, key_secret = os.getenv("CDP_API_KEY_ID"), os.getenv("CDP_API_KEY_SECRET")
network = os.getenv("NETWORK", "eip155:8453" if key_id and key_secret else "eip155:84532")
facilitator = HTTPFacilitatorClient(
    cdp_facilitator(key_id, key_secret)
    if key_id and key_secret
    else FacilitatorConfig(url=os.getenv("FACILITATOR_URL", "https://x402.org/facilitator"))
)

# How the service shows up in Bazaar listings.
listing = {"service_name": SERVICE_NAME, "tags": ["weather", "forecast"]}
if os.getenv("PUBLIC_URL"):
    listing["icon_url"] = f"{os.getenv('PUBLIC_URL')}/icon.png"
location = {"city": {"type": "string"}, "lat": {"type": "number"}, "lon": {"type": "number"}}

routes = {
    "GET /weather": RouteConfig(
        accepts=PaymentOption(scheme="exact", pay_to=PAY_TO, price="$0.001", network=network),
        description="Current weather for a city or lat/lon: temperature, humidity, wind, conditions.",
        mime_type="application/json",
        **listing,
        extensions=declare_discovery_extension(
            input={"city": "London"},
            input_schema={"properties": location},
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
                "properties": {**location, "days": {"type": "integer", "minimum": 1, "maximum": 7}}
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
