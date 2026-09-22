"""SSRF-safe URL validation for hosted scoring."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeURLError(ValueError):
    pass


_BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def assert_public_http_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeURLError("Only http(s) URLs are allowed")
    host = parsed.hostname
    if not host:
        raise UnsafeURLError("URL missing hostname")
    if host.lower() in {"localhost", "metadata.google.internal"}:
        raise UnsafeURLError("Hostname not allowed")

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"DNS resolution failed: {exc}") from exc

    for info in infos:
        ip_str = info[4][0]
        ip = ipaddress.ip_address(ip_str)
        for net in _BLOCKED_NETWORKS:
            if ip in net:
                raise UnsafeURLError(f"Resolved address {ip} is not publicly routable")
    return url.strip()
