"""Deterministic calculation-version records and fingerprints."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from importlib import metadata
import json
import logging
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from exact_orb import swiss_backend
import exact_orb.engine as engine_module
from exact_orb.engine.aspects import AspectConfig
from exact_orb.engine.configurations import ConfigurationConfig
from exact_orb.engine.strength import StrengthConfig
from exact_orb.errors import (
    EphemerisBindingAmbiguousError,
    EphemerisConfigurationError,
)


LOGGER = logging.getLogger(__name__)

CALCULATION_VERSION_SCHEMA = "v1"
UNRESOLVED_DISTRIBUTION = "<unresolved>"
_CALCULATION_VERSION_PREFIX = f"eo:calcver:{CALCULATION_VERSION_SCHEMA}:"
_FILE_READ_CHUNK_SIZE = 1024 * 1024
_NATIVE_SUFFIXES = frozenset({".pyd", ".so"})


class CalculationVersionRecord(BaseModel):
    """Frozen snapshot of the nine calculation-version components."""

    model_config = ConfigDict(frozen=True, strict=True)

    engine_version: str
    profiles_digest: str
    swisseph_version: str
    distribution: str
    native_module_digest: str | None
    ephemeris_files: tuple[tuple[str, str], ...]
    selena_method: str
    body_ids_digest: str
    ephemeris_flags: int


def compute_calculation_version_record(
    *,
    ephemeris_path: str | os.PathLike[str],
    selena_method: str,
    body_ids: Mapping[str, int],
    ephemeris_flags: int,
) -> CalculationVersionRecord:
    """Collect one calculation-version snapshot from explicit startup inputs."""

    return CalculationVersionRecord(
        engine_version=engine_module.ENGINE_VERSION,
        profiles_digest=_digest_json(_profiles_payload()),
        swisseph_version=_swisseph_version(),
        distribution=_swisseph_distribution(),
        native_module_digest=_native_module_digest(),
        ephemeris_files=_ephemeris_file_digests(ephemeris_path),
        selena_method=selena_method,
        body_ids_digest=_digest_json(
            sorted(
                ((name, swe_id) for name, swe_id in body_ids.items()),
                key=lambda item: item[0],
            )
        ),
        ephemeris_flags=ephemeris_flags,
    )


def calculation_version_of(record: CalculationVersionRecord) -> str:
    """Return the pure canonical fingerprint of an existing record."""

    payload = {
        "schema_version": CALCULATION_VERSION_SCHEMA,
        **record.model_dump(mode="json"),
    }
    return f"{_CALCULATION_VERSION_PREFIX}{hashlib.sha256(_canonical_json(payload)).hexdigest()}"


def compute_calculation_version(
    *,
    ephemeris_path: str | os.PathLike[str],
    selena_method: str,
    body_ids: Mapping[str, int],
    ephemeris_flags: int,
) -> str:
    """Collect and fingerprint the calculation environment without logging."""

    record = compute_calculation_version_record(
        ephemeris_path=ephemeris_path,
        selena_method=selena_method,
        body_ids=body_ids,
        ephemeris_flags=ephemeris_flags,
    )
    return calculation_version_of(record)


def log_calculation_version(record: CalculationVersionRecord) -> None:
    """Log one startup calculation-version record and any weakening warning."""

    version = calculation_version_of(record)
    LOGGER.info(
        "calculation_version_computed version=%s engine_version=%s "
        "profiles_digest=%s swisseph_version=%s distribution=%s "
        "native_module_digest=%s ephemeris_files=%s selena_method=%s "
        "body_ids_digest=%s ephemeris_flags=%s",
        version,
        record.engine_version,
        record.profiles_digest,
        record.swisseph_version,
        record.distribution,
        record.native_module_digest,
        record.ephemeris_files,
        record.selena_method,
        record.body_ids_digest,
        record.ephemeris_flags,
    )
    if record.native_module_digest is None:
        LOGGER.warning(
            "calculation_version_weakened "
            "reason=native_module_digest_unavailable"
        )


def _profiles_payload() -> dict[str, object]:
    return {
        "aspect_natal": AspectConfig.natal().model_dump(mode="json"),
        "aspect_transit": AspectConfig.transit().model_dump(mode="json"),
        "configuration": ConfigurationConfig().model_dump(mode="json"),
        "strength": StrengthConfig().model_dump(mode="json"),
    }


def _swisseph_version() -> str:
    value = getattr(swiss_backend.swe, "version", None)
    if not isinstance(value, str) or not value.strip():
        raise EphemerisConfigurationError(
            "Swiss Ephemeris does not expose a non-empty library version"
        )
    return value


def _swisseph_distribution() -> str:
    try:
        provider_mapping = metadata.packages_distributions()
    except Exception as exc:
        raise EphemerisConfigurationError(
            "cannot inspect the Swiss Ephemeris distribution mapping"
        ) from exc

    unique: dict[str, str] = {}
    for provider in provider_mapping.get("swisseph", ()) or ():
        name = str(provider)
        unique.setdefault(name.casefold(), name)
    providers = sorted(unique.values(), key=str.casefold)

    if len(providers) > 1:
        raise EphemerisBindingAmbiguousError(
            "multiple distributions provide swisseph: " + ", ".join(providers)
        )
    if not providers:
        return UNRESOLVED_DISTRIBUTION

    provider = providers[0]
    try:
        distribution_version = metadata.version(provider)
    except Exception as exc:
        raise EphemerisConfigurationError(
            f"cannot read distribution metadata for {provider}"
        ) from exc
    if not isinstance(distribution_version, str) or not distribution_version.strip():
        raise EphemerisConfigurationError(
            f"distribution metadata for {provider} has no version"
        )
    return f"{provider}=={distribution_version}"


def _native_module_digest() -> str | None:
    origin = getattr(swiss_backend.swe, "__file__", None)
    if not isinstance(origin, (str, os.PathLike)):
        return None

    try:
        path = Path(origin)
        if path.suffix.casefold() not in _NATIVE_SUFFIXES or not path.is_file():
            return None
        return _sha256_file(path)
    except (OSError, TypeError, ValueError):
        return None


def _ephemeris_file_digests(
    ephemeris_path: str | os.PathLike[str],
) -> tuple[tuple[str, str], ...]:
    try:
        directory = Path(ephemeris_path)
        if not directory.is_dir():
            raise EphemerisConfigurationError(
                "ephemeris path must name an existing directory"
            )
        files = [
            path
            for path in directory.iterdir()
            if path.suffix.casefold() == ".se1" and path.is_file()
        ]
    except EphemerisConfigurationError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise EphemerisConfigurationError(
            "cannot inspect the ephemeris directory"
        ) from exc

    files.sort(key=lambda path: (path.name.casefold(), path.name))
    digests: list[tuple[str, str]] = []
    for path in files:
        try:
            digest = _sha256_file(path)
        except OSError as exc:
            raise EphemerisConfigurationError(
                f"cannot read ephemeris file {path.name}"
            ) from exc
        digests.append((path.name, digest))
    return tuple(digests)


def _digest_json(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_FILE_READ_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "CALCULATION_VERSION_SCHEMA",
    "UNRESOLVED_DISTRIBUTION",
    "CalculationVersionRecord",
    "calculation_version_of",
    "compute_calculation_version",
    "compute_calculation_version_record",
    "log_calculation_version",
]
