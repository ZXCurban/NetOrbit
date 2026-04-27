from __future__ import annotations

from math import acos, atan2, cos, degrees, pi, radians, sin, sqrt

from .models import GeoPoint


MAP_MIN_LAT = -90.0
MAP_MAX_LAT = 90.0


def project_lat_lon(
    point: GeoPoint,
    width: int,
    height: int,
    min_lat: float = MAP_MIN_LAT,
    max_lat: float = MAP_MAX_LAT,
) -> tuple[int, int]:
    """Project latitude/longitude into terminal character coordinates."""
    x = int((point.lon + 180.0) / 360.0 * max(width, 1))
    lat = max(min_lat, min(max_lat, point.lat))
    y = int((max_lat - lat) / (max_lat - min_lat) * max(height, 1))
    return clamp(x, 0, width - 1), clamp(y, 0, height - 1)


def bezier_arc(
    start: tuple[int, int],
    end: tuple[int, int],
    steps: int = 32,
    lift: float = 0.22,
) -> list[tuple[int, int]]:
    """Return a raised quadratic Bezier arc between two screen points."""
    if steps < 2:
        return [start, end]

    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    distance = max(abs(dx), abs(dy), 1)
    control = (
        sx + dx / 2,
        min(sy, ey) - distance * lift - 2,
    )

    points: list[tuple[int, int]] = []
    for index in range(steps):
        t = index / (steps - 1)
        inv = 1.0 - t
        wave = sin(t * pi) * 0.35
        x = inv * inv * sx + 2 * inv * t * control[0] + t * t * ex
        y = inv * inv * sy + 2 * inv * t * control[1] + t * t * ey - wave
        point = (int(round(x)), int(round(y)))
        if not points or points[-1] != point:
            points.append(point)
    return points


def great_circle_points(start: GeoPoint, end: GeoPoint, steps: int = 48) -> list[GeoPoint]:
    """Return points along the shortest route on the globe."""
    if steps < 2:
        return [start, end]

    lat1 = radians(start.lat)
    lon1 = radians(start.lon)
    lat2 = radians(end.lat)
    lon2 = radians(end.lon)

    x1, y1, z1 = _to_cartesian(lat1, lon1)
    x2, y2, z2 = _to_cartesian(lat2, lon2)
    dot = max(-1.0, min(1.0, x1 * x2 + y1 * y2 + z1 * z2))
    angle = acos(dot)

    if angle == 0:
        return [start for _ in range(steps)]

    points: list[GeoPoint] = []
    divisor = sin(angle)
    for index in range(steps):
        t = index / (steps - 1)
        a = sin((1 - t) * angle) / divisor
        b = sin(t * angle) / divisor
        x = a * x1 + b * x2
        y = a * y1 + b * y2
        z = a * z1 + b * z2
        lat = atan2(z, sqrt(x * x + y * y))
        lon = atan2(y, x)
        points.append(GeoPoint(degrees(lat), degrees(lon)))

    return points


def great_circle_arc(
    start: GeoPoint,
    end: GeoPoint,
    width: int,
    height: int,
    steps: int = 64,
) -> list[tuple[int, int]]:
    """Project a great-circle route to terminal coordinates."""
    projected: list[tuple[int, int]] = []
    for point in great_circle_points(start, end, steps):
        screen_point = project_lat_lon(point, width, height)
        if not projected or projected[-1] != screen_point:
            projected.append(screen_point)
    return projected


def route_char(previous: tuple[int, int], current: tuple[int, int]) -> str:
    dx = current[0] - previous[0]
    dy = current[1] - previous[1]
    if abs(dx) > abs(dy) * 2:
        return "-"
    if abs(dy) > abs(dx) * 2:
        return "|"
    if dx * dy > 0:
        return "\\"
    return "/"


def _to_cartesian(lat: float, lon: float) -> tuple[float, float, float]:
    return cos(lat) * cos(lon), cos(lat) * sin(lon), sin(lat)


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))
