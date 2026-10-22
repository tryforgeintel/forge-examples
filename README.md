# Forge examples

Runnable examples of an x402 paid API instrumented with [Forge](https://forgeintel.co), the analytics layer for APIs that AI agents pay for.

Both examples are the same small weather API, one in Node and one in Python, and both run live on Base mainnet:

| Example | Stack | Live |
| --- | --- | --- |
| [`node-express`](node-express) (SkyCast) | Express, `@x402/express`, [`@forgeintel/sdk`](https://www.npmjs.com/package/@forgeintel/sdk) | [skycast.clawca.sh](https://skycast.clawca.sh) |
| [`python-fastapi`](python-fastapi) (Nimbus) | FastAPI, `x402`, [`forgeintel-sdk`](https://pypi.org/project/forgeintel-sdk/) (Python 3.10+) | [nimbus.clawca.sh](https://nimbus.clawca.sh) |

Each one has:

| Route | Price | What it shows |
| --- | --- | --- |
| `GET /weather?city=London` | $0.001 | A paid GET. Agents send context as query parameters. |
| `POST /forecast` `{"city":"London","days":3}` | $0.002 | A paid JSON POST. Agents send context in the body. |
| `GET /openapi.json` | free | Your spec, with Forge's additions. |
| `GET /health` | free | Whether Forge is on. |
| `GET /` | free | A landing page for people, with the favicon and icons. |

Weather comes from [Open-Meteo](https://open-meteo.com), so you don't need any key other than your Forge SDK key. Payments default to Base Sepolia testnet, so trying it costs nothing.

## What Forge adds

Forge observes the API you already run: it reports which agents call it and what each one did, from the docs it read to the 402 it got and the call it paid for, and shows each visit as a session in your Forge dashboard. It changes nothing agents see: requests reach your code unchanged, responses go out exactly as your app sends them, and prices, payment terms and settlement stay yours. Events are sent in the background, never on the request path, so if Forge is down your API is unaffected.

## Start

1. Sign in at [app.forgeintel.co](https://app.forgeintel.co), add your service, and copy its SDK key.
2. Follow the README of [`node-express`](node-express) or [`python-fastapi`](python-fastapi).

Docs: [docs.forgeintel.co](https://docs.forgeintel.co)

## License

MIT
