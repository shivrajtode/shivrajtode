#!/usr/bin/env python3
"""
Builds every SVG in ../assets (a light and a dark version of each).

    pip install fonttools
    python3 tools/build.py

Edit the CONTENT block below to change words, links or colours, then run it again.
All text is converted to outlines, so the images look the same on every device.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import m3  # noqa: E402
from m3 import animate, n, rrect, shape_path, spin, svg_doc  # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, "..", "assets"))
BOLD = m3.Face(os.path.join(HERE, "fonts", "Outfit-Bold.ttf"))
REG = m3.Face(os.path.join(HERE, "fonts", "Outfit-Regular.ttf"))
MONO = m3.Face(os.path.join(HERE, "fonts", "RedHatMono-Bold.ttf"))

# ---------------------------------------------------------------------------
# CONTENT
# ---------------------------------------------------------------------------
W = 840
NAME = "Shivraj"
TAGLINE = "I test ROMs and build the tools that flash and fix Android phones."
TELEGRAM = "Shivraj_editx"

# Material colour seeds as (hue, chroma). Green primary, tulip-pink tertiary.
SEED = dict(primary=(148, 46), secondary=(118, 22), tertiary=(350, 58), neutral=(148, 6), neutral_variant=(148, 10))

PROJECTS = [
    dict(slug="spft", title="spft", url="https://github.com/shivrajtode/spft",
         desc="SP Flash Tool on a rooted phone. Flash or unbrick MediaTek devices with no PC.",
         chips=[("mono", "$ spft"), ("text", "Termux")], icon="bolt", shape="cookie9",
         bg="primary", fg="onPrimary", ibg="tertiaryContainer", ifg="onTertiaryContainer",
         radii=(96, 40, 96, 40)),
    dict(slug="flashkit", title="flashkit", url="https://github.com/shivrajtode/flashkit",
         desc="Flash, sideload and rescue a second Android device from your rooted phone.",
         chips=[("mono", "$ flashkit"), ("text", "Termux")], icon="phones", shape="flower8",
         bg="tertiaryContainer", fg="onTertiaryContainer", ibg="primary", ifg="onPrimary",
         radii=(40, 96, 40, 96)),
    dict(slug="touchguard", title="TouchGuard", url="https://github.com/shivrajtode/TouchGuard",
         desc="Stops phantom touches before apps see them. A root module made for tulip.",
         chips=[("text", "Magisk"), ("text", "KernelSU")], icon="shield", shape="squircle",
         bg="secondaryContainer", fg="onSecondaryContainer", ibg="tertiary", ifg="onTertiary",
         radii=(108, 108, 108, 108)),
    dict(slug="scarlet", title="Scarlet-X kernel", url="https://github.com/shivrajtode/scarlet_xiaomi_sdm660",
         desc="Fork of the Scarlet-X kernel source for tulip and other sdm660 phones.",
         chips=[("text", "Fork"), ("text", "C")], icon="chip", shape="gem",
         bg="surfaceContainerHigh", fg="onSurface", ibg="primaryContainer", ifg="onPrimaryContainer",
         radii=(28, 28, 28, 28)),
]

ABOUT_ROWS = [
    ("person", "Device name", "Shivraj"),
    ("phone", "Test phone", "Redmi Note 6 Pro (tulip)"),
    ("flask", "Android version", "Custom ROM test builds"),
    ("chip", "Kernel version", "sdm660, Scarlet-X fork"),
    ("terminal", "Tools", "Termux, adb, fastboot, SP Flash Tool"),
]


def theme(mode):
    return m3.scheme(dark=(mode == "dark"), **SEED)


# ---------------------------------------------------------------------------
# small drawing helpers
# ---------------------------------------------------------------------------
def txt(face, s, size, x, y, fill, tracking=0.0, anchor="start", stroke=0.0, extra=""):
    d, w = face.text_d(s, size, x, y, tracking, anchor)
    st = f' stroke="{fill}" stroke-width="{n(stroke)}" stroke-linejoin="round"' if stroke else ""
    return f'<path d="{d}" fill="{fill}"{st}{extra}/>', w


def para(face, s, size, x, y, max_w, lead, fill, tracking=0.0):
    out, lines = [], face.wrap(s, size, max_w, tracking)
    for i, ln in enumerate(lines):
        p, _ = txt(face, ln, size, x, y + i * lead, fill, tracking)
        out.append(p)
    return "".join(out), len(lines)


def pop(inner, delay=0.0, dur=0.9, peak=1.14):
    """Spring a group in once at load. The delay is inside one animation, so nothing flashes before it starts."""
    if not m3.ANIMATE:
        return f"<g>{inner}</g>"
    total = delay + dur
    if delay > 0:
        times = [0, delay / total, (delay + dur * 0.5) / total, (delay + dur * 0.78) / total, 1]
        vals = ["0", "0", n(peak), "0.97", "1"]
        sp = ["0 0 1 1", m3.EASE_EMPH_DECEL, "0.4 0 0.6 1", "0.4 0 0.6 1"]
    else:
        times = [0, 0.5, 0.78, 1]
        vals = ["0", n(peak), "0.97", "1"]
        sp = [m3.EASE_EMPH_DECEL, "0.4 0 0.6 1", "0.4 0 0.6 1"]
    return (f'<g><animateTransform attributeName="transform" type="scale" values="{";".join(vals)}" '
            f'keyTimes="{";".join(n(k, 4) for k in times)}" calcMode="spline" keySplines="{";".join(sp)}" '
            f'dur="{n(total)}s" begin="0s" fill="freeze"/>{inner}</g>')


def glyph(name, color, sw=9, cut=None):
    """Simple stroke icons drawn inside a 100 x 100 box around 0,0."""
    st = f'fill="none" stroke="{color}" stroke-width="{n(sw)}" stroke-linecap="round" stroke-linejoin="round"'
    if name == "bolt":
        return f'<path d="M10 -46L-26 6H-2L-10 46L26 -8H2Z" fill="{color}" stroke="{color}" stroke-width="{n(sw)}" stroke-linejoin="round"/>'
    if name == "phones":
        return (f'<g {st}><rect x="-52" y="-32" width="28" height="64" rx="8"/><rect x="24" y="-32" width="28" height="64" rx="8"/>'
                f'<path d="M-24 0H24"/></g><circle cx="0" cy="0" r="8" fill="{color}"/>')
    if name == "shield":
        return (f'<g {st}><path d="M0 -46C16 -38 30 -36 38 -34V2C38 26 18 40 0 48C-18 40 -38 26 -38 2V-34C-30 -36 -16 -38 0 -46Z"/>'
                f'<circle cx="0" cy="2" r="19"/></g><circle cx="0" cy="2" r="7" fill="{color}"/>')
    if name == "chip":
        pins = "".join(f'<path d="M{x} -24V-42M{x} 24V42M-24 {x}H-42M24 {x}H42"/>' for x in (-12, 12))
        return (f'<g {st}><rect x="-24" y="-24" width="48" height="48" rx="10"/>{pins}</g>'
                f'<rect x="-9" y="-9" width="18" height="18" rx="4" fill="{color}"/>')
    if name == "person":
        return f'<g {st}><circle cx="0" cy="-18" r="14"/><path d="M-32 42C-32 14 -14 6 0 6C14 6 32 14 32 42"/></g>'
    if name == "phone":
        return f'<g {st}><rect x="-24" y="-44" width="48" height="88" rx="12"/><path d="M-9 28H9"/></g>'
    if name == "flask":
        return (f'<g {st}><path d="M-12 -42H12M-7 -42V-10L-33 32C-36 39 -31 45 -24 45H24C31 45 36 39 33 32L7 -10V-42"/>'
                f'<path d="M-21 16H21"/></g>')
    if name == "terminal":
        return f'<g {st}><path d="M-34 -26L-8 0L-34 26"/><path d="M6 30H38"/></g>'
    if name == "arrow":
        return f'<g {st}><path d="M-20 20L18 -18M-6 -18H18V6"/></g>'
    if name == "back":
        return f'<g {st}><path d="M28 0H-24M-4 -22L-26 0L-4 22"/></g>'
    if name == "plane":
        cut = cut or "#000"
        return (f'<path d="M32 -32L-34 -6L-9 6L4 34Z" fill="{color}" stroke="{color}" stroke-width="{n(sw * 0.7)}" stroke-linejoin="round"/>'
                f'<path d="M-9 6L32 -32" fill="none" stroke="{cut}" stroke-width="{n(sw * 0.55)}" stroke-linecap="round"/>')
    raise KeyError(name)


def chip(face, text, size, x, y, h, fg, fill, opacity, pad=22):
    """A pill with centred text. y is the top of the pill. Returns (svg, width)."""
    w = face.width(text, size) + pad * 2
    base = y + h / 2 + face.cap * size / 2
    t, _ = txt(face, text, size, x + pad, base, fg)
    return f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(h / 2)}" fill="{fill}" fill-opacity="{opacity}"/>{t}', w


# ---------------------------------------------------------------------------
# components
# ---------------------------------------------------------------------------
HERO_H = 500


def hero(c, mode):
    H = HERO_H
    P = c["_P"]
    step = P(80) if mode == "light" else P(40)
    pink = c["_T"](50) if mode == "light" else c["_T"](80)
    defs = f'<clipPath id="hc"><path d="{rrect(0, 0, W, H, 64)}"/></clipPath>'
    b = [f'<g clip-path="url(#hc)"><path d="{rrect(0, 0, W, H, 64)}" fill="{c["primaryContainer"]}"/>']
    b.append(f'<g transform="translate(786 30)"><g><path d="{shape_path("cookie12", 330)}" fill="{step}"/>{spin(0, 0, 150)}</g></g>')
    b.append(f'<g transform="translate(0 540)"><g><path d="{shape_path("flower8", 240)}" fill="{step}"/>{spin(0, 0, 120, False)}</g></g>')
    b.append("</g>")

    # tagline, top left
    tag, _ = para(REG, TAGLINE, 36, 46, 104, 420, 46, c["onPrimaryContainer"])
    b.append(tag)

    # the big morphing shape with a terminal prompt inside
    names = ["cookie9", "flower8", "squircle", "burst", "pentagon", "sunny", "cookie12", "circle"]
    anim, first = m3.morph_sequence(names, 112, hold=2.4, move=1.7)
    gl = (f'<g fill="none" stroke="{c["onTertiary"]}" stroke-width="21" stroke-linecap="round" stroke-linejoin="round">'
          f'<path d="M-46 -33L-10 0L-46 33"/><path d="M8 41H55"/></g>')
    inner = f'<g><path d="{first}" fill="{pink}">{anim}</path>{spin(0, 0, 80)}</g>{gl}'
    b.append(f'<g transform="translate(654 128)">{pop(inner, 0.1, 1.1)}</g>')

    # the name, with the dots of i and j drawn as shapes
    size, track, x0, base = 214, -0.02, 44, 432
    pos, _ = BOLD.layout(NAME, size, track)
    letters, dots = [], []
    for ch, px in pos:
        drop = ch in "ij"
        letters.append(BOLD.glyph_d(ch, size, x0 + px, base, drop_dot=drop))
        if drop:
            dx, dy, dd = BOLD.dot_center(ch)
            dots.append((x0 + px + dx * size, base - dy * size, dd * size / 2 * 1.5))
    b.append(f'<path d="{"".join(letters)}" fill="{c["onPrimaryContainer"]}" stroke="{c["onPrimaryContainer"]}" stroke-width="3" stroke-linejoin="round"/>')
    for k, (dxp, dyp, rad) in enumerate(dots):
        shape = ("cookie7", "flower8")[k % 2]
        sp = f'<path d="{shape_path(shape, rad)}" fill="{pink}"/>{spin(0, 0, 9 + 3 * k, k % 2 == 0)}'
        b.append(f'<g transform="translate({n(dxp)} {n(dyp)})">{pop("<g>" + sp + "</g>", 0.55 + 0.18 * k, 0.8, 1.25)}</g>')

    # small satellite
    b.append(f'<g transform="translate(786 420)">{pop("<g><path d=%s fill=%s/>%s</g>" % (chr(34) + shape_path("cookie7", 44) + chr(34), chr(34) + c["primary"] + chr(34), spin(0, 0, 18)), 0.9, 0.8, 1.2)}</g>')
    desc = f"{NAME}: {TAGLINE}"
    return svg_doc(W, H, "\n".join(b), f"{NAME}, Android ROM tester and tool maker", desc, defs)


def divider(c, mode):
    H = 64
    amp, period, sw, frames = 9.0, 64.0, 9.0, 10
    stepx = period / 8
    cnt = int((W - sw - 4) / stepx)

    def env(x):
        def ss(t):
            t = max(0.0, min(1.0, t))
            return t * t * (3 - 2 * t)
        return ss(x / 110.0) * ss((W - x) / 110.0)

    def wave_path(phase):
        pts = []
        for i in range(cnt + 1):
            x = sw / 2 + 2 + i * stepx
            pts.append((x, H / 2 + env(x) * amp * math.sin(2 * math.pi * x / period - phase)))
        d = [f"M{n(pts[0][0])} {n(pts[0][1])}"]
        m = len(pts)
        for i in range(m - 1):
            p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, m - 1)]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            d.append(f"C{n(c1[0])} {n(c1[1])} {n(c2[0])} {n(c2[1])} {n(p2[0])} {n(p2[1])}")
        return "".join(d)

    frames_d = [wave_path(2 * math.pi * k / frames) for k in range(frames + 1)]
    anim = (f'<animate attributeName="d" values="{";".join(frames_d)}" dur="3s" repeatCount="indefinite"/>') if m3.ANIMATE else ""
    defs = f'<path id="w" fill="none" stroke-linecap="round" d="{frames_d[0]}">{anim}</path>'
    body = (f'<use href="#w" xlink:href="#w" stroke="{c["primary"]}" stroke-width="{n(sw)}"/>'
            f'<use href="#w" xlink:href="#w" transform="translate(0 {H}) scale(1 -1)" stroke="{c["tertiary"]}" stroke-width="{n(sw)}"/>')
    return svg_doc(W, H, body, "Divider", "A green and a pink wave, moving gently.", defs)


def heading(c, mode, text, shape="cookie9"):
    H = 104
    pink = c["_T"](50) if mode == "light" else c["_T"](80)
    # shape's left edge (76 - 36) sits on the same 40 px grid line as the card content below
    t, _ = txt(BOLD, text, 60, 128, 74, c["onSurface"], tracking=-0.01)
    body = (f'<g transform="translate(76 52)"><g><path d="{shape_path(shape, 36)}" fill="{pink}"/>{spin(0, 0, 40)}</g></g>{t}')
    return svg_doc(W, H, body, text, f"Section heading: {text}")


DESC_W = 520


def card_height(p):
    lines = REG.wrap(p["desc"], 28, DESC_W)
    return math.ceil(max(220, 36 + 0.706 * 54 + 6 + 54 + (len(lines) - 1) * 38 + 48))


def card(c, mode, p):
    H = card_height(p)
    tl, tr, br, bl = p["radii"]
    bg, fg = c[p["bg"]], c[p["fg"]]
    body = [f'<path d="{rrect(0, 0, W, H, tl, tr, br, bl)}" fill="{bg}"/>']
    # icon on an expressive shape
    cx, cy, R = 40 + 74, H / 2, 74
    body.append(f'<g transform="translate({n(cx)} {n(cy)})"><g><path d="{shape_path(p["shape"], R)}" fill="{c[p["ibg"]]}"/>{spin(0, 0, 70)}</g>'
                f'<g transform="scale(0.78)">{glyph(p["icon"], c[p["ifg"]], 9)}</g></g>')
    tx = 40 + 148 + 34
    # title + chips on one row
    title_size = 54
    base = 36 + 0.706 * title_size + 6
    t, tw = txt(BOLD, p["title"], title_size, tx, base, fg, tracking=-0.01)
    body.append(t)
    cx2 = tx + tw + 26
    ch_h = 44
    ch_y = base - 0.706 * title_size / 2 - ch_h / 2 + 2
    for kind, label in p["chips"]:
        face, size = (MONO, 23) if kind == "mono" else (REG, 25)
        s, w = chip(face, label, size, cx2, ch_y, ch_h, fg, fg, 0.16, pad=20)
        body.append(s)
        cx2 += w + 10
    # description
    d, lines = para(REG, p["desc"], 28, tx, base + 54, DESC_W, 38, fg)
    body.append(d)
    # open button
    bx, by = W - 40 - 28, H - 40 - 28
    body.append(f'<circle cx="{n(bx)}" cy="{n(by)}" r="28" fill="{fg}" fill-opacity="0.16"/>'
                f'<g transform="translate({n(bx)} {n(by)}) scale(0.34)">{glyph("arrow", fg, 15)}</g>')
    return svg_doc(W, H, "\n".join(body), p["title"], f'{p["title"]}: {p["desc"]} Opens the repository on GitHub.')


def about(c, mode):
    rows = ABOUT_ROWS
    head_h, row_h, gap, pad = 204, 88, 4, 20
    H = head_h + len(rows) * row_h + (len(rows) - 1) * gap + pad + 14
    body = [f'<path d="{rrect(0, 0, W, H, 64)}" fill="{c["surfaceContainer"]}"/>']
    # app bar: back button and a large title
    body.append(f'<circle cx="{52 + 28}" cy="{40 + 28}" r="28" fill="{c["surfaceContainerHighest"]}"/>'
                f'<g transform="translate({52 + 28} {40 + 28}) scale(0.34)">{glyph("back", c["onSurface"], 15)}</g>')
    t, _ = txt(BOLD, "About phone", 66, 48, 162, c["onSurface"], tracking=-0.015)
    body.append(t)
    shapes = ["cookie7", "flower8", "sunny", "squircle", "cookie9"]
    tints = [("primaryContainer", "onPrimaryContainer"), ("tertiaryContainer", "onTertiaryContainer"),
             ("secondaryContainer", "onSecondaryContainer"), ("primaryContainer", "onPrimaryContainer"),
             ("tertiaryContainer", "onTertiaryContainer")]
    y = head_h
    for i, (ic, label, value) in enumerate(rows):
        first, last = i == 0, i == len(rows) - 1
        top_r = 40 if first else 12
        bot_r = 40 if last else 12
        x0 = pad
        body.append(f'<path d="{rrect(x0, y, W - 2 * pad, row_h, top_r, top_r, bot_r, bot_r)}" fill="{c["surfaceContainerLowest"]}"/>')
        icx, icy = x0 + 28 + 30, y + row_h / 2
        bgc, fgc = tints[i]
        body.append(f'<g transform="translate({n(icx)} {n(icy)})"><path d="{shape_path(shapes[i], 34)}" fill="{c[bgc]}"/>'
                    f'<g transform="scale(0.4)">{glyph(ic, c[fgc], 10)}</g></g>')
        lt, _ = txt(REG, label, 25, x0 + 118, y + 34, c["onSurfaceVariant"])
        vt, _ = txt(BOLD, value, 33, x0 + 118, y + 70, c["onSurface"], tracking=-0.005)
        body.append(lt + vt)
        y += row_h + gap
    return svg_doc(W, H, "\n".join(body), "About phone: Shivraj",
                   "An Android settings screen about me. " + ". ".join(f"{l}: {v}" for _, l, v in rows) + ".")


def contact(c, mode):
    H = 330
    P = c["_P"]
    T = c["_T"]
    step = T(80) if mode == "light" else T(40)
    defs = f'<clipPath id="cc"><path d="{rrect(0, 0, W, H, 120, 48, 120, 48)}"/></clipPath>'
    b = [f'<g clip-path="url(#cc)"><path d="{rrect(0, 0, W, H, 120, 48, 120, 48)}" fill="{c["tertiaryContainer"]}"/>']
    pink = c["_T"](50) if mode == "light" else c["_T"](80)
    b.append(f'<g transform="translate(736 176)"><g><path d="{shape_path("cookie12", 176)}" fill="{step}"/>{spin(0, 0, 120)}</g></g>')
    b.append("</g>")
    # big plane in a shape
    inner = (f'<g><path d="{shape_path("cookie9", 112)}" fill="{pink}"/>{spin(0, 0, 60, False)}</g>'
             f'<g transform="scale(1.5)">{glyph("plane", c["onTertiary"], 9, cut=pink)}</g>')
    b.append(f'<g transform="translate(736 176)">{pop(inner, 0.2, 1.0)}</g>')
    h1, _ = txt(BOLD, "Stuck on a flash?", 60, 64, 116, c["onTertiaryContainer"], tracking=-0.015)
    h2, _ = txt(BOLD, "Ask me.", 60, 64, 184, c["onTertiaryContainer"], tracking=-0.015)
    b.append(h1 + h2)
    # extended FAB
    label = "@" + TELEGRAM
    fs = 36
    lw = BOLD.width(label, fs)
    fw, fh, fx, fy = lw + 40 + 76 + 28, 84, 64, 222
    b.append(f'<rect x="{fx}" y="{fy}" width="{n(fw)}" height="{fh}" rx="{fh / 2}" fill="{c["primary"]}"/>')
    b.append(f'<g transform="translate({fx + 26 + 26} {fy + fh / 2})"><path d="{shape_path("cookie7", 29)}" fill="{c["onPrimary"]}" fill-opacity="0.18"/>'
             f'<g transform="scale(0.5)">{glyph("plane", c["onPrimary"], 9, cut=c["primary"])}</g></g>')
    lt, _ = txt(BOLD, label, fs, fx + 26 + 52 + 22, fy + fh / 2 + BOLD.cap * fs / 2, c["onPrimary"])
    b.append(lt)
    return svg_doc(W, H, "\n".join(b), f"Message Shivraj on Telegram: @{TELEGRAM}",
                   f"Stuck on a flash? Ask me. Opens Telegram, @{TELEGRAM}.", defs)


# ---------------------------------------------------------------------------
def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return os.path.getsize(path)


# ---------------------------------------------------------------------------
# README (written only with --readme, so hand edits to README.md are never overwritten by accident)
# ---------------------------------------------------------------------------
def picture(name, alt, link=None, motion=True):
    srcs = []
    if motion:
        srcs.append(f'<source media="(prefers-reduced-motion: reduce) and (prefers-color-scheme: dark)" srcset="assets/static/{name}-dark.svg">')
        srcs.append(f'<source media="(prefers-reduced-motion: reduce)" srcset="assets/static/{name}-light.svg">')
    srcs.append(f'<source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">')
    pad = "    " if link else "  "
    pic = (f"{pad}<picture>\n" + "\n".join(f"{pad}  {s}" for s in srcs) +
           f'\n{pad}  <img src="assets/{name}-light.svg" alt="{m3.esc(alt)}" width="{W}">\n{pad}</picture>')
    if link:
        pic = f'  <a href="{link}">\n{pic}\n  </a>'
    return f'<p align="center">\n{pic}\n</p>\n'


def readme():
    parts = [picture("hero", f"{NAME}. {TAGLINE}"), picture("divider", "")]
    parts.append(picture("heading-projects", "Projects"))
    for p in PROJECTS:
        kinds = ", ".join(label for _, label in p["chips"])
        parts.append(picture(f"card-{p['slug']}", f"{p['title']}. {p['desc']} {kinds}. Opens the repository on GitHub.", p["url"]))
    parts.append(picture("divider", ""))
    rows = ". ".join(f"{label}: {value}" for _, label, value in ABOUT_ROWS)
    parts.append(picture("about", f"About phone. {rows}.", motion=False))
    parts.append(picture("contact", f"Stuck on a flash? Ask me. Message @{TELEGRAM} on Telegram.", f"https://t.me/{TELEGRAM}"))
    parts.append('<p align="center"><sub>Material 3 Expressive style, generated by <a href="tools/build.py">tools/build.py</a>. '
                 'Plain SVG: no scripts, no tracking, no external images. Not affiliated with Google.</sub></p>\n')
    return "\n".join(parts)


def main():
    total = 0
    for animated in (True, False):
        m3.ANIMATE = animated
        out_dir = OUT if animated else os.path.join(OUT, "static")
        os.makedirs(out_dir, exist_ok=True)
        for mode in ("light", "dark"):
            c = theme(mode)
            jobs = {
                f"hero-{mode}.svg": hero(c, mode),
                f"divider-{mode}.svg": divider(c, mode),
                f"heading-projects-{mode}.svg": heading(c, mode, "Projects", "cookie9"),
                f"contact-{mode}.svg": contact(c, mode),
            }
            if animated:  # the About card has no motion, so one file serves both sets
                jobs[f"about-{mode}.svg"] = about(c, mode)
            for p in PROJECTS:
                jobs[f"card-{p['slug']}-{mode}.svg"] = card(c, mode, p)
            for name, svg in jobs.items():
                size = write(os.path.join(out_dir, name), svg)
                total += size
                print(f"{'' if animated else 'static/'}{name:34s} {size / 1024:7.1f} KB")
    m3.ANIMATE = True
    print(f"total {total / 1024:.0f} KB")
    if "--readme" in sys.argv:
        write(os.path.normpath(os.path.join(HERE, "..", "README.md")), readme())
        print("wrote README.md")


if __name__ == "__main__":
    main()
