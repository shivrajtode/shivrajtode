"""
m3.py - a small Material 3 Expressive toolkit for building the profile art.

  colour : CAM16 / HCT tonal palettes and the Material 3 colour roles (light + dark)
  shapes : morphable "expressive" shapes (cookie, clover, flower, pill, ...)
  text   : text converted to SVG outlines (with kerning), so the SVGs need no fonts
  svg    : helpers for paths and SMIL animation

The only dependency is fontTools (pip install fonttools).
"""
import math
from functools import lru_cache

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

# ---------------------------------------------------------------------------
# colour: CAM16 -> HCT (hue, chroma, tone), the space Material You is built on
# ---------------------------------------------------------------------------
_M16 = ((0.401288, 0.650173, -0.051461), (-0.250268, 1.204414, 0.045854), (-0.002079, 0.048952, 0.953127))
_XYZ_FROM_LIN = ((0.41233895, 0.35762064, 0.18051042), (0.2126, 0.7152, 0.0722), (0.01932141, 0.11916382, 0.95034478))
_LIN_FROM_XYZ = ((3.2413774792388685, -1.5376652402851851, -0.49885366846268053),
                 (-0.9691452513005321, 1.8758853451067872, 0.04156585616912061),
                 (0.05562093689691305, -0.20395524564742123, 1.0571799111220335))
_WHITE = (95.047, 100.0, 108.883)


def _y_from_lstar(l):
    ft = (l + 16.0) / 116.0
    ft3 = ft ** 3
    return 100.0 * (ft3 if ft3 > 216.0 / 24389.0 else (116.0 * ft - 16.0) / (24389.0 / 27.0))


def _lstar_from_y(y):
    t = y / 100.0
    f = t ** (1.0 / 3.0) if t > 216.0 / 24389.0 else (24389.0 / 27.0 * t + 16.0) / 116.0
    return 116.0 * f - 16.0


# default viewing conditions
_LA = 200.0 / math.pi * _y_from_lstar(50.0) / 100.0
_N = _y_from_lstar(50.0) / _WHITE[1]
_Z = 1.48 + math.sqrt(_N)
_NBB = 0.725 / _N ** 0.2
_NCB = _NBB
_NC = 1.0
_C = 0.69
_F = 1.0
_D = max(0.0, min(1.0, _F * (1.0 - (1.0 / 3.6) * math.exp((-_LA - 42.0) / 92.0))))
_RW = _WHITE[0] * _M16[0][0] + _WHITE[1] * _M16[0][1] + _WHITE[2] * _M16[0][2]
_GW = _WHITE[0] * _M16[1][0] + _WHITE[1] * _M16[1][1] + _WHITE[2] * _M16[1][2]
_BW = _WHITE[0] * _M16[2][0] + _WHITE[1] * _M16[2][1] + _WHITE[2] * _M16[2][2]
_RGBD = (_D * (100.0 / _RW) + 1.0 - _D, _D * (100.0 / _GW) + 1.0 - _D, _D * (100.0 / _BW) + 1.0 - _D)
_K = 1.0 / (5.0 * _LA + 1.0)
_K4 = _K ** 4
_FL = _K4 * _LA + 0.1 * (1.0 - _K4) ** 2 * (5.0 * _LA) ** (1.0 / 3.0)


def _adapt(v):
    af = (_FL * abs(v) / 100.0) ** 0.42
    return math.copysign(1.0, v) * 400.0 * af / (af + 27.13)


_AW = (40.0 * _adapt(_RGBD[0] * _RW) + 20.0 * _adapt(_RGBD[1] * _GW) + _adapt(_RGBD[2] * _BW)) / 20.0 * _NBB


def _srgb_to_lin(v):
    v /= 255.0
    return 100.0 * (v / 12.92 if v <= 0.040449936 else ((v + 0.055) / 1.055) ** 2.4)


def _lin_to_srgb(v):
    v /= 100.0
    v = v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1.0 / 2.4) - 0.055
    return int(round(max(0.0, min(1.0, v)) * 255.0))


def hex_to_rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r, g, b):
    return "#%02X%02X%02X" % (r, g, b)


def hct_from_rgb(r, g, b):
    """sRGB (0-255) -> (hue, chroma, tone)"""
    lin = [_srgb_to_lin(c) for c in (r, g, b)]
    x = sum(_XYZ_FROM_LIN[0][i] * lin[i] for i in range(3))
    y = sum(_XYZ_FROM_LIN[1][i] * lin[i] for i in range(3))
    z = sum(_XYZ_FROM_LIN[2][i] * lin[i] for i in range(3))
    rC = _M16[0][0] * x + _M16[0][1] * y + _M16[0][2] * z
    gC = _M16[1][0] * x + _M16[1][1] * y + _M16[1][2] * z
    bC = _M16[2][0] * x + _M16[2][1] * y + _M16[2][2] * z
    rA, gA, bA = _adapt(_RGBD[0] * rC), _adapt(_RGBD[1] * gC), _adapt(_RGBD[2] * bC)
    a = (11.0 * rA - 12.0 * gA + bA) / 11.0
    b = (rA + gA - 2.0 * bA) / 9.0
    u = (20.0 * rA + 20.0 * gA + 21.0 * bA) / 20.0
    p2 = (40.0 * rA + 20.0 * gA + bA) / 20.0
    hue = math.degrees(math.atan2(b, a)) % 360.0
    ac = p2 * _NBB
    j = 100.0 * (ac / _AW) ** (_C * _Z)
    e_hue = 0.25 * (math.cos(math.radians(hue) + 2.0) + 3.8)
    p1 = 50000.0 / 13.0 * e_hue * _NC * _NCB
    t = p1 * math.hypot(a, b) / (u + 0.305)
    alpha = t ** 0.9 * (1.64 - 0.29 ** _N) ** 0.73
    chroma = alpha * math.sqrt(j / 100.0)
    return hue, chroma, _lstar_from_y(y)


def _xyz_from_jch(j, c, h):
    alpha = 0.0 if (c == 0.0 or j == 0.0) else c / math.sqrt(j / 100.0)
    t = (alpha / (1.64 - 0.29 ** _N) ** 0.73) ** (1.0 / 0.9)
    hr = math.radians(h)
    e_hue = 0.25 * (math.cos(hr + 2.0) + 3.8)
    ac = _AW * (j / 100.0) ** (1.0 / (_C * _Z))
    p1 = e_hue * (50000.0 / 13.0) * _NC * _NCB
    p2 = ac / _NBB
    hs, hc = math.sin(hr), math.cos(hr)
    gamma = 23.0 * (p2 + 0.305) * t / (23.0 * p1 + 11.0 * t * hc + 108.0 * t * hs)
    a, b = gamma * hc, gamma * hs
    rA = (460.0 * p2 + 451.0 * a + 288.0 * b) / 1403.0
    gA = (460.0 * p2 - 891.0 * a - 261.0 * b) / 1403.0
    bA = (460.0 * p2 - 220.0 * a - 6300.0 * b) / 1403.0

    def inv(v):
        base = max(0.0, 27.13 * abs(v) / (400.0 - abs(v)))
        return math.copysign(1.0, v) * (100.0 / _FL) * base ** (1.0 / 0.42)

    rF, gF, bF = inv(rA) / _RGBD[0], inv(gA) / _RGBD[1], inv(bA) / _RGBD[2]
    x = 1.86206786 * rF - 1.01125463 * gF + 0.14918677 * bF
    y = 0.38752654 * rF + 0.62144744 * gF - 0.00897398 * bF
    z = -0.01584150 * rF - 0.03412294 * gF + 1.04996444 * bF
    return x, y, z


def _try_chroma(h, c, y_target):
    """Find J so that the colour has luminance y_target at chroma c; None if outside sRGB."""
    lo, hi = 0.0, 100.0
    xyz = None
    for _ in range(46):
        mid = (lo + hi) / 2.0
        xyz = _xyz_from_jch(mid, c, h)
        if xyz[1] < y_target:
            lo = mid
        else:
            hi = mid
    xyz = _xyz_from_jch((lo + hi) / 2.0, c, h)
    lin = [sum(_LIN_FROM_XYZ[r][i] * xyz[i] for i in range(3)) for r in range(3)]
    if any(v < -0.05 or v > 100.05 for v in lin):
        return None
    return tuple(_lin_to_srgb(v) for v in lin)


@lru_cache(maxsize=None)
def hct(h, c, tone):
    """(hue, chroma, tone) -> '#RRGGBB'. Chroma is reduced until the colour fits sRGB."""
    tone = max(0.0, min(100.0, float(tone)))
    y = _y_from_lstar(tone)
    if c < 0.5 or tone < 0.5 or tone > 99.5:
        g = _lin_to_srgb(y)
        return rgb_to_hex(g, g, g)
    got = _try_chroma(h % 360.0, c, y)
    if got is None:
        lo, hi, got = 0.0, c, None
        for _ in range(26):
            mid = (lo + hi) / 2.0
            r = _try_chroma(h % 360.0, mid, y)
            if r is None:
                hi = mid
            else:
                lo, got = mid, r
        if got is None:
            g = _lin_to_srgb(y)
            got = (g, g, g)
    return rgb_to_hex(*got)


class Tonal:
    """One tonal palette: a hue and a chroma, readable at any tone 0-100."""

    def __init__(self, hue, chroma):
        self.hue, self.chroma = hue, chroma

    def __call__(self, tone):
        return hct(round(self.hue, 3), round(self.chroma, 3), tone)


def scheme(primary, secondary, tertiary, neutral, neutral_variant, dark=False, error=(25.0, 84.0)):
    """Material 3 colour roles. Each argument is a (hue, chroma) pair."""
    P, S, T = Tonal(*primary), Tonal(*secondary), Tonal(*tertiary)
    N, NV, E = Tonal(*neutral), Tonal(*neutral_variant), Tonal(*error)

    def pick(light, darkv):
        return darkv if dark else light

    r = {
        "primary": P(pick(40, 80)), "onPrimary": P(pick(100, 20)),
        "primaryContainer": P(pick(90, 30)), "onPrimaryContainer": P(pick(10, 90)),
        "secondary": S(pick(40, 80)), "onSecondary": S(pick(100, 20)),
        "secondaryContainer": S(pick(90, 30)), "onSecondaryContainer": S(pick(10, 90)),
        "tertiary": T(pick(40, 80)), "onTertiary": T(pick(100, 20)),
        "tertiaryContainer": T(pick(90, 30)), "onTertiaryContainer": T(pick(10, 90)),
        "error": E(pick(40, 80)), "onError": E(pick(100, 20)),
        "errorContainer": E(pick(90, 30)), "onErrorContainer": E(pick(10, 90)),
        "background": N(pick(98, 6)), "onBackground": N(pick(10, 90)),
        "surface": N(pick(98, 6)), "onSurface": N(pick(10, 90)),
        "surfaceDim": N(pick(87, 6)), "surfaceBright": N(pick(98, 24)),
        "surfaceContainerLowest": N(pick(100, 4)), "surfaceContainerLow": N(pick(96, 10)),
        "surfaceContainer": N(pick(94, 12)), "surfaceContainerHigh": N(pick(92, 17)),
        "surfaceContainerHighest": N(pick(90, 22)),
        "surfaceVariant": NV(pick(90, 30)), "onSurfaceVariant": NV(pick(30, 80)),
        "outline": NV(pick(50, 60)), "outlineVariant": NV(pick(80, 30)),
        "inverseSurface": N(pick(20, 90)), "inverseOnSurface": N(pick(95, 20)),
        "inversePrimary": P(pick(80, 40)),
        "primaryFixed": P(90), "primaryFixedDim": P(80), "onPrimaryFixed": P(10), "onPrimaryFixedVariant": P(30),
        "secondaryFixed": S(90), "secondaryFixedDim": S(80), "onSecondaryFixed": S(10),
        "tertiaryFixed": T(90), "tertiaryFixedDim": T(80), "onTertiaryFixed": T(10),
        "shadow": "#000000",
    }
    # raw tonal steps, handy for decorative fills that are not a named role
    r["_P"], r["_S"], r["_T"], r["_N"] = P, S, T, N
    return r


def contrast(hex_a, hex_b):
    """WCAG contrast ratio between two colours."""
    def lum(h):
        r, g, b = hex_to_rgb(h)
        return _y_from_lstar(_lstar_from_y(0.2126 * _srgb_to_lin(r) + 0.7152 * _srgb_to_lin(g) + 0.0722 * _srgb_to_lin(b))) / 100.0
    la, lb = lum(hex_a), lum(hex_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ---------------------------------------------------------------------------
# number + path helpers
# ---------------------------------------------------------------------------
def n(v, places=2):
    s = ("%." + str(places) + "f") % v
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def rrect(x, y, w, h, tl, tr=None, br=None, bl=None):
    """Rounded rectangle path with a radius per corner."""
    tr = tl if tr is None else tr
    br = tl if br is None else br
    bl = tl if bl is None else bl
    return (f"M{n(x + tl)} {n(y)}H{n(x + w - tr)}A{n(tr)} {n(tr)} 0 0 1 {n(x + w)} {n(y + tr)}"
            f"V{n(y + h - br)}A{n(br)} {n(br)} 0 0 1 {n(x + w - br)} {n(y + h)}"
            f"H{n(x + bl)}A{n(bl)} {n(bl)} 0 0 1 {n(x)} {n(y + h - bl)}"
            f"V{n(y + tl)}A{n(tl)} {n(tl)} 0 0 1 {n(x + tl)} {n(y)}Z")


# ---------------------------------------------------------------------------
# shapes: radius functions r(theta), smoothed, normalised to equal area, as cubic paths
# ---------------------------------------------------------------------------
_SAMPLES = 360
_KNOTS = 72


def _smooth(r, sigma):
    if sigma <= 0:
        return list(r)
    cnt = len(r)
    s = sigma / (2 * math.pi / cnt)
    k = int(math.ceil(3 * s))
    w = [math.exp(-0.5 * (i / s) ** 2) for i in range(-k, k + 1)]
    tot = sum(w)
    return [sum(w[j] * r[(i + j - k) % cnt] for j in range(2 * k + 1)) / tot for i in range(cnt)]


def _angles():
    return [2 * math.pi * i / _SAMPLES - math.pi / 2 for i in range(_SAMPLES)]


def _ray_polygon(verts):
    out = []
    m = len(verts)
    for th in _angles():
        dx, dy = math.cos(th), math.sin(th)
        best = 0.0
        for i in range(m):
            px, py = verts[i]
            qx, qy = verts[(i + 1) % m]
            ex, ey = qx - px, qy - py
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t = (px * ey - py * ex) / den
            s = (px * dy - py * dx) / den
            if t > 1e-9 and -1e-9 <= s <= 1 + 1e-9:
                best = max(best, t)
        out.append(best)
    return out


def _ray_sdf(sdf, limit=3.0):
    out = []
    for th in _angles():
        dx, dy = math.cos(th), math.sin(th)
        lo, hi = 0.0, limit
        for _ in range(40):
            mid = (lo + hi) / 2
            if sdf(mid * dx, mid * dy) < 0:
                lo = mid
            else:
                hi = mid
        out.append((lo + hi) / 2)
    return out


def _unit_area(r):
    area = 0.5 * sum(v * v for v in r) * (2 * math.pi / len(r))
    k = math.sqrt(math.pi / area)
    return [v * k for v in r]


def _star(count, inner, sigma, rot=0.0):
    verts = []
    for k in range(2 * count):
        a = -math.pi / 2 + rot + k * math.pi / count
        rad = 1.0 if k % 2 == 0 else inner
        verts.append((rad * math.cos(a), rad * math.sin(a)))
    return _unit_area(_smooth(_ray_polygon(verts), sigma))


def _poly(count, sigma, rot=0.0):
    verts = [(math.cos(-math.pi / 2 + rot + k * 2 * math.pi / count), math.sin(-math.pi / 2 + rot + k * 2 * math.pi / count))
             for k in range(count)]
    return _unit_area(_smooth(_ray_polygon(verts), sigma))


def _pill(aspect, sigma, vertical=False):
    b = 1.0
    a = aspect

    def sdf(x, y):
        if vertical:
            x, y = y, x
        px = max(abs(x) - (a - b), 0.0)
        return math.hypot(px, y) - b

    return _unit_area(_smooth(_ray_sdf(sdf, a + 1), sigma))


def _squircle(power, sigma=0.0):
    r = []
    for th in _angles():
        c, s = abs(math.cos(th)), abs(math.sin(th))
        r.append((c ** power + s ** power) ** (-1.0 / power))
    return _unit_area(_smooth(r, sigma))


def _rose(count, depth, rot=0.0):
    return _unit_area([1 + depth * math.cos(count * (th + math.pi / 2 - rot)) for th in _angles()])


def _circle():
    return [1.0] * _SAMPLES


SHAPES = {
    "circle": _circle,
    "cookie9": lambda: _star(9, 0.80, 0.07),
    "cookie12": lambda: _star(12, 0.84, 0.05),
    "cookie7": lambda: _star(7, 0.76, 0.08),
    "clover4": lambda: _star(4, 0.50, 0.19),
    "flower8": lambda: _star(8, 0.60, 0.13),
    "sunny": lambda: _star(8, 0.80, 0.045),
    "burst": lambda: _star(12, 0.70, 0.07),
    "pentagon": lambda: _poly(5, 0.15),
    "triangle": lambda: _poly(3, 0.22),
    "diamond": lambda: _poly(4, 0.12),
    "squircle": lambda: _squircle(3.2),
    "pill": lambda: _pill(1.5, 0.0),
    "pillv": lambda: _pill(1.5, 0.0, True),
    "gem": lambda: _poly(6, 0.11, rot=math.pi / 6),
    "rose6": lambda: _rose(6, 0.17),
}


@lru_cache(maxsize=None)
def _samples(name):
    return tuple(SHAPES[name]())


def shape_path(name, radius=1.0, rotate=0.0):
    """Closed cubic path (centre 0,0). All shapes share one structure, so SMIL can morph between them."""
    r = _samples(name)
    step = _SAMPLES // _KNOTS
    pts = []
    for i in range(_KNOTS):
        idx = i * step
        th = 2 * math.pi * idx / _SAMPLES - math.pi / 2 + rotate
        pts.append((r[idx] * radius * math.cos(th), r[idx] * radius * math.sin(th)))
    m = len(pts)
    d = [f"M{n(pts[0][0])} {n(pts[0][1])}"]
    for i in range(m):
        p0, p1, p2, p3 = pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{n(c1[0])} {n(c1[1])} {n(c2[0])} {n(c2[1])} {n(p2[0])} {n(p2[1])}")
    return "".join(d) + "Z"


# ---------------------------------------------------------------------------
# text -> outlines
# ---------------------------------------------------------------------------
class Face:
    """A font file that can turn text into SVG path data, with GPOS pair kerning."""

    def __init__(self, path):
        self.tt = TTFont(path)
        self.upm = self.tt["head"].unitsPerEm
        self.cmap = self.tt.getBestCmap()
        self.gs = self.tt.getGlyphSet()
        self.hmtx = self.tt["hmtx"]
        os2 = self.tt["OS/2"]
        self.cap = getattr(os2, "sCapHeight", 0.7 * self.upm) / self.upm
        self.xh = getattr(os2, "sxHeight", 0.5 * self.upm) / self.upm
        self._kern_lookups = self._load_kern()
        self._kern_cache = {}
        self._dots = {}

    # -- kerning
    def _load_kern(self):
        if "GPOS" not in self.tt:
            return []
        gpos = self.tt["GPOS"].table
        idx = set()
        for fr in gpos.FeatureList.FeatureRecord:
            if fr.FeatureTag == "kern":
                idx.update(fr.Feature.LookupListIndex)
        out = []
        for li in sorted(idx):
            subs = []
            for st in gpos.LookupList.Lookup[li].SubTable:
                st = getattr(st, "ExtSubTable", st)
                if st.__class__.__name__ == "PairPos":
                    subs.append(st)
            out.append(subs)
        return out

    @staticmethod
    def _xadv(v):
        return getattr(v, "XAdvance", 0) or 0 if v is not None else 0

    def kern(self, left, right):
        key = (left, right)
        if key in self._kern_cache:
            return self._kern_cache[key]
        val = 0
        found = False
        for subs in self._kern_lookups:
            for st in subs:
                cov = st.Coverage.glyphs
                if left not in cov:
                    continue
                if st.Format == 1:
                    ps = st.PairSet[cov.index(left)]
                    for rec in ps.PairValueRecord:
                        if rec.SecondGlyph == right:
                            val, found = self._xadv(rec.Value1), True
                            break
                else:
                    c1 = st.ClassDef1.classDefs.get(left, 0)
                    c2 = st.ClassDef2.classDefs.get(right, 0)
                    rec = st.Class1Record[c1].Class2Record[c2]
                    val, found = self._xadv(rec.Value1), True
                if found:
                    break
            if found:
                break
        self._kern_cache[key] = val
        return val

    # -- glyphs
    def gname(self, ch):
        return self.cmap.get(ord(ch), ".notdef")

    def advance(self, ch, size):
        return self.hmtx[self.gname(ch)][0] * size / self.upm

    def glyph_d(self, ch, size, x=0.0, y=0.0, drop_dot=False):
        name = self.gname(ch)
        s = size / self.upm
        pen = SVGPathPen(self.gs, ntos=lambda v: n(v, 1))
        tp = TransformPen(pen, (s, 0, 0, -s, x, y))
        if not drop_dot:
            self.gs[name].draw(tp)
            return pen.getCommands()
        rec = DecomposingRecordingPen(self.gs)
        self.gs[name].draw(rec)
        contours, cur = [], []
        for op, args in rec.value:
            if op == "moveTo":
                cur = [(op, args)]
            else:
                cur.append((op, args))
            if op in ("closePath", "endPath"):
                contours.append(cur)
                cur = []

        def ymin(c):
            return min(p[1] for _, a in c for p in a if a)

        def ymax(c):
            return max(p[1] for _, a in c for p in a if a)

        dot = max(contours, key=ymin)
        xs = [p[0] for _, a in dot for p in a if a]
        self._dots[ch] = ((min(xs) + max(xs)) / 2 / self.upm, (ymin(dot) + ymax(dot)) / 2 / self.upm,
                          (max(xs) - min(xs)) / self.upm)
        for c in contours:
            if c is dot:
                continue
            for op, args in c:
                getattr(tp, op)(*args)
        return pen.getCommands()

    def dot_center(self, ch):
        """Centre (x, y, diameter) of the dot of i or j in em units (y up)."""
        if ch not in self._dots:
            self.glyph_d(ch, 1000, drop_dot=True)
        return self._dots[ch]

    def layout(self, text, size, tracking=0.0):
        """[(char, x)] pen positions plus the total width, kerning applied."""
        pos, x, prev = [], 0.0, None
        for ch in text:
            if prev is not None:
                x += self.kern(self.gname(prev), self.gname(ch)) * size / self.upm
            pos.append((ch, x))
            x += self.advance(ch, size) + tracking * size
            prev = ch
        return pos, x - (tracking * size if text else 0)

    def width(self, text, size, tracking=0.0):
        return self.layout(text, size, tracking)[1]

    def text_d(self, text, size, x=0.0, y=0.0, tracking=0.0, anchor="start"):
        pos, w = self.layout(text, size, tracking)
        ox = x - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
        parts = []
        for ch, px in pos:
            if ch != " ":
                parts.append(self.glyph_d(ch, size, ox + px, y))
        return "".join(parts), w

    def wrap(self, text, size, max_w, tracking=0.0):
        lines, cur = [], ""
        for word in text.split():
            trial = (cur + " " + word).strip()
            if cur and self.width(trial, size, tracking) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        if cur:
            lines.append(cur)
        return lines


# ---------------------------------------------------------------------------
# svg + SMIL helpers
# ---------------------------------------------------------------------------
ANIMATE = True                         # build.py switches this off to make the static, reduced-motion set
EASE_STANDARD = "0.2 0 0 1"            # M3 "standard"
EASE_EMPH_DECEL = "0.05 0.7 0.1 1"     # M3 "emphasized decelerate"
EASE_EMPH_ACCEL = "0.3 0 0.8 0.15"     # M3 "emphasized accelerate"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg_doc(w, h, body, title, desc="", defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {n(w)} {n(h)}" width="{n(w)}" height="{n(h)}" '
            f'role="img" aria-labelledby="t d">\n<title id="t">{esc(title)}</title>\n<desc id="d">{esc(desc)}</desc>\n'
            f'{("<defs>" + defs + "</defs>") if defs else ""}\n{body}\n</svg>\n')


def animate(attr, values, dur, key_times=None, spline=EASE_STANDARD, begin="0s", repeat="indefinite", extra=""):
    if not ANIMATE:
        return ""
    vals = ";".join(values)
    kt = ""
    if key_times is not None:
        kt = f' keyTimes="{";".join(n(k, 4) for k in key_times)}"'
    sp = ""
    calc = ""
    if spline:
        segs = len(values) - 1
        sp = f' keySplines="{";".join([spline] * segs)}"'
        calc = ' calcMode="spline"'
        if key_times is None:
            kt = f' keyTimes="{";".join(n(i / segs, 4) for i in range(segs + 1))}"'
    rep = f' repeatCount="{repeat}"' if repeat else ""
    return f'<animate attributeName="{attr}" values="{vals}" dur="{dur}s"{kt}{calc}{sp} begin="{begin}"{rep}{extra}/>'


def spin(cx, cy, dur, clockwise=True, begin="0s"):
    if not ANIMATE:
        return ""
    a, b = (0, 360) if clockwise else (360, 0)
    return (f'<animateTransform attributeName="transform" type="rotate" additive="sum" from="{a} {n(cx)} {n(cy)}" '
            f'to="{b} {n(cx)} {n(cy)}" dur="{dur}s" begin="{begin}" repeatCount="indefinite"/>')


def morph_sequence(names, radius, hold, move, rotate_each=0.0, spline=EASE_STANDARD):
    """SMIL <animate> that morphs a path through the named shapes and loops back to the first."""
    if not ANIMATE:
        return "", shape_path(names[0], radius)
    seq = list(names) + [names[0]]
    paths = [shape_path(s, radius, rotate=rotate_each * i) for i, s in enumerate(seq)]
    total = (hold + move) * len(names)
    values, times = [], []
    t = 0.0
    for i, p in enumerate(paths):
        values.append(p)
        times.append(t / total)
        if i < len(paths) - 1:
            values.append(p)
            times.append((t + hold) / total)
            t += hold + move
    # values: [p0, p0, p1, p1, ..., pN]; build splines so that holds are linear and moves eased
    splines = []
    for i in range(len(values) - 1):
        splines.append("0 0 1 1" if values[i] == values[i + 1] else spline)
    vals = ";".join(values)
    kt = ";".join(n(k, 5) for k in times)
    sp = ";".join(splines)
    return (f'<animate attributeName="d" values="{vals}" keyTimes="{kt}" calcMode="spline" keySplines="{sp}" '
            f'dur="{n(total)}s" repeatCount="indefinite"/>'), paths[0]
