#!/usr/bin/env python3
"""Checks for the advisory subject check and the manual publish gate.

  python3 test_advisory_gate.py

Covers the two things that would silently break:
  - a subject MISMATCH must no longer move the file or override the accept,
    and must leave a subject_advisory row;
  - a refused/errored check must log DID_NOT_RUN, not read as a pass
    (standing rule: a refusal reports distinctly from a pass);
  - accepts must land in pending/, never straight in gallery/unpacked/;
  - --apply must publish only publish=true and carry sidecars along.
"""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.expanduser("~/agentscii"))
import harness
import review_sheet

ANS = "\x1b[0;37;40m" + "#" * 20 + "\n"


def _piece(d, name="_probe.ans", title="PROBE"):
    p = os.path.join(d, name)
    with open(p, "w") as f:
        f.write(f"\x1b[0m{title}\n" + ANS)
    open(p.replace(".ans", ".critique.txt"), "w").write("crit")
    return p


def test_mismatch_is_advisory(monkey):
    """A mismatch logs and changes nothing -- no move, no override."""
    rows = []
    monkey("_log_curation_event", lambda *a: rows.append(a))
    monkey("opus_subject_check", lambda s: {"status": "mismatch", "message": "reads as a duck"})
    monkey("opus_pairwise_regression_check", lambda *a, **k: {"status": "ok", "message": ""})
    monkey("opus_curate_review", lambda *a, **k: {"status": "accept", "message": "fine"})
    with tempfile.TemporaryDirectory() as d:
        src = _piece(d)
        moved = []
        monkey("_move_with_sidecars", lambda s, dd, **k: moved.append(dd) or harness.Path(
            os.path.join(str(dd), os.path.basename(s))))
        monkey("_touch_subject", lambda *a, **k: None)
        msg, dest = harness.curate_piece_opus_gated(harness.Path(src), "accept", "c", shift_id=1)
    assert rows and rows[0][1] == "subject_advisory", rows
    assert "mismatch" in rows[0][4], rows[0][4]
    assert "rejected" not in str(dest), f"mismatch still rejected: {dest}"
    assert moved == [harness.PENDING], f"accept did not go to pending: {moved}"
    print("  ok  mismatch is advisory, accept survives, lands in pending/")


def test_refusal_is_loud(monkey):
    """A check that could not run must not look like a pass."""
    rows = []
    monkey("_log_curation_event", lambda *a: rows.append(a))
    monkey("opus_subject_check", lambda s: {"status": "error", "message": "cap reached"})
    monkey("opus_pairwise_regression_check", lambda *a, **k: {"status": "ok", "message": ""})
    monkey("opus_curate_review", lambda *a, **k: {"status": "accept", "message": "fine"})
    monkey("_move_with_sidecars", lambda s, dd, **k: harness.Path(
        os.path.join(str(dd), os.path.basename(s))))
    monkey("_touch_subject", lambda *a, **k: None)
    with tempfile.TemporaryDirectory() as d:
        harness.curate_piece_opus_gated(harness.Path(_piece(d)), "accept", "c", shift_id=1)
    assert rows, "refusal logged nothing"
    assert "DID_NOT_RUN" in rows[0][4], rows[0][4]
    print("  ok  a refused check logs DID_NOT_RUN, not a silent pass")


def test_apply_publishes_only_approved():
    """--apply moves publish=true (with sidecars) and holds the rest."""
    with tempfile.TemporaryDirectory() as d:
        pend, unp = os.path.join(d, "pending"), os.path.join(d, "unpacked")
        os.makedirs(pend); os.makedirs(unp)
        yes, no = _piece(pend, "_yes.ans"), _piece(pend, "_no.ans")
        review_sheet.PENDING, review_sheet.UNPACKED = pend, unp
        harness._log_curation_event = lambda *a: None
        # _deliver writes to state.db and REVIEWS.md; it has its own test.
        # Stub it so this test can never touch the live DB, and PUT IT BACK
        # afterwards -- a leaked stub silently voided the delivery test.
        real_deliver = review_sheet._deliver
        review_sheet._deliver = lambda answers: 0
        af = os.path.join(d, "a.json")
        json.dump([{"file": "_yes.ans", "publish": True, "reads": True, "good": True, "note": ""},
                   {"file": "_no.ans", "publish": False, "reads": True, "good": False, "note": "weak"}],
                  open(af, "w"))
        try:
            review_sheet.apply(af)
        finally:
            review_sheet._deliver = real_deliver
        assert os.path.exists(os.path.join(unp, "_yes.ans")), "approved piece not published"
        assert os.path.exists(os.path.join(unp, "_yes.critique.txt")), "sidecar left behind"
        assert os.path.exists(os.path.join(pend, "_no.ans")), "held piece was published anyway"
        assert not os.path.exists(os.path.join(unp, "_no.ans")), "unapproved piece published"
    print("  ok  --apply publishes only publish=true, sidecars follow")


def test_deliver_reaches_both_seats():
    """A review batch must reach both seats and land in REVIEWS.md verbatim."""
    import sqlite3
    import review_sheet as rs
    answers = [
        {"file": "_probe.ans", "title": "PROBE", "reads": True, "good": False,
         "publish": False, "note": "reads but the shading is mush"},
        {"file": "_other.ans", "title": "OTHER", "reads": None, "good": None,
         "publish": None, "note": ""},          # never looked at -> skipped
    ]
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE human_messages (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "to_agent TEXT NOT NULL, text TEXT NOT NULL, timestamp REAL NOT NULL,"
                     "delivered INTEGER DEFAULT 0)")
        conn.commit(); conn.close()
        os.makedirs(os.path.join(d, "workspace"))
        saved_root = rs.ROOT
        rs.ROOT = d
        try:
            n = rs._deliver(answers)
        finally:
            rs.ROOT = saved_root
        assert n == 1, f"skipped-piece handling wrong: {n}"
        conn = sqlite3.connect(db)
        rows = conn.execute("SELECT to_agent, text FROM human_messages").fetchall()
        conn.close()
        assert {r[0] for r in rows} == {"artist", "curator"}, rows
        for _seat, txt in rows:
            assert "reads but the shading is mush" in txt, "note not verbatim"
            assert "_probe" in txt and "_other" not in txt
            assert "SEPARATE" in txt, "reads/good separation not stated"
            assert "Do NOT edit METHOD.md" in txt, "no-auto-edit rule missing"
        md = open(os.path.join(d, "workspace", "REVIEWS.md")).read()
        assert "reads but the shading is mush" in md and "_probe" in md
    print("  ok  verdicts reach both seats verbatim + REVIEWS.md, blanks skipped")


def main():
    saved = {}

    def monkey(name, fn):
        saved.setdefault(name, getattr(harness, name))
        setattr(harness, name, fn)

    try:
        test_mismatch_is_advisory(monkey)
        test_refusal_is_loud(monkey)
    finally:
        for k, v in saved.items():
            setattr(harness, k, v)
    test_apply_publishes_only_approved()
    test_deliver_reaches_both_seats()
    print("  all checks passed")


if __name__ == "__main__":
    main()
