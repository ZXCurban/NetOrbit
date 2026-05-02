from __future__ import annotations

import random
import subprocess
import threading
import time
from queue import Empty, Full, Queue
from typing import Any, Iterable, Iterator

from .geo_engine import GeoEngine, is_public_ipv4
from .models import ConnectionEvent, NetOrbitEvent, PacketEvent, StatusEvent


PROTOCOL_NAMES = {
    1: "ICMP",
    6: "TCP",
    17: "UDP",
}
PACKET_QUEUE_SIZE = 2048
UI_QUEUE_SIZE = 1024


class PacketSniffer:
    __slots__ = ("interfaces",)

    def __init__(self, interfaces: str | Iterable[str] | None = None) -> None:
        self.interfaces = normalize_interfaces(interfaces) or detect_capture_interfaces()

    def events(self) -> Iterator[PacketEvent]:
        queue: Queue[PacketEvent] = Queue(maxsize=PACKET_QUEUE_SIZE)

        try:
            from scapy.all import AsyncSniffer, IP  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Scapy is not installed. Run `pip install -r requirements.txt`."
            ) from exc

        def on_packet(packet: object) -> None:
            if IP not in packet:  # type: ignore[operator]
                return
            ip_layer = packet[IP]  # type: ignore[index]
            dst_ip = str(ip_layer.dst)
            if not is_public_ipv4(dst_ip):
                return
            event = PacketEvent(
                src_ip=str(ip_layer.src),
                dst_ip=dst_ip,
                protocol=PROTOCOL_NAMES.get(int(ip_layer.proto), str(ip_layer.proto)),
                size=len(packet),  # type: ignore[arg-type]
                interface=str(getattr(packet, "sniffed_on", "") or ""),
            ).with_timestamp()
            try:
                queue.put_nowait(event)
            except Full:
                return

        sniffer = AsyncSniffer(
            iface=self.interfaces or None,
            prn=on_packet,
            store=False,
        )
        sniffer.start()

        try:
            while True:
                yield queue.get()
        finally:
            try:
                sniffer.stop()
            except Exception:
                pass


class DemoPacketSource:
    __slots__ = ("interval", "source_ip")

    EXAMPLES = (
        ("1.1.1.1", "TCP", 764),
        ("8.8.8.8", "UDP", 128),
        ("9.9.9.9", "UDP", 256),
        ("208.67.222.222", "TCP", 1024),
        ("151.101.1.69", "TCP", 1400),
        ("185.199.108.133", "TCP", 1200),
    )

    def __init__(self, source_ip: str = "192.168.1.5", interval: float = 0.75) -> None:
        self.source_ip = source_ip
        self.interval = interval

    def events(self) -> Iterator[PacketEvent]:
        while True:
            dst_ip, protocol, base_size = random.choice(self.EXAMPLES)
            yield PacketEvent(
                src_ip=self.source_ip,
                dst_ip=dst_ip,
                protocol=protocol,
                size=base_size + random.randint(0, 900),
                interface="demo",
            ).with_timestamp()
            time.sleep(self.interval)


def run_source_pipeline(
    source: object,
    queue: Queue[NetOrbitEvent],
    geo: GeoEngine,
) -> tuple[threading.Thread, threading.Thread]:
    packet_queue: Queue[PacketEvent | StatusEvent] = Queue(maxsize=UI_QUEUE_SIZE)
    source_thread = run_source_in_thread(source, packet_queue)
    resolver_thread = threading.Thread(
        target=_resolve_packets,
        args=(packet_queue, queue, geo),
        daemon=True,
        name="netorbit-geo",
    )
    resolver_thread.start()
    return source_thread, resolver_thread


def run_source_in_thread(
    source: object,
    queue: Queue[PacketEvent | StatusEvent],
) -> threading.Thread:
    def worker() -> None:
        try:
            interfaces = getattr(source, "interfaces", None)
            if interfaces:
                put_latest(
                    queue,
                    StatusEvent(f"Listening on: {', '.join(interfaces)}").with_timestamp(),
                )
            for event in source.events():  # type: ignore[attr-defined]
                put_latest(queue, event)
        except Exception as exc:
            put_latest(
                queue,
                StatusEvent(
                    f"Sniffer stopped: {type(exc).__name__}: {exc}",
                    "error",
                ).with_timestamp(),
            )

    thread = threading.Thread(target=worker, daemon=True, name="netorbit-sniffer")
    thread.start()
    return thread


def _resolve_packets(
    packet_queue: Queue[PacketEvent | StatusEvent],
    queue: Queue[NetOrbitEvent],
    geo: GeoEngine,
) -> None:
    while True:
        event = packet_queue.get()
        if isinstance(event, StatusEvent):
            put_latest(queue, event)
            continue

        result = geo.lookup(event.dst_ip)
        put_latest(
            queue,
            ConnectionEvent(
                src_ip=event.src_ip,
                dst_ip=event.dst_ip,
                coords=result.point if result else None,
                country=result.country if result else "GeoIP miss",
                protocol=event.protocol,
                size=event.size,
                interface=event.interface,
                created_at=event.created_at,
            ),
        )


def put_latest(queue: Queue[Any], item: object) -> None:
    try:
        queue.put_nowait(item)
        return
    except Full:
        pass

    try:
        queue.get_nowait()
    except Empty:
        pass
    try:
        queue.put_nowait(item)
    except Full:
        pass


def normalize_interfaces(interfaces: str | Iterable[str] | None) -> list[str]:
    if interfaces is None:
        return []
    if isinstance(interfaces, str):
        raw = interfaces.replace(";", ",").split(",")
    else:
        raw = list(interfaces)
    normalized: list[str] = []
    for interface in raw:
        name = str(interface).strip()
        if name and name != "lo" and name not in normalized:
            normalized.append(name)
    return normalized


def detect_capture_interfaces() -> list[str]:
    """Find interfaces worth sniffing: policy route first, then normal default route."""
    interfaces: list[str] = []
    for detector in (
        _detect_interface_with_ip_route,
        _detect_main_default_interface,
        _detect_interface_with_scapy,
    ):
        interface = detector()
        if interface and interface != "lo" and interface not in interfaces:
            interfaces.append(interface)
        if len(interfaces) >= 2:
            break
    return interfaces


def list_ipv4_interfaces() -> list[tuple[str, str, bool]]:
    """Return available IPv4 interfaces as (name, address, selected_for_capture)."""
    selected = set(detect_capture_interfaces())
    try:
        result = subprocess.run(
            ["ip", "-brief", "-4", "addr"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    interfaces: list[tuple[str, str, bool]] = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[0] == "lo":
            continue
        interfaces.append((parts[0], parts[2], parts[0] in selected))
    return interfaces


def _detect_main_default_interface() -> str | None:
    try:
        result = subprocess.run(
            ["ip", "-4", "route", "show", "default"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    for line in result.stdout.splitlines():
        parts = line.split()
        if "dev" not in parts:
            continue
        dev_index = parts.index("dev") + 1
        if dev_index < len(parts) and parts[dev_index] != "lo":
            return parts[dev_index]
    return None


def _detect_interface_with_scapy() -> str | None:
    try:
        from scapy.all import conf  # type: ignore
    except ImportError:
        return None

    try:
        route = conf.route.route("8.8.8.8")
    except Exception:
        return None

    if route and route[0] and route[0] != "lo":
        return str(route[0])
    return None


def _detect_interface_with_ip_route() -> str | None:
    try:
        result = subprocess.run(
            ["ip", "route", "get", "8.8.8.8"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    parts = result.stdout.split()
    if "dev" not in parts:
        return None
    dev_index = parts.index("dev") + 1
    if dev_index >= len(parts):
        return None
    interface = parts[dev_index]
    return None if interface == "lo" else interface
