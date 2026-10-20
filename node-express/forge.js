// The Forge SDK: this file is the whole integration, plus one line in server.js.
// Every option: https://docs.forgeintel.co/reference/options
import { createForge } from "@forgeintel/sdk";

export const forge = createForge({
  // Your service's SDK key from app.forgeintel.co. Without it, Forge stays out of the way.
  apiKey: process.env.FORGE_BACKEND_URL ? process.env.FORGE_TEST_API_KEY : process.env.FORGE_API_KEY,
  // Your public origin (e.g. https://skycast.clawca.sh), so rating links are absolute.
  publicUrl: process.env.PUBLIC_URL,
  // Where events go. Unset: Forge's production collector. Set FORGE_BACKEND_URL (with FORGE_TEST_API_KEY, a key
  // from that collector) to test against another one; the production key stays untouched.
  backendUrl: process.env.FORGE_BACKEND_URL || undefined,

  // Both switches are off by default: with only the key, Forge reports your paid traffic
  // and changes nothing agents see.

  // Feedback: ask agents to rate each paid call. Adds the ask to the 402 (and a preview in your
  // Bazaar example), a forge_feedback object with a free rating link to paid responses, and
  // the free /feedback routes.
  feedback: true,

  // x402 discovery: serve /.well-known/x402 (your paid endpoints, for x402 indexes like x402scan) when you
  // don't serve one. Off by default.
  x402Discovery: true,
});
