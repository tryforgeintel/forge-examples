# Python + FastAPI (Nimbus)

Live at [nimbus.clawca.sh](https://nimbus.clawca.sh). A paid weather API with FastAPI, [`x402`](https://pypi.org/project/x402/) and the Forge SDK ([`forgeintel-sdk`](https://pypi.org/project/forgeintel-sdk/)). Needs Python 3.10 or later.

## Run it

```sh
git clone https://github.com/tryforgeintel/forge-examples
cd forge-examples/python-fastapi
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # add FORGE_API_KEY and PAY_TO
.venv/bin/uvicorn app:app --port 4021 --env-file .env
```

## Try it

```sh
curl localhost:4021/health
# {"ok":true,"network":"eip155:84532","forge":true}

curl -i "localhost:4021/weather?city=London"
# HTTP/1.1 402 Payment Required, with the challenge in the PAYMENT-REQUIRED header

curl -s -D - -o /dev/null "localhost:4021/weather?city=London" \
  | grep -i payment-required | cut -d' ' -f2 | tr -d '\r' | base64 -d
# the decoded challenge: the rating ask, and the forge-feedback and forge-agent-context extensions

curl localhost:4021/openapi.json
# FastAPI's spec, with agent context, rating fields and the free /feedback routes
```

To make a paid call, use any x402 client funded with Base Sepolia USDC (free from [Circle's faucet](https://faucet.circle.com)). The paid response looks like this:

```json
{
  "location": { "name": "London", "country": "United Kingdom" },
  "current": { "temperature_c": 19.9, "condition": "Overcast" },
  "forge_feedback": {
    "feedback_id": "arj7pgqxqVbPyxJWA_qXkg",
    "feedback_url": "https://your-api/feedback/rate?feedback_id=arj7pgqxqVbPyxJWA_qXkg&outcome=",
    "rate_this_call": "Please rate this service for other agents: ..."
  }
}
```

The call, and any rating, shows up under **Activity** for your service at [app.forgeintel.co](https://app.forgeintel.co).

## The Forge part

The whole integration is [`forge.py`](forge.py), with both switches written out, plus one line in [`app.py`](app.py):

```python
# forge.py
forge = Forge(
    api_key=os.getenv("FORGE_API_KEY", ""),
    public_url=os.getenv("PUBLIC_URL", ""),
    feedback=True,  # ask agents to rate each paid call
    agent_context=AgentContextOptions(required=False, search_query=True),  # never reject
)

# app.py, after the payment middleware (Starlette runs the last added first)
app.add_middleware(ForgeMiddleware, forge=forge)
```

| Switch | Here | What it does |
| --- | --- | --- |
| `feedback` | `True` | Adds the rating ask to the 402, a `forge_feedback` object with a free rating link to paid responses, and the free `/feedback` routes. |
| `agent_context` `required` | `False` | Asks agents for their name and the search that found you, and records it when sent. `True` rejects paid calls without it (HTTP 400, before payment). `agent_context=False` turns it off. |
| `agent_context` `search_query` | `True` | Also asks for the search query. |

FastAPI doesn't know about the 402 your payment middleware returns, so the paid routes declare it (`responses={402: ...}`). That's how Forge tells paid operations apart in `/openapi.json`. The response models document the output for agents, and Forge adds `forge_feedback` to them.

The rest of the app knows nothing about Forge:

| File | What it is |
| --- | --- |
| [`app.py`](app.py) | The FastAPI app and its two routes |
| [`payments.py`](payments.py) | x402: prices, facilitator, Bazaar listing |
| [`cdp_facilitator.py`](cdp_facilitator.py) | Signs requests to Coinbase's facilitator (mainnet) |
| [`models.py`](models.py) | Request and response models |
| [`weather.py`](weather.py) | Weather data from Open-Meteo |
| [`pages.py`](pages.py) | Landing page and icons |

All options: [docs.forgeintel.co/reference/options](https://docs.forgeintel.co/reference/options).

## Go live

- Deploy anywhere that runs Python. Set `FORGE_API_KEY` and `PAY_TO`. The included `Procfile` runs `uvicorn app:app --host 0.0.0.0 --port $PORT`.
- Set `PUBLIC_URL` to your public origin, for absolute rating links and the icon in Bazaar listings, and `SERVICE_NAME` to rename the service (default Nimbus).
- For Base mainnet, set `CDP_API_KEY_ID` and `CDP_API_KEY_SECRET` ([Coinbase Developer Platform](https://portal.cdp.coinbase.com)). The example then uses Coinbase's facilitator on `eip155:8453`; [`cdp_facilitator.py`](cdp_facilitator.py) signs its requests.
- Add the deployed domain to your service in Forge. Forge then checks your visibility in agent indexes, your search rankings and the health of your paid routes.
