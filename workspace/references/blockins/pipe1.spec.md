# pipe1 — LANTERN ROCK

Pixel space is 80 wide x 100 tall (50 cell rows). All coordinates below
are pixel-space, origin top-left, y increasing downward.

## Subject

A tall stone lighthouse standing on a sea stack at night, its lamp the only
light in frame, with a single small boat far out on the open water to the
left — near, middle and far read as three plainly different sizes.

## Layout

| element | x..x | y..y | size | plane |
|---|---|---|---|---|
| night sky | 0..80 | 0..60 | 80 x 60 | background |
| open sea | 0..80 | 60..100 | 80 x 40 | background → midground |
| horizon line | 0..80 | y = 60 | — | background |
| boat hull | 15..25 | 66..70 | 10 x 4 | background |
| boat mast | 19..20 | 58..66 | 1 x 8 | background |
| rock crown | 47..67 | 62..70 | 20 x 8 | midground |
| rock shoulder | 42..71 | 70..80 | 29 x 10 | midground |
| rock foot | 37..80 | 80..92 | 43 x 12 | midground |
| tower lower shaft | 48..64 | 50..62 | 16 x 12 | foreground |
| tower mid shaft | 49..63 | 36..50 | 14 x 14 | foreground |
| tower upper shaft | 51..61 | 24..36 | 10 x 12 | foreground |
| gallery ring | 47..65 | 20..24 | 18 x 4 | foreground |
| lantern room (THE LAMP) | 51..61 | 12..20 | 10 x 8 | foreground |
| roof cap | 49..63 | 8..12 | 14 x 4 | foreground |
| near water, 5 bottom-anchored steps | 0..80 | crest 86..95 → 100 | full width | foreground |
| spray, windward | circles (33,88)r5 (27,92)r4 (39,92)r3 | | | foreground |
| spray, leeward | circles (71,89)r4 (77,93)r3 | | | foreground |

Compositional anchors: the tower's vertical axis sits at x = 56, on the
right-hand third. The boat sits at x = 20, on the left-hand third. The
36 px of empty sea between them is the subject of the piece as much as
the tower is — it is what makes the boat read as far away rather than small.
The horizon at y = 60 puts the sky at 60% of frame and the tower crossing
it from y = 8 to y = 62, so the tower spans both planes and the rock and
boat do not.

## Scale

- tower height : rock stack visible height = **54 : 30 ≈ 1.8 : 1**
- tower height : boat total height (masthead to waterline) = **54 : 12 = 4.5 : 1**
- tower height : boat hull height = **54 : 4 = 13.5 : 1**
- tower base width : rock foot width = **16 : 43 ≈ 1 : 2.7**
- tower height : canvas height = **54 : 100** — the tower owns over half the frame
- boat hull length : tower base width = **10 : 16**, and the boat is roughly
  four times further from the viewer, so the implied real ratio is about **1 : 25**

The depth is carried by the second and third ratios, not by the first. The
rock is the near/far hinge: it is wider than the tower and narrower than the
sea, so it sits between them.

## Palette

| element | index | note |
|---|---|---|
| night sky | **4** blue | shade toward 0, highlight 12 near the lamp |
| open sea | **8** dark grey | shade toward 0 in troughs, 7 on crests |
| near water | **7** light grey | the only water lit enough to have a light face |
| rock (all three tiers) | **3** brown | shade toward 0; 11 permitted ONLY as a lamp-warmed rim on upward faces |
| tower masonry, gallery, roof | **7** light grey | shade toward 8, highlight 15 |
| lantern room | **11** bright yellow | the light source — the only large 11 mass in the piece |
| boat | **0** black | pure silhouette, no interior value |
| spray | **15** white | the second-brightest thing after the lamp |

Nothing in the piece is 1, 2, 5, 6, 9, 10, 13 or 14. It is a three-family
palette — blue night, brown rock, grey stone — with one yellow source.

## Light

**One direction for the whole piece: from the top-right.** The source is the
lamp at pixel (56, 16); every ray in the scene travels down and to the left
from that point.

- **lantern room** — emits; no shaded face, it is the brightest value in frame
- **roof cap / gallery ring** — top surfaces dark (above the lamp), undersides
  lit by the lamp directly beneath them; this inversion is correct and is the
  one place the light reads as a point source
- **tower shaft** — lit down its **right** face, dark on the left against the sky
- **rock crown** — lit on its **top** face (directly under the lamp) and its
  right flank; the left flank falls away into shadow
- **rock shoulder and foot** — lit on **upper-right** faces only; everything
  the crown overhangs is in shadow
- **boat** — lit on its **top-right** face, the side turned toward the tower;
  its left side is unlit, which is what makes it read as looking at the light
- **spray and near water** — crest tops and right faces lit; troughs and left
  faces dark
- **sky** — darkest at the left edge and at the top, warming slightly toward
  the lamp

## Do not change

1. **The tower's axis at x = 56 and the boat at x = 20.** The empty sea between
   them is the composition. Do not fill it, texture it heavily, or add any
   element into it.
2. **The three scale ratios** — 1.8 : 1 tower-to-rock, 4.5 : 1 tower-to-boat,
   13.5 : 1 tower-to-hull. Detail passes may soften edges but must not grow
   the boat or shorten the tower.
3. **One light direction, top-right, sourced at (56, 16).** Including the
   inverted lit face under the gallery and roof cap. No second light anywhere.
4. **The horizon at y = 60**, unbroken except by the tower, the rock and the
   boat's mast.
5. **The lantern room as the only yellow mass.** 11 elsewhere is a rock rim
   highlight at most, never a field.
6. **The boat stays a flat black silhouette.** No interior detail, no rigging
   beyond the single mast — it is the far scale marker, and detail there
   destroys the depth read.
7. **Element count: three subjects only** — tower, rock, boat. No gulls,
   no second stack, no moon, no beam cone.
