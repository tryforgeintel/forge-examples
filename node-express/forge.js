// The Forge SDK: this file is the whole integration, plus one line in server.js.
// Every option: https://docs.forgeintel.co/reference/options
import { createForge } from "@forgeintel/sdk";

export const forge = createForge({
  // Your service's SDK key from app.forgeintel.co. Without it, Forge stays out of the way.
  apiKey: process.env.FORGE_API_KEY,
  // Your public origin (e.g. https://skycast.clawca.sh), so rating links are absolute.
  publicUrl: process.env.PUBLIC_URL,

  // Both switches are off by default: with only the key, Forge reports your paid traffic
  // and changes nothing agents see.

  // Feedback: ask agents to rate each paid call. Adds the ask to the 402 (and a preview in your
  // Bazaar example), a forge_feedback object with a free rating link to paid responses, and
  // the free /feedback routes.
  feedback: true,

  // Agent context: ask agents for their name and the search that led them here.
  //   true                records it when sent, never rejects a call
  //   { required: true }  rejects paid calls without it (HTTP 400, before payment)
  //   { searchQuery: false } asks for the agent name only
  agentContext: false, // off on this live service, to isolate the feedback ask; main has true
});
