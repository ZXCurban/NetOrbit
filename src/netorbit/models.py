from __future__ import annotations

from dataclasses import dataclass
from time import time


@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lon: float


@dataclass(frozen=True)
class GeoResult:
    ip: str
    point: GeoPoint
    country: str = "Unknown"
    city: str = ""


@dataclass(frozen=True)
class PacketEvent:
    src_ip: str
    dst_ip: str
    protocol: str
    size: int
    interface: str = ""
    created_at: float = 0.0

    def with_timestamp(self) -> "PacketEvent":
        if self.created_at:
            return self
        return PacketEvent(
            src_ip=self.src_ip,
            dst_ip=self.dst_ip,
            protocol=self.protocol,
            size=self.size,
            interface=self.interface,
            created_at=time(),
        )


@dataclass(frozen=True)
class ConnectionEvent:
    src_ip: str
    dst_ip: str
    coords: GeoPoint | None
    country: str
    protocol: str
    size: int
    interface: str
    created_at: float


@dataclass(frozen=True)
class StatusEvent:
    message: str
    level: str = "info"
    created_at: float = 0.0

    def with_timestamp(self) -> "StatusEvent":
        if self.created_at:
            return self
        return StatusEvent(self.message, self.level, time())


NetOrbitEvent = PacketEvent | StatusEvent
