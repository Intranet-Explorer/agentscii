#!/usr/bin/env python3
"""corpus/mem_logger.py -- log pid RSS + system free + swap used every
60s to a file (user direction, 2026-09-19: "so a hang leaves
evidence"). Runs independently of mem_watchdog.py (which acts on
thresholds and exits after a kill or when the pid dies) -- this one
just records, indefinitely, until the watched pid exits.

Usage:
    python3 corpus/mem_logger.py --pid 17159 --out corpus/mem_log.jsonl
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CORPUS_DIR))
import mem_watchdog as mw


def get_pid_rss_mb(pid):
    """RSS in MB via ps (macOS reports RSS in KB by default)."""
    out = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    if not out:
        return None
    try:
        return int(out) / 1024.0
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pid", type=int, required=True)
    ap.add_argument("--out", default=str(CORPUS_DIR / "mem_log.jsonl"))
    ap.add_argument("--interval", type=float, default=60.0)
    args = ap.parse_args()

    print(f"Logging memory for PID {args.pid} every {args.interval}s to {args.out}")

    with open(args.out, "a") as f:
        while True:
            if not mw.pid_alive(args.pid):
                print(f"PID {args.pid} no longer running -- stopping logger.")
                return
            entry = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "epoch": time.time(),
                "pid_rss_mb": get_pid_rss_mb(args.pid),
                "system_available_mb": mw.get_free_mem_mb(),
                "swap_used_mb": mw.get_swap_used_mb(),
            }
            f.write(json.dumps(entry) + "\n")
            f.flush()
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
