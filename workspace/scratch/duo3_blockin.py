"""duo3 block-in. Region tools ONLY, and only for mass.

Subject: a face mid-transformation. Left (viewer's) side intact flesh;
the right temple/cheek/jaw is coming apart into ember, and the right eye
is the hot centre of it. That makes the transformation the light source,
so every form here is lit from the right-front -- one light, motivated.

Pixel space is 80 x 56 (28 cell rows). Geometry, all in px:
  skull   sphere  (38, 20) r14        -> y  6..34
  cheeks  capsule (32,30)-(44,30) r8  -> y 22..38
  chin    capsule (38,34)-(38,42) r6  -> y 28..48
  neck    capsule (38,46)-(38,58) r7  (drawn first, chin occludes it)
Head runs cell rows 3..24 of 28 -- a face filling its frame.

hi_color is the FLESH tone, not a bright one. The first pass used hi=11
and the sphere's lit band ramped from a solid glyph into a flat yellow
cap over a third of the skull -- a region-sized flat fill, the exact
defect this run exists to avoid. The lit half is left as quiet
substrate; ember light gets placed by hand, on cells that face it.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii')
import canvas_tools as ct

W = '/Users/octo/agentscii/workspace'
S = 'duo3'
FLESH, SHADOW = 3, 1           # brown / dark red
LX, LY = 58.0, 14.0            # the ember, right-front and slightly high

if not ct.canvas_exists(W, S):
    ct.new_canvas(W, S, 80, 28, bg=0)

# neck first so the chin occludes it -- occlusion is the only depth cue a
# block-in has (STYLE.md), and a jaw overlapping a neck reads as a head
# on a body rather than a mask floating.
ct.capsule_px(W, S, 38, 46, 38, 58, 7, SHADOW, light_direction="right",
              shadow_color=0, hi_color=SHADOW)
ct.sphere_px(W, S, 38, 20, 14, FLESH, LX, LY, shadow_color=SHADOW,
             hi_color=FLESH)
ct.capsule_px(W, S, 32, 30, 44, 30, 8, FLESH, light_direction="right",
              shadow_color=SHADOW, hi_color=FLESH)
ct.capsule_px(W, S, 38, 34, 38, 42, 6, FLESH, light_direction="right",
              shadow_color=SHADOW, hi_color=FLESH)
print(ct.metrics(W, S))
