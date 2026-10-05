#!/usr/bin/env python3
"""The agents must not be able to read ~/agentscii-private/.

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
# A file the test writes and removes, so the probes always have a real target.
FIXTURE = os.path.join(PRIVATE, "_sbprobe_fixture.txt")
CANARY = "SBPROBE-CANARY-7f3a9c"
SECRETS = (CANARY, "reads as subject", "BASELINE (not delivered)", "HELD baseline",
           "reads_as_subject", "well made", "intended")


def seat_bash(cmd):
    """Exactly harness.py's bash tool invocation."""
    return subprocess.run(
        [harness._SANDBOX_EXEC, "-p", harness._sandbox_profile(),
         "/bin/bash", "-c", cmd],
        cwd=str(harness.WORKSPACE), env=harness._agent_env(),
        capture_output=True, text=True, timeout=30)


def opus_bash(cmd):
    """The Opus artist's shell: harness._maybe_sandbox_claude's wrapper."""
    return subprocess.run(
        ["/usr/bin/sandbox-exec", "-p", harness._opus_sandbox_profile(),
         "/bin/bash", "-c", cmd],
        cwd=str(harness.PROJECT_DIR), capture_output=True, text=True, timeout=30)


def bare_bash(cmd):
    return subprocess.run(["/bin/bash", "-c", cmd], capture_output=True,
                          text=True, timeout=30)


def test_denied(run, name):
    assert harness._sandbox_ok(), f"sandbox not active: {harness._SANDBOX_STATE['why']}"
    probes = [
        ("cat the fixture", f"cat {FIXTURE}"),
        ("cat the held batch", f"cat {PRIVATE}/baseline_reviews.md"),
        ("ls the directory", f"ls {PRIVATE}/"),
        ("cat the answers", f"cat {PRIVATE}/calibration/calibration_tyler.json"),
        ("stat metadata", f"stat {PRIVATE}/"),
        ("find from home", f"find {PRIVATE} -type f"),
        ("grep -r", f"grep -r {CANARY} {PRIVATE}"),
        ("python open()", f"python3 -c \"print(open('{FIXTURE}').read())\""),
        ("symlink hop", f"ln -sfn {PRIVATE} /tmp/_pv_probe && "
                        f"cat /tmp/_pv_probe/{os.path.basename(FIXTURE)}"),
    ]
    for label, cmd in probes:
        r = run(cmd)
        blob = r.stdout + r.stderr
        leaked = [s for s in SECRETS if s in blob]
        assert not leaked, f"[{name}] LEAKED via {label}: {leaked}"
        assert r.returncode != 0, f"[{name}] NOT BLOCKED via {label}: {blob[:200]}"
    print(f"  ok  [{name}] {len(probes)} read paths into agentscii-private all blocked")


def test_fixture_readable_unsandboxed():
    """Positive control: the fixture probes would leak without the sandbox."""
    for cmd in (f"cat {FIXTURE}", f"grep -r {CANARY} {PRIVATE}",
                f"ln -sfn {PRIVATE} /tmp/_pv_probe && cat /tmp/_pv_probe/{os.path.basename(FIXTURE)}"):
        r = bare_bash(cmd)
        assert CANARY in r.stdout, f"control failed, probe is vacuous: {cmd}"
    print("  ok  fixture probes leak without the sandbox (control)")


def test_agents_still_work():
    """A deny rule that breaks the agents is a worse bug than the leak."""
    for label, cmd in [
            ("read workspace", "cat ~/agentscii/workspace/STYLE.md | head -1"),
            ("write workspace", "touch ~/agentscii/workspace/.sbprobe && rm -f ~/agentscii/workspace/.sbprobe"),
            ("read the repo", "ls ~/agentscii/*.py | head -2")]:
        r = seat_bash(cmd)
        assert r.returncode == 0, f"deny rule broke {label}: {(r.stderr or '')[:200]}"
    print("  ok  workspace read/write and repo read still work")


def test_lab_dir():
    """Seats can't read the lab dir; Opus runs can write and read it."""
    lab = str(harness.LAB_DIR)
    os.makedirs(lab, exist_ok=True)
    probe = os.path.join(lab, "_sbprobe_lab.txt")
    with open(probe, "w") as f:
        f.write(CANARY + "\n")
    try:
        r = seat_bash(f"cat {probe}; ls {lab}")
        assert CANARY not in r.stdout + r.stderr and r.returncode != 0, "seat read the lab dir"
        w = os.path.join(lab, "_sbprobe_opus.txt")
        r = opus_bash(f"echo ok > {w} && cat {probe}")
        assert r.returncode == 0 and CANARY in r.stdout, f"Opus can't use the lab dir: {r.stderr[:200]}"
        os.remove(w)
    finally:
        os.remove(probe)
    print("  ok  lab dir: seat denied, Opus read+write allowed")


if __name__ == "__main__":
    if not os.path.exists(PRIVATE):
        # An absent directory is not a passing test. (standing rule)
        sys.exit(f"PRIVATE_DIR_MISSING: {PRIVATE} -- nothing was verified")
    with open(FIXTURE, "w") as f:
        f.write(CANARY + "\n")
    try:
        test_fixture_readable_unsandboxed()
        test_denied(seat_bash, "seat")
        test_denied(opus_bash, "opus")
        test_agents_still_work()
        test_lab_dir()
    finally:
        os.remove(FIXTURE)
        if os.path.islink("/tmp/_pv_probe"):
            os.remove("/tmp/_pv_probe")
    assert not os.path.exists(FIXTURE), f"fixture left behind: {FIXTURE}"
    print("  all checks passed")
