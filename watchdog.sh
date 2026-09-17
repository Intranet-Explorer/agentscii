#!/usr/bin/env bash
# AGENTSCII watchdog: keeps harness.py running, restarting it if it dies.
# Ported from antfarm2-standalone/watchdog.sh — same self-healing behavior,
# same STOP-flag contract.
#
# Usage: nohup bash watchdog.sh > watchdog.log 2>&1 &
# Stop:  touch STOP

set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# launchd runs this with a minimal PATH (no Homebrew) - export a real one so
# harness.py's bash tool calls can actually find things like chafa/jp2a.
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:$PATH"

STOP_FLAG="$DIR/STOP"
LOG="$DIR/harness.log"
WATCHDOG_LOG="$DIR/watchdog.log"
CHECK_INTERVAL=30

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$WATCHDOG_LOG"
}

is_harness_running() {
    pgrep -f "$DIR/harness\.py" > /dev/null 2>&1
}

harness_pid_count() {
    pgrep -f "$DIR/harness\.py" | wc -l | tr -d ' '
}

# Backstop for the harness-side self-heal in opus_curate_review(): a stuck
# `claude login` process holds ~/.claude/.credentials.lock and makes every
# `claude -p` call (the Opus curator gate) fail instantly with exit 1 and
# no stderr. Found live 2026-09-17 (a `claude login` had been hung 16+
# hours, silently blocking every curate_piece review that whole shift).
# Only kill ones older than 5 minutes so a login the user is actively
# completing right now is never touched.
#
# macOS `ps` has no `etimes` (raw-seconds) field, only `etime`, formatted
# as [[dd-]hh:]mm:ss -- awk below converts that to seconds inline.
kill_stale_claude_login() {
    local candidates
    candidates=$(ps -eo pid,etime,command | awk '
        /claude login/ && !/awk/ {
            split($2, t, "-")
            if (length(t) == 2) { days = t[1]; rest = t[2] }
            else { days = 0; rest = t[1] }
            n = split(rest, p, ":")
            if (n == 3) { secs = p[1]*3600 + p[2]*60 + p[3] }
            else if (n == 2) { secs = p[1]*60 + p[2] }
            else { secs = p[1] }
            secs += days * 86400
            print $1, secs
        }
    ')
    [ -z "$candidates" ] && return
    echo "$candidates" | while read -r pid age; do
        [ -z "$pid" ] && continue
        if [ "$age" -ge 300 ]; then
            log "killing stale 'claude login' pid $pid (running ${age}s)"
            kill "$pid" 2>/dev/null
        fi
    done
}

start_harness() {
    local count
    count=$(harness_pid_count)
    if [ "$count" -gt 0 ]; then
        log "refusing to start: $count harness.py process(es) already running (pgrep: $(pgrep -f "$DIR/harness\.py" | tr '\n' ' '))"
        return
    fi
    log "starting harness.py"
    ( python3 "$DIR/harness.py" 2>&1 | tee -a "$LOG" ) &
}

log "watchdog started (checking every ${CHECK_INTERVAL}s)"

if [ -f "$STOP_FLAG" ]; then
    log "STOP flag present at startup - not starting harness.py, exiting"
    exit 0
fi

if ! is_harness_running; then
    start_harness
fi

while true; do
    sleep "$CHECK_INTERVAL"

    if [ -f "$STOP_FLAG" ]; then
        log "STOP flag present - watchdog exiting without restarting"
        exit 0
    fi

    kill_stale_claude_login

    if ! is_harness_running; then
        log "harness.py not running - restarting"
        start_harness
    fi
done
