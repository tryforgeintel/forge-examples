// The Forge SDK: this file is the whole integration, plus one line in server.js.
// Every option: https://docs.forgeintel.co/reference/options
import { createForge } from "@forgeintel/sdk";

// Forge only observes: it reports which agents call SkyCast and what each one did, and changes nothing they see.
export const forge = createForge({
  // Your service's SDK key from app.forgeintel.co. Without it, Forge stays out of the way.
  apiKey: process.env.FORGE_BACKEND_URL ? process.env.FORGE_TEST_API_KEY : process.env.FORGE_API_KEY,
  // Where events go. Unset: Forge's production collector. Set FORGE_BACKEND_URL (with FORGE_TEST_API_KEY, a key
  // from that collector) to test against another one; the production key stays untouched.
  backendUrl: process.env.FORGE_BACKEND_URL || undefined,
});
