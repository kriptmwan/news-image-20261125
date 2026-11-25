# render.py — draws news-image-20261125 entry.png (1024x1024) with PIL.
# Fresh build for the 25 Nov 2026 edition. Design per Gate 1 (MiMo review, build log):
# dominant lead, big House panel, 3-column row, Also strip; 44px floor on
# every panel headline; navy base + white type + red / gold / blue accents only.
# REBUILD 17:17 WIB 25 Nov (user order): lead swapped Nvidia -> LSP treason
# case (ex-police chief + 5 officers named makar suspects; Jokowi link is
# ALLEGED only, never fact), Nvidia moved to the Also strip, stale "VP resigns"
# (12 Nov) dropped. Gate 1 MiMo fixes applied: headline auto-shrinks to fit
# 3 lines, ticker shortened, subline one line with "alleged" kept.
# Everything is drawn in code (vector-style panels, big type, simple iconic shapes);
# no external photos, no network. Deterministic: same bytes every run.
from PIL import Image, ImageDraw, ImageFont
import hashlib
import os

W = H = 1024
M = 36                      # outer margin
LIVE = W - 2 * M            # 952
GUT = 24                    # gutter

BASE = (11, 18, 32)         # near-black navy
PANEL = (22, 35, 56)        # slate navy panel
INK = (255, 255, 255)
MUTED = (199, 210, 224)
RED = (229, 72, 77)         # markets / strikes
GOLD = (217, 164, 65)       # AFCON celebration
BLUE = (127, 179, 232)      # space / politics
DARKRED = (140, 32, 36)

MEASURE = Image.new("RGB", (8, 8))
MDRAW = ImageDraw.Draw(MEASURE)


def font(size, bold=True):
    return ImageFont.truetype(
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)


def text_w(text, fnt):
    return MDRAW.textlength(text, font=fnt)


def wrap(text, fnt, max_w):
    """Greedy word wrap by measured width. Returns list of lines."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def balanced_wrap(text, fnt, max_w, max_lines):
    """Split words into <= max_lines lines, minimising the widest line
    (least ragged), subject to every line fitting max_w. Returns lines
    or None if impossible."""
    words = text.split(" ")
    n = len(words)
    best = [None, None]  # [max_width, lines]

    def rec(start, lines):
        if start == n:
            if lines:
                mw = max(text_w(" ".join(l), fnt) for l in lines)
                if best[0] is None or mw < best[0]:
                    best[0] = mw
                    best[1] = [" ".join(l) for l in lines]
            return
        if len(lines) >= max_lines:
            return
        for end in range(start + 1, n + 1):
            seg = words[start:end]
            w = text_w(" ".join(seg), fnt)
            if w > max_w:
                break
            rec(end, lines + [seg])

    rec(0, [])
    return best[1]


def fit(text, max_lines, max_w, start, floor, bold=True, balanced=False):
    """Largest font size in [floor, start] whose wrap fits in max_lines
    AND every line fits max_w. Returns (size, lines). Raises if the
    floor size still overflows."""
    size = start
    while size >= floor:
        fnt = font(size, bold)
        lines = (balanced_wrap(text, fnt, max_w, max_lines) if balanced
                 else wrap(text, fnt, max_w))
        if lines is not None and len(lines) <= max_lines and all(
                text_w(ln, fnt) <= max_w for ln in lines):
            return size, lines
        size -= 2
    fnt = font(floor, bold)
    lines = wrap(text, fnt, max_w)
    raise AssertionError(
        "OVERFLOW: %r needs %d lines at floor %dpx (max %d), widest %dpx > %dpx"
        % (text, len(lines), floor, max_lines,
           max(text_w(ln, fnt) for ln in lines), max_w))


def check_lines(lines, fnt, max_w, label):
    for ln in lines:
        w = text_w(ln, fnt)
        assert w <= max_w, "OVERFLOW %s: %r is %dpx > %dpx" % (label, ln, w, max_w)


# ---------------------------------------------------------------- icons
def draw_shield(dr, x, y, s):
    """Police shield + red star. s = icon box size."""
    import math
    # shield body: flat top, straight sides, pointed bottom
    dr.polygon([(x + s * 0.10, y + s * 0.06), (x + s * 0.90, y + s * 0.06),
                (x + s * 0.90, y + s * 0.52), (x + s * 0.50, y + s * 0.98),
                (x + s * 0.10, y + s * 0.52)], fill=INK)
    # 5-point star, centred
    cx, cy, r = x + s * 0.50, y + s * 0.40, s * 0.22
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    dr.polygon(pts, fill=RED)


def draw_candles(dr, x, y, w, h):
    """Six descending red candlesticks (AI sell-off)."""
    vals = [0.92, 0.78, 0.84, 0.62, 0.48, 0.30]  # top of body, fraction of h
    n = len(vals)
    slot = w / n
    bw = slot * 0.52
    base = y + h
    for i, v in enumerate(vals):
        cx = x + slot * i + slot / 2
        top = y + h * (1 - v)
        body_h = h * v * 0.55
        # wick
        dr.line([(cx, top - 8), (cx, top + body_h + 10)], fill=RED, width=3)
        # body
        dr.rectangle([cx - bw / 2, top, cx + bw / 2, top + body_h], fill=RED)
    # baseline
    dr.line([(x, base), (x + w, base)], fill=MUTED, width=2)


def draw_capitol(dr, cx, top, s, color):
    """Simple capitol dome: dome + drum + columns + base. s = total height."""
    w = s * 1.05
    x0 = cx - w / 2
    # base
    dr.rectangle([x0, top + s * 0.82, x0 + w, top + s * 0.94], fill=color)
    dr.rectangle([x0 + w * 0.08, top + s * 0.94, x0 + w * 0.92, top + s], fill=color)
    # columns
    for i in range(4):
        colx = x0 + w * (0.14 + i * 0.22)
        dr.rectangle([colx, top + s * 0.52, colx + w * 0.09, top + s * 0.82],
                     fill=color)
    # drum + dome
    dr.rectangle([x0 + w * 0.30, top + s * 0.34, x0 + w * 0.70, top + s * 0.52],
                 fill=color)
    dr.pieslice([x0 + w * 0.22, top, x0 + w * 0.78, top + s * 0.44],
                start=180, end=360, fill=color)
    # finial + flag
    dr.rectangle([cx - 2, top - s * 0.10, cx + 2, top], fill=color)
    dr.polygon([(cx + 2, top - s * 0.10), (cx + 2 + s * 0.22, top - s * 0.05),
                (cx + 2, top)], fill=RED)


def draw_ship_mine(dr, x, y, s):
    """Small ship hull + spiked mine. s = icon box size."""
    # mine: spiked circle, top-right
    mx, my, mr = x + s * 0.68, y + s * 0.26, s * 0.20
    for k in range(8):
        import math
        a = math.pi * k / 4
        dr.line([(mx + math.cos(a) * mr, my + math.sin(a) * mr),
                 (mx + math.cos(a) * (mr + s * 0.09),
                  my + math.sin(a) * (mr + s * 0.09))], fill=RED, width=3)
    dr.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=DARKRED,
               outline=RED, width=2)
    # hull
    dr.polygon([(x + s * 0.02, y + s * 0.62), (x + s * 0.58, y + s * 0.62),
                (x + s * 0.48, y + s * 0.86), (x + s * 0.12, y + s * 0.86)],
               fill=INK)
    # deck + mast
    dr.rectangle([x + s * 0.22, y + s * 0.48, x + s * 0.42, y + s * 0.62],
                 fill=INK)
    dr.line([(x + s * 0.32, y + s * 0.48), (x + s * 0.32, y + s * 0.22)],
            fill=INK, width=3)
    dr.polygon([(x + s * 0.32, y + s * 0.22), (x + s * 0.32, y + s * 0.38),
                (x + s * 0.50, y + s * 0.38)], fill=RED)


def draw_capsule(dr, x, y, s):
    """Space capsule + flame + stars. s = icon box size."""
    import math
    # stars
    for sx, sy, r in [(x + s * 0.08, y + s * 0.14, 4),
                      (x + s * 0.88, y + s * 0.10, 3),
                      (x + s * 0.94, y + s * 0.52, 4)]:
        dr.polygon([(sx, sy - r), (sx + r * 0.35, sy - r * 0.35),
                    (sx + r, sy), (sx + r * 0.35, sy + r * 0.35),
                    (sx, sy + r), (sx - r * 0.35, sy + r * 0.35),
                    (sx - r, sy), (sx - r * 0.35, sy - r * 0.35)], fill=INK)
    # flame
    dr.polygon([(x + s * 0.38, y + s * 0.78), (x + s * 0.62, y + s * 0.78),
                (x + s * 0.50, y + s * 0.98)], fill=GOLD)
    # body
    dr.rounded_rectangle([x + s * 0.30, y + s * 0.14, x + s * 0.70, y + s * 0.80],
                         radius=s * 0.14, fill=INK)
    # window
    dr.ellipse([x + s * 0.40, y + s * 0.30, x + s * 0.60, y + s * 0.50],
               fill=BLUE, outline=BASE, width=2)


def draw_trophy(dr, x, y, s):
    """Gold trophy cup. s = icon box size."""
    # handles
    dr.arc([x + s * 0.02, y + s * 0.22, x + s * 0.30, y + s * 0.58],
           start=90, end=270, fill=GOLD, width=5)
    dr.arc([x + s * 0.70, y + s * 0.22, x + s * 0.98, y + s * 0.58],
           start=270, end=90, fill=GOLD, width=5)
    # cup
    dr.polygon([(x + s * 0.20, y + s * 0.12), (x + s * 0.80, y + s * 0.12),
                (x + s * 0.68, y + s * 0.58), (x + s * 0.32, y + s * 0.58)],
               fill=GOLD)
    # stem + base
    dr.rectangle([x + s * 0.44, y + s * 0.58, x + s * 0.56, y + s * 0.76],
                 fill=GOLD)
    dr.rectangle([x + s * 0.28, y + s * 0.76, x + s * 0.72, y + s * 0.88],
                 fill=GOLD)


# ---------------------------------------------------------------- layout
img = Image.new("RGB", (W, H), BASE)
dr = ImageDraw.Draw(img)

# --- masthead: y 36..132 (h 96), red rule at 134..138, top row at 146
dr.text((M, 38), "THE WORLD IN ONE DAY", font=font(28), fill=MUTED)
date_size, date_lines = fit("WEDNESDAY, 25 NOVEMBER 2026",
                            max_lines=1, max_w=LIVE, start=58, floor=44)
assert len(date_lines) == 1
dr.text((M, 68), date_lines[0], font=font(date_size), fill=INK)
print("masthead date: %dpx" % date_size)
dr.rectangle([M, 136, M + LIVE, 140], fill=RED)

TOP_Y, TOP_H = 146, 480
BOT_Y, BOT_H = 646, 268
ALSO_Y, ALSO_H = 928, 60
assert TOP_Y + TOP_H + 20 == BOT_Y
assert BOT_Y + BOT_H + 14 == ALSO_Y
assert ALSO_Y + ALSO_H + M == H

LEAD_X, LEAD_W = M, 620
HOUSE_X, HOUSE_W = M + LEAD_W + GUT, 308
assert HOUSE_X + HOUSE_W + M == W

# --- lead panel: Indonesia / LSP treason suspects (rebuild 17:17 WIB)
dr.rounded_rectangle([LEAD_X, TOP_Y, LEAD_X + LEAD_W, TOP_Y + TOP_H],
                     radius=12, fill=PANEL)
lx, ly = LEAD_X + 24, TOP_Y + 24
dr.text((lx, ly), "INDONESIA", font=font(30), fill=RED)
lead_size, lead_lines = fit("Ex-police chief, 5 officers named treason suspects",
                            max_lines=3, max_w=LEAD_W - 48,
                            start=74, floor=56, balanced=True)
lfnt = font(lead_size)
check_lines(lead_lines, lfnt, LEAD_W - 48, "lead headline")
hy = ly + 30 + 14
for ln in lead_lines:
    dr.text((lx, hy), ln, font=lfnt, fill=INK)
    hy += int(lead_size * 1.12)
# subline (single line; "alleged" is load-bearing — the Jokowi link is
# alleged by critics, unproven; police named no other party as ordering it)
sub = "Wiretap plot vs Prabowo; Jokowi link alleged"
sfnt = font(24, bold=False)
check_lines([sub], sfnt, LEAD_W - 48, "lead subline")
sub_y = hy + 10
dr.text((lx, sub_y), sub, font=sfnt, fill=MUTED)
# visual band: shield + big "6" / SUSPECTS
band_y = sub_y + 24 + 14
band_h = 100
assert band_y + band_h <= TOP_Y + TOP_H - 24 - 28 - 10, \
    "lead visual band overflow: %d" % (band_y + band_h)
draw_shield(dr, lx, band_y, 96)
big = font(96)
six_x = lx + 118
dr.text((six_x, band_y - 4), "6", font=big, fill=RED)
sus_x = six_x + text_w("6", big) + 14
dr.text((sus_x, band_y + 40), "SUSPECTS", font=font(24), fill=INK)
# ticker line (pinned to bottom)
ticker = "MAKAR CHARGES \u2022 HEARING THU"
tfnt = font(28, bold=False)
check_lines([ticker], tfnt, LEAD_W - 48, "lead ticker")
ticker_y = TOP_Y + TOP_H - 24 - 28
dr.text((lx, ticker_y), ticker, font=tfnt, fill=MUTED)
print("lead headline: %dpx, %d lines: %s" % (lead_size, len(lead_lines), lead_lines))
print("lead visual band: y=%d h=%d" % (band_y, band_h))

# --- House panel: Democrats win the House
dr.rounded_rectangle([HOUSE_X, TOP_Y, HOUSE_X + HOUSE_W, TOP_Y + TOP_H],
                     radius=12, fill=PANEL)
hx = HOUSE_X + 16
dr.text((hx, TOP_Y + 20), "U.S. POLITICS", font=font(24), fill=BLUE)
draw_capitol(dr, HOUSE_X + HOUSE_W // 2, TOP_Y + 66, 76, INK)
house_size, house_lines = fit("Democrats win the House",
                              max_lines=3, max_w=HOUSE_W - 32,
                              start=46, floor=40)
hfnt = font(house_size)
check_lines(house_lines, hfnt, HOUSE_W - 32, "house headline")
hy = TOP_Y + 66 + 76 + 12
for ln in house_lines:
    dr.text((hx, hy), ln, font=hfnt, fill=INK)
    hy += int(house_size * 1.14)
num = font(88)
ny = hy + 6
dr.text((hx, ny), "259+", font=num, fill=INK)
seats_y = ny + 92
dr.text((hx, seats_y), "SEATS", font=font(24), fill=BLUE)
flips_y = seats_y + 30
dr.text((hx, flips_y), "majority flips", font=font(26, bold=False), fill=MUTED)
assert flips_y + 26 + 16 <= TOP_Y + TOP_H, "house panel overflow"
print("house headline: %dpx, %d lines: %s" % (house_size, len(house_lines), house_lines))

# --- bottom row: 3 panels, headline floor 44px
COL_W = [301, 302, 301]
COL_X = [M, M + 301 + GUT, M + 301 + GUT + 302 + GUT]
assert COL_X[2] + COL_W[2] + M == W

PANELS = [
    dict(kicker="MIDDLE EAST", accent=RED, icon="ship",
         headline="Mines hit 2 tankers", subline="Strait of Hormuz"),
    dict(kicker="SPACE", accent=BLUE, icon="capsule",
         headline="Pakistan's first astronaut", subline="Shenzhou-24 launch"),
    dict(kicker="AFCON", accent=GOLD, icon="trophy",
         headline="Senegal champions again", subline="Cup title regained"),
]
for (px, pw, p) in zip(COL_X, COL_W, PANELS):
    dr.rounded_rectangle([px, BOT_Y, px + pw, BOT_Y + BOT_H],
                         radius=12, fill=PANEL)
    ix = px + 16
    dr.text((ix, BOT_Y + 16), p["kicker"], font=font(24), fill=p["accent"])
    icon_fn = {"ship": draw_ship_mine, "capsule": draw_capsule,
               "trophy": draw_trophy}[p["icon"]]
    icon_fn(dr, px + pw - 16 - 52, BOT_Y + 14, 52)
    size, lines = fit(p["headline"], max_lines=3, max_w=pw - 32,
                      start=44, floor=44)
    fnt = font(size)
    check_lines(lines, fnt, pw - 32, p["kicker"] + " headline")
    hy = BOT_Y + 16 + 52 + 8
    for ln in lines:
        dr.text((ix, hy), ln, font=fnt, fill=INK)
        hy += 48
    sub = font(26, bold=False)
    check_lines([p["subline"]], sub, pw - 32, p["kicker"] + " subline")
    dr.text((ix, BOT_Y + BOT_H - 16 - 26), p["subline"], font=sub, fill=MUTED)
    assert hy <= BOT_Y + BOT_H - 16 - 26 - 6, \
        "%s headline collides with subline" % p["kicker"]
    print("%s: %dpx, %d lines: %s" % (p["kicker"], size, len(lines), lines))

# --- Also strip: Gaza + Nvidia / Cartagena / Indonesia mine rescue
# (Nvidia moved here from the lead; stale "VP resigns" (12 Nov) dropped)
dr.rounded_rectangle([M, ALSO_Y, M + LIVE, ALSO_Y + ALSO_H],
                     radius=10, fill=PANEL)
ax = M + 16
also1 = "Gaza strikes kill 7, incl. senior Hamas official"
also2 = "Nvidia sheds 7% \u2022 Cartagena: 20 hostages held \u2022 Indonesia mine rescue"
afnt = font(22)
label = "ALSO: "
dr.text((ax, ALSO_Y + 7), label, font=font(22), fill=RED)
dr.text((ax + text_w(label, afnt), ALSO_Y + 7), also1, font=afnt, fill=INK)
dr.text((ax, ALSO_Y + 32), also2, font=afnt, fill=INK)
check_lines([label + also1], afnt, LIVE - 32, "also line 1")
check_lines([also2], afnt, LIVE - 32, "also line 2")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
img.save(out, format="PNG")
data = open(out, "rb").read()
print("saved %s: %d bytes, sha256 %s" % (out, len(data),
                                        hashlib.sha256(data).hexdigest()))
assert len(data) <= 1048576, "entry.png over 1 MiB"
assert img.size == (1024, 1024)
print("OK: 1024x1024, under 1 MiB, layout asserts passed")
