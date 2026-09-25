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
for name in ['duo3_blockin', 'duo3_left', 'duo3_nose', 'duo3_mouth',
             'duo3_fore', 'duo3_right', 'duo3_bg',
             'duo3_reencode', 'duo3_model', 'duo3_eye2', 'duo3_mouth2', 'duo3_planes']:
    print(name, subprocess.run([sys.executable, str(HERE / (name + '.py'))],
                               capture_output=True, text=True).stdout.strip())
