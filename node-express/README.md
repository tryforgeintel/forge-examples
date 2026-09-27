# Node + Express (SkyCast)

Live at [skycast.clawca.sh](https://skycast.clawca.sh). A paid weather API with Express, [`@x402/express`](https://www.npmjs.com/package/@x402/express) and the Forge SDK ([`@forgeintel/sdk`](https://www.npmjs.com/package/@forgeintel/sdk)). Needs Node 20.19 or later.

## Run it

```sh
git clone https://github.com/tryforgeintel/forge-examples
cd forge-examples/node-express
npm install
cp .env.example .env   # add FORGE_API_KEY and PAY_TO
npm run dev
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
# your spec, with agent context, rating fields and the free /feedback routes
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

Everything else in [`server.js`](server.js) is a normal x402 Express app. Forge adds three lines:

```js
import { createForge } from "@forgeintel/sdk";

const forge = createForge({ apiKey: process.env.FORGE_API_KEY });

app.use(forge.middleware()); // before paymentMiddleware and your /openapi.json route
```

Mount it first, so it sees the 402s your payment middleware returns and can remove `agent_context` before your handlers run. Options: [docs.forgeintel.co/reference/options](https://docs.forgeintel.co/reference/options).

## Go live

- Deploy anywhere that runs Node. Set `FORGE_API_KEY` and `PAY_TO`, and run `npm start`. The server listens on `PORT`.
- If outbound calls time out with `ETIMEDOUT` on a host far from Open-Meteo's servers, set `NODE_OPTIONS=--network-family-autoselection-attempt-timeout=2000`. Node gives each IPv6/IPv4 connection attempt only 250ms by default.
- Set `PUBLIC_URL` to your public origin, for absolute rating links and the icon in Bazaar listings, and `SERVICE_NAME` to rename the service (default SkyCast).
- For Base mainnet, set `CDP_API_KEY_ID` and `CDP_API_KEY_SECRET` ([Coinbase Developer Platform](https://portal.cdp.coinbase.com)). The example then uses Coinbase's facilitator on `eip155:8453`.
- Add the deployed domain to your service in Forge. Forge then checks your visibility in agent indexes, your search rankings and the health of your paid routes.
