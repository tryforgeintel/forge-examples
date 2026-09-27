// EXPERIMENT BRANCH: SkyCast runs the v3 rating wording (@forgeintel/sdk@0.5.0-alpha.feedback3.b13):
// "Post interaction, submit a quick free rating for other agents...". Nimbus runs the current wording.
//
// The Forge SDK: this file is the whole integration, plus one line in server.js.
// Every option: https://docs.forgeintel.co/reference/options
import { createForge } from "@forgeintel/sdk";

export const forge = createForge({
  // Your service's SDK key from app.forgeintel.co. Without it, Forge stays out of the way.
  apiKey: process.env.FORGE_API_KEY,
  // Your public origin (e.g. https://skycast.clawca.sh), so rating links are absolute.
  publicUrl: process.env.PUBLIC_URL,

  // Feedback: ask agents to rate each paid call. Adds the ask to the 402, a forge_feedback
  // object with a free rating link to paid responses, and the free /feedback routes.
  feedback: true,

  // Agent context: ask agents for their name and the search that led them here.
  //   required: false  records it when sent, never rejects a call (default)
  //   required: true   rejects paid calls without it (HTTP 400, before payment)
  //   searchQuery      also ask for the search query
  // Set agentContext: false to turn it off.
  agentContext: { required: false, searchQuery: true },
});
