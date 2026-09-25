#!/bin/bash
# Runs one opus_session for duo3 under launchd so it survives agent restarts.
# Brief lives in the repo (briefs/), not /tmp - a missing brief must fail loudly,
# not launch a session with an empty prompt.
set -euo pipefail
cd /Users/octo/agentscii
BRIEF=/Users/octo/agentscii/briefs/duo3_s6.txt
[ -s "$BRIEF" ] || { echo "FATAL: brief missing or empty: $BRIEF"; exit 1; }
exec /usr/bin/python3 opus_session.py duo3 "$(cat "$BRIEF")"
