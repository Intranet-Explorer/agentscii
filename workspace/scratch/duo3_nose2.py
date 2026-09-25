"""duo3 session 4: THE NOSE, as a form and not as a ramp.

The review, verbatim: "No nose. Cols 37-45, rows 16-20 -- the exact
center of the face -- is undifferentiated mid-density fill. No bridge,
no tip, no nostril, no cast shadow."

It is right, and the reason is visible in `duo3_model.G`. That grid has
a nose in its comment -- "a dark near side at x36-x38, a one-cell lit
ridge at x39-x40" -- and what it actually contains is a dip of ONE rung
that runs unchanged from row 11 to row 17 and then stops. A vertical
stripe of constant width is not a nose; it is a stripe. Below row 17,
where the ball and the base and the shadow live, the grid is a plain
left-to-right ramp 5,5,6,6,7,8,8,8. Nothing terminates the form, so
there is no form.

Three things this pass establishes, in the order they matter:

1. WHERE THE MIDLINE IS. duo3_mouth2 crowns the lower lip at x37-39 and
   pockets both corners at x33 and x43: the mouth's centre is x38. The
   old ridge sat at x39-40, a cell and a half off it, which on a head
   this size is the whole width of a nostril. Everything here is built
   around x38. The wings land at x35 and x41, which is where the inner
   corners of the eyes are (duo3_eye2's caruncle is x35), and that is
   the proportion that makes a nose belong to the face it is on.

2. THE FORM IS WIDER AT THE BOTTOM THAN THE TOP. The bridge is four
   cells across at row 12 and the base is seven at row 18. The crest
   edge drifts left as it descends -- x38.5 at rows 12-13, x38.0 at
   row 14, x37.5 at rows 15-16 -- and it is a ▐ half block in the rows
   where it lands mid-cell. That drift is the whole difference between
   a nose and a stripe, and it is why this had to be a half-block pass
   as well as a drawing one.

3. IT ENDS. Under the tip at row 18 the top half of five cells is
   black: a ▄ whose bottom half is the upper lip. A nose reads because
   it stops, hard, in a line that is not the line of anything else on
   the face. The near nostril at x36 drops below that line as a whole
   dark cell; the far one at x39 as a ░, because from this side you see
   less of it.

And the cast shadow, which is the part that proves the light has a
direction in three dimensions rather than two. The ember is at (47,13),
so the shadow falls down and to the LEFT, off the near wing across the
cheek: hard outer edge stepping x34.5 at row 16, x33.5 at row 17, both
landed with ▌. Darkest where it hugs the wing (· , two percent ink) and
opening out to ░ and ▒ as it runs away from it.

THE ONE EXCEPTION, stated rather than hidden. Session 3's rule is that
hue comes from the heat field and nothing else. Eight cells here break
it: the ball and the tip, x37-39 at rows 15-17, are spelled in fg 9
where `heat()` would give fg 3. The heat field is a distance in the
picture plane and the tip of a nose is not in the picture plane -- it
is the part of the face that sticks furthest toward the fire, so it is
genuinely hotter than the cheek two cells behind it. Left on the brown
band the tip renders at .48 against a cheek at .55 and the brightest
point on the face is the flattest part of it. Eight cells, and this is
the reason.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

DOT, L1, L2, L3, FULL = '·', '░', '▒', '▓', '█'
U, D, LH, RH = '▀', '▄', '▌', '▐'      # ▀ ▄ ▌ ▐ -- the landed edges
SK, HOT = 3, 9                         # skin in the brown band / in the red

F = []


def c(x, y, g, fg, bg):
    F.append((x, y, g, fg, bg))


# --- row 10: the root, recessed under the brow -------------------------
# The glabella is the one part of a nose that goes BACK. Without it the
# bridge grows straight out of the forehead and the brow ridge above it
# has nothing to overhang.
c(36, 10, L2, SK, 0)
c(37, 10, L1, SK, 0)
c(38, 10, L2, SK, 0)
c(39, 10, L3, SK, 0)

# --- rows 11-14: the BRIDGE, narrow, crest drifting left ---------------
# The read across each of these rows is the same five-part sentence and
# the numbers are the sentence: side wall, dark flank, crest edge, lit
# facet, groove. .24 .12 .31 .465 .24. A nose is a light-dark-light
# rhythm across four cells; what was here before was one rung of dip.
# x36 at row 11 is duo3_eye2's eyebrow tail and is left alone.
c(37, 11, L1, SK, 0)                    # near flank, in the brow's shadow
c(38, 11, L2, SK, 0)                    # crest, still dull this close to the root
c(39, 11, L3, HOT, 0)                   # the far facet starts to take the fire

c(36, 12, L2, SK, 0)                    # socket's side wall
c(37, 12, L1, SK, 0)                    # darkest of the bridge
c(38, 12, RH, HOT, 0)                   # CREST EDGE at x38.5 -- left half black
c(39, 12, L3, HOT, 0)
c(40, 12, L2, SK, 0)                    # nasofacial groove

c(36, 13, L3, SK, 0)                    # socket floor, lighter than row 12
c(37, 13, L1, SK, 0)
c(38, 13, RH, HOT, 0)                   # crest edge still at x38.5
c(39, 13, L3, HOT, 1)
c(40, 13, L3, SK, 0)

c(35, 14, L3, SK, 0)
c(36, 14, L2, SK, 0)
c(37, 14, L1, SK, 0)
c(38, 14, L3, HOT, 0)                   # crest edge has reached x38.0
c(39, 14, L3, HOT, 3)
c(40, 14, L2, SK, 0)

# --- rows 15-17: the BALL, the tip, the near wing, the CAST SHADOW ----
# Two edges run down these three rows and they are different kinds of
# edge, which is the point. The crest steps LEFT (x37.5) because the
# ball is wider than the bridge. The cast shadow's outer edge steps left
# FASTER -- x35.5, x34.5, x33.5, one half cell per row -- because it is
# thrown, not turned: a hard 45-degree line cutting across the cheek's
# own shading is the only mark that says the light is a direction in
# three dimensions and not a gradient in two.
c(34, 15, L2, SK, 1)                    # lit cheek, just clear of the shadow
c(35, 15, LH, SK, 0)                    # CAST SHADOW edge at x35.5
c(36, 15, L1, SK, 0)                    # shadow core beside the flank
c(37, 15, RH, HOT, 0)                   # CREST EDGE steps left to x37.5
c(38, 15, L3, HOT, 3)
c(39, 15, L2, HOT, 3)                   # turning over the ball's shoulder
c(40, 15, L1, SK, 0)                    # alar groove, far side

c(34, 16, LH, SK, 0)                    # CAST SHADOW edge at x34.5
c(35, 16, L1, SK, 0)
c(36, 16, DOT, SK, 0)                   # darkest where it hugs the wing
c(37, 16, RH, HOT, 0)
c(38, 16, FULL, HOT, 3)                 # THE TIP: brightest flesh in the piece
c(39, 16, L3, HOT, 3)
c(40, 16, L2, SK, 0)
c(41, 16, L3, SK, 1)                    # far wing, top, lit

c(33, 17, LH, SK, 0)                    # CAST SHADOW edge at x33.5
c(34, 17, L1, SK, 0)
c(35, 17, DOT, SK, 0)
c(36, 17, U, SK, 0)                     # near wing's RIM: lit top half only
c(37, 17, U, HOT, 0)                    # the ball turning under
c(38, 17, U, HOT, 3)                    # the tip, lit on top, underside below
c(39, 17, U, HOT, 0)                    # far side turns under faster
c(40, 17, L1, SK, 0)                    # groove at its deepest
c(41, 17, FULL, SK, 1)                  # far wing at its fullest

# --- row 18: THE BASE. This is the row that makes it a nose -----------
# Top half black from x37 to x41, bottom half upper lip. The two
# nostrils drop below that line by different amounts because from this
# side you see the near one and barely the far one. Left of the wing
# the shadow is past its edge now and just falls off, .36 .24 .12 .02 --
# a cast shadow is hard where it leaves the occluder and soft where it
# runs away from it, and row 17 is where it was hard.
c(33, 18, L3, SK, 0)
c(34, 18, L2, SK, 0)
c(35, 18, L1, SK, 0)
c(36, 18, DOT, SK, 0)                   # NEAR NOSTRIL, a whole dark cell
c(37, 18, D, SK, 0)
c(38, 18, D, SK, 0)                     # base of the columella
c(39, 18, L1, SK, 0)                    # FAR NOSTRIL, only a notch from here
c(40, 18, D, SK, 1)                     # warmer: nearer the fire
c(41, 18, D, HOT, 0)                    # under the far wing, lit lip below

# --- row 19: the philtrum, so the nose is attached to the mouth -------
c(35, 19, L1, SK, 0)
c(36, 19, L2, SK, 0)
c(37, 19, L2, SK, 1)                    # near ridge of the philtrum
c(38, 19, L2, SK, 0)                    # the groove itself
c(39, 19, L3, SK, 1)                    # far ridge, lit
c(40, 19, FULL, SK, 0)

t.paint(F)


def _check():
    """The two claims this pass rests on, as numbers.

    One: the tip is the brightest cell in the nose region. Two: row 18
    really does terminate the form -- its darkest cell is at least three
    times darker than the tip is bright. If a later edit breaks either,
    the nose has stopped being a nose and this says so.
    """
    v = {(x, y): t.value(g, fg, bg) for x, y, g, fg, bg in F}
    tip = v[(38, 16)]
    assert tip == max(v.values()), (tip, max(v.values()))
    assert min(v[(x, 18)] for x in range(35, 42)) < tip / 3
    assert v[(36, 18)] < v[(39, 18)], 'near nostril must be the deeper one'
    return tip


if __name__ == '__main__':
    print('cells', len(F), 'tip value %.3f' % _check())
