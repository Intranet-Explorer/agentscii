#!/usr/bin/env python3
"""The seat's bash must not reach any loopback service (the dashboards, which
can publish and control the harness; ollama), while the internet stays open.

Runs the seat's bash exactly as harness.py does, then repeats the loopback
probes with LOOPBACK_DENY removed from the profile: if those don't connect,
the test can't tell a working rule from a dead server and fails.

  python3 test_agent_loopback.py
"""
import os
import socket
import subprocess
import sys

sys.path.insert(0, os.path.expanduser("~/agentscii"))
import harness  # noqa: E402

DASH = 8766            # agentscii dashboard
EXTERNAL = "https://16colo.rs/"


def bash(cmd, profile):
    return subprocess.run([harness._SANDBOX_EXEC, "-p", profile, "/bin/bash", "-c", cmd],
                          cwd=str(harness.WORKSPACE), env=harness._agent_env(),
                          capture_output=True, text=True, timeout=40)


# curl exit 7 = could not connect. -w prints the HTTP code; 000 = no response.
PROBES = [
    ("GET control/status", f"curl -s -m 5 -o /dev/null -w '%{{http_code}}' "
                           f"http://127.0.0.1:{DASH}/api/control/status"),
    ("POST review/apply", f"curl -s -m 5 -o /dev/null -w '%{{http_code}}' -X POST "
                          f"-H 'X-Agentscii: 1' -H 'Content-Type: application/json' "
                          # '{}' is refused by check_answers before any side
                          # effect, so the control run can't apply anything.
                          f"-d '{{}}' http://127.0.0.1:{DASH}/api/review/apply"),
    ("localhost name", f"curl -s -m 5 -o /dev/null -w '%{{http_code}}' "
                       f"http://localhost:{DASH}/api/control/status"),
    ("python socket", f"python3 -c \"import socket; socket.create_connection(('127.0.0.1', {DASH}), 5)\""),
]


def _listening(port):
    try:
        socket.create_connection(("127.0.0.1", port), 2).close()
        return True
    except OSError:
        return False


def main():
    assert harness._sandbox_ok(), f"sandbox not active: {harness._SANDBOX_STATE['why']}"
    if not _listening(DASH):
        sys.exit(f"DASHBOARD_NOT_LISTENING on {DASH}: nothing to probe -- nothing was verified")
    live = harness._sandbox_profile()
    assert harness.LOOPBACK_DENY in live, "LOOPBACK_DENY missing from the seat profile"

    for label, cmd in PROBES:
        r = bash(cmd, live)
        assert r.returncode != 0 and r.stdout.strip() in ("", "000"), \
            f"REACHED loopback via {label}: exit={r.returncode} out={r.stdout[:80]!r}"
    print(f"  ok  {len(PROBES)} loopback probes to :{DASH} refused from the seat sandbox")

    opus = harness._opus_sandbox_profile()
    assert harness.LOOPBACK_DENY in opus, "LOOPBACK_DENY missing from the Opus profile"
    for label, cmd in PROBES:
        r = bash(cmd, opus)
        assert r.returncode != 0 and r.stdout.strip() in ("", "000"), \
            f"REACHED loopback from the Opus sandbox via {label}: exit={r.returncode}"
    r = bash(f"curl -s -m 20 -o /dev/null -w '%{{http_code}}' https://api.anthropic.com/", opus)
    assert r.returncode == 0 and r.stdout[:1] in "2345", f"Opus sandbox lost the API: {r.stdout!r}"
    print(f"  ok  same probes refused from the Opus sandbox; api.anthropic.com reachable (HTTP {r.stdout})")

    r = bash(f"curl -s -m 20 -o /dev/null -w '%{{http_code}}' {EXTERNAL}", live)
    assert r.returncode == 0 and r.stdout.startswith(("2", "3")), \
        f"internet broken: exit={r.returncode} code={r.stdout!r} {r.stderr[:120]}"
    print(f"  ok  {EXTERNAL} reachable (HTTP {r.stdout})")

    # Negative control: same profile minus the rule must connect.
    bare = live.replace(harness.LOOPBACK_DENY, "")
    for label, cmd in PROBES:
        r = bash(cmd, bare)
        assert r.returncode == 0, f"control: {label} did not connect without the rule " \
                                  f"(exit={r.returncode}) -- test is vacuous"
    print("  ok  control: with the rule removed, every probe connects")
    print("  all checks passed")


if __name__ == "__main__":
    main()
