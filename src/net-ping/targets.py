"""Target parsing: IPs, CIDR ranges, and dash ranges."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass


class TargetError(ValueError):
    """Raised when a target specification is invalid."""


@dataclass(frozen=True)
class TargetSpec:
    """A parsed target specification."""

    hosts: tuple[str, ...]

    def __len__(self) -> int:
        return len(self.hosts)

    def __iter__(self):
        return iter(self.hosts)


def _expand_range(spec: str) -> list[str]:
    """Expand 'a-b' to a list of IPs. E.g. 10.0.0.1-10.0.0.5."""
    start_s, _, end_s = spec.partition("-")
    if not end_s:
        raise TargetError(f"invalid range: {spec}")
    try:
        start = ipaddress.IPv4Address(start_s.strip())
        end = ipaddress.IPv4Address(end_s.strip())
    except ipaddress.AddressValueError as exc:
        raise TargetError(f"invalid range endpoints in {spec!r}: {exc}") from exc

    if int(start) > int(end):
        raise TargetError(f"range start is after end: {spec}")

    return [str(ipaddress.IPv4Address(i)) for i in range(int(start), int(end) + 1)]


def parse_targets(spec: str, *, include_network: bool = False) -> TargetSpec:
    """Parse a single target spec into a list of host IPs.

    Accepts:
      - single IP:     192.168.1.1
      - CIDR:          192.168.1.0/24
      - dash range:    192.168.1.1-192.168.1.50

    For CIDR, the network and broadcast addresses are excluded unless
    `include_network=True` (they aren't pingable hosts on a typical LAN).
    """
    spec = spec.strip()
    if not spec:
        raise TargetError("empty target specification")

    # Dash range: contains '-' but isn't a CIDR
    if "-" in spec and "/" not in spec:
        return TargetSpec(tuple(_expand_range(spec)))

    # CIDR
    if "/" in spec:
        try:
            network = ipaddress.IPv4Network(spec, strict=False)
        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError) as exc:
            raise TargetError(f"invalid CIDR {spec!r}: {exc}") from exc

        hosts = list(network.hosts())
        if include_network:
            hosts = list(network)
        return TargetSpec(tuple(str(h) for h in hosts))

    # Single IP
    try:
        ip = ipaddress.IPv4Address(spec)
    except ipaddress.AddressValueError as exc:
        raise TargetError(f"invalid IP {spec!r}: {exc}") from exc
    return TargetSpec((str(ip),))