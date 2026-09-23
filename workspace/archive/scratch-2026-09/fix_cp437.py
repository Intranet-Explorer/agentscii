M = {0x2500:0xc4, 0x2502:0xd8, 0x250c:0xb3, 0x2510:0xbf, 0x2514:0xa9, 0x2518:0xc0,
     0x251c:0xda, 0x2524:0xb2, 0x252c:0xc3, 0x253c:0xbf, 0x2552:0xf3, 0x2553:0xf6,
     0x2554:0xda, 0x2557:0xfc, 0x2558:0xf4, 0x2559:0xee}

for p in ("submissions/raze-plasma.ans", "submissions/raze-gridfall.ans"):
    b = open(p, "rb").read()
    out = bytearray()
    i = 0
    n = len(b)
    fixed = 0
    while i < n:
        c = b[i]
        if c == 0xe2 and i + 2 < n and 0x80 <= b[i+1] <= 0xbf and 0x80 <= b[i+2] <= 0xbf:
            cp = ((b[i] & 0x3f) << 12) | ((b[i+1] & 0x3f) << 6) | (b[i+2] & 0x3f)
            if cp in M:
                out.append(M[cp])
                fixed += 1
                i += 3
                continue
        out.append(c)
        i += 1
    open(p, "wb").write(out)
    print(p, "fixed", fixed, "-> CP437")
