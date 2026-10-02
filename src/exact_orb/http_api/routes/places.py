"""Read-only place suggestions from the application-owned catalog."""

from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from exact_orb.birth.places import (
    InvalidPlaceQuery, PlaceCatalogUnavailableError, PlaceSuggestions,
)
from exact_orb.http_api.dto import ErrorDTO
from exact_orb.http_api.ownership import observe_disconnect, track_request
from exact_orb.http_api.projectors import project_places
from exact_orb.http_api.request_boundary import (
    BoundaryRejection, error_response, response_headers,
)


router = APIRouter()


def _place_error(
    request_id: str, *, code: str, detail_code: str | None,
    message: str, status: int, retryable: bool, retry_after: int | None = None,
) -> JSONResponse:
    dto = ErrorDTO(
        code=code, detail_code=detail_code,
        user_message=message, retryable=retryable,
    )
    headers = response_headers(request_id)
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return JSONResponse(dto.model_dump(mode="json"), status_code=status, headers=headers)


@router.get("/places")
@track_request
async def places(request: Request) -> JSONResponse:
    try:
        prepared = await request.app.state.request_boundary.prepare(
            request, query_kind="places",
        )
    except BoundaryRejection as rejected:
        return error_response(rejected)

    observe_disconnect(request)
    query = prepared.query
    assert query is not None
    rejection = await request.app.state.admission.reserve_place_search(
        client_ip=prepared.client_ip,
    )
    if rejection is not None:
        return _place_error(
            prepared.request_id, code=rejection.code,
            detail_code=rejection.detail_code,
            message="Слишком много запросов поиска. Попробуйте позже.",
            status=rejection.status_code, retryable=True,
            retry_after=rejection.retry_after,
        )
    try:
        result = await request.app.state.catalog.search(query.query, limit=query.limit)
    except PlaceCatalogUnavailableError:
        return _place_error(
            prepared.request_id, code="PLACE_CATALOG_UNAVAILABLE",
            detail_code=None,
            message="Каталог мест временно недоступен. Попробуйте ещё раз.",
            status=503, retryable=True, retry_after=5,
        )

    if isinstance(result, InvalidPlaceQuery):
        return _place_error(
            prepared.request_id, code="INVALID_PLACE_QUERY",
            detail_code=result.code,
            message="Проверьте поисковый запрос.",
            status=422, retryable=False,
        )
    if not isinstance(result, PlaceSuggestions):
        raise TypeError("unexpected place search outcome")
    dto = project_places(result)
    return JSONResponse(
        dto.model_dump(mode="json"), headers=response_headers(prepared.request_id),
    )
