#!/usr/bin/env python3
# One-shot patch: replace duo_v2's two-stop steel/teal ramps with multi-stop
# light->hue ramps that co-vary DENSITY and BRIGHTNESS per cell (the stride/VIGIL
# technique). This is the single change that turns flat silhouettes into lit bodies.
import re, io

p = "scratch/_duo_v2.py"
src = open(p, encoding="utf-8").read()

new_steel = '''def steel(Lv):
    """steel-blue ramp (VIGIL lineage), MULTI-STOP: deep-blue shadow -> blue ->
    cyan mid -> white-hot highlight. Density AND brightness both track the light,
    so a lit surface reads as a rounded 3D form, not a flat block. Opposite light
    field to teal's, so the two sentinels read as two lit bodies in confrontation."""
    Lv = max(0.0, min(1.0, Lv))
    if Lv > 0.84:
        return "\u2588", 15          # white-hot crest
    elif Lv > 0.66:
        return "\u2588", 12          # bright cyan shoulder
    elif Lv > 0.46:
        return "\u2593", 6           # blue mid-body
    elif Lv > 0.26:
        return "\u2592", 4           # dim blue shadow
    else:
        return "\u2591", 8           # near-black falloff into the void'''

new_teal = '''def teal(Lv):
    """cyan/teal ramp, MULTI-STOP: deep-teal shadow -> green-cyan mid -> bright cyan.
    Same density+brightness co-variation as steel but on a cooler/greener hue so the
    two figures stay distinct in the confrontation. Lit upper-RIGHT (opposite field)."""
    Lv = max(0.0, min(1.0, Lv))
    if Lv > 0.84:
        return "\u2588", 15          # white-hot crest
    elif Lv > 0.66:
        return "\u2588", 14          # bright cyan shoulder
    elif Lv > 0.46:
        return "\u2593", 2           # green/teal mid-body
    elif Lv > 0.26:
        return "\u2592", 10          # dim teal shadow
    else:
        return "\u2591", 8           # near-black falloff into the void'''

# Replace the steel ramp block (from 'def steel' up to but not including 'def teal')
src = re.sub(r"def steel\(Lv\):.*?\n(?=def teal)", new_steel + "\n\n", src, count=1, flags=re.S)
# Replace the teal ramp block (from 'def teal' up to but not including 'def cap')
src = re.sub(r"def teal\(Lv\):.*?\n(?=def cap)", new_teal + "\n\n", src, count=1, flags=re.S)

open(p, "w", encoding="utf-8").write(src)
print("patched steel/teal ramps in", p)
