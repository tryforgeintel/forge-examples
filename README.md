# Forge examples

Runnable examples of an x402 paid API instrumented with [Forge](https://forgeintel.co), the analytics layer for APIs that AI agents pay for.

Both examples are the same small weather API, one in Node and one in Python:

| Example | Stack |
| --- | --- |
| [`node-express`](node-express) | Express, `@x402/express`, [`@forgeintel/sdk`](https://www.npmjs.com/package/@forgeintel/sdk) |
| [`python-fastapi`](python-fastapi) | FastAPI, `x402`, [`forgeintel-sdk`](https://pypi.org/project/forgeintel-sdk/) (Python 3.10+) |

Each one has:

| Route | Price | What it shows |
| --- | --- | --- |
| `GET /weather?city=London` | $0.001 | A paid GET. Agents send context as query parameters. |
| `POST /forecast` `{"city":"London","days":3}` | $0.002 | A paid JSON POST. Agents send context in the body. |
| `GET /openapi.json` | free | Your spec, with Forge's additions. |
| `GET /health` | free | Whether Forge is on. |

Weather comes from [Open-Meteo](https://open-meteo.com), so you don't need any key other than your Forge SDK key. Payments default to Base Sepolia testnet, so trying it costs nothing.

## What Forge adds

Forge adds a few lines to the x402 setup you already have. It never touches prices, payment terms or settlement.

- **Before payment:** the 402 challenge and OpenAPI ask agents to rate the call afterwards, and to say which agent they are and what they searched for. If the route declares a Bazaar listing, Forge adds the same fields there.
- **After payment:** paid JSON responses get a `forge_feedback` object with a free rating link.
- **In the background:** every 402, payment and rating is reported to your Forge dashboard. Nothing is added to the request path, and if Forge is down your API is unaffected.

Agent context is optional by default, so no paid request is rejected without it. See [Agent context](https://docs.forgeintel.co/guides/agent-context).

## Start

1. Sign in at [app.forgeintel.co](https://app.forgeintel.co), add your service, and copy its SDK key.
2. Follow the README of [`node-express`](node-express) or [`python-fastapi`](python-fastapi).

Docs: [docs.forgeintel.co](https://docs.forgeintel.co)

## License

MIT
