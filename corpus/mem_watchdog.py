#!/usr/bin/env python3
"""Kill the training process before memory pressure locks up the machine.

Polls every 15s. If swap used > 1GB or available memory < 4GB, sends
SIGKILL and writes a report with the last logged iteration. Metal OOM can
leave the machine stuck, so this acts before the crash.

Usage:
    python3 corpus/mem_watchdog.py --pid 17159 --log corpus/training_run.log
"""
import argparse
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent


def get_swap_used_mb():
    """macOS: sysctl vm.swapusage -> 'total = 2048.00M  used = 644.06M  free = ...'"""
    out = subprocess.run(["sysctl", "vm.swapusage"], capture_output=True, text=True).stdout
    m = re.search(r"used\s*=\s*([\d.]+)M", out)
    return float(m.group(1)) if m else None


def get_free_mem_mb():
    """Available memory in MB on macOS: free + inactive + speculative + purgeable pages.

    'Pages free' alone badly undercounts, since macOS fills idle RAM with
    reclaimable cache.
    """
    out = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    m = re.search(r"page size of (\d+) bytes", out)
    page_size = int(m.group(1)) if m else 16384

    def _pages(label):
        m2 = re.search(rf"{label}:\s+(\d+)\.?", out)
        return int(m2.group(1)) if m2 else 0

    free = _pages("Pages free")
    inactive = _pages("Pages inactive")
    speculative = _pages("Pages speculative")
    purgeable = _pages("Pages purgeable")
    if free == 0 and inactive == 0:
        return None
    return (free + inactive + speculative + purgeable) * page_size / (1024 * 1024)


def last_logged_iteration(log_path):
    """Parse the training log for the highest 'Iter N' seen so far."""
    try:
        text = Path(log_path).read_text(errors="replace")
    except Exception:
        return None
    matches = re.findall(r"Iter (\d+):", text)
    return int(matches[-1]) if matches else None


def pid_alive(pid):
    """True if pid exists and is not a zombie. kill -0 alone succeeds on zombies."""
    try:
        subprocess.run(["kill", "-0", str(pid)], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        return False
    state = subprocess.run(["ps", "-o", "state=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    if state.startswith("Z"):
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pid", type=int, required=True, help="training process PID to watch/kill")
    ap.add_argument("--log", default=str(CORPUS_DIR / "training_run.log"))
    ap.add_argument("--swap-limit-mb", type=float, default=1024.0, help="kill if swap used exceeds this (1GB default)")
    ap.add_argument("--free-limit-mb", type=float, default=4096.0, help="kill if free memory drops below this (4GB default)")
    ap.add_argument("--poll-interval", type=float, default=15.0)
    ap.add_argument("--out", default=str(CORPUS_DIR / "mem_watchdog_kill_report.json"))
    args = ap.parse_args()

    print(f"Watching PID {args.pid}, polling every {args.poll_interval}s. "
          f"Kill thresholds: swap > {args.swap_limit_mb}MB or free < {args.free_limit_mb}MB.")

    while True:
        if not pid_alive(args.pid):
            print(f"PID {args.pid} is no longer running -- exiting watchdog cleanly (nothing to kill).")
            return

        swap_mb = get_swap_used_mb()
        free_mb = get_free_mem_mb()
        ts = time.strftime("%Y-%m-%d %H:%M:%S")

        breach = None
        if swap_mb is not None and swap_mb > args.swap_limit_mb:
            breach = f"swap used {swap_mb:.0f}MB > limit {args.swap_limit_mb:.0f}MB"
        elif free_mb is not None and free_mb < args.free_limit_mb:
            breach = f"free memory {free_mb:.0f}MB < limit {args.free_limit_mb:.0f}MB"

        if breach:
            iteration = last_logged_iteration(args.log)
            print(f"[{ts}] THRESHOLD BREACHED: {breach}. Killing PID {args.pid}. "
                  f"Last logged iteration: {iteration}")
            import json
            report = {
                "killed_at": ts,
                "pid": args.pid,
                "reason": breach,
                "swap_used_mb": swap_mb,
                "free_mem_mb": free_mb,
                "last_logged_iteration": iteration,
            }
            Path(args.out).write_text(json.dumps(report, indent=2))
            try:
                import os
                os.kill(args.pid, signal.SIGKILL)
                print(f"Sent SIGKILL to {args.pid}. Report written to {args.out}.")
            except ProcessLookupError:
                print(f"PID {args.pid} already gone by the time we tried to kill it.")
            return

        print(f"[{ts}] OK -- swap={swap_mb:.0f}MB free={free_mb:.0f}MB "
              f"(limits: swap<{args.swap_limit_mb:.0f}MB free>{args.free_limit_mb:.0f}MB)")
        time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()
