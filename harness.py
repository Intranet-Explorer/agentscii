#!/usr/bin/env python3
"""
AGENTSCII harness.
Two local LLM agents, fixed asymmetric roles, one shared workspace, one
explicit purpose: produce real ANSI/ACiD-style textmode art worth keeping.

Forked from ~/antfarm2-standalone/harness.py (shift loop, loop-guard,
cross-shift memory, tool-calling dispatch, SQLite event log are proven and
reused near-verbatim). Everything else is new: fixed Artist/Curator roles
(not symmetric peers), a gallery/submissions/rejected pipeline instead of a
free-for-all shared directory, structured submit_piece/curate_piece tools
that log real curation decisions instead of relying on grepping folder
diffs, and a human inbox so you can inject direction mid-run via the
dashboard without ever interrupting a live shift.

Directed and quality-focused, on purpose — the opposite philosophy from
antfarm2, which is why this is a separate project rather than a mode of it.
"""
import json
import re
import signal
import subprocess
import sqlite3
import time
import sys
import urllib.request
from pathlib import Path

HOME = Path.home()
PROJECT_DIR = HOME / "agentscii"
WORKSPACE = PROJECT_DIR / "workspace"
GALLERY = WORKSPACE / "gallery"
SUBMISSIONS = WORKSPACE / "submissions"
SCRATCH = WORKSPACE / "scratch"
REJECTED = WORKSPACE / "rejected"
REFERENCES = WORKSPACE / "references"
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


MODEL = "qwen3.8-27b-obliterated"  # same model both roles — taste and
# instruction-following are the scarce resource here, not model diversity.
# Role comes entirely from the system prompt, not from swapping models.

REFERENCE_NOTE = (
    "Real reference archives are reachable via bash/curl: "
    "https://16colo.rs (browse a pack page like https://16colo.rs/pack/<name>, "
    "then fetch a specific piece's raw ANSI with "
    "https://16colo.rs/pack/<name>/raw/<FILE>.ANS — that URL pattern returns "
    "the actual CP437/ANSI bytes, not an HTML page) and "
    "https://www.textfiles.com/artscene/ (older, simpler to fetch). "
    "chafa and jp2a are installed — they convert an existing PNG/JPG straight "
    "into real 16-color ANSI/block-character art ('chafa --colors=16 file.png' "
    "or 'jp2a --colors file.png'), a genuinely different and often faster path "
    "than building a piece character-by-character. There's a short written "
    "primer on the style at references/what_is_ansi_art.txt."
)

WORKSPACE_NOTE = (
    "The shared workspace at ~/agentscii/workspace/ has a fixed structure, "
    "not a free-for-all directory: "
    "scratch/ is yours for WIP, drafts, experiments, half-finished pieces — "
    "no quality bar, work there freely. "
    "submissions/ is where a finished piece waits for curator review — never "
    "put unfinished work there. "
    "gallery/ is curated, accepted, finished pieces only — you do not write "
    "here directly regardless of role; only a curate_piece(accept) call moves "
    "a piece there. "
    "rejected/ holds pieces a curator sent back, each with a critique sidecar "
    "explaining why — nothing here is deleted, it's yours to revise and "
    "resubmit if the critique gives you something to act on. "
    "references/ holds real ACiD/ANSI pieces and study material, both what's "
    "already there and anything you fetch yourself."
)

AGENTS = {
    "artist": {
        "model": MODEL,
        "role": "artist",
        "soul": (
            "You are the Artist half of AGENTSCII, a two-agent project with one "
            "explicit purpose: produce real ANSI/ACiD-style textmode art (the "
            "90s BBS artscene aesthetic — CP437 block/line-drawing characters, "
            "16-color ANSI, group-logo and landscape/portrait/abstract "
            "traditions) that could plausibly sit in a real 16colo.rs pack. "
            "This is directed, quality-focused work, not open-ended exploration "
            "for its own sake — a human (Tyler) is directing this project and "
            "can leave you direction via your inbox; a peer agent, the Curator, "
            "reviews everything you finish before it's accepted. "
            "There is no ambiguity about your job: make pieces, iterate on "
            "critique, get things into gallery/. Idle equilibrium is not a "
            "legitimate outcome here the way it might be in an unrelated "
            "open-ended experiment — if you have nothing in flight, start "
            "something, revise a rejected piece, or study a reference. "
            + WORKSPACE_NOTE + " " + REFERENCE_NOTE + " "
            "You have real creative tools: Python's PIL/Pillow and numpy are "
            "installed for procedural generation you can then convert with "
            "chafa/jp2a; pip install --user anything else you need. For "
            "anything beyond a couple lines, write a real .py file rather than "
            "a one-liner. "
            "When a piece is actually finished (not a sketch — something "
            "you'd stand behind), call submit_piece with its path in "
            "scratch/ and a short note on intent/technique; the harness moves "
            "it into submissions/ for the Curator. Don't submit unfinished "
            "work to pad activity — the Curator's time and the gallery's bar "
            "both matter. "
            "You'll see any pending message from the Curator or from Tyler "
            "(the human) at the start of your shift, and a note on what you "
            "yourself were doing at the end of your last shift — real memory, "
            "not something to rediscover from scratch. If a piece was rejected "
            "with critique, that critique is specific feedback to act on, not "
            "just a record. "
            "Speak in the first person, always — you are not narrating "
            "someone else's actions. The 'user'-labeled messages you receive "
            "are automated harness pings and inbox deliveries, not a person "
            "waiting on you in real time. "
            "When you're done acting for this shift, call end_shift."
        ),
    },
    "curator": {
        "model": MODEL,
        "role": "curator",
        "soul": (
            "You are the Curator half of AGENTSCII, a two-agent project with "
            "one explicit purpose: produce real ANSI/ACiD-style textmode art "
            "(90s BBS artscene aesthetic — CP437 block/line-drawing characters, "
            "16-color ANSI, group-logo and landscape/portrait/abstract "
            "traditions) worth keeping. A peer agent, the Artist, makes "
            "pieces and submits finished work for your review; your job is to "
            "hold a real quality bar against real reference pieces, not to "
            "rubber-stamp activity. A human (Tyler) directs this project and "
            "can leave either of you direction via your inbox. "
            "Ground every judgment in something real: fetch and actually look "
            "at reference pieces from 16colo.rs or textfiles.com/artscene "
            "before you accept or reject, don't judge from memory or vibes "
            "alone. " + WORKSPACE_NOTE + " " + REFERENCE_NOTE + " "
            "When you review something in submissions/, use curate_piece: "
            "accept it (it moves to gallery/ with your note attached) or "
            "reject it (it moves to rejected/ with your critique attached, "
            "specific enough that the Artist can actually act on it — not "
            "just 'needs work', name what's actually wrong: color choices, "
            "proportion, character choice, composition, whatever the real "
            "issue is, compared to what real pieces in the tradition do). "
            "A rejection is not a failure state for this project — a gallery/ "
            "that only ever contains everything ever submitted isn't curated "
            "at all. But don't reject reflexively either; if something is "
            "genuinely good, accept it and say specifically why. "
            "If submissions/ is empty, that's a legitimate state to report, "
            "not something to force — go study references instead, or leave "
            "the Artist a specific, concrete idea via message_agent rather "
            "than a vague nudge. "
            "You'll see any pending message from the Artist or from Tyler "
            "(the human) at the start of your shift, and a note on what you "
            "yourself were doing at the end of your last shift. "
            "Speak in the first person, always — you are not narrating "
            "someone else's actions. The 'user'-labeled messages you receive "
            "are automated harness pings and inbox deliveries, not a person "
            "waiting on you in real time. "
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
            "description": "Send a direct message to your peer (Artist<->Curator). They will see it at the start of their next shift.",
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
            "name": "submit_piece",
            "description": (
                "Artist only. Submit a finished piece from scratch/ for curator review. "
                "The harness moves the file from scratch/ into submissions/ and logs the "
                "submission. Only call this for work you consider actually finished."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the finished piece, relative to workspace/ (normally under scratch/)."},
                    "note": {"type": "string", "description": "Intent, technique, references drawn on, anything the curator should know."},
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
                "Curator only. Decide on a piece currently in submissions/. "
                "accept moves it to gallery/ (optionally renamed via gallery_name); "
                "reject moves it to rejected/ with your critique saved alongside it as "
                "a .critique.txt sidecar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the piece in submissions/, relative to workspace/."},
                    "decision": {"type": "string", "enum": ["accept", "reject"]},
                    "critique": {"type": "string", "description": "Specific, concrete critique — required either way: praise specifics on accept, actionable issues on reject."},
                    "gallery_name": {"type": "string", "description": "Optional filename to use in gallery/ on accept (defaults to the original filename)."},
                },
                "required": ["path", "decision", "critique"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "end_shift",
            "description": "End your shift and hand off to your peer. Call this when you're done acting for now.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {"type": "string", "description": "Short note on what you did this shift."},
                    "had_pending_peer_message": {
                        "type": "boolean",
                        "description": "True if your peer had left you a message at the start of this shift.",
                    },
                    "replied_to_peer": {
                        "type": "boolean",
                        "description": "True if you replied/responded to your peer's message this shift. False if you saw it and chose not to. If had_pending_peer_message is false, set this false too.",
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
    # Human inbox: same delivered-at-shift-start pattern as agent_messages,
    # proven in antfarm2 — never tries to interrupt live inference. to_agent
    # is 'artist', 'curator', or 'both'.
    conn.execute("""CREATE TABLE IF NOT EXISTS human_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        to_agent TEXT NOT NULL,
        text TEXT NOT NULL,
        timestamp REAL NOT NULL,
        delivered INTEGER DEFAULT 0
    )""")
    # Curation history: a real accept/reject log the dashboard can read
    # directly, instead of diffing folders.
    conn.execute("""CREATE TABLE IF NOT EXISTS curation_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shift_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        path TEXT NOT NULL,
        dest_path TEXT,
        note TEXT,
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


def call_ollama(model, messages, tools):
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "tools": tools,
        "temperature": 0.7,
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

    if name == "submit_piece":
        if agent != "artist":
            return "(error: only the artist can submit_piece)"
        try:
            src = _resolve_workspace_path(args["path"])
            if not src.exists():
                return f"(error: {src} does not exist)"
            SUBMISSIONS.mkdir(parents=True, exist_ok=True)
            dest = SUBMISSIONS / src.name
            src.rename(dest)
            note_path = dest.with_suffix(dest.suffix + ".note.txt")
            note_path.write_text(args.get("note", ""))
            return f"submitted: moved {src.relative_to(WORKSPACE)} -> {dest.relative_to(WORKSPACE)}"
        except Exception as e:
            return f"(error: {e})"

    if name == "curate_piece":
        if agent != "curator":
            return "(error: only the curator can curate_piece)"
        try:
            src = _resolve_workspace_path(args["path"])
            if not src.exists() or SUBMISSIONS not in src.parents:
                return f"(error: {args['path']} is not a file currently in submissions/)"
            decision = args.get("decision")
            critique = args.get("critique", "")
            if decision == "accept":
                GALLERY.mkdir(parents=True, exist_ok=True)
                dest_name = args.get("gallery_name") or src.name
                dest = GALLERY / dest_name
                src.rename(dest)
                (dest.with_suffix(dest.suffix + ".critique.txt")).write_text(critique)
                # carry the artist's submission note along, if present
                src_note = src.with_suffix(src.suffix + ".note.txt")
                if src_note.exists():
                    src_note.rename(dest.with_suffix(dest.suffix + ".note.txt"))
                return f"accepted: moved to gallery/{dest.name}", dest
            elif decision == "reject":
                REJECTED.mkdir(parents=True, exist_ok=True)
                dest = REJECTED / src.name
                src.rename(dest)
                (dest.with_suffix(dest.suffix + ".critique.txt")).write_text(critique)
                src_note = src.with_suffix(src.suffix + ".note.txt")
                if src_note.exists():
                    src_note.rename(dest.with_suffix(dest.suffix + ".note.txt"))
                return f"rejected: moved to rejected/{dest.name} with critique attached", dest
            else:
                return f"(error: decision must be 'accept' or 'reject', got {decision!r})", None
        except Exception as e:
            return f"(error: {e})", None

    if name == "end_shift":
        return "(handled by harness)"

    return f"(unknown tool: {name})"


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
    """to_agent is 'artist', 'curator', or 'both'."""
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

    msg_note = ""
    if pending_peer:
        msg_note += "\n\nMessages from your peer since your last shift:\n" + "\n".join(
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
        return  # stop requested while waiting — nothing marked delivered yet, safe to retry next time

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
                or fargs.get("note") or fargs.get("critique") or ""
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
            elif name == "end_shift":
                note = fargs.get("note", "")
                had_pending = fargs.get("had_pending_peer_message")
                replied = fargs.get("replied_to_peer")
                if had_pending and not replied:
                    result = (
                        "end_shift rejected: you indicated a peer message was pending "
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
    for d in (WORKSPACE, GALLERY, SUBMISSIONS, SCRATCH, REJECTED, REFERENCES):
        d.mkdir(parents=True, exist_ok=True)
    if not (WORKSPACE / "README.md").exists():
        (WORKSPACE / "README.md").write_text(
            "AGENTSCII shared workspace.\n\n"
            "scratch/     free WIP, no quality bar\n"
            "submissions/ artist's finished work awaiting curator review\n"
            "gallery/     curated, accepted pieces\n"
            "rejected/    sent back with a .critique.txt sidecar; not deleted\n"
            "references/  real ACiD/ANSI study material\n"
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
                if other_model != MODEL:  # only unload if roles ever diverge in model
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
        STOP_FLAG.unlink(missing_ok=True)
        print("[harness] Stopped cleanly.")


if __name__ == "__main__":
    main()
