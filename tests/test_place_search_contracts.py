"""Contracts for place-search suggestions and canonical query normalization."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

import exact_orb.birth as birth_api
from exact_orb.birth import places as place_contracts
from exact_orb.birth.places import (
    ALLOWED_ALTERNATE_LANGUAGES,
    InvalidPlaceQuery,
    PlaceSuggestion,
    PlaceSuggestions,
    normalize_place_query,
)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        pytest.param("ＭＯＳＣＯＷ", "moscow", id="nfkc-and-casefold"),
        pytest.param(
            "\u00a8Москва",
            "\u0308москва",
            id="nfkc-before-whitespace-folding",
        ),
        pytest.param(
            "\u2003Москва\u00a0\u202fобласть\u3000",
            "москва область",
            id="unicode-whitespace",
        ),
        pytest.param("Straße", "strasse", id="unicode-casefold"),
        pytest.param("ЁЖ ёлка", "еж елка", id="yo-after-casefold"),
        pytest.param("Łódź-東京", "łódź-東京", id="unicode-name-preserved"),
    ],
)
def test_normalize_place_query_builds_canonical_search_key(
    query: str,
    expected: str,
) -> None:
    assert normalize_place_query(query) == expected


@pytest.mark.parametrize(
    "query",
    [
        pytest.param("\tМосква", id="tab"),
        pytest.param("Москва\n", id="newline"),
        pytest.param("Москва\x00", id="nul"),
    ],
)
def test_raw_control_characters_are_rejected_before_whitespace_folding(
    query: str,
) -> None:
    assert normalize_place_query(query) == InvalidPlaceQuery(
        code="CONTROL_CHARACTERS"
    )


@pytest.mark.parametrize(
    ("query", "expected_code"),
    [
        pytest.param("", "EMPTY", id="empty"),
        pytest.param("\u2003" * 201, "EMPTY", id="whitespace-before-length"),
        pytest.param("#" * 201, "TOO_LONG", id="length-before-searchable"),
        pytest.param("###@@@", "NO_SEARCHABLE_CHARACTERS", id="no-searchable"),
    ],
)
def test_invalid_queries_return_typed_outcomes_in_validation_order(
    query: str,
    expected_code: str,
) -> None:
    result = normalize_place_query(query)

    assert isinstance(result, InvalidPlaceQuery)
    assert result.code == expected_code


def test_normalized_length_is_checked_after_nfkc() -> None:
    query = "\ufb03" * 67

    assert len(query) == 67
    assert normalize_place_query(query) == InvalidPlaceQuery(code="TOO_LONG")


def test_two_hundred_code_point_search_key_is_valid() -> None:
    query = "Я" * 200

    result = normalize_place_query(query)

    assert result == "я" * 200
    assert len(result) == 200


def test_allowed_alternate_languages_are_the_singleton_immutable_contract() -> None:
    assert ALLOWED_ALTERNATE_LANGUAGES == frozenset({"ru"})
    assert isinstance(ALLOWED_ALTERNATE_LANGUAGES, frozenset)


def test_search_models_expose_only_the_contract_fields() -> None:
    suggestion = PlaceSuggestion(
        place_id="524901",
        display_name="Москва",
        admin1_name="Москва",
        country_code="RU",
    )
    suggestions = PlaceSuggestions(items=(suggestion,))
    invalid = InvalidPlaceQuery(code="EMPTY")

    assert tuple(PlaceSuggestion.model_fields) == (
        "place_id",
        "display_name",
        "admin1_name",
        "country_code",
    )
    assert tuple(PlaceSuggestions.model_fields) == ("items",)
    assert tuple(InvalidPlaceQuery.model_fields) == ("code",)
    assert suggestions.items == (suggestion,)
    assert isinstance(suggestions.items, tuple)
    assert invalid.model_dump() == {"code": "EMPTY"}


@pytest.mark.parametrize(
    ("model", "field", "replacement"),
    [
        pytest.param(
            PlaceSuggestion(
                place_id="524901",
                display_name="Москва",
                admin1_name="Москва",
                country_code="RU",
            ),
            "display_name",
            "Moscow",
            id="suggestion",
        ),
        pytest.param(
            PlaceSuggestions(items=()),
            "items",
            (
                PlaceSuggestion(
                    place_id="524901",
                    display_name="Москва",
                    admin1_name="Москва",
                    country_code="RU",
                ),
            ),
            id="suggestions",
        ),
        pytest.param(
            InvalidPlaceQuery(code="EMPTY"),
            "code",
            "TOO_LONG",
            id="invalid-query",
        ),
    ],
)
def test_search_models_are_frozen(
    model: BaseModel,
    field: str,
    replacement: object,
) -> None:
    before = model.model_dump()

    with pytest.raises(ValidationError) as exc_info:
        setattr(model, field, replacement)

    assert {error["type"] for error in exc_info.value.errors()} == {
        "frozen_instance"
    }
    assert model.model_dump() == before


@pytest.mark.parametrize(
    ("model_type", "arguments"),
    [
        pytest.param(
            PlaceSuggestion,
            {
                "place_id": "524901",
                "display_name": "Москва",
                "admin1_name": "Москва",
                "country_code": "RU",
            },
            id="suggestion",
        ),
        pytest.param(
            PlaceSuggestions,
            {"items": ()},
            id="suggestions",
        ),
        pytest.param(
            InvalidPlaceQuery,
            {"code": "EMPTY"},
            id="invalid-query",
        ),
    ],
)
def test_search_models_forbid_extra_fields(
    model_type: type[BaseModel],
    arguments: dict[str, Any],
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        model_type(**arguments, unexpected=True)

    assert {error["type"] for error in exc_info.value.errors()} == {
        "extra_forbidden"
    }


@pytest.mark.parametrize(
    "code",
    [
        "EMPTY",
        "TOO_LONG",
        "CONTROL_CHARACTERS",
        "NO_SEARCHABLE_CHARACTERS",
    ],
)
def test_invalid_place_query_accepts_each_public_error_code(code: str) -> None:
    assert InvalidPlaceQuery(code=code).code == code


def test_invalid_place_query_rejects_unknown_error_code() -> None:
    with pytest.raises(ValidationError) as exc_info:
        InvalidPlaceQuery(code="UNKNOWN")

    assert {error["type"] for error in exc_info.value.errors()} == {"literal_error"}


def test_empty_suggestions_are_success_distinct_from_invalid_query() -> None:
    empty = PlaceSuggestions(items=())
    invalid = InvalidPlaceQuery(code="EMPTY")

    assert empty.items == ()
    assert type(empty) is PlaceSuggestions
    assert type(invalid) is InvalidPlaceQuery
    assert empty != invalid


def test_search_contracts_are_reexported_from_birth_package() -> None:
    assert birth_api.PlaceSearch is place_contracts.PlaceSearch
    assert birth_api.PlaceSuggestion is place_contracts.PlaceSuggestion
    assert birth_api.PlaceSuggestions is place_contracts.PlaceSuggestions
    assert birth_api.InvalidPlaceQuery is place_contracts.InvalidPlaceQuery
