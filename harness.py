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
import json
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
    "as <a href=\"/pack/<name>/<FILE>.ANS\"> links; fetch one directly with "
    "curl, e.g. 'curl -s https://16colo.rs/pack/acdu0193/ACID93.ANS' returns "
    "the real CP437/ANSI bytes, not an HTML page (a /raw/ prefix before the "
    "filename also works, same content). "
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


def do_release_pack(pack_note):
    """Bundle everything in gallery/unpacked/ into the next gallery/packNN/,
    with a generated FILE_ID.DIZ crediting every contributor. Returns
    (result_str, pack_dir_or_None)."""
    GALLERY_UNPACKED.mkdir(parents=True, exist_ok=True)
    pieces = [
        f for f in sorted(GALLERY_UNPACKED.iterdir())
        if f.is_file() and not f.name.endswith((".note.txt", ".critique.txt", ".credits.txt"))
    ]
    if not pieces:
        return "(error: gallery/unpacked/ is empty, nothing to release)", None

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
    for i in range(MAX_TOOL_CALLS_PER_SHIFT):
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
            fuzzy_sig = (name, normalized_arg)
            recent_calls.append(fuzzy_sig)
            recent_calls = recent_calls[-6:]
            if recent_calls.count(fuzzy_sig) >= 3:
                note = f"(loop detected: '{name}' called near-identically 3x in a row, forced end)"
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
