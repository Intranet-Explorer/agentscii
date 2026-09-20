#!/usr/bin/env python3
"""corpus/progress_watchdog.py -- if the training log doesn't advance
for 10 minutes, capture a `sample <pid> 10` diagnostic and report
(user direction, 2026-09-19: "don't kill on this one, just capture").

Distinct from mem_watchdog.py (which kills on a memory threshold
breach): this one only watches for STALLED progress (log file mtime /
content unchanged) regardless of memory, and never kills -- it exists
to leave forensic evidence (a real stack sample) for a hang that
ISN'T caused by the memory pattern mem_watchdog.py catches, so a
future hang of unknown cause has something to diagnose from instead
of just "it stopped."

Usage:
    python3 corpus/progress_watchdog.py --pid 17159 --log corpus/training_run.log
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CORPUS_DIR))
import mem_watchdog as mw


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pid", type=int, required=True)
    ap.add_argument("--log", default=str(CORPUS_DIR / "training_run.log"))
    ap.add_argument("--stall-minutes", type=float, default=10.0)
    ap.add_argument("--check-interval", type=float, default=30.0)
    ap.add_argument("--sample-duration", type=int, default=10, help="seconds passed to `sample <pid> <duration>`")
    ap.add_argument("--out-dir", default=str(CORPUS_DIR / "progress_watchdog_samples"))
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    log_path = Path(args.log)
    last_size = log_path.stat().st_size if log_path.exists() else 0
    last_change_time = time.time()
    already_sampled_this_stall = False

    print(f"Watching {args.log} for {args.stall_minutes}min stalls on PID {args.pid} "
          f"(checking every {args.check_interval}s).")

    while True:
        if not mw.pid_alive(args.pid):
            print(f"PID {args.pid} no longer running -- exiting cleanly.")
            return

        cur_size = log_path.stat().st_size if log_path.exists() else 0
        if cur_size != last_size:
            last_size = cur_size
            last_change_time = time.time()
            already_sampled_this_stall = False
        else:
            stalled_minutes = (time.time() - last_change_time) / 60.0
            if stalled_minutes >= args.stall_minutes and not already_sampled_this_stall:
                ts = time.strftime("%Y%m%d_%H%M%S")
                sample_path = out_dir / f"sample_{ts}.txt"
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] STALL DETECTED: "
                      f"log unchanged for {stalled_minutes:.1f}min. "
                      f"Capturing sample {args.sample_duration}s -> {sample_path}")
                try:
                    result = subprocess.run(
                        ["sample", str(args.pid), str(args.sample_duration)],
                        capture_output=True, text=True, timeout=args.sample_duration + 30,
                    )
                    sample_path.write_text(result.stdout + "\n\nSTDERR:\n" + result.stderr)
                    print(f"Sample captured: {sample_path} ({len(result.stdout)} chars)")
                except Exception as e:
                    sample_path.write_text(f"sample command failed: {e}")
                    print(f"Sample capture FAILED: {e}")
                already_sampled_this_stall = True
                # Reset the stall clock after sampling so a hang that's
                # STILL going stall_minutes later triggers a fresh
                # sample rather than going silent after the first one
                # -- a permanent hang should leave periodic evidence,
                # not just a single snapshot from minute 10.
                last_change_time = time.time()

        time.sleep(args.check_interval)


if __name__ == "__main__":
    main()
