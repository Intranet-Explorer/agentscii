#!/usr/bin/env python3
"""corpus/parse.py -- parse extracted .ans/.asc files into cell-grid arrays.

Ground truth for every design decision here was checked live against
ansilove (the reference ANSI renderer, `brew install ansilove`), not
assumed from spec reading alone:
  - TAB (0x09) advances the cursor to the next 8-column tab stop and paints
    nothing in between (confirmed: a TAB at column 8 lands content at
    column 16, not column 9).
  - CP437 control-range bytes (0x01-0x08, 0x0B-0x1F excl ESC) render as
    real CP437 glyphs (smileys, hearts, etc.), not as control actions --
    only \\n (0x0A), \\r (0x0D), TAB (0x09), and ESC (0x1B, CSI sequences)
    are treated specially. This is standard "ANSI art" convention: the
    file is raw video-memory-style text, and only a small control subset
    is interpreted.
  - ansilove renders each row at a fixed 80-column width (or a SAUCE/-c
    override), wrapping overflow -- matches the harness's own
    _TERMINAL_WIDTH=80 convention already used in ~/agentscii/harness.py.

Each parsed piece becomes a .npz with:
    chars     : (rows, cols) uint32 array of Unicode codepoints (post CP437
                decode), space (0x20) for untouched/background cells
    fg        : (rows, cols) uint8 array, 0-15 (ANSI palette index)
    bg        : (rows, cols) uint8 array, 0-15
    ice_colors: 0-d bool -- whether iCE color mode is in effect (from SAUCE
                TFlags bit 0, or, if no SAUCE, left False -- see
                canonicalize_cell's docstring for why bg 8-15 without iCE
                is folded to blink instead of guessed)
    n_rows, n_cols : 0-d int32, real content extent (grid is padded to
                the max row actually touched, not a fixed guess)
    source_path, sauce_title, sauce_author, sauce_group, sauce_date : bytes
                (structured metadata, empty bytes if absent)

Canonicalization (the point of this step, not just parsing): two cells
that a real terminal displays IDENTICALLY are collapsed to the same
(char, fg, bg) triple, so training data doesn't treat cosmetically
different-but-visually-identical SGR sequences as different classes. See
canonicalize_cell()'s docstring for the specific equivalences handled.

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
TERMINAL_WIDTH = 80  # matches harness.py's _TERMINAL_WIDTH convention
MAX_ROWS_SAFETY = 20000  # a real pathological/corrupt file could otherwise
                          # produce an unbounded row count via repeated \n;
                          # no real artpack in the archive approaches this.

_CSI_RE = re.compile(rb"\x1b\[([0-9;?]*)([A-Za-z])")
SAUCE_RECORD_LEN = 128
SAUCE_COMMENT_LINE_LEN = 64


def _decode_cp437(raw_bytes):
    """CP437 is a full byte->codepoint mapping (no undefined bytes), so
    this never raises -- every .ans byte has a real glyph."""
    return raw_bytes.decode("cp437")


def strip_sauce(raw):
    """Return (content_bytes, sauce_dict_or_None).

    Two separate things happen here, confirmed live against ansilove
    (not assumed from spec reading): (1) a bare 0x1A (EOF/SUB) byte is a
    HARD STOP for content, always -- ansilove renders nothing at or after
    the first 0x1A in a file, with or without a SAUCE record following it
    (verified: 'ABC' + 0x1A + 'DEF' renders only 'ABC', confirmed via
    direct pixel inspection of the ansilove PNG, zero ink in the DEF
    columns). This matches real MS-DOS EOF convention (0x1A = Ctrl-Z,
    "end of text stream") that predates SAUCE and applies independent of
    it. (2) SAUCE lives in the last 128 bytes of the file, ID field ==
    b'SAUCE00' -- when present, it's parsed for metadata, and its own
    preceding 0x1A (guaranteed by the SAUCE spec) is just the general
    EOF-byte case above, not a special SAUCE-specific rule."""
    # Find SAUCE first (may or may not be present) to extract metadata,
    # but the actual content truncation point is governed by EOF-byte
    # rules below, independent of whether SAUCE parsing succeeds.
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

    # Content ends at the FIRST bare 0x1A anywhere before the SAUCE record
    # (or anywhere in the file if there's no SAUCE) -- this is the real
    # EOF rule, not "the byte right before SAUCE00". Searching from the
    # start (not rfind) matters: a file could in principle have earlier
    # 0x1A bytes than the one immediately preceding SAUCE, and ansilove
    # stops at the FIRST one.
    search_end = idx if idx >= 0 else len(raw)
    eof_pos = raw.find(b"\x1a", 0, search_end)
    if eof_pos < 0:
        # no EOF byte before SAUCE (or no SAUCE at all) -- content is
        # everything up to (but not including) SAUCE, or the whole file
        content_end = search_end
    else:
        content_end = eof_pos

    return raw[:content_end], sauce


class Grid:
    """Sparse cursor-addressable cell grid, mirroring harness.py's cursor
    model for ESC[A/B/C/D/H/f handling, but with IMMEDIATE end-of-line
    wrap, not deferred -- confirmed live against ansilove (not assumed):
    filling column 80 then hitting an explicit \\r\\n produces TWO row
    advances in ansilove (one from the fill-triggered auto-wrap, one from
    the newline), not one. Real test: 80 chars + '\\n' + 'X' renders as 3
    rows in ansilove (row0=the 80 chars, row1=BLANK from the auto-wrap,
    row2=X) -- deferred-wrap (harness.py's convention, and this file's
    own earlier version) would produce only 2 rows, collapsing the
    auto-wrap and the explicit newline into one advance, which does NOT
    match ansilove. Cross-checked against a real archive file (AS-MAXX.ANS)
    that has 80-char lines immediately followed by explicit ESC[A
    (cursor-up) -- consistent with the artist compensating for an
    auto-wrap they knew would happen, not with wrap being deferred.

    harness.py's OWN renderer (used for the live agent pipeline, not this
    training corpus) intentionally still uses deferred wrap -- that
    decision was made for a different reason (avoiding a doubled blank
    row on agent-authored files that always end lines at exactly 80
    cols) and is not changed here; this parser's job is matching
    ansilove, the actual ground truth for a training corpus meant to
    generalize to real archive files, not house-authored ones."""

    def __init__(self):
        self.cells = {}  # (row, col) -> (codepoint, fg, bg, blink)
        self.row, self.col = 0, 0
        self.max_row_seen = 0
        self.base_fg, self.bright_fg, self.base_bg = 7, False, 0
        self.blink = False
        self.saved_row, self.saved_col = 0, 0  # ESC[s / ESC[u -- save/
        # restore cursor position (DEC private mode, ANSI.SYS convention).
        # Found live to be extremely common in real archive files (12221
        # ESC[s + 4551 ESC[u occurrences across a 500-file sample) and,
        # before being handled, caused real row-count divergences of 2-8+
        # rows on files that rely on it for column alignment (repeated
        # save-position, draw one cell, cursor-forward, restore-position,
        # newline, restore again -- a common technique for building up a
        # multi-row logo column by column). No stack: real ANSI.SYS only
        # ever tracks ONE saved position, overwritten by each new ESC[s.

    def put(self, codepoint):
        if self.row > MAX_ROWS_SAFETY:
            raise ValueError(f"row count exceeded safety cap ({MAX_ROWS_SAFETY})")
        fg_idx = (self.base_fg + 8) if self.bright_fg else self.base_fg
        # Store the RAW (pre-iCE-resolution) bg + blink bit separately --
        # do NOT fold blink into bg here. Whether the blink SGR bit means
        # "blinking" or "bright background" depends on the file's SAUCE
        # iCE-colors flag, which isn't known until strip_sauce() runs
        # (before parsing) but conceptually belongs to file-level
        # resolution, not per-cell paint time. Folding at paint time (an
        # earlier version of this code did) double-counts when base_bg is
        # ALREADY 8-15 (via SGR 100-107) and blink is also set. Resolved
        # once, correctly, in canonicalize_cell() after parsing.
        self.cells[(self.row, self.col)] = (codepoint, fg_idx % 16, self.base_bg % 16, self.blink)
        self.col += 1
        if self.col >= TERMINAL_WIDTH:
            # IMMEDIATE wrap (see class docstring) -- advance now, not on
            # the next put()/newline().
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
        # advance to next 8-column tab stop, paint nothing -- confirmed
        # live against ansilove (see module docstring). KNOWN EDGE CASE,
        # not fully resolved: when a TAB (or a chain of TABs) would push
        # the cursor to or past column 80, ansilove's exact behavior
        # diverges from the simple "clamp to col 79" model here in a way
        # not yet fully characterized -- found live via corpus validation
        # (rph-atar.asc: a period placed after 3 tabs near the right
        # margin never renders in ansilove's output at all, and no extra
        # row appears, contradicting both a simple clamp AND a wrap
        # model). Affects a narrow, rare pattern (TAB sequences landing
        # within ~10 columns of the right margin) -- measured impact on
        # the validation sample: 4/2400 cells (0.17%) in 1/200 files
        # (0.5%). Left as a documented known gap for step 1 rather than
        # further reverse-engineering ansilove's TAB internals by trial
        # and error; revisit if a later validation pass shows this
        # pattern at a materially higher rate across a larger sample.
        self.col = min(TERMINAL_WIDTH - 1, ((self.col // 8) + 1) * 8)


def parse_ans_bytes(content, ice_colors_hint=False):
    """Parse raw (post-SAUCE-strip) .ans bytes into a Grid. ice_colors_hint
    comes from the file's own SAUCE record when present -- it changes how
    background-bright is interpreted (see canonicalize_cell)."""
    text_bytes = content.replace(b"\r\n", b"\n")
    # NOTE: deliberately do NOT decode to str yet -- CP437 decoding happens
    # per-glyph inside the loop below (put() receives a codepoint), because
    # ESC sequences must be matched on the RAW bytes (CSI parameter bytes
    # are ASCII digits/semicolons regardless of code page, but decoding
    # the whole file to CP437 first would be wrong if it ever contained a
    # literal 0x1b that wasn't meant as ESC -- doesn't happen in practice,
    # but matching harness.py's own raw-byte CSI regex approach exactly).
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
                # strip a leading '?' (private-mode sequences like
                # ESC[?7h/ESC[?33l -- DECAWM/cursor-visibility toggles,
                # no visible effect on the cell grid, safe to parse the
                # numeric part and then simply not act on codes we don't
                # implement, same as harness.py's "any other CSI final
                # byte is consumed and ignored" rule)
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
                            grid.blink = True  # SGR 5 = blink -- distinct from
                            # bold(1)/bright-fg; only matters for bg brightness
                            # when NOT in iCE color mode (see canonicalize_cell)
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
                    # Confirmed live against ansilove: ESC[nC that would
                    # move the cursor to or past column 80 does NOT clamp
                    # to the last column -- it wraps to the NEXT row at
                    # column 0 (tested n=79..85 from col 1, all identically
                    # landed the following character at row+1, col 0, not
                    # a partial-overflow column or a clamped column 79).
                    # This matches ansilove treating ESC[C like printable
                    # characters for wrap purposes, not like a bounded
                    # cursor clamp. Found live: without this, a real file
                    # (bs-trsp.ans, drawn as ONE giant cursor-forward-only
                    # line with no literal newlines at all) had cells
                    # rendering at the wrong row/col past the first wrap.
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
                # other codes (J, K, t (window title/xterm ops), h/l
                # private-mode toggles with no grid effect): consumed,
                # no-op -- matches harness.py's existing convention.
                pos = m.end()
                continue
            else:
                # a lone/malformed ESC not matching CSI syntax -- treat as
                # a literal CP437 glyph rather than silently vanishing, so
                # a corrupt escape doesn't eat real content or desync the
                # cursor. Real corrupt/truncated files in a 30-year archive
                # do occasionally end mid-escape.
                grid.put(ord(_decode_cp437(bytes([b]))))
                pos += 1
                continue
        if b == 0x0D:  # bare \r (not part of \r\n, already normalized above)
            grid.col = 0
            pos += 1
            continue
        # everything else, INCLUDING low control-range bytes 0x01-0x08 and
        # 0x0B-0x1F (excl the ones handled above), renders as a real CP437
        # glyph -- confirmed live against ansilove, see module docstring.
        grid.put(ord(_decode_cp437(bytes([b]))))
        pos += 1

    return grid


def canonicalize_cell(codepoint, fg, bg, blink, ice_colors):
    """Collapse cells that render IDENTICALLY on screen to the same
    (codepoint, fg, bg) triple, so training data doesn't manufacture
    spurious distinct classes out of cosmetically different SGR paths to
    the same visible result.

    Equivalences handled:
    1. A true empty cell (never explicitly painted) vs. an explicitly
       painted space with fg=7,bg=0 render identically -- both canonicalize
       to (' ', 7, 0). Handled by the caller (fill_grid) defaulting
       untouched cells to this triple, not here.
    2. iCE COLORS vs BLINK, the single most consequential ambiguity in
       real ANSI art: SGR 5 (blink) sets the same hardware attribute bit
       that, under iCE color mode, instead selects BRIGHT BACKGROUND
       (0-15 instead of 0-7 for bg). Without knowing the file's iCE flag,
       "bg=4 + blink" and "bg=12, not blinking" are indistinguishable at
       the byte level -- they're the SAME attribute byte, interpreted two
       different ways by two different terminal modes. bg here is always
       the RAW 0-7 base background (SGR 40-47) OR'd directly to 8-15 if
       the file used SGR 100-107 (xterm bright-bg extension, unambiguous
       either way); `blink` is the separate SGR-5 bit tracked per cell.
         - ice_colors=True and blink: bg gets OR'd with 8 (bright bg)
         - otherwise: bg is used as-is (already correct if 100-107 was
           used directly; if not, it's a genuine low-intensity 0-7
           background and the blink attribute is simply dropped for a
           static image, matching what ansilove itself does without -i).
    """
    if ice_colors and blink:
        bg = bg | 8
    return codepoint, fg, bg


def grid_to_arrays(grid):
    # Trim ALL trailing wholly-empty rows (2026-09-17, found via ansilove
    # validation): confirmed live that ansilove trims every consecutive
    # blank row at the end of a file, not just one -- a real test file
    # (KOR-J.ASC, deliberate multi-line whitespace framing before EOF, 5
    # real trailing blank \r\n's) rendered as 21 rows in ansilove despite
    # this parser's real, correct terminal-semantics count of 26. Checked
    # across 500 real archive files: 61/500 (12%) have 2+ trailing empty
    # rows, so trimming only one (an earlier version of this fix) would
    # still have left a systematic mismatch on a meaningful fraction of
    # the corpus. A piece with deliberate mid-content blank rows keeps
    # them fine -- this only trims from the true end backward, stopping
    # at the first row that has any painted cell.
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
            continue  # a trimmed trailing empty row, if any -- has no
                       # cells anyway per construction, but guard for safety
        # grid.cells here holds POST-canonicalize_cell (codepoint, fg, bg)
        # triples -- blink has already been resolved into bg where
        # applicable (see parse_file).
        chars[r, c] = codepoint
        fg_arr[r, c] = fg
        bg_arr[r, c] = bg
    return chars, fg_arr, bg_arr, n_rows, n_cols


def parse_file(path):
    """Parse one .ans/.asc file end to end. Returns a dict ready for
    np.savez, or raises on unrecoverable structural failure (caller
    catches and logs -- a handful of genuinely corrupt files in a 30-year
    archive is expected and should be skipped, not crash the batch)."""
    raw = Path(path).read_bytes()
    content, sauce = strip_sauce(raw)
    ice_colors = bool(sauce and sauce.get("ice_colors"))

    grid = parse_ans_bytes(content)

    # apply canonicalization now that we know the file's real ice_colors
    # flag (parse_ans_bytes tracked raw blink state per-cell; resolve it
    # here in one pass rather than at paint time -- see Grid.put's
    # docstring comment for why paint-time folding was wrong).
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
        out_path = Path(args.output_dir) / (Path(args.file).stem + ".npz")
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
        out_path = output_dir / rel.with_suffix(".npz")
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
