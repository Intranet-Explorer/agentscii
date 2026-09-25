# duo3.s6-unbriefed -- CONTROL

Same canvas, same model, same tools, NO operator brief. It ran on the
standard continuity prompt only (which carries the artist's own previous
NEXT line, so it did the contour work and nothing else). Verified by
reading the prompt out of ~/.claude/projects: 'SESSION 6.' absent,
'structureless wash' absent.

    briefed sessions 3 -> 5 : 14 -> 8 defects
    this unbriefed pass     :  8 -> 10 defects, reads_placeholder TRUE

First piece in the project to be called a placeholder rather than
constructed-with-defects. That delta is the measurement of what the
brief is worth.

    blind subject : Glitched pixelated human head in profile
    verdict       : REJECT   house: pass
    defects       : 10
    metrics       : half_block 11.0% subject-only / 4.1% whole-canvas, shade-of-ink 55.0% subject-only / 20.4% whole-canvas, colors 7, disconnected masses 5, ink 36% of canvas

---

Read both. Here's what's actually there.

## 1. What I literally see

A ~28-row terminal-glyph composition on black, palette restricted to yellow/gold, orange, salmon-red, brick, and dark maroon.

Left-of-center sits a dense mass about 25 rows tall and 25 columns wide with a curved left contour. That contour is real: tracing the leftmost glyph per row gives cols 31, 29, 27, 26, 25, 24, 24, 25, 26, 26, 25, 25, 25, 25, 26, 26, 27, 27, 27, 30, 33 (rows 5→25) — a continuous cranium bulge, a slight cheek flat, and a taper to a chin. Row 25 closes it with a horizontal `▀▀▀▀▀▀▀▀▀` run across cols ~33–41 reading as a jaw edge. Below that, rows 26–28 hold a smaller mass — neck and collar.

Right of the mass, cols ~52–70, is a field of scattered dark-red and brick cells that thins out toward the right edge. Rows 26–28 include a large flat salmon slab. One pure-white cell sits around row 14–15, col ~44. Caption plate at the bottom: rules, `opus / AGENTSCII`, and `What the Fire Left` in cyan.

Subject: a head, facing slightly right, with its right side dispersing into particulate. That much resolves. Facial features do not — see below.

## 2. Concrete defects

**Stamped falloff field, cols ~55–70, rows 10–25.** The same ramp `▒▒▒░░░·` is repeated essentially verbatim on rows 10, 11, 17, 18, 19, 20, 22, 23, 24, 25, shifted a few columns each time. That is a canned gradient stamp tiled ten times, not drawn smoke or ash. It occupies roughly a third of the canvas width.

**Vertical seam at col ~50.** `▐` recurs at exactly col 50 on rows 10, 11, 17, 18 and at cols 44–47 on rows 5–8, with `█` immediately right of it. In the render this is a visible straight stripe down the right side of the face. It's a construction edge showing through, not a form boundary.

**Left contour is one repeated glyph.** `▐` is the leftmost cell on rows 5, 6, 7, 10, 11, 12, 13, 14, 15, 18, 20, 26, 27. The curve is correct but it's drawn with a single stamped character — no thickness or value variation along an edge that is the piece's strongest feature.

**Banding / terracing.** Long horizontal runs of `▀▀▀▀` and `▄▄` at rows 10, 11, 15, 16, 19, 21, 22, 23, 24, 25 read as contour lines stacked in steps rather than modeled volume. In the render these are the flat yellow and dark bars crossing the face.

**Features illegible.** Rows 10–11 have paired `▀▀▀` at cols 32–34 and 45–47, which is presumably a brow/eye pair, but at render scale they read as two light horizontal bars, not eyes. No nose or mouth resolves anywhere in rows 12–24; that region is glyph noise. The `███` cluster at rows 14–18, cols 38–41 is an undifferentiated dark blob.

**Broken silhouette, right side.** The head has no right-hand contour at all. Cols 45–52, rows 4–25 transition straight from face interior into the stamped field. Half a head with a procedural cloud where the other half should be.

**Flat unshaded slab, rows 26–28, cols ~27–42.** The neck/collar renders as a large flat coral fill with almost no internal value structure.

**Isolated debris.** `▒░` floats at cols 49–50 on rows 1–3, fully detached from everything else, plus stray single cells at row 3 col 54 and row 6 col 63. Reads as noise, not embers — nothing connects them to the mass.

**Blown white cell, ~row 14–15 col 44.** A single pure-white block with no falloff around it. Reads as an artifact rather than a highlight.

**No debug text or placeholder strings.** The caption plate is a signature, not leftover scaffolding.

## 3. Assessment

There is genuine drawn work here — the left contour is a real, smoothly constructed skull-to-jaw curve, and the interior uses a varied hand-placed-looking glyph mix (`▄ ▀ █ ▌ ▐ · °`) rather than flat fills. That's not nothing. But it's confined to the left third. The right side of the head is absent, replaced by a gradient stamp tiled ten times; the interior features never resolve; the bottom slab is unmodeled; and a construction seam is visible at col 50. Against a strict bar this is a partially drawn head plus procedural filler standing in for the unfinished remainder.

VERDICT: REJECT
HOUSE: PASS
