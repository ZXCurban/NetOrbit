from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from typing import Iterable

import requests

from .models import GeoPoint, GeoResult


PRIVATE_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
)


@dataclass
class GeoEngine:
    endpoint: str = "http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon,query"
    self_endpoint: str = "http://ip-api.com/json/?fields=status,country,city,lat,lon,query"
    timeout: float = 2.5
    cache: dict[str, GeoResult | None] = field(default_factory=dict)

    def lookup(self, ip: str) -> GeoResult | None:
        if not is_public_ipv4(ip):
            return None
        if ip in self.cache:
            return self.cache[ip]

        result = self._lookup_remote(ip)
        self.cache[ip] = result
        return result

    def lookup_self(self) -> GeoResult | None:
        try:
            response = requests.get(self.self_endpoint, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            return None

        return self._parse_payload(payload)

    def prime(self, results: Iterable[GeoResult]) -> None:
        for result in results:
            self.cache[result.ip] = result

    def _lookup_remote(self, ip: str) -> GeoResult | None:
        try:
            response = requests.get(self.endpoint.format(ip=ip), timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            return None

        return self._parse_payload(payload, fallback_ip=ip)

    def _parse_payload(self, payload: dict[str, object], fallback_ip: str = "") -> GeoResult | None:
        if payload.get("status") != "success":
            return None

        lat = payload.get("lat")
        lon = payload.get("lon")
        if lat is None or lon is None:
            return None

        return GeoResult(
            ip=str(payload.get("query") or fallback_ip),
            point=GeoPoint(lat=float(lat), lon=float(lon)),
            country=str(payload.get("country") or "Unknown"),
            city=str(payload.get("city") or ""),
        )


def is_public_ipv4(ip: str) -> bool:
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return False

    if address.version != 4:
        return False
    if address.is_private or address.is_loopback or address.is_multicast:
        return False
    return not any(address in network for network in PRIVATE_NETWORKS)
