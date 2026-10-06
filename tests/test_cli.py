"""Tests for net_ping.cli."""

from __future__ import annotations

import json
from unittest.mock import patch

from net_ping.cli import main
from net_ping.pinger import PingResult


def _patch(results):
    return patch("net_ping.cli.ping_many", return_value=results)


def test_human_output(capsys) -> None:
    results = [
        PingResult("10.0.0.1", True, rtt_ms=0.5),
        PingResult("10.0.0.2", False),
    ]

    with _patch(results):
        code = main(["10.0.0.1-10.0.0.2"])

    out = capsys.readouterr().out
    assert code == 0
    assert "up" in out
    assert "down" in out
    assert "1 up, 1 down" in out


def test_json_output(capsys) -> None:
    results = [PingResult("10.0.0.1", True, rtt_ms=0.5, method="tcp")]

    with _patch(results):
        code = main(["10.0.0.1", "--json", "-p", "80"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["summary"]["up"] == 1
    assert payload["results"][0]["method"] == "tcp"


def test_all_down_returns_exit_1() -> None:
    results = [PingResult("10.0.0.1", False)]

    with _patch(results):
        code = main(["10.0.0.1"])

    assert code == 1


def test_invalid_port_returns_bad_args() -> None:
    import pytest

    with pytest.raises(SystemExit) as exc:
        main(["10.0.0.1", "-p", "99999"])

    assert exc.value.code == 2