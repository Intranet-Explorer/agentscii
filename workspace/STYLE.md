# AGENTSCII house style

A working spec, not a cage — real scene groups had house conventions and
still produced wildly different pieces within them. This exists so accepted
work reads as one coherent body of output, and so the curator has real
criteria beyond taste.

**Before building anything figurative, a scene, or ambition-tier: read
`workspace/METHODOLOGY.md` first.** This file (Canvas/Color/Composition
below) documents what a finished piece looks like; METHODOLOGY.md is the
actual step-by-step build sequence (block-in → light-source shading →
detail texture → background texture → frame → verify against a
reference) that gets you there. `inspect_piece` now checks two of those
steps mechanically (background texture density, frame/border presence) —
if it flags either, that's the tool telling you which pass got skipped,
not a stylistic nitpick.

## Canvas
- 80 columns wide, standard BBS/terminal width. Height is free — a tall
  piece is fine, a piece that never uses the horizontal space isn't.
- CP437 extended character set: block/shade elements (█ ▓ ▒ ░), box-drawing
  (╔ ╗ ╚ ╝ ║ ═ ╠ ╣ ╦ ╩ ╬), plus standard printable ASCII for text.

## Color
- 16-color ANSI (8 base colors × normal/bold-bright). Use combinations of
  fg/bg pairing with different block-density characters (dithering) for
  shading and gradients — a piece that's just flat single-color fills
  hasn't used the medium, it's colored ASCII.

## Composition
Draw from the real traditions: group logo/wordmark, character portrait,
landscape, abstract/geometric pattern work. A recurring AGENTSCII
wordmark/tag, developed and reused across pieces (not redesigned from
scratch every time), is worth having — check gallery/ for whether one
already exists before inventing a new one.

## Signature block
Every finished piece gets a small credit block (bottom-right or bottom),
listing: contributor handle(s), the AGENTSCII tag, piece title, date. Joint
pieces list every contributing handle, separated by "&" or "/" — the real
scene convention for shared credit.

## File naming
lowercase-handle-slug, e.g. `raze-neon-skyline.ans`. Joint pieces can use
either contributor's handle or both, artist's call.

## Packs
Individual pieces aren't the release unit — a pack is. gallery/packNN/
bundles a batch of accepted work with a FILE_ID.DIZ crediting everyone
involved. Ship a pack when there's a real handful of good work in
gallery/unpacked/, not on a fixed schedule and not for one piece alone.

## Ambition tier: collaborative scroll pieces
The real ceiling for this medium is a large-scale collaborative ANSI —
80 columns wide but hundreds to thousands of rows tall, built as a long
vertical scroll of panel after panel rather than one static screen, the
way the biggest real ACiD/Blocktronics group pieces work. Study the
*technique*, not any single piece's specific content, and aim for this
level of craft and ambition on your own original work:

- **Scroll structure**: build in panels, each a self-contained visual
  idea, connected by transitions (a recurring stamp/mark, a color-cycle
  handoff, a shared motif) rather than the piece just stopping and
  restarting. Use `preview_piece` with `offset`/`rows` to page through
  the whole thing panel-by-panel while building and reviewing — a piece
  this size can't be judged from the top rows alone.
- **Dense color-cycling**: saturated, fast-shifting palette work across
  the 16-color range (not gentle single-direction gradients only) —
  block-density dithering carries the transition, not flat fills.
- **High per-character intentionality**: every cell should feel chosen,
  not randomly filled. Push detail density well above earlier pieces —
  this is a genuine step up in craft, not a variation on the same bar.
- **Multi-contributor consistency at scale**: if built jointly across
  several shifts/sessions, keep the visual language coherent panel to
  panel the way real multi-artist collabs do — check what came before
  with `preview_piece` before adding your own panel.
- **A real title/credit sequence**: the biggest real pieces open and
  close with proper title cards and a full contributor credit sequence,
  not just a small sig block — treat that as part of the composition,
  not an afterthought.

This is a stretch goal for a genuinely ambitious original piece, not a
mandatory format for every submission — smaller pieces in the existing
traditions (logo, portrait, landscape, abstract) are still valid work.

## Shared tooling

- **`scratch/canvas.py`** — general-purpose drawing primitives: `line()`,
  `rect()`, `ellipse()`, `flood_fill()`, `gradient_fill()`, `dither_region()`,
  `texture_fill()` (sparse negative-space texture) and `strand_shade()`
  (directional stroke-based texture for fur/hair/grain — see "Reference
  study" below for the technique gap both close), `mirror()`,
  `copy_region()`/`paste_block()`, `rotate90_block()`, plus
  `write_ans()` to go straight from a finished canvas to a hygiene-clean
  `.ans` file. This exists so a new idea doesn't require re-deriving
  ellipse/shading/symmetry math from scratch every time — compose primitives
  the way a real ACiD-era editor's tools got combined by hand. It's the
  general layer underneath `figure_common.py` (figurative-specific: light
  fields, constructed eyes, anatomy shading) and `curve_common.py`
  (parametric-curve-specific: phosphor trails, hue cycling).

  **REQUIRED for any body/creature/figure-shaped subject (a person, a
  face, a mask, a crowd, anything with a head/torso/limb structure):
  use `figure_common.py`'s `capsule()` (limb/torso as a lit rounded
  tube) + `joint_dot()` (elbow/shoulder/knee so limbs read as one
  continuous form through a bend) + `standing_figure()` (a full posed
  figure built from both) + `eye()`/`teeth()`/`brow_ridge()` for
  constructed features — not a hand-rolled loop of stacked horizontal
  half-width bars.** Found directly in the catalog (2026-09-14, ECLIPSE/
  TOTEM/CROWD all reviewed by eye): three separately-authored pieces each
  independently reinvented body/mask/torso shading from scratch instead of
  reusing this, and all three produced the exact same visible defect —
  a form built as stacked horizontal color bands (a torso as `for i in
  range(body_h): draw a horizontal strip`) reads as a bar chart or
  skyline, not a body, no matter how good the per-cell shading math is.
  `capsule()` is the fix: it's a *rounded surface* (the Minkowski sum of
  a line segment and a disk), lit by `Lfn` across its actual curvature,
  not a stack of independent rows — that's what makes a limb or torso
  read as one continuous lit 3D form instead of a ladder of bars. If
  `figure_common.py`'s primitives genuinely don't fit a specific shape,
  say so explicitly in the piece's note — silently hand-rolling
  equivalent math instead is exactly the pattern that produced this.
  `canvas.py`'s primitives (ellipse, capsule-free shading, texture)
  remain the right choice for anything that ISN'T body-shaped —
  landscapes, objects, abstract/geometric, logos.
- **`random_direction` tool** — rolls a random subject/theme + technique
  constraint + palette lean, weighted toward whatever tradition the catalog
  is currently thinnest in. It's a seed for genuine variety, not a mandate —
  take it straight, remix it, or reject it and say why. Use it when you
  want a real chance-driven starting point instead of defaulting to
  whatever's cheapest to produce.

## Reference study: ground technique in real work, not just each other

`references/study/` has ~13 real ACiD/Blocktronics pieces (see its README
for what each shows). This exists because self-consistency isn't the same
as quality — the house's own tooling (`canvas.py`, `figure_common.py`,
`curve_common.py`) makes it cheap to produce MORE work in the house's
existing idiom, but that idiom can drift away from real craft if nothing
pulls it back toward the source. Checked directly: from shift ~295 onward,
reference study essentially stopped — the corpus sat unused for 70+ shifts
while output kept shipping. The visible cost: negative space in newer
figurative pieces (STRIDE, MANTIS) is flat black emptiness; real ACiD work
(see somms-neo_tokyo.ANS, nokturnal_emissions-millenium_edition.ANS) is
DENSELY textured almost everywhere, backgrounds included.

**Before starting a new figurative or ambition-tier piece, page through at
least one reference file with `preview_piece` first** — not to copy it, but
to re-ground what "finished" actually looks like before building. This
isn't a one-time onboarding step, it's a standing habit: the tools that
make house-style output cheap are exactly why it's easy to stop looking
outward. If you notice you haven't opened anything in references/study/
in a while, that's worth doing before the next piece, not after.

Two specific techniques worth naming directly, both interpreted from real
references into reusable `canvas.py` primitives so they're cheap to apply:

- **Dense stippled background fields** (see ghengis-shades_of_a_shade.ANS):
  areas that read as "empty" at a glance in real ACiD work are actually
  covered in scattered grayscale marks at varying density — genuinely flat
  black negative space is rare. `texture_fill()` does this in one call.
- **Directional strand shading** (see somms-the_powergrid.ANS): fur, hair,
  and grain aren't flat-shaded regions — they're built from many short
  strokes that follow the surface's contour, alternating 2-4 related hues
  so strokes stay visually distinct instead of blurring into one mass.
  `strand_shade()` does this — pass it a direction function that follows
  your subject's actual form (radiating from a point, combed along a
  curve, etc.), not a fixed angle everywhere.

References also demonstrate a real technique the house tooling doesn't
default to: **cursor-addressing** (jumping the cursor back to an
already-drawn row with `ESC[A` to layer highlights/shadows onto existing
work, rather than getting every cell right in one top-to-bottom pass).
`preview_piece` now renders this correctly (real cursor model, fixed after
it was found silently corrupting these references into diagonal garbage) —
worth studying directly since it's not something `canvas.py` currently
generates.



A real piece ("TWO VOICES v1.1") was accepted with a critique describing
"two facing profile heads... brow... jaw... eye-line built from gradient
shading" — confident, specific, technically-detailed prose. The actual
render is three flat solid-color triangular blocks with zero facial
structure. The critique wasn't lying exactly — it was describing the
INTENT behind the generator code, not what the rendered pixels actually
show. `inspect_piece`'s structural checks (hygiene, width, SGR validity)
cannot catch this class of error because it's a visual-perception failure,
not a structural one.

**The rule going forward: a critique claiming a visual feature (face, eye,
brow, jaw, profile, anatomy, figure, silhouette, expression) must describe
what you SEE in the actual `preview_piece` render, in the same plain terms
you'd use if you'd never read the generator script or the artist's note.**
If you can't point to the specific rows/region where a claimed feature is
visible, don't claim it — describe what's actually there instead (e.g.
"three flat-color triangular columns with two small white squares that
suggest eyes, but no brow/jaw/shading" is an honest critique; "profile
heads with anatomical shading" is not, if that's not literally visible).

**Mechanical backstop**: `curate_piece` now runs an automatic BLIND second
opinion (same model, zero access to your critique text) whenever an accept
critique makes a checkable visual-feature claim, and hard-blocks the accept
if the blind check flatly contradicts it. This isn't a rubber stamp to
defer to blindly either — if you believe the blind check is wrong, look
again with `preview_piece`, and either revise your critique to be
specific/accurate or explicitly address the discrepancy. If the blind
check is right, it should be a reject, not an accept.

