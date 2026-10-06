"""Tests for net_ping.targets."""

from __future__ import annotations

import pytest

from net_ping.targets import TargetError, parse_targets


def test_single_ip() -> None:
    spec = parse_targets("192.168.1.5")
    assert spec.hosts == ("192.168.1.5",)


def test_cidr_slash_30_excludes_network_and_broadcast() -> None:
    spec = parse_targets("192.168.1.0/30")
    assert spec.hosts == ("192.168.1.1", "192.168.1.2")


def test_cidr_slash_32() -> None:
    spec = parse_targets("10.0.0.1/32")
    assert spec.hosts == ("10.0.0.1",)


def test_dash_range() -> None:
    spec = parse_targets("10.0.0.1-10.0.0.3")
    assert spec.hosts == ("10.0.0.1", "10.0.0.2", "10.0.0.3")


def test_reversed_range_raises() -> None:
    with pytest.raises(TargetError, match="start is after end"):
        parse_targets("10.0.0.10-10.0.0.1")


def test_invalid_ip_raises() -> None:
    with pytest.raises(TargetError, match="invalid IP"):
        parse_targets("999.1.1.1")


def test_invalid_cidr_raises() -> None:
    with pytest.raises(TargetError):
        parse_targets("10.0.0.0/99")


def test_empty_raises() -> None:
    with pytest.raises(TargetError, match="empty"):
        parse_targets("")


def test_include_network_flag() -> None:
    spec = parse_targets("192.168.1.0/30", include_network=True)
    assert spec.hosts == ("192.168.1.0", "192.168.1.1", "192.168.1.2", "192.168.1.3")