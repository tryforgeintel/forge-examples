"""Files for agents that read before they call, and for crawlers:

  /llms.txt                                  what the service is, with links (llmstxt.org)
  /.well-known/agent-skills/index.json       the skill index (Agent Skills discovery, agentskills.io)
  /.well-known/agent-skills/<name>/SKILL.md  how to call it, as an Agent Skill
  /skill.md                                  the same skill, at the path agents often try first
  /robots.txt and /sitemap.xml               crawl rules and the pages above, for crawlers
"""

import hashlib
import os
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from payments import NETWORK_NAME, SERVICE_NAME

FILES = Path(__file__).parent / "agent-files"
# Skill names are lowercase letters, digits and single hyphens, up to 64 characters.
SLUG = re.sub(r"[^a-z0-9]+", "-", SERVICE_NAME.lower()).strip("-")[:64] or "weather"
SKILL_PATH = f"/.well-known/agent-skills/{SLUG}/SKILL.md"
SOURCE = "https://github.com/tryforgeintel/forge-examples/tree/main/python-fastapi"
CACHE = {"Cache-Control": "public, max-age=300"}
TEXT = "text/plain; charset=utf-8"


def origin_of(request: Request) -> str:
    """Absolute links: PUBLIC_URL when set, else the origin the request came in on."""
    return (os.getenv("PUBLIC_URL") or str(request.base_url)).rstrip("/")


def fill(file: str, origin: str) -> str:
    return (
        (FILES / file)
        .read_text()
        .replace("{{origin}}", origin)
        .replace("{{name}}", SERVICE_NAME)
        .replace("{{slug}}", SLUG)
        .replace("{{network}}", NETWORK_NAME)
        .replace("{{source}}", SOURCE)
    )


def serve(file: str, media_type: str):
    def handler(request: Request) -> Response:
        return Response(fill(file, origin_of(request)), media_type=media_type, headers=CACHE)

    return handler


def skill_index(request: Request) -> JSONResponse:
    body = fill("SKILL.md", origin_of(request))
    description = re.search(r"^description: (.+)$", body, re.M).group(1)
    return JSONResponse(
        {
            "$schema": "https://schemas.agentskills.io/discovery/0.2.0/schema.json",
            "skills": [
                {
                    "name": SLUG,
                    "type": "skill-md",
                    "description": description,
                    "url": SKILL_PATH,
                    "digest": f"sha256:{hashlib.sha256(body.encode()).hexdigest()}",
                }
            ],
        },
        headers=CACHE,
    )


def add_agent_files(app: FastAPI) -> None:
    """Call before add_pages: its static files are served from / as a fallback."""
    routes = {
        "/llms.txt": serve("llms.txt", TEXT),
        "/robots.txt": serve("robots.txt", TEXT),
        "/sitemap.xml": serve("sitemap.xml", "application/xml"),
        "/.well-known/agent-skills/index.json": skill_index,
    }
    for path in (SKILL_PATH, "/skill.md", "/SKILL.md"):
        routes[path] = serve("SKILL.md", "text/markdown; charset=utf-8")
    for path, handler in routes.items():
        app.add_api_route(path, handler, include_in_schema=False)
