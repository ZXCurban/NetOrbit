from __future__ import annotations

import base64
import zlib
from dataclasses import dataclass
from functools import lru_cache
from math import ceil, pi, sin
from typing import Iterable

from rich.style import Style
from rich.text import Text

from .models import GeoPoint


MASK_WIDTH = 360
MASK_HEIGHT = 180
WORLD_MIN_LAT = -90.0
WORLD_MAX_LAT = 90.0
WORLD_MIN_LON = -180.0
WORLD_MAX_LON = 180.0

BRAILLE_BITS = (
    (0x01, 0x08),
    (0x02, 0x10),
    (0x04, 0x20),
    (0x40, 0x80),
)
VIRTUAL_DOT_WIDTH = 2
VIRTUAL_DOT_HEIGHT = 4
BRAILLE_BASE = 0x2800
BRAILLE_CHARS = tuple(chr(BRAILLE_BASE + pattern) for pattern in range(256))
TRAJECTORY_EDGE_COLOR = "#00FFFF"
TRAJECTORY_TRAIL_COLOR = "#333333"
BACKGROUND_STYLE = Style(color="#0f172a")
GRID_STYLE = Style(color="#1d4ed8", dim=True)
LAND_STYLE = Style(color="#2f7d5f")
COAST_STYLE = Style(color="#8bd8bd")
TRAJECTORY_EDGE_STYLE = Style(color=TRAJECTORY_EDGE_COLOR, bold=True)
TRAJECTORY_STYLES = (
    Style(color=TRAJECTORY_TRAIL_COLOR, dim=True),
    Style(color="#4b5563"),
    Style(color="#64748b"),
    Style(color="#94a3b8"),
    Style(color="#67e8f9", bold=True),
)
HOME_STYLE = Style(color="#fb7185", bold=True)
MARKER_STYLE = Style(color="#fbbf24", bold=True)

# Natural Earth 1:110m land polygons rasterized to a 360x180 bit-mask.
# The same equirectangular projection is used by geo_to_canvas().
LAND_MASK_B85 = """
c-rlmJ8vCD6o6;%TAman6Dds)md8azg@h#vTv*<8{0(=MxFbSIW>ApQpxibE!bnIo`~fOF5(qa)<_93Mi4mrV<c(5f6R-Dh_A&3-8($DzMzVDu-<>&gUUTLwA#X-{G>{VlkX?jr0S*fMCoaI2V21bkl@weXmf^c|oWEZ}6$y3?Vczy|)-7Wgpb>kkLGav2p@cyy9<tRoxziNY0HaRGPLD|ZyLmT+;q(}wP<DUUhmTRBBf#HPu0DT;lYV2Zr;LVm%J0Ol`sIe9#9djz@RehgtwH<O5SZJkC47I>Pg#32b21wg%9NuL1>!`sIAym*qclaO7<R!`zZ@m9S1ZgB=KahATzBxeW7tO(Wu(keOiuPo5U)_n&dl8o)|GVupc`doUE&b8*1>cT3`LiZ92oUQHC(i(hmb41Ka}U_7{c+neR+7!%W>jPhx-xR8AFe(EfCJPicXiwab{nZa9QH^>Y@|*xp*0|W$Eoeq7<E*l@Oyi&)mFz&T7_qugnRlQbGt~RVmL7DQO3Xfg%Z)c99z6s2LmvcmmG51=|rW#al#;u!yGZ_Pqh0$`Muw>tHCF2%dEg%LXqNHcD0YfCn)7qW`XB<0esWV}2>~inYPsWdGgvY_u0TZK2_sg(_BJ2nTK4V;Cc?&g*Y|m<`FM^L=G3KX_5gBBRVC)A7^jnb{cCk&dZ><+*mi;gdg#1e`}nk&js<8mltSplf0FHE^7pKOFN~3_Dp`2L=;k8i~d%hUdbaxv*9&R$~}$>Z7P%XE7{@h0lOmnB_6NKD@ou;32RH_Z&6z2-b@=@Zt>6Lo9qR0c$BlbqcpCYJ6I_DK~_Rhh3Iq*03^*VEyxkZ#Aa~o0+-F-2=!RQ-h0cJv?#X7u213gfn~aFn8uTD>MI)cMg;05a^Ku7rf5A>cNHa99Ve(Hh1v#SMe$Dz-0Re$0T1v1Pl8PU;gHV>n|cIHn<~Ho;iNXDz7q7y3Ww>eeS@;o_Eko*Cu@d<fWKhA3h7<ARh%a1RQ)seG|daG>lerH-O`jpCDWlQnKU02Ucztz`rAW+e-`wAhfw@RH#w%o-UXMhX?U=gg*!?Duj2#{G^MfcLI2~%_a9>6he%8dD~!{qt&Pqo(pzW9_g)9T(WMV;dNb)8Cal_?t97@Bc@^NW#P&E5{-c+8We7150Tf*IcYukSr2EhpGU<gmUU%IUHBN+uYj}%*;WWE&qK$Gf>Z@*1&Ltd#H%i_NDo5-mL?O79(pSJ<F|zD`U1GI&Njex;(`#uxLq{`S9;eYEOrOD&8qk|QfBa(=SV0so~yeJ`7;4u8#71c!?(y^Sz?Ey_DUOi=!xYf`6;#`IUVz;a^jSCj`lbKKOHl)bmDXiYap3|l}>j~oL)yqllRgvjK1vz^;fi{Bn@Z7C8f1+O{;w3-j+GpU|{xGle!^R_6#cR5mPb9FQ+egxsy6Z;jmzufSHAbfzQ88-C<3_bS^iN!JWVJB&-E>awl)M)frhyT}+wTppMC+-T4vnE2)_aqjC-JsO|57uchEY4(TM?EzHHQ4&J{QT+eQhC-8CdGM#B((r|_HJP|67Etr6%5UZG(uB7ht5lp^0pyVW5OTp%JvzhkSE`4stE~<^(dTCi@v)N_>F6_)#?V6mX!h3|fm(0#pvNX&sY?J2;#$E&SZTkhok5@?+n$W^?djSXD!78$fh3^-RPVwWFy#=s2L_4^!C#GW+W>jb4D%I5~t&#C-bB*b<2$9($Sb4=twg7G&xEeAJjp5wF)Q4l4g%wkJFiYewX6#ce19Lxu_yyr|3N|6_tovHHx(J**)tDDSDL6B;<;%dC1J9GH6IM<)kh3=K+SLy1l)+f=H9$kRtF2^`c=cJ`Z6S}U*Yr>wOoN;|1<MY8H}0ZNz$oxe08e&XZw&nk7cM4StXSyEbsy%FaNQSIUa>X}R|xwXYT0zBH)wYvOc!;A>t*2EL7}^_PrVbsbcsHAY`_IeLG($!47^|nnJ*!;S^{pDdMdDt>Z)bnH{(By|II4FEph1Rt&D%+@H3L)eJbMEAD_obLeii!aob$V;>5P$!h8Kq#57SpiPDHoUmHV#>^v8U`W8jlb9@F#y6l_ZVO#Xv>p@!;vlR`i^y32!S39$+@0A3PyS%||rC8b@H))s#Jtnq5iau*@NdJl46f1)MF)nm9>ScK|oq7wka*FL`UUz;giTmUxsX42h_Oas)5O(j0{{&}WiAj-pq}Fqo9$6Oy4P0#St`k$joAGbPKhacx69
""".strip()


@dataclass(frozen=True, slots=True)
class MapMarker:
    point: GeoPoint
    char: str = "●"
    style: Style = MARKER_STYLE


@dataclass(frozen=True, slots=True)
class CanvasCell:
    char: str
    style: Style


@dataclass(frozen=True, slots=True)
class BallisticTrajectory:
    start: GeoPoint
    end: GeoPoint
    progress: float = 1.0
    fade: float = 1.0


class BrailleCanvas:
    """High-resolution 2x4-dot overlay stored as Braille cell masks."""

    __slots__ = (
        "edges",
        "height",
        "intensities",
        "patterns",
        "virtual_height",
        "virtual_width",
        "width",
    )

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.virtual_width = width * VIRTUAL_DOT_WIDTH
        self.virtual_height = height * VIRTUAL_DOT_HEIGHT
        cell_count = width * height
        self.patterns = [0] * cell_count
        self.intensities = [0.0] * cell_count
        self.edges = [False] * cell_count

    def plot(self, x: int, y: int, intensity: float = 1.0, edge: bool = False) -> None:
        if not (0 <= x < self.virtual_width and 0 <= y < self.virtual_height):
            return

        char_x = x // VIRTUAL_DOT_WIDTH
        char_y = y // VIRTUAL_DOT_HEIGHT
        index = char_y * self.width + char_x
        self.patterns[index] |= BRAILLE_BITS[y % VIRTUAL_DOT_HEIGHT][x % VIRTUAL_DOT_WIDTH]
        if intensity > self.intensities[index]:
            self.intensities[index] = 1.0 if intensity > 1.0 else intensity
        if edge:
            self.edges[index] = True

    def composite_onto(self, canvas: list[list[CanvasCell]]) -> None:
        width = self.width
        for index, pattern in enumerate(self.patterns):
            if pattern:
                y, x = divmod(index, width)
                canvas[y][x] = CanvasCell(
                    BRAILLE_CHARS[pattern],
                    trajectory_style(self.intensities[index], self.edges[index]),
                )


class LandMask:
    __slots__ = ("data", "height", "width")

    def __init__(self, data: bytes, width: int, height: int) -> None:
        self.data = data
        self.width = width
        self.height = height

    def is_land_index(self, x: int, y: int) -> bool:
        index = y * self.width + x
        return bool(self.data[index // 8] & (1 << (index % 8)))


class WorldMap:
    __slots__ = ("home", "markers", "trajectories")

    background_style = BACKGROUND_STYLE
    grid_style = GRID_STYLE
    land_style = LAND_STYLE
    coast_style = COAST_STYLE
    home_style = HOME_STYLE

    def __init__(
        self,
        home: GeoPoint | None = None,
        markers: Iterable[MapMarker] | None = None,
        trajectories: Iterable[BallisticTrajectory] | None = None,
    ) -> None:
        self.home = home
        self.markers = list(markers or [])
        self.trajectories = list(trajectories or [])

    def render(self) -> Text:
        width, height = self._default_size()
        return self.render_map(width=width, height=height)

    def render_map(
        self,
        width: int | None = None,
        height: int | None = None,
        markers: Iterable[MapMarker] | None = None,
        trajectories: Iterable[BallisticTrajectory] | None = None,
        home: GeoPoint | None = None,
    ) -> Text:
        map_width = max(24, width or 100)
        map_height = max(8, height or max(8, round(map_width / 4)))
        canvas = self._base_canvas(map_width, map_height)

        self._draw_trajectories(
            canvas,
            trajectories if trajectories is not None else self.trajectories,
        )

        for marker in markers if markers is not None else self.markers:
            self._put_geo(canvas, marker.point, marker.char, marker.style)

        home_point = home if home is not None else self.home
        if home_point is not None:
            self._put_geo(canvas, home_point, "●", self.home_style)

        return self._to_text(canvas)

    def _default_size(self) -> tuple[int, int]:
        return 100, 25

    def _base_canvas(self, width: int, height: int) -> list[list[CanvasCell]]:
        return [list(row) for row in base_canvas_template(width, height)]

    def _draw_trajectories(
        self,
        canvas: list[list[CanvasCell]],
        trajectories: Iterable[BallisticTrajectory],
    ) -> None:
        width = len(canvas[0])
        height = len(canvas)
        layer = BrailleCanvas(width, height)

        for trajectory in trajectories:
            points = quadratic_bezier_virtual_points(
                trajectory.start,
                trajectory.end,
                width,
                height,
            )
            progress = clamp_float(trajectory.progress)
            fade = clamp_float(trajectory.fade)
            if not points or progress <= 0.0 or fade <= 0.0:
                continue

            visible_count = min(len(points), max(1, ceil(len(points) * progress)))
            denominator = max(1, visible_count - 1)
            for index in range(visible_count):
                x, y = points[index]
                position = index / denominator
                edge = progress < 1.0 and position >= 0.92
                intensity = fade * (0.16 + 0.84 * position)
                layer.plot(x, y, 1.0 if edge else intensity, edge=edge)

        layer.composite_onto(canvas)

    def _put_geo(
        self,
        canvas: list[list[CanvasCell]],
        point: GeoPoint,
        char: str,
        style: Style,
    ) -> None:
        width = len(canvas[0])
        height = len(canvas)
        x, y = geo_to_canvas(point.lat, point.lon, width, height)
        canvas[y][x] = CanvasCell(char, style)

    def _to_text(self, canvas: list[list[CanvasCell]]) -> Text:
        text = Text()
        for index, row in enumerate(canvas):
            if row:
                run_style = row[0].style
                run_chars: list[str] = []
                for cell in row:
                    if cell.style == run_style:
                        run_chars.append(cell.char)
                        continue
                    text.append("".join(run_chars), style=run_style)
                    run_style = cell.style
                    run_chars = [cell.char]
                text.append("".join(run_chars), style=run_style)
            if index < len(canvas) - 1:
                text.append("\n")
        return text


@lru_cache(maxsize=32)
def base_canvas_template(width: int, height: int) -> tuple[tuple[CanvasCell, ...], ...]:
    background = CanvasCell(" ", BACKGROUND_STYLE)
    canvas = [[background for _ in range(width)] for _ in range(height)]
    draw_grid(canvas, width, height)
    draw_land(canvas, width, height)
    return tuple(tuple(row) for row in canvas)


def draw_grid(canvas: list[list[CanvasCell]], width: int, height: int) -> None:
    vertical = CanvasCell("│", GRID_STYLE)
    horizontal = CanvasCell("─", GRID_STYLE)
    crossing = CanvasCell("┼", GRID_STYLE)

    for lon in range(-150, 181, 30):
        x, _ = geo_to_canvas(0, lon, width, height)
        for y in range(height):
            canvas[y][x] = vertical

    for lat in range(-60, 91, 30):
        _, y = geo_to_canvas(lat, 0, width, height)
        row = canvas[y]
        for x in range(width):
            row[x] = crossing if row[x].char == "│" else horizontal


def draw_land(canvas: list[list[CanvasCell]], width: int, height: int) -> None:
    mask = land_mask()
    x_lookup = scaled_indices(width * VIRTUAL_DOT_WIDTH, mask.width)
    y_lookup = scaled_indices(height * VIRTUAL_DOT_HEIGHT, mask.height)

    full_land = CanvasCell(BRAILLE_CHARS[0xFF], LAND_STYLE)
    for char_y in range(height):
        virtual_y = char_y * VIRTUAL_DOT_HEIGHT
        row = canvas[char_y]
        for char_x in range(width):
            virtual_x = char_x * VIRTUAL_DOT_WIDTH
            pattern = 0
            if mask.is_land_index(x_lookup[virtual_x], y_lookup[virtual_y]):
                pattern |= 0x01
            if mask.is_land_index(x_lookup[virtual_x + 1], y_lookup[virtual_y]):
                pattern |= 0x08
            if mask.is_land_index(x_lookup[virtual_x], y_lookup[virtual_y + 1]):
                pattern |= 0x02
            if mask.is_land_index(x_lookup[virtual_x + 1], y_lookup[virtual_y + 1]):
                pattern |= 0x10
            if mask.is_land_index(x_lookup[virtual_x], y_lookup[virtual_y + 2]):
                pattern |= 0x04
            if mask.is_land_index(x_lookup[virtual_x + 1], y_lookup[virtual_y + 2]):
                pattern |= 0x20
            if mask.is_land_index(x_lookup[virtual_x], y_lookup[virtual_y + 3]):
                pattern |= 0x40
            if mask.is_land_index(x_lookup[virtual_x + 1], y_lookup[virtual_y + 3]):
                pattern |= 0x80
            if pattern == 0xFF:
                row[char_x] = full_land
            elif pattern:
                row[char_x] = CanvasCell(BRAILLE_CHARS[pattern], COAST_STYLE)


@lru_cache(maxsize=64)
def scaled_indices(source_size: int, target_size: int) -> tuple[int, ...]:
    return tuple(
        min(target_size - 1, int(((index + 0.5) / source_size) * target_size))
        for index in range(source_size)
    )


def geo_to_canvas(lat: float, lon: float, map_width: int, map_height: int) -> tuple[int, int]:
    """Map GPS coordinates to a terminal character grid using equirectangular projection."""
    normalized_lon = ((lon - WORLD_MIN_LON) % 360.0) + WORLD_MIN_LON
    if normalized_lon == WORLD_MIN_LON and lon > 0:
        normalized_lon = WORLD_MAX_LON
    clamped_lat = max(WORLD_MIN_LAT, min(WORLD_MAX_LAT, lat))
    x = int((normalized_lon - WORLD_MIN_LON) / (WORLD_MAX_LON - WORLD_MIN_LON) * map_width)
    y = int((WORLD_MAX_LAT - clamped_lat) / (WORLD_MAX_LAT - WORLD_MIN_LAT) * map_height)
    return clamp(x, 0, map_width - 1), clamp(y, 0, map_height - 1)


def map_geo_to_virtual_canvas(
    lat: float,
    lon: float,
    map_width: int,
    map_height: int,
) -> tuple[int, int]:
    """Map GPS coordinates to the Braille overlay's 2x4 virtual-dot grid."""
    virtual_width = max(1, map_width * VIRTUAL_DOT_WIDTH)
    virtual_height = max(1, map_height * VIRTUAL_DOT_HEIGHT)
    normalized_lon = ((lon - WORLD_MIN_LON) % 360.0) + WORLD_MIN_LON
    if normalized_lon == WORLD_MIN_LON and lon > 0:
        normalized_lon = WORLD_MAX_LON
    clamped_lat = max(WORLD_MIN_LAT, min(WORLD_MAX_LAT, lat))
    x = int((normalized_lon - WORLD_MIN_LON) / (WORLD_MAX_LON - WORLD_MIN_LON) * virtual_width)
    y = int((WORLD_MAX_LAT - clamped_lat) / (WORLD_MAX_LAT - WORLD_MIN_LAT) * virtual_height)
    return clamp(x, 0, virtual_width - 1), clamp(y, 0, virtual_height - 1)


def quadratic_bezier_virtual_points(
    start: GeoPoint,
    end: GeoPoint,
    map_width: int,
    map_height: int,
    lift: float = 0.22,
) -> tuple[tuple[int, int], ...]:
    """Return a dense virtual-dot quadratic Bezier arc."""
    return _quadratic_bezier_virtual_points(
        start.lat,
        start.lon,
        end.lat,
        end.lon,
        map_width,
        map_height,
        lift,
    )


@lru_cache(maxsize=2048)
def _quadratic_bezier_virtual_points(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    map_width: int,
    map_height: int,
    lift: float,
) -> tuple[tuple[int, int], ...]:
    virtual_width = max(1, map_width * VIRTUAL_DOT_WIDTH)
    virtual_height = max(1, map_height * VIRTUAL_DOT_HEIGHT)
    start_point = map_geo_to_virtual_canvas(start_lat, start_lon, map_width, map_height)
    end_point = map_geo_to_virtual_canvas(end_lat, end_lon, map_width, map_height)
    sx, sy = start_point
    ex, ey = _unwrap_x_for_shortest_path(sx, end_point[0], virtual_width), end_point[1]
    dx = ex - sx
    dy = ey - sy
    distance = max(abs(dx), abs(dy), 1)
    control_x = sx + dx / 2
    control_y = min(sy, ey) - distance * lift - VIRTUAL_DOT_HEIGHT
    samples = max(16, int(distance * 2.5))

    points: list[tuple[int, int]] = []
    previous: tuple[int, int] | None = None
    for index in range(samples + 1):
        t = index / samples
        inv = 1.0 - t
        wave = sin(t * pi) * 0.35
        x = inv * inv * sx + 2 * inv * t * control_x + t * t * ex
        y = inv * inv * sy + 2 * inv * t * control_y + t * t * ey - wave
        current = (round(x) % virtual_width, clamp(round(y), 0, virtual_height - 1))

        if previous is None:
            points.append(current)
        elif current != previous:
            points.extend(virtual_line_points(previous, current, virtual_width)[1:])
        previous = current

    return tuple(points)


def virtual_line_points(
    start: tuple[int, int],
    end: tuple[int, int],
    virtual_width: int,
) -> list[tuple[int, int]]:
    """Fill any rounding gaps between two virtual-dot coordinates."""
    sx, sy = start
    ex = _unwrap_x_for_shortest_path(sx, end[0], virtual_width)
    ey = end[1]
    dx = ex - sx
    dy = ey - sy
    steps = max(abs(dx), abs(dy), 1)
    points: list[tuple[int, int]] = []
    for index in range(steps + 1):
        t = index / steps
        x = round(sx + dx * t) % virtual_width
        y = round(sy + dy * t)
        point = (x, y)
        if not points or points[-1] != point:
            points.append(point)
    return points


def trajectory_style(intensity: float, edge: bool = False) -> Style:
    if edge:
        return TRAJECTORY_EDGE_STYLE

    value = clamp_float(intensity)
    if value < 0.35:
        return TRAJECTORY_STYLES[0]
    if value < 0.55:
        return TRAJECTORY_STYLES[1]
    if value < 0.74:
        return TRAJECTORY_STYLES[2]
    if value < 0.88:
        return TRAJECTORY_STYLES[3]
    return TRAJECTORY_STYLES[4]


def _unwrap_x_for_shortest_path(start_x: int, end_x: int, virtual_width: int) -> int:
    if virtual_width <= 1:
        return end_x

    delta = end_x - start_x
    half_width = virtual_width / 2
    if delta > half_width:
        return end_x - virtual_width
    if delta < -half_width:
        return end_x + virtual_width
    return end_x


@lru_cache(maxsize=1)
def land_mask() -> LandMask:
    data = zlib.decompress(base64.b85decode(LAND_MASK_B85.encode("ascii")))
    return LandMask(data, MASK_WIDTH, MASK_HEIGHT)


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def clamp_float(value: float) -> float:
    return max(0.0, min(1.0, value))
