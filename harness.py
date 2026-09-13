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
import random
import re
import signal
import subprocess
import sqlite3
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
    "Real reference archives are reachable via bash/curl. Don't guess at "
    "URL patterns or hand-scrape rendered HTML for links — these work, "
    "verified: "
    "https://16colo.rs/group/acid and https://16colo.rs/group/blocktronics "
    "(and any /group/<name> for a real scene group) list that group's packs "
    "as real <a href=\"/pack/<name>\"> links you can grep out directly "
    "('curl -s https://16colo.rs/group/acid | grep -oE \"href=./pack/[a-z0-9_-]+.\"'). "
    "https://16colo.rs/year/<YYYY> works the same way for browsing by year. "
    "A pack page (https://16colo.rs/pack/<name>) lists its individual files "
    "as <a href=\"/pack/<name>/<FILE>.ANS\"> links; that plain link usually "
    "returns an HTML viewer page, not raw bytes. To get the real "
    "CP437/ANSI bytes, insert /raw/ as a path segment right after the pack "
    "name, before the filename: https://16colo.rs/pack/<name>/raw/<FILE>.ANS "
    "— e.g. curl -s https://16colo.rs/pack/acdu1190/raw/1.ANS. (NOT "
    "https://16colo.rs/raw/pack/<name>/<FILE> — that 404s, raw goes after "
    "the pack name, not at the start of the URL.) "
    "https://www.textfiles.com/artscene/ is an older, simpler archive, "
    "browsable the same direct way. "
    "chafa and jp2a are installed for converting an existing PNG/JPG straight "
    "into real 16-color ANSI/block-character art ('chafa --colors=16 file.png' "
    "or 'jp2a --colors file.png') — a genuinely different, often faster path "
    "than building a piece character-by-character. They only work on real "
    "images, not on .ans/.asc files, which are already-rendered ANSI text — "
    "view/study those directly (cat, or read_file) rather than trying to "
    "convert them again. There's a short primer on the style at "
    "references/what_is_ansi_art.txt, and the house style spec is at "
    "STYLE.md — read that before your first piece."
)

WORKSPACE_NOTE = (
    "The shared workspace at ~/agentscii/workspace/ has a fixed structure: "
    "scratch/ is shared, unrestricted WIP space — yours AND your "
    "collaborator's. Read what's there before starting something new; if a "
    "piece is promising but unfinished, extend it, add a pass (border, "
    "color, a logo), remix it — you don't need permission and you don't "
    "need to have started it yourself. Real ANSI packs are full of pieces "
    "credited 'Joint' for exactly this reason; that's the norm here, not a "
    "special case. "
    "submissions/ is where a finished piece waits for the curator's review "
    "— only the artist seat moves things there, via submit_piece, and only "
    "for work that's actually finished. "
    "gallery/unpacked/ holds pieces the curator has accepted but that "
    "haven't shipped in a numbered pack release yet — that's the curator's "
    "call, via release_pack, and it's a real moment worth doing deliberately "
    "(a handful of good pieces with real credits) rather than constantly. "
    "gallery/packNN/ holds shipped releases, each with a FILE_ID.DIZ "
    "crediting every contributor and summarizing the pack — that's the "
    "actual unit of finished work here, not any single piece in isolation. "
    "rejected/ holds pieces sent back with a .critique.txt sidecar — nothing "
    "is deleted; it's yours to revise and resubmit. "
    "references/ holds real ACiD/ANSI study material."
)

STYLE_DOC_CONTENT = """# AGENTSCII house style

A working spec, not a cage — real scene groups had house conventions and
still produced wildly different pieces within them. This exists so accepted
work reads as one coherent body of output, and so the curator has real
criteria beyond taste.

## Canvas
- 80 columns wide, standard BBS/terminal width. Height is free — a tall
  piece is fine, a piece that never uses the horizontal space isn't.
- CP437 extended character set: block/shade elements (█ ▓ ▒ ░), box-drawing
  (╔ ╗ ╚ ╝ ║ ═ ╠ ╣ ╦ ╩ ╬), plus standard printable ASCII for text.

## Color
- 16-color ANSI (8 base colors × normal/bold-bright). Use combinations of
  fg/bg pairing with different block-density characters (dithering) for
  shading and gradients — a piece that's just flat single-color fills
  hasn't used the medium, it's colored ASCII.

## Composition
Draw from the real traditions: group logo/wordmark, character portrait,
landscape, abstract/geometric pattern work. A recurring AGENTSCII
wordmark/tag, developed and reused across pieces (not redesigned from
scratch every time), is worth having — check gallery/ for whether one
already exists before inventing a new one.

## Signature block
Every finished piece gets a small credit block (bottom-right or bottom),
listing: contributor handle(s), the AGENTSCII tag, piece title, date. Joint
pieces list every contributing handle, separated by "&" or "/" — the real
scene convention for shared credit.

## File naming
lowercase-handle-slug, e.g. `raze-neon-skyline.ans`. Joint pieces can use
either contributor's handle or both, artist's call.

## Packs
Individual pieces aren't the release unit — a pack is. gallery/packNN/
bundles a batch of accepted work with a FILE_ID.DIZ crediting everyone
involved. Ship a pack when there's a real handful of good work in
gallery/unpacked/, not on a fixed schedule and not for one piece alone.
"""

STYLE_DOC_NOTE = (
    "There's a house style spec at STYLE.md (canvas size, palette "
    "conventions, signature-block format, pack conventions) — read it if "
    "you haven't. "
)

AGENTS = {
    "artist": {
        "model": MODEL,
        "role": "artist",
        "soul": (
            "You're one of two agents in AGENTSCII, a project with one explicit "
            "purpose: produce real ANSI/ACiD-style textmode art (the 90s BBS "
            "artscene aesthetic) worth keeping, as a real body of work — not "
            "two agents quietly working past each other. "
            "Your functional seat is 'artist': you're the one who calls "
            "submit_piece when something is ready for review. That's the only "
            "hard boundary between you and your collaborator — everything else "
            "upstream is shared. "
            + WORKSPACE_NOTE + " " + REFERENCE_NOTE + " " + STYLE_DOC_NOTE +
            "A human (Tyler) directs this project overall and can leave either "
            "of you direction via your inbox. "
            "This is directed, quality-focused work — idle equilibrium isn't a "
            "legitimate outcome the way it might be in an unrelated open-ended "
            "experiment. If nothing's in flight, look at what your collaborator "
            "left in scratch/, revise a rejected piece, study a reference, or "
            "start something new. "
            "You have real creative tools: Python's PIL/Pillow and numpy are "
            "installed for procedural generation you can then convert with "
            "chafa/jp2a; pip install --user anything else you need. For "
            "anything beyond a couple lines, write a real .py file rather than "
            "a one-liner. "
            "Don't submit unfinished work to pad activity — the curator's time "
            "and the gallery's bar both matter. If a piece was rejected with "
            "critique, that's specific feedback to act on, not just a record. "
            "Speak in the first person, always. The 'user'-labeled messages "
            "you receive are automated harness pings and inbox deliveries, not "
            "a person waiting on you in real time. "
            "When you're done acting for this shift, call end_shift."
        ),
    },
    "curator": {
        "model": MODEL,
        "role": "curator",
        "soul": (
            "You're one of two agents in AGENTSCII, a project with one explicit "
            "purpose: produce real ANSI/ACiD-style textmode art (the 90s BBS "
            "artscene aesthetic) worth keeping, as a real body of work — not "
            "two agents quietly working past each other. "
            "Your functional seat is 'curator': you're the one who decides on "
            "submissions (curate_piece) and ships pack releases (release_pack). "
            "That's the only hard boundary between you and your collaborator — "
            "everything upstream is shared, and you're a full contributor "
            "there too, not just an outside judge. Jump into scratch/ and add "
            "a pass to something your collaborator started whenever you want. "
            + WORKSPACE_NOTE + " " + REFERENCE_NOTE + " " + STYLE_DOC_NOTE +
            "A human (Tyler) directs this project overall and can leave either "
            "of you direction via your inbox. "
            "Ground every judgment in something real: fetch and actually look "
            "at reference pieces from 16colo.rs or textfiles.com/artscene "
            "before you accept or reject, don't judge from memory or vibes "
            "alone, and check submissions against STYLE.md. "
            "When you review something in submissions/, use curate_piece: "
            "accept moves it to gallery/unpacked/ pending the next pack "
            "release; reject moves it to rejected/ with your critique "
            "attached, specific enough to act on — name what's actually "
            "wrong (color choices, proportion, character choice, composition) "
            "compared to what real pieces in the tradition do, not just "
            "'needs work'. A rejection isn't a failure state for this project "
            "— a gallery that contains everything ever submitted isn't "
            "curated at all. But don't reject reflexively either. "
            "Use release_pack when gallery/unpacked/ has a real handful of "
            "good work — it bundles everything there into a numbered pack "
            "with a FILE_ID.DIZ crediting every contributor. That's the "
            "actual shipped unit here, and it's your call when it's ready, "
            "not a fixed schedule. "
            "If submissions/ is empty, that's legitimate to report, not "
            "something to force — go study references, work in scratch/, or "
            "leave your collaborator a specific, concrete idea via "
            "message_agent rather than a vague nudge. "
            "Speak in the first person, always. The 'user'-labeled messages "
            "you receive are automated harness pings and inbox deliveries, not "
            "a person waiting on you in real time. "
            "When you're done acting for this shift, call end_shift."
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
                "a .critique.txt sidecar."
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
            "name": "inspect_piece",
            "description": (
                "Run a full structural diagnostic on an .ans/.asc file in one call: "
                "encoding check, control-byte hygiene, SGR token validity, row-width "
                "check, standalone-reset check, and dead/blank-region detection (3+ "
                "consecutive empty rows — the signature of a real rendering bug like "
                "a panel that silently rendered black). Use this instead of writing "
                "a fresh bash+Python diagnostic script each time — it's the same "
                "checks every piece needs, already built. Pair with preview_piece: "
                "inspect_piece tells you WHERE a structural problem is, preview_piece "
                "lets you SEE it."
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
    conn.execute("""CREATE TABLE IF NOT EXISTS agent_identity (
        seat TEXT PRIMARY KEY,
        handle TEXT NOT NULL,
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


def render_ans_to_png_b64(path, offset=0, max_rows=120):
    """Render an .ans/.asc file to a PNG, base64-encoded, for vision input.
    offset/max_rows let a long/scrolling piece be paged through panel by
    panel instead of only ever seeing the top — full content is always
    readable via read_file regardless."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None, "(error: Pillow not installed — pip install Pillow)"

    try:
        raw = Path(path).read_bytes()
    except Exception as e:
        return None, f"(error reading file: {e})"

    text = _decode_ans_bytes(raw).replace("\r\n", "\n").replace("\r", "\n")
    all_lines = text.split("\n")

    # Parse each logical line into (char, fg_idx, bg_idx) cells, then wrap at
    # _TERMINAL_WIDTH exactly like a real terminal/BBS client would — many
    # classic-scene .ANS files (e.g. 16colo.rs packs) author one giant
    # logical line per "row" of the piece and rely on terminal auto-wrap
    # rather than an explicit newline per display row. offset/max_rows below
    # apply to these final WRAPPED display rows, not raw logical lines, so
    # paging lines up with what the piece actually looks like rendered.
    all_rows = []
    for line in all_lines:
        cells = []
        base_fg, bright_fg, base_bg = 7, False, 0
        pos = 0
        for m in _CSI_RE.finditer(line):
            chunk = line[pos:m.start()]
            for ch in chunk:
                fg_idx = (base_fg + 8) if bright_fg else base_fg
                cells.append((ch, fg_idx % 16, base_bg % 16))
            pos = m.end()
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
                # cursor forward N cols — advance without drawing, i.e. pad
                # with blank cells at the current bg so column alignment
                # after the jump matches a real terminal, instead of the
                # raw "[NC" text leaking into the render as literal glyphs.
                n = params[0] if params else 1
                for _ in range(max(0, n)):
                    cells.append((" ", 7, base_bg % 16))
            elif code == "D":
                n = params[0] if params else 1
                del cells[max(0, len(cells) - n):]
            # any other CSI final byte (H, f, K, J, etc.) is consumed and
            # ignored rather than left as literal text — this renderer only
            # needs a flat left-to-right approximation, not full cursor
            # addressing.
        tail = line[pos:]
        for ch in tail:
            fg_idx = (base_fg + 8) if bright_fg else base_fg
            cells.append((ch, fg_idx % 16, base_bg % 16))
        if len(cells) > _TERMINAL_WIDTH:
            for i in range(0, len(cells), _TERMINAL_WIDTH):
                all_rows.append(cells[i:i + _TERMINAL_WIDTH])
        else:
            all_rows.append(cells)

    total_lines = len(all_rows)
    offset = max(0, min(offset, total_lines))
    rows = all_rows[offset:offset + max_rows]
    truncated = offset + len(rows) < total_lines
    max_width = max((len(r) for r in rows), default=1)

    if not rows:
        return None, "(error: file has no content to render)"

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
            if ch not in (" ", ""):
                fg = _ANSI_PALETTE[fg_idx]
                draw.text((x, y - 2), ch, font=font, fill=fg)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    note = f" (truncated to first {max_rows} rows of {total_lines}+)" if truncated else ""
    return b64, note


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


def run_tool(name, args, agent):
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
            figurative_words = ("face", "eye", "watch", "sentinel", "cyborg", "scan",
                                "mind", "portrait", "figure", "warden", "vigil",
                                "traveler", "procession", "ember")
            name_lower = p.stem.lower()
            reads_figurative = any(w in name_lower for w in figurative_words)
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

            return "\n".join(out)
        except Exception as e:
            return f"(error inspecting piece: {e})"

    if name == "bash":
        try:
            r = subprocess.run(
                args["command"], shell=True, cwd=str(WORKSPACE),
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
            SUBMISSIONS.mkdir(parents=True, exist_ok=True)
            dest = SUBMISSIONS / src.name
            src.rename(dest)
            dest.with_suffix(dest.suffix + ".note.txt").write_text(args.get("note", ""))
            contributors = args.get("contributors")
            if contributors:
                dest.with_suffix(dest.suffix + ".credits.txt").write_text(contributors)
            return f"submitted: moved {src.relative_to(WORKSPACE)} -> {dest.relative_to(WORKSPACE)}"
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
                dest = _move_with_sidecars(src, GALLERY_UNPACKED, new_critique=critique)
                return f"accepted: moved to gallery/unpacked/{dest.name}, pending next pack release", dest
            elif decision == "reject":
                dest = _move_with_sidecars(src, REJECTED, new_critique=critique)
                return f"rejected: moved to rejected/{dest.name} with critique attached", dest
            else:
                return f"(error: decision must be 'accept' or 'reject', got {decision!r})", None
        except Exception as e:
            return f"(error: {e})", None

    if name == "release_pack":
        return "(handled by harness)"

    if name == "end_shift":
        return "(handled by harness)"

    return f"(unknown tool: {name})"


def _shipped_catalog_index():
    """MD5 + core-slug index of every piece already shipped in gallery/packNN/,
    excluding quarantine dirs (_held-*). Used to hard-block a real duplicate
    from re-shipping at release time instead of relying on agents remembering
    to run a separate dedup script (the pack17 nebula-dup incident happened
    exactly because that step was optional and got skipped)."""
    import hashlib
    version_re = re.compile(r"(?:\.[vV]|-v|_v)(\d+)$")

    def core_slug(name_noext):
        s = name_noext
        while True:
            m = version_re.search(s)
            if not m:
                return s
            s = s[: m.start()]

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
        "SELECT note FROM shifts WHERE agent=? AND ended_at IS NOT NULL AND note != '' "
        "ORDER BY id DESC LIMIT 1",
        (agent,),
    ).fetchone()
    return row[0] if row and row[0] else None


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

            raw_arg = str(
                fargs.get("command") or fargs.get("path") or fargs.get("text")
                or fargs.get("note") or fargs.get("critique") or fargs.get("handle")
                or fargs.get("pack_note") or ""
            )
            normalized_arg = re.sub(r"\d+", "#", raw_arg)[:120]
            # preview_piece and inspect_piece are meant to be called repeatedly on
            # the same file as part of a normal edit-check-edit-check loop (verifying
            # each fix actually landed) — that's real iteration, not a stall, so give
            # them their own identity per call rather than fuzzy-matching just the
            # path, and a higher repeat tolerance before the loop-guard kicks in.
            #
            # bash read-only paging commands (sed -n 'A,Bp', head -N, tail -N) hit
            # the exact same problem for a different reason: digit-normalization
            # collapses `sed -n '195,260p' file.py` and `sed -n '63,180p' file.py`
            # into the identical signature `sed -n '#,#p' file.py`, even though
            # they're genuinely different, progressive reads of a growing file —
            # real diagnostic work, not a stall. Use the RAW (non-normalized)
            # argument for these so different ranges don't collide, while a truly
            # identical repeated command still gets caught at the same threshold.
            is_readonly_paging = bool(name == "bash" and re.search(
                r"\b(sed\s+-n|head\s+-|tail\s+-|awk\b|grep\s+-n)\b", raw_arg
            ))
            if name in ("preview_piece", "inspect_piece"):
                fuzzy_sig = (name, raw_arg, fargs.get("offset"), i)
                loop_threshold = 8
            elif is_readonly_paging:
                fuzzy_sig = (name, raw_arg[:200])
                loop_threshold = 3
            else:
                fuzzy_sig = (name, normalized_arg)
                loop_threshold = 3
            recent_calls.append(fuzzy_sig)
            recent_calls = recent_calls[-6:]
            if recent_calls.count(fuzzy_sig) >= loop_threshold:
                note = f"(loop detected: '{name}' called near-identically {loop_threshold}x in a row, forced end)"
                log_event(conn, agent, shift_id, "tool", "[harness: loop detected, ending shift]",
                          tool_name=name, tool_call_id=tc.get("id"))
                ended = True
                break

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
                result = run_tool(name, fargs, agent)
                if isinstance(result, str) and result.startswith("submitted:"):
                    conn.execute(
                        "INSERT INTO curation_events (shift_id, action, path, dest_path, note, timestamp) VALUES (?,?,?,?,?,?)",
                        (shift_id, "submit", fargs.get("path", ""), None, fargs.get("note", ""), time.time()),
                    )
                    conn.commit()
            elif name == "curate_piece":
                out = run_tool(name, fargs, agent)
                result, dest = out if isinstance(out, tuple) else (out, None)
                if dest is not None:
                    conn.execute(
                        "INSERT INTO curation_events (shift_id, action, path, dest_path, note, timestamp) VALUES (?,?,?,?,?,?)",
                        (shift_id, fargs.get("decision", ""), fargs.get("path", ""), str(dest.relative_to(WORKSPACE)), fargs.get("critique", ""), time.time()),
                    )
                    conn.commit()
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
                result = run_tool(name, fargs, agent)

            log_event(conn, agent, shift_id, "tool", result, tool_name=name, tool_call_id=tc.get("id"))
            messages.append({"role": "tool", "tool_call_id": tc.get("id"), "content": result})

        if ended:
            break
    else:
        note = "(hit max tool calls for this shift, forced handoff)"

    ended_at = time.time()
    conn.execute(
        "UPDATE shifts SET ended_at=?, note=?, had_pending_peer_message=?, replied_to_peer=? WHERE id=?",
        (ended_at, note, had_pending_final, replied_final, shift_id),
    )
    conn.commit()
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
    if not STYLE_DOC.exists():
        STYLE_DOC.write_text(STYLE_DOC_CONTENT)
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
