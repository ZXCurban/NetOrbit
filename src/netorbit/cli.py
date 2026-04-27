from __future__ import annotations

import argparse
import os
import shutil
import sys
from queue import Queue

from .geo_engine import GeoEngine
from .models import GeoPoint, GeoResult, NetOrbitEvent
from .sniffer import (
    DemoPacketSource,
    PacketSniffer,
    detect_capture_interfaces,
    list_ipv4_interfaces,
    run_source_in_thread,
)
from .ui import NetOrbitUI


DEMO_GEO = (
    GeoResult("1.1.1.1", GeoPoint(-33.8688, 151.2093), "Australia", "Sydney"),
    GeoResult("8.8.8.8", GeoPoint(37.3861, -122.0839), "United States", "Mountain View"),
    GeoResult("9.9.9.9", GeoPoint(47.3769, 8.5417), "Switzerland", "Zurich"),
    GeoResult("208.67.222.222", GeoPoint(37.7749, -122.4194), "United States", "San Francisco"),
    GeoResult("151.101.1.69", GeoPoint(40.7128, -74.0060), "United States", "New York"),
    GeoResult("185.199.108.133", GeoPoint(52.52, 13.405), "Germany", "Berlin"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NetOrbit: live terminal map for outgoing IPv4 traffic.")
    parser.add_argument("-i", "--interface", help="Network interface(s) to sniff, e.g. wlo1 or tun0,wlo1.")
    parser.add_argument("--home-lat", type=float, help="Home latitude. Defaults to local public IP geolocation.")
    parser.add_argument("--home-lon", type=float, help="Home longitude. Defaults to local public IP geolocation.")
    parser.add_argument("--fps", type=int, default=12, help="TUI refresh rate.")
    parser.add_argument("--demo", action="store_true", help="Use generated packet events instead of Scapy.")
    parser.add_argument("--list-interfaces", action="store_true", help="Print detected IPv4 interfaces and exit.")
    parser.add_argument(
        "--no-auto-sudo",
        action="store_true",
        help="Do not re-run through sudo when packet capture needs root privileges.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.list_interfaces:
        print_interfaces()
        return

    interfaces = [item.strip() for item in args.interface.split(",")] if args.interface else detect_capture_interfaces()
    ensure_capture_privileges(args, interfaces)

    queue: Queue[NetOrbitEvent] = Queue()
    geo = GeoEngine()
    home = resolve_home_point(args, geo)
    source = DemoPacketSource() if args.demo else PacketSniffer(interfaces)

    if args.demo:
        geo.prime(DEMO_GEO)

    run_source_in_thread(source, queue)
    ui = NetOrbitUI(
        event_queue=queue,
        geo=geo,
        home=home,
        fps=max(1, min(args.fps, 60)),
    )
    ui.run()


def ensure_capture_privileges(args: argparse.Namespace, interfaces: list[str]) -> None:
    if args.demo or args.no_auto_sudo:
        return
    if os.name != "posix" or not hasattr(os, "geteuid"):
        return
    if os.geteuid() == 0:
        return

    sudo = shutil.which("sudo")
    if sudo is None:
        print("Packet capture needs root privileges. Install sudo or run as root.", file=sys.stderr)
        return

    print("NetOrbit needs capture privileges; re-running through sudo...", file=sys.stderr)
    argv = list(sys.argv)
    if not args.interface and interfaces:
        argv.extend(["--interface", ",".join(interfaces)])
    os.execvp(sudo, [sudo, sys.executable, *argv])


def print_interfaces() -> None:
    interfaces = list_ipv4_interfaces()
    if not interfaces:
        print("No IPv4 interfaces detected.")
        return
    for name, address, selected in interfaces:
        marker = "*" if selected else " "
        print(f"{marker} {name:<14} {address}")


def resolve_home_point(args: argparse.Namespace, geo: GeoEngine) -> GeoPoint:
    detected = geo.lookup_self()
    fallback = GeoPoint(55.7558, 37.6173)
    base = detected.point if detected else fallback
    lat = args.home_lat if args.home_lat is not None else base.lat
    lon = args.home_lon if args.home_lon is not None else base.lon
    return GeoPoint(lat, lon)
