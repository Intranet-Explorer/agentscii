"""Rebuild duo3 from nothing, in pass order. Every pass is idempotent
over a fresh canvas, so the piece is reproducible rather than being a
JSON blob whose history only exists in one session's scrollback."""
import subprocess, sys, pathlib
HERE = pathlib.Path(__file__).parent
CANVAS = HERE.parent / 'canvases' / 'duo3.json'
if '--fresh' in sys.argv:
    CANVAS.unlink(missing_ok=True)
# Session 2 appends three passes. duo3_reencode MUST run exactly once and
# before the feature passes: it re-spells RAMP cells and reads their value
# back out of the cell, so running it twice with a different band set
# quantises the value twice and flattens the surface it is respelling.
# That is not hypothetical -- it happened live, and the cheek came back as
# eighteen identical cells. A fresh deterministic rebuild is the fix.
# Session 4 appends five and replaces one. duo3_right2 supersedes
# duo3_right entirely (same territory, prominence-driven), and duo3_bg
# must follow it because it asks duo3_tools.reach() where each row's
# dissolve ends. The rebuilt features run AFTER their session-3
# versions rather than instead of them: duo3_eye3 owns rows 12-14 and
# leaves duo3_eye2's eyebrow and socket floor alone, so eye2 still has
# to lay those down first. duo3_hue is last and is a no-op on a fresh
# build -- BANDS and duo3_bg no longer make a magenta cell -- but its
# assert is the guard that says so.
# Session 5 appends two, and they go LAST among the drawing passes for
# a reason: duo3_contour moves the head's left edge and erases what used
# to be outside it, so anything that paints the intact half has to have
# painted it already. It also fills the masseter only into cells that
# are still empty, which is only well defined once everything else has
# had its turn.
for name in ['duo3_blockin', 'duo3_left', 'duo3_nose', 'duo3_mouth',
             'duo3_fore', 'duo3_right2', 'duo3_bg',
             'duo3_reencode', 'duo3_model', 'duo3_eye2', 'duo3_mouth2',
             'duo3_planes',
             'duo3_nose2', 'duo3_eye3', 'duo3_mouth3', 'duo3_planes2', 'duo3_buttress',
             'duo3_contour', 'duo3_neck',
             'duo3_hue']:
    print(name, subprocess.run([sys.executable, str(HERE / (name + '.py'))],
                               capture_output=True, text=True).stdout.strip())
