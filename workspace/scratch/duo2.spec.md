# duo1 — spec

Canvas: 80 cols x 50 rows = **80 x 100 pixel space** (half-block pixels).
Roll: "a hand reaching through something", cool tones dominant.
Symmetry: **rejected** — a reaching hand is asymmetric; a mirrored hand
reads as a crest or a leaf, not a hand.

## Revision note (rev 2 — plane cue)

A blind viewer saw the rev-1 block-in and said *"a hand reaching up from
the ground"*. The hand read; the relationship did not. The pane was a
featureless blue field, so radiating cracks defaulted to cracked earth —
nothing in the silhouette said **vertical surface**.

Rev 2 gives the pane a **casement**: two jambs, a transom, one vertical
mullion, flat grey. The cue is carried entirely by shape, not by value —
the transom passes **behind the four fingers** and the mullion **behind
the thumb**, so the hand occludes structure that runs edge to edge. A
bar that a hand interrupts and that resumes on the other side can only be
a surface behind the hand. Read at block-in, with no shading anywhere.

Family check vs CATALOG: `raze-reach` = hand in open space. `_reach`
(rejected) = hand **behind** a scope lattice — this is the inverse, the
hand is in FRONT and occludes the bars. `_breach` (rejected) = hand
rising through a water surface, seen side-on, wrist receding down. This
is none of those: a glazed pane **shattered outward toward the viewer**,
hand palm-forward through the hole, fingers spread in front of the wall
plane. The "something" is a solid vertical surface with a broken hole
in it, and the hand is in FRONT of that surface, not behind or below it.

## Subject

A palm-forward hand, fingers spread, pressed against a shattered pane of
glass seen straight on — the window frame's mullion and transom pass
BEHIND the hand, cracks radiate from the break across the pane.

SPEC CORRECTED 2026-09-24 after two block-in blind reads. The original
line said "pushing out THROUGH a hole smashed in the pane". Two
independent blind viewers never read "through": rev 0 gave "a hand
reaching up from the ground", rev 1 gave "a hand pressed against a
window". Penetration needs shard depth and a thickness lip, which are
value cues, and a block-in has no value. The subject is now what the
composition actually carries. Do not chase "through" with more cues.

## Layout

Pixel space, origin top-left, x 0-79, y 0-99. Draw order top to bottom.

| # | element | position (px) | size | plane |
|---|---|---|---|---|
| 1 | glazed pane | x 0-79, y 0-99 | full field | back — flat wall plane, fills frame |
| 2 | crack spikes | 7 tapered wedges, 3 of them running UP the pane | 24-30 px long | in the pane surface, void black; each dies at a bar |
| 3 | left jamb | x 0-4, y 0-99 | 5 x 100 | pane plane — casement, in front of the glass |
| 4 | right jamb | x 75-79, y 0-99 | 5 x 100 | pane plane |
| 5 | transom | x 0-79, y 26-29 | 80 x 4 | pane plane — **runs behind all four fingers** |
| 6 | mullion | x 20-22, y 0-99 | 3 x 100 | pane plane — **runs behind the thumb**, destroyed at the hole, stub below it |
| 7 | breach hole | jagged 16-tooth polygon centred (40,74) | x 9-71, y 52-96 | cut through pane; black void beyond |
| 8 | hanging shards | 6 tapered wedges off the hole's UPPER rim | 8-14 px long | pane blue, hanging down into the void |
| 9 | forearm | (40,66) -> (40,100), r 7 -> 8 | 16 x 34 | mid — crosses the hole rim, the "through" |
| 10 | palm | centred (40,52) | x 26-54, y 40-66 | front |
| 11 | thumb | (28,57) -> (15,43), r 4 | left-up diagonal | front, left of palm |
| 12 | index finger | (32,43) -> (28,12), r 3 | 31 tall | front |
| 13 | middle finger | (39,42) -> (38,8), r 3 | 34 tall | front, longest |
| 14 | ring finger | (46,43) -> (48,13), r 3 | 30 tall | front |
| 15 | pinky | (52,45) -> (57,21), r 3 | 24 tall | front, shortest |

Fingers fan: index tilts left, pinky tilts right, middle near-vertical.
Gaps between fingers stay >= 2 px so the pane shows between them — this
is what makes the hand read as a hand and not a paddle, and it is also
where the transom shows through, which is what makes the pane read as a
pane.

## The plane cue (rev 2 — the point of the revision)

Four cues, all of them readable in **flat silhouette**, no shading:

1. **Occlusion.** The transom is a straight bar running the full 80 px;
   the hand cuts it into six visible segments (two long runs plus four
   slivers in the finger gaps). The mullion is a straight bar running the
   full 100 px; the thumb cuts it. Straight structure interrupted by the
   figure and resuming in line = the structure is behind the figure.
2. **Break continuity.** The mullion is destroyed where the hole is and
   resumes as a stub in the pane below the hole's closed lower rim. The
   break took the glass and the bar with it.
3. **Hanging shards.** Six blue teeth hang DOWN off the hole's upper rim
   into the void. Glass hangs; ground does not.
4. **Cracks terminate at bars.** Every crack dies where it meets a jamb
   or the transom, because each light is a separate piece of glass. Three
   cracks now run UP the pane; rev 1's cracks fanned sideways only, which
   is what read as a horizon.

No shading pass may be relied on to carry any of these. If the piece were
printed as a two-colour stencil the plane would still read.

## Scale

These ratios are the whole read; they are the piece.

- Hand spans x 11-60 and fingertip y 5 down to the frame bottom = **61%
  of width, full height**. Dominant single figure, no competing mass.
- Palm 28 wide x 26 tall — near-square, the human ratio. Palm width is
  **1.75x** the four-finger group's combined base (16 px).
- Finger length : palm height = **34 : 26 (1.3)** for the middle finger.
  Shorter and the hand reads as a mitten; longer and it reads as a rake.
- Hole 62 x 44 px is **~4x the forearm width** (16 px). Roughly 20 px of
  void shows on each side of the arm — that gap is the depth cue that
  says the arm came through the pane rather than being painted on it.
- The hole's lower rim closes at y 96, inside the frame, with pane
  visible beneath it. A hole that runs off the bottom edge reads as a
  shadow; a closed rim reads as an opening.
- Palm sits at y 52, just above centre. The forearm exits the bottom of
  the frame — the arm leaves frame, it does not float.
- Casement bars stay thin: jambs 5 px, transom 4 px, mullion 3 px. They
  are a cue, not a subject — total bar area stays under 20% of the field
  so the hand keeps the composition.
- No head/sill bar. The casement is open at the top and bottom, so it
  reads as architecture continuing past the frame rather than as a
  decorative border, and the middle fingertip at y 5 stays clear of any
  bar (no tangency).

## Palette

Cool tones only. 16-colour indices, not SGR.

| element | block-in index | shading pass |
|---|---|---|
| glazed pane | 4 blue | 4 base, 12 lit faces, 8 dither toward black |
| casement bars | 8 grey | 8 base, 7 on the top/left face of each bar, 0 on the lower-right |
| void through hole | 0 black | 0 with 2 dim-green depth flecks at the rim |
| crack spikes | 0 black | 0 core, 12 hairline on the upper-left lip of each |
| hanging shards | 4 blue | 4 base, 12 on the upper-left lip, 8 toward the tip |
| forearm | 6 cyan | 6 into 4 shadow — darkest hand form, it recedes |
| palm | 6 cyan | 6 base, 14 highlight, 4 shadow |
| thumb, all four fingers | 6 cyan | 6 base, 14 highlight top-left, 4 shadow |

No warm index (1, 3, 5) anywhere in the piece.

## Light

**ONE source: top-left**, high, in front of the pane.

- Glazed pane: its upper and left faces catch 12; the pane darkens
  down-right.
- Casement bars (slab_px, same top-left): top and left face of each bar
  lit, lower-right face dark. The bars are the only forms in the pane
  plane with real thickness, so they are what sells the surface once
  shading exists — but the plane must already read without them lit.
- Crack spikes: the upper-left lip of every crack takes the 12 hairline
  (glass bevel); the lower-right lip stays black.
- Palm (sphere_px, light_x/light_y up-left): lit on its upper-left arc,
  terminator running lower-right, 4 shadow at bottom-right.
- Each finger and the thumb (capsule_px, light_direction 'top-left'):
  lit stripe on the left flank, shadow on the right flank, so every
  finger is a cylinder lit from the same side.
- Forearm (capsule_px, same top-left): held near shadow value throughout
  — it is inside the hole, shaded by the pane.
- The void is not lit. Nothing inside the hole catches the source.

## Do not change

1. The hand stays in FRONT of the pane plane. Nothing overdraws the
   fingers — not the transom, not the mullion, not a shard.
2. The transom stays occluded by all four fingers and the mullion stays
   occluded by the thumb. Moving either bar clear of the hand removes the
   occlusion cue and the piece goes back to reading as cracked ground.
3. The mullion stays broken at the hole, with the stub below the lower rim.
4. One light direction, top-left, everywhere. No second source in the void.
5. Finger gaps stay open — they are both the hand read and the transom
   read. Do not fill between fingers at any pass.
6. Hole stays ~4x the forearm width, with void showing on both sides.
7. The hole's lower rim stays closed inside the frame.
8. Middle finger stays the longest, pinky the shortest.
9. Palm as sphere_px, every finger/thumb/forearm as capsule_px, pane and
   casement bars as slab_px. No fill_px on any of them after block-in.
10. No warm colours.
11. Finished hand span stays >= 55% of canvas width.
12. No head or sill bar, and no decorative border — the casement is
    subject, not frame. The frame pass, if any, comes later and outside
    these 80x100 px.
