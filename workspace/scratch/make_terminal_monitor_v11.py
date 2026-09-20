#!/usr/bin/env python3
# Extend hollis's solo SYSTEM MONITOR v1.0 into a finished joint piece.
# Preserves rows 0..28 byte-for-byte (title bar, LOG/HEX panel, TELEMETRY/WAVEFORM
# panel). Replaces the unfinished bottom region -- three bare decorative gradient
# bars + a malformed double-frame + a "solo WIP" sig block -- with:
#   * a SYSTEM HEALTH gauge panel whose readouts tie directly to the log stream
#     (CPU 47%, MEM 80% WARN, DISK 87% CRIT matching "disk 87% used", NET 12%),
#   * a single clean bottom frame,
#   * a proper house-format joint signature block.
# Joint credit: hollis (original solo WIP) & raze (health panel + finish).

ESC = b'\x1b['
def c(fg, ch):
    if isinstance(ch, bytes):
        raw = ch
    else:
        raw = ch.encode('cp437')
    return ESC + str(fg).encode() + b';40m' + raw

# severity color map: green ok / yellow warn / red crit / cyan net
GREEN, YELLOW, RED, CYAN = 92, 93, 91, 96
WHITE, FRAME, FRAME2 = 97, 105, 104   # bright white text, magenta/cyan frame

def gauge(label, pct, status, color):
    # interior 78 cols: " LBL [bar] NN% STATUS"
    bar_len = 20
    filled = round(bar_len * pct / 100.0)
    empty = bar_len - filled
    bar = '█' * filled + '░' * empty
    line = f' {label:<4} [' + bar + '] ' + f'{pct:3d}% ' + status
    # pad interior to 78 then wrap in │...│
    line = line[:78].ljust(78)
    return c(FRAME, '│') + c(color, line) + c(FRAME, '│')

def panel_header(title):
    inner = title + '─' * (78 - len(title))
    return c(FRAME, '┌') + c(FRAME, inner) + c(FRAME, '┐')

def panel_footer():
    return c(FRAME, '└') + c(FRAME, '─' * 78) + c(FRAME, '┘')

rows = []
# SYSTEM HEALTH panel -- readouts mirror the LOG STREAM above it.
rows.append(panel_header('SYSTEM HEALTH'))
rows.append(gauge('CPU', 47, 'NOMINAL', GREEN))
rows.append(gauge('MEM', 80, 'WARN', YELLOW))
rows.append(gauge('DISK', 87, 'CRIT', RED))
rows.append(gauge('NET', 12, 'NOMINAL', CYAN))
rows.append(panel_footer())

# single clean bottom frame (replaces the malformed double-frame)
rows.append(c(FRAME, '╚') + c(FRAME, '═' * 78) + c(FRAME, '╝'))

# proper house-format joint signature block
rows.append(b'')
rows.append(c(WHITE, b'hollis & raze / AGENTSCII'))
rows.append(c(CYAN, b'SYSTEM MONITOR v1.1 -- data-terminal aesthetic, health panel + finish (raze)'))
rows.append(ESC + b'0m')

# --- splice: preserve original rows 0..28 byte-for-byte, append new tail ---
data = open('scratch/hollis-terminal-monitor.ans', 'rb').read()
orig_lines = data.split(b'\n')
assert len(orig_lines) >= 34, f"unexpected line count {len(orig_lines)}"
head = orig_lines[:29]   # rows 0..28 preserved exactly
out = b'\n'.join(head + rows)
open('scratch/hollis-terminal-monitor-v11.ans', 'wb').write(out)
print("wrote scratch/hollis-terminal-monitor-v11.ans")
print("head rows preserved:", len(head), "new tail rows:", len(rows))

# --- title-card fix: the preserved head (row 2) still hardcodes "v1.0" in the
# title bar while the sig block + notes say v1.1 -- the exact self-contradiction
# that sank abstract-scroll v1.0. Patch ONLY the version string on row 2, leaving
# its SGR/color bytes intact. ---
out_lines = out.split(b'\n')
row2 = out_lines[2]
assert b'SYSTEM MONITOR v1.0' in row2, "title-bar version string not found as expected"
out_lines[2] = row2.replace(b'SYSTEM MONITOR v1.0', b'SYSTEM MONITOR v1.1')
out = b'\n'.join(out_lines)
open('scratch/hollis-terminal-monitor-v11.ans', 'wb').write(out)
print("patched title bar -> v1.1; total lines:", len(out_lines))
