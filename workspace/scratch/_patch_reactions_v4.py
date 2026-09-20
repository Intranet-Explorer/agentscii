#!/usr/bin/env python3
# Patch make_reactions.py -> make_reactions_v4.py: fix the broken Gray-Scott update.
s = open("make_reactions.py").read()

old = '''def simulate(feed, kill, steps, seed, dA=0.2, dB=0.1):
    rng = np.random.default_rng(seed)
    A = np.ones((SH, SW), dtype=np.float64)
    B = np.zeros((SH, SW), dtype=np.float64)
    cy0, cy1 = SH//2 - 5, SH//2 + 6
    cx0, cx1 = SW//2 - 9, SW//2 + 10
    B[cy0:cy1, cx0:cx1] = 1.0
    D_A, D_B = 1.0, 0.5
    DAMP = 0.12                          # implicit-like damping keeps the explicit scheme stable
    for _ in range(steps):
        la = lap9(A); lb = lap9(B)
        react = A*A*B*3.0
        A = A + D_A*DAMP*la - react + feed*(1-A)
        B = B + D_B*DAMP*lb + react - (kill+feed)*B
        np.clip(A, 0.0, 1.0, out=A)
        np.clip(B, 0.0, 1.0, out=B)
    return B'''

new = '''def simulate(feed, kill, steps, seed, dA=0.2, dB=0.1):
    rng = np.random.default_rng(seed)
    A = np.ones((SH, SW), dtype=np.float64)
    B = np.zeros((SH, SW), dtype=np.float64)
    cy0, cy1 = SH//2 - 5, SH//2 + 6
    cx0, cx1 = SW//2 - 9, SW//2 + 10
    B[cy0:cy1, cx0:cx1] = 1.0
     # standard Gray-Scott explicit Euler (dt=1): A fed+consumed by reaction,
     # B produced by reaction and killed. Stable for dA~0.16-0.20, dB~0.08-0.10.
    for _ in range(steps):
        la = lap9(A); lb = lap9(B)
        react = A*A*B
        An = A + dA*la - react + feed*(1.0 - A)
        Bn = B + dB*lb + react - (kill + feed)*B
        np.clip(An, 0.0, 1.0, out=An)
        np.clip(Bn, 0.0, 1.0, out=Bn)
        A, B = An, Bn
    return B'''

assert old in s, "old simulate() block not found -- aborting"
s = s.replace(old, new)

# more steps so patterns have time to grow; widen D search into the stable band
s = s.replace("B = simulate(feed, kill, 600, seed, dA, dB)",
               "B = simulate(feed, kill, 1200, seed, dA, dB)")

s = s.replace("DIFF = [ (0.2,0.1), (0.15,0.075), (0.1,0.05), (0.08,0.04) ]",
               "DIFF = [ (0.16,0.08), (0.20,0.10), (0.18,0.09), (0.14,0.07) ]")

# write to a v4 output so we don't clobber the broken v3 on disk
s = s.replace('open("scratch/raze-reactions.ans"', 'open("scratch/raze-reactions-v4.ans"')
s = s.replace('open("scratch/raze-reactions.ans", "rb")',
               'open("scratch/raze-reactions-v4.ans", "rb")')

# title bump v3 -> v4 (plain substring, no nested-quote escaping)
s = s.replace("REACTIONS v3.0 -- gray-scott", "REACTIONS v4.0 -- gray-scott")

open("make_reactions_v4.py", "w").write(s)
print("patched OK: standard stable Gray-Scott, 1200 steps, widened D band, v4 output")
