"""Raw HTTP validation shared by future business routes.

FastAPI resolves a route before its handler calls ``prepare``. This module
does not register business endpoints or touch admission/application components.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import date, time
import json
import re
from typing import Any, Literal
from urllib.parse import parse_qsl
from uuid import uuid4

from starlette.requests import Request
from starlette.responses import JSONResponse

from exact_orb.http_api.dto import ErrorDTO, IssueDTO
from exact_orb.http_api.proxy import InvalidForwardedHeaders, client_ip, trusted_networks


_COOKIE_NAME = "__Host-exact_orb_session"
_COOKIE_VALUE = re.compile(r"[A-Za-z0-9_-]{43}\Z", re.ASCII)
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z", re.ASCII)
_TIME = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]\Z", re.ASCII)
_LIMIT = re.compile(r"(?:[1-9]|1[0-9]|20)\Z", re.ASCII)

_ERRORS: dict[str, tuple[int, str, bool, int | None]] = {
    "SERVICE_SHUTTING_DOWN": (503, "Сервис перезапускается. Попробуйте ещё раз.", True, 30),
    "FORWARDED_HEADER_INVALID": (400, "Некорректные данные доверенного прокси.", False, None),
    "ORIGIN_NOT_ALLOWED": (403, "Источник запроса не разрешён.", False, None),
    "UNSUPPORTED_MEDIA_TYPE": (415, "Отправьте запрос в формате JSON UTF-8.", False, None),
    "REQUEST_TIMEOUT": (408, "Не удалось получить запрос вовремя.", True, 1),
    "REQUEST_TOO_LARGE": (413, "Запрос превышает допустимый размер.", False, None),
    "INVALID_REQUEST": (422, "Проверьте формат запроса и значения полей.", False, None),
    "SESSION_REQUIRED": (409, "Сначала откройте или восстановите сессию.", False, None),
}


class BoundaryRejection(Exception):
    """A safe transport rejection made before admission or a component call."""

    def __init__(
        self,
        code: str,
        *,
        detail_code: str | None = None,
        issue_fields: tuple[str, ...] = (),
        clear_cookie: bool = False,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.detail_code = detail_code
        self.issue_fields = issue_fields
        self.clear_cookie = clear_cookie
        self.request_id: str | None = None

    @property
    def status_code(self) -> int:
        return _ERRORS[self.code][0]

    @property
    def retry_after(self) -> int | None:
        return _ERRORS[self.code][3]


@dataclass(frozen=True, slots=True)
class SessionCookie:
    status: Literal["missing", "valid", "invalid", "duplicate"]
    value: str | None = None


@dataclass(frozen=True, slots=True)
class BuildPayload:
    birth_date: date
    birth_time: time | None
    place_id: str


@dataclass(frozen=True, slots=True)
class PlaceQuery:
    query: str
    limit: int


@dataclass(frozen=True, slots=True)
class PreparedRequest:
    request_id: str
    client_ip: str
    origin: str | None
    body: dict[str, Any] | BuildPayload | None
    query: PlaceQuery | None
    cookie: SessionCookie


def response_headers(request_id: str) -> dict[str, str]:
    return {"Cache-Control": "no-store", "X-Request-ID": request_id}


def error_response(rejection: BoundaryRejection) -> JSONResponse:
    """Render approved transport fields through the shared public ErrorDTO."""

    if rejection.request_id is None:
        raise ValueError("a boundary rejection must have a server request_id")
    status, message, retryable, retry_after = _ERRORS[rejection.code]
    fields: dict[str, Any] = {
        "code": rejection.code,
        "detail_code": rejection.detail_code,
        "user_message": message,
        "retryable": retryable,
    }
    if rejection.issue_fields:
        fields["issues"] = tuple(
            IssueDTO(field=field, code="INVALID") for field in rejection.issue_fields
        )
    payload = ErrorDTO(**fields).model_dump(mode="json")
    headers = response_headers(rejection.request_id)
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return JSONResponse(payload, status_code=status, headers=headers)


def _raw_header_values(scope: Mapping[str, Any], name: bytes) -> list[bytes]:
    return [value for key, value in scope.get("headers", []) if key.lower() == name]


def session_cookie(scope: Mapping[str, Any]) -> SessionCookie:
    """Inspect every raw Cookie field and every occurrence of the session key."""

    matches: list[str] = []
    malformed = False
    for header in _raw_header_values(scope, b"cookie"):
        for raw_part in header.decode("latin1").split(";"):
            part = raw_part.strip()
            if "=" not in part:
                malformed |= part == _COOKIE_NAME
                continue
            name, value = part.split("=", 1)
            if name.strip() == _COOKIE_NAME:
                matches.append(value)
    if len(matches) > 1:
        return SessionCookie("duplicate")
    if malformed or (matches and _COOKIE_VALUE.fullmatch(matches[0]) is None):
        return SessionCookie("invalid")
    if matches:
        return SessionCookie("valid", matches[0])
    return SessionCookie("missing")


def _check_origin(scope: Mapping[str, Any], allowed: frozenset[str]) -> str | None:
    values = _raw_header_values(scope, b"origin")
    if not values:
        return None
    if len(values) != 1:
        raise BoundaryRejection("ORIGIN_NOT_ALLOWED")
    try:
        origin = values[0].decode("ascii")
    except UnicodeDecodeError as exc:
        raise BoundaryRejection("ORIGIN_NOT_ALLOWED") from exc
    if origin not in allowed:
        raise BoundaryRejection("ORIGIN_NOT_ALLOWED")
    return origin


def _check_post_media(scope: Mapping[str, Any]) -> None:
    if _raw_header_values(scope, b"content-encoding"):
        raise BoundaryRejection("UNSUPPORTED_MEDIA_TYPE")
    content_types = _raw_header_values(scope, b"content-type")
    if len(content_types) != 1:
        raise BoundaryRejection("UNSUPPORTED_MEDIA_TYPE")
    try:
        content_type = content_types[0].decode("ascii")
    except UnicodeDecodeError as exc:
        raise BoundaryRejection("UNSUPPORTED_MEDIA_TYPE") from exc
    parts = [part.strip() for part in content_type.split(";")]
    if parts[0].lower() != "application/json" or len(parts) > 2:
        raise BoundaryRejection("UNSUPPORTED_MEDIA_TYPE")
    if len(parts) == 2:
        key, separator, value = parts[1].partition("=")
        if separator != "=" or key.strip().lower() != "charset" or value.strip().lower() != "utf-8":
            raise BoundaryRejection("UNSUPPORTED_MEDIA_TYPE")


async def _receive_body(
    receive: Callable[[], Awaitable[dict[str, Any]]],
    *,
    scheduler: Any,
    timeout_seconds: float,
    max_bytes: int,
) -> bytes:
    first = await receive()
    if first["type"] == "http.disconnect":
        raise asyncio.CancelledError
    if first["type"] != "http.request":
        raise BoundaryRejection("INVALID_REQUEST", issue_fields=("request.body",))
    deadline = scheduler.now() + timeout_seconds
    body = bytearray()
    message = first
    while True:
        chunk = message.get("body", b"")
        if not isinstance(chunk, bytes):
            raise BoundaryRejection("INVALID_REQUEST", issue_fields=("request.body",))
        body.extend(chunk)
        if len(body) > max_bytes:
            raise BoundaryRejection("REQUEST_TOO_LARGE")
        if not message.get("more_body", False):
            return bytes(body)

        incoming = asyncio.create_task(receive())
        timer = asyncio.create_task(scheduler.wait_until(deadline))
        try:
            done, _ = await asyncio.wait({incoming, timer}, return_when=asyncio.FIRST_COMPLETED)
            if incoming not in done or scheduler.now() > deadline:
                raise BoundaryRejection("REQUEST_TIMEOUT", detail_code="BODY_RECEIVE_TIMEOUT")
            message = incoming.result()
            if message["type"] == "http.disconnect":
                raise asyncio.CancelledError
            if message["type"] != "http.request":
                raise BoundaryRejection("INVALID_REQUEST", issue_fields=("request.body",))
        finally:
            for task in (incoming, timer):
                if not task.done():
                    task.cancel()
            await asyncio.gather(incoming, timer, return_exceptions=True)


def _json_object(body: bytes) -> dict[str, Any]:
    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result

    def reject_constant(_: str) -> Any:
        raise ValueError("non-JSON numeric constant")

    try:
        value = json.loads(
            body.decode("utf-8"), object_pairs_hook=unique_pairs,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise BoundaryRejection("INVALID_REQUEST", issue_fields=("request.body",)) from exc
    if not isinstance(value, dict):
        raise BoundaryRejection("INVALID_REQUEST", issue_fields=("request.body",))
    return value


def _bootstrap_body(value: dict[str, Any]) -> dict[str, Any]:
    if value:
        field = next(iter(value))
        raise BoundaryRejection("INVALID_REQUEST", issue_fields=(f"request.{field}",))
    return value


def _build_body(value: dict[str, Any]) -> BuildPayload:
    expected = {"birth_date", "birth_time", "place_id"}
    extra = next((name for name in value if name not in expected), None)
    if extra is not None:
        raise BoundaryRejection("INVALID_REQUEST", issue_fields=(f"request.{extra}",))
    birth_date = value.get("birth_date")
    if not isinstance(birth_date, str) or _DATE.fullmatch(birth_date) is None:
        raise BoundaryRejection("INVALID_REQUEST", issue_fields=("birth.date",))
    try:
        parsed_date = date.fromisoformat(birth_date)
    except ValueError as exc:
        raise BoundaryRejection("INVALID_REQUEST", issue_fields=("birth.date",)) from exc
    if "birth_time" not in value:
        raise BoundaryRejection("INVALID_REQUEST", issue_fields=("birth.time",))
    birth_time = value["birth_time"]
    if birth_time is not None and (
        not isinstance(birth_time, str) or _TIME.fullmatch(birth_time) is None
    ):
        raise BoundaryRejection("INVALID_REQUEST", issue_fields=("birth.time",))
    parsed_time = time.fromisoformat(birth_time) if birth_time is not None else None
    place_id = value.get("place_id")
    if not isinstance(place_id, str) or not 1 <= len(place_id) <= 128:
        raise BoundaryRejection("INVALID_REQUEST", issue_fields=("birth.place",))
    return BuildPayload(parsed_date, parsed_time, place_id)


def _places_query(raw: bytes) -> PlaceQuery:
    try:
        pairs = parse_qsl(
            raw.decode("ascii"), keep_blank_values=True,
            encoding="utf-8", errors="strict",
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise BoundaryRejection("INVALID_REQUEST") from exc
    values: dict[str, list[str]] = {}
    for name, value in pairs:
        values.setdefault(name, []).append(value)
    if len(values.get("query", [])) != 1:
        raise BoundaryRejection("INVALID_REQUEST", detail_code="QUERY_REQUIRED")
    query = values["query"][0]
    if len(query) > 512:
        raise BoundaryRejection("INVALID_REQUEST", detail_code="QUERY_TOO_LONG")
    if len(values.get("limit", [])) > 1:
        raise BoundaryRejection("INVALID_REQUEST", detail_code="LIMIT_INVALID")
    if any(name not in {"query", "limit"} for name in values):
        raise BoundaryRejection("INVALID_REQUEST")
    limit_values = values.get("limit", [])
    if limit_values and _LIMIT.fullmatch(limit_values[0]) is None:
        raise BoundaryRejection("INVALID_REQUEST", detail_code="LIMIT_INVALID")
    return PlaceQuery(query, int(limit_values[0]) if limit_values else 10)


class RequestBoundary:
    """Validate one matched business request before cookie/admission/I/O."""

    def __init__(
        self,
        *,
        allowed_origins: tuple[str, ...],
        public_origin: str,
        trusted_proxy_cidrs: tuple[str, ...],
        body_timeout_seconds: float,
        max_body_bytes: int,
        scheduler: Any,
        is_ready: Callable[[], bool],
    ) -> None:
        self._origins = frozenset((*allowed_origins, public_origin))
        self._trusted = trusted_networks(trusted_proxy_cidrs)
        self._body_timeout = body_timeout_seconds
        self._max_body = max_body_bytes
        self._scheduler = scheduler
        self._is_ready = is_ready

    async def prepare(
        self,
        request: Request,
        *,
        body_kind: Literal["none", "bootstrap", "build"] = "none",
        query_kind: Literal["none", "places"] = "none",
        cookie_mode: Literal["ignore", "optional", "required"] = "ignore",
    ) -> PreparedRequest:
        request_id = str(uuid4())
        try:
            if not self._is_ready():
                raise BoundaryRejection("SERVICE_SHUTTING_DOWN")
            try:
                address = client_ip(request.scope, self._trusted)
            except InvalidForwardedHeaders as exc:
                raise BoundaryRejection("FORWARDED_HEADER_INVALID") from exc
            origin = _check_origin(request.scope, self._origins)

            payload: dict[str, Any] | BuildPayload | None = None
            query: PlaceQuery | None = None
            if request.method == "POST":
                _check_post_media(request.scope)
                payload = _json_object(await _receive_body(
                    request.receive,
                    scheduler=self._scheduler,
                    timeout_seconds=self._body_timeout,
                    max_bytes=self._max_body,
                ))
                if body_kind == "bootstrap":
                    payload = _bootstrap_body(payload)
                elif body_kind == "build":
                    payload = _build_body(payload)
            elif query_kind == "places":
                query = _places_query(request.scope.get("query_string", b""))
            elif request.scope.get("query_string", b""):
                raise BoundaryRejection("INVALID_REQUEST")

            cookie = session_cookie(request.scope) if cookie_mode != "ignore" else SessionCookie("missing")
            if cookie_mode == "required" and cookie.status != "valid":
                raise BoundaryRejection(
                    "SESSION_REQUIRED", clear_cookie=cookie.status in {"invalid", "duplicate"},
                )
            return PreparedRequest(request_id, address, origin, payload, query, cookie)
        except BoundaryRejection as exc:
            exc.request_id = request_id
            raise
