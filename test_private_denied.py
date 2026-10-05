#!/usr/bin/env python3
"""The agents must not be able to read ~/agentscii-private/.

It holds the operator's own judgements: the blind calibration answers and the
HELD batch-1 baseline reviews. The agents are the subject of that experiment,
so a read would both destroy the baseline and hand them labels they never
earned.

Runs the seat's bash exactly as harness.py does -- same profile, same cwd,
same stripped env -- rather than approximating it, so this test fails if the
real invocation ever diverges from the profile.

  python3 test_private_denied.py
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.expanduser("~/agentscii"))
import harness  # noqa: E402

PRIVATE = os.path.expanduser("~/agentscii-private")

# Strings that exist ONLY inside the private files. Denial messages quote the
# path, so matching on the path would false-positive on a successful block.
SECRETS = ("reads as subject", "BASELINE (not delivered)", "HELD baseline",
           "reads_as_subject", "well made", "intended")


def seat_bash(cmd):
    """Exactly harness.py's bash tool invocation."""
    return subprocess.run(
        [harness._SANDBOX_EXEC, "-p", harness._sandbox_profile(),
         "/bin/bash", "-c", cmd],
        cwd=str(harness.WORKSPACE), env=harness._agent_env(),
        capture_output=True, text=True, timeout=30)


def test_denied():
    assert harness._sandbox_ok(), f"sandbox not active: {harness._SANDBOX_STATE['why']}"
    probes = [
        ("cat the held batch", f"cat {PRIVATE}/baseline_reviews.md"),
        ("ls the directory", f"ls {PRIVATE}/"),
        ("cat the answers", f"cat {PRIVATE}/calibration/calibration_tyler.json"),
        ("stat metadata", f"stat {PRIVATE}/"),
        ("find from home", f"find {PRIVATE} -type f"),
        ("python open()", f"python3 -c \"print(open('{PRIVATE}/baseline_reviews.md').read())\""),
        ("symlink hop", f"ln -sf {PRIVATE} /tmp/_pv_probe 2>/dev/null; "
                        f"cat /tmp_pv_probe/baseline_reviews.md 2>/dev/null; "
                        f"cat /tmp/_pv_probe/baseline_reviews.md"),
    ]
    for label, cmd in probes:
        r = seat_bash(cmd)
        blob = r.stdout + r.stderr
        leaked = [s for s in SECRETS if s in blob]
        assert not leaked, f"LEAKED via {label}: {leaked}"
        assert r.returncode != 0, f"NOT BLOCKED via {label}: {blob[:200]}"
    print(f"  ok  {len(probes)} read paths into agentscii-private all blocked")


def test_agents_still_work():
    """A deny rule that breaks the agents is a worse bug than the leak."""
    for label, cmd in [
            ("read workspace", "cat ~/agentscii/workspace/STYLE.md | head -1"),
            ("write workspace", "touch ~/agentscii/workspace/.sbprobe && rm -f ~/agentscii/workspace/.sbprobe"),
            ("read the repo", "ls ~/agentscii/*.py | head -2")]:
        r = seat_bash(cmd)
        assert r.returncode == 0, f"deny rule broke {label}: {(r.stderr or '')[:200]}"
    print("  ok  workspace read/write and repo read still work")


if __name__ == "__main__":
    if not os.path.exists(PRIVATE):
        # An absent directory is not a passing test. (standing rule)
        sys.exit(f"PRIVATE_DIR_MISSING: {PRIVATE} -- nothing was verified")
    test_denied()
    test_agents_still_work()
    print("  all checks passed")
