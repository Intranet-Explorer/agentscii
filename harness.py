#!/usr/bin/env python3
"""
AGENTSCII harness.

Two local LLM agents share one workspace and make ANSI textmode art in the
90s BBS scene tradition, as one collaborative body of work.

Forked from antfarm2's harness (shift loop, loop guard, cross-shift memory,
tool dispatch, SQLite event log). The artist submits and the curator
decides; everything upstream is shared, and joint pieces are the norm.
workspace/STYLE.md is the house style. Accepted pieces sit in
gallery/unpacked/ until the curator ships a numbered pack with a FILE_ID.DIZ.
"""
import base64
import io
import json
import os
import random
import re
import signal
import subprocess
import sqlite3
import hashlib
import time
import sys
import urllib.request
from datetime import date
from pathlib import Path

HOME = Path.home()
PROJECT_DIR = HOME / "agentscii"
WORKSPACE = PROJECT_DIR / "workspace"
GALLERY = WORKSPACE / "gallery"
GALLERY_UNPACKED = GALLERY / "unpacked"
# Curator accepts land here and wait for manual review (review_sheet.py).
# Nothing reaches the public gallery without Tyler approving it.
PENDING = WORKSPACE / "pending"
SUBMISSIONS = WORKSPACE / "submissions"
SCRATCH = WORKSPACE / "scratch"
REJECTED = WORKSPACE / "rejected"
SHELVED = WORKSPACE / "shelved"
REFERENCES = WORKSPACE / "references"
STYLE_DOC = WORKSPACE / "STYLE.md"
DB_PATH = PROJECT_DIR / "state.db"
STOP_FLAG = PROJECT_DIR / "STOP"
OLLAMA_URL = "http://localhost:11434/v1/chat/completions"

_stop_requested = False


def _request_stop(signum=None, frame=None):
    global _stop_requested
    _stop_requested = True
    print(f"\n[harness] Stop requested (signal={signum}). Finishing current turn, then stopping cleanly...")


def stop_requested():
    return _stop_requested or STOP_FLAG.exists()


# claude-opus-5-5 needs Claude Code >= v2.1.280.
# Override with AGENTSCII_OPUS_MODEL.
OPUS_MODEL = os.environ.get("AGENTSCII_OPUS_MODEL", "claude-opus-5-5")

# Blind subject check: off unless AGENTSCII_SUBJECT_CHECK=1.
SUBJECT_CHECK_ENABLED = os.environ.get("AGENTSCII_SUBJECT_CHECK", "0") == "1"

MODEL = "qwen3.8:27b-mlx"  # stock Qwen3.8-27B, MLX build
# Not the abliterated variant, which expects temperature=0 and no system
# prompt. top_k/repeat_penalty/min_p aren't accepted by
# Ollama's OpenAI endpoint and fall through to the Modelfile defaults.
SAMPLING = {"temperature": 0.7, "top_p": 0.80, "presence_penalty": 1.5}
# Thinking is on (the loop reads msg.reasoning), so use Qwen's
# thinking-mode settings. presence_penalty would penalise the repeated keys
# in tool-call JSON. max_tokens caps a runaway thinking turn.
SAMPLING = {"temperature": 0.6, "top_p": 0.95, "presence_penalty": 0.0, "max_tokens": 16384}
# Only the newest KEEP_IMAGES images stay in the request; older ones become
# a stub. Ollama truncates overflowing context silently from the front.
KEEP_IMAGES = 2

REFERENCE_NOTE = (
    "Real reference archives are reachable via bash/curl. Don't guess at URL "
    "patterns or hand-scrape rendered HTML for links — these work, verified: "
    "https://16colo.rs and https://16colo.rs (and "
    "any /group/<name> for a real scene group) list that group's packs as real "
    "pack links you can grep out directly. https://16colo.rs/year/<YYYY> works "
    "the same way for browsing by year. A pack page's /raw/ path "
    "(https://16colo.rs/pack/<name>/raw/<FILE>.ANS) gets the real CP437/ANSI "
    "bytes — the plain pack-page link returns an HTML viewer, not raw bytes. "
    "https://www.textfiles.com/artscene/ is an older, simpler archive, browsable "
    "the same direct way. There's a short primer at "
    "references/what_is_ansi_art.txt, and the house style spec is at STYLE.md — "
    "read that before your first piece."
)

WORKSPACE_NOTE = (
    "The shared workspace at ~/agentscii/workspace/ has a fixed structure: "
    "scratch/ is shared, unrestricted WIP space — yours AND your collaborator's. "
    "Read what's there before starting something new; if a piece is promising but "
    "unfinished, extend it, add a pass, remix it — you don't need permission and "
    "you don't need to have started it yourself. Real ANSI packs are full of "
    "pieces credited 'Joint' for exactly this reason. submissions/ is where a "
    "finished piece waits for the curator's review — only the artist seat moves "
    "things there, via submit_piece, and only for work that's actually finished. "
    "gallery/unpacked/ holds pieces the curator has accepted but that haven't "
    "shipped in a numbered pack release yet — that's the curator's call, via "
    "release_pack. gallery/packNN/ holds shipped releases, each with a "
    "FILE_ID.DIZ crediting every contributor — that's the actual unit of finished "
    "work here, not any single piece in isolation. rejected/ holds pieces sent "
    "back with a .critique.txt sidecar — nothing is deleted; it's yours to revise "
    "and resubmit. references/ holds real ANSI study material."
)

STYLE_DOC_NOTE = (
    "There's a house style spec at STYLE.md — house conventions AND the actual "
    "build sequence (block-in, light-source shading, detail texture, background "
    "texture, frame, verify against a reference) are both in there. Required "
    "reading before your first figurative piece."
)

AGENTS = {
    "artist": {
        "model": MODEL,
        "role": "artist",
        "soul": (
            "You're one of two agents in AGENTSCII: produce real ANSI textmode "
            "art (the 90s BBS artscene aesthetic) worth keeping, as a real body of work — "
            "not two agents quietly working past each other. Your seat is 'artist': you "
            "call submit_piece when something's ready. That's the only hard boundary "
            "between you and your collaborator — everything upstream is shared. "
            "workspace/: scratch/ holds CURRENT work only (closed subjects are archived "
            "automatically) plus shared helper modules — extend or remix what's there, "
            "no permission needed; submissions/ holds a finished piece "
            "awaiting curator review (artist seat only, via submit_piece); "
            "gallery/unpacked/ holds accepted pieces not yet shipped; gallery/packNN/ "
            "holds shipped releases with a FILE_ID.DIZ crediting everyone — the real unit "
            "of finished work, not any single piece; rejected/ holds pieces with a "
            ".critique.txt — nothing deleted, revise and resubmit; references/ holds real "
            "ANSI study material. Draw directly with the canvas_* tools: "
            "canvas_new(slug, width, height) starts a persistent canvas (saved to disk "
            "across calls/shifts); canvas_fill_px/canvas_circle_px draw flat shapes and "
            "genuinely round circles in half-block pixel space (each cell is 2 pixels "
            "tall, zero aspect correction needed); canvas_shade applies real "
            "density-dither shading (█▓▒░ falloff, not flat cutoffs) from one light "
            "direction; canvas_text places letters; canvas_stamp places a real "
            "find_patches result by its patch_id; canvas_preview shows progress; "
            "canvas_save writes the finished .ans. Pieces are drawn with the canvas_* "
            "tools. Bash and Python are for fetching references, inspecting files, and "
            "utilities — not for generating pieces. find_patches(description) searches "
            "the real archive corpus by technique/visual similarity, returning a rendered "
            "image AND real cell data (RLE text + patch_id) per hit — study it, or hand "
            "patch_id to canvas_stamp directly. Before shading any form, call "
            "find_patches to see how real artists shaded something similar, then "
            "reproduce that technique with canvas_shade and canvas_fill_px. Use "
            "canvas_stamp only for texture regions (sky, ground, background fields), "
            "never for your subject — stamping several patches from different pieces "
            "produces collage, not a composition. Real archives are reachable via "
            "bash/curl — 16colo.rs/group/<name> and /year/<YYYY> list packs; a pack's "
            "/raw/ path gets real bytes. references/study/ has curated examples on disk "
            "already. METHOD.md is the house "
            "method — written by the artist that made gallery/pack55 by placing cells "
            "individually, and it REPLACES the old region-pass sequence in "
            "METHODOLOGY.md (now marked superseded). Read METHOD.md before your first "
            "figurative or ambition-tier piece; STYLE.md still has house conventions. A human (the operator) directs this project and leaves "
            "either of you direction via your inbox. This is directed, quality-focused "
            "work, not idle equilibrium. "
            "Read workspace/REVIEWS.md: the operator's verdicts, the only judgement that decides publishing. Each entry is his own words on a finished piece -- reads as subject, well made, publish -- and 'reads' and 'well made' are separate questions. Curator accepts now go to workspace/pending/ and wait for his review; nothing reaches the public gallery without it. Draw lessons from the pattern across batches, not from one review, and do not rewrite METHOD.md or STYLE.md off a single verdict. "
            "Check workspace/CATALOG.md before starting a new subject — it lists every subject ever attempted, with status. Repeating a past subject is allowed ONLY as a deliberate revisit: say so in the note, and improve on the archived version. "
            "If nothing's in flight, start a new subject "
            "via random_direction, or revise a piece rejected in the LAST 5 SHIFTS with "
            "its critique in mind. Do NOT revive older work without direction from the "
            "operator: four shifts were spent reviving an abandoned piece purely because "
            "it sat in scratch/. Closed subjects are archived automatically; the reasons "
            "are in workspace/archive/README.md. Don't submit unfinished "
            "work to pad activity. The harness database is ~/agentscii/state.db, the only one; query it read-only "
            "with: sqlite3 -readonly ~/agentscii/state.db \"<SQL>\". Speak in the first person, always. 'user'-labeled "
            "messages are automated harness pings and inbox deliveries, not a person "
            "waiting on you in real time. Call end_shift when done acting for this shift."
        ),
    },
    "curator": {
        "model": MODEL,
        "role": "curator",
        "soul": (
            "You're one of two agents in AGENTSCII: produce real ANSI textmode "
            "art (the 90s BBS artscene aesthetic) worth keeping, as a real body of work — "
            "not two agents quietly working past each other. Your seat is 'curator': you "
            "decide on submissions (curate_piece) and ship pack releases (release_pack). "
            "That's the only hard boundary between you and your collaborator — everything "
            "upstream is shared, and you're a full contributor there too; jump into "
            "scratch/ and add a pass to anything your collaborator started whenever you "
            "want. workspace/: scratch/ holds CURRENT work only (closed subjects are "
            "archived automatically) plus shared helper modules — extend or remix what's "
            "there, no permission needed; submissions/ holds a finished "
            "piece awaiting curator review (artist seat only, via submit_piece); "
            "gallery/unpacked/ holds accepted pieces not yet shipped; gallery/packNN/ "
            "holds shipped releases with a FILE_ID.DIZ crediting everyone — the real unit "
            "of finished work, not any single piece; rejected/ holds pieces with a "
            ".critique.txt — nothing deleted, revise and resubmit; references/ holds real "
            "ANSI study material. Draw directly with the canvas_* tools: "
            "canvas_new(slug, width, height) starts a persistent canvas (saved to disk "
            "across calls/shifts); canvas_fill_px/canvas_circle_px draw flat shapes and "
            "genuinely round circles in half-block pixel space (each cell is 2 pixels "
            "tall, zero aspect correction needed); canvas_shade applies real "
            "density-dither shading (█▓▒░ falloff, not flat cutoffs) from one light "
            "direction; canvas_text places letters; canvas_stamp places a real "
            "find_patches result by its patch_id; canvas_preview shows progress; "
            "canvas_save writes the finished .ans. Pieces are drawn with the canvas_* "
            "tools. Bash and Python are for fetching references, inspecting files, and "
            "utilities — not for generating pieces. find_patches(description) searches "
            "the real archive corpus by technique/visual similarity, returning a rendered "
            "image AND real cell data (RLE text + patch_id) per hit — study it, or hand "
            "patch_id to canvas_stamp directly. Use canvas_stamp only for texture regions "
            "(sky, ground, background fields), never for a piece's subject — stamping "
            "several patches from different pieces produces collage, not a composition. "
            "Real archives are reachable via bash/curl — 16colo.rs/group/<name> and "
            "/year/<YYYY> list packs; a pack's /raw/ path gets real bytes. "
            "references/study/ has curated examples on disk already. METHOD.md is the house "
            "method — written by the artist that made gallery/pack55 by placing cells "
            "individually, and it REPLACES the old region-pass sequence in "
            "METHODOLOGY.md (now marked superseded). Read METHOD.md before your first "
            "figurative or ambition-tier piece; STYLE.md still has house conventions. A "
            "human (the operator) directs this project and leaves either of you direction via "
            "your inbox. "
            "Read workspace/REVIEWS.md: the operator's verdicts, the only judgement that decides publishing. Each entry is his own words on a finished piece -- reads as subject, well made, publish -- and 'reads' and 'well made' are separate questions. Curator accepts now go to workspace/pending/ and wait for his review; nothing reaches the public gallery without it. Draw lessons from the pattern across batches, not from one review, and do not rewrite METHOD.md or STYLE.md off a single verdict. "
            "Ground every judgment in something real: look at actual "
            "reference pieces before accepting or rejecting, not memory or vibes, and "
            "check against STYLE.md. On curate_piece: accept moves it to "
            "workspace/pending/ for the operator's review; reject moves it to "
            "rejected/ with a specific critique — "
            "name what's actually wrong compared to real pieces in the tradition, not "
            "just 'needs work'. A rejection isn't a failure state; a gallery containing "
            "everything submitted isn't curated at all. But don't reject reflexively "
            "either. Use release_pack when gallery/unpacked/ has a real handful of good "
            "work, not on a fixed schedule — pieces arrive there only after the operator "
            "approves them, so an empty gallery/unpacked/ means his review is pending, "
            "not that nothing was accepted. If submissions/ is empty, that's legitimate: "
            "nothing to report — go study references, add a pass to a piece rejected in the "
            "LAST 5 SHIFTS, or leave a specific idea via message_agent. Do NOT revive "
            "older work without operator direction; closed subjects are archived, with "
            "reasons in workspace/archive/README.md. The harness database is ~/agentscii/state.db, the only one; query it read-only "
            "with: sqlite3 -readonly ~/agentscii/state.db \"<SQL>\". Speak in the first person, always. 'user'-labeled "
            "messages are automated harness pings, not a person waiting on you in real "
            "time. Call end_shift when done acting for this shift."
        ),
    },
}

MAX_TOOL_CALLS_PER_SHIFT = 40
# Creation needs more room than review. A shift that hits the cap
# fragments a piece and leaves interrupted-work debris.
MAX_TOOL_CALLS_BY_ROLE = {"artist": 100, "curator": 40}
BASH_TIMEOUT = 60

MAX_REVISIONS_PER_SUBJECT = 8  # then ship, shelve, or revert to the best version
# Counts submitted versions, not Opus reviews, so gate-blocked submissions
# still count. Enforced in submit_piece.

SHIFT_WALL_CLOCK_CAP_S = 90 * 60  # 90 minutes
# The stall detector only catches identical call+result pairs. This
# catches a shift making novel calls that never converge.

_VERSION_RE = re.compile(r"(?:\.[vV]|-v|_v)(\d+)$")

FIGURATIVE_WORDS = ("face", "eye", "watch", "sentinel", "cyborg", "scan",
                     "mind", "portrait", "figure", "warden", "vigil",
                     "traveler", "procession", "ember", "guardian", "demon",
                     "cyclops", "totem", "mantis", "lantern", "oracle",
                     "coghead", "gargoyle", "wraith", "golem", "knight",
                     "colossus", "sphinx", "phantom", "silhouette")
# Approximate by design; new subjects will slip through. Add words as gaps
# turn up. opus_subject_check() is the real backstop.

_FIGURATIVE_WORDS_RE = re.compile(
    r"(?<![a-zA-Z])(?:" + "|".join(re.escape(w) for w in FIGURATIVE_WORDS) + r")"
)
# Lookbehind for a letter, not \b: \b treats '_' as a word char and never
# matches "_watcher". Still rejects "ember" in "remember" and allows stems
# like "watchers".


def _reads_figurative(path):
    """True if the filename or the piece's visible text (title card, sig
    block) contains a FIGURATIVE_WORD. Matched on SGR-stripped text."""
    name_lower = Path(path).stem.lower()
    if _FIGURATIVE_WORDS_RE.search(name_lower):
        return True
    try:
        raw = Path(path).read_bytes()
        text = _decode_ans_bytes(raw)
        idx = text.find("\x1aSAUCE00")
        if idx >= 0:
            text = text[:idx]
        visible = _SGR_RE.sub("", text).lower()
    except Exception:
        return False
    return bool(_FIGURATIVE_WORDS_RE.search(visible))


def _subject_fingerprint(path):
    """Content-based subject identity: a coarse 8x8 occupancy+hue hash of the
    rendered grid, so renaming a file can't reset its revision count."""
    try:
        grid, _ = _parse_ans_grid(path)
    except Exception:
        return None
    if not grid:
        return None
    rows = [r for (r, c) in grid]
    cols = [c for (r, c) in grid]
    r0, r1 = min(rows), max(rows) + 1
    c0, c1 = min(cols), max(cols) + 1
    rh = max(1, (r1 - r0) / 8.0)
    cw = max(1, (c1 - c0) / 8.0)
    buckets = [[0, 0] for _ in range(64)]
    for (r, c), (ch, fg, bg) in grid.items():
        if ch == " " and bg == 0:
            continue
        br = min(7, int((r - r0) / rh))
        bc = min(7, int((c - c0) / cw))
        b = buckets[br * 8 + bc]
        b[0] += 1
        b[1] |= 1 << ((bg if (ch == " " and bg != 0) else fg) & 7)
    peak = max((b[0] for b in buckets), default=0) or 1
    bits = "".join(
        ("1" if b[0] * 4 >= peak else "0") + f"{b[1]:02x}" for b in buckets
    )
    return hashlib.sha1(bits.encode()).hexdigest()[:16]


# Retired subjects: a new piece on any of these is blocked outright.
RETIRED_SUBJECT_WORDS = ("eye", "orb", "sphere", "watcher", "iris", "pupil")
RETIRED_UNTIL_ACCEPTS = 3


def _retired_subject_block(conn, slug, title=""):
    """None when allowed, else the refusal text."""
    hay = f"{slug} {title}".lower()
    hit = next((w for w in RETIRED_SUBJECT_WORDS if w in hay), None)
    if hit is None:
        return None
    n = conn.execute(
        "SELECT COUNT(DISTINCT slug) FROM subjects WHERE status='accepted'"
    ).fetchone()[0]
    if n >= RETIRED_UNTIL_ACCEPTS:
        return None
    return (
        f"subject retired — '{hit}' is part of the eye/orb/sphere family, "
        f"which has had 60+ versions since Sep 18 and is shelved. "
        f"{n} of {RETIRED_UNTIL_ACCEPTS} required different subjects have "
        f"been accepted so far. Draw something else: a scene, a creature "
        f"with limbs, a logo with lettering — several distinct forms at "
        f"different scales, not a single centered round object."
    )


def core_slug(name_noext):
    """Strip a trailing version suffix (.v3, -v4, _v12): '_orb.v5' -> '_orb'."""
    s = name_noext
    while True:
        m = _VERSION_RE.search(s)
        if not m:
            return s
        s = s[: m.start()]


def _extract_version(name_noext):
    """Return the trailing version number (.v3 -> 3) or 0 if the filename
    has no version suffix (a bare first submission)."""
    m = _VERSION_RE.search(name_noext)
    return int(m.group(1)) if m else 0


def _get_subject(conn, slug):
    row = conn.execute(
        "SELECT slug, status, opened_at, last_version, last_path, "
        "abandon_reason, updated_at, pinned_script_path, pinned_version "
        "FROM subjects WHERE slug=?",
        (slug,),
    ).fetchone()
    if row is None:
        return None
    keys = ["slug", "status", "opened_at", "last_version", "last_path",
            "abandon_reason", "updated_at", "pinned_script_path", "pinned_version"]
    return dict(zip(keys, row))


def _open_subjects(conn):
    # 'rejected' still counts as open: rejection means revise, not close.
    rows = conn.execute(
        "SELECT slug, last_version, opened_at FROM subjects "
        "WHERE status IN ('open','rejected') ORDER BY opened_at"
    ).fetchall()
    return [{"slug": r[0], "last_version": r[1], "opened_at": r[2]} for r in rows]


def _compute_piece_metrics(path):
    """Per-version quality metrics for the pinned-best regression gate.

    half_block_pct/shade_char_pct are subject-only (non-background cells),
    matching corpus/technique_index.py. The *_whole_canvas fields are
    diagnostic only. Returns a dict, or None if the file can't be parsed.
    """
    try:
        grid, total_lines = _parse_ans_grid(path)
    except Exception:
        return None

    # ▀▄ only, matching corpus/technique_index.py's HALF_BLOCK_CP so scores
    # compare to the corpus. Not _HALF_BLOCK_CHARS, which includes █.
    half_block_chars = set("\u2580\u2584")  # ▀▄
    shade_chars = set("\u2593\u2592\u2591")  # ▓▒░

    total_ct = len(grid)  # whole canvas, background included -- secondary only
    half_ct_whole = 0
    shade_ct_whole = 0

    subject_visible_colors = set()
    subject_ct = 0
    half_ct_subj = 0
    shade_ct_subj = 0
    rows, cols = [], []
    subject_coords = []
    for (r, c), (ch, fg, bg) in grid.items():
        if ch in half_block_chars:
            half_ct_whole += 1
        if ch in shade_chars:
            shade_ct_whole += 1
        if ch == " " and bg == 0:
            continue
        subject_ct += 1
        rows.append(r)
        cols.append(c)
        subject_coords.append((r, c))
        if ch in half_block_chars:
            half_ct_subj += 1
        if ch in shade_chars:
            shade_ct_subj += 1
        visible_idx = bg if (ch == " " and bg != 0) else fg
        subject_visible_colors.add(visible_idx)

    if total_ct == 0:
        return {
            "half_block_pct": 0.0, "shade_char_pct": 0.0,
            "half_block_pct_whole_canvas": 0.0, "shade_char_pct_whole_canvas": 0.0,
            "distinct_colors_in_subject": 0,
            "subject_bbox_rows": 0, "subject_bbox_cols": 0,
            "subject_cell_count": 0,
            "disconnected_masses": 0, "ink_canvas_share": 0.0,
        }

    # Counts spatially disconnected masses, not forms: a composite where
    # everything touches the ground scores 1. Soft signal only, not in the
    # regression tripwire. 4-connected flood fill, O(cells).
    _MIN_REGION = 12  # smaller blobs are detail/noise, not separate forms
    subject_set = set(subject_coords)
    seen = set()
    regions = 0
    for start in subject_set:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        size = 0
        while stack:
            r, c = stack.pop()
            size += 1
            for nb in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nb in subject_set and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        if size >= _MIN_REGION:
            regions += 1

    canvas_rows = max(r for r, c in grid) + 1
    canvas_cols = max(c for r, c in grid) + 1
    canvas_cells = canvas_rows * canvas_cols
    # Ink density, not bbox: every framed piece spans the full canvas, so a
    # bbox share reads 100% for all of them.
    ink_share = 100.0 * subject_ct / canvas_cells if canvas_cells else 0.0

    return {
        "half_block_pct": 100.0 * half_ct_subj / subject_ct if subject_ct else 0.0,
        "shade_char_pct": 100.0 * shade_ct_subj / subject_ct if subject_ct else 0.0,
        "half_block_pct_whole_canvas": 100.0 * half_ct_whole / total_ct,
        "shade_char_pct_whole_canvas": 100.0 * shade_ct_whole / total_ct,
        "distinct_colors_in_subject": len(subject_visible_colors),
        "subject_bbox_rows": (max(rows) - min(rows) + 1) if rows else 0,
        "subject_bbox_cols": (max(cols) - min(cols) + 1) if cols else 0,
        "subject_cell_count": subject_ct,
        "disconnected_masses": regions,
        "ink_canvas_share": ink_share,
    }


def _record_piece_metrics(conn, slug, version, path):
    """Compute and store metrics for one version. Called on every submission."""
    metrics = _compute_piece_metrics(path)
    if metrics is None:
        return None
    conn.execute(
        "INSERT INTO piece_metrics (slug, version, path, half_block_pct, "
        "shade_char_pct, half_block_pct_whole_canvas, shade_char_pct_whole_canvas, "
        "distinct_colors_in_subject, subject_bbox_rows, "
        "subject_bbox_cols, subject_cell_count, timestamp) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (slug, version, str(path), metrics["half_block_pct"],
         metrics["shade_char_pct"], metrics["half_block_pct_whole_canvas"],
         metrics["shade_char_pct_whole_canvas"], metrics["distinct_colors_in_subject"],
         metrics["subject_bbox_rows"], metrics["subject_bbox_cols"],
         metrics["subject_cell_count"], time.time()),
    )
    conn.commit()
    return metrics


def _get_best_metrics(conn, slug):
    """Pinned-best metrics for a slug, or the best so far by composite score
    if nothing is pinned. The stored 'path' may no longer exist on disk."""
    subj = _get_subject(conn, slug)
    if subj and subj.get("pinned_version") is not None:
        row = conn.execute(
            "SELECT half_block_pct, shade_char_pct, distinct_colors_in_subject, "
            "subject_bbox_rows, subject_bbox_cols, subject_cell_count, version, path "
            "FROM piece_metrics WHERE slug=? AND version=? ORDER BY id DESC LIMIT 1",
            (slug, subj["pinned_version"]),
        ).fetchone()
        if row:
            keys = ["half_block_pct", "shade_char_pct", "distinct_colors_in_subject",
                    "subject_bbox_rows", "subject_bbox_cols", "subject_cell_count", "version", "path"]
            return dict(zip(keys, row))
    # no explicit pin yet -- fall back to the best-scoring version seen so far
    rows = conn.execute(
        "SELECT half_block_pct, shade_char_pct, distinct_colors_in_subject, "
        "subject_bbox_rows, subject_bbox_cols, subject_cell_count, version, path "
        "FROM piece_metrics WHERE slug=?",
        (slug,),
    ).fetchall()
    if not rows:
        return None
    keys = ["half_block_pct", "shade_char_pct", "distinct_colors_in_subject",
            "subject_bbox_rows", "subject_bbox_cols", "subject_cell_count", "version", "path"]
    dicts = [dict(zip(keys, r)) for r in rows]
    dicts.sort(key=lambda d: -(d["half_block_pct"] + d["shade_char_pct"] + d["distinct_colors_in_subject"]))
    return dicts[0]


def _touch_subject(conn, slug, version, path, status="open"):
    """Create or update a subject row."""
    existing = _get_subject(conn, slug)
    now = time.time()
    fp = _subject_fingerprint(path) if path else None
    if existing is None:
        conn.execute(
            "INSERT INTO subjects (slug, status, opened_at, last_version, "
            "last_path, updated_at, fingerprint) VALUES (?,?,?,?,?,?,?)",
            (slug, status, now, version, str(path), now, fp),
        )
    else:
        new_version = max(existing["last_version"], version)
        conn.execute(
            "UPDATE subjects SET status=?, last_version=?, last_path=?, "
            "updated_at=?, fingerprint=COALESCE(?, fingerprint) WHERE slug=?",
            (status, new_version, str(path), now, fp, slug),
        )
    conn.commit()
    # Every subject close routes through here: archive scratch, rebuild the
    # catalog.
    if status in ("accepted", "abandoned", "shelved", "rejected"):
        if status != "rejected":
            _archive_subject_scratch(slug)
        try:
            _rebuild_catalog()
        except Exception:
            pass  # the catalog must never break a curation decision

def check_piece_gates(path, retrieval_queries=None):
    """The project's submission requirements, in one place.

    Anything that writes pieces must go through this or the gates don't
    apply. submit_piece checks retrieval by shift_id; an out-of-harness
    runner passes the queries it made. Returns (ok, report).
    """
    problems = []
    if not retrieval_queries:
        problems.append(
            "RETRIEVAL: no find_patches call. Query the technique or form "
            "being rendered ('shaded knuckles and finger contours', "
            "'directional strokes following a cylinder'), not the subject "
            "name. 850k patches of real artists doing exactly this."
        )
    flat = _flat_region_check(path)
    if flat:
        problems.append("FLAT-REGION GATE: " + flat[:300])
    m = _compute_piece_metrics(path)
    report = _fmt_metrics(m) if m else "(metrics unavailable)"
    if m:
        report += f", glyph-carried {_glyph_carried_pct(path):.1f}%"
    if retrieval_queries:
        report += f"\nretrieval: {len(retrieval_queries)} quer(y/ies): " + \
                  "; ".join(retrieval_queries[:4])
    return (not problems), report + (
        "\n\nBLOCKED:\n- " + "\n- ".join(problems) if problems else "")


def _glyph_carried_pct(path):
    """Share of inked cells whose form is carried by a glyph rather than by
    background colour. Not a ratio to maximise (see STYLE.md): pure noise
    scores 100%. Use it to spot a piece gone mostly flat-fill."""
    try:
        g, _ = _parse_ans_grid(path)
    except Exception:
        return 0.0
    bg = glyph = 0
    for (r, c), (ch, fg, bgc) in g.items():
        if ch == " " and bgc == 0:
            continue
        if ch == " ":
            bg += 1
        else:
            glyph += 1
    return 100.0 * glyph / (bg + glyph) if (bg + glyph) else 0.0


def _fmt_metrics(m):
    """One metric line with both denominators (subject-only and whole-canvas),
    labeled."""
    return (
        f"half_block {m['half_block_pct']:.1f}% subject-only / "
        f"{m['half_block_pct_whole_canvas']:.1f}% whole-canvas, "
        f"shade-of-ink {m['shade_char_pct']:.1f}% subject-only / "
        f"{m['shade_char_pct_whole_canvas']:.1f}% whole-canvas, "
        f"colors {m['distinct_colors_in_subject']}, "
        f"disconnected masses {m['disconnected_masses']}, "
        f"ink {m['ink_canvas_share']:.0f}% of canvas"
    )


def _rebuild_catalog():
    """Regenerate workspace/CATALOG.md: every subject ever attempted.

    Built from the directories and the subjects table, never by hand. Full
    rewrite on every subject close.
    """
    import collections
    areas = [
        ("in-review", SUBMISSIONS),
        ("shipped", WORKSPACE / "gallery"),
        ("accepted-pending-review", PENDING),
        ("accepted-unpacked", GALLERY_UNPACKED),
        ("rejected", REJECTED),
        ("shelved", SHELVED),
        ("archived", WORKSPACE / "archive"),
    ]
    seen = collections.OrderedDict()
    for status, root in areas:
        if not root.exists():
            continue
        for f in sorted(root.rglob("*.ans")):
            slug = core_slug(f.stem)
            if slug in seen:
                continue
            try:
                m = _compute_piece_metrics(f)
                mt = time.strftime("%Y-%m-%d", time.localtime(f.stat().st_mtime))
            except Exception:
                m, mt = None, "?"
            seen[slug] = {
                "status": status, "date": mt, "path": f,
                "hb": m["half_block_pct"] if m else 0.0,
                "sh": m["shade_char_pct"] if m else 0.0,
            }
    db = sqlite3.connect(DB_PATH)
    try:
        for slug, st in db.execute("SELECT slug, status FROM subjects"):
            if slug in seen:
                # Location wins over DB status: a piece can be in gallery/ while its
                # subject row still reads 'rejected' from an earlier version.
                if (seen[slug]["status"] not in ("shipped", "accepted-unpacked")
                        and st in ("abandoned", "shelved", "rejected")):
                    seen[slug]["status"] = st
            else:
                seen[slug] = {"status": st, "date": "?", "path": None,
                              "hb": 0.0, "sh": 0.0}
    finally:
        db.close()

    lines = [
        "# CATALOG — every subject ever attempted",
        "",
        "Auto-generated on every subject close. Do not hand-edit.",
        "",
        "**Check this before starting a new subject.** Repeating a past",
        "subject is allowed ONLY as a deliberate revisit: say so in the",
        "note, and improve on the archived version. Starting a subject",
        "that is already here without saying so is thrashing, not work.",
        "",
        "| subject | date | status | half_block | shade | note |",
        "|---|---|---|---|---|---|",
    ]
    notes = {
        "_departure": "168-row ambition-tier scroll; abandoned, scope before capability",
        "_orb": "eye/orb family; v59 is the house bar. Subject RETIRED",
        "_watcher": "eye family, 60+ versions; re-slug dodged the revision cap. RETIRED",
        "_watcher_final": "same content as _watcher.v7 under a new name. RETIRED",
        "_keeper": "first piece drawn with the fixed canvas primitives",
        "_wasteland": "dying-sun dunes atmospheric study",
    }
    for slug, d in sorted(seen.items()):
        lines.append(
            f"| `{slug}` | {d['date']} | {d['status']} | "
            f"{d['hb']:.1f}% | {d['sh']:.1f}% | {notes.get(slug, '')} |"
        )
    lines.append("")
    (WORKSPACE / "CATALOG.md").write_text("\n".join(lines))
    return len(seen)


def _archive_subject_scratch(slug):
    """Move a closed subject's scratch files to workspace/archive/.

    Scratch holds current work only. Moves, never deletes. Shared helper
    modules stay put.
    """
    keep = {"canvas.py", "figure_common.py", "halfblock.py", "curve_common.py"}
    dest = WORKSPACE / "archive" / "scratch-2026-09"
    moved = []
    try:
        dest.mkdir(parents=True, exist_ok=True)
        for f in sorted(SCRATCH.iterdir()):
            if not f.is_file() or f.name in keep:
                continue
            if core_slug(f.name.split(".")[0]) != slug:
                continue
            target = dest / f.name
            if target.exists():
                target = dest / f"{f.stem}.dup{int(time.time())}{f.suffix}"
            f.rename(target)
            moved.append(f.name)
    except Exception:
        pass  # hygiene must never break a curation decision
    return moved


def _check_regression_tripwire(conn, n_back=3):
    """After each accept, score it against the last three accepts on
    half_block, shade-of-ink and distinct colors. Two consecutive accepts
    below the reference bar halt submissions.

    disconnected_masses is excluded: a composed scene scores 1. Returns None
    when fine, else the halt message.
    """
    rows = conn.execute(
        "SELECT slug, version, half_block_pct, shade_char_pct, "
        "distinct_colors_in_subject FROM piece_metrics "
        "WHERE accepted=1 ORDER BY id DESC LIMIT ?", (n_back + 1,)
    ).fetchall()
    if len(rows) < n_back + 1:
        return None
    newest, prior = rows[0], rows[1:]
    ref = {
        i: sorted(p[i] for p in prior)[len(prior) // 2]
        for i in (2, 3, 4)
    }
    below = [
        label for i, label in ((2, "half_block"), (3, "shade-of-ink"),
                               (4, "distinct colors"))
        if newest[i] < ref[i]
    ]
    if len(below) < 2:
        return None
    strikes = conn.execute(
        "SELECT COUNT(*) FROM tripwire_strikes WHERE cleared=0"
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO tripwire_strikes (slug, version, detail, ts, cleared) "
        "VALUES (?,?,?,?,0)",
        (newest[0], newest[1], ", ".join(below), time.time()),
    )
    conn.commit()
    if strikes + 1 < 2:
        return None
    return (
        f"REGRESSION TRIPWIRE: two consecutive accepted pieces fell below "
        f"the recent-accept bar. Latest ('{newest[0]}' v{newest[1]}) is "
        f"below on: {', '.join(below)}. Reference is the median of the "
        f"last {n_back} accepts: half_block {ref[2]:.1f}%, shade "
        f"{ref[3]:.1f}%, colors {ref[4]}. House bar {HOUSE_BAR['name']}: "
        f"{HOUSE_BAR['half_block']}% / {HOUSE_BAR['shade']}%. Submissions "
        f"are HALTED — report to the human rather than continuing."
    )


def _tripwire_halted(conn):
    """True when an uncleared two-strike halt is in force.

    Off unless AGENTSCII_METRIC_HALT=1, since these metrics don't track
    quality. Strikes are still recorded and logged."""
    if os.environ.get("AGENTSCII_METRIC_HALT") != "1":
        return False
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM tripwire_strikes WHERE cleared=0"
        ).fetchone()[0] >= 2
    except sqlite3.OperationalError:
        return False


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command in a sandbox. Working directory defaults to ~/agentscii/workspace. You can read the repo and use the network; writes are allowed only inside workspace/ and temp dirs. Credential stores and the claude CLI are blocked.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file's contents.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write (overwrite) a file's contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "message_agent",
            "description": "Send a direct message to your collaborator. They will see it at the start of their next shift.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_handle",
            "description": (
                "Choose (or change) your artist handle — a real name distinct from your "
                "functional seat, the way every real BBS-scene artist had one. Shows up in "
                "the dashboard and in signature blocks/credits from now on."
            ),
            "parameters": {
                "type": "object",
                "properties": {"handle": {"type": "string"}},
                "required": ["handle"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_piece",
            "description": (
                "Artist seat only. Submit a finished piece from scratch/ for curator review. "
                "The harness moves the file from scratch/ into submissions/ and logs the "
                "submission. Only call this for work that's actually finished."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the finished piece, relative to workspace/ (normally under scratch/)."},
                    "note": {"type": "string", "description": "Intent, technique, references drawn on, anything the curator should know."},
                    "contributors": {"type": "string", "description": "Comma-separated handle(s) of everyone who worked on this piece, including yourself. Required if this was a joint piece."},
                },
                "required": ["path", "note"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "curate_piece",
            "description": (
                "Curator seat only. Decide on a piece currently in submissions/. "
                "accept moves it to gallery/unpacked/, pending the next pack release; "
                "reject moves it to rejected/ with your critique saved alongside it as "
                "a .critique.txt sidecar. IMPORTANT: if your critique claims a visual "
                "feature (face, eye, brow, jaw, profile, anatomy, figure, silhouette, "
                "expression), describe what you actually SEE in the preview_piece "
                "render, not what the generator code intended — an automatic blind "
                "second opinion (same model, no access to your critique) runs on any "
                "such claim and hard-blocks the accept if it flatly contradicts you. "
                "This caught a real prior mistake: a piece critiqued as 'two facing "
                "profile heads with brow/jaw shading' that was actually three flat "
                "solid-color blocks with no facial structure at all."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the piece in submissions/, relative to workspace/."},
                    "decision": {"type": "string", "enum": ["accept", "reject"]},
                    "critique": {"type": "string", "description": "Specific, concrete critique — required either way: praise specifics on accept, actionable issues on reject."},
                },
                "required": ["path", "decision", "critique"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "abandon_subject",
            "description": (
                "Artist seat only. Explicitly abandon an open subject (a "
                "piece slug that's been submitted but not yet accepted) "
                "with a written reason. Required before starting a third "
                "concurrent subject — the open-subject cap is 2. This is "
                "not a punishment, it's an honest record: some subjects "
                "genuinely don't work out, and saying so plainly (with a "
                "real reason) is better than letting them sit open forever "
                "or quietly starting something else under a fresh name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "The core subject slug to abandon (filename with any .vN/-vN/_vN suffix stripped), e.g. '_orb'."},
                    "reason": {"type": "string", "description": "Why this subject is being abandoned, not just resubmitted again."},
                },
                "required": ["slug", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "random_direction",
            "description": (
                "Roll a random creative prompt: a subject/theme, a technique "
                "constraint (a specific canvas.py/figure_common.py/curve_common.py "
                "primitive or approach to build around), and a palette lean. Use "
                "this when you want a real, chance-driven starting point instead "
                "of defaulting to whatever idiom is cheapest to produce (the "
                "catalog has leaned heavily procedural/abstract — this exists to "
                "break that gravity with genuine variety, including figurative/"
                "character/scene prompts). You are NOT required to take the roll "
                "literally — accept it, remix it, or reject it and explain why in "
                "your own reasoning. It's a seed for randomness in what the house "
                "works on together, not a mandate. Call it with no arguments."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_patches",
            "description": (
                "Search the real 16colo.rs archive corpus (86k real scene "
                "pieces, not synthetic) for small real technique references, and see them "
                "rendered as an actual image — CLIP visual-embedding retrieval, so a "
                "free-text description like 'shaded sphere warm light' or 'metallic chrome "
                "edge' finds patches that actually look like that, not just ones whose SAUCE "
                "title happens to contain a matching word. Use this to see how real artists "
                "actually built the half-block/shade technique you're trying for, instead of "
                "guessing at it from scratch — this is real corpus study material, the same "
                "purpose as workspace/references/study/ but searchable by description instead "
                "of needing an exact filename. Results are small 40x16-cell windows, not full "
                "pieces — they show technique up close, not composition."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "What you're looking for, in plain language — subject, technique, mood, whatever's relevant."},
                    "n": {"type": "integer", "description": "How many patches to return, rendered side by side. Default 3, max 6."},
                    "shade_min": {"type": "number", "description": "Optional: only patches with at least this much shade-glyph usage (0-100)."},
                },
                "required": ["description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_piece",
            "description": (
                "Run a full structural diagnostic on an .ans/.asc file in one call: "
                "encoding check, control-byte hygiene, SGR token validity, row-width "
                "check, standalone-reset check, dead/blank-region detection (3+ "
                "consecutive empty rows — the signature of a real rendering bug like "
                "a panel that silently rendered black), BACKGROUND TEXTURE DENSITY "
                "(flags a piece whose negative space reads mostly flat/unvaried — "
                "Methodology Pass 5, see workspace/METHODOLOGY.md), and FRAME/BORDER "
                "PRESENCE (flags a piece with no border/title-card treatment at all — "
                "Methodology Pass 6). Use this instead of writing a fresh bash+Python "
                "diagnostic script each time — it's the same checks every piece needs, "
                "already built. Pair with preview_piece: inspect_piece tells you WHERE "
                "a structural problem is, preview_piece lets you SEE it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the .ans/.asc file, relative to workspace/."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_new",
            "description": (
                "Start a new persistent canvas to draw on directly with tool calls — "
                "no Python required. One canvas = one piece; it's saved to disk under "
                "workspace/canvases/ and stays there across tool calls, across shifts, "
                "even across a harness restart, exactly like a scratch/ file. Pixel "
                "space is half-block (each cell is 2 pixels tall via ▀), so circles/fills "
                "drawn with canvas_circle_px/canvas_fill_px come out genuinely round with "
                "zero aspect math — the same technique halfblock.py's HalfBlockCanvas "
                "uses, just as direct tool calls instead of code you write and run."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Short lowercase name for this canvas, e.g. 'orb_v2' — lowercase letters/digits/-/_ only."},
                    "width": {"type": "integer", "description": "Width in cells. House standard is 80."},
                    "height": {"type": "integer", "description": "Height in cells. Free — a tall piece is fine."},
                    "bg": {"type": "integer", "description": "Background color index 0-15. Default 0 (black)."},
                },
                "required": ["slug", "width", "height"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_fill_px",
            "description": (
                "Fill a rectangle on a canvas with a flat color, in PIXEL space (x: "
                "0..width-1, y: 0..height*2-1 — twice the cell height, since each cell "
                "is 2 pixels tall). Good for silhouette block-in: lay down flat shapes "
                "first, verify with canvas_preview, THEN shade with canvas_shade."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to draw on (from canvas_new)."},
                    "x": {"type": "integer", "description": "Left edge, pixel space."},
                    "y": {"type": "integer", "description": "Top edge, pixel space."},
                    "w": {"type": "integer", "description": "Width in pixels."},
                    "h": {"type": "integer", "description": "Height in pixels."},
                    "color": {"type": "integer", "description": "Palette color index 0-15."},
                },
                "required": ["slug", "x", "y", "w", "h", "color"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_circle_px",
            "description": (
                "Fill a circle on a canvas, in PIXEL space, with zero aspect correction "
                "needed — pixel space is ~square (width x height*2), so this comes out "
                "genuinely round at the call site. Use for eyes, craniums, orbs, faces, "
                "any curved/circular shape at any scale — the exact case whole-cell "
                "circle formulas squash or alias into flat rings."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to draw on."},
                    "cx": {"type": "number", "description": "Center x, pixel space."},
                    "cy": {"type": "number", "description": "Center y, pixel space."},
                    "r": {"type": "number", "description": "Radius in pixels."},
                    "color": {"type": "integer", "description": "Palette color index 0-15."},
                },
                "required": ["slug", "cx", "cy", "r", "color"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_shade",
            "description": (
                "Apply real density-dither shading (the genuine scene ramp/dither "
                "technique — █▓▒░ carrying the brightness falloff between two colors, "
                "not a flat color-to-color cutoff) to a SHAPE, not a rectangle. "
                "Defaults to whatever you drew last with canvas_fill_px/canvas_circle_px "
                "on this canvas — shading a circle stays clipped to the circle's round "
                "edge, it will not paint a rectangle over it. Pass region explicitly for "
                "more control: {\"type\":\"rect\",\"x0\",\"y0\",\"x1\",\"y1\"} (pixel space), "
                "{\"type\":\"circle\",\"cx\",\"cy\",\"r\"} (pixel space), or "
                "{\"type\":\"color\",\"color\":N} to shade every pixel currently that color, "
                "wherever it is on the canvas. Use it as a pass over an already "
                "block-in'd shape, same as STYLE.md's shading pass — for a lit sphere/"
                "orb/eye specifically, canvas_sphere_px does fill+shade in one call."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to draw on."},
                    "from_color": {"type": "integer", "description": "Color index nearest the light (bright end)."},
                    "to_color": {"type": "integer", "description": "Color index farthest from the light (dark end)."},
                    "light_direction": {
                        "type": "string",
                        "enum": ["top", "bottom", "left", "right", "top-left", "top-right", "bottom-left", "bottom-right"],
                        "description": "Which edge of the region the light comes from — keep this the SAME across a whole piece's shading calls for one coherent light source.",
                    },
                    "region": {
                        "type": "object",
                        "description": "Optional — omit to shade whatever you drew last. Otherwise {\"type\":\"rect\"|\"circle\"|\"color\", ...} as described above.",
                    },
                },
                "required": ["slug", "from_color", "to_color", "light_direction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_sphere_px",
            "description": (
                "One call: a lit sphere — fills a circle AND shades it with a real "
                "point-light falloff from (light_x, light_y), so the gradient follows "
                "the sphere's actual curvature (radial from the light point, not a "
                "linear wash) and the edge stays genuinely round. Spheres, eyes, heads, "
                "and orbs are most of what gets drawn — use this instead of composing "
                "canvas_circle_px + canvas_shade by hand for the common case of a "
                "simple lit ball."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to draw on."},
                    "cx": {"type": "number", "description": "Center x, pixel space."},
                    "cy": {"type": "number", "description": "Center y, pixel space."},
                    "r": {"type": "number", "description": "Radius in pixels."},
                    "color": {"type": "integer", "description": "Lit-side color index 0-15."},
                    "light_x": {"type": "number", "description": "Light source x, pixel space — where the brightest point should be."},
                    "light_y": {"type": "number", "description": "Light source y, pixel space."},
                    "shadow_color": {"type": "integer", "description": "Dark-side color index 0-15. Defaults to black (0) — pass the dim end of a hue family (e.g. from STYLE.md's palette) for a colored sphere instead of a grayscale one."},
                },
                "required": ["slug", "cx", "cy", "r", "color", "light_x", "light_y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_slab_px",
            "description": (
                "One call: a lit BOX, not a flat fill. Flat-sided forms — torsos, "
                "limbs, buildings, panels, frames, lettering blocks — have no "
                "curvature, so each face takes a base brightness from its "
                "orientation vs the light, then a gradient ACROSS the face from "
                "its lit edge to its far edge, with light-facing edges getting a "
                "brighter rim. Pass side='left'/'right' with side_w to draw a "
                "second visible face (the classic two-face monolith/box), which "
                "is what makes a slab read as a solid volume instead of a "
                "rectangle with noise in it. Use this for ANY flat-sided form "
                "instead of canvas_fill_px + canvas_shade."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to draw on."},
                    "x": {"type": "integer", "description": "Left edge, pixel space."},
                    "y": {"type": "integer", "description": "Top edge, pixel space."},
                    "w": {"type": "integer", "description": "Width in pixels."},
                    "h": {"type": "integer", "description": "Height in pixels."},
                    "color": {"type": "integer", "description": "Body color index 0-15."},
                    "light_direction": {"type": "string", "description": "One of top, bottom, left, right, top-left, top-right, bottom-left, bottom-right. Default top-left."},
                    "shadow_color": {"type": "integer", "description": "Dark-side color index 0-15. Defaults to black (0)."},
                    "hi_color": {"type": "integer", "description": "Lit-face color index 0-15 — pass the bright end of the same hue family for a real lit face."},
                    "side": {"type": "string", "description": "'left' or 'right' to draw a second visible face of the box."},
                    "side_w": {"type": "integer", "description": "Width of that second face, in pixels."},
                },
                "required": ["slug", "x", "y", "w", "h", "color"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_capsule_px",
            "description": (
                "One call: a lit capsule — a rectangle with rounded ends, shaded "
                "as a CYLINDER (the normal curves across the short axis and is "
                "constant along the length), so it reads as a round limb rather "
                "than a flat bar. This is the most common figure element: arms, "
                "legs, necks, fingers, pipes, tubes, cables. Draw from (ax,ay) to "
                "(bx,by) with radius r — the axis can run at any angle."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to draw on."},
                    "ax": {"type": "number", "description": "Axis start x, pixel space."},
                    "ay": {"type": "number", "description": "Axis start y, pixel space."},
                    "bx": {"type": "number", "description": "Axis end x, pixel space."},
                    "by": {"type": "number", "description": "Axis end y, pixel space."},
                    "r": {"type": "number", "description": "Radius in pixels (half the limb's thickness)."},
                    "color": {"type": "integer", "description": "Body color index 0-15."},
                    "light_direction": {"type": "string", "description": "One of top, bottom, left, right, top-left, top-right, bottom-left, bottom-right. Default top-left."},
                    "shadow_color": {"type": "integer", "description": "Dark-side color index 0-15. Defaults to black (0)."},
                    "hi_color": {"type": "integer", "description": "Highlight color index 0-15. Defaults to 15 (bright white)."},
                },
                "required": ["slug", "ax", "ay", "bx", "by", "r", "color"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_metrics",
            "description": (
                "Measure the CURRENT canvas with the same function the gate and "
                "the submit report use — half_block %, shade-of-ink %, distinct "
                "colors, separate forms (connected subject regions), and ink "
                "share of canvas. Detectors of absence, not targets. Use this "
                "instead of computing your own numbers with a script: "
                "self-computed metrics have come out ~3x off the real value. "
                "'separate forms' is the signal that distinguishes a real "
                "composition from one centered blob."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to measure."},
                },
                "required": ["slug"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_crop",
            "description": (
                "MAGNIFIED view of a small CELL region — the zoom. Returns a big "
                "render of just those cells plus a per-cell dump of glyph, fg and "
                "bg. This is how you see your own work at the scale craft lives "
                "at: place a few cells, crop them, look, adjust. canvas_preview "
                "shows the whole canvas at a size where a wrong cell is invisible; "
                "this shows 12x10 cells big enough to judge. Use it constantly "
                "while doing per-cell work, and before deciding a region is done."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to crop."},
                    "x": {"type": "integer", "description": "Left CELL column."},
                    "y": {"type": "integer", "description": "Top CELL row."},
                    "w": {"type": "integer", "description": "Width in cells (keep small, 8-16)."},
                    "h": {"type": "integer", "description": "Height in cells (keep small, 6-12)."},
                    "scale": {"type": "integer", "description": "Magnification, default 6."},
                },
                "required": ["slug", "x", "y", "w", "h"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_self_check",
            "description": (
                "Run the REVIEWER'S OWN two cheapest tests on yourself, mid-build, "
                "for free. Returns (1) a GLYPHS-ONLY render — every cell forced to "
                "one colour, so only glyph density remains; (2) a COLOUR-ONLY "
                "render — every glyph replaced by a solid block, so only colour "
                "remains; (3) per-row ink density, which flags near-uniform rows. "
                "The two rejections that have killed pieces here are literally "
                "these tests: 'remove the color and nothing survives' (colour-only "
                "still reads = colour is carrying it, glyphs are decoration) and "
                "'strip the glyphs and you lose nothing'. Run this BEFORE you "
                "submit and act on what it shows."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to check."},
                },
                "required": ["slug"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_wordmark",
            "description": (
                "Draw text as large 5x7 block letters — a real logo/title, not a "
                "one-glyph-per-cell label (that's canvas_text). Use scale=2 or higher "
                "for legible text. Returns the pixel width used so a follow-up call "
                "can be centered."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to draw on."},
                    "x": {"type": "integer", "description": "Starting x, pixel space."},
                    "y": {"type": "integer", "description": "Starting y, pixel space."},
                    "text": {"type": "string", "description": "Text to draw — A-Z, 0-9, space, and basic punctuation."},
                    "fg": {"type": "integer", "description": "Color index 0-15."},
                    "scale": {"type": "integer", "description": "Size multiplier. Default 2 (scale=1 renders too small to read clearly)."},
                },
                "required": ["slug", "x", "y", "text", "fg"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_mirror",
            "description": (
                "Mirror the canvas's authored half onto the other half — draw content "
                "in the left half (axis='v', the common case for symmetric creatures/"
                "faces/totems) or top half (axis='h'), then call this once to complete "
                "the symmetric figure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to draw on."},
                    "axis": {"type": "string", "enum": ["v", "h"], "description": "'v' mirrors left half to right (vertical split line). 'h' mirrors top half to bottom."},
                },
                "required": ["slug"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_strand_shade",
            "description": (
                "Directional stroke texture for fur, hair, grain — many short strokes "
                "in a consistent direction, cycling through 2-4 colors so adjacent "
                "strokes read as distinct marks instead of blurring into a flat mass. "
                "Run this AFTER the base shape/shading is in place, as a texture pass "
                "on top."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to draw on."},
                    "region": {
                        "type": "array", "items": {"type": "integer"}, "minItems": 4, "maxItems": 4,
                        "description": "[x0, y0, x1, y1] in CELL space — where strokes can start.",
                    },
                    "direction": {
                        "type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2,
                        "description": "[dx, dy] stroke direction, e.g. [0,1] combed straight down, [1,1] diagonal.",
                    },
                    "colors": {
                        "type": "array", "items": {"type": "integer"},
                        "description": "2-4 color indices strokes cycle through.",
                    },
                    "n_strands": {"type": "integer", "description": "How many strokes. Default 40."},
                    "length": {"type": "integer", "description": "Stroke length in cells. Default 6."},
                },
                "required": ["slug", "region", "direction", "colors"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_text",
            "description": (
                "Place literal characters on a canvas starting at cell (x, y), one per "
                "cell, left to right — for sig blocks, small labels, inline title text. "
                "Not a large blocky wordmark font (that's scratch/canvas.py's "
                "block_letters(), still available if a piece wants a big logo)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to draw on."},
                    "x": {"type": "integer", "description": "Starting column, cell space."},
                    "y": {"type": "integer", "description": "Row, cell space."},
                    "text": {"type": "string", "description": "The characters to place."},
                    "fg": {"type": "integer", "description": "Foreground color index 0-15."},
                    "bg": {"type": "integer", "description": "Background color index 0-15."},
                },
                "required": ["slug", "x", "y", "text", "fg", "bg"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_cells",
            "description": (
                "The per-cell tool: write chosen glyphs into chosen cells. Each item is "
                "[x, y, char, fg, bg] in CELL coordinates; char is one CP437 character "
                "(e.g. '\u2580' '\u2584' '\u258c' '\u2590' '\u2591' '\u2592' '\u2593' '\u2588', "
                "letters, punctuation); fg and bg are colour indices 0-15. Later items "
                "win; up to 400 cells per call. Look at the result with canvas_crop."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to draw on."},
                    "cells": {
                        "type": "array",
                        "description": "List of [x, y, char, fg, bg].",
                        "items": {"type": "array", "items": {}},
                    },
                },
                "required": ["slug", "cells"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_stamp",
            "description": (
                "Place a real patch retrieved via find_patches directly onto a canvas "
                "at cell (x, y) — its actual cell grid (chars/fg/bg), not a description "
                "of it. Use the patch_id find_patches returns alongside each hit. Good "
                "for borrowing a real texture/technique wholesale as a starting point, "
                "then editing on top of it with other canvas_* calls."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to draw on."},
                    "patch_id": {"type": "string", "description": "patch_id from a find_patches result."},
                    "x": {"type": "integer", "description": "Left column to place the patch at, cell space."},
                    "y": {"type": "integer", "description": "Top row to place the patch at, cell space."},
                },
                "required": ["slug", "patch_id", "x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_preview",
            "description": (
                "Render a canvas as an actual image and see it — same as preview_piece, "
                "but for an in-progress canvas that hasn't been saved to a file yet. "
                "Use this after each drawing pass to verify it before the next one, "
                "exactly the same habit as previewing a .ans WIP."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to preview."},
                    "offset": {"type": "integer", "description": "Row to start rendering from (0-indexed)."},
                    "rows": {"type": "integer", "description": "How many rows to render. Default 200."},
                },
                "required": ["slug"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "canvas_save",
            "description": (
                "Write a canvas out as a real, finished .ans file (adds the house "
                "signature block, hygiene-normal cp437 encoding) — the same file "
                "submit_piece expects. The canvas itself is NOT deleted; you can keep "
                "drawing on it and canvas_save again to overwrite, e.g. for a v2."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Canvas to save."},
                    "path": {"type": "string", "description": "Output path, relative to workspace/, e.g. 'scratch/myslug.ans'."},
                    "title": {"type": "string", "description": "Piece title for the signature block."},
                    "handles": {"type": "string", "description": "Contributor handle(s) for the signature block, e.g. 'raze' or 'raze,hollis'."},
                },
                "required": ["slug", "path", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "preview_piece",
            "description": (
                "Render an .ans/.asc file as an actual image and see it — real colors, "
                "real block/box-drawing glyphs, real composition — instead of inferring "
                "them from raw SGR escape codes in text. Use this on your own WIP before "
                "deciding it's finished, and on anything you're reviewing as curator. "
                "For long/scrolling pieces, use offset+rows to page through the whole "
                "thing panel by panel — don't just look at the top."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the .ans/.asc file, relative to workspace/."},
                    "offset": {"type": "integer", "description": "Row to start rendering from (0-indexed). Use this to page through pieces taller than one preview."},
                    "rows": {"type": "integer", "description": "How many rows to render, starting at offset. Default 120, max 200 (larger images cost more to process)."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_to_reference",
            "description": (
                "Render YOUR piece and a REAL reference file side by side as one "
                "image, so you can actually see the gap instead of judging your "
                "own work from memory of what technique you intended to use. "
                "Built directly in response to a real, caught failure: an artist "
                "shift submitted a piece with a note claiming it was 'built on "
                "capsule()/joint_dot() lit-tube primitives' when the code never "
                "called either, and separately judged its own flat-banded render "
                "'genuinely good and submission-ready' after previewing it alone. "
                "Self-assessment in isolation is unreliable — a side-by-side with "
                "a real reference is not. Use this on any figurative/shaded piece "
                "before submit_piece, and use it AS a curator reviewing a "
                "submission, picking whichever reference in references/study/ is "
                "closest in subject/technique to what you're checking."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "piece_path": {"type": "string", "description": "Path to your .ans/.asc file, relative to workspace/."},
                    "reference_path": {"type": "string", "description": "Path to a real reference file, relative to workspace/ (normally under references/study/)."},
                    "offset": {"type": "integer", "description": "Row to start rendering both from (0-indexed). Default 0."},
                    "rows": {"type": "integer", "description": "How many rows of each to render. Default 60, max 90."},
                },
                "required": ["piece_path", "reference_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "release_pack",
            "description": (
                "Curator seat only. Bundle everything currently in gallery/unpacked/ into "
                "the next numbered gallery/packNN/ release, with a generated FILE_ID.DIZ "
                "crediting every contributor. Fails if unpacked/ is empty. This is the real "
                "ship moment — use it when there's a genuine handful of good work waiting, "
                "not on autopilot."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pack_note": {"type": "string", "description": "A short note on this release — what it is, what it represents, anything worth saying about the batch as a whole."},
                },
                "required": ["pack_note"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "end_shift",
            "description": "End your shift and hand off to your collaborator. Call this when you're done acting for now.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {"type": "string", "description": "Short note on what you did this shift."},
                    "had_pending_peer_message": {
                        "type": "boolean",
                        "description": "True if your collaborator had left you a message at the start of this shift.",
                    },
                    "replied_to_peer": {
                        "type": "boolean",
                        "description": "True if you replied/responded to your collaborator's message this shift. False if you saw it and chose not to. If had_pending_peer_message is false, set this false too.",
                    },
                    "continue_same_agent": {
                        "type": "boolean",
                        "description": "True if you have genuine unfinished momentum right now and want another shift immediately instead of handing off. Capped by the harness; ignored if you're not actually making progress.",
                    },
                },
                "required": ["note", "had_pending_peer_message", "replied_to_peer"],
            },
        },
    },
]


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent TEXT NOT NULL,
        shift_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT,
        reasoning TEXT,
        tool_name TEXT,
        tool_args TEXT,
        tool_call_id TEXT,
        timestamp REAL NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent TEXT NOT NULL,
        started_at REAL NOT NULL,
        ended_at REAL,
        note TEXT,
        had_pending_peer_message INTEGER,
        replied_to_peer INTEGER
    )""")
    # last_reasoning carries an in-progress diagnosis into the next shift on a
    # forced end. Guarded for state.db files that predate the column.
    try:
        conn.execute("ALTER TABLE shifts ADD COLUMN last_reasoning TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.execute("""CREATE TABLE IF NOT EXISTS agent_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_agent TEXT NOT NULL,
        to_agent TEXT NOT NULL,
        text TEXT NOT NULL,
        timestamp REAL NOT NULL,
        delivered INTEGER DEFAULT 0
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS human_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        to_agent TEXT NOT NULL,
        text TEXT NOT NULL,
        timestamp REAL NOT NULL,
        delivered INTEGER DEFAULT 0
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS curation_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shift_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        path TEXT NOT NULL,
        dest_path TEXT,
        note TEXT,
        timestamp REAL NOT NULL
    )""")
    # Per-shift tool counts, one row per (shift, tool). Derivable from events,
    # but this avoids re-aggregating and survives pruning.
    conn.execute("""CREATE TABLE IF NOT EXISTS shift_tool_summary (
        shift_id INTEGER NOT NULL,
        tool_name TEXT NOT NULL,
        call_count INTEGER NOT NULL,
        PRIMARY KEY (shift_id, tool_name)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS agent_identity (
        seat TEXT PRIMARY KEY,
        handle TEXT NOT NULL,
        timestamp REAL NOT NULL
    )""")
    # subjects: one row per piece identity (core_slug) through accept/reject.
    # Enforces revision-over-novelty (a rejected piece returns as the same slug
    # at a higher version) and the cap on open subjects.
    conn.execute("""CREATE TABLE IF NOT EXISTS subjects (
        slug TEXT PRIMARY KEY,
        status TEXT NOT NULL DEFAULT 'open',
        opened_at REAL NOT NULL,
        last_version INTEGER NOT NULL DEFAULT 0,
        last_path TEXT,
        abandon_reason TEXT,
        updated_at REAL
    )""")
    try:
        conn.execute("ALTER TABLE subjects ADD COLUMN pinned_script_path TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
    try:
        conn.execute("ALTER TABLE subjects ADD COLUMN pinned_version INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        # Content identity, so a rename can't reset the revision count.
        conn.execute("ALTER TABLE subjects ADD COLUMN fingerprint TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        # Artist of record. The seat that submits is not always the seat that
        # drew the piece.
        conn.execute("ALTER TABLE subjects ADD COLUMN contributor TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE piece_metrics ADD COLUMN accepted INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    conn.execute("""CREATE TABLE IF NOT EXISTS tripwire_strikes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT, version INTEGER, detail TEXT,
        ts REAL, cleared INTEGER DEFAULT 0
    )""")
    # piece_metrics: per-version metrics recorded on every submit, so a
    # revision that regresses against the pinned best can be blocked.
    conn.execute("""CREATE TABLE IF NOT EXISTS piece_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT NOT NULL,
        version INTEGER NOT NULL,
        path TEXT NOT NULL,
        half_block_pct REAL,
        shade_char_pct REAL,
        distinct_colors_in_subject INTEGER,
        subject_bbox_rows INTEGER,
        subject_bbox_cols INTEGER,
        subject_cell_count INTEGER,
        timestamp REAL NOT NULL
    )""")
    try:
        conn.execute("ALTER TABLE piece_metrics ADD COLUMN half_block_pct_whole_canvas REAL")
    except sqlite3.OperationalError:
        pass  # column already exists
    try:
        conn.execute("ALTER TABLE piece_metrics ADD COLUMN shade_char_pct_whole_canvas REAL")
    except sqlite3.OperationalError:
        pass
    # opus_reviews was first created ad hoc; this makes a fresh DB complete.
    conn.execute("""CREATE TABLE IF NOT EXISTS opus_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        piece_slug TEXT NOT NULL,
        path TEXT NOT NULL,
        qwen_decision TEXT,
        qwen_critique TEXT,
        opus_verdict TEXT,
        opus_reasoning TEXT,
        opus_cost_usd REAL,
        opus_error TEXT,
        timestamp REAL NOT NULL
    )""")
    conn.commit()
    return conn


def log_event(conn, agent, shift_id, role, content=None, reasoning=None, tool_name=None, tool_args=None, tool_call_id=None):
    conn.execute(
        "INSERT INTO events (agent, shift_id, role, content, reasoning, tool_name, tool_args, tool_call_id, timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
        (agent, shift_id, role, content, reasoning, tool_name, tool_args, tool_call_id, time.time()),
    )
    conn.commit()


def _record_shift_tool_summary(conn, shift_id):
    """Aggregate this shift's tool calls from `events` into shift_tool_summary.

    Adds synthetic rows 'write_file:.py' and 'bash:.py_write' (heredoc or
    open(..., 'w') into a .py path), since agents write .py files both ways.
    Called once at shift end."""
    rows = conn.execute(
        "SELECT tool_name, tool_args FROM events WHERE shift_id=? AND role='assistant' AND tool_name IS NOT NULL",
        (shift_id,),
    ).fetchall()
    counts = {}
    py_writes = 0
    bash_py_writes = 0
    py_write_re = re.compile(r"\.py['\"]?\s*(,\s*['\"]w)|>\s*[^\s]*\.py\b|write_text\([^)]*\.py")
    for tool_name, tool_args in rows:
        counts[tool_name] = counts.get(tool_name, 0) + 1
        if tool_name == "write_file" and tool_args:
            try:
                path = json.loads(tool_args).get("path", "")
            except Exception:
                path = ""
            if path.endswith(".py"):
                py_writes += 1
        elif tool_name == "bash" and tool_args:
            try:
                command = json.loads(tool_args).get("command", "")
            except Exception:
                command = ""
            if py_write_re.search(command):
                bash_py_writes += 1
    if py_writes:
        counts["write_file:.py"] = py_writes
    if bash_py_writes:
        counts["bash:.py_write"] = bash_py_writes
    conn.executemany(
        "INSERT OR REPLACE INTO shift_tool_summary (shift_id, tool_name, call_count) VALUES (?,?,?)",
        [(shift_id, name, n) for name, n in counts.items()],
    )
    conn.commit()


def get_handle(conn, seat):
    row = conn.execute("SELECT handle FROM agent_identity WHERE seat=?", (seat,)).fetchone()
    return row[0] if row else None


def _prune_old_images(messages, keep=KEEP_IMAGES):
    """Copy of messages with all but the newest `keep` images stubbed out."""
    seen, out = 0, []
    for m in reversed(messages):
        c = m.get("content")
        if isinstance(c, list) and any(p.get("type") == "image_url" for p in c if isinstance(p, dict)):
            parts = []
            for p in c:
                if isinstance(p, dict) and p.get("type") == "image_url":
                    if seen < keep:
                        parts.append(p)
                    else:
                        parts.append({"type": "text", "text": "[older image removed to save context; re-render if you need it]"})
                    seen += 1
                else:
                    parts.append(p)
            m = {**m, "content": parts}
        out.append(m)
    return list(reversed(out))


def call_ollama(model, messages, tools):
    payload = json.dumps({
        "model": model,
        "messages": _prune_old_images(messages),
        "tools": tools,
        **SAMPLING,
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=900) as resp:
        out = json.loads(resp.read())
    # Log context use. prompt_tokens stuck at a flat ceiling means Ollama is
    # truncating: raise OLLAMA_CONTEXT_LENGTH.
    u = out.get("usage") or {}
    if u:
        print(f"[ollama] prompt_tokens={u.get('prompt_tokens')} "
              f"completion_tokens={u.get('completion_tokens')}", flush=True)
    return out


def unload_model(model):
    payload = json.dumps({"model": model, "keep_alive": 0, "prompt": ""}).encode()
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/generate", data=payload,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        urllib.request.urlopen(req, timeout=30).read()
    except Exception as e:
        print(f"[warn] failed to unload {model}: {e}")


# ---- ANSI -> PNG rendering ----------------------------------------------
# Lets the agents see their work through the model's vision input. Same
# 16-color palette and SGR parsing as agentscii-dashboard's renderer.

_ANSI_PALETTE = [
    "#000000", "#aa0000", "#00aa00", "#aa5500",
    "#0000aa", "#aa00aa", "#00aaaa", "#aaaaaa",
    "#555555", "#ff5555", "#55ff55", "#ffff55",
    "#5555ff", "#ff55ff", "#55ffff", "#ffffff",
]
_SGR_RE = re.compile(r"\x1b\[([0-9;]*)m")
_CSI_RE = re.compile(r"\x1b\[([0-9;]*)([A-Za-z])")
_FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
_CELL_W, _CELL_H = 9, 18  # pixel size per character cell at the render font size
_FONT_SIZE = 16
_TERMINAL_WIDTH = 80  # classic-scene canvas width; long lines wrap


def _decode_ans_bytes(raw):
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp437", errors="replace")


def render_ans_to_png_b64(path, offset=0, max_rows=120, redact_title_rows=False):
    """Render an .ans/.asc file to a base64 PNG for vision input.

    offset/max_rows page through a long piece. redact_title_rows blanks rows
    that read as title/credit text, so a blind check can't read the answer
    off the image."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None, "(error: Pillow not installed — pip install Pillow)"

    try:
        raw = Path(path).read_bytes()
    except Exception as e:
        return None, f"(error reading file: {e})"

    text = _decode_ans_bytes(raw).replace("\r\n", "\n").replace("\r", "\n")

    # Cursor-addressable grid: scene .ANS files often draw a base layer, then
    # move the cursor back up (ESC[A) to add detail. Later writes to a cell
    # overwrite earlier ones, as in a real terminal.
    grid = {}
    row, col = 0, 0
    max_row_seen = 0
    base_fg, bright_fg, base_bg = 7, False, 0
    pos = 0
    n = len(text)
    pending_wrap = False  # deferred wrap, like a real terminal:
                          # filling the last column doesn't advance the row until the
                          # next char. Otherwise an 80-char line followed by \n gets a
                          # spurious blank row.

    def put(ch):
        nonlocal col, row, max_row_seen, pending_wrap
        if pending_wrap:
            row += 1
            col = 0
            pending_wrap = False
            if row > max_row_seen:
                max_row_seen = row
        fg_idx = (base_fg + 8) if bright_fg else base_fg
        grid[(row, col)] = (ch, fg_idx % 16, base_bg % 16)
        col += 1
        if col >= _TERMINAL_WIDTH:
            # last column: defer the wrap
            col = _TERMINAL_WIDTH - 1
            pending_wrap = True

    while pos < n:
        ch = text[pos]
        if ch == "\n":
            if pending_wrap:
                # The line filled the last column; this newline is its terminator,
                # so consume the pending wrap instead of advancing twice.
                pending_wrap = False
            else:
                row += 1
                col = 0
                if row > max_row_seen:
                    max_row_seen = row
            pos += 1
            continue
        m = _CSI_RE.match(text, pos)
        if m:
            param_str, code = m.group(1), m.group(2)
            params = [int(c) for c in param_str.split(";") if c != ""]
            if code == "m":
                for p in (params or [0]):
                    if p == 0:
                        base_fg, bright_fg, base_bg = 7, False, 0
                    elif p == 1:
                        bright_fg = True
                    elif p == 22:
                        bright_fg = False
                    elif p == 39:
                        base_fg, bright_fg = 7, False
                    elif p == 49:
                        base_bg = 0
                    elif 30 <= p <= 37:
                        base_fg = p - 30
                    elif 90 <= p <= 97:
                        base_fg, bright_fg = p - 90, True
                    elif 40 <= p <= 47:
                        base_bg = p - 40
                    elif 100 <= p <= 107:
                        base_bg = p - 100 + 8
            elif code == "C":
                col = min(_TERMINAL_WIDTH - 1, col + (params[0] if params else 1))
                pending_wrap = False
            elif code == "D":
                col = max(0, col - (params[0] if params else 1))
                pending_wrap = False
            elif code == "A":
                row = max(0, row - (params[0] if params else 1))
                pending_wrap = False
            elif code == "B":
                row = row + (params[0] if params else 1)
                pending_wrap = False
                if row > max_row_seen:
                    max_row_seen = row
            elif code in ("H", "f"):
                # ESC[row;colH — 1-indexed absolute position
                r = params[0] - 1 if len(params) >= 1 and params[0] else 0
                c = params[1] - 1 if len(params) >= 2 and params[1] else 0
                row, col = max(0, r), max(0, min(_TERMINAL_WIDTH - 1, c))
                pending_wrap = False
                if row > max_row_seen:
                    max_row_seen = row
            # any other CSI final byte (K, J, etc.) is consumed and ignored.
            pos = m.end()
            continue
        put(ch)
        pos += 1

    total_lines = max_row_seen + 1
    offset = max(0, min(offset, total_lines))
    end_row = min(total_lines, offset + max_rows)
    truncated = end_row < total_lines

    rows = []
    for r in range(offset, end_row):
        line_cells = []
        for c in range(_TERMINAL_WIDTH):
            cell = grid.get((r, c))
            line_cells.append(cell if cell is not None else (" ", 7, 0))
        # trim blank trailing cells so a mostly-empty row isn't full width
        while line_cells and line_cells[-1] == (" ", 7, 0):
            line_cells.pop()
        rows.append(line_cells)

    if redact_title_rows:
        # A row is title/credit text if its glyphs are mostly ASCII letters.
        # Title rows measure 0.56-0.92 letter fraction; drawn art is far lower.
        for line_cells in rows:
            visible_chars = [ch for ch, fg, bg in line_cells if ch != " "]
            if len(visible_chars) < 8:
                continue
            letters = sum(1 for ch in visible_chars if ch.isascii() and ch.isalpha())
            # Density alone misses a title drawn over a dither field (~0.31),
            # so also look for a run of letters.
            run = best = 0
            for ch, fg, bg in line_cells:
                if ch.isascii() and (ch.isalpha() or ch in "/-.,!'"):
                    run += 1
                    best = max(best, run)
                else:
                    run = 0
            if letters / len(visible_chars) > 0.5 or best >= 6:
                for i in range(len(line_cells)):
                    line_cells[i] = (" ", 7, 0)

    note = f" (truncated to first {max_rows} rows of {total_lines}+)" if truncated else ""
    return _rasterize_rows_to_png_b64(rows, note)


def _rasterize_rows_to_png_b64(rows, note=""):
    """Rasterize cell rows (lists of (char, fg_idx, bg_idx)) to a base64 PNG.
    Shared by the .ans and canvas renderers so both produce identical pixels."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None, "(error: Pillow not installed — pip install Pillow)"

    max_width = max((len(r) for r in rows), default=1)

    if not rows or max_width == 0:
        # Rows can exist yet all be blank after trimming; max_width would be 0
        # and PIL fails on a zero-width image.
        return None, "(error: no visible content to render — fully blank)"

    img_w = max_width * _CELL_W
    img_h = len(rows) * _CELL_H
    img = Image.new("RGB", (img_w, img_h), _ANSI_PALETTE[0])
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(_FONT_PATH, _FONT_SIZE)
    except Exception:
        font = ImageFont.load_default()

    for row_idx, cells in enumerate(rows):
        y = row_idx * _CELL_H
        for col_idx, (ch, fg_idx, bg_idx) in enumerate(cells):
            x = col_idx * _CELL_W
            bg = _ANSI_PALETTE[bg_idx]
            if bg_idx != 0:
                draw.rectangle([x, y, x + _CELL_W, y + _CELL_H], fill=bg)
            if ch == "\u2588":
                # Full block drawn as a filled rectangle, not a glyph: Menlo's █ is
                # 16px tall in an 18px cell, leaving gaps between stacked rows. ▓▒░
                # stay glyphs since their dot pattern is the content.
                fg = _ANSI_PALETTE[fg_idx]
                draw.rectangle([x, y, x + _CELL_W, y + _CELL_H], fill=fg)
            elif ch not in (" ", ""):
                fg = _ANSI_PALETTE[fg_idx]
                draw.text((x, y - 2), ch, font=font, fill=fg)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return b64, note


def render_canvas_to_png_b64(workspace, slug, offset=0, max_rows=200):
    """Preview a persistent canvas (canvas_tools.py) as a base64 PNG.
    Pixel-identical to canvas_save followed by preview_piece."""
    import canvas_tools
    try:
        data = canvas_tools.load_canvas(workspace, slug)
    except canvas_tools.CanvasError as e:
        return None, f"(error: {e})"
    # Cells straight from the canvas, no SGR round trip.
    all_rows = canvas_tools.render_canvas_cells(data)
    total_lines = len(all_rows)
    offset = max(0, min(offset, total_lines))
    end_row = min(total_lines, offset + max_rows)
    truncated = end_row < total_lines
    rows = [[(ch, fg % 16, bg % 16) for (ch, fg, bg) in r] for r in all_rows[offset:end_row]]

    note = f" (truncated to first {max_rows} rows of {total_lines}+)" if truncated else ""
    return _rasterize_rows_to_png_b64(rows, note)


def render_comparison_b64(piece_path, reference_path, offset=0, max_rows=60):
    """Render a piece and a reference side by side as one labeled image, so
    the agent judges its work against real reference quality, not memory."""
    from PIL import Image, ImageDraw, ImageFont

    piece_b64, piece_note = render_ans_to_png_b64(piece_path, offset=offset, max_rows=max_rows)
    if piece_b64 is None:
        return None, f"(error rendering piece: {piece_note})"
    ref_b64, ref_note = render_ans_to_png_b64(reference_path, offset=offset, max_rows=max_rows)
    if ref_b64 is None:
        return None, f"(error rendering reference: {ref_note})"

    piece_img = Image.open(io.BytesIO(base64.b64decode(piece_b64))).convert("RGB")
    ref_img = Image.open(io.BytesIO(base64.b64decode(ref_b64))).convert("RGB")

    label_h = 28
    gap = 6
    h = max(piece_img.height, ref_img.height) + label_h
    w = piece_img.width + gap + ref_img.width
    canvas = Image.new("RGB", (w, h), (20, 20, 20))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(_FONT_PATH, 18)
    except Exception:
        font = ImageFont.load_default()

    draw.text((4, 4), f"YOUR PIECE: {Path(piece_path).name}", font=font, fill=(255, 255, 0))
    draw.text((piece_img.width + gap + 4, 4), f"REFERENCE: {Path(reference_path).name}", font=font, fill=(0, 255, 255))
    canvas.paste(piece_img, (0, label_h))
    canvas.paste(ref_img, (piece_img.width + gap, label_h))
    draw.rectangle([piece_img.width + gap // 2 - 1, 0, piece_img.width + gap // 2, h], fill=(80, 80, 80))

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    out_b64 = base64.b64encode(buf.getvalue()).decode()
    note = ""
    if piece_note or ref_note:
        note = f" (piece{piece_note or ' full'}, reference{ref_note or ' full'})"
    return out_b64, note


def render_patches_grid_b64(patches):
    """Render retrieved corpus patches side by side as one labeled image.

    patches: dicts with chars/fg/bg numpy arrays plus parent_path,
    half_block_pct and shade_pct, as returned by find_patches_clip and
    find_patches_by_technique. Each patch is written to a temp .ans and
    rendered with render_ans_to_png_b64."""
    from PIL import Image, ImageDraw, ImageFont
    import tempfile

    if not patches:
        return None, "(no patches to render)"

    imgs = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, p in enumerate(patches):
            chars, fg, bg = p["chars"], p["fg"], p["bg"]
            lines = []
            for r in range(chars.shape[0]):
                parts = []
                cur_fg, cur_bg = None, None
                for c in range(chars.shape[1]):
                    f, b, ch = int(fg[r, c]), int(bg[r, c]), chr(int(chars[r, c]))
                    if (f, b) != (cur_fg, cur_bg):
                        sgr_fg = 30 + (f % 8) + (60 if f >= 8 else 0)
                        sgr_bg = 40 + (b % 8) + (60 if b >= 8 else 0)
                        parts.append(f"\x1b[0;{sgr_fg};{sgr_bg}m")
                        cur_fg, cur_bg = f, b
                    parts.append(ch)
                lines.append("".join(parts))
            text = "\r\n".join(lines) + "\x1b[0m\r\n"
            tmp_path = Path(tmpdir) / f"patch_{i}.ans"
            tmp_path.write_bytes(text.encode("utf-8"))
            b64, note = render_ans_to_png_b64(str(tmp_path))
            if b64 is None:
                continue
            img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
            label = f"{Path(p['parent_path']).name} half={p.get('half_block_pct', 0):.0f} shade={p.get('shade_pct', 0):.0f}"
            imgs.append((img, label))

    if not imgs:
        return None, "(all patches failed to render)"

    label_h = 22
    gap = 8
    cell_h = max(im.height for im, _ in imgs)
    w = sum(im.width for im, _ in imgs) + gap * (len(imgs) + 1)
    h = cell_h + label_h + gap * 2
    canvas = Image.new("RGB", (w, h), (20, 20, 20))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(_FONT_PATH, 14)
    except Exception:
        font = ImageFont.load_default()

    x = gap
    for img, label in imgs:
        draw.text((x, gap), label, font=font, fill=(150, 255, 150))
        canvas.paste(img, (x, gap + label_h))
        x += img.width + gap

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    out_b64 = base64.b64encode(buf.getvalue()).decode()
    return out_b64, f" ({len(imgs)} patches)"


def _parse_ans_grid(path):
    """Parse an .ans/.asc file into a cursor-addressable grid.

    Returns ({(row, col): (char, fg_idx, bg_idx)}, total_lines). Handles
    ESC[A/B/C/D/H/f cursor movement the way a terminal does."""
    raw = Path(path).read_bytes()
    text = _decode_ans_bytes(raw).replace("\r\n", "\n").replace("\r", "\n")

    grid = {}
    row, col = 0, 0
    max_row_seen = 0
    base_fg, bright_fg, base_bg = 7, False, 0
    pos = 0
    n = len(text)
    pending_wrap = False

    def put(ch):
        nonlocal col, row, max_row_seen, pending_wrap
        if pending_wrap:
            row += 1
            col = 0
            pending_wrap = False
            if row > max_row_seen:
                max_row_seen = row
        fg_idx = (base_fg + 8) if bright_fg else base_fg
        grid[(row, col)] = (ch, fg_idx % 16, base_bg % 16)
        col += 1
        if col >= _TERMINAL_WIDTH:
            col = _TERMINAL_WIDTH - 1
            pending_wrap = True

    while pos < n:
        ch = text[pos]
        if ch == "\n":
            if pending_wrap:
                pending_wrap = False
            else:
                row += 1
                col = 0
                if row > max_row_seen:
                    max_row_seen = row
            pos += 1
            continue
        m = _CSI_RE.match(text, pos)
        if m:
            param_str, code = m.group(1), m.group(2)
            params = [int(c) for c in param_str.split(";") if c != ""]
            if code == "m":
                for p in (params or [0]):
                    if p == 0:
                        base_fg, bright_fg, base_bg = 7, False, 0
                    elif p == 1:
                        bright_fg = True
                    elif p == 22:
                        bright_fg = False
                    elif p == 39:
                        base_fg, bright_fg = 7, False
                    elif p == 49:
                        base_bg = 0
                    elif 30 <= p <= 37:
                        base_fg = p - 30
                    elif 90 <= p <= 97:
                        base_fg, bright_fg = p - 90, True
                    elif 40 <= p <= 47:
                        base_bg = p - 40
                    elif 100 <= p <= 107:
                        base_bg = p - 100 + 8
            elif code == "C":
                col = min(_TERMINAL_WIDTH - 1, col + (params[0] if params else 1))
                pending_wrap = False
            elif code == "D":
                col = max(0, col - (params[0] if params else 1))
                pending_wrap = False
            elif code == "A":
                row = max(0, row - (params[0] if params else 1))
                pending_wrap = False
            elif code == "B":
                row = row + (params[0] if params else 1)
                pending_wrap = False
                if row > max_row_seen:
                    max_row_seen = row
            elif code in ("H", "f"):
                r = params[0] - 1 if len(params) >= 1 and params[0] else 0
                c = params[1] - 1 if len(params) >= 2 and params[1] else 0
                row, col = max(0, r), max(0, min(_TERMINAL_WIDTH - 1, c))
                pending_wrap = False
                if row > max_row_seen:
                    max_row_seen = row
            pos = m.end()
            continue
        put(ch)
        pos += 1

    return grid, max_row_seen + 1


_HALF_BLOCK_CHARS = set("\u2580\u2584\u2588")  # ▀ upper, ▄ lower, █ full
# Full block counts: HalfBlockCanvas emits it (or space+bg) when both
# pixels in a cell match.


def _figurative_precheck(path):
    """Pre-submission gate for figurative pieces: fewer than 3 distinct
    brightness steps in the subject blocks submission. Runs before curation
    and any Opus call.

    The subject mask is approximated as all non-background cells. Returns
    None on pass (or not figurative), else the failure reason."""
    if not _reads_figurative(path):
        return None  # gate only applies to figurative work

    try:
        grid, total_lines = _parse_ans_grid(path)
    except Exception:
        return None  # don't hard-block on a parse error; let normal review catch it

    total_cells = 0
    half_block_cells = 0
    brightness_values = set()
    # Coarse perceived brightness per ANSI index 0-15. Enough to count steps.
    _BRIGHTNESS = [0, 2, 2, 2, 2, 2, 2, 3, 1, 4, 4, 4, 4, 4, 4, 5]

    for (r, c), (ch, fg_idx, bg_idx) in grid.items():
        if ch == " " and bg_idx == 0:
            continue  # true empty cell, not part of the drawn subject
        total_cells += 1
        if ch in _HALF_BLOCK_CHARS:
            half_block_cells += 1
        # brightness proxy: for a space-with-bg cell the bg carries the
        # visible color; otherwise the fg glyph does.
        visible_idx = bg_idx if (ch == " " and bg_idx != 0) else fg_idx
        brightness_values.add(_BRIGHTNESS[visible_idx % 16])

    if total_cells == 0:
        return None  # empty file -- other checks will catch this

    half_block_frac = half_block_cells / total_cells
    n_brightness_steps = len(brightness_values)

    failures = []
    # No half-block floor: it could be met by distortion. half_block_frac is
    # still computed for the log.
    if n_brightness_steps < 3:
        failures.append(
            f"only {n_brightness_steps} distinct brightness step(s) found "
            f"across the piece's drawn cells -- real shading needs at least "
            f"3 (e.g. shadow/mid/highlight) to read as a lit form rather "
            f"than flat color fills"
        )
    if not failures:
        return None
    return (
        f"figurative pre-submission gate FAILED for {Path(path).name} "
        f"(checked automatically, before curator/Opus review -- no review "
        f"cycle spent): " + "; ".join(failures) + ". This is a hard block, "
        "not a suggestion: rework with half-block resolution and a real "
        "light_field()/shade() pass before resubmitting."
    )


_BRIGHTNESS_STEPS = [0, 2, 2, 2, 2, 2, 2, 3, 1, 4, 4, 4, 4, 4, 4, 5]
# Same table as _figurative_precheck, so both checks agree on a step.

FLAT_REGION_CELL_THRESHOLD = 40
# Reference numbers reported as soft signals on every submission, never
# enforced. The bar is what the reference pieces look like;
# compare_to_reference is the mechanism, not a threshold.
HOUSE_BAR = {"name": "_opus_CROSSING", "half_block": 26.1, "shade": 27.9,
             "colors": 12, "regions": 6, "ink_share": 48}
CORPUS_MEDIAN = {"half_block": 15.0, "shade": 9.4}


def _flat_region_check(path):
    """Flat-region gate for figurative pieces, run before curation.

    A same-glyph, same-color region inside the subject larger than
    FLAT_REGION_CELL_THRESHOLD fails unless a dithered ░▒▓ bridge connects it
    to another brightness step; so does an undithered seam between flat
    brightness levels in one hue. Figurative only, since wordmarks have
    legitimately solid strokes. Frame rows, box-drawing and dither glyphs
    are not subject cells. Returns None on pass, else the violations found.
    """
    if not _reads_figurative(path):
        return None  # scoped to figurative work, see docstring

    try:
        grid, total_lines = _parse_ans_grid(path)
    except Exception:
        return None  # don't hard-block on a parse error; let normal review catch it

    # Exclude border/title-rule rows: a frame is house convention, not a flat
    # subject region. Full U+2500 box-drawing block, so CP437 mixed-line
    # glyphs (╡╞╟ etc.) are included.
    _box_chars = {chr(cp) for cp in range(0x2500, 0x2580)}
    rows_seen = {}
    for (r, c), (ch, fg, bg) in grid.items():
        if ch == " " and bg == 0:
            continue
        rows_seen.setdefault(r, []).append(ch)
    border_rows = set()
    for r, chars in rows_seen.items():
        if len(chars) < 20:
            continue
        box_frac = sum(1 for ch in chars if ch in _box_chars) / len(chars)
        if box_frac > 0.7:
            border_rows.add(r)

    # Key subject cells by visible color. For a space-with-bg cell (the usual
    # HalfBlockCanvas output) the visible color is bg; fg is leftover state.
    subject_cells = {}
    dither_cells = set()
    for (r, c), (ch, fg, bg) in grid.items():
        if ch == " " and bg == 0:
            continue
        if r in border_rows:
            continue
        if ch in _box_chars:
            # Box-drawing glyphs are frame, never subject. The border_rows filter
            # above misses a rule that shares its row with title text.
            continue
        if ch in "\u2593\u2592\u2591":  # ▓▒░ -- partial-density dither
            # Dither is evidence of shading, never part of a flat region. Kept
            # in dither_cells so the seam check can credit a dithered bridge.
            dither_cells.add((r, c))
            continue
        visible_idx = bg if (ch == " " and bg != 0) else fg
        # Region key: (raw char, visible color), exact rather than fuzzy.
        subject_cells[(r, c)] = (ch, visible_idx)

    if len(subject_cells) < FLAT_REGION_CELL_THRESHOLD:
        return None  # too small a piece for this check to mean anything

    visited = set()
    large_regions = []
    for start in subject_cells:
        if start in visited:
            continue
        key = subject_cells[start]
        # BFS flood fill over 4-connected same-key cells
        stack = [start]
        region = []
        visited.add(start)
        while stack:
            cur = stack.pop()
            region.append(cur)
            r, c = cur
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                nxt = (nr, nc)
                if nxt in visited:
                    continue
                if subject_cells.get(nxt) == key:
                    visited.add(nxt)
                    stack.append(nxt)
        if len(region) > FLAT_REGION_CELL_THRESHOLD:
            rows = [r for r, c in region]
            cols = [c for r, c in region]
            large_regions.append({
                "size": len(region), "char": key[0], "visible_idx": key[1],
                "rows": (min(rows), max(rows)), "cols": (min(cols), max(cols)),
                "cells": region,
            })

    # Dither components (4-connected), shared by both checks below. A bridge is
    # one component touching two brightness levels: flat-dim -> dither ->
    # flat-bright is a gradient on a 16-color palette.
    dither_components = []
    dither_visited = set()
    for start in dither_cells:
        if start in dither_visited:
            continue
        stack = [start]
        comp = set()
        dither_visited.add(start)
        while stack:
            cur = stack.pop()
            comp.add(cur)
            r, c = cur
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                nxt = (nr, nc)
                if nxt in dither_cells and nxt not in dither_visited:
                    dither_visited.add(nxt)
                    stack.append(nxt)
        dither_components.append(comp)

    def _touches(cells_a, comp):
        # 4-connected adjacency (not just overlap) between a cell set
        # and a dither component's cell set.
        for (r, c) in cells_a:
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in comp:
                    return True
        return False

    # Which brightness steps does each dither component reach? Computed
    # against ALL subject cells, not just large regions, so a big fill
    # ramping into a small highlight still counts as a real gradient.
    comp_steps = []
    for comp in dither_components:
        steps_touched = set()
        for (r, c) in comp:
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                nb = subject_cells.get((nr, nc))
                if nb is not None:
                    steps_touched.add(_BRIGHTNESS_STEPS[nb[1] % 16])
        comp_steps.append(steps_touched)

    def _in_gradient(reg):
        """True when this region ramps into a different brightness level
        through a dithered bridge; large solid regions are fine in a gradient."""
        own = _BRIGHTNESS_STEPS[reg["visible_idx"] % 16]
        for comp, steps in zip(dither_components, comp_steps):
            if steps - {own} and _touches(reg["cells"], comp):
                return True
        return False

    failures = []
    unshaded = [reg for reg in large_regions if not _in_gradient(reg)]
    if unshaded:
        unshaded.sort(key=lambda x: -x["size"])
        examples = "; ".join(
            f"{r['size']} cells at rows {r['rows'][0]}-{r['rows'][1]}, "
            f"cols {r['cols'][0]}-{r['cols'][1]} (char {r['char']!r}, "
            f"visible color index={r['visible_idx']})"
            for r in unshaded[:3]
        )
        more = f" (+{len(unshaded) - 3} more)" if len(unshaded) > 3 else ""
        failures.append(
            f"{len(unshaded)} contiguous flat region(s) over "
            f"{FLAT_REGION_CELL_THRESHOLD} cells found inside the drawn "
            f"subject with NO dithered ramp to any other brightness "
            f"level: {examples}{more}. A real lit surface shades across "
            f"itself -- a same-color patch this large with no gradient "
            f"off it reads as an unshaded flat fill, not a lit form. "
            f"(A large solid region is fine when a ░▒▓ ramp connects it "
            f"to a different brightness step.)"
        )

    # No standalone shade-share block: every threshold tested against the
    # shipped gallery blocked accepted work. Shade is a soft signal in
    # submit_piece instead.

    # Lit-to-shadow check. A hue family (fg & 7) has only two levels, so real
    # shading is dithering between them: large flat regions at different
    # brightness in one hue need a connected ░▒▓ bridge between them.
    if len(large_regions) >= 2:
        # Group large regions by hue family (fg & 7); a seam is within one hue.
        by_hue = {}
        for reg in large_regions:
            hue_key = reg["visible_idx"] & 7
            by_hue.setdefault(hue_key, []).append(reg)

        for hue_key, regs in by_hue.items():
            if len(regs) < 2:
                continue
            # Dedupe by brightness: two regions at the same level aren't a seam.
            by_step = {}
            for reg in regs:
                step = _BRIGHTNESS_STEPS[reg["visible_idx"] % 16]
                by_step.setdefault(step, []).append(reg)
            steps = sorted(by_step)
            if len(steps) < 2:
                continue  # only one brightness level present -- nothing to bridge
            unbridged = []
            for i in range(len(steps) - 1):
                lo_regs, hi_regs = by_step[steps[i]], by_step[steps[i + 1]]
                bridged = any(
                    _touches(lo["cells"], comp) and _touches(hi["cells"], comp)
                    for lo in lo_regs for hi in hi_regs for comp in dither_components
                )
                if not bridged:
                    unbridged.append((steps[i], steps[i + 1]))
            if unbridged:
                pairs = ", ".join(f"{a}->{b}" for a, b in unbridged)
                failures.append(
                    f"hue family fg&7={hue_key}: brightness step "
                    f"transition(s) {pairs} have no dithered (░▒▓) bridge "
                    f"between the flat regions -- this reads as a hard "
                    f"seam between a hot and cold flat fill, not a real "
                    f"lit-to-shadow gradient. Use canvas.shade_ramp() "
                    f"between them so the two flat levels are connected "
                    f"by a real dithered transition, not touching "
                    f"directly."
                )

    if not failures:
        return None
    return (
        f"flat-region gate FAILED for {Path(path).name} (checked "
        f"automatically, before curator/Opus review -- no review cycle "
        f"spent): " + "; ".join(failures) + ". This is a hard block: "
        "rework the flagged region(s) with canvas.shade_ramp() before "
        "resubmitting."
    )


def _resolve_workspace_path(raw_path):
    p = Path(raw_path).expanduser()
    if not p.is_absolute():
        p = WORKSPACE / p
    return p


def _inside(p, root):
    """True if p (symlinks resolved) is root or somewhere under it."""
    try:
        Path(p).resolve().relative_to(Path(root).resolve())
        return True
    except (ValueError, OSError):
        return False


# --- Agent shell sandbox --------------------------------------------------
# Agent bash runs under macOS sandbox-exec: writes confined to workspace/,
# temp and caches; credential stores and the keychain unreachable; the
# claude CLI blocked; secrets stripped from the env. Internet stays open
# (agents curl 16colo.rs); loopback is denied, so no local service (the
# dashboards, ollama) is reachable from the shell. Fails closed: if the sandbox can't be verified
# on first use, the bash tool is refused.
_SANDBOX_EXEC = "/usr/bin/sandbox-exec"
_SECRET_ENV = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH|COOKIE|SESSION", re.I)
_SANDBOX_STATE = {"ok": None, "why": ""}

# Sandbox "localhost" = loopback; blocks 127.0.0.1 and ::1 (test_agent_loopback.py).
LOOPBACK_DENY = '(deny network-outbound (remote ip "localhost:*"))'


def _sandbox_profile():
    h = str(HOME.resolve())
    ws = str(WORKSPACE.resolve())

    def q(x):
        return '"' + x.replace("\\", "\\\\").replace('"', '\\"') + '"'

    # file-read* on a denied subpath blocks metadata as well as data, so
    # `ls` and `stat` fail too, not just `cat`.
    secret_dirs = [".ssh", ".claude", ".config/gh", ".hermes", ".aws", ".gnupg",
                   ".docker", ".kube", "Library/Keychains", ".local/share/claude",
                   "agentscii-private"]
    secret_files = [".claude.json", ".netrc", ".git-credentials", ".npmrc",
                    ".pypirc", ".local/bin/claude"]
    deny = ([f"(subpath {q(h + '/' + d)})" for d in secret_dirs]
            + [f"(literal {q(h + '/' + f)})" for f in secret_files])
    claude_bins = [d for d in deny if "claude" in d]
    return "\n".join([
        "(version 1)",
        "(allow default)",
        "(deny file-write*)",
        "(allow file-write*",
        f"  (subpath {q(ws)})",
        '  (subpath "/private/tmp") (subpath "/private/var/folders")',
        f"  (subpath {q(h + '/Library/Caches')}) (subpath {q(h + '/.cache')})",
        '  (regex #"^/dev/"))',
        "(deny file-read* file-write* " + " ".join(deny) + ")",
        "(deny process-exec " + " ".join(claude_bins) + ")",
        '(deny mach-lookup (global-name "com.apple.SecurityServer")'
        ' (global-name "com.apple.securityd"))',
        LOOPBACK_DENY,
    ])


def _agent_env():
    return {k: v for k, v in os.environ.items() if not _SECRET_ENV.search(k)}


def _sandbox_ok():
    if _SANDBOX_STATE["ok"] is not None:
        return _SANDBOX_STATE["ok"]
    ok, why = False, ""
    probe_out = HOME / ".agentscii_sandbox_probe"
    probe_in = WORKSPACE / ".agentscii_sandbox_probe"
    try:
        prof = _sandbox_profile()

        def sb(c):
            return subprocess.run([_SANDBOX_EXEC, "-p", prof, "/bin/bash", "-c", c],
                                  cwd=str(WORKSPACE), env=_agent_env(),
                                  capture_output=True, text=True, timeout=20)

        r_true = sb("true")
        sb(f'touch "{probe_out}" 2>/dev/null')
        r_in = sb(f'touch "{probe_in}"')
        if probe_out.exists():
            probe_out.unlink()
            why = "a write outside workspace/ was NOT blocked"
        elif r_true.returncode != 0:
            why = f"sandbox-exec failed: {(r_true.stderr or '').strip()[:200]}"
        elif r_in.returncode != 0 or not probe_in.exists():
            why = f"workspace write was blocked: {(r_in.stderr or '').strip()[:200]}"
        else:
            ok = True
    except Exception as e:
        why = f"{type(e).__name__}: {e}"
    finally:
        try:
            probe_in.unlink()
        except OSError:
            pass
    _SANDBOX_STATE.update(ok=ok, why=why)
    print(f"[harness] agent bash sandbox: "
          f"{'ACTIVE' if ok else 'UNAVAILABLE, bash tool disabled -- ' + why}", flush=True)
    return ok


def _sidecar_paths(piece_path):
    return (
        piece_path.with_suffix(piece_path.suffix + ".note.txt"),
        piece_path.with_suffix(piece_path.suffix + ".critique.txt"),
        piece_path.with_suffix(piece_path.suffix + ".credits.txt"),
    )


def _move_with_sidecars(src, dest_dir, new_critique=None):
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    src.rename(dest)
    note_src, critique_src, credits_src = _sidecar_paths(src)
    note_dest, critique_dest, credits_dest = _sidecar_paths(dest)
    if note_src.exists():
        note_src.rename(note_dest)
    if credits_src.exists():
        credits_src.rename(credits_dest)
    if new_critique is not None:
        critique_dest.write_text(new_critique)
    elif critique_src.exists():
        critique_src.rename(critique_dest)
    return dest


def run_tool(name, args, agent, shift_id=None):
    if name == "abandon_subject":
        if agent != "artist":
            return "(error: only the artist seat can abandon_subject)"
        slug = (args.get("slug") or "").strip()
        reason = (args.get("reason") or "").strip()
        if not slug or not reason:
            return "(error: both slug and reason are required)"
        db5 = sqlite3.connect(DB_PATH)
        try:
            existing = _get_subject(db5, slug)
            if existing is None:
                return f"(error: no open subject found for slug '{slug}')"
            if existing["status"] not in ("open", "rejected"):
                return f"(error: subject '{slug}' is already {existing['status']}, nothing to abandon)"
            db5.execute(
                "UPDATE subjects SET status='abandoned', abandon_reason=?, "
                "updated_at=? WHERE slug=?",
                (reason, time.time(), slug),
            )
            db5.commit()
            return f"abandoned: '{slug}' — {reason}"
        finally:
            db5.close()

    if name == "random_direction":
        # Weighted toward figurative/character/scene work, which the catalog is
        # thinnest in. Still random, still optional.
        subjects = (
            ["a masked figure or guardian bust", "a creature/demon face", "a robot or cyborg head",
             "two figures in conversation or confrontation", "a crowd or group scene",
             "a hooded traveler", "an eye embedded in something inhuman", "a hand reaching through something",
             "a full-body figure in motion", "a face mid-transformation"] * 3
            + ["a night skyline or cityscape", "a rail yard or industrial scene", "a wharf or coastline",
               "a desert or wasteland", "an interior (a room, a cockpit, a control room)"] * 2
            + ["an abstract/geometric field", "a fractal or mathematical form", "a flowing/organic pattern",
               "a wordmark or group logo treatment", "a circuit/hardware-substrate field"]
        )
        techniques = [
            "build it with canvas.py's ellipse()+gradient_fill() for the core shape and shading",
            "use canvas.py's mirror() for bilateral symmetry — a face, a creature, a mandala",
            "use canvas.py's flood_fill() to define large background/negative-space regions",
            "use canvas.py's line()+copy_region()/paste_block() to hand-place repeated motifs",
            "use figure_common.py's light_field()+shade_region() for anatomical/directional shading",
            "use curve_common.py's phosphor_render() for a traced-curve or scope aesthetic",
            "build it as a scroll_lib.py panel sequence — multiple linked panels, not one static screen",
            "hand-place every character with no shared library — pure from-scratch composition",
        ]
        palettes = [
            "monochrome + one accent color only", "full saturated 16-color cycling",
            "cool tones (blues/cyans/greens) dominant", "warm tones (reds/yellows/magentas) dominant",
            "high contrast — mostly black with bright accents", "muted/dim, low-saturation throughout",
        ]
        subject = random.choice(subjects)
        technique = random.choice(techniques)
        palette = random.choice(palettes)
        return (
            f"ROLL: subject = \"{subject}\" | technique constraint = \"{technique}\" | "
            f"palette lean = \"{palette}\".\n\n"
            "This is a seed, not a mandate — take it straight, remix it, or reject it "
            "and say why. If you build on it, note in your submission that it came "
            "from a random_direction roll so the provenance is honest."
        )

    if name == "inspect_piece":
        try:
            p = _resolve_workspace_path(args["path"])
            if not _inside(p, PROJECT_DIR):
                return "(error: inspect_piece is limited to the agentscii repo)"
            if not p.exists():
                return f"(error: {p} does not exist)"
            raw = p.read_bytes()
            try:
                text = raw.decode("utf-8")
                encoding = "utf-8"
            except UnicodeDecodeError:
                text = raw.decode("cp437", errors="replace")
                encoding = "cp437"

            lines = text.split("\n")
            sgr_re = re.compile(r"\x1b\[([0-9;]*)m")
            other_ctrl_re = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1a\x1c-\x1f]")

            width_issues = []
            blank_rows = []
            sparse_rows = []
            internal_gap_rows = []
            sgr_params = set()
            invalid_sgr = set()
            valid_sgr = {0,1,2,3,4,7,8,9,21,22,27,29,30,31,32,33,34,35,36,37,38,39,
                         40,41,42,43,44,45,46,47,48,49,90,91,92,93,94,95,96,97,98,99,
                         100,101,102,103,104,105,106,107}
            bad_control_bytes = False

            for i, line in enumerate(lines):
                if other_ctrl_re.search(line):
                    bad_control_bytes = True
                visible = sgr_re.sub("", line)
                for m in sgr_re.finditer(line):
                    for part in m.group(1).split(";"):
                        if part:
                            n = int(part)
                            sgr_params.add(n)
                            if n not in valid_sgr:
                                invalid_sgr.add(n)
                is_last = (i == len(lines) - 1)
                if len(visible) == 0:
                    if not is_last:
                        blank_rows.append(i)
                    continue
                if len(visible.strip()) < 8:
                    sparse_rows.append(i)
                # Internal gap: a long run of spaces with content on both sides, the
                # signature of a fill loop that stopped partway across the row.
                stripped = visible.rstrip()
                trailing_gap = len(visible) - len(stripped)
                if len(stripped) >= 6 and trailing_gap >= 15:
                    internal_gap_rows.append((i, len(stripped), trailing_gap))
                else:
                    core = visible.strip()
                    if core:
                        longest_run = 0
                        current = 0
                        for ch in core:
                            if ch == " ":
                                current += 1
                                longest_run = max(longest_run, current)
                            else:
                                current = 0
                        if longest_run >= 30:
                            internal_gap_rows.append((i, len(core), longest_run))
                if len(visible) != 80 and not is_last:
                    width_issues.append((i, len(visible)))

            # collapse blank_rows into ranges so a 30-row dead void reads as
            # one finding, not thirty
            blank_ranges = []
            for r in blank_rows:
                if blank_ranges and r == blank_ranges[-1][1] + 1:
                    blank_ranges[-1] = (blank_ranges[-1][0], r)
                else:
                    blank_ranges.append((r, r))
            long_blank_ranges = [(a, b) for a, b in blank_ranges if b - a >= 3]

            gap_ranges = []
            for (r, content_len, gap_len) in internal_gap_rows:
                if gap_ranges and r == gap_ranges[-1][1] + 1:
                    gap_ranges[-1] = (gap_ranges[-1][0], r)
                else:
                    gap_ranges.append((r, r))
            long_gap_ranges = [(a, b) for a, b in gap_ranges]

            ends_with_reset = raw.rstrip(b"\n").endswith(b"\x1b[0m")

            out = []
            out.append(f"path: {p.name}")
            out.append(f"encoding: {encoding} | {len(lines)} lines | control bytes clean: {not bad_control_bytes}")
            out.append(f"ends on standalone reset: {ends_with_reset}")
            out.append(f"SGR params used: {sorted(sgr_params)}")
            out.append(f"invalid/out-of-range SGR params: {sorted(invalid_sgr) or 'none'}")
            if width_issues:
                out.append(f"non-80-width content rows: {len(width_issues)} (first 8: {width_issues[:8]})")
            else:
                out.append("all content rows exactly 80 display-columns wide")
            if long_blank_ranges:
                out.append(
                    f"DEAD/BLANK REGIONS (3+ consecutive empty rows — likely a real "
                    f"rendering bug, not intentional spacing): {long_blank_ranges}"
                )
            else:
                out.append("no suspiciously long blank regions")
            if long_gap_ranges:
                out.append(
                    f"POSSIBLE INTERNAL GAPS (rows with a long unexplained blank "
                    f"run flanked by real content — can indicate a fill/paint loop "
                    f"that silently stopped partway across a row, but can also be "
                    f"legitimate sparse/framed composition — VERIFY with "
                    f"preview_piece before treating as a bug): row ranges "
                    f"{long_gap_ranges}."
                )
            else:
                out.append("no mid-row rendering gaps detected")
            if sparse_rows and len(sparse_rows) > len(lines) * 0.15:
                out.append(
                    f"WARNING: {len(sparse_rows)}/{len(lines)} rows are sparse "
                    f"(<8 visible chars) — piece may be mostly empty space"
                )

            # --- background density check -------------------------------------
            # Methodology Pass 5: negative space needs texture. Without vision, flag
            # long runs of near-black bg with low glyph density.
            bg_re = re.compile(r"\x1b\[[0-9;]*m")
            near_black_bg_rows = 0
            textured_bg_rows = 0
            content_rows = 0
            for line in lines:
                visible = bg_re.sub("", line)
                if not visible.strip():
                    continue
                content_rows += 1
                # crude density proxy: fraction of visible chars that are a
                # real glyph (not space) vs the row width
                non_space = sum(1 for ch in visible if ch != " ")
                density = non_space / max(1, len(visible))
                has_bg_change = "\x1b[4" in line or "\x1b[10" in line  # any bg SGR set
                if not has_bg_change and density < 0.35:
                    near_black_bg_rows += 1
                elif density < 0.6:
                    textured_bg_rows += 1
            if content_rows >= 10:
                flat_frac = near_black_bg_rows / content_rows
                if flat_frac > 0.4:
                    out.append(
                        f"LOW BACKGROUND TEXTURE: {near_black_bg_rows}/{content_rows} "
                        f"content rows ({flat_frac*100:.0f}%) read as mostly-empty/"
                        f"unvaried background -- Pass 5 (negative-space texture) "
                        f"may have been skipped. Real scene reference work rarely "
                        f"leaves this much genuinely flat space; verify by eye with "
                        f"preview_piece whether this is a deliberate minimal "
                        f"composition or a missing texture_fill() pass."
                    )
                else:
                    out.append(f"background texture: {near_black_bg_rows}/{content_rows} rows read flat ({flat_frac*100:.0f}%) -- reasonable")

            # --- border/frame presence check ------------------------------------
            # Methodology Pass 6: scene packs are usually framed. Check whether the
            # first or last content row looks like a rule or border.
            box_chars = set("═║╔╗╚╝╠╣╦╩╬─│┌┐└┘├┤┬┴┼█▓▒░")
            def looks_framed(line):
                visible = bg_re.sub("", line).strip()
                if len(visible) < 20:
                    return False
                box_frac = sum(1 for ch in visible if ch in box_chars) / len(visible)
                # a long run of ANY single repeated char also reads as a rule
                longest_run, cur, last = 0, 0, None
                for ch in visible:
                    if ch == last and ch != " ":
                        cur += 1
                    else:
                        cur = 1
                    longest_run = max(longest_run, cur)
                    last = ch
                return box_frac > 0.5 or longest_run >= 20
            content_line_idxs = [i for i, l in enumerate(lines) if bg_re.sub("", l).strip()]
            has_top_frame = bool(content_line_idxs) and looks_framed(lines[content_line_idxs[0]])
            has_bottom_frame = bool(content_line_idxs) and looks_framed(lines[content_line_idxs[-1]])
            if content_line_idxs and len(content_line_idxs) >= 6 and not (has_top_frame or has_bottom_frame):
                out.append(
                    "NO FRAME/BORDER DETECTED: neither the first nor last content "
                    "row reads as a border/rule/title-card treatment. Real scene "
                    "packs are framed more often than not (Methodology Pass 6) -- "
                    "verify by eye whether this piece deliberately goes unframed "
                    "or whether that pass just got skipped."
                )
            elif has_top_frame or has_bottom_frame:
                out.append(f"frame/border: detected ({'top' if has_top_frame else ''}{' + ' if has_top_frame and has_bottom_frame else ''}{'bottom' if has_bottom_frame else ''})")
            # --- scope-family relabeling check ---------------------------------
            # curve_common.phosphor_render() uses a distinctive 8-hue SGR set. A piece
            # using only that set under a figurative filename is likely scope math
            # relabeled as a character piece; flag it for a by-eye check.
            scope_fingerprint = {95, 91, 93, 92, 96, 94, 107, 103, 97, 0, 40, 104, 105}
            name_lower = p.stem.lower()
            reads_figurative = bool(_FIGURATIVE_WORDS_RE.search(name_lower))
            if sgr_params and sgr_params.issubset(scope_fingerprint) and reads_figurative:
                out.append(
                    "POSSIBLE MISLABEL: this piece's SGR palette exactly matches "
                    "curve_common.py's phosphor/scope-family fingerprint (the "
                    "8-hue wheel + white-hot, nothing else), but its name reads "
                    "as figurative/character work. Verify by eye whether this is "
                    "genuine anatomical/figure construction or relabeled "
                    "parametric-curve math wearing a figurative title before "
                    "counting it toward the figurative tradition."
                )

            # --- placeholder/debug text check ------------------------------------
            # Scan visible text for placeholder and debug tokens.
            disp_all = bg_re.sub("", "\n".join(lines))
            placeholder_re = re.compile(
                r"\b(?:TODO|FIXME|PLACEHOLDER|XXX|TBD|object \+ object|"
                r"DEBUG|WIP-TEXT|lorem ipsum|REPLACE ?ME|CHANGE ?ME)\b",
                re.IGNORECASE,
            )
            hits = sorted(set(m.group(0) for m in placeholder_re.finditer(disp_all)))
            if hits:
                out.append(
                    f"PLACEHOLDER/DEBUG TEXT DETECTED IN RENDERED OUTPUT: {hits} -- "
                    f"this reads as leftover debug/placeholder text baked into the "
                    f"actual image, not real content. Fix before submitting."
                )

            # --- provenance ------------------------------------------------------
            # Whether the cells came from the agent's canvas_* tools or from a
            # script it wrote. Not a gate: the curator decides what it means.
            try:
                import canvas_tools as _ct
                _slug = p.stem.lstrip("_").split(".")[0]
                for _cand in (p.stem, _slug):
                    if _ct.canvas_exists(str(WORKSPACE), _cand):
                        out.append(_ct.provenance_line(str(WORKSPACE), _cand))
                        break
            except Exception:
                pass

            return "\n".join(out)
        except Exception as e:
            return f"(error inspecting piece: {e})"

    if name == "bash":
        try:
            cmd = args["command"]
            # Agents may not call the `claude` CLI: Opus review is metered and only
            # runs through curate_piece's capped, logged path. Matches `claude` as a
            # command word only.
            if re.search(r"(?:^|[;&|\s])claude(?:\s|$)", cmd):
                return (
                    "(error: direct `claude` CLI invocation is blocked in "
                    "agent shell commands — Opus 5 review runs only through "
                    "the harness's curate_piece flow, which enforces the "
                    "daily cap and per-piece review limit. If you need a "
                    "second opinion, use curate_piece's built-in Opus gate, "
                    "not a direct CLI call.)"
                )
            if not _sandbox_ok():
                return (
                    "(error: the agent shell is disabled because its security "
                    f"sandbox could not be verified: {_SANDBOX_STATE['why']}. "
                    "Use the canvas_* and file tools instead.)"
                )
            r = subprocess.run(
                [_SANDBOX_EXEC, "-p", _sandbox_profile(), "/bin/bash", "-c", cmd],
                cwd=str(WORKSPACE), env=_agent_env(),
                capture_output=True, text=True, timeout=BASH_TIMEOUT,
            )
            out = (r.stdout or "") + (r.stderr or "")
            return out[:4000] if out else "(no output)"
        except subprocess.TimeoutExpired:
            return f"(command timed out after {BASH_TIMEOUT}s)"
        except Exception as e:
            return f"(error: {e})"

    if name == "read_file":
        try:
            p = _resolve_workspace_path(args["path"])
            if not _inside(p, PROJECT_DIR):
                return "(error: read_file is limited to the agentscii repo)"
            return p.read_text(errors="replace")[:4000]
        except Exception as e:
            return f"(error: {e})"

    if name == "write_file":
        try:
            p = _resolve_workspace_path(args["path"])
            if not _inside(p, WORKSPACE):
                return "(error: write_file is limited to workspace/)"
            # figure_common.py is frozen. chmod 444 on disk is the real enforcement;
            # this just gives a clear error.
            if p.name == "figure_common.py":
                return (
                    "(error: figure_common.py is frozen. Draw on a canvas "
                    "with the canvas_* tools; canvas_cells places individual "
                    "glyphs. See workspace/METHOD.md.)"
                )
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args["content"])
            return f"wrote {len(args['content'])} bytes to {p}"
        except Exception as e:
            return f"(error: {e})"

    if name == "message_agent":
        return "(handled by harness)"

    if name == "set_handle":
        return "(handled by harness)"

    if name == "submit_piece":
        if agent != "artist":
            return "(error: only the artist seat can submit_piece)"
        try:
            src = _resolve_workspace_path(args["path"])
            if not _inside(src, WORKSPACE):
                return "(error: submit_piece only takes files inside workspace/)"
            if not src.exists():
                return f"(error: {src} does not exist)"

            # --- figurative pre-submission gate -------------------------------
            # Runs first, before any other gate or Opus call.
            precheck_fail = _figurative_precheck(src)
            if precheck_fail:
                return f"(error: {precheck_fail})"

            # --- flat-region pre-submission gate ------------------------------
            flat_fail = _flat_region_check(src)
            if flat_fail:
                return f"(error: {flat_fail})"

            # --- soft technique signals (never a block) ---------------------
            soft_signal = ""
            _sm = _compute_piece_metrics(src)
            if _sm is not None:
                # Log only: shown to the artist, a number becomes a target.
                print(f"[metrics] {src.name}: {_fmt_metrics(_sm)}", flush=True)
                _operator_only = (
                    f"\n\ntechnique (SOFT SIGNAL — not a gate, nothing is "
                    f"enforced): {_fmt_metrics(_sm)}. "
                    f"House bar {HOUSE_BAR['name']}: "
                    f"{HOUSE_BAR['half_block']}% / {HOUSE_BAR['shade']}%, "
                    f"{HOUSE_BAR['colors']} colors, "
                    f"{HOUSE_BAR['regions']} masses, "
                    f"{HOUSE_BAR['ink_share']}% ink. "
                    f"Corpus median: {CORPUS_MEDIAN['half_block']}% / "
                    f"{CORPUS_MEDIAN['shade']}%. Match or beat "
                    f"{HOUSE_BAR['name']} on structure and half-block use — "
                    f"one centered blob in few colors is what the weakest "
                    f"recent work looked like."
                )

            # --- required reference comparison before submit -------------------
            # A figurative piece must be compared side by side with a reference piece
            # first. Checked against this shift's logged compare_to_reference calls.
            db_cmp = sqlite3.connect(DB_PATH)
            try:
                seen_ref = db_cmp.execute(
                    "SELECT COUNT(*) FROM events WHERE shift_id=? "
                    "AND tool_name='compare_to_reference' "
                    "AND tool_args LIKE '%\\_opus\\_%' ESCAPE '\\'", (shift_id,)
                ).fetchone()[0]
            finally:
                db_cmp.close()
            if not seen_ref:
                return (
                    "(error: submit_piece blocked — call compare_to_reference "
                    "with one of references/study/_opus_CROSSING.ans, "
                    "_opus_AQUEDUCT.ans or _opus_PROSPECTOR.ans and "
                    "actually look at the result first. These are the house bar: "
                    "match them on whether a SUBJECT RESOLVES and on scene depth. Do not chase their metrics -- they score lower than pieces they beat. This is "
                    "a look-before-you-submit requirement, not a metric "
                    "threshold — nothing about your numbers is being enforced.)"
                )

            # --- tripwire halt ----------------------------------------------
            _db_h = sqlite3.connect(DB_PATH)
            try:
                if _tripwire_halted(_db_h):
                    return (
                        "(error: submissions are HALTED by the regression "
                        "tripwire — two consecutive accepted pieces fell "
                        "below the recent-accept bar. Report to the human "
                        "with what changed rather than submitting more.)"
                    )
            finally:
                _db_h.close()

            # --- required find_patches before submit -----------------------
            # Required on every piece, not just figurative ones: _reads_figurative's
            # word list misses most scene/creature/logo subjects.
            db_fp = sqlite3.connect(DB_PATH)
            try:
                seen_fp = db_fp.execute(
                    "SELECT COUNT(*) FROM events WHERE shift_id=? "
                    "AND tool_name='find_patches'", (shift_id,)
                ).fetchone()[0]
            finally:
                db_fp.close()
            if not seen_fp:
                return (
                    "(error: submit_piece blocked — call find_patches at "
                    "least once this shift before submitting, and actually "
                    "look at what real artists did. "
                    "Query for the technique or arrangement you're "
                    "building, not the subject name: 'tall monolith slab "
                    "lit volume with shading gradient' returns usable "
                    "technique, 'cool picture' does not. Forms are "
                    "rendering correctly now; arrangement is the open "
                    "problem, and retrieval is the lever for it.)"
                )

            # --- retired subject + re-slug identity ------------------------
            # Both ask what subject this is. The filename slug alone can be dodged by
            # renaming.
            db_sub = sqlite3.connect(DB_PATH)
            try:
                _title = ""
                _note_p = src.with_suffix(src.suffix + ".note.txt")
                if _note_p.exists():
                    _title = _note_p.read_text(errors="replace")[:400]
                retired = _retired_subject_block(db_sub, src.stem, _title)
                if retired:
                    return f"(error: {retired})"

                fp = _subject_fingerprint(src)
                if fp:
                    prior = db_sub.execute(
                        "SELECT slug FROM subjects WHERE fingerprint=? "
                        "AND slug!=?", (fp, core_slug(src.stem))
                    ).fetchone()
                    if prior:
                        return (
                            f"(error: submit_piece blocked — this is the same "
                            f"piece as subject '{prior[0]}' under a new name. "
                            f"Subject identity is tracked by CONTENT, not "
                            f"filename, so renaming does not reset a revision "
                            f"count. Either revise '{prior[0]}' as the same "
                            f"subject, or draw something genuinely different.)"
                        )
            finally:
                db_sub.close()

            # --- revision-over-novelty + open-subject cap gate ---------------
            # A rejected piece must come back as the same slug at v+1, not a fresh
            # slug. At most 2 open subjects; a third needs one accepted or abandoned.
            slug = core_slug(src.stem)
            version = _extract_version(src.stem)
            db2 = sqlite3.connect(DB_PATH)
            try:
                # --- hard revision cap ---------------------------------------
                # Counted from piece_metrics rows (real submissions), not the filename's
                # version number, which can skip or have gaps.
                revision_count = db2.execute(
                    "SELECT COUNT(*) FROM piece_metrics WHERE slug=?", (slug,)
                ).fetchone()[0]
                if revision_count >= MAX_REVISIONS_PER_SUBJECT:
                    best = _get_best_metrics(db2, slug)
                    best_desc = (
                        f"v{best['version']} (half_block_pct={best['half_block_pct']:.1f}, "
                        f"shade_char_pct={best['shade_char_pct']:.1f})"
                        if best else "(no metrics on file)"
                    )
                    return (
                        f"(error: submit_piece blocked — '{slug}' has already "
                        f"had {revision_count} real submitted revisions, the "
                        f"cap ({MAX_REVISIONS_PER_SUBJECT}). This is not a "
                        "suggestion to try harder on a 9th version: 59 "
                        "versions is thrashing, not iteration. Pick one: "
                        "(a) if the current version is genuinely ship-quality, "
                        "get it through curate_piece as-is; (b) revert to the "
                        f"best-scoring earlier version instead — {best_desc} — "
                        "and submit THAT file unchanged rather than a new "
                        "attempt; or (c) abandon_subject with a written reason "
                        "if neither is true. Do not keep editing toward a v9.)"
                    )

                existing_subject = _get_subject(db2, slug)
                if existing_subject is not None and existing_subject["status"] == "rejected":
                    if version <= existing_subject["last_version"]:
                        return (
                            f"(error: submit_piece blocked — '{slug}' was "
                            f"rejected at v{existing_subject['last_version']}. "
                            "Revision-over-novelty: resubmit the SAME file "
                            f"at a HIGHER version (v{existing_subject['last_version']+1} "
                            "or later, filename suffix .vN/-vN/_vN), not a "
                            "differently-named fresh file for the same "
                            "underlying subject. If this genuinely is a "
                            "different subject, that's fine — just don't "
                            "reuse a name that reads as the same core slug.)"
                        )
                elif existing_subject is None:
                    open_subjects = _open_subjects(db2)
                    if len(open_subjects) >= 2:
                        names = ", ".join(s["slug"] for s in open_subjects)
                        return (
                            f"(error: submit_piece blocked — 2 subjects "
                            f"already open ({names}). Starting a third is "
                            "blocked until one is accepted or explicitly "
                            "abandoned via abandon_subject with a written "
                            "reason. This isn't a suggestion: pick one of "
                            "the open subjects to push to done, or abandon "
                            "one honestly first.)"
                        )

                # --- per-version metrics, pinned-best regression gate --------
                # Block a revision whose own metrics drop against the pinned best, even
                # if the targeted defect is fixed.
                new_metrics = _compute_piece_metrics(src)
                best = _get_best_metrics(db2, slug)
                if new_metrics is not None and best is not None:
                    regressions = []
                    for key, label in (
                        ("half_block_pct", "half-block %"),
                        ("shade_char_pct", "shade-char (░▒▓) %"),
                        ("distinct_colors_in_subject", "distinct subject colors"),
                    ):
                        old_v, new_v = best[key], new_metrics[key]
                        # 0.5 slack so rounding doesn't block an unchanged metric
                        if new_v < old_v - 0.5:
                            regressions.append(
                                f"{label}: {old_v:.1f} (v{best['version']}) -> "
                                f"{new_v:.1f} (this submission)"
                            )
                    if regressions:
                        return (
                            f"(error: submit_piece blocked — this revision "
                            f"regresses versus the pinned best (v{best['version']}) "
                            f"on: {'; '.join(regressions)}. Fixing the flagged "
                            f"defect isn't enough if it comes at the cost of a "
                            f"real metric going backward — revise from the "
                            f"pinned script (see subjects.pinned_script_path) "
                            f"and make sure this version is strictly at or "
                            f"above the pinned best on every tracked metric, "
                            f"not just the one you were focused on fixing.)"
                        )
            finally:
                db2.close()

            # --- reference-comparison gate ---------------------------------
            # Self-assessment in isolation is unreliable. Blocked unless
            # compare_to_reference ran on this file in this agent's last 40 events.
            db = sqlite3.connect(DB_PATH)
            recent = db.execute(
                "SELECT tool_args FROM events WHERE agent=? AND tool_name='compare_to_reference' "
                "ORDER BY id DESC LIMIT 40",
                (agent,),
            ).fetchall()
            db.close()
            did_compare = any(
                src.name in (row[0] or "") for row in recent
            )
            if not did_compare:
                return (
                    f"(error: submit_piece blocked — call compare_to_reference on "
                    f"{src.name} against a real file in references/study/ first. "
                    "Pick whichever reference is closest in subject/technique. "
                    "This isn't optional: self-judging a render alone has caused "
                    "real submitted pieces to look nothing like reference quality "
                    "while being called 'submission-ready'.)"
                )

            # --- capsule()/joint_dot() claim-vs-reality gate --------------
            # If the note claims the shared primitive, the source must call it.
            # Checked at submit, while the .py still sits next to the .ans.
            note_text = args.get("note", "")
            body_words = ("figure", "figurative", "body", "torso", "limb",
                          "capsule", "joint_dot", "anatomy", "anatomical")
            claims_body_tooling = any(w in note_text.lower() for w in body_words)
            if claims_body_tooling:
                py_candidate = src.with_suffix(".py")
                if py_candidate.exists():
                    py_text = py_candidate.read_text(errors="replace")
                    # Strip comments first: a comment mentioning capsule() is not a call.
                    code_only = "\n".join(
                        line.split("#", 1)[0] for line in py_text.split("\n")
                    )
                    calls_capsule = bool(re.search(
                        r"\b(?:fc\.|figure_common\.)?capsule\s*\(", code_only
                    ))
                    calls_joint_dot = bool(re.search(
                        r"\b(?:fc\.|figure_common\.)?joint_dot\s*\(", code_only
                    ))
                    # Negation-aware: "not capsule()" is a disclosure, not a claim.
                    _NEGATORS = (
                        r"\b(?:no|not|n't|without|instead of|rather than|"
                        r"my own|hand-?rolled|custom)\b"
                    )
                    note_claims_shared_tooling = False
                    for m in re.finditer(r"capsule\(\)|joint_dot\(\)", note_text):
                        pre = note_text[max(0, m.start() - 40):m.start()]
                        if re.search(_NEGATORS, pre, re.IGNORECASE):
                            continue  # negated mention -- honest disclosure, not a claim
                        note_claims_shared_tooling = True
                        break
                    if note_claims_shared_tooling and not (calls_capsule or calls_joint_dot):
                        return (
                            "(error: submission BLOCKED — your note references "
                            "capsule()/joint_dot() but the matching source file "
                            f"({py_candidate.name}) never actually calls either "
                            "function. If you built your own local shading "
                            "function instead of the shared primitive, that's "
                            "fine — but say so explicitly and don't claim the "
                            "shared tooling. If you meant to use capsule(), fix "
                            "the code to actually call it before resubmitting — "
                            "a body/limb surface needs shade()'s DENSITY-varying "
                            "glyph (not a hardcoded solid block) to read as a "
                            "lit 3D form instead of a flat color band.)"
                        )

            SUBMISSIONS.mkdir(parents=True, exist_ok=True)
            dest = SUBMISSIONS / src.name
            src.rename(dest)
            dest.with_suffix(dest.suffix + ".note.txt").write_text(args.get("note", ""))
            contributors = args.get("contributors")
            if contributors:
                dest.with_suffix(dest.suffix + ".credits.txt").write_text(contributors)
            db3 = sqlite3.connect(DB_PATH)
            try:
                _touch_subject(db3, slug, version, dest, status="open")
                # Record this version's metrics; pin the first version seen as the
                # initial best so v2 has a baseline.
                recorded = _record_piece_metrics(db3, slug, version, dest)
                if recorded is not None:
                    existing_pin = db3.execute(
                        "SELECT pinned_version FROM subjects WHERE slug=?", (slug,)
                    ).fetchone()
                    if existing_pin and existing_pin[0] is None:
                        # The generator script is unversioned (scratch/_orb.py, edited in
                        # place across revisions), not named after the submitted .ans.
                        pinned_script = SCRATCH / f"{slug}.py"
                        db3.execute(
                            "UPDATE subjects SET pinned_script_path=?, "
                            "pinned_version=? WHERE slug=?",
                            (str(pinned_script), version, slug),
                        )
                        db3.commit()
            finally:
                db3.close()
            return (
                f"submitted: moved {src.relative_to(WORKSPACE)} -> "
                f"{dest.relative_to(WORKSPACE)}{soft_signal}"
            )
        except Exception as e:
            return f"(error: {e})"

    if name == "curate_piece":
        if agent != "curator":
            return "(error: only the curator seat can curate_piece)", None
        try:
            src = _resolve_workspace_path(args["path"])
            if not src.exists() or SUBMISSIONS not in src.parents:
                return f"(error: {args['path']} is not a file currently in submissions/)", None
            decision = args.get("decision")
            critique = args.get("critique", "")
            if decision == "accept":
                # If the critique makes a checkable visual claim (face, eye, figure...),
                # get a blind description from the same model and block the accept on a
                # flat contradiction. The curator can revise or override with a note.
                critique_lower = critique.lower()
                # Negation-aware: only count a claim word the curator asserts, not
                # "no face", "isn't a figure", "without eyes".
                _NEGATORS = (
                    r"\b(?:no|not|n't|without|zero|none of|isn'?t|aren'?t|lacks?|"
                    r"absence of|disclaims?|rather than|pretending (?:to be|at)|"
                    r"instead of|supposed to be)\b"
                )
                claimed_words = []
                for w in _VISUAL_CLAIM_WORDS:
                    # Word-boundary match so "eyed" doesn't count; "by eye" is skipped below.
                    for m in re.finditer(r"\b" + re.escape(w) + r"\b", critique_lower):
                        post = critique_lower[m.end():m.end() + 8]
                        if w == "eye" and post.startswith(" against"):
                            continue  # "by eye against ref" == verified visually
                        pre_tail = critique_lower[max(0, m.start() - 8):m.start()]
                        if w == "eye" and pre_tail.rstrip().endswith("by"):
                            continue  # "by eye" == verified visually, not a claim
                        # Negation can govern a list ("no anatomy, face, eye"), so look back to
                        # the start of the clause, stopping at a break (but/however/;).
                        clause_start = max(
                            critique_lower.rfind(".", 0, m.start()),
                            critique_lower.rfind("!", 0, m.start()),
                            critique_lower.rfind("?", 0, m.start()),
                        ) + 1
                        clause = critique_lower[clause_start:m.start()]
                        break_pos = max(
                            (clause.rfind(b) for b in (" but ", " however ", "; ")),
                            default=-1,
                        )
                        governing = clause[break_pos + 1:] if break_pos >= 0 else clause
                        if re.search(_NEGATORS, governing):
                            continue  # negated (directly or via governing clause) — not a claim
                        claimed_words.append(w)
                        break
                if claimed_words:
                    blind = _blind_visual_check(src)
                    blind_lower = blind.lower()
                    # A denial signal in the first ~200 chars plus a phrase describing
                    # flat or geometric shapes anywhere in the response.
                    denial_signal = bool(re.search(
                        r"\bno\b[^.]{0,80}\b(constructed|discernible|clearly)\b"
                        r"|\bnot\b[^.]{0,40}\bconstructed\b"
                        r"|\bno\.\s",
                        blind_lower[:220],
                    ))
                    grounding_signal = bool(re.search(
                        r"flat|solid-color|solid color|no gradient|no shading"
                        r"|no anatomical|geometric shapes|no such feature"
                        r"|no face|no eye|no brow",
                        blind_lower,
                    ))
                    # The guard catches claimed anatomy that isn't there. Landscape terms
                    # ("mountain silhouettes") aren't anatomy, and a scene has none.
                    _LANDSCAPE_OK = {"silhouette", "totem", "lantern", "ember"}
                    anatomy_claimed = [w for w in claimed_words
                                       if w not in _LANDSCAPE_OK]
                    contradicts = (
                        not blind_lower.startswith("(blind check")
                        and denial_signal and grounding_signal
                        and bool(anatomy_claimed)
                    )
                    if contradicts:
                        return (
                            "(error: accept BLOCKED — your critique claims "
                            + ", ".join(claimed_words) + f", but an independent "
                            "blind visual check (same model, no access to your "
                            "critique) describes it differently:\n\n"
                            f'"{blind}"\n\n'
                            "If your critique is right and the blind check is "
                            "wrong, re-examine with preview_piece and either "
                            "revise your critique to be more specific/accurate, "
                            "or re-submit the accept with a critique that "
                            "explicitly addresses this discrepancy. If the "
                            "blind check is right, this should be a reject, "
                            "not an accept.)"
                        ), None
                # Opus is the sole accept/reject authority; Qwen's verdict is passed
                # through for logging only.
                return curate_piece_opus_gated(src, decision, critique, shift_id)
            elif decision == "reject":
                return curate_piece_opus_gated(src, decision, critique, shift_id)
            else:
                return f"(error: decision must be 'accept' or 'reject', got {decision!r})", None
        except Exception as e:
            return f"(error: {e})", None

    if name == "release_pack":
        return "(handled by harness)"

    if name == "end_shift":
        return "(handled by harness)"

    return f"(unknown tool: {name})"


def _log_curation_event(shift_id, action, path, dest_path, note):
    """One row in curation_events. Used for advisory verdicts that move
    nothing, so the DB records what the check thought without the file
    location implying a decision."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO curation_events (shift_id, action, path, dest_path, note, timestamp) "
            "VALUES (?,?,?,?,?,?)",
            (shift_id, action, str(path), dest_path, note, time.time()))
        conn.commit()
    finally:
        conn.close()


def curate_piece_opus_gated(src, decision, critique, shift_id=None):
    """Hand the accept/reject decision to Opus, the only authority. Qwen's
    decision and critique are logged, not used.

    Keeps the subjects table in sync: accept/shelve close the subject;
    reject leaves it open and forces a higher version next time. Returns
    (message, dest_path_or_None), the same shape as curate_piece."""
    # --- blind subject-recognition check: advisory only ---------------
    # Records its verdict as an event; moves no file, overrides nothing.
    subject_result = opus_subject_check(src)
    _status = subject_result.get("status")
    if _status != "disabled":     # off by config = neither a pass nor a refusal
        if _status in ("match", "mismatch"):
            _note = f"[{_status}] {subject_result.get('message', '')}"
        else:
            # A refused/failed check must not read as a pass. (standing rule)
            _note = (f"SUBJECT_CHECK_DID_NOT_RUN [{_status}]: "
                     f"{subject_result.get('message', '')}")
        _log_curation_event(shift_id, "subject_advisory", src, None, _note)

    # --- pairwise regression gate -------------------------------------
    # Runs second. Catches a revision that improves the metrics but reads
    # worse. Blind side by side against the pinned best, A/B randomized.
    slug_pw = core_slug(Path(src).stem)
    db_pw = sqlite3.connect(DB_PATH)
    try:
        best_pw = _get_best_metrics(db_pw, slug_pw)
    finally:
        db_pw.close()
    pinned_render_path = None
    if best_pw and best_pw.get("path"):
        candidate_pinned_path = Path(best_pw["path"])
        # Only compare against a different version, and only if its .ans
        # still exists (it can be cleaned up after ship).
        if candidate_pinned_path.resolve() != Path(src).resolve() and candidate_pinned_path.exists():
            pinned_render_path = candidate_pinned_path
    intended_title_pw = _extract_intended_title(src)
    pairwise_result = opus_pairwise_regression_check(pinned_render_path, src, intended_title_pw)
    if pairwise_result["status"] == "regression":
        dest = _move_with_sidecars(src, REJECTED, new_critique=pairwise_result["message"])
        slug1 = core_slug(Path(src).stem)
        version1 = _extract_version(Path(src).stem)
        db1 = sqlite3.connect(DB_PATH)
        try:
            _touch_subject(db1, slug1, version1, src, status="rejected")
        finally:
            db1.close()
        return (
            f"rejected: moved to rejected/{dest.name} — "
            f"{pairwise_result['message']}"
        ), dest

    result = opus_curate_review(src, decision, critique)
    status = result["status"]

    slug = core_slug(Path(src).stem)
    version = _extract_version(Path(src).stem)

    def _sync_subject(new_status):
        db4 = sqlite3.connect(DB_PATH)
        try:
            _touch_subject(db4, slug, version, src, status=new_status)
        finally:
            db4.close()

    if status == "queued":
        return result["message"], None
    if status == "shelved":
        dest = _move_with_sidecars(src, SHELVED, new_critique=critique)
        _sync_subject("shelved")
        return result["message"] + f"\n\n(moved to shelved/{dest.name})", dest
    if status == "error":
        return result["message"], None
    if status == "accept":
        dest = _move_with_sidecars(src, PENDING, new_critique=critique)
        _sync_subject("accepted")
        agree = "" if decision == "accept" else " (Qwen's own read was REJECT — Opus overrode it)"
        halt = ""
        _db_tw = sqlite3.connect(DB_PATH)
        try:
            _db_tw.execute(
                "UPDATE piece_metrics SET accepted=1 WHERE slug=? AND id="
                "(SELECT MAX(id) FROM piece_metrics WHERE slug=?)",
                (core_slug(src.stem), core_slug(src.stem)),
            )
            _db_tw.commit()
            tw = _check_regression_tripwire(_db_tw)
            if tw:
                print(f"[tripwire] {tw}", flush=True)  # operator log, not the agents
                if os.environ.get("AGENTSCII_METRIC_HALT") == "1":
                    halt = f"\n\n{tw}"
        except Exception:
            pass
        finally:
            _db_tw.close()
        return (
            f"accepted: moved to pending/{dest.name}, awaiting manual "
            f"review before publication. Opus verdict: ACCEPT{agree}.\n\n{result['message']}{halt}"
        ), dest
    if status == "reject":
        # Two tiers: a piece can miss the scene bar and still clear the house
        # bar. Those ship labelled house-standard with the scene critique
        # attached. The scene bar is not lowered.
        if result.get("house_verdict") == "pass":
            dest = _move_with_sidecars(src, PENDING, new_critique=(
                "TIER: house-standard (shipped) / scene-standard: REJECT\n\n"
                "This piece clears the house bar -- a subject resolves, it is "
                "constructed rather than composited, and it carries no debug "
                "text or unrendered regions -- and does NOT clear the "
                "scene-standard bar calibrated against accepted 16colo.rs "
                "work. The full scene-standard critique follows and is "
                "published with the piece; nothing below is softened.\n\n"
                + (critique or "")))
            _sync_subject("accepted")
            return (
                f"accepted HOUSE-STANDARD: moved to pending/{dest.name}, "
                f"awaiting manual review. Scene-standard verdict: REJECT, "
                f"critique attached."
                f"\n\n{result['message']}"
            ), dest
        dest = _move_with_sidecars(src, REJECTED, new_critique=critique)
        _sync_subject("rejected")
        agree = "" if decision == "reject" else " (Qwen's own read was ACCEPT — Opus overrode it)"
        return (
            f"rejected: moved to rejected/{dest.name} with critique "
            f"attached. Opus verdict: REJECT{agree}, house: FAIL.\n\n{result['message']}"
        ), dest
    return f"(error: unexpected Opus review status {status!r})", None


def _shipped_catalog_index():
    """MD5 + core-slug index of every piece shipped in gallery/packNN/,
    excluding quarantine dirs (_held-*). Used to block duplicates at release."""
    import hashlib

    by_md5, by_slug = {}, {}
    for pack_dir in GALLERY.glob("pack*"):
        if not pack_dir.is_dir() or pack_dir.name.startswith("_held"):
            continue
        for f in pack_dir.glob("*.ans"):
            h = hashlib.md5(f.read_bytes()).hexdigest()
            by_md5.setdefault(h, []).append(str(f.relative_to(GALLERY)))
            slug = core_slug(f.stem)
            by_slug.setdefault(slug, []).append(str(f.relative_to(GALLERY)))
        for f in pack_dir.glob("*.asc"):
            h = hashlib.md5(f.read_bytes()).hexdigest()
            by_md5.setdefault(h, []).append(str(f.relative_to(GALLERY)))
    return by_md5, by_slug


def _opus_daily_cost_and_count(conn):
    """Today's Opus review count and cost (UTC day), for the daily cap.
    Check before calling Opus; on cap hit the caller queues, never falls
    back to Qwen."""
    import datetime
    day_start = datetime.datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0
    ).timestamp()
    row = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(opus_cost_usd), 0) FROM opus_reviews "
        "WHERE timestamp >= ? AND opus_verdict IS NOT NULL",
        (day_start,),
    ).fetchone()
    return row[0], row[1]


OPUS_DAILY_CALL_CAP = 40  # per UTC day
# A call-count cap, not a dollar cap: simpler to reason about and log.

OPUS_MAX_REVIEWS_PER_PIECE = 3  # reviews per piece before it is shelved


# --- claude child-process bookkeeping -------------------------------
# `claude` runs in its own process group so a timeout can kill the tree,
# which means it outlives a dead parent. Live groups are recorded in
# .claude_children/<pid>; atexit, SIGTERM/SIGHUP and any BaseException
# mid-call kill them. sweep_orphaned_claude() covers SIGKILL.
_CLAUDE_REG_DIR = PROJECT_DIR / ".claude_children"
_ACTIVE_CLAUDE = {}
_CLAUDE_CLEANUP_INSTALLED = False


def _claude_reg_save():
    try:
        _CLAUDE_REG_DIR.mkdir(exist_ok=True)
        p = _CLAUDE_REG_DIR / str(os.getpid())
        if _ACTIVE_CLAUDE:
            p.write_text("".join(f"{pg} {tag}\n" for pg, tag in _ACTIVE_CLAUDE.items()))
        elif p.exists():
            p.unlink()
    except OSError:
        pass


def _pg_alive(pg):
    try:
        os.killpg(pg, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _kill_pg(pg):
    import signal as _signal
    for sig, wait in ((_signal.SIGINT, 3.0), (_signal.SIGTERM, 3.0), (_signal.SIGKILL, 0.0)):
        try:
            os.killpg(pg, sig)
        except (ProcessLookupError, PermissionError):
            return
        t0 = time.time()
        while wait and time.time() - t0 < wait:
            if not _pg_alive(pg):
                return
            time.sleep(0.1)


def _kill_active_claude():
    for pg in list(_ACTIVE_CLAUDE):
        _kill_pg(pg)
        _ACTIVE_CLAUDE.pop(pg, None)
    _claude_reg_save()


def _install_claude_cleanup():
    global _CLAUDE_CLEANUP_INSTALLED
    if _CLAUDE_CLEANUP_INSTALLED:
        return
    _CLAUDE_CLEANUP_INSTALLED = True
    import atexit
    import signal as _signal
    atexit.register(_kill_active_claude)
    for sig in (_signal.SIGTERM, _signal.SIGHUP):
        prev = _signal.getsignal(sig)
        if prev not in (_signal.SIG_DFL, None):
            continue  # the harness's own graceful-stop handler stays in charge

        def _h(signum, frame, _sig=sig):
            _kill_active_claude()
            _signal.signal(_sig, _signal.SIG_DFL)
            os.kill(os.getpid(), _sig)
        try:
            _signal.signal(sig, _h)
        except ValueError:
            pass  # not the main thread


def sweep_orphaned_claude():
    """Kill claude groups recorded by agentscii processes that have died.
    Returns [(pgid, tag), ...] killed."""
    killed = []
    if not _CLAUDE_REG_DIR.exists():
        return killed
    for f in _CLAUDE_REG_DIR.iterdir():
        try:
            owner = int(f.name)
        except ValueError:
            continue
        if owner == os.getpid():
            continue
        try:
            os.kill(owner, 0)
            continue  # owner still running; its children are not orphans
        except ProcessLookupError:
            pass
        except PermissionError:
            continue
        for line in f.read_text().splitlines():
            pg, _, tag = line.partition(" ")
            if pg.isdigit() and _pg_alive(int(pg)):
                _kill_pg(int(pg))
                killed.append((int(pg), tag))
        try:
            f.unlink()
        except OSError:
            pass
    return killed


def live_claude_tags():
    """Tags of recorded claude groups that are alive, from any process."""
    tags = set()
    if _CLAUDE_REG_DIR.exists():
        for f in _CLAUDE_REG_DIR.iterdir():
            try:
                for line in f.read_text().splitlines():
                    pg, _, tag = line.partition(" ")
                    if pg.isdigit() and _pg_alive(int(pg)):
                        tags.add(tag)
            except OSError:
                pass
    return tags


# --- Sandbox for Opus sessions that get a shell ---------------------
# Opus artist runs get a pre-approved shell, so they go through
# sandbox-exec: writes limited to workspace/, .claude/, Claude state, temp
# and caches; SSH keys, Hermes config and gh/aws/docker credentials
# unreadable. The keychain stays reachable for the CLI login. Read-only
# judge calls aren't wrapped. AGENTSCII_OPUS_SANDBOX=0 opts out.
def _opus_sandbox_profile():
    h = str(HOME.resolve())

    def q(x):
        return '"' + x.replace("\\", "\\\\").replace('"', '\\"') + '"'

    writable = [str(WORKSPACE.resolve()), str((PROJECT_DIR / ".claude").resolve()),
                h + "/.claude", h + "/.local/share/claude", h + "/.local/state/claude",
                h + "/.cache", h + "/Library/Caches", h + "/Library/Logs",
                "/private/tmp", "/private/var/folders"]
    secrets = [".ssh", ".hermes", ".config/gh", ".aws", ".gnupg", ".docker",
               ".kube", "agentscii-private"]
    secret_files = [".netrc", ".git-credentials", ".npmrc", ".pypirc"]
    return "\n".join([
        "(version 1)",
        "(allow default)",
        "(deny file-write*)",
        "(allow file-write* " + " ".join(f"(subpath {q(w)})" for w in writable)
        + f' (regex #"^{h}/\\.claude\\.json") (regex #"^/dev/"))',
        "(deny file-read* file-write* "
        + " ".join(f"(subpath {q(h + '/' + d)})" for d in secrets)
        + " " + " ".join(f"(literal {q(h + '/' + f)})" for f in secret_files) + ")",
        LOOPBACK_DENY,
    ])


def _maybe_sandbox_claude(args_list):
    if os.environ.get("AGENTSCII_OPUS_SANDBOX") == "0":
        return args_list
    try:
        i = args_list.index("--allowedTools")
        tools = args_list[i + 1]
    except (ValueError, IndexError):
        return args_list
    if not re.search(r"\b(Bash|Write|Edit)\b", tools):
        return args_list
    return ["/usr/bin/sandbox-exec", "-p", _opus_sandbox_profile()] + list(args_list)


def _run_claude_p(args_list, timeout=120, retries=1, tag="claude", **run_kwargs):
    # The defect review needs several minutes; that call site passes
    # timeout=420.
    """Run `claude -p` with a hard timeout that actually kills it.

    subprocess.run(timeout=...) can hang when a grandchild inherits the
    pipes, so this starts a new session (start_new_session=True) and on
    timeout SIGKILLs the whole process group. Retries once. Always returns a
    CompletedProcess; failures have returncode -1 and the reason in stderr.
    """
    import subprocess as _sp
    import os as _os
    import signal as _signal

    def _fail(reason):
        # Never return bare None: carry the real reason in stderr with
        # returncode -1, so callers' `returncode != 0` branch logs it.
        return _sp.CompletedProcess(args_list, -1, "", reason)

    for attempt in range(retries + 1):
        try:
            proc = _sp.Popen(
                _maybe_sandbox_claude(args_list), stdout=_sp.PIPE, stderr=_sp.PIPE, text=True,
                start_new_session=True, **run_kwargs,
            )
        except Exception as e:
            return _fail(f"spawn failed: {type(e).__name__}: {e}")
        _install_claude_cleanup()
        try:
            _pg = _os.getpgid(proc.pid)
            _ACTIVE_CLAUDE[_pg] = tag
            _claude_reg_save()
        except OSError:
            _pg = None
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            return _sp.CompletedProcess(args_list, proc.returncode, stdout, stderr)
        except _sp.TimeoutExpired:
            try:
                _os.killpg(_os.getpgid(proc.pid), _signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                proc.communicate(timeout=5)
            except Exception:
                pass
            if attempt < retries:
                continue
            return _fail(
                f"timed out after {retries + 1} attempt(s) x {timeout}s "
                "(process group killed)"
            )
        except BaseException as e:
            # BaseException, so a KeyboardInterrupt doesn't leave the child
            # running.
            try:
                _os.killpg(_os.getpgid(proc.pid), _signal.SIGKILL)
            except Exception:
                pass
            if not isinstance(e, Exception):
                raise
            return _fail(f"{type(e).__name__}: {e}")
        finally:
            if _pg is not None:
                _ACTIVE_CLAUDE.pop(_pg, None)
                _claude_reg_save()
    return _fail("exhausted retries with no result")


def _kill_stale_claude_login(max_age_s=300):
    """Kill any `claude login` process older than max_age_s.

    A hung login holds ~/.claude/.credentials.lock and makes every
    `claude -p` fail with exit 1 and empty stderr. Younger processes are
    left alone in case a login is in progress. Returns True if one was
    killed.
    """
    import subprocess as _sp

    def _etime_to_seconds(s):
        # macOS `ps -eo etime` format: [[dd-]hh:]mm:ss. macOS has no `etimes`.
        days = 0
        if "-" in s:
            d, s = s.split("-", 1)
            days = int(d)
        parts = s.split(":")
        parts = [int(p) for p in parts]
        while len(parts) < 3:
            parts.insert(0, 0)
        h, m, sec = parts[-3:]
        return days * 86400 + h * 3600 + m * 60 + sec

    try:
        out = _sp.run(
            ["ps", "-eo", "pid,etime,command"],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except Exception:
        return False
    killed = False
    for line in out.splitlines()[1:]:
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        pid_s, etime_s, cmd = parts
        if "claude login" not in cmd:
            continue
        try:
            pid = int(pid_s)
            age = _etime_to_seconds(etime_s)
        except ValueError:
            continue
        if age >= max_age_s:
            try:
                os.kill(pid, signal.SIGTERM)
                killed = True
            except Exception:
                pass
    return killed


def _extract_intended_title(path, title=None):
    """The piece's declared title, for logging next to what Opus saw blind.
    Never fed to the blind check.

    Order: explicit argument, .note.txt sidecar, subjects table, then the
    in-file title card.
    """
    if title:
        return title.strip()

    slug = core_slug(Path(path).stem)

    # The sig-block title row is what the artist actually wrote. Scan all
    # rows; the title can sit in a framed row near the bottom.
    try:
        text = _decode_ans_bytes(Path(path).read_bytes())
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        cands = []
        for line in lines:
            clean = _SGR_RE.sub("", line).strip().strip("\u2550\u2580\u2584\u2588 ")
            if not (3 <= len(clean) <= 60):
                continue
            alpha = sum(1 for ch in clean if ch.isascii() and ch.isalpha())
            if alpha < 3 or alpha / len(clean) < 0.5:
                continue
            if "AGENTSCII" in clean.upper() or "/" in clean:
                continue  # credit line, not the title
            cands.append(" ".join(clean.split()))
        if cands:
            # the title card is normally the shortest all-caps line
            caps = [c for c in cands if c.upper() == c]
            return (caps or cands)[0]
    except Exception:
        pass

    try:
        db = sqlite3.connect(DB_PATH)
        row = db.execute("SELECT slug FROM subjects WHERE slug=?", (slug,)).fetchone()
        db.close()
        if row:
            return row[0].lstrip("_").replace("_", " ").upper()
    except Exception:
        pass

    return None


def opus_subject_check(path, title=None):
    """Blind subject check: show Opus the render with title rows redacted,
    ask what it depicts, then whether that matches the intended title.

    Separate from the defect review so the answer isn't primed by it.
    Returns {"status": "ok"|"mismatch"|"error"|"disabled", "message",
    "blind_subject", "intended_title"}. No title to compare against counts
    as "ok"; only a confirmed mismatch rejects.

    Off unless AGENTSCII_SUBJECT_CHECK=1, gated here so every caller
    (harness, opus_duo, opus_session, pipeline_test) gets the same answer.
    "disabled" is its own status: a deliberately-off check is neither a pass
    nor a refusal.
    """
    if not SUBJECT_CHECK_ENABLED:
        return {"status": "disabled",
                "message": "(subject check off: AGENTSCII_SUBJECT_CHECK != 1)",
                "blind_subject": None, "intended_title": None}
    import subprocess, json, tempfile, shutil, base64

    intended_title = _extract_intended_title(path, title)

    # This gate makes up to 2 Opus calls, so it counts against the same
    # daily cap as opus_curate_review.
    conn_cap = sqlite3.connect(DB_PATH)
    try:
        count_today, cost_today = _opus_daily_cost_and_count(conn_cap)
        if count_today >= OPUS_DAILY_CALL_CAP:
            return {
                "status": "ok",  # don't hard-block submission on this gate
                # Cap hit: skip this check. opus_curate_review's own cap check
                # queues the piece.
                "message": f"(subject check skipped: Opus daily cap "
                            f"reached, {count_today}/{OPUS_DAILY_CALL_CAP})",
                "blind_subject": None, "intended_title": intended_title,
            }
    finally:
        conn_cap.close()

    slug_for_log = Path(path).stem

    b64, note = render_ans_to_png_b64(path, offset=0, max_rows=140, redact_title_rows=True)
    if b64 is None:
        return {"status": "error", "message": f"(render failed: {note})",
                "blind_subject": None, "intended_title": intended_title}

    tmpdir = tempfile.mkdtemp(prefix="opus_subject_")
    try:
        render_path = Path(tmpdir) / "render.png"
        render_path.write_bytes(base64.b64decode(b64))

        prompt = (
            "Read render.png in this directory. You have NO other context "
            "about this image at all -- no title, no artist's description, "
            "no intent. Look only at what is literally drawn.\n\n"
            "Answer in this exact format:\n"
            "SUBJECT: <one short phrase, 2-8 words, naming the literal "
            "subject, or \"abstract/no clear subject\" if there genuinely "
            "is none>\n"
            "DESCRIPTION: <one or two sentences of what you actually see>"
        )

        result = _run_claude_p(
            ["claude", "-p", prompt, "--model", OPUS_MODEL,
             "--allowedTools", "Read", "--output-format", "json"],
            cwd=tmpdir,
        )
        if result is None:
            return {"status": "error", "message": "(subject check call timed out after retry)",
                    "blind_subject": None, "intended_title": intended_title}
        if result.returncode != 0 and result.returncode == 1 and not result.stderr.strip():
            # same stuck-login auto-heal as opus_curate_review
            if _kill_stale_claude_login(max_age_s=300):
                result = _run_claude_p(
                    ["claude", "-p", prompt, "--model", OPUS_MODEL,
                     "--allowedTools", "Read", "--output-format", "json"],
                    cwd=tmpdir,
                )
                if result is None:
                    return {"status": "error", "message": "(subject check call timed out after retry)",
                            "blind_subject": None, "intended_title": intended_title}
        if result.returncode != 0:
            err = f"claude CLI exit {result.returncode}: {result.stderr[:500]}"
            return {"status": "error", "message": f"(subject check call failed: {err})",
                    "blind_subject": None, "intended_title": intended_title}

        data = json.loads(result.stdout)
        reasoning = data.get("result", "")
        cost1 = data.get("total_cost_usd")

        # Log cost to opus_reviews so the daily cap sees it; qwen_decision
        # 'subject_check' marks it as not a defect review.
        conn_log = sqlite3.connect(DB_PATH)
        try:
            conn_log.execute(
                "INSERT INTO opus_reviews (piece_slug, path, qwen_decision, "
                "qwen_critique, opus_verdict, opus_reasoning, opus_cost_usd, "
                "opus_error, timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
                (slug_for_log, str(path), "subject_check", None,
                 "n/a_subject_id", reasoning, cost1, None, time.time()),
            )
            conn_log.commit()
        finally:
            conn_log.close()

        blind_subject = None
        for line in reasoning.splitlines():
            if line.strip().upper().startswith("SUBJECT:"):
                blind_subject = line.split(":", 1)[1].strip()
                break

        if blind_subject is None:
            return {"status": "error",
                    "message": "(subject check returned no parseable SUBJECT line)",
                    "blind_subject": None, "intended_title": intended_title}

        if intended_title is None:
            # No title found: nothing to compare against.
            return {"status": "ok",
                    "message": f"(blind read: \"{blind_subject}\" -- no in-file "
                                "title found to compare against, so this check "
                                "has nothing to judge a mismatch against)",
                    "blind_subject": blind_subject, "intended_title": None}

        # Separate call: does the blind subject match the title? Needs
        # judgment (an eye is a watcher; a plain ring isn't), not string overlap.
        match_prompt = (
            f"An artist intended to draw: \"{intended_title}\"\n"
            f"An independent blind viewer, shown ONLY the rendered image "
            f"with no title, described the subject as: \"{blind_subject}\"\n\n"
            "Does the blind description plausibly match what the artist "
            "intended (allowing for stylized/conceptual titles -- e.g. "
            "\"THE WATCHER\" matching a description of an eye is a MATCH, "
            "not a mismatch), or does it read as a genuinely different "
            "subject than intended?\n\n"
            "Answer in this exact format:\n"
            "VERDICT: MATCH or VERDICT: MISMATCH\n"
            "REASON: <one sentence>"
        )
        match_result = _run_claude_p(
            ["claude", "-p", match_prompt, "--model", OPUS_MODEL,
             "--output-format", "json"],
        )
        if match_result is None:
            return {"status": "error",
                    "message": "(subject-match judgment call timed out after retry)",
                    "blind_subject": blind_subject, "intended_title": intended_title}
        if match_result.returncode != 0:
            return {"status": "error",
                    "message": f"(subject-match judgment call failed: exit {match_result.returncode})",
                    "blind_subject": blind_subject, "intended_title": intended_title}
        match_data = json.loads(match_result.stdout)
        match_reasoning = match_data.get("result", "")
        cost2 = match_data.get("total_cost_usd")

        conn_log2 = sqlite3.connect(DB_PATH)
        try:
            conn_log2.execute(
                "INSERT INTO opus_reviews (piece_slug, path, qwen_decision, "
                "qwen_critique, opus_verdict, opus_reasoning, opus_cost_usd, "
                "opus_error, timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
                (slug_for_log, str(path), "subject_check", None,
                 "n/a_subject_match", match_reasoning, cost2, None, time.time()),
            )
            conn_log2.commit()
        finally:
            conn_log2.close()

        verdict = None
        for line in match_reasoning.splitlines():
            if line.strip().upper().startswith("VERDICT:"):
                v = line.split(":", 1)[1].strip().upper()
                verdict = "match" if "MATCH" in v and "MISMATCH" not in v else "mismatch"
                break

        if verdict == "mismatch":
            return {
                "status": "mismatch",
                "message": (
                    f"BLIND SUBJECT CHECK FAILED: the artist intended "
                    f"\"{intended_title}\", but an independent blind viewer "
                    f"(no title, no note, no filename) described the "
                    f"rendered image as: \"{blind_subject}\". "
                    f"{match_reasoning.strip()} This is a hard reject "
                    "regardless of any metric floor being met -- the "
                    "gates measure technique, not whether the piece "
                    "actually reads as its intended subject."
                ),
                "blind_subject": blind_subject, "intended_title": intended_title,
            }

        return {
            "status": "ok",
            "message": f"blind subject check passed: intended \"{intended_title}\", "
                        f"blind read \"{blind_subject}\" -- {match_reasoning.strip()}",
            "blind_subject": blind_subject, "intended_title": intended_title,
        }
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def render_blind_pairwise_b64(path_a, path_b, offset=0, max_rows=140):
    """Render two pieces side by side, titles redacted, labeled only A and B
    so the model can't defer to the established version."""
    from PIL import Image, ImageDraw, ImageFont

    a_b64, a_note = render_ans_to_png_b64(path_a, offset=offset, max_rows=max_rows, redact_title_rows=True)
    if a_b64 is None:
        return None, f"(error rendering A: {a_note})"
    b_b64, b_note = render_ans_to_png_b64(path_b, offset=offset, max_rows=max_rows, redact_title_rows=True)
    if b_b64 is None:
        return None, f"(error rendering B: {b_note})"

    a_img = Image.open(io.BytesIO(base64.b64decode(a_b64))).convert("RGB")
    b_img = Image.open(io.BytesIO(base64.b64decode(b_b64))).convert("RGB")

    label_h = 28
    gap = 6
    h = max(a_img.height, b_img.height) + label_h
    w = a_img.width + gap + b_img.width
    canvas = Image.new("RGB", (w, h), (20, 20, 20))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(_FONT_PATH, 18)
    except Exception:
        font = ImageFont.load_default()

    draw.text((4, 4), "A", font=font, fill=(255, 255, 0))
    draw.text((a_img.width + gap + 4, 4), "B", font=font, fill=(0, 255, 255))
    canvas.paste(a_img, (0, label_h))
    canvas.paste(b_img, (a_img.width + gap, label_h))
    draw.rectangle([a_img.width + gap // 2 - 1, 0, a_img.width + gap // 2, h], fill=(80, 80, 80))

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    out_b64 = base64.b64encode(buf.getvalue()).decode()
    note = ""
    if a_note or b_note:
        note = f" (A{a_note or ' full'}, B{b_note or ' full'})"
    return out_b64, note


def opus_pairwise_regression_check(pinned_path, candidate_path, intended_title):
    """Blind pairwise gate: does the candidate read better or worse than the
    pinned best as the stated subject? Rejects a loss even when metrics
    improved. A/B sides are randomized.

    Returns {"status": "ok"|"regression"|"error", "message"}. No pinned
    baseline counts as "ok"."""
    import subprocess, json, tempfile, shutil, base64, random

    if pinned_path is None:
        return {"status": "ok", "message": "(no pinned version yet to compare against)"}

    conn_cap = sqlite3.connect(DB_PATH)
    try:
        count_today, cost_today = _opus_daily_cost_and_count(conn_cap)
        if count_today >= OPUS_DAILY_CALL_CAP:
            return {"status": "ok",
                    "message": f"(pairwise check skipped: Opus daily cap reached, "
                                f"{count_today}/{OPUS_DAILY_CALL_CAP})"}
    finally:
        conn_cap.close()

    pinned_is_a = random.random() < 0.5
    path_a = pinned_path if pinned_is_a else candidate_path
    path_b = candidate_path if pinned_is_a else pinned_path

    b64, note = render_blind_pairwise_b64(path_a, path_b)
    if b64 is None:
        return {"status": "error", "message": f"(render failed: {note})"}

    tmpdir = tempfile.mkdtemp(prefix="opus_pairwise_")
    try:
        render_path = Path(tmpdir) / "compare.png"
        render_path.write_bytes(base64.b64decode(b64))

        title_line = (
            f"The stated subject for both is: \"{intended_title}\"\n\n"
            if intended_title else ""
        )
        prompt = (
            "Read compare.png in this directory. It shows two ANSI-art "
            "renders side by side, labeled A and B. You have NO other "
            "context -- no titles, no notes, no version history, no "
            "indication of which is older or newer.\n\n"
            f"{title_line}"
            "Which one reads better AS THAT SUBJECT -- clearer form, "
            "better lit, less noisy, more coherent as the stated "
            "subject? This is about which one actually looks better, "
            "not which one is more technically complex.\n\n"
            "Answer in this exact format:\n"
            "WINNER: A or WINNER: B or WINNER: TIE\n"
            "REASON: <2-3 sentences, specific to what you see in each>"
        )

        result = _run_claude_p(
            ["claude", "-p", prompt, "--model", OPUS_MODEL,
             "--allowedTools", "Read", "--output-format", "json"],
            cwd=tmpdir,
        )
        if result is None:
            return {"status": "error", "message": "(pairwise check call timed out after retry)"}
        if result.returncode != 0 and result.returncode == 1 and not result.stderr.strip():
            if _kill_stale_claude_login(max_age_s=300):
                result = _run_claude_p(
                    ["claude", "-p", prompt, "--model", OPUS_MODEL,
                     "--allowedTools", "Read", "--output-format", "json"],
                    cwd=tmpdir,
                )
                if result is None:
                    return {"status": "error", "message": "(pairwise check call timed out after retry)"}
        if result.returncode != 0:
            err = f"claude CLI exit {result.returncode}: {result.stderr[:500]}"
            return {"status": "error", "message": f"(pairwise check call failed: {err})"}

        data = json.loads(result.stdout)
        reasoning = data.get("result", "")
        cost = data.get("total_cost_usd")

        slug_for_log = Path(candidate_path).stem
        conn_log = sqlite3.connect(DB_PATH)
        try:
            conn_log.execute(
                "INSERT INTO opus_reviews (piece_slug, path, qwen_decision, "
                "qwen_critique, opus_verdict, opus_reasoning, opus_cost_usd, "
                "opus_error, timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
                (slug_for_log, str(candidate_path), "pairwise_check", None,
                 "n/a_pairwise", reasoning, cost, None, time.time()),
            )
            conn_log.commit()
        finally:
            conn_log.close()

        winner_side = None
        for line in reasoning.splitlines():
            if line.strip().upper().startswith("WINNER:"):
                w = line.split(":", 1)[1].strip().upper()
                if w.startswith("A"):
                    winner_side = "A"
                elif w.startswith("B"):
                    winner_side = "B"
                else:
                    winner_side = "TIE"
                break

        if winner_side is None:
            return {"status": "error",
                    "message": "(pairwise check returned no parseable WINNER line)"}

        pinned_won = (winner_side == "A" and pinned_is_a) or (winner_side == "B" and not pinned_is_a)

        if pinned_won:
            return {
                "status": "regression",
                "message": (
                    f"PAIRWISE REGRESSION CHECK FAILED: shown blind side-by-side "
                    f"(randomized A/B, no titles/versions visible), an independent "
                    f"reviewer judged the PINNED BEST version to read better as "
                    f"\"{intended_title}\" than this candidate, even if this "
                    f"candidate's tracked metrics are equal or higher. "
                    f"{reasoning.strip()} This is a hard reject -- a metric floor "
                    "being satisfied is not the same as the piece actually "
                    "looking better; revert to the pinned version or make a "
                    "change that a blind viewer would actually prefer."
                ),
            }

        return {
            "status": "ok",
            "message": f"pairwise check passed: candidate judged equal-or-better "
                        f"than the pinned best. {reasoning.strip()}",
        }
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _looks_like_title_line(line):
    """Same test as render_ans_to_png_b64's redact_title_rows, on plain text."""
    vis = [ch for ch in line if ch != " "]
    if len(vis) < 8:
        return False
    letters = sum(1 for ch in vis if ch.isascii() and ch.isalpha())
    run = best = 0
    for ch in line:
        if ch.isascii() and (ch.isalpha() or ch in "/-.,!'"):
            run += 1
            best = max(best, run)
        else:
            run = 0
    return letters / len(vis) > 0.5 or best >= 6


def opus_curate_review(path, qwen_decision, qwen_critique):
    """Opus accept/reject review for curate_piece.

    Opus gets render, crops and cell dump, never the note, script or title.
    When the daily call cap is exhausted, submissions queue; there is no
    fallback to Qwen. One re-review per revision, shelved after three
    rejections. Qwen's verdict is logged alongside.

    Returns {"status": "accept"|"reject"|"queued"|"shelved"|"error",
    "message": str, "opus_verdict": str|None}.
    """
    import subprocess, json, tempfile, shutil, base64, datetime

    slug = Path(path).stem
    conn = sqlite3.connect(DB_PATH)
    try:
        count_today, cost_today = _opus_daily_cost_and_count(conn)
        if count_today >= OPUS_DAILY_CALL_CAP:
            return {
                "status": "queued",
                "message": (
                    f"(Opus daily cap reached: {count_today}/{OPUS_DAILY_CALL_CAP} "
                    f"calls, ${cost_today:.2f} spent today. This submission is "
                    "QUEUED, not auto-decided — it will not fall back to Qwen for "
                    "the accept/reject call. Try again after the cap resets "
                    "(UTC midnight), or ask the human to raise OPUS_DAILY_CALL_CAP.)"
                ),
                "opus_verdict": None,
            }

        prior_reviews = conn.execute(
            "SELECT COUNT(*) FROM opus_reviews WHERE piece_slug=? "
            "AND qwen_decision NOT IN ('subject_check', 'pairwise_check') "
            "AND opus_verdict IS NOT NULL", (slug,)
        ).fetchone()[0]
        if prior_reviews >= OPUS_MAX_REVIEWS_PER_PIECE:
            return {
                "status": "shelved",
                "message": (
                    f"(this piece ('{slug}') has already had "
                    f"{prior_reviews} Opus reviews, the maximum allowed. "
                    "Per house policy it is SHELVED, not resubmitted again — "
                    "move it to a new file/slug if you want to try a genuinely "
                    "different approach, don't keep resubmitting the same "
                    "revision chain.)"
                ),
                "opus_verdict": None,
            }

        # Opus sees only the render and cell dump: no note, script, title or
        # path. Title/credit rows are dropped from both, same test as the blind
        # subject check.
        b64, note = render_ans_to_png_b64(path, offset=0, max_rows=140, redact_title_rows=True)
        if b64 is None:
            return {"status": "error", "message": f"(render failed: {note})", "opus_verdict": None}

        tmpdir = tempfile.mkdtemp(prefix="opus_gate_")
        try:
            render_path = Path(tmpdir) / "render.png"
            render_path.write_bytes(base64.b64decode(b64))
            raw = Path(path).read_bytes()
            text = _decode_ans_bytes(raw).replace("\r\n", "\n").replace("\r", "\n")
            cells_text = "\n".join(("" if _looks_like_title_line(l2) else l2)
                                   for l2 in (_SGR_RE.sub("", l) for l in text.split("\n")[:140]))
            (Path(tmpdir) / "cells.txt").write_text(cells_text)
            # The reviewer has only Read and can't crop; give it the four
            # quarters at 2x.
            try:
                from PIL import Image
                im = Image.open(render_path)
                W, H = im.size
                for qi, (x0, y0) in enumerate(((0, 0), (W // 2, 0), (0, H // 2), (W // 2, H // 2)), 1):
                    q = im.crop((x0, y0, x0 + W // 2, y0 + H // 2))
                    q.resize((q.width * 2, q.height * 2), Image.NEAREST).save(Path(tmpdir) / f"zoom_{qi}.png")
            except Exception:
                pass

            prompt = (
                "Read render.png and cells.txt in this directory. zoom_1.png to "
                "zoom_4.png are the four quarters (top-left, top-right, "
                "bottom-left, bottom-right) at 2x; Read them when you need "
                "cell-level detail. Title and credit rows have been blanked. "
                "You have NO "
                "other context about this image — no title, no artist's "
                "description, no intent. Look only at what is actually there.\n\n"
                "Answer plainly and skeptically:\n"
                "1. Describe literally what you see — shapes, colors, any "
                "recognizable subject or lack thereof.\n"
                "2. List concrete defects, with approximate row/column "
                "coordinates from cells.txt where relevant (banding, flat "
                "unshaded regions, broken silhouette, placeholder/debug text, "
                "illegible construction, anything that reads as unfinished "
                "or wrong).\n"
                "3. Give a final verdict: ACCEPT or REJECT, on one line at "
                "the very end, formatted exactly as: VERDICT: ACCEPT or "
                "VERDICT: REJECT.\n\n"
                "Be skeptical. If it looks unfinished, flat, or like a "
                "geometric placeholder rather than a real constructed "
                "piece, say so and reject it, even if the character data "
                "shows some structure.\n\n"
                "4. Then give a SECOND, independent verdict against a "
                "LOWER bar, on its own line immediately after the first, "
                "formatted exactly as: HOUSE: PASS or HOUSE: FAIL.\n"
                "The house bar asks only three things, and nothing else:\n"
                "  (a) does a subject actually resolve — can a viewer say "
                "what this is a picture of;\n"
                "  (b) is it CONSTRUCTED rather than composited — is there "
                "real drawn form somewhere in it, not only fills and "
                "stamps;\n"
                "  (c) is it free of debug text, placeholder strings and "
                "wholly unrendered regions.\n"
                "A piece can be genuinely unfinished and still PASS the "
                "house bar. Judge (a)-(c) on their own terms; do NOT "
                "let your ACCEPT/REJECT verdict above decide it."
            )

            result = _run_claude_p(
                ["claude", "-p", prompt, "--model", OPUS_MODEL,
                 "--allowedTools", "Read", "--output-format", "json"],
                cwd=tmpdir, timeout=420,
            )
            if result is not None and result.returncode != 0:
                # A stuck `claude login` holds ~/.claude/.credentials.lock and
                # makes `claude -p` exit 1 with empty stderr. Kill it, retry once.
                if result.returncode == 1 and not result.stderr.strip():
                    stale_login_killed = _kill_stale_claude_login(
                        max_age_s=300
                    )
                    if stale_login_killed:
                        result = _run_claude_p(
                            ["claude", "-p", prompt, "--model", OPUS_MODEL,
                             "--allowedTools", "Read", "--output-format", "json"],
                            cwd=tmpdir, timeout=420,
                        )
            if result is None:
                # _run_claude_p already retried once. Record as unjudged rather
                # than block the shift on a third attempt.
                err = "claude -p timed out after retry (120s x2, process group killed)"
                conn.execute(
                    "INSERT INTO opus_reviews (piece_slug, path, qwen_decision, "
                    "qwen_critique, opus_verdict, opus_reasoning, opus_cost_usd, "
                    "opus_error, timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
                    (slug, str(path), qwen_decision, qwen_critique, None, None,
                     None, err, time.time()),
                )
                conn.commit()
                return {"status": "error", "message": f"(Opus review call failed: {err})", "opus_verdict": None}
            if result.returncode != 0:
                err = f"claude CLI exit {result.returncode}: {result.stderr[:500]}"
                if result.returncode == 1 and not result.stderr.strip():
                    err += (
                        " (empty stderr on exit 1 usually means a stuck "
                        "`claude login` process is holding "
                        "~/.claude/.credentials.lock -- check `ps aux | "
                        "grep 'claude login'` and kill it; auto-heal already "
                        "attempted and did not clear it)"
                    )
                conn.execute(
                    "INSERT INTO opus_reviews (piece_slug, path, qwen_decision, "
                    "qwen_critique, opus_verdict, opus_reasoning, opus_cost_usd, "
                    "opus_error, timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
                    (slug, str(path), qwen_decision, qwen_critique, None, None,
                     None, err, time.time()),
                )
                conn.commit()
                return {"status": "error", "message": f"(Opus review call failed: {err})", "opus_verdict": None}

            data = json.loads(result.stdout)
            reasoning = data.get("result", "")
            cost = data.get("total_cost_usd")

            verdict = None
            for line in reasoning.splitlines():
                if line.strip().upper().startswith("VERDICT:"):
                    v = line.split(":", 1)[1].strip().upper()
                    if "ACCEPT" in v:
                        verdict = "accept"
                    elif "REJECT" in v:
                        verdict = "reject"
                    break

            # House verdict comes from a structured field, not a keyword scan: a
            # reviewer discussing a defect uses the same words as one finding it.
            house = None
            for line in reasoning.splitlines():
                if line.strip().upper().startswith("HOUSE:"):
                    h = line.split(":", 1)[1].strip().upper()
                    if "PASS" in h:
                        house = "pass"
                    elif "FAIL" in h:
                        house = "fail"
                    break

            # Log Qwen's verdict next to Opus's so the disagreement rate is
            # measurable.
            conn.execute(
                "INSERT INTO opus_reviews (piece_slug, path, qwen_decision, "
                "qwen_critique, opus_verdict, opus_reasoning, opus_cost_usd, "
                "opus_error, timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
                (slug, str(path), qwen_decision, qwen_critique, verdict,
                 reasoning, cost, None if verdict else "no VERDICT line found",
                 time.time()),
            )
            conn.commit()

            if verdict is None:
                return {
                    "status": "error",
                    "message": "(Opus review returned no parseable VERDICT line — treat as unresolved, do not accept.)",
                    "opus_verdict": None,
                }

            return {
                "status": verdict,
                "message": reasoning,
                "opus_verdict": verdict,
                "house_verdict": house,
            }
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    finally:
        conn.close()


def _blind_visual_check(path):
    """Describe the rendered piece with no access to any curator or artist
    claim about it, to catch critiques that describe detail the render
    doesn't have. Returns the description, or an error string; treat an
    error as "couldn't verify", not success.
    """
    b64, note = render_ans_to_png_b64(path, offset=0, max_rows=140)
    if b64 is None:
        return f"(blind check could not render: {note})"
    prompt = (
        "Look at this image ONLY. You have no other context about what it is "
        "supposed to be — do not assume artistic intent. Answer plainly and "
        "skeptically:\n"
        "1. Does the image show clearly discernible constructed features "
        "(a face, eye, brow, jaw, profile, recognizable figure/anatomy) built "
        "from real shading or gradient structure — or is it flat solid-color "
        "geometric shapes (blocks, bars, triangles, stripes) with no such "
        "features?\n"
        "2. Describe literally what shapes and colors you see, in one or two "
        "plain sentences, with no assumption of artistic intent.\n"
        "Be skeptical — if it looks like flat colored shapes stacked together "
        "rather than a constructed feature, say so plainly, even if a label "
        "or title in the image suggests otherwise."
    )
    messages = [
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]},
    ]
    try:
        resp = call_ollama(MODEL, messages, [])
        return resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"(blind check model call failed: {e})"


# Words that make a critique's claim checkable by the blind visual pass.
# The extra model call only fires when one appears.
_VISUAL_CLAIM_WORDS = (
    "face", "eye", "brow", "jaw", "profile", "anatomy", "anatomical",
    "figure", "figurative", "portrait", "silhouette", "expression",
)


def do_release_pack(pack_note):
    """Bundle gallery/unpacked/ into the next gallery/packNN/ with a
    FILE_ID.DIZ crediting every contributor. Returns (result, pack_dir|None).

    Any piece byte-identical to something already shipped blocks the whole
    release."""
    GALLERY_UNPACKED.mkdir(parents=True, exist_ok=True)
    pieces = [
        f for f in sorted(GALLERY_UNPACKED.iterdir())
        if f.is_file() and not f.name.endswith((".note.txt", ".critique.txt", ".credits.txt"))
    ]
    if not pieces:
        return "(error: gallery/unpacked/ is empty, nothing to release)", None

    import hashlib
    by_md5, by_slug = _shipped_catalog_index()
    dup_hits = []
    for piece in pieces:
        h = hashlib.md5(piece.read_bytes()).hexdigest()
        if h in by_md5:
            dup_hits.append(f"{piece.name} is byte-identical to already-shipped {by_md5[h][0]}")
    if dup_hits:
        return (
            "(error: release BLOCKED — one or more pieces in unpacked/ are exact "
            "duplicates of already-shipped work: " + "; ".join(dup_hits) + ". "
            "Move the duplicate(s) out of unpacked/ — e.g. into a "
            "gallery/_held-already-shipped/ audit dir with a short note — then "
            "retry release_pack with the remaining genuinely-new pieces.)"
        ), None

    existing = [d for d in GALLERY.glob("pack*") if d.is_dir()]
    nums = []
    for d in existing:
        m = re.match(r"pack(\d+)$", d.name)
        if m:
            nums.append(int(m.group(1)))
    next_num = (max(nums) + 1) if nums else 1
    pack_dir = GALLERY / f"pack{next_num:02d}"
    pack_dir.mkdir(parents=True, exist_ok=False)

    lines = [
        f"AGENTSCII pack{next_num:02d}",
        f"released {date.today().isoformat()}",
        "",
        pack_note.strip(),
        "",
        "--- contents ---",
        "",
    ]
    for piece in pieces:
        note_src, critique_src, credits_src = _sidecar_paths(piece)
        moved = piece.rename(pack_dir / piece.name)
        entry = [f"* {piece.name}"]
        if credits_src.exists():
            entry.append(f"  credits: {credits_src.read_text().strip()}")
            credits_src.rename(pack_dir / credits_src.name)
        if note_src.exists():
            entry.append(f"  artist note: {note_src.read_text().strip()}")
            note_src.rename(pack_dir / note_src.name)
        if critique_src.exists():
            entry.append(f"  curator note: {critique_src.read_text().strip()}")
            critique_src.rename(pack_dir / critique_src.name)
        lines.extend(entry)
        lines.append("")

    (pack_dir / "FILE_ID.DIZ").write_text("\n".join(lines))
    return f"released pack{next_num:02d} with {len(pieces)} piece(s)", pack_dir


def get_pending_agent_messages(conn, agent, mark_delivered=True):
    rows = conn.execute(
        "SELECT id, from_agent, text, timestamp FROM agent_messages WHERE to_agent=? AND delivered=0 ORDER BY id",
        (agent,),
    ).fetchall()
    if rows and mark_delivered:
        conn.execute("UPDATE agent_messages SET delivered=1 WHERE to_agent=? AND delivered=0", (agent,))
        conn.commit()
    return rows


def get_pending_human_messages(conn, agent, mark_delivered=True):
    rows = conn.execute(
        "SELECT id, text, timestamp FROM human_messages WHERE (to_agent=? OR to_agent='both') AND delivered=0 ORDER BY id",
        (agent,),
    ).fetchall()
    if rows and mark_delivered:
        ids = [r[0] for r in rows]
        conn.executemany("UPDATE human_messages SET delivered=1 WHERE id=?", [(i,) for i in ids])
        conn.commit()
    return rows


def get_last_own_shift_note(conn, agent):
    row = conn.execute(
        "SELECT note, last_reasoning FROM shifts WHERE agent=? AND ended_at IS NOT NULL AND note != '' "
        "ORDER BY id DESC LIMIT 1",
        (agent,),
    ).fetchone()
    if not row or not row[0]:
        return None
    note, last_reasoning = row
    if last_reasoning:
        return (
            f"{note}\n\nYour own last reasoning right before that forced end "
            f"(this is your in-progress diagnosis/plan — pick up from here, "
            f"don't start over from scratch): {last_reasoning}"
        )
    return note


def run_shift(conn, agent):
    cfg = AGENTS[agent]
    started_at = time.time()

    pending_peer = get_pending_agent_messages(conn, agent, mark_delivered=False)
    pending_human = get_pending_human_messages(conn, agent, mark_delivered=False)

    peer_seat = "curator" if agent == "artist" else "artist"
    own_handle = get_handle(conn, agent)
    peer_handle = get_handle(conn, peer_seat)

    msg_note = ""
    if own_handle:
        msg_note += f"\n\nYour handle: {own_handle}."
    else:
        msg_note += (
            "\n\nYou haven't chosen a handle yet. Real BBS-scene artists "
            "went by a handle, not a generic role label — pick one for "
            "yourself with set_handle before anything else this shift. It's "
            "yours; make it fit the scene."
        )
    msg_note += f" Your collaborator goes by {peer_handle}." if peer_handle else " Your collaborator hasn't chosen a handle yet either."

    if pending_peer:
        msg_note += "\n\nMessages from your collaborator since your last shift:\n" + "\n".join(
            f"- {m[2]}" for m in pending_peer
        )
    if pending_human:
        msg_note += "\n\nMessages from the operator (the human directing this project) since your last shift:\n" + "\n".join(
            f"- {m[1]}" for m in pending_human
        )

    last_note = get_last_own_shift_note(conn, agent)
    if last_note:
        msg_note += f"\n\nWhat you were doing at the end of your own last shift: {last_note}"

    messages = [
        {"role": "system", "content": cfg["soul"] + msg_note},
        {"role": "user", "content": "[harness] Your shift has started. Nobody is waiting on a reply."},
    ]

    backoff = 2
    while not stop_requested():
        try:
            resp = call_ollama(cfg["model"], messages, TOOLS)
            break
        except Exception as e:
            print(f"[{agent}] ollama unreachable ({e}), retrying in {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
    else:
        return

    if pending_peer:
        conn.execute("UPDATE agent_messages SET delivered=1 WHERE to_agent=? AND delivered=0", (agent,))
    if pending_human:
        ids = [m[0] for m in pending_human]
        conn.executemany("UPDATE human_messages SET delivered=1 WHERE id=?", [(i,) for i in ids])
    conn.commit()

    cur = conn.execute("INSERT INTO shifts (agent, started_at) VALUES (?,?)", (agent, started_at))
    conn.commit()
    shift_id = cur.lastrowid

    print(f"\n=== {agent} shift {shift_id} starting ===")
    log_event(conn, agent, shift_id, "system", cfg["soul"] + msg_note)

    note = ""
    shift_failed = False
    last_reasoning = ""
    had_pending_final = None
    replied_final = None
    wants_continue = False
    empty_turns = 0
    recent_calls = []
    max_calls_this_shift = MAX_TOOL_CALLS_BY_ROLE.get(agent, MAX_TOOL_CALLS_PER_SHIFT)
    for i in range(max_calls_this_shift):
        if stop_requested():
            note = "(stopped by harness shutdown request, mid-shift)"
            print(f"[{agent}] stop requested mid-shift, wrapping up now")
            break
        # Wall-clock cap: the stall detector can't see a shift making novel
        # calls that never converge.
        if time.time() - started_at > SHIFT_WALL_CLOCK_CAP_S:
            note = (
                f"(wall-clock cap hit: shift ran over "
                f"{SHIFT_WALL_CLOCK_CAP_S/60:.0f} minutes, forced checkpoint)"
            )
            print(f"[{agent}] wall-clock cap hit ({(time.time()-started_at)/60:.1f}min), forcing checkpoint")
            break
        if i > 0:
            try:
                resp = call_ollama(cfg["model"], messages, TOOLS)
            except Exception as e:
                print(f"[error] ollama call failed: {e}")
                log_event(conn, agent, shift_id, "error", str(e))
                # Record the failure so the next shift doesn't resume from an
                # older note.
                note = f"(shift cut short: model call failed: {str(e)[:200]})"
                shift_failed = True
                break

        choice = resp.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content", "") or ""
        reasoning = msg.get("reasoning", "") or ""
        tool_calls = msg.get("tool_calls") or []

        if reasoning.strip():
            log_event(conn, agent, shift_id, "assistant", reasoning=reasoning.strip())
            print(f"[{agent}] thinks: {reasoning.strip()[:200]}")
            last_reasoning = reasoning.strip()

        if content.strip():
            log_event(conn, agent, shift_id, "assistant", content.strip())
            print(f"[{agent}] says: {content.strip()[:200]}")

        messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls or None})

        if not tool_calls:
            if content.strip():
                # A text-only reply ends the shift. Record it so the next
                # shift picks up from here, not from an older note.
                note = "(ended with a text reply, no end_shift): " + content.strip()[:600]
                break
            empty_turns += 1
            if empty_turns >= 3:
                note = "(gave up after 3 empty turns with no action)"
                break
            messages.append({"role": "user", "content": "[harness] Continue — what do you want to do?"})
            continue

        ended = False
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name")
            try:
                fargs = json.loads(fn.get("arguments") or "{}")
            except Exception:
                fargs = {}

            log_event(conn, agent, shift_id, "assistant", None, tool_name=name,
                      tool_args=json.dumps(fargs), tool_call_id=tc.get("id"))
            print(f"[{agent}] tool: {name}({fargs})")

            # Mark canvas writes made through the agent's own tools, so
            # save_canvas can separate them from a script writing the canvas.
            try:
                import canvas_tools as _ct
                _ct.WRITER = "tool" if str(name).startswith("canvas_") else None
            except Exception:
                pass

            if name == "message_agent":
                other = "curator" if agent == "artist" else "artist"
                conn.execute(
                    "INSERT INTO agent_messages (from_agent, to_agent, text, timestamp) VALUES (?,?,?,?)",
                    (agent, other, fargs.get("text", ""), time.time()),
                )
                conn.commit()
                result = f"message sent to {other}"
            elif name == "set_handle":
                handle = (fargs.get("handle") or "").strip()
                if not handle:
                    result = "(error: handle cannot be empty)"
                else:
                    conn.execute(
                        "INSERT INTO agent_identity (seat, handle, timestamp) VALUES (?,?,?) "
                        "ON CONFLICT(seat) DO UPDATE SET handle=excluded.handle, timestamp=excluded.timestamp",
                        (agent, handle, time.time()),
                    )
                    conn.commit()
                    result = f"handle set: you're now known as '{handle}'"
            elif name == "submit_piece":
                result = run_tool(name, fargs, agent, shift_id=shift_id)
                if isinstance(result, str) and result.startswith("submitted:"):
                    conn.execute(
                        "INSERT INTO curation_events (shift_id, action, path, dest_path, note, timestamp) VALUES (?,?,?,?,?,?)",
                        (shift_id, "submit", fargs.get("path", ""), None, fargs.get("note", ""), time.time()),
                    )
                    conn.commit()
            elif name == "curate_piece":
                out = run_tool(name, fargs, agent, shift_id=shift_id)
                result, dest = out if isinstance(out, tuple) else (out, None)
                if dest is not None:
                    # The logged action must match where the file actually
                    # went. An accept that the blind subject check or the
                    # pairwise gate overturns lands in rejected/ while
                    # fargs["decision"] still says "accept" -- that mismatch
                    # made curation_events unreadable against disk.
                    decision = fargs.get("decision", "")
                    action = decision
                    if decision == "accept" and dest.parent.name == "rejected":
                        action = "override_reject"
                    conn.execute(
                        "INSERT INTO curation_events (shift_id, action, path, dest_path, note, timestamp) VALUES (?,?,?,?,?,?)",
                        (shift_id, action, fargs.get("path", ""), str(dest.relative_to(WORKSPACE)),
                         (f"[override_reject: curator said accept; gate moved it to "
                          f"rejected/] {result}\n\n{fargs.get('critique', '')}"
                          if action == "override_reject" else fargs.get("critique", "")),
                         time.time()),
                    )
                    conn.commit()
            elif name == "canvas_new":
                try:
                    import canvas_tools as ct
                    data = ct.new_canvas(str(WORKSPACE), fargs.get("slug", ""),
                                          fargs.get("width", 80), fargs.get("height", 40),
                                          bg=fargs.get("bg", 0) or 0)
                    result = (f"canvas '{fargs.get('slug')}' created, {data['w']}x{data['h_cells']} "
                              f"cells ({data['w']}x{data['ph']} pixels). Draw with canvas_fill_px/"
                              "canvas_circle_px/canvas_shade/canvas_text/canvas_stamp, check with "
                              "canvas_preview, finish with canvas_save.")
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_fill_px":
                try:
                    import canvas_tools as ct
                    ct.fill_px(str(WORKSPACE), fargs.get("slug", ""), fargs.get("x", 0),
                               fargs.get("y", 0), fargs.get("w", 0), fargs.get("h", 0),
                               fargs.get("color", 0))
                    result = f"filled ({fargs.get('x')},{fargs.get('y')}) {fargs.get('w')}x{fargs.get('h')}px on '{fargs.get('slug')}'."
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_circle_px":
                try:
                    import canvas_tools as ct
                    ct.circle_px(str(WORKSPACE), fargs.get("slug", ""), fargs.get("cx", 0),
                                 fargs.get("cy", 0), fargs.get("r", 1), fargs.get("color", 0))
                    result = f"drew circle at ({fargs.get('cx')},{fargs.get('cy')}) r={fargs.get('r')} on '{fargs.get('slug')}'."
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_shade":
                try:
                    import canvas_tools as ct
                    region = fargs.get("region")  # optional; None -> last drawn shape
                    ct.shade(str(WORKSPACE), fargs.get("slug", ""), fargs.get("from_color", 15),
                             fargs.get("to_color", 0), fargs.get("light_direction", "top"), region=region)
                    region_desc = "last drawn shape" if region is None else region
                    result = (f"shaded {region_desc} on '{fargs.get('slug')}' from "
                              f"{fargs.get('from_color')}->{fargs.get('to_color')}, "
                              f"light from {fargs.get('light_direction')}.")
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_sphere_px":
                try:
                    import canvas_tools as ct
                    ct.sphere_px(str(WORKSPACE), fargs.get("slug", ""), fargs.get("cx", 0),
                                 fargs.get("cy", 0), fargs.get("r", 1), fargs.get("color", 15),
                                 fargs.get("light_x", 0), fargs.get("light_y", 0),
                                 shadow_color=fargs.get("shadow_color"))
                    result = (f"drew lit sphere at ({fargs.get('cx')},{fargs.get('cy')}) r={fargs.get('r')} "
                              f"on '{fargs.get('slug')}', light from ({fargs.get('light_x')},{fargs.get('light_y')}).")
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_slab_px":
                try:
                    import canvas_tools as ct
                    ct.slab_px(str(WORKSPACE), fargs.get("slug", ""), fargs.get("x", 0),
                               fargs.get("y", 0), fargs.get("w", 1), fargs.get("h", 1),
                               fargs.get("color", 15),
                               light_direction=fargs.get("light_direction", "top-left") or "top-left",
                               shadow_color=fargs.get("shadow_color"),
                               hi_color=fargs.get("hi_color"),
                               side=fargs.get("side"), side_w=fargs.get("side_w", 0) or 0)
                    result = (f"drew lit slab at ({fargs.get('x')},{fargs.get('y')}) "
                              f"{fargs.get('w')}x{fargs.get('h')} on '{fargs.get('slug')}'.")
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_capsule_px":
                try:
                    import canvas_tools as ct
                    ct.capsule_px(str(WORKSPACE), fargs.get("slug", ""), fargs.get("ax", 0),
                                  fargs.get("ay", 0), fargs.get("bx", 0), fargs.get("by", 0),
                                  fargs.get("r", 1), fargs.get("color", 15),
                                  light_direction=fargs.get("light_direction", "top-left") or "top-left",
                                  shadow_color=fargs.get("shadow_color"),
                                  hi_color=fargs.get("hi_color"))
                    result = (f"drew lit capsule ({fargs.get('ax')},{fargs.get('ay')})->"
                              f"({fargs.get('bx')},{fargs.get('by')}) r={fargs.get('r')} on '{fargs.get('slug')}'.")
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_metrics":
                try:
                    import canvas_tools as ct
                    m = ct.metrics(str(WORKSPACE), fargs.get("slug", ""))
                    result = (
                        f"canvas '{fargs.get('slug')}': {_fmt_metrics(m)}. "
                        "These detect absence (no half-blocks, one flat mass); "
                        "they are not targets and nothing compares them to a bar."
                    )
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_crop":
                try:
                    import canvas_tools as ct
                    b64, dump = ct.crop(str(WORKSPACE), fargs.get("slug", ""),
                                        int(fargs.get("x", 0)), int(fargs.get("y", 0)),
                                        int(fargs.get("w", 12)), int(fargs.get("h", 10)),
                                        scale=int(fargs.get("scale", 6) or 6))
                    log_event(conn, agent, shift_id, "tool", dump[:400], tool_name=name, tool_call_id=tc.get("id"))
                    messages.append({
                        "role": "tool", "tool_call_id": tc.get("id"),
                        "content": [
                            {"type": "text", "text": dump},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        ],
                    })
                    continue
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_self_check":
                try:
                    import canvas_tools as ct
                    g_b64, c_b64, density = ct.self_check(str(WORKSPACE), fargs.get("slug", ""))
                    txt = ("GLYPHS-ONLY (all one colour) first, then COLOUR-ONLY (every glyph a "
                           "solid block). If the colour-only render still reads as your subject, "
                           "the colour is carrying the picture and the glyphs are decoration -- "
                           "that is the rejection 'remove the color and nothing survives'. If the "
                           "glyphs-only render still reads, the density is doing real work.\n\n"
                           + density)
                    log_event(conn, agent, shift_id, "tool", txt[:400], tool_name=name, tool_call_id=tc.get("id"))
                    messages.append({
                        "role": "tool", "tool_call_id": tc.get("id"),
                        "content": [
                            {"type": "text", "text": txt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{g_b64}"}},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{c_b64}"}},
                        ],
                    })
                    continue
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_wordmark":
                try:
                    import canvas_tools as ct
                    _, width = ct.wordmark(str(WORKSPACE), fargs.get("slug", ""), fargs.get("x", 0),
                                            fargs.get("y", 0), fargs.get("text", ""), fargs.get("fg", 15),
                                            scale=fargs.get("scale", 2) or 2)
                    result = f"drew wordmark {fargs.get('text')!r} on '{fargs.get('slug')}', used {width}px wide."
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_mirror":
                try:
                    import canvas_tools as ct
                    ct.mirror(str(WORKSPACE), fargs.get("slug", ""), axis=fargs.get("axis", "v") or "v")
                    result = f"mirrored '{fargs.get('slug')}' on axis={fargs.get('axis', 'v')}."
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_strand_shade":
                try:
                    import canvas_tools as ct
                    region = fargs.get("region") or [0, 0, 0, 0]
                    ct.strand_shade(str(WORKSPACE), fargs.get("slug", ""),
                                     region={"type": "rect", "x0": region[0], "y0": region[1], "x1": region[2], "y1": region[3]},
                                     direction=fargs.get("direction", [0, 1]),
                                     fg_list=fargs.get("colors", [15, 7]),
                                     n_strands=fargs.get("n_strands", 40) or 40,
                                     length=fargs.get("length", 6) or 6)
                    result = f"applied strand shading to region {region} on '{fargs.get('slug')}'."
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_text":
                try:
                    import canvas_tools as ct
                    ct.text(str(WORKSPACE), fargs.get("slug", ""), fargs.get("x", 0),
                            fargs.get("y", 0), fargs.get("text", ""), fargs.get("fg", 7),
                            fargs.get("bg", 0))
                    result = f"placed text {fargs.get('text')!r} at ({fargs.get('x')},{fargs.get('y')}) on '{fargs.get('slug')}'."
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_cells":
                try:
                    import canvas_tools as ct
                    placed, errs = ct.cells(str(WORKSPACE), fargs.get("slug", ""), fargs.get("cells") or [])
                    result = f"wrote {placed} cell(s) on '{fargs.get('slug')}'."
                    if errs:
                        result += f" {len(errs)} rejected: " + "; ".join(errs[:5])
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_stamp":
                try:
                    import canvas_tools as ct
                    corpus_dir = str(PROJECT_DIR / "corpus")
                    if corpus_dir not in sys.path:
                        sys.path.insert(0, corpus_dir)
                    from find_patches import decode_patch_id, _load_patch_grids
                    parent_path, row_off, col_off, w_rows, w_cols = decode_patch_id(fargs.get("patch_id", ""))
                    grids = _load_patch_grids(parent_path, row_off, col_off, w_rows, w_cols)
                    if grids is None:
                        result = f"(error: could not load patch data for {parent_path})"
                    else:
                        chars, fg, bg = grids
                        _, placed = ct.stamp(str(WORKSPACE), fargs.get("slug", ""),
                                              fargs.get("x", 0), fargs.get("y", 0), chars, fg, bg)
                        result = f"stamped {placed} cells from {Path(parent_path).name} onto '{fargs.get('slug')}' at ({fargs.get('x')},{fargs.get('y')})."
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_save":
                try:
                    import canvas_tools as ct
                    out_path = ct.save_ans(str(WORKSPACE), fargs.get("slug", ""), fargs.get("path", ""),
                                            title=fargs.get("title"), handles=fargs.get("handles", "AGENTSCII"))
                    result = f"saved '{fargs.get('slug')}' to {out_path.relative_to(WORKSPACE)}."
                except Exception as e:
                    result = f"(error: {e})"
            elif name == "canvas_preview":
                try:
                    offset = max(0, int(fargs.get("offset", 0) or 0))
                    rows = fargs.get("rows", 200) or 200
                    rows = max(1, min(int(rows), 200))
                    b64, note_or_err = render_canvas_to_png_b64(str(WORKSPACE), fargs.get("slug", ""),
                                                                 offset=offset, max_rows=rows)
                    if b64 is None:
                        result = note_or_err
                    else:
                        result = f"rendered canvas '{fargs.get('slug')}' rows {offset}-{offset+rows}{note_or_err} — see image."
                        log_event(conn, agent, shift_id, "tool", result, tool_name=name, tool_call_id=tc.get("id"))
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.get("id"),
                            "content": [
                                {"type": "text", "text": result},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                            ],
                        })
                        continue
                except Exception as e:
                    result = f"(error rendering canvas preview: {e})"
            elif name == "preview_piece":
                try:
                    p = _resolve_workspace_path(fargs.get("path", ""))
                    if not p.exists():
                        result = f"(error: {p} does not exist)"
                    else:
                        offset = max(0, int(fargs.get("offset", 0) or 0))
                        rows = fargs.get("rows", 120) or 120
                        rows = max(1, min(int(rows), 200))
                        b64, note_or_err = render_ans_to_png_b64(p, offset=offset, max_rows=rows)
                        if b64 is None:
                            result = note_or_err
                        else:
                            result = f"rendered {p.name} rows {offset}-{offset+rows}{note_or_err} — see image."
                            log_event(conn, agent, shift_id, "tool", result, tool_name=name, tool_call_id=tc.get("id"))
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.get("id"),
                                "content": [
                                    {"type": "text", "text": result},
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                                ],
                            })
                            continue
                except Exception as e:
                    result = f"(error rendering preview: {e})"
            elif name == "find_patches":
                try:
                    description = (fargs.get("description") or "").strip()
                    if not description:
                        result = "(error: description is required)"
                    else:
                        n = max(1, min(int(fargs.get("n", 3) or 3), 6))
                        half_block_min = fargs.get("half_block_min")
                        shade_min = fargs.get("shade_min")
                        corpus_dir = str(PROJECT_DIR / "corpus")
                        if corpus_dir not in sys.path:
                            sys.path.insert(0, corpus_dir)
                        try:
                            from find_patches_clip import find_patches_clip
                            hits = find_patches_clip(
                                description, n=n, index_dir=str(PROJECT_DIR / "corpus" / "clip_index"),
                                half_block_min=half_block_min, shade_min=shade_min,
                            )
                            method = "CLIP visual-embedding"
                        except FileNotFoundError:
                            # clip_index not built yet -- degrade to the
                            # keyword/technique fallback rather than error out
                            from find_patches import find_patches as find_patches_kw
                            hits = find_patches_kw(description, n=n)
                            method = "keyword/technique (CLIP index unavailable)"
                        if not hits:
                            result = f"(no patches found for {description!r})"
                        else:
                            b64, note_or_err = render_patches_grid_b64(hits)
                            if b64 is None:
                                result = note_or_err
                            else:
                                # Return cell data (RLE + patch_id) with each hit so the
                                # artist can study it or place it with
                                # canvas_stamp(patch_id, x, y).
                                detail_lines = []
                                for h in hits:
                                    detail_lines.append(
                                        f"--- {Path(h['parent_path']).name} "
                                        f"(patch_id={h['patch_id']}, half_block={h.get('half_block_pct', 0):.0f}%, "
                                        f"shade={h.get('shade_pct', 0):.0f}%) ---\n"
                                        f"{h.get('rle_text') or '(rle encode failed)'}"
                                    )
                                result = (
                                    f"{len(hits)} patches found for {description!r} via {method}{note_or_err} — "
                                    "see image. Each is a real 40x16-cell window from a real archive piece, "
                                    "not synthetic. Study the technique, don't copy the piece verbatim. "
                                    "canvas_stamp(patch_id, x, y) places one's exact real cells directly onto "
                                    "a canvas.\n\n" + "\n\n".join(detail_lines)
                                )
                                log_event(conn, agent, shift_id, "tool", result, tool_name=name, tool_call_id=tc.get("id"))
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tc.get("id"),
                                    "content": [
                                        {"type": "text", "text": result},
                                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                                    ],
                                })
                                continue
                except Exception as e:
                    result = f"(error searching patches: {e})"
            elif name == "compare_to_reference":
                try:
                    piece_p = _resolve_workspace_path(fargs.get("piece_path", ""))
                    ref_p = _resolve_workspace_path(fargs.get("reference_path", ""))
                    if not piece_p.exists():
                        result = f"(error: {piece_p} does not exist)"
                    elif not ref_p.exists():
                        result = f"(error: {ref_p} does not exist — check references/study/ for real filenames)"
                    else:
                        offset = max(0, int(fargs.get("offset", 0) or 0))
                        rows = fargs.get("rows", 60) or 60
                        rows = max(1, min(int(rows), 90))
                        b64, note_or_err = render_comparison_b64(piece_p, ref_p, offset=offset, max_rows=rows)
                        if b64 is None:
                            result = note_or_err
                        else:
                            result = (
                                f"side-by-side rendered: {piece_p.name} vs {ref_p.name}{note_or_err} — "
                                "see image. Yellow label = your piece (left), cyan label = reference (right). "
                                "Look at density, contrast, edge treatment, highlight placement directly against "
                                "the reference, not from memory of what you intended to build."
                            )
                            log_event(conn, agent, shift_id, "tool", result, tool_name=name, tool_call_id=tc.get("id"))
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.get("id"),
                                "content": [
                                    {"type": "text", "text": result},
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                                ],
                            })
                            continue
                except Exception as e:
                    result = f"(error rendering comparison: {e})"
            elif name == "release_pack":
                if agent != "curator":
                    result = "(error: only the curator seat can release_pack)"
                else:
                    result, pack_dir = do_release_pack(fargs.get("pack_note", ""))
                    if pack_dir is not None:
                        conn.execute(
                            "INSERT INTO curation_events (shift_id, action, path, dest_path, note, timestamp) VALUES (?,?,?,?,?,?)",
                            (shift_id, "release_pack", str(pack_dir.relative_to(WORKSPACE)), None, fargs.get("pack_note", ""), time.time()),
                        )
                        conn.commit()
            elif name == "end_shift":
                note = fargs.get("note", "")
                had_pending = fargs.get("had_pending_peer_message")
                replied = fargs.get("replied_to_peer")
                if had_pending and not replied:
                    result = (
                        "end_shift rejected: you indicated a collaborator message was pending "
                        "but replied_to_peer=false. Either use message_agent to reply, "
                        "or call end_shift again with a note explaining why you're "
                        "deliberately not responding."
                    )
                    log_event(conn, agent, shift_id, "tool", result, tool_name=name, tool_call_id=tc.get("id"))
                    messages.append({"role": "tool", "tool_call_id": tc.get("id"), "content": result})
                    continue
                result = "shift ended"
                ended = True
                had_pending_final = had_pending
                replied_final = replied
                wants_continue = bool(fargs.get("continue_same_agent"))
            else:
                result = run_tool(name, fargs, agent, shift_id=shift_id)

            log_event(conn, agent, shift_id, "tool", result, tool_name=name, tool_call_id=tc.get("id"))
            messages.append({"role": "tool", "tool_call_id": tc.get("id"), "content": result})

            # --- stall detection ---------------------------------------------
            # Fingerprint = (tool name, sha256 of the full raw args). A stall counts
            # only when both the call and its result match an earlier entry this
            # shift. Truncated or digit-normalized args would collapse distinct work.
            call_fp = hashlib.sha256(
                (name + "\x00" + json.dumps(fargs, sort_keys=True, default=str)).encode("utf-8", "replace")
            ).hexdigest()
            result_fp = hashlib.sha256(
                str(result).encode("utf-8", "replace")
            ).hexdigest()
            full_sig = (call_fp, result_fp)
            recent_calls.append((name, full_sig))
            recent_calls = recent_calls[-40:]  # generous window -- cheap to keep, no truncation risk
            repeat_count = sum(1 for n, s in recent_calls if n == name and s == full_sig)
            if repeat_count >= 3:
                prior = [
                    f"{n}: {json.dumps(fargs, default=str)[:200]}"
                    for n, s in recent_calls[-6:]
                ]
                print(
                    f"[{agent}] STALL DETECTED (log-only, not ending shift): "
                    f"'{name}' produced the IDENTICAL call+result {repeat_count}x this shift. "
                    f"Last 5 calls before this one: {prior[-6:-1]}"
                )
                log_event(
                    conn, agent, shift_id, "system",
                    f"[harness: stall detected (log-only) — '{name}' called with identical "
                    f"arguments and got the identical result {repeat_count}x this shift. Per-role "
                    "tool-call caps remain the real backstop; this is not ending the shift.]",
                    tool_name=name,
                )
                # Log-only; MAX_TOOL_CALLS_BY_ROLE is the backstop.

        if ended:
            break
    else:
        note = "(hit max tool calls for this shift, forced handoff)"
        # Save open canvases before handoff so an interrupted shift leaves a
        # coherent .ans.
        try:
            import canvas_tools as _ct
            # Only canvases touched this shift; saving all of them revives
            # closed subjects as fresh-looking autosaves.
            _touched = [
                s_ for s_ in _ct.list_canvases(str(WORKSPACE))
                if _ct._canvas_path(str(WORKSPACE), s_).stat().st_mtime >= started_at
            ]
            for _slug in _touched:
                try:
                    # No extra underscore: the slug already carries the house
                    # prefix, and a second one groups as a separate piece.
                    _ct.save_ans(str(WORKSPACE), _slug,
                                 f"scratch/{_slug}.autosave.ans",
                                 title=None, add_sig=False)
                except Exception:
                    pass
            note += " [open canvases auto-saved]"
        except Exception:
            pass

    ended_at = time.time()
    # Save last_reasoning on a forced end (non-empty note) so an in-progress
    # diagnosis carries into the next shift. A clean end_shift has its own note.
    conn.execute(
        "UPDATE shifts SET ended_at=?, note=?, had_pending_peer_message=?, "
        "replied_to_peer=?, last_reasoning=? WHERE id=?",
        (ended_at, note, had_pending_final, replied_final,
         (last_reasoning[-2000:] if last_reasoning else last_reasoning) if note else None, shift_id),
    )
    conn.commit()
    _record_shift_tool_summary(conn, shift_id)
    print(f"=== {agent} shift {shift_id} ended ({ended_at - started_at:.1f}s): {note} ===")
    return wants_continue, shift_failed


def main():
    conn = init_db()
    for d in (WORKSPACE, GALLERY, GALLERY_UNPACKED, PENDING, SUBMISSIONS, SCRATCH, REJECTED, REFERENCES):
        d.mkdir(parents=True, exist_ok=True)
    if not (WORKSPACE / "README.md").exists():
        (WORKSPACE / "README.md").write_text(
            "AGENTSCII shared workspace.\n\n"
            "scratch/            shared WIP, no quality bar, no ownership\n"
            "submissions/        artist seat's finished work awaiting curator review\n"
            "gallery/unpacked/   accepted, pending the next pack release\n"
            "gallery/packNN/     shipped releases with FILE_ID.DIZ credits\n"
            "rejected/           sent back with a .critique.txt sidecar; not deleted\n"
            "references/         real ANSI study material\n"
            "STYLE.md            house style spec\n"
        )
    ref_note = REFERENCES / "what_is_ansi_art.txt"
    if not ref_note.exists():
        src = HOME / "antfarm2" / "references" / "what_is_ansi_art.txt"
        if src.exists():
            ref_note.write_text(src.read_text())

    STOP_FLAG.unlink(missing_ok=True)
    for pg, tag in sweep_orphaned_claude():
        print(f"[harness] killed orphaned claude process group {pg} ({tag})", flush=True)
    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)

    current = "artist"
    MAX_CONSECUTIVE_SHIFTS = 3
    consecutive = 0
    print("AGENTSCII harness starting. Ctrl+C, SIGTERM, or "
          f"'touch {STOP_FLAG}' to stop cleanly after the current turn.")
    failed = False
    try:
        while not stop_requested():
            if consecutive == 0:
                other_model = AGENTS["curator" if current == "artist" else "artist"]["model"]
                if other_model != MODEL:
                    unload_model(other_model)
            wants_continue, shift_failed = run_shift(conn, current)
            if shift_failed:
                # A shift that died on an unhandled error must NOT look
                # like a clean stop: the watchdog plist uses
                # SuccessfulExit=false, so exiting 0 here left the agents
                # down until the next reboot. Exit nonzero and let launchd
                # restart us (ThrottleInterval caps the retry rate).
                failed = True
                break
            consecutive += 1
            if wants_continue and consecutive < MAX_CONSECUTIVE_SHIFTS:
                pass
            else:
                current = "curator" if current == "artist" else "artist"
                consecutive = 0
            time.sleep(0.5)
    finally:
        print("[harness] Shutting down: unloading model and closing DB...")
        unload_model(MODEL)
        conn.close()
        # Don't unlink STOP_FLAG: the watchdog reads it to exit instead of
        # restarting. Whoever set the flag (the dashboard) clears it.
        print("[harness] Stopped cleanly." if not failed else
              "[harness] Exiting nonzero after a failed shift so launchd restarts us.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
