"""Session cookie generation and browser attributes for HTTP routes."""

from __future__ import annotations

import base64
import secrets

from starlette.responses import Response


COOKIE_NAME = "__Host-exact_orb_session"
_MAX_AGE = 604800


def new_session_id() -> str:
    """Return 32 random bytes as unpadded URL-safe base64."""

    return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")


def issue_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        COOKIE_NAME, session_id, max_age=_MAX_AGE, path="/",
        secure=True, httponly=True, samesite="lax",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        COOKIE_NAME, path="/", secure=True, httponly=True, samesite="lax",
    )
