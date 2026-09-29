"""The Forge SDK: this file is the whole integration, plus one line in app.py.

Every option: https://docs.forgeintel.co/reference/options
"""

import os

from forgeintel import Forge

forge = Forge(
    # Your service's SDK key from app.forgeintel.co. Without it, Forge stays out of the way.
    api_key=os.getenv("FORGE_API_KEY", ""),
    # Your public origin (e.g. https://nimbus.clawca.sh), so rating links are absolute.
    public_url=os.getenv("PUBLIC_URL", ""),
    # Both switches are off by default: with only the key, Forge reports your paid traffic
    # and changes nothing agents see.
    #
    # Feedback: ask agents to rate each paid call. Adds the ask to the 402 (and a preview in your
    # Bazaar example), a forge_feedback object with a free rating link to paid responses, and
    # the free /feedback routes.
    feedback=True,
    # Agent context: ask agents for their name and the search that led them here.
    #   True                                records it when sent, never rejects a call
    #   AgentContextOptions(required=True)  rejects paid calls without it (HTTP 400, before payment)
    #   AgentContextOptions(search_query=False)  asks for the agent name only
    agent_context=True,
    # x402 discovery: serve /.well-known/x402 (your paid endpoints, for x402 indexes like x402scan) when you
    # don't serve one. Off by default.
    x402_discovery=True,
)
