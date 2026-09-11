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

if ! is_harness_running; then
    start_harness
fi

while true; do
    sleep "$CHECK_INTERVAL"

    if [ -f "$STOP_FLAG" ]; then
        log "STOP flag present - watchdog exiting without restarting"
        exit 0
    fi

    if ! is_harness_running; then
        log "harness.py not running - restarting"
        start_harness
    fi
done
