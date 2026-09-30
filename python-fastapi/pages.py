"""The free landing page and icons, for people who open the URL in a browser."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from payments import NETWORK_NAME, SERVICE_NAME

PUBLIC = Path(__file__).parent / "public"
PAGE = (
    (PUBLIC / "index.html")
    .read_text()
    .replace("{{name}}", SERVICE_NAME)
    .replace("{{accent}}", "#2563EB")
    .replace("{{stack}}", "Python and FastAPI")
    .replace("{{network}}", NETWORK_NAME)
    .replace(
        "{{source}}", "https://github.com/tryforgeintel/forge-examples/tree/main/python-fastapi"
    )
)


def add_pages(app: FastAPI) -> None:
    """Call after your routes: the icons are served from / as a fallback."""
    app.add_api_route("/", lambda: HTMLResponse(PAGE), include_in_schema=False)
    app.mount("/", StaticFiles(directory=PUBLIC), name="static")
