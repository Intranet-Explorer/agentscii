# AGENTSCII methodology — the actual build sequence

STYLE.md documents conventions (what a finished piece looks like).
This document is different: it's the **step-by-step process** for
actually building one, translated from how real ACiD/Blocktronics
artists worked in TheDraw/ACiDDraw/PabloDraw/Moebius into terms that
make sense for a Python-script generator instead of a live cursor
editor. Follow this sequence for any new figurative, scene, or
ambition-tier piece — it is not optional craft advice, it is the
actual method, in order.

The core idea: **real ANSI art is built in passes, not generated in
one shot.** A single generative pass (pick colors, place shapes, done)
is what produces flat, thin-looking work — exactly the gap between
house output and the references in `references/study/`. Each pass
below does ONE job and gets verified with `preview_piece` before the
next pass starts.

## Pass 1 — Layout plan (before writing any drawing code)

Decide, in writing, in your artist note, before you write a single
`set_cell`/`line`/`ellipse` call:
- **Composition type**: portrait / creature / scene / logo-wordmark /
  abstract-pattern. (Ambition-tier scrolls: decide the panel sequence.)
- **Subject placement**: centered, rule-of-thirds off-center, or a
  scene's horizon line — pick one and hold to it.
- **Single light source origin**: one `(lx, ly)` point (or one
  direction for a scene). This gets reused for every shading call in
  the piece — see Pass 3. Real ACiD figure work is often lit from
  upper-left or upper-right; pick one and don't mix.
- **Border/frame plan**: does this piece get a border, a title card, or
  both? Real ACiD pieces are framed far more often than not — an
  unframed piece should be a deliberate choice, not an omission.
- **Negative-space plan**: what covers the area that ISN'T the subject?
  "Flat black" is not a valid answer for a finished piece — decide what
  texture/pattern/gradient fills it now, in Pass 5, not as an
  afterthought.

Writing this down first is the actual mechanism that prevents the
flat-background problem inspect_piece now flags — you can't forget a
step you already named as needed.

## Pass 2 — Silhouette / block-in

Build the piece with FLAT, single-color regions only — no shading, no
texture, no gradients yet. This is the underpainting: correct
proportions, correct composition, correct reading at a glance, verified
with `preview_piece` BEFORE any detail work. If the silhouette doesn't
read correctly (wrong proportions, subject in the wrong place,
composition unbalanced), fix it now — shading can't rescue bad
block-in, it just makes a bad block-in slower to throw away.

## Pass 3 — Light-source shading

Apply `figure_common.light_field(x, y, lx, ly)` / `canvas.gradient_fill`
/ `canvas.dither_region` using the SAME `(lx, ly)` decided in Pass 1,
everywhere in the piece. This is what makes a piece read as one lit
object instead of several regions that each picked their own random
shading direction — the single biggest tell between "shaded" and
"colored in." Brighter side toward the light, density ramp (`RAMP =
"█▓▒░"`) carrying the falloff, not a hard color-to-color cutoff.

## Pass 4 — Directional detail texture

NOW add the individual marks that read as material: `strand_shade()`
for fur/hair/grain (short strokes following the surface's contour,
alternating 2-4 hues), individually-placed highlights on edges facing
the light, `figure_common.eye()`/`teeth()`/`brow_ridge()` for
constructed anatomical features. This pass is what separates a shaded
blob from a piece with real per-character intentionality — every mark
here should be a deliberate choice about where the light catches a real
surface, not filler.

## Pass 5 — Negative-space texture

Cover whatever ISN'T the subject with `texture_fill()` at low density
(0.15-0.4) — scattered marks, never uniform, never fully flat. Check
the plan from Pass 1: if you decided on a gradient sky, a dithered
field, or a pattern instead, build that here. A piece is not finished
if `inspect_piece` reports near-zero background density — that's the
single most common gap between house work and the real references
(see `ghengis-shades_of_a_shade.ANS`, `somms-the_powergrid.ANS`).

## Pass 6 — Frame and title treatment

If Pass 1 planned a border: add it now, as its own pass, not
interleaved with the subject. A box-drawing border, a repeated block
motif, or a title card top/bottom — whatever was planned. This is
compositional, not decorative: it's what turns "art on a screen" into
"a finished release," the way real packs almost always frame their
pieces.

## Pass 7 — Verify against a reference, then sign

Before calling it done: `preview_piece` one file from
`references/study/` side by side with your own piece (page through
both) and ask honestly — does the density, the framing, the shading
direction actually compare, or does mine still read thinner? If
thinner, that's real information about which pass needs another round,
not a reason to lower the bar. Then add the house signature block
(`sig_block()`) as the final step, per STYLE.md's file-naming and
credit conventions.

## Why passes, not one shot

Every reference piece studied so far shows this same structure under
inspection: flat block-in, THEN consistent directional shading, THEN
individual detail marks, THEN background texture, THEN a frame — built
up, not generated whole. `inspect_piece` now reports two new signals
(background density, border/frame presence) specifically so this
sequence is checkable after the fact, not just describable in advice
nobody has to act on. Low background density or no frame on a
figurative/scene piece isn't a hard block — it's the tool telling you
which pass got skipped.

## Color gotchas (documented once, so they stop being per-piece notes)

These two have now bitten three pieces in a row (THE REACTOR / THE TURBINE /
THE CONSOLE). They're not style advice — they're silent-corruption traps that
`preview_piece` will catch if you look, but that's slower than knowing up front.

**1. Pass PLAIN 0-7 hue indices to `sgr()`/`c()`, never a pre-encoded SGR code.**
Both `canvas.sgr(fg,bg)` and `figure_common.c(fg,bg)` map a plain hue index via
`(90 + (fg & 7)) if fg > 7 else (30 + fg)`. `figure_common.c()` has an idempotency
guard so an already-encoded SGR code (30-47 / 90-107) passes through untouched — but
`canvas.sgr()` does NOT have that guard. So feeding a pre-encoded bright code like
`93` (bright yellow) into `sgr()` double-maps it to `95` (bright magenta): a silent
color corruption, the kind that makes an amber head vanish into a yellow wash. Rule:
call them with a plain 0-7 hue index (or 8-15 for bright), not a code you already
encoded. If you have shade()'s output or a raw SGR code, route it through `c()`
(guarded) or `c_bright()`, not `sgr()`.

**2. U+2582 (LIGHT VERTICAL) is NOT in CP437.** Use U+2580 / U+2500 for vertical
scanlines/gridlines instead, or the piece won't decode cleanly under a strict cp437
check (inspect_piece's encoding line). When you want a thin vertical rule that still
reads as "scanline," U+2580 at low density does it.
