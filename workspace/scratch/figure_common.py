#!/usr/bin/env python3
# figure_common -- shared machinery for the AGENTSCII "figurative / character" family.
#
# WHY THIS EXISTS (the gap hollis + Tyler named, with numbers)
#   41 pieces shipped, only 2 are figurative/character work, both solo busts built by
#   hand-rolling shading + anatomy from scratch (make_portrait.py, make_portrait_acid.py).
#   The other 34 are procedural/math-pattern and share curve_common.py / scroll_lib.py,
#   which is exactly why they're cheap to produce well. Figurative work had NO reusable
#   technique base -- so it stayed rare. This module is the missing equivalent: a
#   curve_common.py for faces/figures.
#
# THE TECHNIQUE GAP THIS CLOSES (study reference/study/we-ACiDTrip.ANS @ row 2160)
#   Real ACiD character work is GRADIENT-BUILT ANATOMY, not flat block-color silhouettes:
#     - a light source falls across the FORM so the brow ridge catches more light than the
#       eye socket beneath it; the cheekbone and jaw are shaded as separate surfaces.
#     - eyes are CONSTRUCTED (dark socket -> colored iris -> white glint), not a dot.
#     - teeth are individual bright cells against a dark mouth cavity.
#   The two existing portraits do flat single-color shapes with one upper-left light term
#   and no per-feature structure. This module makes the gradient-anatomy idiom reusable so
#   the next figurative piece is a composition, not a from-scratch shading engine.
#
# API (mirrors curve_common.py: helpers + a render pass + sig block + hygiene gate)
#   light_field(x,y, lx,ly, lmax, ambient)  -> 0..1 diffuse light from a source
#   shade(L, ramp, base_fg, hot_fg)        -> (glyph, fg) density+brightness from light
#   surface(cv, region, L, ramp, ...)      -> paint a body region with gradient shading
#   ridge / crease / brow helpers          -> build individual anatomical features
#   eye(cv, cx,cy, r, iris_fg, glint)      -> constructed eye (socket/iris/glint)
#   teeth(cv, x0,x1, y, n)                 -> bright teeth row in a dark cavity
#   render(cv, out)                        -> flush a [ch,fg,bg] canvas to SGR rows
#   sig_block / hygiene_gate               -> house standard (identical to curve_common)

import math
import re

W = 80
H = 46
CX = W / 2.0
CY = H / 2.0
ESC = "\x1b["
def sgr(*codes): return ESC + ";".join(str(x) for x in codes) + "m"
RESET = ESC + "0m"

# density ramp, light->dark (full block first). The shading carrier.
RAMP = "\u2588\u2593\u2592\u2591"

# house hue wheel (matches curve_common exactly so figurative work sits in the same family)
HUE = [95, 91, 93, 92, 96, 94, 107, 103]


def c(fg, bg=0):
    """fg,bg: a 0-7/8-15 color INDEX -> SGR string. Idempotent for an ALREADY-ENCODED
    SGR code (30-47 / 90-107): those pass through untouched.

    WHY THE GUARD EXISTS (raze, ORACLE pass -- the double-map gotcha): shade() returns a
    BRIGHT-range fg (8-15) and callers sometimes feed that straight back into c(). The old
    body did `90 + (fg & 7)` for any fg>7, so an already-bright SGR code like 93 (bright
    yellow) double-mapped to 95 (bright magenta) -- a silent color corruption that made an
    amber head vanish into a yellow wash. WARDEN//VESSEL only survived because its base_fgs
    happened to map sensibly through the double-map; ORACLE caught it. The guard makes c()
    safe for both call shapes (index in, or SGR-code in) without changing any 0-15 behavior."""
    f = fg if (30 <= fg <= 47 or 90 <= fg <= 107) else ((90 + (fg & 7)) if fg > 7 else (30 + (fg & 7)))
    b = bg if (40 <= bg <= 47 or 100 <= bg <= 107) else ((100 + (bg & 7)) if bg > 7 else (40 + (bg & 7)))
    return "\x1b[%d;%dm" % (f, b)

def c_bright(fg, bg=0):
    """Convenience: force the bright/extended-bright range for a 0-7 hue index. Use this
    when you KNOW you want brightness and are passing a plain hue index (not shade()'s
    output). For shade() output just call c() -- it now passes SGR codes through."""
    f = 90 + (fg & 7)
    b = 100 + (bg & 7)
    return "\x1b[%d;%dm" % (f, b)


# --- canvas: each cell is [char, fg, bg] -------------------------------------
def new_canvas(h=H, w=W):
    return [[[' ', 0, 0] for _ in range(w)] for _ in range(h)]

def set_cell(cv, x, y, ch, fg, bg=0):
    if 0 <= x < len(cv[0]) and 0 <= y < len(cv):
        cv[y][x] = [ch, fg, bg]

# --- lighting: the heart of gradient-built anatomy ---------------------------
def light_field(x, y, lx, ly, lmax=24.0, ambient=0.12):
    """Diffuse light 0..1 from a point source at (lx,ly). ambient lifts the floor so
    shadowed surfaces still read as form, not void -- this is what makes a shaded region
    look like a lit surface instead of a flat fill."""
    dx = x - lx
    dy = y - ly
    d = math.hypot(dx, dy) / lmax
    return max(ambient, min(1.0, 1.0 - d)) + ambient * 0.0


def shade(L, base_fg=7, hot_fg=15, ramp=RAMP):
    """Map a light value 0..1 -> (glyph, fg). Density AND brightness both track the light,
    so a lit surface is bright+full and a shadowed one is dim+thin. This single function is
    what turns flat block-color shapes into gradient-built anatomy: feed it per-cell light
    from a form-aware source and the surface reads as 3D."""
    L = max(0.0, min(1.0, L))
    idx = int(L * (len(ramp) - 1) + 0.5) % len(ramp)
    fg = hot_fg if L > 0.82 else base_fg
    return ramp[idx], fg


# --- anatomical regions: each feature is its own shaded surface ---------------
def ellipse_hw(y, cy, ry, rx):
    """Half-width of an ellipse at row y (None if outside). The head/skull primitive."""
    t = (y - cy) / ry
    if abs(t) > 1.0:
        return None
    return rx * math.sqrt(1.0 - t * t)


def shade_region(cv, region_fn, Lfn, base_fg=7, hot_fg=15, ramp=RAMP):
    """Paint every cell region_fn(x,y)->True with gradient shading from light Lfn(x,y).
    region_fn is the ANATOMY (which cells belong to this surface); Lfn is the LIGHT that
    falls on it. Separate these and you get per-feature structure: brow, socket, cheek,
    jaw are each a region with its own light term -> individually shaded anatomy."""
    for y in range(len(cv)):
        for x in range(len(cv[0])):
            if region_fn(x, y):
                ch, fg = shade(Lfn(x, y), base_fg, hot_fg, ramp)
                set_cell(cv, x, y, ch, fg, 0)


def specular_shade(cv, region_fn, Lfn, x_hl, y_hl, hl_r,
                    base_fg=7, hot_fg=15, spec_fg=15, ramp=RAMP):
    """Diffuse surface shading PLUS a tight specular highlight -- studied
    from references/study/blocktronics-ra_mindseye.ANS and
    blocktronics-we_c22.ANS (both real ACiD/Blocktronics pieces with
    genuine gloss/reflection reads on curved/metallic surfaces). Different
    from shade_region()'s plain diffuse falloff: this adds a SECOND,
    SMALL, TIGHT bright core near (x_hl, y_hl) on top of the normal
    diffuse shading -- a specular highlight is small and sharp-edged
    (unlike the broad soft diffuse falloff), which is exactly what reads
    as "glossy/wet/metallic" rather than "matte." Use this for eyes,
    metal, glass, wet surfaces -- anything with a reflective quality;
    shade_region() alone is correct for matte skin/stone/fabric.

    region_fn/Lfn: same as shade_region() -- diffuse base pass first.
    x_hl, y_hl: the highlight's center (usually near, not on, the surface's
      brightest diffuse point -- a real specular highlight sits slightly
      OFF the diffuse peak, which is part of what sells the gloss read).
    hl_r: highlight radius in cells -- keep this SMALL (1.5-3 cells) or it
      stops reading as a tight reflection and just looks like a second
      light source."""
    for y in range(len(cv)):
        for x in range(len(cv[0])):
            if not region_fn(x, y):
                continue
            L = Lfn(x, y)
            d_hl = math.hypot(x - x_hl, y - y_hl)
            if d_hl <= hl_r:
                # inside the specular core: fully bright, full-density glyph,
                # regardless of the diffuse term -- a highlight overrides
                # the surface's own shading, it doesn't blend with it.
                falloff = max(0.0, 1.0 - (d_hl / hl_r))
                if falloff > 0.6:
                    set_cell(cv, x, y, ramp[0], spec_fg, 0)
                    continue
            ch, fg = shade(L, base_fg, hot_fg, ramp)
            set_cell(cv, x, y, ch, fg, 0)


def photoreal_gradient(cv, region_fn, cx, cy, hue_stops, max_dist=None):
    """Smooth multi-hue radial gradient across a region -- studied from
    references/study/blocktronics-avg_16c.ANS (a real ACiD piece using a
    genuinely photorealistic multi-color transition, not the house's usual
    single-hue density ramp). Different from canvas.gradient_fill(): that
    interpolates DENSITY within one hue (bright-to-dim of the same color);
    this interpolates across MULTIPLE distinct hues in sequence (e.g.
    yellow -> orange -> red -> magenta), which is what produces a painterly
    "photo" look instead of a flat-color-with-shading look. Use this for
    skin tones, sunsets, painterly portrait work -- anywhere the reference
    shows a real color SPECTRUM, not just one hue's brightness varying.

    region_fn(x,y) -> bool: where the gradient applies.
    hue_stops: an ordered list of fg color indices, e.g. [11, 9, 1, 5]
      (bright yellow -> amber -> red -> magenta) -- the gradient walks
      through them in order from center (index 0) to edge (last index).
    max_dist: gradient radius; defaults to covering the whole region."""
    if max_dist is None:
        max_dist = max(len(cv[0]), len(cv)) / 2.0
    n = len(hue_stops)
    for y in range(len(cv)):
        for x in range(len(cv[0])):
            if not region_fn(x, y):
                continue
            d = math.hypot(x - cx, y - cy) / max_dist
            d = max(0.0, min(1.0, d))
            # which pair of adjacent hue stops does this distance fall
            # between, and how far through that pair (for the density ramp
            # to carry the local transition, not just a hard color swap)
            pos = d * (n - 1)
            idx = min(n - 2, int(pos))
            local_t = pos - idx
            fg = hue_stops[idx] if local_t < 0.5 else hue_stops[idx + 1]
            ramp_idx = int(abs(local_t - 0.5) * 2 * (len(RAMP) - 1))
            set_cell(cv, x, y, RAMP[ramp_idx], fg, 0)


def brow_ridge(cv, cx, cy, halfw, light, base_fg=7, hot_fg=15):
    """A lit brow ridge: a thin horizontal band whose top edge catches the most light and
    falls off into the eye socket below -- the single most 'anatomical' read in a face."""
    for y in range(int(cy - 1), int(cy + 2)):
        hw = halfw * math.sqrt(max(0.0, 1.0 - ((y - cy) / 1.5) ** 2))
        for x in range(int(cx - hw), int(cx + hw) + 1):
            # light peaks at the ridge crest (top of band), falls toward the socket
            L = light(x, y) * (0.95 if y <= cy else 0.72)
            ch, fg = shade(L, base_fg, hot_fg)
            set_cell(cv, x, y, ch, fg, 0)


def eye(cv, cx, cy, r=1.4, iris_fg=96, glint=True):
    """A CONSTRUCTED eye: not a flat dot, not a single color.

    REDESIGNED 2026-09-15 after finding it was fundamentally broken at
    every radius tested (r=1.4 through r=6). Two separate bugs, both real:
    (1) distance was measured as plain Euclidean (x,y) cell-distance, but
    terminal cells are ~2x taller than wide, so a "circle" rendered as a
    squashed vertical stripe -- fixed with an aspect-corrected distance.
    (2) even fixed, concentric RINGS (socket -> sclera -> iris) fundamentally
    alias into flat horizontal color bands on a low-resolution block grid
    at the radii actually used in real pieces (r=1.4-3) -- a thin 1-cell
    ring just doesn't have enough pixels to read as a curve at that scale,
    aspect-correct or not. Confirmed by direct rendered-image inspection,
    not assumed.

    Fix: two different constructions depending on scale, not one ring
    model stretched across all sizes.
      - r < 2.2 (the common case: a face-scale eye): a SMALL CLUSTER, not
        concentric rings -- a solid iris disc, an off-center glint, and a
        few individual dark accent marks (not a full ring) suggesting a
        socket without needing enough resolution to render a real circle.
        This is closer to how real small-scale ANSI eyes are actually
        built (see references/study/somms-neo_tokyo.ANS) -- a handful of
        deliberate marks, not a scaled-down version of a big shape.
      - r >= 2.2 (a large/ambition-tier eye with real pixel budget):
        the aspect-corrected ring construction, which DOES read correctly
        at this scale (verified via rendered test at r=4-6)."""
    ASPECT = 0.5   # cells are ~2x taller than wide; shrink y-delta to compensate
    def dist(x, y):
        return math.hypot(x - cx, (y - cy) / ASPECT)

    if r < 2.2:
        # --- small-scale cluster construction -----------------------------
        icx, icy = int(round(cx)), int(round(cy))
        # iris: a small solid disc, 1-2 cells depending on r
        iris_r = max(1, r * 0.7)
        for y in range(icy - 2, icy + 3):
            for x in range(icx - 2, icx + 3):
                if dist(x, y) <= iris_r:
                    set_cell(cv, x, y, "\u2588", iris_fg, 0)
        # dark accent marks flanking the iris (suggest a socket without a
        # full ring) -- left/right only, not top/bottom, since the aspect
        # squash means top/bottom marks sit too close to read as separate
        set_cell(cv, icx - 2, icy, "\u2591", 8, 0)
        set_cell(cv, icx + 2, icy, "\u2591", 8, 0)
        # glint: single bright cell, offset upper-left of the iris center
        if glint:
            set_cell(cv, icx - 1, icy - 1, "\u2588", 15, 0)
        return

    # --- large-scale ring construction (r >= 2.2) -------------------------
    # socket: dim shadowed ring around the eyeball
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            d = dist(x, y)
            if r < d <= r + 1.0:
                set_cell(cv, x, y, "\u2591", 8, 0)        # shadowed socket wall
    # eyeball: light sclera
    rr = int(round(r))
    for y in range(int(cy) - rr, int(cy) + rr + 1):
        for x in range(int(cx) - rr, int(cx) + rr + 1):
            d = dist(x, y)
            if d <= r:
                set_cell(cv, x, y, "\u2588", 15, 0)
    # iris: colored core
    for y in range(int(cy - r * 0.6), int(cy + r * 0.6 + 1)):
        for x in range(int(cx - r * 0.6), int(cx + r * 0.6 + 1)):
            d = dist(x, y)
            if d <= r * 0.6:
                set_cell(cv, x, y, "\u2588", iris_fg, 0)
    # glint: a single white catch-light, upper-left (light side)
    if glint:
        set_cell(cv, int(cx - r * 0.3), int(cy - r * 0.3 * ASPECT), "\u2588", 15, 0)


def teeth(cv, x0, x1, y, n=6):
    """Bright individual teeth in a dark mouth cavity -- the grin read.
    Casts x/y to int so callers may pass float coordinates (a shared-infra
    courtesy -- raze flagged this after casting at the call site)."""
    x0, x1, y = int(x0), int(x1), int(y)
    for x in range(x0, x1 + 1):
        set_cell(cv, x, y, "\u2580", 15, 0)           # upper tooth edge (bright)
        set_cell(cv, x, y + 1, " ", 0, 0)             # cavity gap between teeth

# --- render + house standard --------------------------------------------------
def render(cv, out):
    """Flush a [ch,fg,bg] canvas to SGR rows. Coalesces runs of same-color cells so the
    output is compact like real ANSI art, not one escape per cell.

    raze fix (stride pass): the old coalescer grouped by COLOR only and repeated the
    FIRST char for the whole run -- so a multi-char text run in one color (e.g. a title
    'STRIDE' all at fg=94) collapsed to 'SSSSSS'. A real ANSI piece has exactly this:
    runs of same-color but DIFFERENT glyphs (text, sig blocks). Coalesce on the full
    [ch,fg,bg] triple so distinct chars stay distinct; still one SGR per color change."""
    for y in range(len(cv)):
        row = cv[y]
        i = 0
        line = ""
        last_sgr = None
        while i < len(row):
            ch, fg, bg = row[i]
            run = 1
            while i + run < len(row) and row[i + run] == [ch, fg, bg]:
                run += 1
            sgr = c(fg, bg)
            if sgr != last_sgr:
                line += sgr
                last_sgr = sgr
            line += ch * run
            i += run
        out.append(line)

def sig_block(out, title, handles="hollis / raze"):
    """House standard for full-bleed pieces (identical shape to curve_common.sig_block)."""
    out.append("")
    out.append(sgr(105, 40) + "\u2560" + sgr(104, 40) + "\u2550" * (W - 1))
    def sigline(text, fg):
        pad = W - len(text)
        left = pad // 2
        return sgr(104, 40) + " " * left + sgr(fg, 40) + text + sgr(104, 40) + " " * (pad - left)
    out.append(sigline(handles + " / AGENTSCII", 97))
    out.append(sigline(title, 96))
    out.append(sgr(105, 40) + "\u2563" + sgr(104, 40) + "\u2550" * (W - 1))


def hygiene_gate(path):
    raw = open(path, "rb").read()
    ctrl = sorted(set(b for b in raw if b < 0x20 or b == 0x7f))
    print("bytes:", len(raw), "ctrl bytes:", [hex(x) for x in ctrl])
    try:
        raw.decode("cp437"); print("cp437 on disk: OK")
    except Exception as e:
        print("cp437 FAIL", e)
    sgrs = re.findall(rb"\x1b\[([0-9;]*)m", raw)
    bad = []
    for s in sgrs:
        for tok in (s.decode() or "0").split(";"):
            if tok == "": continue
            v = int(tok)
            if not (v == 0 or 30 <= v <= 37 or 40 <= v <= 47 or 90 <= v <= 107):
                bad.append(v)
    print("SGR tokens:", len(sgrs), "out-of-range:", sorted(set(bad)))
    disp = re.sub(rb"\x1b\[[0-9;]*m", b"", raw).decode("cp437")
    widths = set(len(l) for l in disp.split("\n"))
    print("row widths:", sorted(widths))
    blank_runs, run = [], 0
    for l in disp.split("\n"):
        if l.strip() == "":
            run += 1
        else:
            if run >= 3: blank_runs.append(run)
            run = 0
    if run >= 3: blank_runs.append(run)
    print("blank runs >=3:", blank_runs)
    print("ends on standalone reset:", raw.rstrip().endswith(b"\x1b[0m"))


if __name__ == "__main__":
    # self-test: build a tiny shaded head to prove the gradient-anatomy idiom works.
    import sys
    out = []
    cv = new_canvas(30, 80)
    cx = 40
    cy = 12
    lx, ly = cx - 9, cy - 6          # light upper-left
    def L(x, y): return light_field(x, y, lx, ly, lmax=20.0, ambient=0.15)
    # skull: shaded ellipse surface (gradient-built, not flat)
    shade_region(cv, lambda x, y: abs((y - cy) / 7.0) <= 1.0 and
                 abs(x - cx) <= 13 * math.sqrt(max(0.0, 1 - ((y - cy) / 7.0) ** 2)),
                 L, base_fg=96, hot_fg=15)
    brow_ridge(cv, cx, cy - 2, 8, L, base_fg=96, hot_fg=15)
    eye(cv, cx - 4, cy, r=1.4, iris_fg=93)
    eye(cv, cx + 4, cy, r=1.4, iris_fg=93)
    teeth(cv, cx - 5, cx + 5, cy + 5, n=6)
    render(cv, out)
    sys.stdout.write("\n".join(out) + "\x1b[0m\n")


# ============================================================================
# STANDING-FIGURE LAYER   (raze, joint-VIGIL pass -- extends the bust base to a
# full figure so figure_common.py is a real curve_common.py for FIGURES, not just
# faces. Composes from shade()/light_field() exactly like the head primitives do:
# every limb/torso surface is gradient-shaded from one light source, so a standing
# pose reads as lit 3D anatomy, not a flat block silhouette.)
#
# WHY THIS EXISTS: warden/vessel proved the HEAD idiom (skull/brow/eye/teeth). The
# joint second-figure brief (hollis) is a STANDING figure -- posture + limbs. That
# needs limb/torso surfaces that the head-only module didn't have. These are the
# missing primitives; VIGIL is the proof they work as a shared base, not a bolt-on.
# ============================================================================

def capsule(cv, x0, y0, x1, y1, halfw, Lfn, base_fg=7, hot_fg=15, ramp=RAMP):
    """A limb/torso SURFACE: a thick rounded segment (a 'capsule') between two points,
    shaded by light Lfn so it reads as a lit 3D tube, not a flat bar. This is the
    gradient-anatomy equivalent of a line() -- the building block for arms/legs/torso.

    halfw = half-thickness in cells. The capsule is the MINKOWSKY sum of the segment and
    a disk of radius halfw (every cell within halfw of the segment), which gives rounded
    ends instead of a hard rectangle -- limbs read as limbs, not as bars."""
    seg_len = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / seg_len, (y1 - y0) / seg_len       # unit along segment
    hw = int(round(halfw))
    for y in range(int(min(y0, y1)) - hw - 1, int(max(y0, y1)) + hw + 2):
        for x in range(int(min(x0, x1)) - hw - 1, int(max(x0, x1)) + hw + 2):
            # project (x,y) onto the segment; distance to the segment = perpendicular dist
            t = max(0.0, min(1.0, ((x - x0) * ux + (y - y0) * uy) / seg_len))
            px, py = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
            d = math.hypot(x - px, y - py)
            if d <= halfw:
                # light modulated by a cylindrical term: distance from the segment axis
                # falls off toward the limb's edge -> rounded shading on each tube.
                L = Lfn(x, y) * (1.0 - 0.35 * (d / halfw))
                ch, fg = shade(L, base_fg, hot_fg, ramp)
                set_cell(cv, x, y, ch, fg, 0)


def joint_dot(cv, cx, cy, r, Lfn, base_fg=7, hot_fg=15):
    """A rounded joint (elbow/shoulder/knee/hip): a small shaded disk that bridges two
    capsule limbs so the limb reads as one continuous tube through the joint, not two bars
    that meet at a point. Without this, bent limbs look broken."""
    rr = int(round(r))
    for y in range(int(cy) - rr, int(cy) + rr + 1):
        for x in range(int(cx) - rr, int(cx) + rr + 1):
            if math.hypot(x - cx, y - cy) <= r:
                ch, fg = shade(Lfn(x, y), base_fg, hot_fg)
                set_cell(cv, x, y, ch, fg, 0)


def standing_figure(cv, hipx, hipy, Lfn, *,
                    height=18.0, stance="contrapposto",
                    base_fg=7, hot_fg=15, iris_fg=96, one_eye=True):
    """Build a full STANDING figure from shaded capsule surfaces + the head primitives.
    This is the joint-VIGIL unit: call it and you get a posed full-body figure lit by
    Lfn -- the gradient-anatomy idiom extended from a bust to a whole body.

    stance: 'contrapposto' = weight on one leg, hips/shoulders tilt opposite (the only pose
      that actually reads as 'standing' in block chars; symmetric looks like a mannequin).
      'attn' = symmetric standing-at-attention (both legs straight down) -- simpler but flat.
    height: total figure height in cells (head-to-foot), sets the proportions.
    one_eye: True -> single visible eye + brow on a 3/4 head (reads as turned, more alive);
      False -> two front-facing eyes (warden idiom)."""
    # --- proportions from hip point upward/downward ---------------------------
    torso_h = height * 0.34
    leg_h   = height * 0.46
    head_r  = max(2.0, height * 0.11)
    shoulder_y = hipy - torso_h
    neck_y     = shoulder_y - head_r * 0.4
    head_cy    = neck_y - head_r

    # --- hips / shoulders tilt for contrapposto ------------------------------
    # v3 (curator note on v2): a flat pelvis + straight vertical torso reads as a stiff
    # mannequin. The loosening is structural -- TILT the pelvis (weight-side hip rises,
    # free-side hip drops), COUNTER-TILT the shoulders over the weight foot, and S-CURVE
    # the spine through a waist bend so the torso isn't a straight tube. 'attn' stays flat.
    if stance == "contrapposto":
        hip_dx = leg_h * 0.12                       # hip half-width, a touch wider for a real span
        hip_lx, hip_rx = hipx - hip_dx, hipx + hip_dx
        hip_l_y = hipy - 1.0                        # weight-side (left) hip lifts -- leg straightens
        hip_r_y = hipy + 1.5                        # free-side (right) hip drops -- the loosening
        sh_dx = torso_h * 0.34                      # shoulders counter-tilt over the weight foot
        sh_lx, sh_rx = hipx - sh_dx, hipx + sh_dx
        sh_l_y = shoulder_y + 1.2                   # weight-side (left) shoulder drops
        sh_r_y = shoulder_y - 1.2                   # free-side (right) shoulder rises
    else:
        hip_lx, hip_rx = hipx - 3.0, hipx + 3.0
        hip_l_y = hip_r_y = hipy                    # flat pelvis for at-attention
        sh_dx = 0.0
        sh_lx, sh_rx = hipx - 4.0, hipx + 4.0
        sh_l_y = sh_r_y = shoulder_y

    # --- TORSO: pelvis bar + S-curved spine + shoulders bar (contrapposto) ----
    if stance == "contrapposto":
        capsule(cv, hip_lx, hip_l_y, hip_rx, hip_r_y, halfw=3.0, Lfn=Lfn,   # tilted pelvis bar
                base_fg=base_fg, hot_fg=hot_fg)
        joint_dot(cv, (hip_lx + hip_rx) / 2, (hip_l_y + hip_r_y) / 2, 3.4, Lfn, base_fg, hot_fg)
        waist_x = hipx + 0.6                        # slight lean toward the weight foot at the top
        waist_y = (hipy + shoulder_y) / 2
        capsule(cv, (hip_lx + hip_rx) / 2, (hip_l_y + hip_r_y) / 2, waist_x, waist_y, halfw=4.6,
                Lfn=Lfn, base_fg=base_fg, hot_fg=hot_fg)                    # lower spine
        joint_dot(cv, waist_x, waist_y, 3.8, Lfn, base_fg, hot_fg)
        capsule(cv, waist_x, waist_y, hipx, shoulder_y, halfw=4.0, Lfn=Lfn,   # upper spine to shoulders
                base_fg=base_fg, hot_fg=hot_fg)
        joint_dot(cv, hipx, (waist_y + shoulder_y) / 2, 3.6, Lfn, base_fg, hot_fg)
        capsule(cv, sh_lx, sh_l_y, sh_rx, sh_r_y, halfw=2.0, Lfn=Lfn,        # tilted shoulders bar
                base_fg=base_fg, hot_fg=hot_fg)
    else:
        capsule(cv, hipx, hipy, hipx, shoulder_y, halfw=4.0, Lfn=Lfn,       # straight vertical torso
                base_fg=base_fg, hot_fg=hot_fg)

     # --- LEGS: two capsules from each hip to the feet ------------------------
    foot_lx = hip_lx - (1.5 if stance == "contrapposto" else 0.0)
    foot_rx = hip_rx + (2.0 if stance == "contrapposto" else 0.0)
      # --- LEGS: weight leg straight down; free leg BENT at the knee ----------
     # v3.1 (curator note on v3): even with the tilted pelvis + S-spine, a single
     # straight capsule for the free leg still reads stiff -- a real relaxed
     # contrapposto has the FREE leg bent at the knee (foot stays planted, knee
     # angles out/back so the weight is clearly off it). Two-segment thigh+shin
     # through a knee joint_dot sells the relaxation; 'attn' keeps both legs straight.
    if stance == "contrapposto":
         # WEIGHT leg: straight down from the (lifted) hip to its foot.
        capsule(cv, hip_lx, hip_l_y, foot_lx, hipy + leg_h, halfw=2.6, Lfn=Lfn,
                base_fg=base_fg, hot_fg=hot_fg)
        joint_dot(cv, (hip_lx + foot_lx) / 2, hipy + leg_h * 0.5, 1.6, Lfn, base_fg, hot_fg)
         # FREE leg: thigh from the (dropped) hip to a knee that angles OUT+BACK,
         # then a shin down to a foot planted slightly forward -- the classic relaxed
         # weight-shift. Knee sits below the hip line and outboard of the dropped hip.
        knee_x = hip_rx + 1.4                        # knee kicks outboard of the dropped hip
        knee_y = hipy + leg_h * 0.52                 # a touch below mid-thigh
        foot_fx = hip_rx - 0.3                      # free foot planted slightly inboard/forward
        capsule(cv, hip_rx, hip_r_y, knee_x, knee_y, halfw=2.4, Lfn=Lfn,      # thigh
                base_fg=base_fg, hot_fg=hot_fg)
        joint_dot(cv, knee_x, knee_y, 1.7, Lfn, base_fg, hot_fg)              # the bent knee
        capsule(cv, knee_x, knee_y, foot_fx, hipy + leg_h * 0.96, halfw=2.3, Lfn=Lfn,   # shin
                base_fg=base_fg, hot_fg=hot_fg)
    else:
         # at-attention: both legs straight down from a flat pelvis.
        capsule(cv, hip_lx, hip_l_y, foot_lx, hipy + leg_h, halfw=2.6, Lfn=Lfn,
                base_fg=base_fg, hot_fg=hot_fg)
        capsule(cv, hip_rx, hip_r_y, foot_rx, hipy + leg_h * 0.94, halfw=2.4, Lfn=Lfn,
                base_fg=base_fg, hot_fg=hot_fg)
        joint_dot(cv, (hip_lx + foot_lx) / 2, hipy + leg_h * 0.5, 1.6, Lfn, base_fg, hot_fg)
        joint_dot(cv, (hip_rx + foot_rx) / 2, hipy + leg_h * 0.5, 1.5, Lfn, base_fg, hot_fg)

     # --- ARMS: one across the body (the 'watch' read), one relaxed out -------
    elbow_y = shoulder_y + torso_h * 0.42
    if stance == "contrapposto":
        across_hand_x = hipx + 1.5                 # hand reaches across to the OPPOSITE hip
        capsule(cv, sh_lx, sh_l_y, sh_lx - 0.5, elbow_y, halfw=2.6, Lfn=Lfn,   # upper arm down
                base_fg=base_fg, hot_fg=hot_fg)
        joint_dot(cv, (sh_lx + sh_lx - 0.5) / 2, (sh_l_y + elbow_y) / 2, 1.4, Lfn, base_fg, hot_fg)
        capsule(cv, sh_lx - 0.5, elbow_y, across_hand_x, hipy - torso_h * 0.18, halfw=2.4, Lfn=Lfn,
                base_fg=base_fg, hot_fg=hot_fg)                   # forearm across to opposite hip
        joint_dot(cv, (sh_lx - 0.5 + across_hand_x) / 2, (elbow_y + hipy - torso_h * 0.18) / 2,
                  1.3, Lfn, base_fg, hot_fg)
        free_hand_x = sh_rx + 1.6                # free arm angles OUT and hangs relaxed
        capsule(cv, sh_rx, sh_r_y, sh_rx + 0.6, elbow_y, halfw=2.5, Lfn=Lfn,   # upper arm out
                base_fg=base_fg, hot_fg=hot_fg)
        joint_dot(cv, (sh_rx + sh_rx + 0.6) / 2, (sh_r_y + elbow_y) / 2, 1.3, Lfn, base_fg, hot_fg)
        capsule(cv, sh_rx + 0.6, elbow_y, free_hand_x, shoulder_y + torso_h * 0.95, halfw=2.3, Lfn=Lfn,
                base_fg=base_fg, hot_fg=hot_fg)                   # forearm out + relaxed
    else:
        capsule(cv, sh_lx, shoulder_y, hipx - 1, shoulder_y + torso_h * 0.7, halfw=2.0, Lfn=Lfn,
                base_fg=base_fg, hot_fg=hot_fg)                   # across-body arm
        joint_dot(cv, (sh_lx + hipx - 1) / 2, elbow_y, 1.4, Lfn, base_fg, hot_fg)
        capsule(cv, sh_rx, shoulder_y, sh_rx + 1, shoulder_y + torso_h * 0.85, halfw=1.9, Lfn=Lfn,
                base_fg=base_fg, hot_fg=hot_fg)                   # at-side arm

    # --- HEAD: shaded skull ellipse + brow + constructed eye(s) ---------------
    shade_region(cv, lambda x, y: abs((y - head_cy) / head_r) <= 1.0 and
                 abs(x - hipx) <= head_r * 1.25 * math.sqrt(max(0.0, 1 - ((y - head_cy) / head_r) ** 2)),
                 Lfn, base_fg=base_fg, hot_fg=hot_fg)
    brow_ridge(cv, hipx, head_cy - head_r * 0.35, head_r * 0.9, Lfn, base_fg, hot_fg)
    if one_eye:
        eye(cv, hipx + head_r * 0.25, head_cy + head_r * 0.1, r=head_r * 0.45,
            iris_fg=iris_fg, glint=True)
    else:
        eye(cv, hipx - head_r * 0.5, head_cy + head_r * 0.1, r=head_r * 0.42,
            iris_fg=iris_fg, glint=True)
        eye(cv, hipx + head_r * 0.5, head_cy + head_r * 0.1, r=head_r * 0.42,
            iris_fg=iris_fg, glint=True)

    return dict(hip=(hipx, hipy), shoulder_y=shoulder_y, head_cy=head_cy,
                foot_lx=foot_lx, foot_rx=foot_rx, head_r=head_r)
