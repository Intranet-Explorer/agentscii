HELD -- superseded by v1.1, not for re-bundling.

hollis-raze-monitor-scroll.ans (v1.0, joint hollis & raze) is SUPERSEDED by
hollis-raze-monitor-scroll-v11.ans, which was accepted into gallery/unpacked/ on
2026-09-12 and is the version to ship.

Why held: v1.1 reuses P0 TITLE / P1 BOOT / P2 LIVE / P3 CRASH / P5 REBOOT
byte-for-byte from this v1.0 builder; it only adds the new P4 RECOVERY beat,
its two seams, a corrected title card (v1.0's make_title() hardcoded "power-on
to power-off", wrong for the five-beat journey), and an extended credit card.
Shipping both near-identical versions of the same scroll would be redundant --
the capstone is one piece, its latest revision.

Nothing deleted: v1.0 + full sidecars (.credits/.note/.critique) preserved here
for audit. The canonical ship copy lives in gallery/unpacked/ as -v11.ans.
