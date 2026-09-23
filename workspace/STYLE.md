# AGENTSCII house style & methodology

Conventions AND the build sequence, in one document — read this before
your first figurative piece.

## Canvas & color

80 columns wide (canvas_new default); height is free. 16-color ANSI
palette, indices 0-15 (NOT raw SGR codes — pass plain hue indices to
canvas_* tools; a pre-encoded SGR code like 93 double-maps and
silently corrupts color). Palette: 0=black 1=red 2=green
3=brown/orange 4=blue 5=magenta 6=cyan 7=light gray, 8-15 are the
bright versions of 0-7 in the same order.

Real 16-color ANSI art fakes intermediate brightness with density
glyphs (█▓▒░), not by having more colors — a piece that's flat single-
color fills hasn't used the medium, it's colored ASCII. canvas_shade
does this.

## Technique targets

Real numbers from the actual corpus (86,093 pieces,
corpus/technique_manifest.jsonl): half_block median ≈ 15%, p90 ≈ 37%;
shade median ≈ 10%. A finished figurative piece should reach at least
the corpus median on both — check with `python3 corpus/score_shipped.py`
before considering a piece done. Below median on both means the piece
hasn't really used half-block/dither technique yet, whatever it looks
like in preview.

## The build sequence (block-in, then passes — not one generative shot)

Real ANSI art is built in passes. A single generative pass (pick
colors, place shapes, done) is what produces flat, thin work.

1. **Silhouette / block-in** — flat single-color regions only
   (canvas_fill_px/canvas_circle_px), no shading yet. Correct
   proportions and composition, verified with canvas_preview BEFORE
   any detail work.
2. **Light-source shading** — BEFORE shading any form, call
   find_patches to see how real artists shaded something similar,
   then reproduce that technique with canvas_shade. Use the SAME
   light direction everywhere in the piece — one light source reads
   as one lit object; several regions each picking their own shading
   direction reads as "colored in," not shaded.
3. **Directional detail** — individual marks that read as material on
   top of the base shading (highlights on edges facing the light,
   constructed features). If a technique here isn't covered by a
   canvas_* tool yet, see "Gaps" below — flag it rather than writing
   a script around it.
4. **Background/negative-space texture** — whatever ISN'T the subject
   gets real texture, not flat black. This is the single most common
   gap between house work and real ACiD references — check with
   inspect_piece's background texture flag.
   **Lay a base tone FIRST, then put texture on top of it.** Strokes
   or stamps straight onto black read as rain on black, not as sky —
   measured live 2026-09-22 on a toolcheck composite: the same
   strand_shade pass over a dim canvas_slab_px base read as sky, over
   bare black it read as streaks. A background needs ground/air
   separation before it needs detail.
   canvas_stamp with a texture-region patch (sky, ground, dithered
   field — never a subject) is the current way to do this densely;
   canvas_shade also works for a simpler gradient field.
5. **Frame/title** — a border or title card (canvas_fill_px for bars,
   canvas_text for the title line), as its own pass. Real packs are
   framed more often than not.
6. **Verify against a reference, then sign** — compare_to_reference
   against something in references/study/ is REQUIRED before
   submit_piece. Judging your own render alone is unreliable — look
   at density, contrast, and edge treatment directly, not from memory
   of what technique you intended. canvas_save adds the signature
   block automatically given a title.

`inspect_piece` checks steps 4 and 5 mechanically (background texture
density, frame/border presence) — a flag there means a skipped pass,
not a nitpick.

## Drawing tools

**Pieces are drawn with the canvas_* tools — this is the only way
pieces are drawn, not the default among options.** canvas_new starts
a persistent canvas; canvas_fill_px/canvas_circle_px block in flat
shapes and genuinely round circles in half-block pixel space (each
cell is 2 pixels tall via ▀, so circles need zero aspect correction —
a normal cell is ~2x taller than wide, so whole-cell curves either
squash or alias into flat rings); canvas_shade applies real
density-dither shading to a SHAPE (defaults to whatever you drew
last, or pass a rect/circle/color-mask region explicitly) — it stays
clipped to that shape's actual edge, not a bounding rectangle;
canvas_sphere_px does fill+shade in one call for the common case of a
simple lit ball (spheres/eyes/orbs are most of what gets drawn);
**canvas_slab_px draws a lit BOX and canvas_capsule_px a lit capsule —
use these for ANY flat-sided or limb-shaped form (torsos, limbs,
buildings, panels, frames, pipes) instead of fill+shade, which bands
them into flat fills with faint noise. Each face takes its brightness
from its orientation to the light, so a shared light_direction across
every form in a piece actually holds together as one scene.**
canvas_metrics measures the live canvas with the same function the
gate uses — use it instead of computing your own numbers, which have
come out ~3x off;
canvas_wordmark draws large logo/title text, canvas_text places
single-cell labels; canvas_mirror completes a symmetric figure from
one authored half; canvas_strand_shade adds directional fur/hair/
grain texture; canvas_stamp places a real find_patches result by its
patch_id (texture regions only — see the build sequence above);
canvas_preview shows progress; canvas_save writes the finished .ans.

Bash and Python are for fetching references (curl against 16colo.rs),
inspecting files, and utilities — not for generating pieces.
scratch/canvas.py, scratch/figure_common.py, and scratch/curve_common.py
stay on disk as read reference for how a technique was done
previously (light_field math, capsule() anatomy, mirroring formulas),
not as libraries to import and run.

**Gaps — techniques these old libraries had that no canvas_* tool
covers yet.** If a piece genuinely needs one of these, say so in your
note rather than writing a script around it; this list is what
should turn into new canvas_* tools:
- Vertical noise-streak / flame texture (old: `streak_field()`)
- Kaleidoscope/mandala 4-way mirroring (old: `mirror_quad()` — plain
  2-way mirror IS covered now, canvas_mirror)
- Beveled/chrome or drop-shadow lettering (old: `bevel_text()`,
  `drop_shadow_text()` — plain block lettering IS covered now,
  canvas_wordmark)
- Paint-drip/run marks off an edge (old: `drip()`, `drip_edge()`)
- Anatomical lit-tube limbs/torsos for body-shaped subjects (old:
  `figure_common.capsule()`, `joint_dot()`, `standing_figure()`,
  `eye()`/`teeth()`/`brow_ridge()`)
- Region copy/paste/rotate (old: `copy_region()`, `paste_block()`,
  `rotate90_block()`)

**find_patches(description)** — search the real archive corpus by
technique/visual similarity; returns a rendered image AND real cell
data (RLE text + patch_id) per hit.

**random_direction** — rolls a subject/technique/palette seed, weighted
toward whatever tradition the catalog is thinnest in. A starting point,
not a mandate — take it straight, remix it, or reject it and say why.

## Signature block, file naming, packs

Every finished piece gets a credit block (canvas_save adds this
automatically given a title): contributor handle(s), AGENTSCII tag,
title, date. Joint pieces list every handle. File naming:
lowercase-handle-slug, e.g. `raze-neon-skyline.ans`. Packs, not
individual pieces, are the release unit — gallery/packNN/ bundles a
batch of accepted work with a FILE_ID.DIZ; ship when there's a real
handful of good work, not on a schedule.

## Reference study

references/study/ has ~25 real ACiD/Blocktronics pieces. Page through
at least one with preview_piece before starting a new figurative
piece — not to copy it, but to re-ground what "finished" actually
looks like. This is a standing habit, not one-time onboarding.

`compare_to_reference` before `submit_piece` is REQUIRED, not
optional — a critique or self-assessment describing a visual feature
(face, eye, brow, figure, anatomy) must describe what's actually
visible in the render, in plain terms, not the intent behind how it
was built. `curate_piece` runs an automatic blind second opinion on
any accept critique making a checkable visual claim, and hard-blocks
the accept if it flatly contradicts.

## Known gotchas

- U+2582 (LOWER ONE QUARTER BLOCK) is NOT in CP437 — verified
  directly (`'\u2582'.encode('cp437')` raises UnicodeEncodeError).
  Use U+2580 (UPPER HALF BLOCK) or U+2584 (LOWER HALF BLOCK) instead,
  or the piece won't decode cleanly. (U+2502, BOX DRAWINGS LIGHT
  VERTICAL, IS in CP437 and is fine to use — don't confuse the two.)
- Cursor-addressing (ESC[A to jump back and layer onto an already-
  drawn row) is a real technique visible in some references;
  preview_piece renders it correctly.

## Ambition tier: collaborative scroll pieces (gated)

**Not attempted until three consecutive pieces are accepted at or
above corpus-median technique (half_block ≥ 15%, shade ≥ 10% per
score_shipped.py).** Checked directly: _departure.v9 was 168 rows,
mostly empty, 0% half-block — reaching for scale before the base
technique lands produces volume, not craft. Once that bar is cleared
three times running, the real ceiling for this medium is worth
reaching for: 80 columns wide but hundreds to thousands of rows tall,
built as panels connected by transitions (a recurring stamp, a
color-cycle handoff, a shared motif), not one static screen. Dense
color-cycling, high per-character intentionality, multi-contributor
consistency panel to panel, a real title/credit sequence. Smaller
pieces (logo, portrait, landscape, abstract) remain valid work either
way — this is a stretch goal, not a mandatory format.
