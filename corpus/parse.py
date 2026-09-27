#!/usr/bin/env python3
"""Parse .ans/.asc files into cell-grid arrays, matching ansilove's output.

Behaviour checked against ansilove:
  - TAB advances to the next 8-column stop and paints nothing.
  - Control bytes 0x01-0x08 and 0x0B-0x1F render as CP437 glyphs. Only
    \\n, \\r, TAB and ESC (CSI sequences) are interpreted.
  - Rows are 80 columns; overflow wraps.

Each piece becomes a .npz with:
    chars      : (rows, cols) uint32 Unicode codepoints, space for empty cells
    fg, bg     : (rows, cols) uint8 palette index 0-15
    ice_colors : 0-d bool from SAUCE TFlags bit 0, False without SAUCE
    n_rows, n_cols : 0-d int32 content extent
    source_path, sauce_title, sauce_author, sauce_group, sauce_date : bytes
                 (empty if absent)

Cells that display identically are canonicalized to the same
(char, fg, bg) triple; see canonicalize_cell().

Usage:
    python3 corpus/parse.py --input-dir corpus/data --output-dir corpus/parsed
    python3 corpus/parse.py --file corpus/data/1996/forge_09/AS-MAXX.ANS
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

CORPUS_DIR = Path(__file__).resolve().parent
TERMINAL_WIDTH = 80  # same as harness.py's _TERMINAL_WIDTH
MAX_ROWS_SAFETY = 20000  # guards against corrupt files with endless newlines

_CSI_RE = re.compile(rb"\x1b\[([0-9;?]*)([A-Za-z])")
SAUCE_RECORD_LEN = 128
SAUCE_COMMENT_LINE_LEN = 64


def _decode_cp437(raw_bytes):
    """Decode CP437. Every byte maps to a glyph, so this never raises."""
    return raw_bytes.decode("cp437")


def strip_sauce(raw):
    """Return (content_bytes, sauce_dict_or_None).

    Content ends at the first 0x1A (DOS EOF), SAUCE or not; ansilove renders
    nothing after it. SAUCE is the last 128 bytes, starting b'SAUCE00', and
    is parsed for metadata only.
    """
    # SAUCE gives metadata only; the EOF byte decides where content ends.
    idx = raw.rfind(b"SAUCE00")
    sauce = None
    if idx >= 0 and len(raw) - idx >= SAUCE_RECORD_LEN - 7:
        full = raw[idx:]
        if len(full) >= SAUCE_RECORD_LEN:
            rec = full[:SAUCE_RECORD_LEN]

            def field(offset, length):
                return rec[offset:offset + length]

            title = field(7, 35).rstrip(b" ").decode("cp437", errors="replace")
            author = field(42, 20).rstrip(b" ").decode("cp437", errors="replace")
            group = field(62, 20).rstrip(b" ").decode("cp437", errors="replace")
            date = field(82, 8).decode("cp437", errors="replace")
            data_type = rec[95]
            file_type = rec[96]
            t_info1 = int.from_bytes(rec[97:99], "little")
            t_info2 = int.from_bytes(rec[99:101], "little")
            n_comments = rec[104]
            t_flags = rec[105]
            ice_colors = bool(t_flags & 0x01)
            sauce = {
                "title": title, "author": author, "group": group, "date": date,
                "data_type": data_type, "file_type": file_type,
                "columns": t_info1, "lines": t_info2, "ice_colors": ice_colors,
            }

    # Search from the start: ansilove stops at the first 0x1A, not the one
    # just before SAUCE.
    search_end = idx if idx >= 0 else len(raw)
    eof_pos = raw.find(b"\x1a", 0, search_end)
    if eof_pos < 0:
        content_end = search_end
    else:
        content_end = eof_pos

    return raw[:content_end], sauce


class Grid:
    """Sparse cursor-addressed cell grid with immediate end-of-line wrap.

    Filling column 80 wraps at once, so 80 chars + '\\n' + 'X' is three rows,
    as in ansilove. harness.py uses deferred wrap on purpose, because agent
    files end every line at exactly 80 columns; this parser follows ansilove.
    """

    def __init__(self):
        self.cells = {}  # (row, col) -> (codepoint, fg, bg, blink)
        self.row, self.col = 0, 0
        self.max_row_seen = 0
        self.base_fg, self.bright_fg, self.base_bg = 7, False, 0
        self.blink = False
        self.saved_row, self.saved_col = 0, 0  # ESC[s / ESC[u save/restore.
        # Common in archive files. ANSI.SYS keeps one saved position, no stack.

    def put(self, codepoint):
        if self.row > MAX_ROWS_SAFETY:
            raise ValueError(f"row count exceeded safety cap ({MAX_ROWS_SAFETY})")
        fg_idx = (self.base_fg + 8) if self.bright_fg else self.base_fg
        # Keep raw bg and the blink bit separate. Whether blink means bright
        # bg depends on the file's iCE flag; canonicalize_cell() resolves it.
        self.cells[(self.row, self.col)] = (codepoint, fg_idx % 16, self.base_bg % 16, self.blink)
        self.col += 1
        if self.col >= TERMINAL_WIDTH:
            # Immediate wrap; see class docstring.
            self.row += 1
            self.col = 0
            if self.row > self.max_row_seen:
                self.max_row_seen = self.row

    def newline(self):
        self.row += 1
        self.col = 0
        if self.row > self.max_row_seen:
            self.max_row_seen = self.row

    def tab(self):
        # Next 8-column stop, paint nothing. Known gap: near the right margin
        # ansilove does neither clamp nor wrap; this clamps to col 79. Rare.
        self.col = min(TERMINAL_WIDTH - 1, ((self.col // 8) + 1) * 8)


def parse_ans_bytes(content, ice_colors_hint=False):
    """Parse SAUCE-stripped .ans bytes into a Grid.

    ice_colors_hint is unused; iCE is resolved later in parse_file.
    """
    text_bytes = content.replace(b"\r\n", b"\n")
    # Match CSI on raw bytes and decode CP437 per glyph, as harness.py does.
    grid = Grid()
    pos = 0
    n = len(text_bytes)
    while pos < n:
        b = text_bytes[pos]
        if b == 0x0A:  # \n
            grid.newline()
            pos += 1
            continue
        if b == 0x09:  # TAB
            grid.tab()
            pos += 1
            continue
        if b == 0x1B:  # ESC
            m = _CSI_RE.match(text_bytes, pos)
            if m:
                param_str = m.group(1).decode("ascii", errors="replace")
                code = chr(m.group(2)[0])
                # Drop '?' from private-mode sequences (ESC[?7h etc.);
                # they have no grid effect and fall through as no-ops.
                param_str = param_str.lstrip("?")
                params = [int(c) for c in param_str.split(";") if c != ""]
                if code == "m":
                    for p in (params or [0]):
                        if p == 0:
                            grid.base_fg, grid.bright_fg = 7, False
                            grid.base_bg, grid.blink = 0, False
                        elif p == 1:
                            grid.bright_fg = True
                        elif p == 5:
                            grid.blink = True  # bright bg under iCE; see canonicalize_cell
                        elif p == 22:
                            grid.bright_fg = False
                        elif p == 25:
                            grid.blink = False
                        elif p == 39:
                            grid.base_fg, grid.bright_fg = 7, False
                        elif p == 49:
                            grid.base_bg = 0
                        elif 30 <= p <= 37:
                            grid.base_fg = p - 30
                        elif 90 <= p <= 97:
                            grid.base_fg, grid.bright_fg = p - 90, True
                        elif 40 <= p <= 47:
                            grid.base_bg = p - 40
                        elif 100 <= p <= 107:
                            grid.base_bg = p - 100 + 8
                elif code == "C":
                    # ESC[nC past column 79 wraps to column 0 of the next
                    # row, as in ansilove; it does not clamp.
                    new_col = grid.col + (params[0] if params else 1)
                    if new_col >= TERMINAL_WIDTH:
                        grid.row += 1
                        grid.col = 0
                        if grid.row > grid.max_row_seen:
                            grid.max_row_seen = grid.row
                    else:
                        grid.col = new_col
                elif code == "D":
                    grid.col = max(0, grid.col - (params[0] if params else 1))
                elif code == "A":
                    grid.row = max(0, grid.row - (params[0] if params else 1))
                elif code == "B":
                    grid.row = grid.row + (params[0] if params else 1)
                    if grid.row > grid.max_row_seen:
                        grid.max_row_seen = grid.row
                elif code in ("H", "f"):
                    r = params[0] - 1 if len(params) >= 1 and params[0] else 0
                    c = params[1] - 1 if len(params) >= 2 and params[1] else 0
                    grid.row, grid.col = max(0, r), max(0, min(TERMINAL_WIDTH - 1, c))
                    if grid.row > grid.max_row_seen:
                        grid.max_row_seen = grid.row
                elif code == "s":
                    grid.saved_row, grid.saved_col = grid.row, grid.col
                elif code == "u":
                    grid.row, grid.col = grid.saved_row, grid.saved_col
                # Other codes (J, K, t, h, l) are consumed as no-ops.
                pos = m.end()
                continue
            else:
                # Malformed ESC: emit it as a glyph so it can't eat content
                # or desync the cursor.
                grid.put(ord(_decode_cp437(bytes([b]))))
                pos += 1
                continue
        if b == 0x0D:  # bare \r
            grid.col = 0
            pos += 1
            continue
        # Everything else, low control bytes included, is a CP437 glyph.
        grid.put(ord(_decode_cp437(bytes([b]))))
        pos += 1

    return grid


def canonicalize_cell(codepoint, fg, bg, blink, ice_colors):
    """Map cells that display identically to one (codepoint, fg, bg) triple.

    Empty cells default to (' ', 7, 0) in grid_to_arrays, matching a painted
    default space.

    iCE vs blink: SGR 5 sets the attribute bit that iCE mode reads as bright
    background. With ice_colors and blink, bg |= 8. Otherwise bg is kept and
    blink is dropped, as ansilove does without -i. SGR 100-107 already set
    bg 8-15 directly.
    """
    if ice_colors and blink:
        bg = bg | 8
    return codepoint, fg, bg


def grid_to_arrays(grid):
    # Trim every trailing empty row, as ansilove does. Blank rows inside
    # the content are kept.
    occupied_rows = set(r for (r, c) in grid.cells)
    n_rows = grid.max_row_seen + 1
    while n_rows > 1 and (n_rows - 1) not in occupied_rows:
        n_rows -= 1
    n_cols = TERMINAL_WIDTH
    chars = np.full((n_rows, n_cols), ord(" "), dtype=np.uint32)
    fg_arr = np.full((n_rows, n_cols), 7, dtype=np.uint8)
    bg_arr = np.zeros((n_rows, n_cols), dtype=np.uint8)
    for (r, c), (codepoint, fg, bg) in grid.cells.items():
        if r >= n_rows:
            continue  # trimmed row; guard only
        # Cells are already canonicalized (codepoint, fg, bg); see parse_file.
        chars[r, c] = codepoint
        fg_arr[r, c] = fg
        bg_arr[r, c] = bg
    return chars, fg_arr, bg_arr, n_rows, n_cols


def parse_file(path):
    """Parse one .ans/.asc file into a dict for np.savez. Raises on corrupt files; the caller skips them."""
    raw = Path(path).read_bytes()
    content, sauce = strip_sauce(raw)
    ice_colors = bool(sauce and sauce.get("ice_colors"))

    grid = parse_ans_bytes(content)

    # Resolve blink/iCE now that the file's flag is known.
    canon_cells = {}
    for (r, c), (codepoint, fg, bg, blink) in grid.cells.items():
        canon_cells[(r, c)] = canonicalize_cell(codepoint, fg, bg, blink, ice_colors)
    grid.cells = canon_cells

    chars, fg_arr, bg_arr, n_rows, n_cols = grid_to_arrays(grid)

    return {
        "chars": chars,
        "fg": fg_arr,
        "bg": bg_arr,
        "ice_colors": np.array(ice_colors),
        "n_rows": np.array(n_rows, dtype=np.int32),
        "n_cols": np.array(n_cols, dtype=np.int32),
        "source_path": str(path).encode("utf-8"),
        "sauce_title": (sauce["title"] if sauce else "").encode("utf-8"),
        "sauce_author": (sauce["author"] if sauce else "").encode("utf-8"),
        "sauce_group": (sauce["group"] if sauce else "").encode("utf-8"),
        "sauce_date": (sauce["date"] if sauce else "").encode("utf-8"),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input-dir", default=str(CORPUS_DIR / "data"))
    ap.add_argument("--output-dir", default=str(CORPUS_DIR / "parsed"))
    ap.add_argument("--file", default=None, help="parse a single file instead of a whole directory (debugging)")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    if args.file:
        result = parse_file(args.file)
        out_path = Path(args.output_dir) / (Path(args.file).name + ".npz")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(out_path, **result)
        print(f"parsed {args.file} -> {out_path} ({result['n_rows']}x{result['n_cols']})")
        return

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        p for p in input_dir.rglob("*")
        if p.suffix.lower() in (".ans", ".asc") and p.is_file()
    )
    if args.limit:
        files = files[: args.limit]

    ok, failed = 0, []
    for i, path in enumerate(files):
        rel = path.relative_to(input_dir)
        out_path = output_dir / rel.with_name(rel.name + ".npz")
        try:
            result = parse_file(path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(out_path, **result)
            ok += 1
        except Exception as e:
            failed.append((str(rel), str(e)))
        if (i + 1) % 100 == 0:
            print(f"  ...{i+1}/{len(files)} ({ok} ok, {len(failed)} failed)")

    print(f"\nDone. {ok}/{len(files)} parsed OK, {len(failed)} failed.")
    if failed:
        print("Failures:")
        for rel, err in failed[:20]:
            print(f"  {rel}: {err}")
        if len(failed) > 20:
            print(f"  ...and {len(failed) - 20} more")


if __name__ == "__main__":
    main()
