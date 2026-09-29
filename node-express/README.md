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

The whole integration is [`forge.js`](forge.js), with both switches written out, plus one line in [`server.js`](server.js):

```js
// forge.js
export const forge = createForge({
  apiKey: process.env.FORGE_API_KEY,
  publicUrl: process.env.PUBLIC_URL,
  feedback: true,     // ask agents to rate each paid call (off by default)
  agentContext: true, // ask for agent name + search; never reject (off by default)
  x402Discovery: true, // serve /.well-known/x402 for x402 indexes (off by default)
});

// server.js
app.use(forge.middleware()); // first: before payments and /openapi.json
```

| Switch | Here | What it does |
| --- | --- | --- |
| `feedback` | `true` | Adds the rating ask to the 402 (and a preview in the Bazaar example), a `forge_feedback` object with a free rating link to paid responses, and the free `/feedback` routes. Off by default. |
| `agentContext` | `true` | Asks agents for their name and the search that found you, and records it when sent. `{ required: true }` rejects paid calls without it (HTTP 400, before payment); `{ searchQuery: false }` asks for the name only. Off by default. |
| `x402Discovery` | `true` | Serves `/.well-known/x402`, the list of your paid endpoints that x402 indexes crawl, since this app doesn't serve one. Off by default. With `feedback` on, Forge also serves `/.well-known/forge-feedback.json`. |

With neither switch, Forge still reports every 402 and paid call to your dashboard, and changes nothing agents see.

The rest of the app knows nothing about Forge:

| File | What it is |
| --- | --- |
| [`server.js`](server.js) | The Express app and its two routes |
| [`payments.js`](payments.js) | x402: prices, facilitator, Bazaar listing |
| [`openapi.js`](openapi.js) | The API description agents read |
| [`weather.js`](weather.js) | Weather data from Open-Meteo |
| [`site.js`](site.js) | Landing page and icons |

All options: [docs.forgeintel.co/reference/options](https://docs.forgeintel.co/reference/options).

## Go live

- Deploy anywhere that runs Node. Set `FORGE_API_KEY` and `PAY_TO`, and run `npm start`. The server listens on `PORT`.
- If outbound calls time out with `ETIMEDOUT` on a host far from Open-Meteo's servers, set `NODE_OPTIONS=--network-family-autoselection-attempt-timeout=2000`. Node gives each IPv6/IPv4 connection attempt only 250ms by default.
- Set `PUBLIC_URL` to your public origin, for absolute rating links and the icon in Bazaar listings, and `SERVICE_NAME` to rename the service (default SkyCast).
- For Base mainnet, set `CDP_API_KEY_ID` and `CDP_API_KEY_SECRET` ([Coinbase Developer Platform](https://portal.cdp.coinbase.com)). The example then uses Coinbase's facilitator on `eip155:8453`.
- Add the deployed domain to your service in Forge. Forge then checks your visibility in agent indexes, your search rankings and the health of your paid routes.
