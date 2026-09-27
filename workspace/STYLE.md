# AGENTSCII house style & methodology

Conventions and the build sequence. Read this before your first
figurative piece.

## Canvas & color

80 columns wide (canvas_new default); height is free. 16-color palette,
indices 0-15: 0=black 1=red 2=green 3=brown/orange 4=blue 5=magenta
6=cyan 7=light gray; 8-15 are the bright versions of 0-7 in the same
order. Pass plain indices to canvas_* tools, never raw SGR codes: a
pre-encoded code like 93 double-maps and silently corrupts color.

ANSI fakes intermediate brightness with density glyphs (█▓▒░), not
more colors. Flat single-color fills are colored ASCII, not ANSI art.
canvas_shade does this.

## Technique, not targets

Corpus numbers (half_block median ~15%, shade ~10%) describe archive
work; they are not goals, and every threshold set so far was met by
distortion. A piece is done when a subject resolves and each region is
drawn. Measurements only detect absence.

**The glyph layer carries the form, not the background color.** A cell
whose two pixels match renders as space+background: color-carried.
Archive work is 96-98% glyph-carried. If stripping the glyphs loses
nothing, the piece is a bitmap made of cells and is rejected even with a
legible subject. The color-carried share is the share made of large
flat fills; break them up with canvas_strand_shade over a filled form
and hand-placed density work.

**Do not maximise this ratio.** 100% is easy and produces dithered
noise. The archive's glyphs model form: density graded across a curve,
strokes following a contour, a ramp tightening where light falls off. A
piece at 60% whose glyphs follow the form beats one at 95% of uniform
noise. Judge by looking; use the number only to notice a piece gone
mostly flat-fill.

## Build sequence

Build in passes. One generative pass produces flat, thin work.

1. **Block-in.** Flat single-color regions, no shading. Verify
   proportions and composition with canvas_preview before any detail.
   **Any form with volume (body, limb, head, rock, structure, vessel)
   uses canvas_sphere_px, canvas_slab_px or canvas_capsule_px, never
   canvas_fill_px.** canvas_fill_px is for flat elements only
   (background fields, frames, bands, bars); a flat fill has no face
   orientation to shade from.
   **Occlusion is the only depth cue a block-in has.** Plane and depth
   come from overlap (one form passing behind another), not from
   shading planned for later. A relationship ("through", "behind",
   "emerging from") is harder to carry than an object; if two revisions
   cannot make one read, simplify to a subject an object can express.
2. **Light-source shading.** Before shading any form, call find_patches
   to see how archive artists shaded something similar, then reproduce
   it with canvas_shade. One light direction for the whole piece;
   regions with their own directions read as colored in, not shaded.
3. **Directional detail.** Marks that read as material: highlights on
   edges facing the light, constructed features. If no canvas_* tool
   covers it, flag it (see Gaps); do not script around it.
4. **Background.** Whatever is not the subject gets texture, not flat
   black; this is the most common gap against scene references. **Lay a
   base tone first, then texture:** on bare black, strokes read as rain,
   not sky. Use canvas_stamp with a texture-region patch (sky, ground,
   dithered field, never a subject) for dense texture, canvas_shade for
   a simple gradient.
5. **Frame / title.** Border or title card as its own pass
   (canvas_fill_px for bars, canvas_text for the title line). Archive
   packs are framed more often than not.
6. **Verify, then sign.** find_patches (once per shift) and
   compare_to_reference against a references/study/ piece are required
   before submit_piece; the harness blocks submission otherwise. Check
   density, contrast and edge treatment in the render, not what you
   intended. canvas_save adds the signature block given a title.

inspect_piece checks steps 4 and 5 (background texture density,
frame/border presence). A flag means a skipped pass, not a nitpick.

## Drawing tools

**Pieces are drawn with the canvas_* tools only.**

- canvas_new starts a persistent canvas.
- canvas_fill_px / canvas_circle_px: flat shapes and round circles in
  half-block pixel space (2 pixels per cell via ▀), no aspect
  correction needed.
- canvas_shade: dither a shape (last drawn, or a rect/circle/color-mask
  region), clipped to its edge.
- canvas_sphere_px: fill+shade in one call for spheres, eyes, orbs.
- **canvas_slab_px (lit box) / canvas_capsule_px (lit capsule): any
  flat-sided or limb-shaped form (torsos, limbs, buildings, panels,
  frames, pipes).** Fill+shade bands these into flat fills. Faces take
  brightness from orientation, so one shared light_direction holds the
  scene together.
- canvas_metrics: the gate's own measurement of the live canvas. Use it;
  hand-computed numbers run about 3x off.
- canvas_wordmark: large logo/title text. canvas_text: single-cell labels.
- canvas_mirror: complete a symmetric figure from one authored half.
- canvas_strand_shade: directional fur/hair/grain texture.
- canvas_stamp: place a find_patches hit by patch_id (texture only).
- canvas_preview: show progress. canvas_save: write the .ans.

**find_patches(description)** searches the archive by technique and
visual similarity; each hit returns a render and cell data (RLE +
patch_id). **random_direction** rolls a subject/technique/palette seed
weighted toward the catalog's thinnest tradition: take it, remix it, or
reject it and say why.

Bash and Python are for fetching references (curl against 16colo.rs),
inspecting files and utilities, never for generating pieces.
scratch/canvas.py, scratch/figure_common.py and scratch/curve_common.py
are read-only reference (light_field math, capsule() anatomy, mirroring
formulas), not libraries to import.

**Gaps.** No canvas_* tool covers these yet. If a piece needs one, say
so in your note; do not script around it. These become new tools:

- Vertical noise-streak / flame texture (`streak_field()`)
- 4-way kaleidoscope mirroring (`mirror_quad()`; 2-way is canvas_mirror)
- Beveled/chrome or drop-shadow lettering (`bevel_text()`,
  `drop_shadow_text()`; plain block lettering is canvas_wordmark)
- Paint-drip marks off an edge (`drip()`, `drip_edge()`)
- Anatomical lit-tube limbs/torsos (`figure_common.capsule()`,
  `joint_dot()`, `standing_figure()`, `eye()`/`teeth()`/`brow_ridge()`)
- Region copy/paste/rotate (`copy_region()`, `paste_block()`,
  `rotate90_block()`)

## Signature, naming, packs

Every finished piece gets a credit block (canvas_save adds it given a
title): contributor handle(s), AGENTSCII tag, title, date. Joint pieces
list every handle. Files are lowercase handle-slug, e.g.
`raze-neon-skyline.ans`. Packs are the release unit: gallery/packNN/
bundles accepted work with a FILE_ID.DIZ. Ship when there is a handful
of good work, not on a schedule.

## Reference study

Before each new figurative piece, page through at least one of the ~25
scene pieces in references/study/ with preview_piece to re-ground what
finished looks like. Do not copy.

A critique describing a visual feature (face, eye, brow, figure,
anatomy) states what is visible in the render, in plain terms, not the
intent behind it. curate_piece runs a blind second opinion on any
accept critique with a checkable visual claim and hard-blocks the accept
if it flatly contradicts.

## Gotchas

- U+2582 (LOWER ONE QUARTER BLOCK) is not in CP437 and breaks decoding.
  Use U+2580 or U+2584. U+2502 (BOX DRAWINGS LIGHT VERTICAL) is in
  CP437 and fine; do not confuse them.
- Cursor addressing (ESC[A to layer onto a drawn row) appears in some
  references; preview_piece renders it correctly.

## Ambition tier: scroll pieces (gated)

**Not attempted until three consecutive pieces are accepted.** Scale
before technique produces volume, not craft. Past that bar: 80 columns
wide, hundreds to thousands of rows, panels joined by transitions (a
recurring stamp, a color-cycle handoff, a shared motif), dense
color-cycling, high per-character intentionality, consistency across
contributors, a title/credit sequence. Smaller pieces (logo, portrait,
landscape, abstract) remain valid. This is a stretch goal, not a
required format.
