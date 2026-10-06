"""Tests for net_ping.pinger."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from net_ping.pinger import PingResult, ping_many, tcp_ping


async def test_tcp_ping_success() -> None:
    reader = object()
    writer = asyncio.StreamWriter.__new__(asyncio.StreamWriter)

    class _FakeWriter:
        def close(self) -> None: ...
        async def wait_closed(self) -> None: ...

    fake_writer = _FakeWriter()

    async def fake_open(host, port):
        return reader, fake_writer

    with patch("asyncio.open_connection", side_effect=fake_open):
        result = await tcp_ping("127.0.0.1", 80, timeout=1.0)

    assert result.alive
    assert result.method == "tcp"
    assert result.rtt_ms is not None


async def test_tcp_ping_timeout() -> None:
    async def slow_open(host, port):
        await asyncio.sleep(10)
        raise AssertionError("should have timed out")

    with patch("asyncio.open_connection", side_effect=slow_open):
        result = await tcp_ping("10.255.255.1", 80, timeout=0.05)

    assert not result.alive
    assert "timeout" in (result.error or "").lower()


async def test_tcp_ping_connection_refused() -> None:
    with patch("asyncio.open_connection", side_effect=ConnectionRefusedError):
        result = await tcp_ping("127.0.0.1", 1, timeout=1.0)

    assert not result.alive
    assert result.error


async def test_ping_many_bounded_concurrency() -> None:
    async def fake_ping(host, *, tcp_port=None, count=1, timeout=2.0):
        await asyncio.sleep(0.01)
        return PingResult(host=host, alive=True, rtt_ms=1.0)

    with patch("net_ping.pinger.ping_host", side_effect=fake_ping):
        results = await ping_many(
            [f"10.0.0.{i}" for i in range(1, 21)],
            concurrency=5,
        )

    assert len(results) == 20
    assert all(r.alive for r in results)