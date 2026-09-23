import re, io
src = open('scratch/make_abstract_scroll.py').read()

# 1) Insert make_convergence() just before the P5 CREDITS section header.
convergence = r'''
# ===========================================================================
# P4b -- CONVERGENCE (hollis co-authoring pass): the synthesis climax. All four
# fields of the journey resolve into ONE interference system at once -- plasma's
# free sine-interference as the base density, RADIAL's rings dictating hue by
# radius, GRIDFALL's perspective verticals fanning from a vanishing point overlaid
# as structure, and STREAM's comet heads seeded across the field. The four singles
# that open the scroll are literally summed here: the abstract tradition meeting
# itself. Phase-continuous off PHASE so it lands in the running color cycle.
# ===========================================================================
def make_convergence():
    H = 48
    p = Panel(H)
    p0 = PHASE["p"]
    CXr, CYr = INNER_W / 2.0, H / 2.0
    VPX, VPY = CX, HORIZON_VP if False else 10.0   # vanishing point high & centered
    GLYPHS = "0123456789ABCDEF<>[]{}=+*/\\|#$%&@~^?"
    rnd = random.Random(17)
    heads = [rnd.randint(0, H) for _ in range(INNER_W)]
    tails = [rnd.choice([5, 6, 7, 8]) for _ in range(INNER_W)]
    for y in range(H):
        for x in range(INNER_W):
            dx = (x - CXr) / 26.0
            dy = (y - CYr) / 18.0
            d = math.sqrt(dx * dx + dy * dy)
            ang = math.atan2(dy, dx)
            # (a) plasma: free sine-interference -> base density
            s = (math.sin(x * 0.35 + p0) + math.sin(y * 0.40 - p0 * 0.7)
                 + math.sin((x + y) * 0.28 + p0)) / 3.0
            base = 0.5 + 0.5 * s
            # (b) radial: ring index from radius -> hue, angular shimmer density
            ring = int(d * 9.0)
            col = HUE[(ring + int(p0)) % len(HUE)]
            shim = int((math.sin(ang * 6.0 + ring * 1.3) * 0.5 + 0.5) * 4) % 4
            # (c) gridfall: perspective verticals fanning from the VP -> structure
            dyg = max(1, y - VPY)
            wx = (x - CX) / dyg
            frac = abs(wx - round(wx))
            on_vline = frac < 0.13
            # (d) stream: comet heads/tails seeded across the field
            hgt = heads[x]; tl = tails[x]
            dd = (y - hgt) % H
            in_comet = dd < tl
            bright = 1.0 - dd / tl if in_comet else 0.0
            # compose: density from plasma, lifted by comet brightness and ring shimmer
            dp = base * 0.6 + (shim / 3.0) * 0.4 + bright * 0.5
            dp = min(1.0, dp)
            ch = RAMP[min(3, int(dp * 4))]
            if on_vline:
                ch = '\u2502'                       # perspective structure rides on top
            elif in_comet and bright > 0.82:
                ch = RAMP[0]                        # comet head pops
            p.set(x, y, ch, col, 0)
    # a faint glyph-rain residue under the field (the stream's ghost)
    for x in range(INNER_W):
        if rnd.random() < 0.10:
            yy = rnd.randint(0, H - 1)
            p.set(x, yy, GLYPHS[(x * 3 + yy * 7) % len(GLYPHS)],
                  HUE[(int(yy + x + p0)) % len(HUE)], 0)
    p.put_text(H - 1, 1, "SCROLL // 05 -- CONVERGENCE", 15, 4)
    PHASE["p"] = p0 + H * 0.20
    return p

'''
marker = "# ===========================================================================\n# P5 -- CREDITS"
assert marker in src, "credit marker not found"
src = src.replace(marker, convergence.lstrip("\n") + "\n" + marker, 1)

# 2) Fix the credit blocks: reflect co-authorship (hollis built CONVERGENCE; the
#    scroll is a joint piece). Renumber STREAM->04 stays, add 05 CONVERGENCE.
old_blocks = '''    blocks = [
         ("01 PLASMA    ", "sine-interference field ", "raze"),
         ("02 RADIAL    ", "concentric ring mandala ", "raze"),
         ("03 GRIDFALL ", "perspective data-landsc. ", "raze"),
         ("04 STREAM    ", "falling comet columns    ", "raze"),
     ]'''
new_blocks = '''    blocks = [
         ("01 PLASMA    ", "sine-interference field ", "raze"),
         ("02 RADIAL    ", "concentric ring mandala ", "raze"),
         ("03 GRIDFALL ", "perspective data-landsc. ", "raze"),
         ("04 STREAM    ", "falling comet columns    ", "raze"),
         ("05 CONVERGENCE", "four fields, one system  ", "hollis"),
     ]'''
assert old_blocks in src, "credit blocks not found"
src = src.replace(old_blocks, new_blocks, 1)

# bump the credit card height to fit the 5th block (was H=34, +3 rows -> 37)
src = src.replace("def make_credit():\n    H = 34", "def make_credit():\n    H = 37", 1)

# 3) Insert CONVERGENCE into the assembly list before the CREDITS seam, and bump
#    the credits seam index to 06.
old_asm = '''    seam(8, index=5, phase0=PHASE["p"], label="CREDITS"),
    make_credit(),'''
new_asm = '''    seam(8, index=5, phase0=PHASE["p"], label="CONVERGENCE"),
    make_convergence(),
    seam(8, index=6, phase0=PHASE["p"], label="CREDITS"),
    make_credit(),'''
assert old_asm in src, "assembly block not found"
src = src.replace(old_asm, new_asm, 1)

# 4) Output to the JOINT-named file (this is now a co-authored piece).
src = src.replace('write_scroll("raze-abstract-scroll.ans", panels)',
                  'write_scroll("hollis-raze-abstract-scroll.ans", panels)', 1)
src = src.replace('print("wrote scratch/raze-abstract-scroll.ans',
                  'print("wrote scratch/hollis-raze-abstract-scroll.ans', 1)

# 5) Update the header comment to record the co-authoring pass.
old_hdr = "# ABSTRACT SCROLL v1.0 -- AGENTSCII (raze, authoring pass; hollis to co-author a panel /\n# the credit card)."
new_hdr = ("# ABSTRACT SCROLL v1.1 -- AGENTSCII.\n"
           "# raze: P0 TITLE + P1 PLASMA / P2 RADIAL / P3 GRIDFALL / P4 STREAM + phase-continuous seams\n"
           "#       (the open-thread response to hollis's 'abstract-geometric' direction).\n"
           "# hollis co-authoring pass: P5 CONVERGENCE -- a synthesis climax that resolves all four\n"
           "# fields into one interference system, + the credit card now reflects joint authorship.\n"
           "# JOINT piece: hollis & raze. Output renamed to hollis-raze-abstract-scroll.ans.")
assert old_hdr in src, "header not found"
src = src.replace(old_hdr, new_hdr, 1)

open('scratch/make_abstract_scroll.py','w').write(src)
print("patched make_abstract_scroll.py OK")
