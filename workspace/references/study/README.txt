REFERENCE: we-ACiDTrip.ANS — Blocktronics ACiD Trip (2013)

Source: https://16colo.rs/pack/blocktronics_acid_trip/we-ACiDTrip.ANS
Downloaded raw from: https://16colo.rs/pack/blocktronics_acid_trip/raw/we-ACiDTrip.ANS

What this is: a 23-artist collaborative ANSI scroll, DemoSplash 2013
ANSi/ASCII compo winner, one of the most-viewed ANSi pieces ever made.
80 columns wide, ~3325 rows tall when rendered (one continuous vertical
scroll built from ~775 logical lines that wrap at 80 cols, plus explicit
CRLF breaks — page through it in ~80-row chunks via preview_piece).

Why it's here: this is the technique reference for the house "Ambition
tier" in STYLE.md — study it for real craft, not to copy it panel-for-
panel. Look at:
  - how color-cycling dithering actually reads at a distance vs up close
  - how panels hand off into each other (no jarring hard cuts)
  - density and intentionality — very few cells are "wasted" flat fill
  - how a border/frame motif repeats and varies across a very long scroll
  - how multiple contributors' sections stay visually coherent as one
    piece despite 23 different hands

Files in this folder:
  - we-ACiDTrip.ANS -- the flagship deep-dive reference (see above). 3325-row
    scroll, panel handoffs, color-cycling dithering, a real demon/creature
    face (study @ row 2160) with gradient-built anatomical shading.
  - somms-neo_tokyo.ANS -- "Neo Tokyo" by Somms, ACiD Productions 1994. A
    muscular figure built entirely from shaded block regions -- study for
    how much anatomical structure (shoulder, chest, arm definition) a
    disciplined light-source + density-ramp pass can carry with NO gradient
    math, just careful hand-placed block-density choices per region. Uses
    real cursor-addressing (ESC[A, cursor-forward jumps) to layer shading
    onto rows already drawn -- this is THE technique gap the house has been
    missing: real ACiD work is rarely drawn top-to-bottom once, it's built
    in passes that go back and add detail.
  - ghengis_ragnarok-ides_of_march.ANS -- "Ides of March" by Ghengis &
    Ragnarok, ACiD Productions 1995. A two-artist joint character portrait
    (chick drawn by Ghengis, rest by Ragnarok per the piece's own credits)
    with genuinely dense per-feature shading: individually shaded strands
    of hair, jewelry with metallic highlight/shadow pairs, a fully
    constructed face with brow/cheek/jaw as separate lit surfaces. Also
    relies heavily on cursor-up layering -- study how the piece interleaves
    base color blocks with later highlight passes.
  - asphyx-acid_logo.ANS -- "ACiD" by Asphyx, ACiD Productions 2003. A
    wordmark/logo piece with a face built INTO the negative space of the
    lettering -- study for how a logo piece can carry real figurative
    content instead of being flat typography, and for dense background
    texture (this piece has almost no unshaded negative space anywhere).
  - nokturnal_emissions-millenium_edition.ANS -- "Millenium Edition" by
    Nokturnal Emissions, ACiD Productions 2003. A genie/creature face with
    a fully rendered horned head, individually shaded beard/mustache
    strands, and a dense patterned border framing a credits panel below --
    study for panel structure (art zone + separate text zone, both fully
    developed) and for background texture density around a figure (compare
    against how flat/empty the house's own figurative pieces leave their
    negative space).
  - ghengis-shades_of_a_shade.ANS -- "Shades of a Shade" by Ghengis, ACiD
    Productions 1996. Study for DENSE STIPPLED BACKGROUND FIELDS: even the
    areas that read as "empty" at a glance are covered in scattered
    grayscale dot/block marks at varying density, never truly flat black --
    this is the single biggest technique gap between house work and real
    ACiD pieces. Also a strong reference for saturated color blocking with
    hard-edged color transitions (not always gradient blends).
  - somms-the_powergrid.ANS -- "The PowerGrid" by Somms, ACiD Productions
    1995. Study for DIRECTIONAL STRAND SHADING: fur/mane/hair texture isn't
    a flat-shaded region, it's built from many short strokes that follow
    the surface's contour, alternating between 2-4 related hues per area
    so individual strands stay visually distinct instead of blurring into
    one flat mass. See canvas.py's strand_shade() for a reusable version
    of this technique.
  - avg-theterminator.ans -- a character portrait via SHADED BLOCK REGIONS
    (not per-cell gradient math) -- a different, equally valid technique for
    building a recognizable face: broad color-region blocking with internal
    shading transitions, plus a real title-card wordmark top and bottom.
  - del-jaws.ans -- a scene composition: wordmark banner, gradient-shaded
    water, a submerged silhouette shape rising into frame, a tagline caption.
    Good reference for landscape/scene pieces with a clear focal subject.
  - we-One_love.ans -- a longer (150-row) piece combining a character
    portrait with a logo treatment -- study for how a figure and a wordmark
    share one composition without either one looking like an afterthought.
  - acdu1190_1.ans, bt_acidtrip_1.ans (+ critique), bt_what-happened-with-
    luciano-ayres.ans -- earlier-gathered study files, kept for reference.

NOTE on cursor-addressing (ESC[A / ESC[B / ESC[row;colH): several of the
newer references above use this real classic-scene technique -- draw a base
layer, then move the cursor back to an already-drawn row to add highlights,
shadows, or fine detail on top, rather than getting every cell right in one
top-to-bottom pass. preview_piece's renderer (harness.py) was fixed to
actually support this (a real row/col cursor model, not a flat per-line
parser) -- before the fix, any piece using this technique rendered as
diagonal garbage. If a preview ever looks like torn/streaked static instead
of a coherent image, that's a real render bug worth flagging, not a broken
reference file.

All downloaded raw from 16colo.rs (raw/ endpoint, unmodified source bytes).
Same rule as before: study technique, don't reproduce or resubmit any of
these as house work. If you want more variety than what's here, more real
Blocktronics/ACiD packs exist at 16colo.rs/group/blocktronics -- pull
additional individual pieces via curl if a specific technique gap calls
for a specific reference (e.g. "I want to see how a real piece handles X").

