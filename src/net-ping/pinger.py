"""ICMP and TCP ping implementations."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from typing import Any


@dataclass
class PingResult:
    """Result of pinging a single host."""

    host: str
    alive: bool
    rtt_ms: float | None = None
    method: str = "icmp"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "host": self.host,
            "alive": self.alive,
            "method": self.method,
        }
        if self.rtt_ms is not None:
            out["rtt_ms"] = round(self.rtt_ms, 3)
        if self.error:
            out["error"] = self.error
        return out


async def tcp_ping(host: str, port: int, timeout: float) -> PingResult:
    """TCP connect ping — no root required."""
    loop = asyncio.get_running_loop()
    start = loop.time()
    try:
        fut = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(fut, timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        elapsed_ms = (loop.time() - start) * 1000
        return PingResult(host=host, alive=True, rtt_ms=elapsed_ms, method="tcp")
    except (TimeoutError, asyncio.TimeoutError):
        return PingResult(
            host=host, alive=False, method="tcp", error=f"timeout after {timeout}s"
        )
    except (OSError, socket.gaierror) as exc:
        return PingResult(host=host, alive=False, method="tcp", error=str(exc))


async def ping_host(
    host: str,
    *,
    tcp_port: int | None = None,
    count: int = 1,
    timeout: float = 2.0,
) -> PingResult:
    """Ping a single host.

    If `tcp_port` is set, uses TCP connect only (no root needed).
    Otherwise tries ICMP (requires root) and returns an error if not privileged.
    """
    if tcp_port is not None:
        return await tcp_ping(host, tcp_port, timeout)

    # ICMP path — needs root. Try to use icmplib; if we lack privileges,
    # report a clear error rather than silently failing.
    try:
        import icmplib
    except ImportError:
        return PingResult(
            host=host,
            alive=False,
            method="icmp",
            error="icmplib not installed",
        )

    loop = asyncio.get_running_loop()

    def _sync_ping() -> PingResult:
        try:
            result = icmplib.ping(host, count=count, timeout=timeout, privileged=True)
        except PermissionError:
            return PingResult(
                host=host,
                alive=False,
                method="icmp",
                error="ICMP requires root; try -p PORT for TCP ping",
            )
        except Exception as exc:
            return PingResult(host=host, alive=False, method="icmp", error=str(exc))

        if result.is_alive:
            return PingResult(
                host=host,
                alive=True,
                rtt_ms=result.avg_rtt,
                method="icmp",
            )
        return PingResult(host=host, alive=False, method="icmp", error="no reply")

    return await loop.run_in_executor(None, _sync_ping)


async def ping_many(
    hosts: list[str],
    *,
    tcp_port: int | None = None,
    count: int = 1,
    timeout: float = 2.0,
    concurrency: int = 64,
) -> list[PingResult]:
    """Ping many hosts concurrently, bounded by a semaphore."""
    semaphore = asyncio.Semaphore(concurrency)

    async def _one(host: str) -> PingResult:
        async with semaphore:
            return await ping_host(
                host, tcp_port=tcp_port, count=count, timeout=timeout
            )

    return await asyncio.gather(*(_one(h) for h in hosts))