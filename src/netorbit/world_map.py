from __future__ import annotations

import base64
import zlib
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Sequence

from rich.console import RenderableType
from rich.style import Style
from rich.text import Text

from .models import GeoPoint

try:
    from textual.widgets import Static
except ModuleNotFoundError:  # Rich-only runtime fallback.
    class Static:  # type: ignore[no-redef]
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass


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

# Natural Earth 1:110m land polygons rasterized to a 360x180 bit-mask.
# The same equirectangular projection is used by geo_to_canvas().
LAND_MASK_B85 = """
c-rlmJ8vCD6o6;%TAman6Dds)md8azg@h#vTv*<8{0(=MxFbSIW>ApQpxibE!bnIo`~fOF5(qa)<_93Mi4mrV<c(5f6R-Dh_A&3-8($DzMzVDu-<>&gUUTLwA#X-{G>{VlkX?jr0S*fMCoaI2V21bkl@weXmf^c|oWEZ}6$y3?Vczy|)-7Wgpb>kkLGav2p@cyy9<tRoxziNY0HaRGPLD|ZyLmT+;q(}wP<DUUhmTRBBf#HPu0DT;lYV2Zr;LVm%J0Ol`sIe9#9djz@RehgtwH<O5SZJkC47I>Pg#32b21wg%9NuL1>!`sIAym*qclaO7<R!`zZ@m9S1ZgB=KahATzBxeW7tO(Wu(keOiuPo5U)_n&dl8o)|GVupc`doUE&b8*1>cT3`LiZ92oUQHC(i(hmb41Ka}U_7{c+neR+7!%W>jPhx-xR8AFe(EfCJPicXiwab{nZa9QH^>Y@|*xp*0|W$Eoeq7<E*l@Oyi&)mFz&T7_qugnRlQbGt~RVmL7DQO3Xfg%Z)c99z6s2LmvcmmG51=|rW#al#;u!yGZ_Pqh0$`Muw>tHCF2%dEg%LXqNHcD0YfCn)7qW`XB<0esWV}2>~inYPsWdGgvY_u0TZK2_sg(_BJ2nTK4V;Cc?&g*Y|m<`FM^L=G3KX_5gBBRVC)A7^jnb{cCk&dZ><+*mi;gdg#1e`}nk&js<8mltSplf0FHE^7pKOFN~3_Dp`2L=;k8i~d%hUdbaxv*9&R$~}$>Z7P%XE7{@h0lOmnB_6NKD@ou;32RH_Z&6z2-b@=@Zt>6Lo9qR0c$BlbqcpCYJ6I_DK~_Rhh3Iq*03^*VEyxkZ#Aa~o0+-F-2=!RQ-h0cJv?#X7u213gfn~aFn8uTD>MI)cMg;05a^Ku7rf5A>cNHa99Ve(Hh1v#SMe$Dz-0Re$0T1v1Pl8PU;gHV>n|cIHn<~Ho;iNXDz7q7y3Ww>eeS@;o_Eko*Cu@d<fWKhA3h7<ARh%a1RQ)seG|daG>lerH-O`jpCDWlQnKU02Ucztz`rAW+e-`wAhfw@RH#w%o-UXMhX?U=gg*!?Duj2#{G^MfcLI2~%_a9>6he%8dD~!{qt&Pqo(pzW9_g)9T(WMV;dNb)8Cal_?t97@Bc@^NW#P&E5{-c+8We7150Tf*IcYukSr2EhpGU<gmUU%IUHBN+uYj}%*;WWE&qK$Gf>Z@*1&Ltd#H%i_NDo5-mL?O79(pSJ<F|zD`U1GI&Njex;(`#uxLq{`S9;eYEOrOD&8qk|QfBa(=SV0so~yeJ`7;4u8#71c!?(y^Sz?Ey_DUOi=!xYf`6;#`IUVz;a^jSCj`lbKKOHl)bmDXiYap3|l}>j~oL)yqllRgvjK1vz^;fi{Bn@Z7C8f1+O{;w3-j+GpU|{xGle!^R_6#cR5mPb9FQ+egxsy6Z;jmzufSHAbfzQ88-C<3_bS^iN!JWVJB&-E>awl)M)frhyT}+wTppMC+-T4vnE2)_aqjC-JsO|57uchEY4(TM?EzHHQ4&J{QT+eQhC-8CdGM#B((r|_HJP|67Etr6%5UZG(uB7ht5lp^0pyVW5OTp%JvzhkSE`4stE~<^(dTCi@v)N_>F6_)#?V6mX!h3|fm(0#pvNX&sY?J2;#$E&SZTkhok5@?+n$W^?djSXD!78$fh3^-RPVwWFy#=s2L_4^!C#GW+W>jb4D%I5~t&#C-bB*b<2$9($Sb4=twg7G&xEeAJjp5wF)Q4l4g%wkJFiYewX6#ce19Lxu_yyr|3N|6_tovHHx(J**)tDDSDL6B;<;%dC1J9GH6IM<)kh3=K+SLy1l)+f=H9$kRtF2^`c=cJ`Z6S}U*Yr>wOoN;|1<MY8H}0ZNz$oxe08e&XZw&nk7cM4StXSyEbsy%FaNQSIUa>X}R|xwXYT0zBH)wYvOc!;A>t*2EL7}^_PrVbsbcsHAY`_IeLG($!47^|nnJ*!;S^{pDdMdDt>Z)bnH{(By|II4FEph1Rt&D%+@H3L)eJbMEAD_obLeii!aob$V;>5P$!h8Kq#57SpiPDHoUmHV#>^v8U`W8jlb9@F#y6l_ZVO#Xv>p@!;vlR`i^y32!S39$+@0A3PyS%||rC8b@H))s#Jtnq5iau*@NdJl46f1)MF)nm9>ScK|oq7wka*FL`UUz;giTmUxsX42h_Oas)5O(j0{{&}WiAj-pq}Fqo9$6Oy4P0#St`k$joAGbPKhacx69
""".strip()


@dataclass(frozen=True)
class MapMarker:
    point: GeoPoint
    char: str = "●"
    style: Style = Style(color="#0062ff", bold=True)


@dataclass(frozen=True)
class CanvasCell:
    char: str
    style: Style


class LandMask:
    def __init__(self, data: bytes, width: int, height: int) -> None:
        self.data = data
        self.width = width
        self.height = height

    def is_land(self, lat: float, lon: float) -> bool:
        x, y = geo_to_canvas(lat, lon, self.width, self.height)
        index = y * self.width + x
        return bool(self.data[index // 8] & (1 << (index % 8)))


class WorldMap(Static):
    background_style = Style(color="#222222")
    grid_style = Style(color="#0D3D18", dim=True)
    land_style = Style(color="#0A3F16")
    coast_style = Style(color="#1CA304")
    trajectory_style = Style(color="#58a6ff", bold=True)
    home_style = Style(color="#ff3030", bold=True)

    def __init__(
        self,
        home: GeoPoint | None = None,
        markers: Iterable[MapMarker] | None = None,
        trajectories: Iterable[Sequence[GeoPoint]] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.home = home
        self.markers = list(markers or [])
        self.trajectories = list(trajectories or [])

    def render(self) -> RenderableType:
        width, height = self._textual_size()
        return self.render_map(width=width, height=height)

    def render_map(
        self,
        width: int | None = None,
        height: int | None = None,
        markers: Iterable[MapMarker] | None = None,
        trajectories: Iterable[Sequence[GeoPoint]] | None = None,
        home: GeoPoint | None = None,
    ) -> RenderableType:
        map_width = max(48, width or 100)
        map_height = max(12, height or max(12, round(map_width / 4)))
        canvas = self._base_canvas(map_width, map_height)

        self._draw_grid(canvas)
        self._draw_land(canvas)
        self._draw_trajectories(canvas, trajectories if trajectories is not None else self.trajectories)

        for marker in markers if markers is not None else self.markers:
            self._put_geo(canvas, marker.point, marker.char, marker.style)

        home_point = home if home is not None else self.home
        if home_point is not None:
            self._put_geo(canvas, home_point, "●", self.home_style)

        return self._to_text(canvas)

    def _textual_size(self) -> tuple[int, int]:
        size = getattr(self, "size", None)
        width = getattr(size, "width", 100) or 100
        height = getattr(size, "height", 0) or max(12, round(width / 4))
        return width, height

    def _base_canvas(self, width: int, height: int) -> list[list[CanvasCell]]:
        return [[CanvasCell(" ", self.background_style) for _ in range(width)] for _ in range(height)]

    def _draw_grid(self, canvas: list[list[CanvasCell]]) -> None:
        width = len(canvas[0])
        height = len(canvas)

        for lon in range(-150, 181, 30):
            x, _ = geo_to_canvas(0, lon, width, height)
            for y in range(height):
                canvas[y][x] = CanvasCell("│", self.grid_style)

        for lat in range(-60, 91, 30):
            _, y = geo_to_canvas(lat, 0, width, height)
            for x in range(width):
                current = canvas[y][x].char
                canvas[y][x] = CanvasCell("┼" if current == "│" else "─", self.grid_style)

    def _draw_land(self, canvas: list[list[CanvasCell]]) -> None:
        width = len(canvas[0])
        height = len(canvas)
        mask = land_mask()

        for char_y in range(height):
            for char_x in range(width):
                pattern = 0
                for dot_y in range(4):
                    for dot_x in range(2):
                        lat, lon = dot_to_geo(char_x, char_y, dot_x, dot_y, width, height)
                        if mask.is_land(lat, lon):
                            pattern |= BRAILLE_BITS[dot_y][dot_x]

                if pattern:
                    style = self.land_style if pattern == 0xFF else self.coast_style
                    canvas[char_y][char_x] = CanvasCell(chr(0x2800 + pattern), style)

    def _draw_trajectories(
        self,
        canvas: list[list[CanvasCell]],
        trajectories: Iterable[Sequence[GeoPoint]],
    ) -> None:
        for trajectory in trajectories:
            for point in trajectory:
                self._put_geo(canvas, point, "·", self.trajectory_style)

    def _put_geo(self, canvas: list[list[CanvasCell]], point: GeoPoint, char: str, style: Style) -> None:
        width = len(canvas[0])
        height = len(canvas)
        x, y = geo_to_canvas(point.lat, point.lon, width, height)
        canvas[y][x] = CanvasCell(char, style)

    def _to_text(self, canvas: list[list[CanvasCell]]) -> Text:
        text = Text()
        for row in canvas:
            for cell in row:
                text.append(cell.char, style=cell.style)
            text.append("\n")
        return text


def geo_to_canvas(lat: float, lon: float, map_width: int, map_height: int) -> tuple[int, int]:
    """Map GPS coordinates to a terminal character grid using equirectangular projection."""
    normalized_lon = ((lon - WORLD_MIN_LON) % 360.0) + WORLD_MIN_LON
    if normalized_lon == WORLD_MIN_LON and lon > 0:
        normalized_lon = WORLD_MAX_LON
    clamped_lat = max(WORLD_MIN_LAT, min(WORLD_MAX_LAT, lat))
    x = int((normalized_lon - WORLD_MIN_LON) / (WORLD_MAX_LON - WORLD_MIN_LON) * map_width)
    y = int((WORLD_MAX_LAT - clamped_lat) / (WORLD_MAX_LAT - WORLD_MIN_LAT) * map_height)
    return clamp(x, 0, map_width - 1), clamp(y, 0, map_height - 1)


def dot_to_geo(
    char_x: int,
    char_y: int,
    dot_x: int,
    dot_y: int,
    map_width: int,
    map_height: int,
) -> tuple[float, float]:
    dot_width = map_width * 2
    dot_height = map_height * 4
    lon = WORLD_MIN_LON + ((char_x * 2 + dot_x + 0.5) / dot_width) * (WORLD_MAX_LON - WORLD_MIN_LON)
    lat = WORLD_MAX_LAT - ((char_y * 4 + dot_y + 0.5) / dot_height) * (WORLD_MAX_LAT - WORLD_MIN_LAT)
    return lat, lon


@lru_cache(maxsize=1)
def land_mask() -> LandMask:
    data = zlib.decompress(base64.b85decode(LAND_MASK_B85.encode("ascii")))
    return LandMask(data, MASK_WIDTH, MASK_HEIGHT)


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))
