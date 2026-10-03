"""Resolve a canonical client IP from the raw ASGI peer and trusted hops."""

from __future__ import annotations

from ipaddress import (
    IPv4Address, IPv4Network, IPv6Address, IPv6Network, ip_address, ip_network,
)
from typing import Any, Mapping


IPAddress = IPv4Address | IPv6Address
IPNetwork = IPv4Network | IPv6Network


class InvalidForwardedHeaders(ValueError):
    """A trusted peer supplied an incomplete or malformed forwarding chain."""


def trusted_networks(cidrs: tuple[str, ...]) -> tuple[IPNetwork, ...]:
    """Parse an already validated app allowlist once at composition time."""

    return tuple(ip_network(cidr, strict=False) for cidr in cidrs)


def _canonical_address(value: str) -> IPAddress:
    if not value or "%" in value or any(char.isspace() for char in value):
        raise InvalidForwardedHeaders("invalid IP literal")
    try:
        address = ip_address(value)
    except ValueError as exc:
        raise InvalidForwardedHeaders("invalid IP literal") from exc
    if isinstance(address, IPv6Address) and address.ipv4_mapped is not None:
        return address.ipv4_mapped
    return address


def _header_values(
    headers: list[tuple[bytes, bytes]], name: bytes,
) -> list[bytes]:
    return [value for key, value in headers if key.lower() == name]


def client_ip(
    scope: Mapping[str, Any], trusted: tuple[IPNetwork, ...],
) -> str:
    """Return the first untrusted address from right to left, or the ASGI peer.

    Forwarding fields from an untrusted peer are ignored without parsing them.
    The result is suitable for an in-process quota key and is never logged.
    """

    peer = scope.get("client")
    if not isinstance(peer, tuple) or len(peer) != 2 or not isinstance(peer[0], str):
        raise InvalidForwardedHeaders("missing ASGI peer")
    peer_address = _canonical_address(peer[0])
    if not trusted or not any(peer_address in network for network in trusted):
        return str(peer_address)

    headers = scope.get("headers", [])
    forwarded_for = _header_values(headers, b"x-forwarded-for")
    forwarded_proto = _header_values(headers, b"x-forwarded-proto")
    if len(forwarded_for) != 1 or len(forwarded_proto) != 1:
        raise InvalidForwardedHeaders("trusted forwarding fields must be singular")
    if forwarded_proto[0] != b"https":
        raise InvalidForwardedHeaders("trusted forwarded protocol must be HTTPS")
    try:
        items = forwarded_for[0].decode("ascii").split(",")
    except UnicodeDecodeError as exc:
        raise InvalidForwardedHeaders("invalid forwarded chain") from exc
    if not 1 <= len(items) <= 10:
        raise InvalidForwardedHeaders("invalid forwarded chain length")

    chain = [_canonical_address(item.strip(" \t")) for item in items]
    for address in reversed([*chain, peer_address]):
        if not any(address in network for network in trusted):
            return str(address)
    raise InvalidForwardedHeaders("forwarded chain has no client")
