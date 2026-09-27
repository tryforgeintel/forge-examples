# Python + FastAPI

A paid weather API with FastAPI, [`x402`](https://pypi.org/project/x402/) and the Forge SDK ([`forgeintel-sdk`](https://pypi.org/project/forgeintel-sdk/)). Needs Python 3.10 or later.

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

Everything else in [`app.py`](app.py) is a normal x402 FastAPI app. Forge adds three lines:

```python
from forgeintel import Forge, ForgeMiddleware

forge = Forge(api_key=os.getenv("FORGE_API_KEY", ""))

app.add_middleware(ForgeMiddleware, forge=forge)  # after PaymentMiddlewareASGI
```

Starlette runs the last added middleware first, so adding Forge after the payment middleware puts it in front of payments. It then sees the 402s and removes `agent_context` before FastAPI validates the request. That's why `ForecastInput` can forbid extra fields.

FastAPI doesn't know about the 402 your payment middleware returns, so the paid routes declare it (`responses={402: ...}`). That's how Forge tells paid operations apart in `/openapi.json`. Options: [docs.forgeintel.co/reference/options](https://docs.forgeintel.co/reference/options).

## Go live

- Deploy anywhere that runs Python. Set `FORGE_API_KEY` and `PAY_TO`. The included `Procfile` runs `uvicorn app:app --host 0.0.0.0 --port $PORT`.
- For Base mainnet, set `NETWORK=eip155:8453` and `FACILITATOR_URL` to a facilitator that settles on Base mainnet.
- Add the deployed domain to your service in Forge. Forge then checks your visibility in agent indexes, your search rankings and the health of your paid routes.
