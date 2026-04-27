from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from queue import Empty, Queue

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .geo_engine import GeoEngine
from .models import ConnectionEvent, GeoPoint, NetOrbitEvent, PacketEvent, StatusEvent
from .world_map import MapMarker, WorldMap


@dataclass
class DestinationMarker:
    point: GeoPoint
    event: ConnectionEvent
    started_at: float
    ttl: float = 8.0

    def progress(self, now: float) -> float:
        return min(1.0, max(0.0, (now - self.started_at) / self.ttl))

    def alive(self, now: float) -> bool:
        return self.progress(now) < 1.0


class NetOrbitUI:
    def __init__(
        self,
        event_queue: Queue[NetOrbitEvent],
        geo: GeoEngine,
        home: GeoPoint,
        fps: int = 12,
    ) -> None:
        self.event_queue = event_queue
        self.geo = geo
        self.home = home
        self.world_map = WorldMap(home=home)
        self.fps = fps
        self.markers: list[DestinationMarker] = []
        self.recent: deque[ConnectionEvent] = deque(maxlen=10)
        self.statuses: deque[StatusEvent] = deque(maxlen=4)
        self.captured_packets = 0
        self.mapped_packets = 0
        self.geo_misses = 0

    def run(self) -> None:
        console = Console()
        with Live(self.render(console), console=console, refresh_per_second=self.fps, screen=True) as live:
            while True:
                self.drain_events()
                self.markers = [marker for marker in self.markers if marker.alive(time.time())]
                live.update(self.render(console))
                time.sleep(1 / self.fps)

    def drain_events(self) -> None:
        while True:
            try:
                message = self.event_queue.get_nowait()
            except Empty:
                return

            if isinstance(message, StatusEvent):
                self.statuses.appendleft(message)
                continue

            packet = message
            self.captured_packets += 1
            geo_result = self.geo.lookup(packet.dst_ip)
            coords = geo_result.point if geo_result else None
            country = geo_result.country if geo_result else "GeoIP miss"
            if geo_result is None:
                self.geo_misses += 1

            event = ConnectionEvent(
                src_ip=packet.src_ip,
                dst_ip=packet.dst_ip,
                coords=coords,
                country=country,
                protocol=packet.protocol,
                size=packet.size,
                interface=packet.interface,
                created_at=packet.created_at,
            )
            if event.coords is not None:
                self.markers.append(DestinationMarker(event.coords, event, time.time()))
                self.mapped_packets += 1
            self.recent.appendleft(event)

    def render(self, console: Console | None = None) -> Group:
        return Group(
            Panel(self.render_map(console), title="NetOrbit", border_style="cyan"),
            self.render_status(),
            self.render_connections(),
        )

    def render_map(self, console: Console | None = None) -> Text:
        width = max(72, min(144, (console.width - 4) if console else 100))
        height = max(18, min(36, round(width / 4)))
        markers = [MapMarker(marker.point) for marker in self.markers]
        return self.world_map.render_map(width=width, height=height, markers=markers, home=self.home)

    def render_connections(self) -> Panel:
        table = Table(expand=True, show_header=True, header_style="bold cyan")
        table.add_column("IP")
        table.add_column("Country")
        table.add_column("Proto", justify="center")
        table.add_column("Iface", justify="center")
        table.add_column("Size", justify="right")

        for event in self.recent:
            table.add_row(event.dst_ip, event.country, event.protocol, event.interface or "-", str(event.size))

        if not self.recent:
            table.add_row("-", "waiting for traffic", "-", "-", "-")

        return Panel(table, title="Last 10 connections", border_style="cyan")

    def render_status(self) -> Panel:
        text = Text()
        text.append(f"captured={self.captured_packets}  ", style="bold cyan")
        text.append(f"mapped={self.mapped_packets}  ", style="bold green")
        text.append(f"geo_miss={self.geo_misses}", style="yellow")

        for status in self.statuses:
            style = "red" if status.level == "error" else "bright_black"
            text.append(f"\n{status.message}", style=style)

        if not self.statuses:
            text.append("\nStarting sniffer...", style="bright_black")

        return Panel(text, title="Status", border_style="cyan")
