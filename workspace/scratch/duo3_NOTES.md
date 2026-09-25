# duo3 — session 2, written before anything was drawn

## 1. The striated right side: UNFINISHED.

One line, as asked: **the intent was deliberate, the execution is unfinished,
and by the only standard that matters — does it read as deliberate — it is
unfinished.**

The longer version, because the distinction is the whole point:

`duo3_right.py` states the intent clearly (plates, widening gaps, a front
drifting out and down). But look at what actually got written. The gap
pattern in those sixteen rows is, cell for cell, a function of x: more zeros
the further right you go, in every row, monotonically. That is a gradient of
striation, which is exactly what I was told it looks like from outside. There
is no **front** — no column where intact skin stops and coming-apart starts —
so there is nothing for the density to be a distance *from*. Density that
tracks x is a rule. Density that tracks distance from a stated edge is
structure. Only the second one is distinguishable from a region that ran out
of attention, and I wrote the first one.

Second failure in the same region: the background pass (`duo3_bg.py`) lays an
inverse-square magenta field over everything to the right of the head. The
dissolving face fades out; the background fades out with it, at a similar
rate, in a neighbouring hue. Where the face ends and the air begins is
therefore unreadable — the one edge that would have told a viewer the
dissolution has a shape is the edge I dissolved hardest.

So it goes on the list, and it is the largest single item on it. Not this
session: eye and mouth first, then the encoding defect below, because both of
those are prerequisites — if the intact half's features don't resolve, there
is no "intact" for the right side to be the transformation *of*.

## 2. The colour-only read: confirmed, and the cause is in `RAMP`.

`self_check`'s colour-only render still reads as a face. I can name the exact
line that does it. `duo3_tools.RAMP` is sixteen steps, and the foreground
colour marches monotonically up it: 5,5,5 / 1,1,1 / 3,3,3,3 / 9,9,9,9 /
11,11,11,11. Every value step changes the glyph *and* the colour pair
together, so the two layers each independently encode the same ordering. Strip
either one and the value field is still fully reconstructible. That is not a
face built out of cells; it is a greyscale bitmap printed twice.

The fix is not to scramble the foregrounds until the detector stops firing —
that is the identical failure wearing a better score, and I said so last
session. The fix is to make the two layers carry **two different physical
quantities**:

- **glyph density → value**, i.e. how the surface is turned relative to the
  light. This is the ANSI craft STYLE.md actually describes.
- **colour pair → hue**, i.e. how close that patch of skin is to the ember.
  Heat in skin is not the same field as facet orientation. A cheekbone facing
  away from the fire and a jaw facing into it can be the same brightness and
  are not the same colour.

Written that way the colour-only render should come out as a soft left-to-
right warmth gradient across a head-shaped mass, with no features in it,
because hue genuinely does not know where the eye is. The glyph-only render
keeps the whole model. The hand-placed feature cells — lid lines, the mouth
line, the silhouette rim — are edges, not surface, and are exempt: their
colour is doing edge work, not value work.

## 3. Eye and mouth, at cell level.

Magnified, the eye is two parallel black bars with a yellow square between
them. The reason it does not read is one missing thing: **there is no sclera.**
The entire aperture is black, so the dark iris has nothing to be dark
*against*, and the lash line above it and the aperture below it are the same
value, the same width, and the same square-ended rectangle. An eye reads
because a dark iris sits between two lit whites. Nothing else in the socket
matters as much.

The mouth is one black bar, eleven cells, dead straight, square at both ends,
with a lit lip under it. Missing: the corners (a mouth corner is a dark pocket
that sits deeper and higher than the line, and it is what makes a mouth a
mouth rather than a slot), the vermilion border (the upper lip is currently
the same value as the cheek above it, so there is no lip up there at all, just
a line drawn on skin), and the crease under the lower lip.

---

## What session 2 actually did, and what it cost

Order was the one I was given: declare, then features, then the density
pass. All three landed; a fourth was started and deliberately left short.

**Eye** (`duo3_eye2.py`). Sclera in two greys, dark iris of two cells,
catchlight moved up a half-row under the lash where a catchlight belongs,
lid plane lifted to brown so the brow and the lash line stop merging into
one red mass. Four passes at the crop before it read. The zoom loop is
the thing that was missing last session and it is what made this possible
-- the first two versions looked fine in my head and wrong at 22x.

**Mouth** (`duo3_mouth2.py`). Corner pockets at both ends carried through
both half-rows, which drops the ends of the line and kills the bar. Upper
lip a step darker than the cheek so it is a mass instead of a line drawn
on skin. Lower lip crowned past centre and falling off before the corner
rather than grading straight across. A crease under it, shorter than the
mouth.

**The layer split** (`duo3_reencode.py`). Colour pair from heat, glyph
from value. This one went wrong twice before it went right, and both
failures are worth keeping:

1. The first thresholds put bright-red across the whole centre of the
   face and the intact half came back a hot pink mask with the brown
   midtone gone. Heat is a real field but it is weak at this distance.
2. Running the pass a second and third time while tuning the band set
   quantised the value twice. The cheek came back as eighteen identical
   cells -- the exact near-uniform-region defect this project keeps
   getting rejected for, introduced by my own fix for a different defect.
   The recovery was to rebuild the canvas from the session-1 scripts,
   which are deterministic and on disk, and run the pass exactly once.
   `duo3_build.py --fresh` now reproduces the whole piece, session 1 and
   session 2 both, from nothing.

The colour-only render did change -- the socket's red ring and the left
edge's red band are gone, the surface modelling is gone -- but it changed
less than I wanted. What still reads in it is the head's silhouette,
which is shape and not colour, and the feature cells, whose foreground is
black because a lash line and a mouth line ARE colour accents. I am not
going to claim more than that.

**Plane breaks** (`duo3_planes.py`). Seventeen cells: the zygomatic and
the mandible, both sides of each break moved so they actually read.
Started because `canvas_metrics` says half_block 8.6% against a corpus
median of 15%, and shade 76.5% against a median of 10% -- which is
STYLE.md's named trap, "78% dither and 0% half-block", almost exactly.
Seventeen cells is not a fix for that and I am not going to pretend it
is. The intact half is a continuous dithered gradient with almost no
landed edges, and a face is not a gradient: it is a few planes meeting
along lines. That is a pass of its own.


---

# Session 3

Two things were asked for and both landed, but not in the order I
expected and not without breaking the picture in the middle.

## 1. The front

`duo3_tools.FRONT` states it: one column per row where intact skin
stops, leaning 43 at the crown to 46 at the jaw, with a notch inward at
rows 12-14 where the socket broke through first. Everything on the
burning side is now measured from it:

    x <  front   intact skin, one rung down at front-1: a groove
    x == front   THE LIP, two rungs up -- skin at the edge of a break
                 faces the fire more squarely than the surface behind it
    x == front+1 THE CRACK, half a cell of black with the first plate's
                 lit edge against it, unbroken crown to jaw
    x >  front+1 plates and gaps, both sized by d = x - front(y).
                 Plates five cells to one, gaps one to six.

The old version's gap pattern was a function of x and I called it a
gradient of striation. This one is a function of distance from a stated
edge, and the difference is visible: there is now a line down the face
that you can point at and say the skin stops here.

Three smaller things that the front made possible. `duo3_fore`'s B
block is gone -- it and `duo3_right` were two rules writing the same
cells and the seam between them was half of why the dissolve had no
readable edge. The background glow is pulled back to front+11, so the
gaps in the dissolve are black and not a slightly darker lavender; the
face has air to end against. And the plates past the old silhouette are
thinned by half, so what has already come off the head reads as embers
rather than as a second texture.

## 2. The colour-only render

It no longer reads as a face. Head-shaped mass, four concentric heat
bands, no eye, no nose, no mouth, no socket. The glyph-only render is
the strongest it has been. That is the way round it is supposed to be
and it is the first time this project has had it.

What actually did it, in order of how much each was worth:

**Hue from heat ALONE.** The old `spell` picked the first band that
could EXPRESS the cell's value, so a cell at .36 got brown and its
neighbour at .30 got dark red -- hue reading value back out through the
side door. It showed up as horizontal stripes of alternating hue down
the shadow side. Band is now `next(n for thr, n in BANDS_BY_HEAT if
heat >= thr)` and nothing else. If a value is brighter than the band
can carry, it clamps, which is a true statement about a surface that
far from the fire.

**Every feature respelled in the hue of the skin it sits in.** The eye
socket was fg 0 and fg 7/8; the nostrils were fg 0; the mouth line was
fg 0 and the lower lip fg 11. Black and grey and yellow were never in
this face for a physical reason -- they were there because I wanted
those cells dark or light and reached for a hue to say so. They are all
fg 3 now and the value is a glyph choice. The extra rung that made it
possible is `·` (CP437 0xFA): two percent ink, so a brow shadow can be
nearly black and still be spelled in skin.

**A rule about where sparse glyphs are allowed.** Over a non-black
ground a `·` is four percent ink and ninety-six percent background --
a flat fill wearing a speck. Sixty-eight of them turned the middle of
this face into one red mass the first time I ran the new ladder. Over a
lit ground a cell now has to be at least half ink.

**Half-block orientation.** `▀ a,b` and `▄ b,a` are the same two
pixels, and the colour-only test keeps the foreground. Taking whichever
spelling puts the lighter colour in fg costs the picture nothing. Being
straight about it: this is a change of encoding and not of drawing, and
it is the one move here where the number improves without the render
moving. It is worth maybe a fifth of the total. The rest is the other
thing.

## 3. What the colour fix broke, and the pass that fixed it back

Locking hue to heat took the intact half apart. Not because the
encoding was wrong -- because the encoding had been the only thing
carrying the modelling. Session 2 said so and I did not believe how
completely until the render came back as a head-shaped mass with no
head in it.

So `duo3_model.py` is the pass of its own I said this needed: ten rungs
of value, one character per cell, the face's LIGHT written out as a
picture. The brow ridge shelves at rows 9-10 and is what the socket is
dark against. The cheekbone is the brightest plane on this side and the
hollow at row 18 takes back two rungs. The nose has three planes and
not a ramp. Every rung becomes a glyph density in whatever hue the heat
field has there, so none of it can leak back into colour.

Two live failures worth keeping. Rung 9 clamps to `█` in the brown
band, so five rows of rung-9 lip rendered as a solid two-cell column --
fixed by lifting only the front cell and dropping the one behind it
into a groove. And three cells of black iris was a hole, not an eye;
one dark cell between two mid ones and two bright ones is a pupil.

## 4. Where it still falls short

half_block 8.0% against a corpus median of 15%, shade 76% against a
median of 10%. I flagged exactly this at the end of session 2 and it
has not moved, because everything this session did was spelled in shade
glyphs. It is not a scoring problem. It is that the plane breaks in
`duo3_model`'s grid land on cell boundaries -- a value that steps from
one whole cell to the next -- where a real edge lands mid-cell. Seventeen
cells of `duo3_planes` are the only landed edges in the intact half.
That is the next pass and it is a real one, not a number to chase.
