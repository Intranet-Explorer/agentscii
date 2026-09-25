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
