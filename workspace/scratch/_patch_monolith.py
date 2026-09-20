# patch _monolith.py: (a) tighten light so the form reads as a rounded lit body,
# (b) cool-only phosphor tail (drop green), (c) gentler mirror jitter, (d) rim highlight.
import re
src = open("scratch/_monolith.py").read()

# (a) L_left: let the radial light field do more work, less axial wash-out
old_L = '''def L_left(x, y):
    r = light_field(x, y, 18, 9, lmax=30.0, ambient=0.10)    # single source, upper-left
    axial = 0.5 + 0.5 * (CX - x) / 20.0                       # extra bias toward the lit side
    return max(0.0, min(1.0, r * 0.6 + axial * 0.4))'''
new_L = '''def L_left(x, y):
    r = light_field(x, y, 16, 8, lmax=26.0, ambient=0.06)    # single source, upper-left, tight
    axial = 0.35 + 0.45 * (CX - x) / 22.0                     # gentle bias toward the lit side
    return max(0.0, min(1.0, r * 0.78 + axial * 0.22))'''
assert old_L in src, "L_left block not found"
src = src.replace(old_L, new_L)

# (b) cool-only phosphor wheel: drop green (92), keep blue/cyan/teal only
old_ph = "PHOS = [94, 96, 92, 105]           # dim cool phosphor wheel the reflection shimmers through"
new_ph = "PHOS = [94, 96, 97, 105]           # cool-only phosphor wheel (blue/cyan/white) -- no green bleed"
assert old_ph in src, "PHOS line not found"
src = src.replace(old_ph, new_ph)

# (c) gentler mirror jitter: amplitude 0.6 -> 0.3 so the tail reads as a wavering mirror, not scattered blocks
old_jit = "        jit = round(0.6 * math.sin((my) * 0.55 + depth * 0.3))"
new_jit = "        jit = round(0.3 * math.sin((my) * 0.42 + depth * 0.25))"
assert old_jit in src, "jit line not found"
src = src.replace(old_jit, new_jit)

open("scratch/_monolith.py", "w").write(src)
print("patched: L_left tightened, PHOS cool-only, jitter gentler")
