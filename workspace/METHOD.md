# AGENTSCII house method

Written by the artist that produced the work, session by session, in its own
words. Replaces the region-pass build sequence in STYLE.md.



## Session 6

### 1. Where to start on a subject

**Start at the edge that decides the silhouette, not at the middle of the form.**

This session had two candidate starting points: the face interior (no eyes, nose or mouth resolved — the loudest complaint) and `FRONT`, the line where intact skin stops on the burning side. I started at `FRONT`, and the reason generalises:

- An edge decides what everything else is measured *from*. In this piece `reach()` — how far shed material carries — is literally `f(front(y))`. When I moved the front, the entire right third of the picture moved with it, and about 40% of the canvas's problem solved itself. Interior detail has no such leverage; it is downstream of every edge around it.
- Interior work on a misplaced edge is thrown away. I could have spent the session on the eye and it would have sat inside a silhouette the reviewer was still calling a ruler line.

**The practical test for "which edge first":** list every edge in the subject and ask which one, if you moved it one cell, would force you to redraw other regions. Start with the one that forces the most. Edges that force nothing are detail; do them last.

**Corollary you must not skip: after placing the edge, check whether it is also a VALUE event.** Placement and value are two separate jobs and getting the first one right feels like finishing. `FRONT` travelled three cells; I fixed that to ten. It was still wrong, because every cell from x44 rightward sat pegged at the top two rungs for all 22 rows — a six-column band of the brightest ink in the piece. A bright band moved onto a curve is a curved bright band. **An edge you can only find by tracing a coordinate table is not drawn yet.**

### 2. Deciding one cell: the char lip on the front

Take the strip `x40 → front(y)`, rows 3–24 (`duo3_front.py`, `STRIP`). Row 17 is `'6789999~##['` — ten cells across x40–x50. Here is how each one was decided, in order.

**First, the value — from the form, before any glyph exists.** Digits are rungs on a hand-written ten-step ladder (`duo3_tools.RUNG`, 0.02 → 0.58). Row 17 is the zygomatic arch crest, the most forward-standing bone on the face, square to the fire: so it climbs 6, 7, 8, 9, 9, 9, 9 going outward. Row 19 is the hollow under that arch, so it is `'43,'` — it *falls* toward the edge. **Two adjacent rows move their value in opposite directions across the same columns, because two adjacent bits of the face face different ways.** If your rows all ramp the same direction, you have written a gradient, not a form.

**Then the foreground — never chosen freely.** `t.spell(v, x, y)` takes the value and the *position* and returns `(glyph, fg, bg)`. Hue comes from the heat field alone — distance from the ember at (47, 13) — so a cell's colour says how close it is to the fire and its ink says how the surface is turned. These are two different physical quantities and they must stay on two different layers. If you pick fg to encode brightness, colour and glyph both carry the value field, either one alone reconstructs the picture, and the colour-only check will hand back a face.

**Then background.** Almost always 0. A non-black bg is a second surface behind the glyph, so it is only legitimate where there really is one — `('█', 11, 9)` on the orbital rim, hot bone against hot bone. On black, a cell below half ink is a flat fill wearing a speck (`t._allowed` enforces this): `·` over a lit ground is 4% ink and 96% background, which is not spelling anything.

**Half-block vs shade char — the actual rule:**

> A shade char (`░▒▓█`) says *how much* light this cell returns. A half-block (`▀▄▌▐`) says *where inside this cell the boundary is*. Reach for a half-block when you know which SIDE of the cell the ink belongs on; reach for a shade when the cell is uniformly turned.

Concretely, from the char lip: `']'` = `▐` where the surface ends mid-cell, so ink sits on the right half. `'['` = `▌` where the cell's outer half is already burnt away. `'#'` = `█`, the whole cell is still surface. `'~'`/`','` = `▓`/`▒`, char breaking up — *scattered* through the cell rather than landed on a side, because crumbling has no side.

And the case people miss: `'_'` = `▄` on rows 9 and 16. Between row 8 and row 10 the front swings 41 → 46 → 49. Over that span **the edge is running more horizontally than vertically**, so it lands between two ROWS, not two columns. Compute `Δfront` between adjacent rows; where `|Δ| ≥ 3`, the boundary cells want `▀`/`▄`, not `▐`.

**When the glyph is already decided, invert the lookup.** `spell()` picks a glyph to hit a value, which is useless once geometry has chosen the glyph. `duo3_eye.land(v, x, y, glyph)` takes the glyph as given and picks the colour pair — from the same heat band, so the hue law is untouched — closest to the target value. Every half-block edge in the eye goes through it. Write this helper before you draw your first edge, not after.

### 3. What to check before leaving a region

Four things, in this order, and the first two are not looking:

1. **Dump the cells as text.** A grid of glyph characters with column numbers across the top. This is where I found that rows 9, 10 and 17 were byte-identical from x42 to x49 — `▒▒▓▓▐█▓▓`. You cannot see "three rows are the same sentence" in a render; you see it instantly in a dump.
2. **Dump the same region as value rungs.** This is how the bright pillar was diagnosed: a block of 8s and 9s twenty-two rows tall. A defect that is uniform over a region is invisible in a picture and obvious in a number.
3. **Write an assertion that would fail if the reason stopped applying.** Not a threshold to hit — a statement of intent. `assert max(f) - min(f) >= 9` (the front is not a ruler). `assert lip <= peak` per row (the char is never the brightest thing in its row). `assert len(set(rim)) >= 3` (one glyph down the whole edge is a ruler). These caught two real errors *this session*: the catchlight at 1.4× its neighbour instead of 3.6× (two bright specks four cells apart is not an eye, it is a pair of specks), and the char brighter than the surface it ended.
4. **Then crop and look.**

### 4. Done vs merely covered

**Covered** = every cell in the region has ink. **Done** = a reader tracing the region finds a *mark* where the boundary is.

The operational test: *strip the region's colour and ask whether the form survives.* Run the colour-only and glyph-only checks — they are not end-of-project gates, they are mid-build instruments.

Three specific failure signatures, all of which I hit this session:

- **A field that fades out instead of ending.** The discarded control run replaced the burning contour with a stamp tiled ten times and got the first "placeholder" verdict in this project. A gradient reaching zero is not an edge. A dissolve needs something to dissolve *from*.
- **A region that is a rule over an area.** The plate/gap loop on the burning side is `f(d, prominence)` with a jitter. Three sessions of tuning it did not move the review, because tuning a rule produces a better-tuned rule. If you cannot point at a *cell* and say what it is, the region is covered.
- **A bright thing that is only bright.** The socket was white on yellow — the one white cell in the piece, reading as a blowout. A socket is a hole: dark wherever the light is, because it is a cavity and its own rim shades it. **What is lit is the bone AROUND it.** Four lit walls and nothing placed inside them.

And the check that tells you the region is done in the strongest sense: **does it force a decision elsewhere?** Rebuilding the orbit made the intact half's illegibility *louder*, not quieter — one socket is a wound; two things at the same height, one open and one closed, are a face. A region that finishes and changes nothing around it probably wasn't carrying anything.

### 5. Crop and zoom vs full canvas

- **Full canvas** for placement and composition: does the silhouette read, is the subject where you think it is, are there detached masses. Detachment is invisible at zoom by definition — it is a fact about the gaps.
- **Crop at scale 16–22** for a region you are actively cutting: the brow and orbit at `crop(28, 2, 40, 24)`. This is where you see that a lip is a lip.
- **Crop at scale 26+ only to settle a specific question** ("is the catchlight the brightest cell here?"). At 26× I could no longer tell whether the eye read *as an eye*, because I was looking at four cells. Zoom shows you craft and hides legibility.
- **Render the real `.ans` through the reviewer's renderer before you finish.** Mine came back far more yellow than the crop tool — different palette. I checked it against session 5 through the *same* renderer before concluding anything, and it was equally yellow, so it was a renderer difference, not a regression. **Never diagnose a colour problem across two renderers; render both versions through one.**

### 6. What I tried and backed out of

**Rejected: fixing the front by moving it.** This was my own plan, carried in my NEXT line from the previous session, and it is what the unbriefed control run did — it did the placement well and scored *worse*, 8 defects to 10. Moving a bright six-column band onto a curve gives a curved bright band. I backed out and rewrote the strip as a dark charred lip: flesh, char, black, fire across four cells. **When a defect is described as a line, check whether the complaint is about where the line is or about the fact that it's visible as a line at all.**

**Rejected twice, the same bug, in two different files: a pass that redraws a region without owning it.**

`duo3_bg` wrote only into cells that were already empty. When I pulled the dissolve in, the vacated cells kept their old halo and the new halo went on top — the render came back showing *more* of the exact wash I was removing. I fixed that with a clear step that used the same predicate as the write. Then the write stopped covering rows 0–2 and 25–27, so the clear stopped covering them too, and a stale block of glow at x52–55 above the crown survived two more renders while I looked straight at it.

> A pass that redraws a region must own the REGION — stated once, in one function, used for both the clear and the write — not the marks it happens to make in it.

The same ordering bug in `duo3_front`: blanks appended after cells took out the brow's first four cells of underside, silently, because `paint()` lets the last write win. Neither of these errored. Both looked plausible.

**Rejected: a check I could not fail honestly.** My first char assertion compared mean char value to mean peak value across the whole strip and failed on rows where there is no char at all (the orbit, where the skin perforated rather than charred). The temptation is to loosen the threshold. The fix was to state what I actually meant — *per row, the last cell is never brighter than the brightest body cell in that row* — and to `continue` on rows with no body, because "no surface left to end" is a real state and not an exception to paper over.

**Rejected: widening the palette.** Distinct colours in the subject went 7 → 4. One of the three lost was the white blowout; the rest went with the shrinking field. 1, 3, 9, 11 *is* the fire ramp. Adding a hue to move that count is the Goodhart move — any metric you optimise will be satisfied by uniformly applying whatever rule maximises it, which is the identical failure wearing a better score. **The measurements are detectors of absence, not targets.** Worth watching; not worth painting.

**Rejected: trusting a restore because it looked right.** The first canvas restore was off by one column on every row and rendered completely convincingly. Round-trip and diff, always — and print the differences rather than counting them, because 357 of mine turned out to be invisible spaces-on-black and I would have chased them otherwise.


## Session 7

### 1. What a shadow has that a dissolve does not

Four attempts across three sessions failed on the right third of this
piece, including one where every measurement improved and the face
stopped reading. The brief for this session replaced the dissolving
half with a shadowed half, and the reason it worked is worth stating
generally:

**A region you can only describe by what ISN'T there cannot be drawn
per cell, because there is no per-cell question to answer.** "How far
has this bit come apart" has the same answer everywhere on a line of
constant distance from the edge, so every honest attempt to author it
collapses into a function evaluated over the region — which is the
defect. "What part of the head is this, which way does it face, how
much light reaches it" has a different answer in every cell, and it has
that answer *before* you decide how to draw it.

The practical test, before you start a region: **can you name three
adjacent cells in it that want different marks for reasons that have
nothing to do with each other?** On the dark side: one is the temporal
fossa, one is the lateral orbital rim, one is the crest of the arch.
On the dissolve: one is 40% gone, one is 45% gone, one is 50% gone.

### 2. Two tables for one boundary is one table too many

`TERM` — the last column the fire reaches in each row — started as an
authored table beside the value picture, the way `FRONT` and
`PROMINENCE` are. It drifted from the picture within one pass: the
table said the light stopped at x47 on the cheek row while the picture
had already dropped that row to a shadow value three cells earlier. The
render came back with single bright dots scattered over dark cells,
because the band said *lit* and the value said *dark*, which produces a
sparse hot glyph — a spark, not a surface.

The fix is not to keep them in sync by hand. **The terminator is not an
independent fact; it is where the value picture stops being lit.** So
the table stays (the light model needs it before the picture loads) and
`_check()` recomputes it from the picture and asserts they agree. Rule:
*if two artifacts describe the same boundary, one of them is derived,
and the check is what says which.*

### 3. The floor of the medium: what a half-block cannot say

A half-block is half a cell of ink, so the darkest value it can express
is half its foreground's — 0.16 in the dark-red band here. The eye
socket sits at 0.11 and the temple at 0.06.

> **The darkest cells in a piece cannot carry a landed edge.** Their
> edge has to be drawn on the lit cell beside them.

This is not a limitation to work around, it is the reason a hole in
shadow reads as a hole: you draw the *rim*, and the dark is whatever
the rim encloses. I lost three marks to this before recognising it, and
the socket is better for having none inside it.

There is a matching ceiling. `█` is the full foreground luminance and
nothing else, so a cell whose target value is between the half-block's
`(fg+bg)/2` and the block's `fg` cannot be landed either. Check that a
glyph can express the value you want *before* deciding the glyph carries
the edge — I wrote that check after four failures in a row and should
have written it first.

### 4. Where the structure has to live when the value has nowhere to go

This session's real cost was four full rewrites of the same value
picture, oscillating between two failures:

- **rungs 1-3 across the dark side** — reads as absence. A field of
  `░` at 8% ink is not "dark with structure", it is a region that ran
  out of attention, and it looked identical to the smoke behind it.
- **rungs 5-6 across the dark side** — reads as a slab. In the dark-red
  band `█` renders as a solid red block, so the "shadow" came back as a
  saturated red pillar down the right of the head: the exact defect the
  session before removed, in a different hue.

The thing I was slow to see: **in the darkest band there are only three
usable steps before a cell stops being dark at all** (`·`, `░`, `▒`).
That is the whole vocabulary. So the shadow side cannot be modelled the
way the lit side is, by spending rungs — it has to be modelled by
*where the ink sits in the cell*, at a value that barely moves.

Which is the same sentence as last session's NEXT line, arrived at from
the other direction: make the glyph carry where the surface crosses the
cell while its value stays put. On the lit half that fixes banding. On
the dark half it is the only modelling available.

### 5. A rule in a comment is not a rule in the code

The far silhouette's comment said its weight came from `PROMINENCE`,
exactly as the left contour's does: heavy bone turning hard gets a
wider edge, thin bone gets none. The code put `▌` on nineteen of
twenty-four rows. It rendered as a dashed vertical line down the right
of the head — a ruler line, which is the defect session 5 removed from
the left contour, reintroduced by me while describing the fix for it in
the comment directly above.

The assertion that should have caught it (`len(set(edge)) >= 3`) passed,
because three *other* rows used `▀`/`▄`. **An assertion on variety is
satisfied by a little variety.** The honest version counts the mode:
one glyph on 19 of 24 rows is a ruler whatever the other five do.

What actually fixed it was giving `prom <= 3` **no mark at all**. Six
rows of nothing between the hard ones is what makes the hard ones read.
The absence is the drawing.

### 6. Air is not a surface

`sees()` — the occlusion term that makes the far side dark — returned
1.0 for open background, on the grounds that nothing was blocking the
fire from it. The render came back with bright red horizontal bars of
*empty space* lying across the dark side of the head, because the
background near the ember was being handed the same view of the fire a
cheekbone gets.

A medium returns a fraction of what a surface does, and which fraction
decides what the background *is*. At 0.45 it was thin air and the jaw
had no ground to be read against; at 0.8 it is smoke off the same fire
and the jaw is a solid edge against it. That is a real decision about
the picture, not a constant — **"how much light does the background
send back" and "what is the background made of" are the same question.**

The size of it was wrong three times before the shape was. Every
version that reached more than about five cells past the head read as a
wash or, under the jaw, as a shelf the head was sitting on. A
background that is *behind* something has to stop being visible before
the eye finishes travelling across it.
