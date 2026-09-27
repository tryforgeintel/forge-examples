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
    # Feedback: ask agents to rate each paid call. Adds the ask to the 402, a forge_feedback
    # object with a free rating link to paid responses, and the free /feedback routes.
    feedback=True,
    # Agent context: ask agents for their name and the search that led them here.
    #   required=False  records it when sent, never rejects a call (default)
    #   required=True   rejects paid calls without it (HTTP 400, before payment)
    #   search_query    also ask for the search query
    # Set agent_context=False to turn it off.
    agent_context=False,  # off for the feedback experiment; main has AgentContextOptions(...)
)
