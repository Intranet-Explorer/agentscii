"""Rebuild duo3 from nothing, in pass order. Every pass is idempotent
over a fresh canvas, so the piece is reproducible rather than being a
JSON blob whose history only exists in one session's scrollback."""
import subprocess, sys, pathlib
HERE = pathlib.Path(__file__).parent
CANVAS = HERE.parent / 'canvases' / 'duo3.json'
if '--fresh' in sys.argv:
    CANVAS.unlink(missing_ok=True)
for name in ['duo3_blockin', 'duo3_left', 'duo3_nose', 'duo3_mouth',
             'duo3_right', 'duo3_fore', 'duo3_bg']:
    print(name, subprocess.run([sys.executable, str(HERE / (name + '.py'))],
                               capture_output=True, text=True).stdout.strip())
