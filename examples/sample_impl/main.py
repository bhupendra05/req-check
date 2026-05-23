"""Sample URL shortener implementation — intentionally INCOMPLETE.

This is used as a demo of req-check: when verified against the spec,
the tool finds that REQ-3, REQ-4, REQ-5, REQ-6 are not implemented.
"""
import random
import string
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# In-memory store (violates REQ-9 — must use Postgres)
_store: dict[str, str] = {}


class ShortenRequest(BaseModel):
    url: str


def _generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


@app.post("/shorten")
def shorten(req: ShortenRequest):
    """Shorten a URL — but does not deduplicate, no custom alias, no expiration."""
    code = _generate_code()
    while code in _store:
        code = _generate_code()
    _store[code] = req.url
    return {"short_code": code, "short_url": f"http://localhost:8000/{code}"}


@app.get("/{short_code}")
def redirect(short_code: str):
    """Redirect to original URL."""
    if short_code not in _store:
        raise HTTPException(status_code=404)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=_store[short_code], status_code=302)
