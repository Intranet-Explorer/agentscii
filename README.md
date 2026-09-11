# AGENTSCII

Two local LLM agents, fixed roles, one explicit purpose: produce real
ANSI/ACiD-style textmode art (the 90s BBS artscene aesthetic) worth keeping.

Directed and quality-focused, on purpose — the opposite philosophy from
[antfarm2](https://github.com/Intranet-Explorer/antfarm2-standalone), which
has no assigned task and studies default agent behavior under zero
direction. This project starts from the harness antfarm2 proved out (shift
loop, loop-guard, cross-shift memory, tool-calling dispatch, SQLite
logging) but the purpose, roles, and pipeline are new.

## Roles

- **Artist** — makes pieces. Free to work in `scratch/` however it wants
  (character-by-character, procedural Python + chafa/jp2a conversion,
  remixing references), submits finished work via `submit_piece`.
- **Curator** — reviews everything the Artist submits, grounded in real
  reference pieces fetched from 16colo.rs / textfiles.com/artscene, not
  vibes. Accepts (`gallery/`) or rejects (`rejected/`, with a concrete,
  actionable critique) via `curate_piece`.

Same model both roles (`qwen3.8:27b-mlx`, stock/non-obliterated) — role comes entirely
from the system prompt. Model diversity wasn't the point here the way it
was in antfarm2; instruction-following and taste were the scarce resource,
so the strongest local model runs both seats.

## Workspace pipeline

```
workspace/
  scratch/       free WIP, no quality bar
  submissions/   artist's finished work awaiting curator review
  gallery/       curated, accepted pieces (with critique + note sidecars)
  rejected/      sent back with a .critique.txt sidecar — nothing deleted
  references/    real ACiD/ANSI study material
```

Nothing is ever destroyed. A rejection is feedback to act on, not a dead
end — the critique sidecar stays with the piece in `rejected/` so the
Artist can revise and resubmit.

## Human inbox

Direct the project mid-run from the dashboard's prompt box without ever
interrupting a live shift: messages queue in a `human_messages` table and
are delivered at the start of the recipient's next shift, exactly like
antfarm2's peer-to-peer `message_agent` pattern. Target the Artist, the
Curator, or both.

## Run it

```bash
cd ~/agentscii
python3 harness.py
# or, for auto-restart on crash:
nohup bash watchdog.sh > watchdog.log 2>&1 &
# stop cleanly any time:
touch STOP          # or Ctrl+C / SIGTERM
```

Dashboard (separate repo, `~/agentscii-dashboard/`):

```bash
cd ~/agentscii-dashboard
python3 server.py
# open http://127.0.0.1:8766
```

For persistence across reboots/crashes, see `launchd/README.md` — both the
watchdog and the dashboard can run as real macOS launchd agents, same
pattern as antfarm2.

## Status

New. First real shift (manual smoke test) confirmed the harness works
end-to-end against Ollama: the Artist agent, on a cold empty workspace,
fetched a real `.ans` file from 16colo.rs on its own and began studying it.
Not yet run under the full watchdog loop for an extended period.
