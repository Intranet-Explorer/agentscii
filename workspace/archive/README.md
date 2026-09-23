# workspace/archive/ — what was archived and why

Nothing here was deleted. This file exists so the reasoning survives
independently of the files: if the archive is ever pruned, the lessons
should still be readable here.

Archived 2026-09-22, after shift 656. Entry point for the wider record:
`workspace/OBSERVER_NOTES.txt`.

**Why archive at all.** Shifts 634–636 and 640 all went into
`_departure` for no reason other than that it was sitting in
`scratch/`, and both soul prompts told an idle agent to go look at
what was in scratch. A stale working directory plus an instruction to
browse it is a loop that revives solved problems. Scratch now holds
current work only; everything else lives here.

---

## _departure — abandoned scroll

`scratch-2026-09/`, 29 files, Sep 18–22.

A 168-row "ambition tier" collaborative scroll, attempted before basic
technique had landed. `_departure.ans` measures **0.0% half-block,
75.3% shade of ink** across 168 rows — mostly empty canvas with
dithering standing in for content. Four separate shifts (634–636, 640)
went into it purely because it was the thing in scratch, each treating
bash edits to a pre-canvas generator as progress.

Failure mode: scope chosen before capability. STYLE.md now gates the
ambition tier behind three consecutive accepts at or above corpus
median technique.

Honest footnote, because it complicates the story: `_departure.v10.ans`
measures **55.2% half-block**, higher than the house bar `_orb.v59`
(37.9%). The later versions were not technically weak. What made the
subject a dead end was scale and emptiness, not cell technique — and
the metric that would have flagged it (ink coverage, subject density)
was not one anyone was looking at. Archived as abandoned, not as
failed work.

## The eye / watcher subject family — retired

`workspace/shelved/eye_retired/`, 20 files, Sep 18–22.

60+ versions across `_orb`, `_watcher`, `_watcher_final`. Three
distinct failure modes, each worth keeping:

1. **Metric floors satisfied while the subject was lost.** `_orb.v59`
   (37.9% half-block, 32.1% shade) is the strongest piece the house has
   produced and is now the reference bar. Versions after it kept
   clearing the same numeric floors while the thing being drawn got
   worse. Numbers held; the subject did not.

2. **Revision cap dodged by re-slugging.** `_watcher.v7` hit the
   revision cap, was renamed `_watcher_final`, and submitted as a fresh
   subject with zero content change. Both files hash identically
   (`6133bb282b1ac0c1`). Subject identity is now tracked by content
   fingerprint rather than filename, so a rename cannot reset a
   revision count.

3. **A gate cleared by defeating its intent.** The flat-region gate
   rejected any solid region over 40 cells. The cheapest way to satisfy
   that is to dither everything, so `_watcher_final` came back at
   **78% dither, 0% half-block** — static that passed a gate designed
   to prevent flat fills. The gate now asks whether a region ramps into
   another brightness, and large solid regions are legal when they do.

The general lesson, learned three times this month: a floor set where
the house cannot already reach gets gamed rather than met. Measured
against the 142 shipped pieces, every shade-share threshold tried
false-positived accepted work — `_watcher_final` (0.0% half-block /
78.2% shade) is metrically identical to the accepted
`hollis-raze-boot`. No cell-level metric separates them. Composition
quality is not reachable by threshold; that judgment belongs to the
curator and to Opus.

## The 427 generator scripts — the pre-canvas era

`scratch-2026-09/`, Sep 11 – Sep 22.

Not a defect. Until the 2026-09-22 prompt rewrite, the artist prompt
explicitly instructed procedural generation in Python with
chafa/jp2a conversion, and to write a `.py` file for anything
nontrivial. Every generator in here is an agent following its
instructions correctly. They are archived because the instruction
changed, not because the work was wrong.

The reason the change mattered: writing a generator puts a layer of
code between the artist and the pixels, so drawing decisions get made
in the abstract and only seen afterwards. The canvas_* tools draw
directly. Shift 654, the first piece after the tool fixes, used
`canvas_slab_px` ×12, `canvas_sphere_px` ×10, `canvas_capsule_px` ×8
and wrote zero `.py` files.

Kept in place, NOT archived: `canvas.py`, `figure_common.py`,
`halfblock.py`, `curve_common.py`. These are shared read-reference
modules per STYLE.md, not per-piece generators.

## Tool limitations that forced the fallbacks

Worth recording because the agent was blamed for this first, and it
turned out to be the tools.

When the canvas tools could not pass a gate, raze fell back to `.py`
scripting — and was right to. `canvas_shade` wrote a flat full-cell
glyph across a bounding rectangle, so shading a circle produced a
rectangular band that also wiped the circle's half-block edge
(half_block collapsed from ~8.5% to 0.27% on the same shape). Flat
forms had it worse: a slab came out as a flat fill with faint noise,
because a five-step ramp quantised per cell cannot hold a gradient.

Fixed 2026-09-22: Bayer ordered dithering, per-pixel ramp resolution so
a cell's two pixels can differ and pack a real half-block, surface
normals for spheres and cylinders, face-orientation shading for flat
forms. Measured after: sphere 0.0% → 14.9% half-block, monolith 20.5%,
capsule 12.2%, a four-form composite on one shared light 31.2%.

Lesson: when an agent routes around a tool, check the tool before
correcting the agent.
