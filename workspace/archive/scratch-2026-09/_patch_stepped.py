#!/usr/bin/env python3
# v13 joint pass (raze + hollis): fix "stacked color bands" on THE ONE WHO STEPPED OUT.
import re

src = open("_stepped.py").read()

def replace_block(src, start_marker, end_marker, new_text, label):
    i = src.index(start_marker)
    j = src.index(end_marker, i)
    assert i != -1 and j != -1, f"{label}: markers not found"
    return src[:i] + new_text + src[j:]

# --- (1) warm_wheel -> single continuous-hue wheel -----------------------------
new_wheel = '''def warm_wheel(li):
      """ONE continuous lit surface: a SINGLE warm hue across the whole skull/jaw/body so form
    reads from DENSITY falloff, not from color boundaries between parts (the v12 'stacked bands'
    failure). The reference (ghengis shades_of_a_shade) carries a lit figure's form by density
    inside one hue; hard hue boundaries read as 'colored ASCII.' Bright amber across the lit
    cheek/forehead, dimming to warm orange ONLY in deep shadow -- the shadow stays WARM so a lit
    figure never reads blue against the cold crowd. White-hot catch-light at the very crest."""
    if li > 0.95:
        return WARM_HI              # 15 white-hot catch-light, tiny crest only
    if li < 0.30:
        return ORANGE               # 9 warm orange -- deep shadow side (stays WARM; lit figure != blue)
    return AMBER                    # 11 bright amber -- the continuous lit surface, density carries form

'''
src = replace_block(src, "def warm_wheel(li):", "\ndef shade_hero(", new_wheel, "warm_wheel")

# --- (2) eye signature: bigger default radius ----------------------------------
src = src.replace("def eye(cv, cx, cy, r=1.5, iris_fg=CYAN):",
                  "def eye(cv, cx, cy, r=2.0, iris_fg=CYAN):")

# socket wall -> dim (8) so the eye pops against the warm skull
src = re.sub(r'cv\.set\(x, y, "\\\u2591", COOL_SH, 0\)\s*# shadowed socket wall.*',
             'cv.set(x, y, "\\u2591", 8, 0)               # shadowed socket wall -- dim, so the eye pops',
             src)

# --- (3) draw sequence: head as ONE surface, eyes bigger/higher-contrast -------
old_seq_pat = re.compile(
    r'    shade_hero\(cv, in_head\).*?mouth\(cv, HERO_X, HEAD_CY \+ 7\.0, 3\.4\)',
    re.DOTALL)
new_seq = '''     # (a) skull+jaw as ONE continuous lit surface -- density carries form, NO per-part color reset
    shade_hero(cv, in_head)               # (a1) skull: single warm hue, tight local light field
    rim_light(cv, in_head)                # (a2) white-hot lit-edge rim -- separates silhouette from crowd
    shade_hero(cv, jaw_region)            # (b) jaw/chin: SAME wheel/hue -> one skull, not a band
    shade_hero(cv, body_region, floor_warm=True)       # (c) shoulders+torso to waist -- stays warm

      # (d) constructed anatomy on top of the lit skull -- eyes bigger + higher contrast so the
      #      "face you can look INTO" reads at thumbnail scale (the v12 gap hollis flagged).
    brow_ridge(cv, HERO_X, HEAD_CY - 3.0, 5.4)
    eye(cv, HERO_X - 3.2, HEAD_CY - 0.6, r=2.0, iris_fg=CYAN)
    eye(cv, HERO_X + 3.2, HEAD_CY - 0.6, r=2.0, iris_fg=CYAN)
    nose(cv, HERO_X, HEAD_CY + 0.5, HEAD_CY + 5.0)
    mouth(cv, HERO_X, HEAD_CY + 7.0, 3.4)'''
src2 = old_seq_pat.sub(lambda m: new_seq, src, count=1)
assert src2 != src, "draw sequence not replaced"
src = src2

# --- (4) version tag -----------------------------------------------------------
src = src.replace('title="THE ONE WHO STEPPED OUT v1.0"', 'title="THE ONE WHO STEPPED OUT v1.3"')

open("_stepped.py", "w").write(src)
print("patched OK")
