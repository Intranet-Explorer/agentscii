"""duo3 session 4: the eye rebuilt as a BALL, not as a sandwich.

The review, verbatim: "The left eye, the right eye, and the mouth are
the same construction: horizontal rule, dark core, second rule. An eye
and a mouth are different objects and should not be built identically.
This is a motif placed three times, not three observed forms."

Checking it against my own source rather than arguing: duo3_eye2 is
row 12 a run of ▀, row 13 a run of aperture cells, row 14 a run of ▄.
duo3_mouth2 is row 20 a run of ▀, row 21 a run of lip cells, row 22 a
run of ▄. Same three rows, same order, same glyphs. It is one motif.

The tempting fix is three parameterisations of that motif, which is the
same defect with more knobs. So instead: what is actually different
about an eye?

An eye is a SPHERE SET INTO A HOLE. Everything about how it should be
built follows from that and from nothing else:

  * A sphere lit from one side has ONE bright pole and shades away from
    it monotonically. The old aperture was ░ █ █ ▒ · ▒ █ -- symmetric
    about the pupil, which is a sphere lit from the front by a light
    that does not exist in this picture. It is now .12 .24 .40 .24 .02
    .24 .48 : dim on the side turned from the fire, brightest at x34
    where the ball faces it. Nothing else in the socket is that bright.
  * A lid DRAPES OVER the sphere, so it covers MORE of it at the
    corners and less over the iris. The lash line is therefore not a
    line at a constant height. It sits at row 13.0 at x28-29 (whole
    cells of lid skin -- the aperture is nearly closed out there), rises
    to 12.5 across x30-33, and drops again at x34.
  * A lid CASTS A SHADOW ON THE SPHERE. This is the thing that was
    completely absent and it is the reason the old eye read as a slot:
    the aperture went from lash straight to full-value sclera with no
    turn between them. The shadow now occupies the TOP HALF of the
    sclera cells (▄), which is a landed mid-cell edge and also the
    literal truth about where a lid's shadow falls.
  * The far corner is deeper than the near one. x27 is a whole cell of
    · -- two percent ink -- and it is the deepest cell in the head.

The mouth is rebuilt in duo3_mouth3 as the other thing entirely: a
barrel, not a hole.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

DOT, L1, L2, L3, FULL = '·', '░', '▒', '▓', '█'
U, D, LH, RH = '▀', '▄', '▌', '▐'
SK = 3

F = []


def c(x, y, g, fg, bg):
    F.append((x, y, g, fg, bg))


# --- row 12: THE UPPER LID, a fold with its own value ------------------
# Not a rule of identical ▀. The lid is a curved flap of skin and it is
# lit by the same fire as the rest of the face, so it has a gradient of
# its own; and where it covers more of the ball it is a whole cell of
# skin rather than half of one. Lash height, left to right:
# 13.0, 13.0, 12.5, 12.5, 12.5, 12.5, 13.0 -- the arch.
c(27, 12, DOT, SK, 0)                   # the far corner: deepest cell in the head
c(28, 12, L2, SK, 0)                    # aperture nearly closed out here: a WHOLE
c(29, 12, L3, SK, 0)                    # cell of lid rather than half of one, and
                                        # dim, because the far corner is also the
                                        # part of the lid turned from the fire
c(30, 12, U, SK, 0)                     # lash lifts to 12.5: the arch opens
c(31, 12, U, SK, 1)                     # lid skin brighter where it faces up
c(32, 12, U, SK, 0)
c(33, 12, U, SK, 11)                    # the catchlight keeps its one honest cell
c(34, 12, U, SK, 1)                     # lid nearest the fire, brightest
c(35, 12, RH, SK, 0)

# --- row 13: THE SPHERE, with the lid's shadow landed on top of it ----
# .12 .24 .40 .24 .02 .24 .48 -- one bright pole at x34, one dark iris,
# and no symmetry anywhere in it.
c(28, 13, L1, SK, 0)                    # sclera, deep on the side turned away
c(29, 13, D, SK, 0)                     # LID SHADOW in the top half, sclera below
c(30, 13, D, SK, 1)                     # same, over brighter sclera
c(31, 13, L2, SK, 0)                    # limbus: the iris's dark rim
c(32, 13, DOT, SK, 0)                   # PUPIL
c(33, 13, L2, SK, 0)                    # limbus, far side
c(34, 13, FULL, SK, 0)                  # the ball's LIT POLE, facing the fire
c(35, 13, RH, SK, 0)                    # caruncle

# --- row 14: the lower rim, and the shadow the ball throws on it ------
# Top half is the underside of the sphere, bottom half is the lid's lit
# rim. The rim brightens toward the fire and the shadow above it is
# deepest under the ball's fullest, most turned-away part.
c(28, 14, DOT, SK, 0)
c(29, 14, L1, SK, 0)
c(30, 14, D, SK, 0)
c(31, 14, D, SK, 0)
c(32, 14, D, SK, 1)
c(33, 14, D, SK, 1)
c(34, 14, L3, SK, 1)                    # rim at its brightest, nearest the fire
c(35, 14, U, SK, 0)

t.paint(F)


def _check():
    """The sphere's defining claim, as a number: on a ball lit from one
    side the sclera climbs toward the light and does not come back. If
    the aperture is ever symmetric about the pupil again this fails."""
    v = {x: t.value(g, fg, bg) for x, y, g, fg, bg in F if y == 13}
    left = [v[x] for x in (28, 29, 30)]
    assert left == sorted(left), left          # climbing into the iris
    assert v[34] == max(v.values()), v         # one pole, and it is x34
    assert v[28] != v[34], 'symmetric sclera is a front light, not this one'
    return v[34] / max(v[28], 1e-9)


if __name__ == '__main__':
    print('cells', len(F), 'pole/far-side ratio %.1fx' % _check())
