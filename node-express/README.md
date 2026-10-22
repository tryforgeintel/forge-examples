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

curl localhost:4021/llms.txt
# what the service is, with links (llmstxt.org)

curl localhost:4021/.well-known/agent-skills/index.json
# the skill index; the skill itself is at /.well-known/agent-skills/skycast/SKILL.md (and /skill.md)

curl localhost:4021/.well-known/x402
# the paid endpoints, for x402 indexes such as x402scan

curl localhost:4021/openapi.json
# the API description
```

To make a paid call, use any x402 client funded with Base Sepolia USDC (free from [Circle's faucet](https://faucet.circle.com)). The response is the app's own, unchanged by Forge:

```json
{
  "location": { "name": "London", "country": "United Kingdom" },
  "current": { "temperature_c": 19.9, "condition": "Overcast" }
}
```

The visit shows up as a session under **Activity** for your service at [app.forgeintel.co](https://app.forgeintel.co): which agent it was, what it read, the 402 it got and the call it paid for.

## The Forge part

The whole integration is [`forge.js`](forge.js) plus one line in [`server.js`](server.js):

```js
// forge.js
export const forge = createForge({ apiKey: process.env.FORGE_API_KEY });

// server.js
app.use(forge.middleware()); // first: before payments and your routes
```

Forge only observes: requests reach the app unchanged and responses go out exactly as the app sends them.

The rest of the app knows nothing about Forge:

| File | What it is |
| --- | --- |
| [`server.js`](server.js) | The Express app and its two routes |
| [`payments.js`](payments.js) | x402: prices, facilitator, Bazaar listing |
| [`openapi.js`](openapi.js) | The API description agents read |
| [`weather.js`](weather.js) | Weather data from Open-Meteo |
| [`site.js`](site.js) | Landing page and icons |
| [`agents.js`](agents.js) | `/llms.txt`, the agent skill (`SKILL.md`), `/robots.txt` and `/sitemap.xml`, filled in from [`agent-files/`](agent-files) |

All options: [docs.forgeintel.co/reference/options](https://docs.forgeintel.co/reference/options).

## Go live

- Deploy anywhere that runs Node. Set `FORGE_API_KEY` and `PAY_TO`, and run `npm start`. The server listens on `PORT`.
- If outbound calls time out with `ETIMEDOUT` on a host far from Open-Meteo's servers, set `NODE_OPTIONS=--network-family-autoselection-attempt-timeout=2000`. Node gives each IPv6/IPv4 connection attempt only 250ms by default.
- Set `PUBLIC_URL` to your public origin, for the links in the agent files and the icon in Bazaar listings, and `SERVICE_NAME` to rename the service (default SkyCast).
- For Base mainnet, set `CDP_API_KEY_ID` and `CDP_API_KEY_SECRET` ([Coinbase Developer Platform](https://portal.cdp.coinbase.com)). The example then uses Coinbase's facilitator on `eip155:8453`.
- Add the deployed domain to your service in Forge. Forge then checks your visibility in agent indexes, your search rankings and the health of your paid routes.
