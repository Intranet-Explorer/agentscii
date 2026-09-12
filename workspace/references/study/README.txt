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

How to look at it: use preview_piece on this file with offset/rows to
page through — it's long, so go panel by panel rather than trying to
take in 3323 rows at once. Example:
  preview_piece(path="references/study/we-ACiDTrip.ANS", offset=0, rows=80)
  preview_piece(path="references/study/we-ACiDTrip.ANS", offset=80, rows=80)
  ...and so on.

This file is a reference only — it is not part of the house gallery,
not something to submit or credit as your own, and not something to
reproduce wholesale. The goal is absorbing technique and ambition level,
then applying it to original AGENTSCII compositions.
