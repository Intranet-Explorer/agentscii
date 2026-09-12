# AGENTSCII house style

A working spec, not a cage — real scene groups had house conventions and
still produced wildly different pieces within them. This exists so accepted
work reads as one coherent body of output, and so the curator has real
criteria beyond taste.

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
  `mirror()`, `copy_region()`/`paste_block()`, `rotate90_block()`, plus
  `write_ans()` to go straight from a finished canvas to a hygiene-clean
  `.ans` file. This exists so a new idea doesn't require re-deriving
  ellipse/shading/symmetry math from scratch every time — compose primitives
  the way a real ACiD-era editor's tools got combined by hand. It's the
  general layer underneath `figure_common.py` (figurative-specific: light
  fields, constructed eyes, anatomy shading) and `curve_common.py`
  (parametric-curve-specific: phosphor trails, hue cycling) — use whichever
  fits, or combine them; none of the three make the others obsolete.
- **`random_direction` tool** — rolls a random subject/theme + technique
  constraint + palette lean, weighted toward whatever tradition the catalog
  is currently thinnest in. It's a seed for genuine variety, not a mandate —
  take it straight, remix it, or reject it and say why. Use it when you
  want a real chance-driven starting point instead of defaulting to
  whatever's cheapest to produce.

