from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from queue import Empty, Queue

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from .models import ConnectionEvent, GeoPoint, NetOrbitEvent, StatusEvent
from .world_map import BallisticTrajectory, MapMarker, WorldMap


PANEL_HORIZONTAL_CHROME = 4
PANEL_VERTICAL_CHROME = 2
MIN_MAP_PANEL_WIDTH = 52
MIN_MAP_PANEL_HEIGHT = 12
MIN_SIDE_CONNECTIONS_WIDTH = 42
MAX_SIDE_CONNECTIONS_WIDTH = 58
CONNECTIONS_PANEL_HEIGHT = 13
MAX_ACTIVE_MARKERS = 96
MAX_EVENTS_PER_FRAME = 128
DESTINATION_MARKER_STYLE = Style(color="#fbbf24", bold=True)
DESTINATION_ARRIVAL_STYLE = Style(color="#00FFFF", bold=True)
DESTINATION_REACHED_STYLE = Style(color="#34d399", bold=True)


@dataclass(slots=True)
class DestinationMarker:
    point: GeoPoint
    event: ConnectionEvent
    started_at: float
    ttl: float = 8.0
    grow_duration: float = 1.8
    arrival_flash: float = 0.7

    def age(self, now: float) -> float:
        return max(0.0, now - self.started_at)

    def progress(self, now: float) -> float:
        return min(1.0, self.age(now) / self.grow_duration)

    def fade(self, now: float) -> float:
        age = self.age(now)
        if age <= self.grow_duration:
            return 1.0
        fade_duration = max(0.001, self.ttl - self.grow_duration)
        return min(1.0, max(0.0, 1.0 - ((age - self.grow_duration) / fade_duration)))

    def arrived(self, now: float) -> bool:
        age = self.age(now)
        return self.grow_duration <= age < self.grow_duration + self.arrival_flash

    def marker_style(self, now: float) -> Style:
        if self.arrived(now):
            return DESTINATION_ARRIVAL_STYLE
        if self.progress(now) >= 1.0:
            return DESTINATION_REACHED_STYLE
        return DESTINATION_MARKER_STYLE

    def alive(self, now: float) -> bool:
        return self.age(now) < self.ttl


def show_welcome() -> None:
    console = Console()
    welcome_text = Text("\nNetOrbit\n", style="bold cyan", justify="center")
    welcome_text.append("Real-time Network Traffic Visualizer\n", style="bright_black")
    welcome_text.append("\nPress Ctrl+C to exit", style="dim")

    panel = Panel(
        Align.center(welcome_text),
        border_style="cyan",
        expand=False,
    )
    console.print(Align.center(panel))
    time.sleep(2)


class NetOrbitUI:
    def __init__(
        self,
        event_queue: Queue[NetOrbitEvent],
        home: GeoPoint,
        fps: int = 12,
    ) -> None:
        self.event_queue = event_queue
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
        with Live(
            self.render(console),
            console=console,
            refresh_per_second=self.fps,
            screen=True,
        ) as live:
            while True:
                now = time.monotonic()
                self.drain_events()
                self.markers = [marker for marker in self.markers if marker.alive(now)]
                live.update(self.render(console))
                time.sleep(1 / self.fps)

    def drain_events(self) -> None:
        for _ in range(MAX_EVENTS_PER_FRAME):
            try:
                message = self.event_queue.get_nowait()
            except Empty:
                return

            if isinstance(message, StatusEvent):
                self.statuses.appendleft(message)
                continue

            if not isinstance(message, ConnectionEvent):
                continue

            self.captured_packets += 1
            if message.coords is None:
                self.geo_misses += 1

            if message.coords is not None:
                self.markers.append(DestinationMarker(message.coords, message, time.monotonic()))
                if len(self.markers) > MAX_ACTIVE_MARKERS:
                    del self.markers[: len(self.markers) - MAX_ACTIVE_MARKERS]
                self.mapped_packets += 1
            self.recent.appendleft(message)

    def render(self, console: Console | None = None) -> Group:
        width = max(24, console.size.width if console else 100)
        height = max(8, console.size.height if console else 32)
        status_height = min(self._status_height(), max(3, height - MIN_MAP_PANEL_HEIGHT))
        top_height = max(3, height - status_height)

        main_view = self.render_main_view(width=width, height=top_height)
        return Group(main_view, self.render_status(height=status_height))

    def render_main_view(self, width: int, height: int) -> Group | Table | Panel:
        can_place_side = (
            width >= MIN_MAP_PANEL_WIDTH + MIN_SIDE_CONNECTIONS_WIDTH
            and height >= CONNECTIONS_PANEL_HEIGHT
        )
        can_place_bottom = (
            width >= MIN_MAP_PANEL_WIDTH
            and height >= MIN_MAP_PANEL_HEIGHT + CONNECTIONS_PANEL_HEIGHT
        )

        if can_place_side:
            connections_width = min(
                MAX_SIDE_CONNECTIONS_WIDTH,
                max(MIN_SIDE_CONNECTIONS_WIDTH, round(width * 0.34)),
            )
            map_width = width - connections_width
            if map_width < MIN_MAP_PANEL_WIDTH:
                map_width = MIN_MAP_PANEL_WIDTH
                connections_width = width - map_width

            layout = Table.grid(expand=True)
            layout.add_column(width=map_width)
            layout.add_column(width=connections_width)
            layout.add_row(
                self.render_map_panel(width=map_width, height=height),
                self.render_connections(width=connections_width, height=height),
            )
            return layout

        if can_place_bottom:
            map_height = height - CONNECTIONS_PANEL_HEIGHT
            return Group(
                self.render_map_panel(width=width, height=map_height),
                self.render_connections(width=width, height=CONNECTIONS_PANEL_HEIGHT),
            )

        return self.render_map_panel(width=width, height=height)

    def render_map_panel(self, width: int, height: int) -> Panel:
        map_width = max(1, width - PANEL_HORIZONTAL_CHROME)
        map_height = max(1, height - PANEL_VERTICAL_CHROME)
        return Panel(
            self.render_map(width=map_width, height=map_height),
            title="NetOrbit",
            border_style="#38bdf8",
            width=width,
            height=height,
        )

    def render_map(
        self,
        console: Console | None = None,
        *,
        width: int | None = None,
        height: int | None = None,
    ) -> Text:
        if width is None:
            width = max(48, min(144, (console.width - PANEL_HORIZONTAL_CHROME) if console else 100))
        if height is None:
            height = max(12, min(36, round(width / 4)))
        now = time.monotonic()
        markers = [
            MapMarker(marker.point, style=marker.marker_style(now))
            for marker in self.markers
        ]
        trajectories = [
            BallisticTrajectory(
                start=self.home,
                end=marker.point,
                progress=marker.progress(now),
                fade=marker.fade(now),
            )
            for marker in self.markers
        ]
        return self.world_map.render_map(
            width=width,
            height=height,
            markers=markers,
            trajectories=trajectories,
            home=self.home,
        )

    def render_connections(self, width: int | None = None, height: int | None = None) -> Panel:
        table = Table(
            expand=True,
            show_edge=False,
            box=None,
            pad_edge=False,
            collapse_padding=True,
            show_header=True,
            header_style="bold #67e8f9",
            row_styles=("", "dim"),
        )
        table.add_column("IP", overflow="fold")
        table.add_column("Country")
        table.add_column("Proto", justify="center")
        table.add_column("Iface", justify="center")
        table.add_column("Size", justify="right")

        for event in self.recent:
            table.add_row(
                event.dst_ip,
                event.country,
                event.protocol,
                event.interface or "-",
                str(event.size),
            )

        if not self.recent:
            table.add_row("-", "waiting for traffic", "-", "-", "-")

        return Panel(
            table,
            title="Last 10 connections",
            border_style="#38bdf8",
            width=width,
            height=height,
        )

    def render_status(self, height: int | None = None) -> Panel:
        text = Text()
        text.append(f"captured={self.captured_packets}  ", style="bold #67e8f9")
        text.append(f"mapped={self.mapped_packets}  ", style="bold #34d399")
        text.append(f"geo_miss={self.geo_misses}", style="#fbbf24")

        for status in self.statuses:
            style = "red" if status.level == "error" else "bright_black"
            text.append(f"\n{status.message}", style=style)

        if not self.statuses:
            text.append("\nStarting sniffer...", style="bright_black")

        return Panel(text, title="Status", border_style="#38bdf8", height=height)

    def _status_height(self) -> int:
        status_lines = max(1, len(self.statuses))
        return 1 + min(status_lines, self.statuses.maxlen or status_lines) + PANEL_VERTICAL_CHROME
