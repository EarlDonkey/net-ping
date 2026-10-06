# net-ping

> Async ping sweeper with ICMP and TCP fallback.

`net-ping` pings single hosts, CIDR ranges, or dash ranges — concurrently and
fast. Uses ICMP when it can (root), falls back to TCP connect when it can't.

## Features

- **ICMP ping** (requires root) — real ICMP echo
- **TCP connect ping** (`-p PORT`) — works unprivileged, no root needed
- **Concurrent sweeps** via asyncio (64 hosts in parallel by default)
- Accepts **IPs, CIDR, and dash ranges**
- `--json` output for scripting
- Non-zero exit when nothing responds

## Install

```bash
git clone https://github.com/YOUR_USERNAME/net-ping.git
cd net-ping
pipx install .
```

For development:

```bash
pip install -e ".[dev]"
```

## Usage

```bash
# Single host (ICMP, may need sudo)
sudo net-ping 192.168.1.1

# Sweep a subnet
sudo net-ping 192.168.1.0/24

# Sweep a range
sudo net-ping 192.168.1.1-192.168.1.50

# No root? Use TCP ping
net-ping 192.168.1.0/24 -p 443

# Multiple pings per host
sudo net-ping 192.168.1.1 -c 4

# JSON output
net-ping 192.168.1.0/24 -p 80 --json

# Tune concurrency and timeout
net-ping 10.0.0.0/24 -p 22 -C 128 -t 1
```

## Example output

```
$ net-ping 192.168.1.0/29 -p 443
192.168.1.1      up     0.42 ms
192.168.1.2      up     1.03 ms
192.168.1.3      down   -
192.168.1.4      down   -
192.168.1.5      up     0.88 ms
192.168.1.6      down   -

3 up, 3 down
```

```json
$ net-ping 192.168.1.1 -p 443 --json
{
  "results": [
    {
      "host": "192.168.1.1",
      "alive": true,
      "method": "tcp",
      "rtt_ms": 0.421
    }
  ],
  "summary": { "total": 1, "up": 1, "down": 0 }
}
```

## ICMP vs TCP

| | ICMP | TCP |
|---|---|---|
| Requires root | Yes | No |
| Detects hosts with all ports closed | Yes | No |
| Works through most firewalls | Sometimes | Sometimes |
| Cross-platform | Needs raw sockets | Yes |

**Rule of thumb:** ICMP for accuracy, TCP when you can't elevate.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | At least one host responded |
| `1` | No hosts responded |
| `2` | Bad arguments |

## Development

```bash
pytest
ruff check .
mypy src
```

## ⚠️ Legal

Only ping hosts and networks you own or have explicit permission to probe.
Mass scanning without authorization may violate law or terms of service.

## License

MIT — see [LICENSE](LICENSE).