"""Command-line interface for net-ping."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import NoReturn

from net_ping import __version__
from net_ping.pinger import PingResult, ping_many
from net_ping.targets import TargetError, parse_targets

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BAD_ARGS = 2


def _parse_ports(spec: str) -> int:
    """Accepts a single port. (Future: comma list.)"""
    try:
        port = int(spec)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid port: {spec}") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(f"port out of range: {port}")
    return port


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="net-ping",
        description="Async ping sweeper with ICMP and TCP fallback.",
        epilog="Only ping hosts you are authorized to probe.",
    )
    parser.add_argument(
        "target",
        help="IP, CIDR (192.168.1.0/24), or dash range (192.168.1.1-50).",
    )
    parser.add_argument(
        "-p",
        "--tcp-port",
        dest="tcp_port",
        type=_parse_ports,
        default=None,
        help="Use TCP connect ping on this port instead of ICMP (no root needed).",
    )
    parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=1,
        help="Number of ICMP pings per host (default: 1).",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=2.0,
        help="Per-host timeout in seconds (default: 2).",
    )
    parser.add_argument(
        "-C",
        "--concurrency",
        type=int,
        default=64,
        help="Max concurrent pings (default: 64).",
    )
    parser.add_argument(
        "-j",
        "--json",
        dest="as_json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"net-ping {__version__}",
    )
    return parser


def _print_human(results: list[PingResult]) -> None:
    up = 0
    for r in results:
        if r.alive:
            up += 1
            rtt = f"{r.rtt_ms:.2f} ms" if r.rtt_ms is not None else "-"
            print(f"{r.host:<16} up     {rtt}")
        else:
            print(f"{r.host:<16} down   -")
    down = len(results) - up
    print(f"\n{up} up, {down} down")


def _print_json(results: list[PingResult]) -> None:
    payload = {
        "results": [r.to_dict() for r in results],
        "summary": {
            "total": len(results),
            "up": sum(1 for r in results if r.alive),
            "down": sum(1 for r in results if not r.alive),
        },
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _fail(message: str, code: int) -> NoReturn:
    print(f"net-ping: error: {message}", file=sys.stderr)
    sys.exit(code)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        spec = parse_targets(args.target)
    except TargetError as exc:
        _fail(str(exc), EXIT_BAD_ARGS)

    if not spec.hosts:
        _fail("no hosts to ping after parsing target", EXIT_BAD_ARGS)

    try:
        results = asyncio.run(
            ping_many(
                list(spec.hosts),
                tcp_port=args.tcp_port,
                count=args.count,
                timeout=args.timeout,
                concurrency=args.concurrency,
            )
        )
    except KeyboardInterrupt:
        _fail("interrupted", EXIT_ERROR)

    if args.as_json:
        _print_json(results)
    else:
        _print_human(results)

    return EXIT_OK if any(r.alive for r in results) else EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())