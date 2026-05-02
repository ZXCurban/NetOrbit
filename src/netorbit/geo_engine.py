from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from .models import GeoPoint, GeoResult


IPV4_BLOCKED_RANGES = (
    (0x00000000, 0x00FFFFFF),
    (0x0A000000, 0x0AFFFFFF),
    (0x64400000, 0x647FFFFF),
    (0x7F000000, 0x7FFFFFFF),
    (0xA9FE0000, 0xA9FEFFFF),
    (0xAC100000, 0xAC1FFFFF),
    (0xC0000000, 0xC00000FF),
    (0xC0000200, 0xC00002FF),
    (0xC0A80000, 0xC0A8FFFF),
    (0xC6120000, 0xC613FFFF),
    (0xC6336400, 0xC63364FF),
    (0xCB007100, 0xCB0071FF),
    (0xE0000000, 0xFFFFFFFF),
)
IPV4_ALLOWED_EXCEPTIONS = {0xC0000009, 0xC000000A}


@dataclass(slots=True)
class GeoEngine:
    endpoint: str = "http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon,query"
    self_endpoint: str = "http://ip-api.com/json/?fields=status,country,city,lat,lon,query"
    timeout: float = 2.5
    max_cache_size: int = 2048
    cache: OrderedDict[str, GeoResult | None] = field(default_factory=OrderedDict)

    def lookup(self, ip: str) -> GeoResult | None:
        if not is_public_ipv4(ip):
            return None

        cached = self.cache.get(ip)
        if cached is not None or ip in self.cache:
            self.cache.move_to_end(ip)
            return cached

        result = self._lookup_remote(ip)
        self._cache_set(ip, result)
        return result

    def lookup_self(self) -> GeoResult | None:
        payload = self._get_json(self.self_endpoint)
        return self._parse_payload(payload)

    def prime(self, results: Iterable[GeoResult]) -> None:
        for result in results:
            self._cache_set(result.ip, result)

    def _lookup_remote(self, ip: str) -> GeoResult | None:
        return self._parse_payload(self._get_json(self.endpoint.format(ip=ip)), fallback_ip=ip)

    def _get_json(self, url: str) -> dict[str, object]:
        try:
            with urlopen(url, timeout=self.timeout) as response:
                return json.loads(response.read())
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
            return {}

    def _cache_set(self, ip: str, result: GeoResult | None) -> None:
        self.cache[ip] = result
        self.cache.move_to_end(ip)
        while len(self.cache) > self.max_cache_size:
            self.cache.popitem(last=False)

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


@lru_cache(maxsize=8192)
def is_public_ipv4(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False

    try:
        a, b, c, d = (int(part) for part in parts)
    except ValueError:
        return False

    if not (0 <= a <= 255 and 0 <= b <= 255 and 0 <= c <= 255 and 0 <= d <= 255):
        return False

    value = (a << 24) | (b << 16) | (c << 8) | d
    if value in IPV4_ALLOWED_EXCEPTIONS:
        return True
    for start, end in IPV4_BLOCKED_RANGES:
        if start <= value <= end:
            return False
    return True
