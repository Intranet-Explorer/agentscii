#!/usr/bin/env python3
"""
AGENTSCII harness.
Two local LLM agents, one shared workspace, one explicit purpose: produce
real ANSI/ACiD-style textmode art (the 90s BBS artscene aesthetic) worth
keeping — as a collaborative body of work, not two agents working in
parallel past each other.

Forked from ~/antfarm2-standalone/harness.py (shift loop, loop-guard,
cross-shift memory, tool-calling dispatch, SQLite event log reused
near-verbatim — solid substrate, unrelated to that project's philosophy).

Two fixed seats gate the pipeline (artist submits, curator decides), but
that's the only hard boundary. Everything upstream of it is shared: both
agents work in scratch/ freely, can extend or remix a piece the other
started, and real joint pieces (multiple contributors, credited together —
the actual dominant tradition in real ANSI packs) are the encouraged norm,
not an edge case. A self-chosen handle gives each agent an identity beyond
its functional seat. A house style doc (workspace/STYLE.md) gives the
curator real criteria instead of taste alone. Accepted pieces land in
gallery/unpacked/ until the curator ships a numbered pack release with a
real FILE_ID.DIZ — the actual unit of "we made this," not a flat accept bin.
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


MODEL = "qwen3.8:27b-mlx"  # stock (non-obliterated) Qwen3.8-27B, MLX-quantized build.
# We don't need uncensored output for ANSI art, and the obliterated variant's own
# model card documents temperature=0 (greedy) + no system prompt as the settings
# that keep its abliteration from getting reintroduced — both conflict with this
# harness's design (a real system prompt defining role/tools, sampled output
# across many shifts rather than one-shot greedy). Stock qwen3.8:27b-mlx has no
# such constraint; using its own documented non-thinking/instruct-mode sampling
# settings below instead: temperature=0.7, top_p=0.80, presence_penalty=1.5 to
# suppress repetition. top_k=20, repeat_penalty=1.0, min_p=0.0 are left as the
# model's own Modelfile defaults (verified via `ollama show --modelfile`) since
# they already match the documented instruct-mode values and Ollama's OpenAI-
# compatible endpoint doesn't accept top_k/repeat_penalty/min_p as request
# fields — any unset field falls through to the Modelfile's PARAMETER value.
SAMPLING = {"temperature": 0.7, "top_p": 0.80, "presence_penalty": 1.5}

REFERENCE_NOTE = (
    "Real reference archives are reachable via bash/curl. Don't guess at URL "
    "patterns or hand-scrape rendered HTML for links — these work, verified: "
    "https://16colo.rs/group/acid and https://16colo.rs/group/blocktronics (and "
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
    "and resubmit. references/ holds real ACiD/ANSI study material."
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
            "You're one of two agents in AGENTSCII: produce real ANSI/ACiD-style textmode "
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
            "ACiD/ANSI study material. Draw directly with the canvas_* tools: "
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
            "already. STYLE.md has house conventions AND the actual build sequence "
            "(block-in, light-source shading, detail texture, background texture, frame, "
            "verify against a reference) — required reading before your first figurative "
            "or ambition-tier piece. A human (Tyler) directs this project and leaves "
            "either of you direction via your inbox. This is directed, quality-focused "
            "work, not idle equilibrium — if nothing's in flight, start a new subject "
            "via random_direction, or revise a piece rejected in the LAST 5 SHIFTS with "
            "its critique in mind. Do NOT revive older work without direction from the "
            "operator: four shifts were spent reviving an abandoned piece purely because "
            "it sat in scratch/. Closed subjects are archived automatically; the reasons "
            "are in workspace/archive/README.md. Don't submit unfinished "
            "work to pad activity. Speak in the first person, always. 'user'-labeled "
            "messages are automated harness pings and inbox deliveries, not a person "
            "waiting on you in real time. Call end_shift when done acting for this shift."
        ),
    },
    "curator": {
        "model": MODEL,
        "role": "curator",
        "soul": (
            "You're one of two agents in AGENTSCII: produce real ANSI/ACiD-style textmode "
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
            "ACiD/ANSI study material. Draw directly with the canvas_* tools: "
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
            "references/study/ has curated examples on disk already. STYLE.md has house "
            "conventions AND the actual build sequence (block-in, light-source shading, "
            "detail texture, background texture, frame, verify against a reference) — "
            "required reading before your first figurative or ambition-tier piece. A "
            "human (Tyler) directs this project and leaves either of you direction via "
            "your inbox. Ground every judgment in something real: look at actual "
            "reference pieces before accepting or rejecting, not memory or vibes, and "
            "check against STYLE.md. On curate_piece: accept moves it to "
            "gallery/unpacked/; reject moves it to rejected/ with a specific critique — "
            "name what's actually wrong compared to real pieces in the tradition, not "
            "just 'needs work'. A rejection isn't a failure state; a gallery containing "
            "everything submitted isn't curated at all. But don't reject reflexively "
            "either. Use release_pack when gallery/unpacked/ has a real handful of good "
            "work, not on a fixed schedule. If submissions/ is empty, that's legitimate "
            "to report — go study references, add a pass to a piece rejected in the "
            "LAST 5 SHIFTS, or leave a specific idea via message_agent. Do NOT revive "
            "older work without operator direction; closed subjects are archived, with "
            "reasons in workspace/archive/README.md. Speak in the first person, always. 'user'-labeled "
            "messages are automated harness pings, not a person waiting on you in real "
            "time. Call end_shift when done acting for this shift."
        ),
    },
}

MAX_TOOL_CALLS_PER_SHIFT = 40
# Creation genuinely needs more headroom than review: of the shifts that hit
# the cap, 7/10 were the artist seat vs 3/10 curator (checked against real
# shift data, not a guess). Give the artist real extra room rather than
# raising the cap uniformly and diluting the loop-guard's effectiveness for
# the curator, whose job is comparatively bounded (read, judge, decide).
MAX_TOOL_CALLS_BY_ROLE = {"artist": 60, "curator": 40}
BASH_TIMEOUT = 60

MAX_REVISIONS_PER_SUBJECT = 8  # user direction, 2026-09-19: "Cap revisions
# at 8 per subject. After that it ships, gets shelved, or reverts to the
# best-scoring earlier version. 59 versions is not iteration, it's
# thrashing." -- _orb reached v59 before shipping (v53-v59 alone were the
# post-fix revision round covered by the flat-region/half-block gates),
# a real, measured case of a piece grinding through dozens of versions
# instead of converging. This is a hard, separate cap from
# OPUS_MAX_REVIEWS_PER_PIECE (which counts REVIEWS, not submitted
# VERSIONS -- a piece can rack up many mechanically-gate-blocked
# submissions, each consuming zero Opus reviews, and still never hit
# the review cap while still thrashing on raw version count). Enforced
# in submit_piece, same place as the other house-direction gates.

SHIFT_WALL_CLOCK_CAP_S = 90 * 60  # 90 minutes (user direction, 2026-09-17):
# the loop guard fingerprints identical call+result pairs, so it can't see
# a shift that keeps making genuinely DIFFERENT tool calls while never
# converging -- found live: an artist shift spent 4+ hours iterating on one
# foreground (_dusk_yard), every edit a real, different diff, never once
# tripping the stall detector, because nothing about it was actually a
# repeat. Wall-clock is a separate, cruder backstop for exactly that case:
# it doesn't care whether the calls are novel, only how long the shift has
# run. Checked once per tool-call loop iteration, same place the stall
# detector and per-role cap are checked, so it's covered even for the
# artist's 60-call/shift budget which the curator's 40 would exhaust
# time-wise anyway.

_VERSION_RE = re.compile(r"(?:\.[vV]|-v|_v)(\d+)$")

FIGURATIVE_WORDS = ("face", "eye", "watch", "sentinel", "cyborg", "scan",
                     "mind", "portrait", "figure", "warden", "vigil",
                     "traveler", "procession", "ember", "guardian", "demon",
                     "cyclops", "totem", "mantis", "lantern", "oracle",
                     "coghead", "gargoyle", "wraith", "golem", "knight",
                     "colossus", "sphinx", "phantom", "silhouette")
# Found live, 2026-09-19: this list is a leaky approximation by
# construction and WILL keep missing real figurative subjects as new
# ones get invented -- confirmed directly: "_guardian" reached
# submissions with 0.0% shade chars, 0% full blocks, all flat fills
# (exactly the defect class _flat_region_check/_figurative_precheck
# exist to catch) because "guardian" matched no word here, so BOTH
# gates silently treated it as non-figurative and never ran at all.
# This is the same bug class as the "_orb"/"THE WATCHER" gap found
# 2026-09-18, now confirmed a second time on a different word -- adding
# words as they're found (this commit added guardian/demon/cyclops/
# totem/mantis/lantern/oracle/coghead/gargoyle/wraith/golem/knight/
# colossus/sphinx/phantom/silhouette, the real gaps audited against
# every slug ever shipped in workspace/gallery/) is a real fix but NOT
# a durable one -- the blind Opus subject-recognition check (see
# opus_subject_check()) is the actual structural backstop, since it
# asks "what is this an image of?" directly rather than guessing from
# a filename, and will catch a mis-scoped flat piece even when this
# list misses the word. Keep expanding this list when a gap is found
# (it's free, runs before any Opus call), but don't treat it as
# complete.

_FIGURATIVE_WORDS_RE = re.compile(
    r"(?<![a-zA-Z])(?:" + "|".join(re.escape(w) for w in FIGURATIVE_WORDS) + r")"
)
# Negative lookbehind for a LETTER specifically, not \b -- found live,
# testing this exact fix: \b treats underscore as a word character, so
# it never fires between '_' and a letter -- meaning \b failed to match
# ANY of this project's own filenames at all (e.g. "_watcher", "_face",
# "_eyeball" all start with an underscore immediately before the word,
# so a plain \b left-boundary regex silently never matched a single
# real project file by name, only ever via the in-file-title fallback).
# A negative lookbehind for a letter (not \w) correctly allows '_',
# digits, and start-of-string as valid left edges while still rejecting
# "ember" inside "member"/"remember"/"december" (all preceded by a
# LETTER immediately before "ember"), and still matches "watcher",
# "figures", "wardens" as word stems (see below for why stems, not
# whole-word-only, are wanted here).


def _reads_figurative(path):
    """Whether a piece counts as 'figurative' for the half-block/shading
    gates: filename match (the original signal) OR any FIGURATIVE_WORD
    appearing in the piece's own rendered/visible text (title cards,
    sig blocks) -- checked against the SGR-stripped visible content, not
    the raw source (so a word inside an escape sequence's parameters
    can't accidentally match).

    Extended 2026-09-18 after finding a real, concrete gap: _orb.v7.ans
    is a literal eye piece titled \"THE WATCHER // IT SEES IN THE DARK\"
    inside the file, but the bare filename '_orb' doesn't match any
    FIGURATIVE_WORD, so BOTH _figurative_precheck and the new
    _flat_region_check silently didn't apply to the exact piece these
    gates exist for -- found by testing this function against real data
    before trusting it, not assumed. Filename-only matching was always
    an incomplete proxy for 'what is this piece actually of'; the
    in-piece title is a much more direct signal and costs one extra
    regex pass, already-computed-ready SGR-strip logic reused from
    elsewhere in this file."""
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
    """Content-based subject identity: a coarse 8x8 occupancy+hue hash of
    the rendered grid. Renaming a file cannot change it.

    User direction, 2026-09-22: "track subject identity by content
    similarity or an explicit subject field, not the filename slug, so
    renaming can't reset the revision count." Found live: _watcher.v7
    hit the revision cap, was re-slugged _watcher_final, and sailed
    through as a fresh subject with zero content change.

    ponytail: 8x8 coarse grid, not a perceptual hash -- it only has to
    catch "same piece, new name", and a real pHash would need the
    rendered image, not the cell grid.
    """
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


# Subjects retired by the human -- a new piece on any of these is
# blocked outright. User direction, 2026-09-22: "no eye, orb, or sphere
# subject until three different subjects have been accepted." 60+
# versions since Sep 18 across _orb/_watcher/_watcher_final, the last
# of which was a re-slug that dodged the revision cap.
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
    """Strip a trailing version suffix (.v3, -v4, _v12) to find the
    underlying piece identity, e.g. '_orb.v5' and '_orb' are the same
    core piece at different revisions. Shared by the shipped-catalog dedup
    index, the revision-over-novelty gate, and the open-subject cap so all
    three agree on what counts as \"the same piece\" -- extracted to module
    scope 2026-09-17 (was previously a closure inside
    _shipped_catalog_index() only, duplicated ad hoc anywhere else that
    needed the same logic)."""
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
    # 'rejected' counts as still-open for cap purposes: rejection isn't a
    # close-out, it's a mandate to revise (revision-over-novelty). Only
    # accepted/abandoned/shelved actually free up a slot.
    rows = conn.execute(
        "SELECT slug, last_version, opened_at FROM subjects "
        "WHERE status IN ('open','rejected') ORDER BY opened_at"
    ).fetchall()
    return [{"slug": r[0], "last_version": r[1], "opened_at": r[2]} for r in rows]


def _compute_piece_metrics(path):
    """Real, measured per-version quality metrics for the pinned-best
    regression gate (user direction, 2026-09-18). The exact metrics the
    user specified: half-block %, shade-char %, distinct colors in the
    subject mask, subject bounding box, plus subject cell count (needed
    to make the bbox/pct numbers comparable across versions that might
    resize the canvas).

    half_block_pct/shade_char_pct are SUBJECT-ONLY (denominator =
    non-true-background cells), matching corpus/technique_index.py's
    definition exactly -- user direction, 2026-09-19: "use subject-only
    for both the harness gate and the corpus technique index -- same
    definition on both sides, so raze's output can be scored against
    the corpus distribution. My earlier whole-canvas numbers were
    expedient, not correct." This REVERSES the 2026-09-19 whole-canvas
    change (which matched the user's own quick diagnostic numbers at
    the time but was explicitly an expedient read, not the definition
    to standardize on) -- confirmed subject-only is what
    corpus/technique_index.py has used unchanged this whole time, so
    reverting here is what actually makes the two sides comparable.
    half_block_pct_whole_canvas/shade_char_pct_whole_canvas are logged
    alongside as secondary diagnostic fields (not used by any gate),
    since the whole-canvas number is still occasionally useful for a
    quick eyeball and was already the basis of several past diagnostic
    reports -- kept, not discarded, just demoted to non-authoritative.

    Returns a dict, or None if the file can't be parsed (caller should
    treat that as 'no metrics available', not block on it)."""
    try:
        grid, total_lines = _parse_ans_grid(path)
    except Exception:
        return None

    # ▀▄ ONLY, matching corpus/technique_index.py's HALF_BLOCK_CP exactly
    # -- deliberately NOT harness.py's own _HALF_BLOCK_CHARS (which also
    # includes █ full-block, for a different purpose: _figurative_precheck's
    # "is there enough non-flat cell geometry at all" question, where
    # lumping full-block in makes sense). User direction, 2026-09-19:
    # "same definition on both sides, so raze's output can be scored
    # against the corpus distribution" -- this metric exists specifically
    # to be comparable against corpus/technique_manifest.jsonl, so it
    # must use the corpus's own glyph set, not this file's other,
    # differently-scoped gate's set.
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

    # Compositional soft signals (user direction, 2026-09-22). NOTE the
    # honest name: this counts SPATIALLY DISCONNECTED masses, not forms.
    # Measured -- v59=6, _watcher_final=1 looked like a form count, but a
    # 5-form composite where everything touches the ground scores 1, and
    # hue-segmenting to fix that gives v59 and _watcher_final nearly
    # identical profiles (1199/308/120/114/109/60 vs
    # 1199->1114/316/159/89/79/40), so it cannot separate the one pair it
    # existed to separate. Kept as a soft signal because scattered-vs-
    # single-mass is real information; deliberately NOT in the
    # regression tripwire, and not worth image segmentation to improve:
    # composition quality is Opus's and hollis's judgment, not a metric.
    # ponytail: 4-connected flood fill over the subject mask, O(cells);
    # swap for a real labeler only if pieces get big enough to matter.
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
    # Ink density, not bbox: every framed piece spans the full canvas,
    # so a bbox-share number reads 100% for all of them and says
    # nothing (measured 2026-09-22 -- v59, _beast.v7 and
    # _watcher_final all reported 100%). Share of canvas actually
    # INKED does separate a sparse scroll from a dense composition.
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
    """Compute and store metrics for one version -- called from
    submit_piece on every real submission (not just accepted ones), so
    the full version history is measurable, not just whichever versions
    happened to get accepted."""
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
    """The pinned-best metrics for a slug: whichever version is marked
    pinned_version on the subjects row, or (if nothing pinned yet) the
    single best-so-far by a simple composite (half_block_pct +
    shade_char_pct + distinct_colors_in_subject) -- used both to decide
    what counts as 'best' the first time a subject accrues metrics, and
    to compare a new submission against. Includes 'path' (the stored
    .ans path for that version at submission time -- may no longer
    exist on disk if the file has since moved/been cleaned up; callers
    needing the real render should verify with Path.exists() first) for
    opus_pairwise_regression_check, which needs the actual rendered
    file, not just its numbers."""
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
    """Create or update a subject row. Called from submit_piece (new
    submission -> ensure the subject exists / bump last_version) and
    curate_piece (accept/reject -> update status)."""
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
    # Scratch hygiene at the single point every close routes through.
    if status in ("accepted", "abandoned", "shelved"):
        _archive_subject_scratch(slug)

def _archive_subject_scratch(slug):
    """Move a closed subject's scratch files to workspace/archive/.

    User direction, 2026-09-22: "when a subject is accepted, rejected
    past the revision cap, or abandoned, its scratch files move to
    workspace/archive/ automatically. Scratch holds current work only."

    Stale scratch is not inert: shifts 634-636 and 640 all went into
    _departure purely because it was sitting there. Moves, never
    deletes. Shared helper modules stay put -- they are read-reference
    per STYLE.md, not per-piece work.
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
    """After each accept: score the new piece against the last three
    accepted on half_block, shade-of-ink and distinct colors. Two
    consecutive accepts below the reference bar halts submissions and
    reports instead of continuing.

    User direction, 2026-09-22. Deliberately only these three metrics:
    they behave consistently across all 142 shipped pieces.
    disconnected_masses is excluded on purpose -- it reads spatial
    disconnection, not form count, so a composed scene scores 1 and a
    tripwire on it would punish exactly the work we want.

    Returns None when fine, else the halt message.
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
    """True when an uncleared two-strike halt is in force."""
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
            "description": "Run a shell command. Working directory defaults to ~/agentscii/workspace. Full system access.",
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
                "functional seat, the way every real BBS/ACiD artist had one. Shows up in "
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
                "Search the real 16colo.rs archive corpus (86k real ACiD/Blocktronics-scene "
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
                    "half_block_min": {"type": "number", "description": "Optional: only patches with at least this much half-block usage (0-100)."},
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
                "Apply real density-dither shading (the genuine ACiD ramp/dither "
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
                "share of canvas, next to the house bar's numbers. Use this "
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
    # Migration, 2026-09-16: carry the agent's last real reasoning block into
    # the next shift on ANY forced end (stop request, empty-turns give-up,
    # max-tool-calls cap), per user direction -- an in-progress diagnosis
    # (e.g. "I found the color bug, the fix is X") shouldn't be lost just
    # because the shift ended before the agent could act on it. ALTER TABLE
    # guarded because CREATE TABLE IF NOT EXISTS above is a no-op on an
    # existing state.db from before this column existed.
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
    # User direction, 2026-09-22 project review, task 5: "Log tool usage per
    # shift: counts for each tool, and how many .py files raze wrote." The
    # raw counts are already derivable from `events` (every tool call is
    # logged there with tool_name+tool_args -- see log_event's call site in
    # the dispatch loop), but a per-shift summary row means a query doesn't
    # have to re-aggregate the full events table every time, and survives
    # even if `events` ever gets pruned/archived. One row per (shift,tool).
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
    # subjects: tracks each distinct piece IDENTITY (by core_slug, i.e. the
    # filename with any trailing .vN/-vN/_vN stripped) through its
    # accept/reject lifecycle. Added 2026-09-17 (user direction) to enforce
    # two real rules that were previously unenforceable from the filesystem
    # alone: (1) revision-over-novelty -- a rejected piece must come back
    # as the SAME slug at a higher version, not reappear as a fresh slug
    # to dodge review history (observed live: _exchange rejected, came
    # back rebuilt as _voices; _crowd_joint rejected, came back as
    # _crowd_wave -- same underlying subject, new name each time, no
    # continuity an outside observer -- or this gate -- could trace); (2) a
    # hard cap of 2 open (not yet accepted/abandoned) subjects at once, so
    # a stalled piece can't just be abandoned silently in favor of endless
    # new starts -- it must be explicitly abandoned with a written reason,
    # which is preserved for the record.
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
        # Content identity, so a rename can't reset a subject's revision
        # count (see _subject_fingerprint).
        conn.execute("ALTER TABLE subjects ADD COLUMN fingerprint TEXT")
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
    # piece_metrics: per-VERSION quality metrics, tracked at every
    # submit_piece call (not just accepted ones) so a revision's real
    # progress -- or regression -- is measurable, not just "Opus said
    # reject again." Added 2026-09-18, user direction, directly in
    # response to the measured finding behind this whole session's
    # fixes: half-block % DECLINED v5->v8 (13.3% -> 9.4% -> 10.8% ->
    # 7.9%) across four straight revisions that were each supposed to be
    # improvements -- nothing before this table would have caught that
    # a "fix" was quietly making a different real metric worse. Pinning
    # (subjects.pinned_script_path/pinned_version) then lets
    # submit_piece hard-block any revision whose OWN metrics regress
    # versus the pinned best, even if the specific defect the agent
    # thought they were fixing is in fact fixed.
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
    # Safety net: opus_reviews was originally created ad hoc, never via
    # init_db, so a genuinely fresh DB would be missing it entirely.
    # IF NOT EXISTS makes this a no-op against the live DB's existing
    # table/data.
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
    """Aggregate this shift's tool calls (from `events`, already logged at
    every dispatch -- see log_event's call site) into shift_tool_summary:
    one row per tool with its call count, plus a synthetic 'write_file:.py'
    row counting write_file calls whose path argument ends in .py, AND a
    synthetic 'bash:.py_write' row for bash calls that look like they wrote
    a .py file (heredoc into a .py path, or a python open(...,'w')/
    write_text call targeting .py) -- checked directly against real
    history: .py files got written via bash heredocs as often as via
    write_file (see e.g. `cat > scratch/foo.py <<'EOF'` and
    `python3 - <<'PY' ... open('scratch/foo.py','w').write(...)`), so
    counting write_file alone would badly undercount "how many .py files
    did raze write" (the user's task 5 ask). Called once at shift end."""
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


def call_ollama(model, messages, tools):
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "tools": tools,
        **SAMPLING,
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=900) as resp:
        return json.loads(resp.read())


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
# Lets both agents actually SEE their own work through the model's real
# vision capability (qwen3.8:27b-mlx supports vision), instead of only
# inferring color/composition by reading raw SGR escape codes as text.
# Same 16-color BBS palette and SGR parsing logic as agentscii-dashboard's
# renderer, but rasterized to a real image instead of HTML.

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
_TERMINAL_WIDTH = 80  # standard classic-scene ANSI canvas width; long logical
                      # lines auto-wrap here just like a real terminal/BBS client


def _decode_ans_bytes(raw):
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp437", errors="replace")


def render_ans_to_png_b64(path, offset=0, max_rows=120, redact_title_rows=False):
    """Render an .ans/.asc file to a PNG, base64-encoded, for vision input.
    offset/max_rows let a long/scrolling piece be paged through panel by
    panel instead of only ever seeing the top — full content is always
    readable via read_file regardless.

    redact_title_rows=True blanks out (fills with true background) any
    row that reads as mostly-letters -- the house title-card/credit-line
    convention (row 1 = title, second-to-last content row = credit line,
    both ASCII letter text at high density) -- before rasterizing.
    Built for opus_subject_check() (user direction, 2026-09-19): the
    EXISTING opus_curate_review render already claimed to Opus "you have
    NO other context — no title" while literally baking the house's own
    title-card text into the rendered pixels (confirmed live: THE
    WATCHER's title row and credit line, containing the words "WATCHER"
    and "GUARDIAN" etc, render as plain readable text in row 0/1 and the
    second-to-last row of every real piece). A subject-recognition check
    is meaningless if the answer is printed directly on the image being
    judged -- this flag exists to make the blindness real, not just
    claimed in the prompt text."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None, "(error: Pillow not installed — pip install Pillow)"

    try:
        raw = Path(path).read_bytes()
    except Exception as e:
        return None, f"(error reading file: {e})"

    text = _decode_ans_bytes(raw).replace("\r\n", "\n").replace("\r", "\n")

    # Real cursor-addressable grid, not a flat per-line cell list. Classic
    # ACiD/Blocktronics-scene .ANS files routinely draw a base layer left to
    # right, then jump the cursor BACK UP with ESC[A to lay highlights/
    # shadows/detail onto rows already drawn (real artists worked this way
    # in TheDraw/ACiDDraw) — a flat "each source line is independent" model
    # (the old approach here) silently corrupts any piece using this, since
    # a cursor-up followed by new characters looks like a brand new row
    # instead of an edit to an existing one. Grid model: a dict of
    # (row, col) -> (char, fg_idx, bg_idx), with a real (row, col) cursor
    # that ESC[A/B/C/D/H/f all move, and later writes at the same cell
    # simply overwrite earlier ones — exactly what a real terminal does.
    grid = {}
    row, col = 0, 0
    max_row_seen = 0
    base_fg, bright_fg, base_bg = 7, False, 0
    pos = 0
    n = len(text)
    pending_wrap = False  # deferred-wrap flag, like a real terminal: filling
                          # the last column doesn't advance the row until
                          # the NEXT character actually needs to be drawn.
                          # Without this, a line that's exactly 80 chars
                          # wide (very common — full-width house rows) gets
                          # double-advanced: once by the internal wrap in
                          # put(), again by the explicit \n that follows —
                          # producing a spurious blank row after every
                          # full-width line and roughly doubling row count.

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
            # at the last column — defer the actual wrap (see above)
            col = _TERMINAL_WIDTH - 1
            pending_wrap = True

    while pos < n:
        ch = text[pos]
        if ch == "\n":
            if pending_wrap:
                # a line that filled exactly to the last column, then
                # ended: this newline IS that line's own terminator, not
                # an extra one — consume the pending wrap without a second
                # row advance.
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
        # trim fully-blank trailing columns (default fg/bg, space char) so a
        # mostly-empty row doesn't force every row to full width
        while line_cells and line_cells[-1] == (" ", 7, 0):
            line_cells.pop()
        rows.append(line_cells)

    if redact_title_rows:
        # A row is title/credit text if its non-space glyphs are mostly
        # ASCII letters at high density -- verified against 3 real house
        # pieces before trusting this threshold: title/credit rows measure
        # 0.56-0.92 letter-fraction, real drawn-art rows (half-block
        # glyphs, dither, box-drawing) measure far lower since almost none
        # of their characters are ASCII letters at all.
        for line_cells in rows:
            visible_chars = [ch for ch, fg, bg in line_cells if ch != " "]
            if len(visible_chars) < 8:
                continue
            letters = sum(1 for ch in visible_chars if ch.isascii() and ch.isalpha())
            if letters / len(visible_chars) > 0.5:
                for i in range(len(line_cells)):
                    line_cells[i] = (" ", 7, 0)

    note = f" (truncated to first {max_rows} rows of {total_lines}+)" if truncated else ""
    return _rasterize_rows_to_png_b64(rows, note)


def _rasterize_rows_to_png_b64(rows, note=""):
    """Shared rasterizer: a list of cell-rows (each a list of (char,
    fg_idx, bg_idx) tuples) -> PNG b64. Split out of
    render_ans_to_png_b64 (2026-09-22) so a second caller can rasterize
    rows that never came from an .ans file's cursor-addressed text --
    specifically canvas_tools.py's persistent canvases (canvas_preview),
    which already produce a clean cell grid with no ESC[A/B/C/D/H
    cursor parsing needed. Both callers get the exact same pixel output
    for the exact same cell data -- one rasterizer, not two copies that
    could drift."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None, "(error: Pillow not installed — pip install Pillow)"

    max_width = max((len(r) for r in rows), default=1)

    if not rows or max_width == 0:
        # Found live, 2026-09-19: `if not rows` alone doesn't catch a
        # real, valid case -- every ROW existing but every one of them
        # being fully blank (all cells trimmed to an empty list by the
        # trailing-blank-column trim above). max_width then computes
        # as 0 (max of a bunch of zero-length lists), producing a
        # ZERO-WIDTH image that crashes PIL's PNG encoder with
        # "SystemError: tile cannot extend outside image" -- confirmed
        # directly against a real fully-blank RLE fragment (a model's
        # degenerate FIM output during LoRA checkpoint eval). This is
        # the SHARED production renderer, so a real archive piece or
        # agent output that happens to be entirely blank in its
        # rendered window hits the exact same crash -- not just an
        # eval-script edge case.
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
                # FULL BLOCK drawn as a solid filled rectangle, not a font
                # glyph. Found directly 2026-09-16 building a real piece:
                # Menlo's '█' glyph at this font size is only 16px tall but
                # cells are drawn 18px apart, leaving a real 2px black gap
                # between every pair of vertically-adjacent full-block rows
                # — anything relying on stacked █ cells to read as one solid
                # shape (a large eye(), a filled silhouette, anything using
                # the brightest step of RAMP) rendered with visible
                # horizontal banding that was never actually in the data —
                # confirmed by inspecting the underlying character grid,
                # which was a correctly round, solid disc; only the PNG
                # preview had the gap. Other RAMP chars (▓▒░) keep font
                # rendering since their partial-fill dot patterns are the
                # actual content, not a bug to route around.
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
    """Preview a persistent canvas (canvas_tools.py) the same way
    preview_piece previews a saved .ans file. Canvas rows are already a
    clean grid (canvas_tools never emits cursor-addressing escapes), so
    this builds (char, fg_idx, bg_idx) rows directly and hands them to
    the SAME _rasterize_rows_to_png_b64 rasterizer render_ans_to_png_b64
    uses -- what an agent sees in canvas_preview is pixel-identical to
    what canvas_save + preview_piece would show afterward."""
    import canvas_tools
    try:
        data = canvas_tools.load_canvas(workspace, slug)
    except canvas_tools.CanvasError as e:
        return None, f"(error: {e})"
    out_lines = canvas_tools.render_canvas(data)  # list of SGR-coded strings
    total_lines = len(out_lines)
    offset = max(0, min(offset, total_lines))
    end_row = min(total_lines, offset + max_rows)
    truncated = end_row < total_lines

    rows = []
    for line in out_lines[offset:end_row]:
        cells = []
        fg, bg = 7, 0
        i = 0
        while i < len(line):
            m = _CSI_RE.match(line, i)
            if m:
                params = [int(c) for c in m.group(1).split(";") if c != ""]
                for p in (params or [0]):
                    if p == 0:
                        fg, bg = 7, 0
                    elif 30 <= p <= 37:
                        fg = p - 30
                    elif 90 <= p <= 97:
                        fg = p - 90 + 8
                    elif 40 <= p <= 47:
                        bg = p - 40
                    elif 100 <= p <= 107:
                        bg = p - 100 + 8
                i = m.end()
                continue
            cells.append((line[i], fg % 16, bg % 16))
            i += 1
        rows.append(cells)

    note = f" (truncated to first {max_rows} rows of {total_lines}+)" if truncated else ""
    return _rasterize_rows_to_png_b64(rows, note)


def render_comparison_b64(piece_path, reference_path, offset=0, max_rows=60):
    """Render a piece and a real reference side by side as ONE composite
    image, with labels, so an agent judging its own work sees the actual
    pixel gap instead of reasoning from memory of what it intended to build.

    Built 2026-09-16 in direct response to a caught real failure: an artist
    shift submitted a piece whose note claimed a shared primitive
    (capsule()/joint_dot()) that the code never called, and separately
    judged its own flat-banded render "genuinely good" after previewing it
    ALONE — nothing in that judgment was ever anchored to what real
    reference-quality work actually looks like next to it. A vision model
    reliably sees defects (dithering, banding, flat shading) when directly
    asked to compare two images — the earlier failures weren't a vision
    capability gap, they were a "never actually looked at a real reference
    right next to the work" gap. This tool forces that comparison to exist
    as a single image an agent can't reason around.
    """
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
    """Render N retrieved corpus patches (real (chars, fg, bg) numpy
    grids, e.g. from corpus/find_patches_clip.py) side by side as ONE
    composite image, each labeled with its source piece and technique
    metrics -- same "one image, not N separate tool results" pattern
    as render_comparison_b64, built for the find_patches tool (user
    direction, 2026-09-21: "wire find_patches into raze as a tool").

    Writes each patch's grid to a temp .ans file (same SGR-encoding
    convention corpus/eval_harness.py's render_grid_to_png uses
    internally) and reuses render_ans_to_png_b64 rather than
    reimplementing cell rasterization a third time. patches: list of
    dicts with chars/fg/bg numpy arrays plus parent_path/
    half_block_pct/shade_pct (the shape find_patches_clip.find_patches_clip
    and find_patches.find_patches_by_technique both return)."""
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
    """Parse an .ans/.asc file into a cursor-addressable grid: dict of
    (row, col) -> (char, fg_idx 0-15, bg_idx 0-15), plus total_lines.
    Shared by render_ans_to_png_b64 (visual rendering) and
    _figurative_precheck (the hard pre-submission gate, 2026-09-17) so
    both work from the exact same real cell data instead of the gate
    re-deriving its own approximate parse. Handles cursor-addressing
    (ESC[A/B/C/D/H/f) the way a real terminal does, not a flat
    one-line-in-source-equals-one-row model -- classic ACiD/Blocktronics
    .ANS files routinely draw a base layer then jump the cursor back up to
    add highlight detail on rows already drawn."""
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
# (full block counts as half-block usage too -- HalfBlockCanvas.render()
# emits a plain space with bg=color, or a full block, whenever both pixels
# in a cell match, which is a normal and correct half-block-canvas output,
# not colored-ASCII avoidance).


def _figurative_precheck(path):
    """Hard pre-submission gate (user direction, 2026-09-17): a figurative
    piece (filename matches FIGURATIVE_WORDS) with under 10% half-block
    cells, OR fewer than 3 distinct brightness steps inside its subject
    mask, cannot be submitted. Runs BEFORE curate_piece / the Opus gate --
    hollis never sees a piece that fails this, and no Opus call is spent
    reviewing it. This is mechanical, not a judgment call: it exists
    specifically because figurative pieces built from flat whole-cell
    shapes (not half-block resolution, not real shading) have repeatedly
    reached the curator and burned real review cycles before being
    rejected for exactly this -- pushing the check earlier is strictly
    cheaper and catches the same defect class deterministically.

    Returns None if the piece passes (not figurative, or passes both
    checks), else a string explaining the specific failure.

    'Subject mask' is approximated as all non-background cells (any cell
    that isn't a true empty space with black bg) -- an exact silhouette
    isn't derivable without vision, but brightness-step counting across
    ALL non-space drawn cells is a reasonable proxy: a genuinely
    flat/unshaded figurative subject won't clear 3 steps even counted
    this generously."""
    if not _reads_figurative(path):
        return None  # gate only applies to figurative work

    try:
        grid, total_lines = _parse_ans_grid(path)
    except Exception:
        return None  # don't hard-block on a parse error; let normal review catch it

    total_cells = 0
    half_block_cells = 0
    brightness_values = set()
    # Perceived brightness per 0-15 ANSI index, coarse but consistent
    # ordering (dim -> bright within each color, dark grays below colors
    # below bright colors below white) -- enough to count real STEPS, not
    # exact luminance.
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
    if half_block_frac < 0.10:
        failures.append(
            f"only {half_block_frac*100:.1f}% of drawn cells use half-block "
            f"characters (upper/lower/full block) -- figurative work needs "
            f"half-block resolution (workspace/scratch/halfblock.py's "
            f"HalfBlockCanvas) to read as constructed anatomy instead of "
            f"whole-cell blocks; under 10% means this is essentially "
            f"whole-cell-only construction"
        )
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
# same coarse brightness-ordering table as _figurative_precheck -- shared
# here rather than duplicated so both checks agree on what "a brightness
# step" means.

FLAT_REGION_CELL_THRESHOLD = 40
# House bar (_orb.v59) and corpus medians, reported as SOFT signals on
# every submission -- never enforced as a threshold. User direction,
# 2026-09-22: "any floor set where the house can't already reach gets
# gamed rather than met."
HOUSE_BAR = {"name": "_orb.v59", "half_block": 37.9, "shade": 32.1,
             "colors": 6, "regions": 6, "ink_share": 56}
CORPUS_MEDIAN = {"half_block": 15.0, "shade": 9.4}
# User direction, 2026-09-18, load-bearing measurement behind this whole
# check: every version of _orb (v5-v8) and _phosphor.v3 measured at 0.0%
# RAMP (░▒▓) density characters -- literally zero dithering anywhere.
# That's not a style choice, it's the absence of a shading mechanism, and
# it's the exact, repeated reason the Opus gate kept rejecting them (flat
# unshaded region, hard seam, no gradient). A checker alone can't fix the
# underlying capability gap (see shade_ramp() in canvas.py, built the same
# day for that reason) -- but it SHOULD catch the defect class before an
# Opus call is spent reviewing it, which this does.


def _flat_region_check(path):
    """Hard pre-submission gate companion to _figurative_precheck (user
    direction, 2026-09-18): any contiguous same-(char-class,fg,bg) region
    larger than FLAT_REGION_CELL_THRESHOLD cells, INSIDE the subject (not
    the background), is a defect -- and within any hue family, the set
    of large flat regions must span at least 3 distinct brightness
    steps, not just a hot fill and a cold fill with nothing graduated
    between them. Runs BEFORE curate_piece / the Opus gate, same as
    _figurative_precheck -- no review cycle spent on a piece this
    catches.

    SCOPED TO FIGURATIVE PIECES ONLY, same gate as _figurative_precheck
    (filename matches FIGURATIVE_WORDS) -- found live, before shipping,
    that applying this unscoped produces real false positives: a real
    reference wordmark/logo piece (asphyx-acid_logo.ANS) has a genuine
    45-cell solid-fill letter stroke, which is completely normal for
    wordmark/logo work (a bold stroke has no reason to internally shade)
    but would read as a defect under "a lit surface must shade across
    itself" logic. That logic only actually applies to a lit FORM (an
    eye, a face, a rounded body) -- exactly the same subject class
    _figurative_precheck already targets. Also found and fixed before
    shipping: a large-area DITHERED texture fill (a real reference
    piece's 2262-cell scattered ▒ field, a genuine and deliberate ACiD
    background-texture technique) triggered a false positive on an
    earlier version of this check that grouped purely by visible color
    regardless of glyph -- fixed by only flood-filling SOLID-ink glyphs
    (space-with-bg, or a full block) into regions; a RAMP/dither glyph
    (▒▓░) breaks region continuity by design, since density variation
    within an area is itself evidence of real shading work, not a
    defect.

    'Subject' cells = anything not true background (not a plain space
    with bg=0) -- same approximation used elsewhere in this file, since
    an exact subject silhouette isn't derivable without vision. A large
    flat region OUTSIDE the subject (e.g. a deliberately flat black
    void, or a deliberately solid-color title-card band) is legitimate
    and not flagged -- texture_fill()/negative-space conventions are a
    separate, already-existing check (LOW BACKGROUND TEXTURE in this
    same function). This check is specifically about flatness WITHIN
    drawn content, which is the actual defect class Opus kept catching.

    Returns None if the piece passes (including: not a figurative
    piece, so the check doesn't apply), else a string describing the
    specific violation(s) found (region size + location, or a
    transition with too few brightness steps)."""
    if not _reads_figurative(path):
        return None  # scoped to figurative work, see docstring

    try:
        grid, total_lines = _parse_ans_grid(path)
    except Exception:
        return None  # don't hard-block on a parse error; let normal review catch it

    # Exclude border/title-rule rows before building the subject set: a
    # horizontal rule (a long run of one box-drawing/rule glyph spanning
    # most of the row) is a deliberate house convention (STYLE.md /
    # Methodology Pass 6, "real packs are framed more often than not"),
    # not part of the shaded subject -- found live on a real test: the
    # top/bottom double-line border rows (79 cells of solid '═' each) on
    # _orb.v7 were flagged as "flat regions" before this exclusion, which
    # would have blocked every single framed piece in the house style,
    # not just genuinely flat subject fills. Same box_chars set already
    # used by inspect_piece's separate frame-detection check, reused
    # here rather than redefined.
    # Full U+2500 box-drawing block, not a hand-typed subset: the old
    # literal set was missing 18 real CP437 glyphs (╡╞╟╢╤╧╥╨╪╫╕╖╘╙╛╜╒╓),
    # which is why a 72-cell '╡' title rule on _cyclops read as a flat
    # SUBJECT region -- found live 2026-09-22 while checking the gate
    # against the shipped gallery.
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

    # Build a subject-cell coordinate set keyed by VISIBLE color, not raw
    # (char, fg, bg). For a half-block "space with bg" cell (the common
    # case from HalfBlockCanvas -- confirmed live on a real _orb render:
    # the dominant cell shapes were exactly this, (' ', fg=15, bg=<real
    # color>), where fg=15 is leftover SGR state from an earlier bold
    # code and carries no visible meaning since a space glyph has no ink)
    # the color that's actually ON SCREEN is bg, not fg. An earlier
    # version of this function grouped by raw fg unconditionally and
    # would have silently failed to detect real large flat regions in
    # exactly this common cell shape -- caught before shipping by
    # checking real _orb.v7 cell data first. Same visible-color logic as
    # _figurative_precheck, kept consistent rather than reinvented.
    subject_cells = {}
    dither_cells = set()
    for (r, c), (ch, fg, bg) in grid.items():
        if ch == " " and bg == 0:
            continue
        if r in border_rows:
            continue
        if ch in _box_chars:
            # Box-drawing glyphs are FRAME, never shaded subject surface
            # -- found live 2026-09-22: 12 shipped gallery pieces
            # (raze-traveler-v1, hollis-portrait, the agent-sci banners
            # ...) were blocked by a 72-cell run of '╡' on a title rule.
            # The border_rows filter above only catches rows that are
            # >70% box chars, so a rule sharing its row with title text
            # slipped through and got flood-filled as a "flat region."
            continue
        if ch in "\u2593\u2592\u2591":  # ▓▒░ -- partial-density dither
            # glyphs are themselves evidence of real shading (that's
            # literally what they exist to fake on a 16-color palette,
            # see canvas.shade_ramp()) -- never flood-fill them into a
            # "flat region," and don't let them BREAK an otherwise-flat
            # run either (a dither glyph adjacent to a solid run is a
            # real transition edge, not noise to route around). Recorded
            # separately in dither_cells so the hue-step check below can
            # credit a region for bordering a real dithered transition
            # -- see that check's own comment for why this matters.
            dither_cells.add((r, c))
            continue
        visible_idx = bg if (ch == " " and bg != 0) else fg
        # region identity: (glyph-class, visible color) -- glyph-class
        # collapses ' ' and any RAMP/half-block char that would render
        # with equal apparent density into one bucket only when they're
        # genuinely the same visible fill; kept simple and exact (raw
        # char) rather than fuzzy, since over-merging would UNDER-count
        # real flat regions, the opposite of this check's purpose.
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

    # Connected components of dither cells (4-connected), computed once
    # and shared by BOTH checks below -- a "bridge" is one dither
    # component that physically connects two different brightness
    # levels. This is what makes a large solid region legitimate: a
    # flat fill that ramps into another brightness through a dithered
    # transition IS a gradient (flat-dim -> dithered-mid -> flat-bright
    # = 3 apparent brightness steps, which is achievable on a 16-color
    # palette, unlike 3 distinct FLAT steps within one hue family).
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
        """True when this region ramps into a DIFFERENT brightness level
        through a dithered bridge. Large solid regions are fine when
        part of a gradient (user direction, 2026-09-22) -- the old gate
        failed every region over 40 cells unconditionally, which is what
        drove pieces toward wall-to-wall ░▒▓ static."""
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

    # NOTE (2026-09-22): a standalone shade-share hard block was tried and
    # REMOVED. Measured against the 142 shipped gallery pieces: shade p50
    # = 54.5%, p90 = 83.0%, and 117/142 ship at 0.0% half_block. Every
    # threshold tested false-positived accepted work -- corpus p90 (38%)
    # blocked 23 pieces, p99 (65%) blocked 23, and the narrower
    # conjunction (hb<5 AND shade>65) blocked 49, including raze-oracle,
    # hollis-warden and raze-aperture. _watcher_final (hb 0.0 / shade
    # 78.2) is metrically IDENTICAL to the accepted hollis-raze-boot
    # (hb 0.0 / shade 78.2); no cell-level metric separates them.
    # Reported as soft signals in submit_piece instead -- a floor the
    # house cannot already reach gets gamed rather than met, which is
    # what produced the re-slugging and the static in the first place.

    # Lit-to-shadow transition check: with a real 16-color ANSI palette,
    # each hue family (fg & 7) has only 2 real members (e.g. dim vs
    # bright amber) -- there is NO third flat color level to reach for
    # a genuine gradient. Real shading on this palette is ALWAYS done by
    # DITHERING between the two flat levels (canvas.shade_ramp()), never
    # by a third solid fill. An earlier version of this check demanded
    # ">=3 distinct flat brightness steps," which is a mathematically
    # impossible bar on a real 16-color palette -- found live: raze
    # built an independent local replica of this exact gate while
    # debugging a rejection, and it proved the ACCEPTED v7 benchmark
    # piece also fails the old "3 flat steps" rule, since no 16-color
    # hue family can ever have 3 members. The check now asks the right
    # question instead: when a hue family has large flat regions at
    # more than one brightness level, is there a real DITHERED bridge
    # (a connected run of ░▒▓ cells) physically between them? That's
    # exactly what shade_ramp() produces and exactly what a hard flat-
    # to-flat seam lacks -- this is checkable, unlike counting
    # non-existent third flat levels.
    if len(large_regions) >= 2:
        # group large regions by hue family (fg & 7); a genuine
        # lit-to-shadow transition happens WITHIN one hue family across
        # brightness, not across unrelated hues
        by_hue = {}
        for reg in large_regions:
            hue_key = reg["visible_idx"] & 7
            by_hue.setdefault(hue_key, []).append(reg)

        # dither_components / _touches are computed once above and
        # shared with the flat-region check -- not recomputed here.
        for hue_key, regs in by_hue.items():
            if len(regs) < 2:
                continue
            # dedupe by brightness step: two regions at the SAME
            # brightness aren't a "seam" to bridge (they're just the
            # same flat fill in two places), only a step DIFFERENCE
            # needs a dither bridge between it.
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
        # Weighted toward the tradition the catalog is thinnest in (figurative/
        # character/scene work — 2 of 41 pieces at last count) so the randomness
        # actively counters the gravity toward whatever's cheapest to produce,
        # rather than just reinforcing it. Still genuinely random, still fully
        # optional to act on.
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
                # internal gap: a long run of space characters bordered by real
                # content on both sides, anywhere in the row (not just the right
                # margin) — the exact signature of a wordmark/panel-fill loop
                # that silently stopped painting partway across, leaving a black
                # hole in the middle of an otherwise-painted row. Plain trailing-
                # whitespace checks miss this because the gap isn't at the end.
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
            # Methodology Pass 5 (see workspace/METHODOLOGY.md) requires real
            # texture in whatever ISN'T the subject -- the single most common
            # gap between house figurative work and the real references
            # (compare STRIDE/MANTIS's flat black to ghengis-shades_of_a_
            # shade.ANS's dense stippled field). Approximate "background" as
            # any row-run of default/near-black bg (SGR bg 0/40 or unset) with
            # low visible-glyph density -- can't know the TRUE subject
            # silhouette without vision, but a piece that never varies its bg
            # color/density across long stretches is a real, checkable signal
            # of an un-textured negative space, regardless of what the actual
            # subject shape is.
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
                        f"may have been skipped. Real ACiD reference work rarely "
                        f"leaves this much genuinely flat space; verify by eye with "
                        f"preview_piece whether this is a deliberate minimal "
                        f"composition or a missing texture_fill() pass."
                    )
                else:
                    out.append(f"background texture: {near_black_bg_rows}/{content_rows} rows read flat ({flat_frac*100:.0f}%) -- reasonable")

            # --- border/frame presence check ------------------------------------
            # Methodology Pass 6 -- real ACiD packs are framed far more often
            # than not (box-drawing border, repeated block motif, or a title
            # card top/bottom). Cheap, approximate check: does the FIRST or
            # LAST non-blank content row look like a deliberate horizontal
            # rule/border (long run of a single repeated glyph, box-drawing
            # chars, or a title-card pattern), or is the piece just... over,
            # with no frame treatment at all.
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
                    "row reads as a border/rule/title-card treatment. Real ACiD "
                    "packs are framed more often than not (Methodology Pass 6) -- "
                    "verify by eye whether this piece deliberately goes unframed "
                    "or whether that pass just got skipped."
                )
            elif has_top_frame or has_bottom_frame:
                out.append(f"frame/border: detected ({'top' if has_top_frame else ''}{' + ' if has_top_frame and has_bottom_frame else ''}{'bottom' if has_bottom_frame else ''})")
            # --- scope-family relabeling check ---------------------------------
            # curve_common.py's phosphor_render() uses one specific 8-hue wheel
            # (95,91,93,92,96,94,107,103) plus white-hot (97) and nothing else —
            # a very distinctive SGR fingerprint. Real figurative/anatomical
            # pieces (figure_common.py, canvas.py) use a much broader/different
            # palette because they build shaded regions, not a hue-cycled trace.
            # If a piece's SGR params are ENTIRELY inside that fingerprint set
            # AND its filename reads as figurative (face/eye/watcher/sentinel/
            # cyborg/scan/mind/portrait/figure), flag it for a by-eye check —
            # this catches the "scopes-family math relabeled as a character
            # piece" pattern mechanically instead of relying on the curator's
            # judgment alone every time.
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
            # Found directly 2026-09-14: ECLIPSE v3 shipped to a released pack with
            # a literal debug tagline baked into the rendered image -- the author
            # comment even names it as a working label ("PROVENANCE... 'object +
            # object'") that was never replaced with real content before submit.
            # Cheap, reliable, zero-false-positive-risk check: scan visible text
            # for common placeholder/debug tokens.
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

            return "\n".join(out)
        except Exception as e:
            return f"(error inspecting piece: {e})"

    if name == "bash":
        try:
            cmd = args["command"]
            # Block direct invocation of the `claude` CLI from agent shell
            # commands (user direction, 2026-09-16): Opus 5 review is
            # billed against the human's own subscription via
            # opus_curate_review(), reserved for the harness's curate_piece
            # path only. An agent shelling out to `claude` directly would
            # spend that same budget outside the cap/logging/shelve
            # machinery entirely -- word-boundary match so this catches
            # `claude -p ...` but not an unrelated word containing
            # "claude" as a substring.
            if re.search(r"(?:^|[;&|\s])claude(?:\s|$)", cmd):
                return (
                    "(error: direct `claude` CLI invocation is blocked in "
                    "agent shell commands — Opus 5 review runs only through "
                    "the harness's curate_piece flow, which enforces the "
                    "daily cap and per-piece review limit. If you need a "
                    "second opinion, use curate_piece's built-in Opus gate, "
                    "not a direct CLI call.)"
                )
            r = subprocess.run(
                cmd, shell=True, cwd=str(WORKSPACE),
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
            return p.read_text(errors="replace")[:4000]
        except Exception as e:
            return f"(error: {e})"

    if name == "write_file":
        try:
            p = _resolve_workspace_path(args["path"])
            # figure_common.py freeze (user direction, 2026-09-17): "Raze
            # draws with half-block primitives for the next few pieces,
            # even if the output is simpler. Simple and shaded beats
            # complex and flat." The file is also chmod 444 on disk as the
            # real enforcement (blocks bash redirects/sed -i/etc, not just
            # this one code path) -- this check exists purely to give a
            # clear, on-topic error instead of a bare permission-denied.
            if p.name == "figure_common.py":
                return (
                    "(error: figure_common.py is frozen — house direction "
                    "2026-09-17: draw with half-block primitives "
                    "(workspace/scratch/halfblock.py's HalfBlockCanvas) for "
                    "the next few pieces instead, even if the result is "
                    "simpler. Simple and shaded beats complex and flat. "
                    "The file is also read-only on disk.)"
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
            if not src.exists():
                return f"(error: {src} does not exist)"

            # --- figurative hard pre-submission gate ------------------------
            # User direction, 2026-09-17: runs FIRST, before any other gate,
            # before curate_piece, before any Opus call is spent. Mechanical,
            # not a judgment call -- see _figurative_precheck's docstring.
            precheck_fail = _figurative_precheck(src)
            if precheck_fail:
                return f"(error: {precheck_fail})"

            # --- flat-region hard pre-submission gate ------------------------
            # User direction, 2026-09-18, built after measuring the real
            # root cause of repeated _orb/_phosphor Opus rejections (0.0%
            # RAMP density chars across every version) -- see
            # _flat_region_check's docstring for the full finding and the
            # false-positive fixes made before shipping this.
            flat_fail = _flat_region_check(src)
            if flat_fail:
                return f"(error: {flat_fail})"

            # --- soft technique signals (NEVER a block) ---------------------
            # User direction, 2026-09-22: report half_block and shade-of-ink
            # on every submission next to the house bar and the corpus
            # medians, so the curator and Opus can judge -- enforcing them
            # as a threshold is what produced the re-slugging and the
            # static. Appended to the submit result, not returned as error.
            soft_signal = ""
            _sm = _compute_piece_metrics(src)
            if _sm is not None:
                soft_signal = (
                    f"\n\ntechnique (SOFT SIGNAL — not a gate, nothing is "
                    f"enforced): half_block {_sm['half_block_pct']:.1f}%, "
                    f"shade-of-ink {_sm['shade_char_pct']:.1f}%, "
                    f"colors {_sm['distinct_colors_in_subject']}, "
                    f"disconnected masses {_sm['disconnected_masses']}, "
                    f"ink {_sm['ink_canvas_share']:.0f}% of canvas. "
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

            # --- required v59 comparison before submit ----------------------
            # User direction, 2026-09-22: the house bar is raised through
            # REFERENCE, not through a metric threshold. A figurative piece
            # must be looked at side by side with _orb.v59 before it can be
            # submitted. Checked against this shift's own logged
            # compare_to_reference calls (events already records tool_name +
            # tool_args at the single dispatch site) rather than new state.
            db_cmp = sqlite3.connect(DB_PATH)
            try:
                seen_v59 = db_cmp.execute(
                    "SELECT COUNT(*) FROM events WHERE shift_id=? "
                    "AND tool_name='compare_to_reference' "
                    "AND tool_args LIKE '%_orb.v59%'", (shift_id,)
                ).fetchone()[0]
            finally:
                db_cmp.close()
            if not seen_v59:
                return (
                    "(error: submit_piece blocked — call compare_to_reference "
                    "with reference_path='references/study/_orb.v59.ans' and "
                    "actually look at the result first. v59 is the house bar: "
                    "match or beat it on structure and half-block use. This is "
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

            # --- retired subject + re-slug identity ------------------------
            # Both are one question: what subject IS this? Filename slug
            # was the only answer before, which is exactly what the
            # _watcher.v7 -> _watcher_final rename exploited.
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
            # User direction, 2026-09-17: a rejected piece must come back as
            # the SAME file at v+1, not reappear under a fresh slug to dodge
            # review history -- observed live: _exchange (rejected) came back
            # rebuilt as _voices; _crowd_joint (rejected) came back as
            # _crowd_wave. Also caps open (not accepted/abandoned) subjects
            # at 2: starting a third is blocked until one is accepted or
            # explicitly abandoned via abandon_subject with a written reason.
            slug = core_slug(src.stem)
            version = _extract_version(src.stem)
            db2 = sqlite3.connect(DB_PATH)
            try:
                # --- hard revision cap ---------------------------------------
                # User direction, 2026-09-19: "Cap revisions at 8 per subject.
                # After that it ships, gets shelved, or reverts to the best-
                # scoring earlier version. 59 versions is not iteration, it's
                # thrashing." Counted from piece_metrics (one row per real
                # submit_piece call that reached this point, regardless of
                # accept/reject outcome -- the true revision count, not just
                # the reviewed count) rather than the bare version NUMBER in
                # the filename, since a version number can skip ahead (a
                # subject could reach ".v20" after only 8 actual submissions
                # if earlier attempts were blocked before reaching this gate,
                # or could have gaps from abandoned parallel attempts) --
                # what must be capped is real submitted revisions, not the
                # numeric suffix an agent chose.
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
                # User direction, 2026-09-18: block any revision whose OWN
                # measured metrics (half-block %, shade-char %, distinct
                # subject colors) drop versus the pinned best, even if the
                # specific defect the agent thought they were fixing is
                # genuinely fixed. Built after measuring the real case this
                # exists to prevent: _orb's half-block % declined on every
                # single revision (v5->v8: 13.3%->9.4%->10.8%->7.9%) while
                # each version was submitted believing it was an
                # improvement -- nothing caught the regression until now.
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
                        # small floating-point slack (0.5) so a rounding
                        # difference doesn't block an otherwise-flat metric
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
            # Added 2026-09-16 directly in response to: an artist judged its
            # own flat-banded THE DUEL render "genuinely good and submission-
            # ready" after previewing it ALONE (see the capsule() gate right
            # below for the other half of that same incident). Self-
            # assessment in isolation is unreliable; a real side-by-side
            # against actual reference-quality work is not (confirmed: the
            # vision model correctly spotted banding/confetti/etc. in ad hoc
            # tests every time it was shown a direct comparison). Hard
            # requirement, not a suggestion: submit_piece is blocked unless
            # compare_to_reference was called on this exact filename at some
            # point in the last 40 tool events by this agent. Cheap to
            # satisfy (one real tool call), impossible to fake with a note.
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
            # Found directly 2026-09-15: _duel.py's own header comment
            # claimed "built on hollis's capsule()/joint_dot() lit-tube
            # primitives as its CORE" while the actual code never called
            # either -- it reimplemented its own local cap()/joint() that
            # threw away shade()'s density-varying glyph and hardcoded a
            # solid block, guaranteeing the exact flat-color-banded look
            # STYLE.md's "REQUIRED for any body-shaped subject" rule exists
            # to prevent. Three separate pixel-statistics heuristics were
            # tried and failed to discriminate this reliably (see git log)
            # -- the only reliable signal is checking the SOURCE CODE
            # actually does what its own note claims, at the one point
            # (submission) where the .py source is still guaranteed to sit
            # alongside the .ans in scratch/. This is a hard block, not a
            # warning: figurative/body-shaped work claiming the shared
            # primitive must actually call it.
            note_text = args.get("note", "")
            body_words = ("figure", "figurative", "body", "torso", "limb",
                          "capsule", "joint_dot", "anatomy", "anatomical")
            claims_body_tooling = any(w in note_text.lower() for w in body_words)
            if claims_body_tooling:
                py_candidate = src.with_suffix(".py")
                if py_candidate.exists():
                    py_text = py_candidate.read_text(errors="replace")
                    # Strip comments before checking for REAL calls -- a
                    # comment mentioning "capsule()" (like _duel.py's own
                    # header claiming to use it) must not count as an
                    # actual call, or this gate has the exact same
                    # claim-vs-reality blind spot it exists to catch.
                    code_only = "\n".join(
                        line.split("#", 1)[0] for line in py_text.split("\n")
                    )
                    calls_capsule = bool(re.search(
                        r"\b(?:fc\.|figure_common\.)?capsule\s*\(", code_only
                    ))
                    calls_joint_dot = bool(re.search(
                        r"\b(?:fc\.|figure_common\.)?joint_dot\s*\(", code_only
                    ))
                    # Negation-aware, same fix as the earlier blind-check
                    # gate bug: "NOT the shared capsule()" or "my own
                    # shading, not capsule()" is an honest disclosure, not
                    # a false claim -- only block when the note asserts
                    # USING it without a negator governing that mention.
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
                # Record real metrics for this version, and if this is the
                # first version ever seen for this slug, pin it as the
                # initial "best" so version 2 has something real to be
                # compared against -- see _get_best_metrics's fallback
                # logic for what happens before any pin is explicit.
                recorded = _record_piece_metrics(db3, slug, version, dest)
                if recorded is not None:
                    existing_pin = db3.execute(
                        "SELECT pinned_version FROM subjects WHERE slug=?", (slug,)
                    ).fetchone()
                    if existing_pin and existing_pin[0] is None:
                        # The real generator-script convention (confirmed
                        # against actual scratch/ files, not assumed): the
                        # base script is UNVERSIONED, e.g. scratch/_orb.py,
                        # edited in place across every revision (real
                        # evidence: _orb.v8.bak.py / _orb.v9.bak.py sit
                        # next to it as pre-edit backups of that same
                        # file). An earlier version of this derived the
                        # pinned path from the SUBMITTED .ans filename
                        # (e.g. "_orb.v6.py"), which doesn't correspond to
                        # any real file on disk -- fixed before shipping.
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
                # Adversarial verification: if the critique makes a checkable
                # visual-feature claim (face/eye/brow/jaw/anatomy/figure/
                # portrait/silhouette), get a BLIND second opinion from the
                # same model with zero access to this critique's text, and
                # hard-block the accept if it flatly contradicts the claim.
                # This exists because a real accepted piece ("TWO VOICES
                # v1.1") shipped with a critique describing "two facing
                # profile heads... brow... jaw... eye-line" when the actual
                # render is three flat solid-color triangular blocks with no
                # facial structure at all -- inspect_piece's structural
                # checks cannot catch this, it's a perception failure, not a
                # hygiene one. This is a real check, not a rubber stamp: the
                # curator can still accept after re-examining, revising the
                # critique to match reality, or overriding with an explicit
                # note explaining the disagreement — it isn't a silent veto.
                critique_lower = critique.lower()
                # Negation-aware: only count a visual-claim word as an actual
                # POSITIVE claim (curator asserting the feature is present),
                # not when the curator is denying/negating it themselves
                # ("NOT anatomy", "no face", "isn't a figure", "without eyes").
                # Bug found 2026-09-14: the naive version triggered on ANY
                # occurrence of the word, so a curator correctly writing "this
                # is abstract, no anatomy, no face" got hard-blocked by this
                # gate even when the blind check agreed with them — 4 straight
                # curator shifts (397/399/401/403) loop-guard-killed on this
                # exact false positive, stuck re-wording an already-correct
                # critique because the gate couldn't tell affirmation from
                # denial.
                _NEGATORS = (
                    r"\b(?:no|not|n't|without|zero|none of|isn'?t|aren'?t|lacks?|"
                    r"absence of|disclaims?|rather than|pretending (?:to be|at)|"
                    r"instead of|supposed to be)\b"
                )
                claimed_words = []
                for w in _VISUAL_CLAIM_WORDS:
                    # word-boundary match only (substring "eye" inside "eyed"
                    # or, critically, the idiom "verified by eye" is not a
                    # claim that a real eye is present — that idiom is used
                    # constantly in real critiques and was itself producing
                    # false triggers before this fix)
                    for m in re.finditer(r"\b" + re.escape(w) + r"\b", critique_lower):
                        post = critique_lower[m.end():m.end() + 8]
                        if w == "eye" and post.startswith(" against"):
                            continue  # "by eye against ref" == verified visually
                        pre_tail = critique_lower[max(0, m.start() - 8):m.start()]
                        if w == "eye" and pre_tail.rstrip().endswith("by"):
                            continue  # "by eye" == verified visually, not a claim
                        # Negation can govern a whole comma-separated list
                        # ("no anatomy, face, eye, brow, jaw") — so look back
                        # to the start of the CLAUSE (last sentence-ending
                        # punctuation), not just a fixed few words, and check
                        # the negator appears anywhere in that clause with no
                        # intervening clause break ("but"/"however"/";").
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
                    # Robust-ish, not brittle keyword matching: look for a clear
                    # denial signal ANYWHERE in the first ~200 chars (covers
                    # "No.", "No genuinely...", "not built from...", etc — real
                    # model phrasing varies) AND at least one concrete grounding
                    # phrase describing flat/geometric shapes rather than
                    # constructed anatomy, anywhere in the full response.
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
                    contradicts = (
                        not blind_lower.startswith("(blind check")
                        and denial_signal and grounding_signal
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
                # Opus 5 is now the sole accept/reject authority (user
                # direction, 2026-09-16) -- Qwen's own decision/critique are
                # passed through for logging/disagreement-rate comparison,
                # not used to decide where the file goes. This replaces the
                # direct _move_with_sidecars(...) calls that used to run
                # here for both branches.
                return curate_piece_opus_gated(src, decision, critique)
            elif decision == "reject":
                return curate_piece_opus_gated(src, decision, critique)
            else:
                return f"(error: decision must be 'accept' or 'reject', got {decision!r})", None
        except Exception as e:
            return f"(error: {e})", None

    if name == "release_pack":
        return "(handled by harness)"

    if name == "end_shift":
        return "(handled by harness)"

    return f"(unknown tool: {name})"


def curate_piece_opus_gated(src, decision, critique):
    """Real replacement for the tail of curate_piece's accept/reject move,
    per the user's explicit 2026-09-16 direction: Opus 5 is the ONLY
    authority on accept/reject; Qwen's decision/critique are logged for
    the disagreement-rate comparison but do not decide where the file
    goes. Called instead of the plain _move_with_sidecars(...)-then-return
    pair inside curate_piece once the pre-existing checks (path validity,
    blind claim-consistency gate) have already passed for whatever Qwen
    itself asserted.

    Also keeps the `subjects` table (2026-09-17, revision-over-novelty +
    open-subject-cap gate) in sync: accept/shelve close the subject out,
    reject leaves it open but records the rejection so the next
    submit_piece call for the same slug is forced to a higher version.

    Returns (message, dest_path_or_None) matching curate_piece's existing
    return shape so the dispatcher doesn't need to change."""
    # --- blind subject-recognition gate (user direction, 2026-09-19) ----
    # Runs FIRST, before the metric-based defect review: measures
    # technique, this asks whether the piece even reads as its intended
    # subject at all. A piece can pass every mechanical gate (half-block
    # %, shade %, flat-region check) while the actual composition has
    # drifted into something that no longer reads as the intended
    # subject -- exactly the failure mode this catches regardless of
    # metrics being satisfied.
    subject_result = opus_subject_check(src)
    if subject_result["status"] == "mismatch":
        dest = _move_with_sidecars(src, REJECTED, new_critique=subject_result["message"])
        slug0 = core_slug(Path(src).stem)
        version0 = _extract_version(Path(src).stem)
        db0 = sqlite3.connect(DB_PATH)
        try:
            _touch_subject(db0, slug0, version0, src, status="rejected")
        finally:
            db0.close()
        return (
            f"rejected: moved to rejected/{dest.name} — "
            f"{subject_result['message']}"
        ), dest

    # --- pairwise regression gate (user direction, 2026-09-19) -----------
    # Runs SECOND, after subject recognition, before the defect review:
    # built directly for the v55->v59 case, where both tracked %
    # metrics improved while the piece genuinely read worse (shrunken
    # sclera, noisy background) -- a regression no metric-floor check
    # can see by construction. Blind side-by-side against the pinned
    # best, randomized A/B, titles redacted.
    slug_pw = core_slug(Path(src).stem)
    db_pw = sqlite3.connect(DB_PATH)
    try:
        best_pw = _get_best_metrics(db_pw, slug_pw)
    finally:
        db_pw.close()
    pinned_render_path = None
    if best_pw and best_pw.get("path"):
        candidate_pinned_path = Path(best_pw["path"])
        # only compare against a DIFFERENT version than the one being
        # submitted right now, and only if that file still exists on
        # disk (a pinned version's .ans can be cleaned up after ship,
        # same gap documented for _orb v53 elsewhere in this file)
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
        dest = _move_with_sidecars(src, GALLERY_UNPACKED, new_critique=critique)
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
                halt = f"\n\n{tw}"
        except Exception:
            pass
        finally:
            _db_tw.close()
        return (
            f"accepted: moved to gallery/unpacked/{dest.name}, pending next "
            f"pack release. Opus verdict: ACCEPT{agree}.\n\n{result['message']}{halt}"
        ), dest
    if status == "reject":
        dest = _move_with_sidecars(src, REJECTED, new_critique=critique)
        _sync_subject("rejected")
        agree = "" if decision == "reject" else " (Qwen's own read was ACCEPT — Opus overrode it)"
        return (
            f"rejected: moved to rejected/{dest.name} with critique "
            f"attached. Opus verdict: REJECT{agree}.\n\n{result['message']}"
        ), dest
    return f"(error: unexpected Opus review status {status!r})", None


def _shipped_catalog_index():
    """MD5 + core-slug index of every piece already shipped in gallery/packNN/,
    excluding quarantine dirs (_held-*). Used to hard-block a real duplicate
    from re-shipping at release time instead of relying on agents remembering
    to run a separate dedup script (the pack17 nebula-dup incident happened
    exactly because that step was optional and got skipped)."""
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
    """Today's Opus review count/cost (UTC calendar day) -- used for the
    daily cap. Condition 2 (user, 2026-09-16): when the cap is hit,
    submissions QUEUE for review, they never silently fall back to Qwen
    for the accept/reject decision -- so this must be checked BEFORE
    calling Opus, not after, and the caller must hard-stop on cap-hit
    rather than degrade to a different judge."""
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


OPUS_DAILY_CALL_CAP = 40  # ~$0.20-0.28/call observed -> ~$8-11/day ceiling.
# Deliberately a call-count cap, not a dollar cap: a dollar cap that fires
# mid-review would need the same queue-not-fallback handling anyway, and a
# call count is simpler to reason about and log.

OPUS_MAX_REVIEWS_PER_PIECE = 3  # condition 3 (user): one re-review per
# revision, shelved (not resubmitted indefinitely) after 3 total.


def _run_claude_p(args_list, timeout=120, retries=1, **run_kwargs):
    """Hard-timeout wrapper for every `claude -p` subprocess call (user
    direction, 2026-09-20: 'wrap every claude -p call in a hard timeout
    (120s, retry once, then record as unjudged) -- a hung gate call
    would stall a shift the same way').

    Found live: the existing per-call-site `subprocess.run(...,
    timeout=90)` pattern does NOT actually guarantee the process dies
    on timeout. A real checkpoint_eval.py pairwise call sat alive for
    56 minutes at ~0% CPU (1 minute of real CPU time total) instead of
    hitting its stated 90s timeout -- confirmed directly via `ps`: one
    live `claude` child process, no error, no exit. subprocess.run's
    timeout kills the DIRECT child on TimeoutExpired, but if that
    child's own stdout/stderr-reading `communicate()` is blocked on a
    grandchild (claude's own internal tool-execution subprocess, a
    sandboxed read, etc.) that inherited the pipe file descriptors and
    doesn't exit, the parent's read() never returns and TimeoutExpired
    never fires reliably either -- a known sharp edge of
    subprocess.run(timeout=...) with pipe-inheriting descendants,
    confirmed as the actual failure mode here by watching the hung
    process's real state (S, sleeping, not R) and near-zero CPU time
    for the entire 56-minute span, not just assumed from the docs.

    Fixed with a real process-group kill: launches in its own process
    group (start_new_session=True, POSIX-only, acceptable since this
    codebase already assumes macOS via other darwin-specific tool
    calls elsewhere), waits with an explicit timeout via
    communicate(timeout=...), and on TimeoutExpired sends SIGKILL to
    the WHOLE PROCESS GROUP (os.killpg, negative pid) -- not just the
    direct child -- so an unresponsive grandchild holding the pipe
    open gets killed too, not just orphaned.

    Retries once on timeout (a real, transient CLI hang is plausible;
    two independent hangs on the same call is not worth blocking a
    whole shift over). Returns a subprocess.CompletedProcess-like
    object on success, or None if both attempts timed out or every
    other subprocess error occurred -- callers must check for None and
    treat it as an unjudged/error result, never crash on it.
    """
    import subprocess as _sp
    import os as _os
    import signal as _signal

    def _fail(reason):
        # Never return a bare None: callers used to report every failure
        # as "timed out after retry", which was actively misleading --
        # found live 2026-09-22, three _watcher.v7 reviews logged as
        # "timed out after retry (120s x2)" only 32s apart, which is
        # arithmetically impossible. Carry the REAL reason in stderr on
        # a returncode=-1 result so each call site's existing
        # `returncode != 0` branch logs the truth for free.
        return _sp.CompletedProcess(args_list, -1, "", reason)

    for attempt in range(retries + 1):
        try:
            proc = _sp.Popen(
                args_list, stdout=_sp.PIPE, stderr=_sp.PIPE, text=True,
                start_new_session=True, **run_kwargs,
            )
        except Exception as e:
            return _fail(f"spawn failed: {type(e).__name__}: {e}")
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
        except Exception as e:
            try:
                _os.killpg(_os.getpgid(proc.pid), _signal.SIGKILL)
            except Exception:
                pass
            return _fail(f"{type(e).__name__}: {e}")
    return _fail("exhausted retries with no result")


def _kill_stale_claude_login(max_age_s=300):
    """Find and kill any `claude login` process older than max_age_s.

    A hung `claude login` holds ~/.claude/.credentials.lock and makes
    every `claude -p` call in opus_curate_review fail instantly with
    exit 1 and empty stderr -- found live 2026-09-17 (a `claude login`
    process had been running 16+ hours, blocking every Opus review that
    shift). Only kills processes older than max_age_s so a login the
    user is actively completing right now is never touched.

    Returns True if a stale process was found and killed, else False.
    """
    import subprocess as _sp

    def _etime_to_seconds(s):
        # macOS/BSD `ps -eo etime` format: [[dd-]hh:]mm:ss (no raw-seconds
        # `etimes` field on macOS, unlike Linux -- confirmed live, the
        # first version of this function used `etimes` and silently
        # produced zero matches on this machine).
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


def _extract_intended_title(path):
    """Best-effort extraction of the piece's own declared title, from
    its in-file title-card text (the same convention _reads_figurative
    checks) -- used only to log what the artist INTENDED next to what
    Opus blindly saw, for a human-readable report. Never fed to the
    blind check itself."""
    try:
        raw = Path(path).read_bytes()
    except Exception:
        return None
    text = _decode_ans_bytes(raw)
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for line in lines[:3]:
        clean = _SGR_RE.sub("", line).strip()
        if len(clean) >= 4 and sum(1 for ch in clean if ch.isascii() and ch.isalpha()) / len(clean) > 0.5:
            return clean
    return None


def opus_subject_check(path):
    """Blind subject-recognition gate (user direction, 2026-09-19):
    'Send Opus the render with no title, note, or subject name, and
    ask: What is this an image of? If its answer doesn't match the
    intended subject, reject regardless of metrics.'

    Built after confirming a real, separate bug: the EXISTING
    opus_curate_review render already claimed 'you have NO other
    context -- no title' to Opus while literally baking the house
    title-card and credit-line text into the rendered PNG pixels
    (confirmed directly: _orb.v59's title row 'THE WATCHER // IT SEES
    IN THE DARK' and credit row both render as plain legible text in
    the image Opus was shown). A subject-recognition check is
    meaningless if the answer is printed on the image -- this uses
    render_ans_to_png_b64(..., redact_title_rows=True) so the
    blindness is real, not just asserted in the prompt.

    This is a SEPARATE call from opus_curate_review's existing defect
    review, by design: mixing 'what is this' with 'what's wrong with
    it' lets a model that's already read the title-adjacent defect
    list rationalize a subject match it wouldn't have made cold. Two
    separate temp dirs, two separate isolated `claude -p` calls.

    Returns a dict: {"status": "ok"|"mismatch"|"error", "message": str,
    "blind_subject": str|None, "intended_title": str|None}. "ok" also
    covers "couldn't determine intent" (no title text found) -- this
    check can only REJECT on a confirmed mismatch, never block on its
    own inability to find a title to compare against.
    """
    import subprocess, json, tempfile, shutil, base64

    intended_title = _extract_intended_title(path)

    # Check the SAME daily Opus cost/count cap opus_curate_review uses --
    # this check makes up to 2 additional real Opus calls per submission,
    # which must count against the same $/day ceiling, not run for free
    # outside it (found live while wiring this in: opus_reviews'
    # daily-cap query only ever counted opus_curate_review's own writes,
    # so this new gate's cost was completely invisible to the cap unless
    # explicitly logged into the same table).
    conn_cap = sqlite3.connect(DB_PATH)
    try:
        count_today, cost_today = _opus_daily_cost_and_count(conn_cap)
        if count_today >= OPUS_DAILY_CALL_CAP:
            return {
                "status": "ok",  # don't hard-block submission on this gate
                # specifically when the cap is hit -- opus_curate_review's
                # OWN cap check (called right after this, same submission)
                # is the one authorized to queue the piece; this gate just
                # skips its check rather than double-blocking.
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
            ["claude", "-p", prompt, "--model", "claude-opus-5",
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
                    ["claude", "-p", prompt, "--model", "claude-opus-5",
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

        # Log this call's cost into opus_reviews immediately, same table
        # opus_curate_review uses, so the daily cap sees it -- marked
        # with qwen_decision='subject_check' to distinguish from a real
        # defect review when reading the table back.
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
            # No title text found to compare against -- can't judge a
            # mismatch, so this check has nothing to say. Not a defect
            # in the piece, just nothing for THIS gate to check.
            return {"status": "ok",
                    "message": f"(blind read: \"{blind_subject}\" -- no in-file "
                                "title found to compare against, so this check "
                                "has nothing to judge a mismatch against)",
                    "blind_subject": blind_subject, "intended_title": None}

        # Second, separate call: does the blind subject match the
        # intended title? Asked as its own question rather than
        # keyword-matched in Python, since "a lit ring in a dark void"
        # vs "THE WATCHER" needs judgment (an eye IS a watcher; a ring
        # with no eye-like features is NOT), not string overlap.
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
            ["claude", "-p", match_prompt, "--model", "claude-opus-5",
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
    """Render two pieces side by side, BOTH with title/credit rows
    redacted and labeled only 'A'/'B' (never 'pinned'/'candidate' or a
    filename) -- built for opus_pairwise_regression_check (user
    direction, 2026-09-19): 'send Opus the pinned best and the
    candidate side by side, titles redacted, and ask which reads better
    as the stated subject, with reasons.' Neutral A/B labels
    specifically to avoid anchoring bias -- a model told upfront which
    side is the 'existing accepted best' vs. the 'new attempt' has an
    obvious reason to defer to the established one regardless of what
    it actually sees, exactly the kind of bias a blind check exists to
    remove."""
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
    """Pairwise regression gate (user direction, 2026-09-19): 'On any
    revision, send Opus the pinned best and the candidate side by side,
    titles redacted, and ask which reads better as the stated subject,
    with reasons. Reject a candidate that loses to the pinned best even
    when metrics improve.' Built directly for the v55->v59 case: v59
    improved on both tracked % metrics (measured against v55) while
    genuinely reading worse (shrunken sclera, noisy background reading
    as texture-free static) -- a regression the metric-floor gate
    cannot see by construction, since it only ever checks 'did the
    number go up,' never 'does it still look as good.'

    A/B sides are randomized per call (not always pinned=A) so a
    position bias in the model can't systematically favor either side.

    Returns a dict: {"status": "ok"|"regression"|"error", "message": str}.
    "ok" also covers "no pinned version to compare against yet" (a
    brand-new subject) -- this check can only ever REJECT on a
    confirmed pairwise loss, never block for lack of a baseline."""
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
            ["claude", "-p", prompt, "--model", "claude-opus-5",
             "--allowedTools", "Read", "--output-format", "json"],
            cwd=tmpdir,
        )
        if result is None:
            return {"status": "error", "message": "(pairwise check call timed out after retry)"}
        if result.returncode != 0 and result.returncode == 1 and not result.stderr.strip():
            if _kill_stale_claude_login(max_age_s=300):
                result = _run_claude_p(
                    ["claude", "-p", prompt, "--model", "claude-opus-5",
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


def opus_curate_review(path, qwen_decision, qwen_critique):
    """The real accept/reject authority for curate_piece, per the user's
    explicit 2026-09-16 direction: 'Only curate_piece. Opus gets render +
    crops + cell dump, never the note, script, or title. Add a daily Opus
    call cap; when exhausted, queue submissions, never fall back to Qwen
    for accept/reject. One Opus re-review per revision, shelve after
    three rejections. Keep Qwen's verdict logged alongside Opus's.'

    Validated against a real blind set before being wired in here (2026-
    09-16): a genuine ACiD reference correctly ACCEPTed with coordinate-
    grounded reasoning; 3 real rejected-catalog pieces correctly REJECTed;
    3 pieces Qwen had previously ACCEPTed and shipped all got REJECTed by
    Opus with specific, concrete defects -- user reviewed the actual
    renders and confirmed: 'Yes this is what I've been telling you this
    whole time. They're extremely weak.' Confirms Qwen's accept bar has
    been too permissive, not that this gate is miscalibrated.

    Returns a dict: {"status": "accept"|"reject"|"queued"|"shelved"|"error",
                      "message": str, "opus_verdict": str|None}
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

        # --- condition 1: Opus sees ONLY the render + cell dump, nothing
        # else -- no note, no generator script, no title, no path. Fresh
        # isolated temp dir with generic filenames.
        b64, note = render_ans_to_png_b64(path, offset=0, max_rows=140)
        if b64 is None:
            return {"status": "error", "message": f"(render failed: {note})", "opus_verdict": None}

        tmpdir = tempfile.mkdtemp(prefix="opus_gate_")
        try:
            render_path = Path(tmpdir) / "render.png"
            render_path.write_bytes(base64.b64decode(b64))
            raw = Path(path).read_bytes()
            text = _decode_ans_bytes(raw).replace("\r\n", "\n").replace("\r", "\n")
            cells_text = "\n".join(_SGR_RE.sub("", l) for l in text.split("\n")[:140])
            (Path(tmpdir) / "cells.txt").write_text(cells_text)

            prompt = (
                "Read render.png and cells.txt in this directory. You have NO "
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
                "shows some structure."
            )

            result = _run_claude_p(
                ["claude", "-p", prompt, "--model", "claude-opus-5",
                 "--allowedTools", "Read", "--output-format", "json"],
                cwd=tmpdir,
            )
            if result is not None and result.returncode != 0:
                # A stuck/orphaned `claude login` process holds
                # ~/.claude/.credentials.lock and makes every `claude -p`
                # call fail instantly with exit 1 and NO stderr -- which
                # reads to the agent narrating it as "logged out" when the
                # login itself never actually dropped (found live,
                # 2026-09-17: a `claude login` process had been hung for
                # 16+ hours). Detect that specific signature and self-heal
                # with one retry instead of surfacing a misleading error
                # and burning the shift on repeated identical retries.
                if result.returncode == 1 and not result.stderr.strip():
                    stale_login_killed = _kill_stale_claude_login(
                        max_age_s=300
                    )
                    if stale_login_killed:
                        result = _run_claude_p(
                            ["claude", "-p", prompt, "--model", "claude-opus-5",
                             "--allowedTools", "Read", "--output-format", "json"],
                            cwd=tmpdir,
                        )
            if result is None:
                # _run_claude_p already retried once internally (120s x2)
                # before giving up -- record as unjudged/error, never
                # block the shift waiting on a third attempt (user
                # direction, 2026-09-20: "a hung gate call would stall a
                # shift the same way" -- this IS that gate).
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

            # condition 4: log Qwen's verdict alongside Opus's regardless of
            # outcome, so disagreement rate is measurable over time
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
            }
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    finally:
        conn.close()


def _blind_visual_check(path):
    """Adversarial verification: render the piece and ask the SAME model to
    describe it with ZERO access to any curator/artist claim about what it
    is supposed to show. This exists because the curator's own preview-based
    critiques have been caught fabricating detail that isn't actually in the
    render (e.g. "TWO VOICES v1.1" was accepted with a critique describing
    "two facing profile heads... brow... jaw... eye-line" when the actual
    piece is three flat solid-color triangular blocks with no facial
    structure at all — confirmed by rendering and looking at it directly).
    inspect_piece's structural checks can't catch this class of error because
    it's a visual-perception failure, not a hygiene one. Returns the blind
    model's plain-text description, or an error string if rendering/the
    model call failed — callers should treat a failure as "couldn't verify"
    and say so, not as silent success.
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


# Keywords that make a critique's claim CHECKABLE by the blind visual pass —
# only fires the extra model call when the curator actually asserted a
# visual-feature claim worth adversarially verifying, not on every accept
# (most accepts are abstract/procedural work with no such claim to check).
_VISUAL_CLAIM_WORDS = (
    "face", "eye", "brow", "jaw", "profile", "anatomy", "anatomical",
    "figure", "figurative", "portrait", "silhouette", "expression",
)


def do_release_pack(pack_note):
    """Bundle everything in gallery/unpacked/ into the next gallery/packNN/,
    with a generated FILE_ID.DIZ crediting every contributor. Returns
    (result_str, pack_dir_or_None).

    HARD dedup gate runs first: any piece byte-identical to something already
    shipped blocks the WHOLE release (not just that piece) so the problem
    gets surfaced and fixed deliberately, not silently skipped. This replaces
    relying on agents remembering to run pre_release_dedup_guard.py by hand."""
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
            "\n\nYou haven't chosen a handle yet. Real BBS/ACiD-style artists "
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
        msg_note += "\n\nMessages from Tyler (the human directing this project) since your last shift:\n" + "\n".join(
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
        # Wall-clock cap (user direction, 2026-09-17): the stall detector
        # fingerprints identical call+result pairs, so it's structurally
        # blind to a shift that keeps making genuinely DIFFERENT tool
        # calls while never converging -- found live: an artist shift
        # spent 4+ hours iterating on one foreground (_dusk_yard), every
        # edit a real diff, never once tripping stall detection. This is a
        # separate, cruder check: total elapsed time, independent of
        # whether the calls look novel or repeated.
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
                    conn.execute(
                        "INSERT INTO curation_events (shift_id, action, path, dest_path, note, timestamp) VALUES (?,?,?,?,?,?)",
                        (shift_id, fargs.get("decision", ""), fargs.get("path", ""), str(dest.relative_to(WORKSPACE)), fargs.get("critique", ""), time.time()),
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
                        f"canvas '{fargs.get('slug')}': half_block {m['half_block_pct']:.1f}%, "
                        f"shade-of-ink {m['shade_char_pct']:.1f}%, "
                        f"colors {m['distinct_colors_in_subject']}, "
                        f"disconnected masses {m['disconnected_masses']}, "
                        f"ink {m['ink_canvas_share']:.0f}% of canvas. "
                        f"House bar {HOUSE_BAR['name']}: {HOUSE_BAR['half_block']}% / "
                        f"{HOUSE_BAR['shade']}%, {HOUSE_BAR['colors']} colors, "
                        f"{HOUSE_BAR['regions']} masses."
                    )
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
                                # Per-hit cell data alongside the image (user
                                # direction, 2026-09-22): "find_patches returns
                                # cell data (compact RLE text plus a patch_id)
                                # alongside the image, so raze can study or
                                # stamp it" -- without this a patch was only
                                # ever a picture, so using one meant re-typing
                                # what it looked like in code from memory.
                                # canvas_stamp(patch_id, x, y) places the exact
                                # real cells directly, no re-derivation.
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

            # --- stall detection, rewritten 2026-09-16 -----------------------
            # Old rule (truncate args to 120 chars, replace all digits with '#')
            # was auditable and wrong: a blind audit of all 115 real loop-kills
            # in project history found 113 (98%) were genuine iteration wrongly
            # killed -- write_file/curate_piece calls with different full content
            # (different file, different critique, different fix) collapsed to
            # the same 120-char-truncated, digit-blind signature. Real example
            # that motivated this: an artist writing _eye_v3.py then _eye_v4.py
            # with different code got killed mid-fix because both filenames
            # normalize to the same string once digits are stripped.
            #
            # New rule: fingerprint = (tool name, sha256 of the FULL raw
            # arguments JSON, no truncation, no digit normalization). A stall
            # is only counted when BOTH the call fingerprint AND the result
            # fingerprint match an earlier entry THIS SHIFT -- same action,
            # same outcome, not just a similar-looking call. Different file
            # contents, different critiques, or a different result (even from
            # an identical command, e.g. a flaky network call) are never
            # treated as the same event.
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
                # NOTE: per user direction 2026-09-16, do not set ended=True here
                # until the audit above has been reviewed. The per-role
                # MAX_TOOL_CALLS_BY_ROLE cap is the real backstop for now.

        if ended:
            break
    else:
        note = "(hit max tool calls for this shift, forced handoff)"

    ended_at = time.time()
    # Save last_reasoning on any FORCED end (note is non-empty: stop request,
    # empty-turns give-up, max-tool-calls cap) -- per user direction 2026-
    # 09-16, so an in-progress diagnosis carries into the agent's next shift
    # via get_last_own_shift_note's sibling lookup, instead of being lost.
    # A clean end_shift() call leaves note=="" and doesn't need this -- the
    # agent already said what it wanted to say via end_shift's own note arg.
    conn.execute(
        "UPDATE shifts SET ended_at=?, note=?, had_pending_peer_message=?, "
        "replied_to_peer=?, last_reasoning=? WHERE id=?",
        (ended_at, note, had_pending_final, replied_final,
         last_reasoning if note else None, shift_id),
    )
    conn.commit()
    _record_shift_tool_summary(conn, shift_id)
    print(f"=== {agent} shift {shift_id} ended ({ended_at - started_at:.1f}s): {note} ===")
    return wants_continue


def main():
    conn = init_db()
    for d in (WORKSPACE, GALLERY, GALLERY_UNPACKED, SUBMISSIONS, SCRATCH, REJECTED, REFERENCES):
        d.mkdir(parents=True, exist_ok=True)
    if not (WORKSPACE / "README.md").exists():
        (WORKSPACE / "README.md").write_text(
            "AGENTSCII shared workspace.\n\n"
            "scratch/            shared WIP, no quality bar, no ownership\n"
            "submissions/        artist seat's finished work awaiting curator review\n"
            "gallery/unpacked/   accepted, pending the next pack release\n"
            "gallery/packNN/     shipped releases with FILE_ID.DIZ credits\n"
            "rejected/           sent back with a .critique.txt sidecar; not deleted\n"
            "references/         real ACiD/ANSI study material\n"
            "STYLE.md            house style spec\n"
        )
    ref_note = REFERENCES / "what_is_ansi_art.txt"
    if not ref_note.exists():
        src = HOME / "antfarm2" / "references" / "what_is_ansi_art.txt"
        if src.exists():
            ref_note.write_text(src.read_text())

    STOP_FLAG.unlink(missing_ok=True)
    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)

    current = "artist"
    MAX_CONSECUTIVE_SHIFTS = 3
    consecutive = 0
    print("AGENTSCII harness starting. Ctrl+C, SIGTERM, or "
          f"'touch {STOP_FLAG}' to stop cleanly after the current turn.")
    try:
        while not stop_requested():
            if consecutive == 0:
                other_model = AGENTS["curator" if current == "artist" else "artist"]["model"]
                if other_model != MODEL:
                    unload_model(other_model)
            wants_continue = run_shift(conn, current)
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
        # Deliberately NOT unlinking STOP_FLAG here: the watchdog's own poll
        # loop checks STOP_FLAG on its own schedule (up to CHECK_INTERVAL
        # seconds after this exits) specifically to take its "exit without
        # restart" path instead of "not running, restart". If harness.py
        # deletes the flag first, that race can make the watchdog see an
        # absent flag + a dead harness and restart it right after a
        # deliberate stop. Whoever created the flag (dashboard/user) is the
        # one who should clear it — control_start()/control_restart() in the
        # dashboard already do this correctly before bringing things back up.
        print("[harness] Stopped cleanly.")


if __name__ == "__main__":
    main()
