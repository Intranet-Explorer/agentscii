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
    open(p + ".critique.txt", "w").write("crit")
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


def test_apply_routes_every_answered_piece():
    """publish=yes -> unpacked/, answered no -> reviewed/ with answers,
    unanswered -> stays in pending/. Sidecars follow. First delivery under
    BASELINE_MIN is refused unless forced."""
    rs = review_sheet
    with tempfile.TemporaryDirectory() as d:
        pend, unp, rev = (os.path.join(d, x) for x in ("pending", "unpacked", "reviewed"))
        os.makedirs(pend)
        for n in ("_yes.ans", "_no.ans", "_skip.ans"):
            _piece(pend, n)
        design = os.path.join(d, "EXPERIMENT_DESIGN.txt")
        open(design, "w").write("FIRST DELIVERY: <not yet>\n")
        saved = (rs.PENDING, rs.UNPACKED, rs.REVIEWED, rs.DESIGN_TXT,
                 rs._deliver, harness._log_curation_event)
        rs.PENDING, rs.UNPACKED, rs.REVIEWED, rs.DESIGN_TXT = pend, unp, rev, design
        harness._log_curation_event = lambda *a: None
        # _deliver writes to state.db and REVIEWS.md; it has its own test.
        rs._deliver = lambda answers, hold=False: 0
        af = os.path.join(d, "a.json")
        no = {"file": "_no.ans", "publish": False, "reads": True, "good": False, "note": "weak"}
        json.dump([{"file": "_yes.ans", "publish": True, "reads": True, "good": True, "note": ""}, no,
                   {"file": "_skip.ans", "publish": None, "reads": None, "good": None, "note": ""}],
                  open(af, "w"))
        try:
            try:
                rs.apply(af)
                raise AssertionError("first delivery of 2 pieces was not refused")
            except ValueError as e:
                assert "BASELINE_TOO_SMALL" in str(e) and "with 2 reviewed" in str(e), e
            assert len(os.listdir(pend)) == 6, "a refused apply moved files"
            rs.apply(af, no_deliver=True)          # held batch: guard does not apply
            for n in ("_yes.ans", "_no.ans"):      # put them back for the forced run
                for f in os.listdir(unp if n == "_yes.ans" else rev):
                    os.rename(os.path.join(unp if n == "_yes.ans" else rev, f), os.path.join(pend, f))
            os.remove(os.path.join(pend, "_no.ans.review.json"))
            rs.apply(af, force=True)
        finally:
            (rs.PENDING, rs.UNPACKED, rs.REVIEWED, rs.DESIGN_TXT,
             rs._deliver, harness._log_curation_event) = saved
        assert sorted(os.listdir(unp)) == ["_yes.ans", "_yes.ans.critique.txt"], os.listdir(unp)
        assert sorted(os.listdir(rev)) == ["_no.ans", "_no.ans.critique.txt", "_no.ans.review.json"]
        assert json.load(open(os.path.join(rev, "_no.ans.review.json"))) == no
        assert sorted(os.listdir(pend)) == ["_skip.ans", "_skip.ans.critique.txt"], os.listdir(pend)
    print("  ok  yes -> unpacked, no -> reviewed + answers, unanswered stays; "
          "small first delivery refused unless forced")


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
        # REVIEWS_MD is a module constant, so redirect it too -- patching
        # ROOT alone silently wrote to the live workspace/REVIEWS.md.
        # DESIGN_TXT too: _send records the first delivery there.
        saved = (rs.ROOT, rs.REVIEWS_MD, rs.DESIGN_TXT)
        rs.ROOT = d
        rs.REVIEWS_MD = os.path.join(d, "workspace", "REVIEWS.md")
        rs.DESIGN_TXT = os.path.join(d, "EXPERIMENT_DESIGN.txt")
        open(rs.DESIGN_TXT, "w").write("FIRST DELIVERY: <not yet>\n")
        try:
            n = rs._deliver(answers)
            assert "<not yet>" not in open(rs.DESIGN_TXT).read(), "first delivery not recorded"
        finally:
            rs.ROOT, rs.REVIEWS_MD, rs.DESIGN_TXT = saved
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


def test_baseline_held_then_released():
    """Batch 1 must reach the agents NEVER, then exactly once on release."""
    import sqlite3
    import review_sheet as rs
    answers = [{"file": "_base.ans", "title": "BASE", "reads": True,
                "good": False, "publish": True, "note": "reads, shading flat"}]
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE human_messages (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "to_agent TEXT NOT NULL, text TEXT NOT NULL, timestamp REAL NOT NULL,"
                     "delivered INTEGER DEFAULT 0)")
        conn.commit(); conn.close()
        os.makedirs(os.path.join(d, "workspace"))
        saved = (rs.ROOT, rs.BASELINE_MD, rs.REVIEWS_MD, rs.DESIGN_TXT)
        rs.ROOT = d
        rs.DESIGN_TXT = os.path.join(d, "EXPERIMENT_DESIGN.txt")
        rs.BASELINE_MD = os.path.join(d, "private", "baseline_reviews.md")
        rs.REVIEWS_MD = os.path.join(d, "workspace", "REVIEWS.md")
        try:
            def sent():
                c = sqlite3.connect(db)
                rows = c.execute("SELECT to_agent, text FROM human_messages").fetchall()
                c.close(); return rows

            assert rs._deliver(answers, hold=True) == 1
            assert sent() == [], "HELD BATCH WAS SENT -- baseline destroyed"
            assert not os.path.exists(rs.REVIEWS_MD), "held batch leaked into REVIEWS.md"
            held = open(rs.BASELINE_MD).read()
            assert "BASELINE (not delivered)" in held and "shading flat" in held

            # outside workspace/, where the agents browse
            assert "workspace" not in os.path.relpath(rs.BASELINE_MD, d).split(os.sep)[0]

            assert rs.deliver_baseline() == 1
            rows = sent()
            assert {r[0] for r in rows} == {"artist", "curator"}, rows
            for _seat, txt in rows:
                assert "shading flat" in txt, "note not verbatim on release"
                assert "BASELINE" not in txt, "release still marked as held"
            assert "shading flat" in open(rs.REVIEWS_MD).read()
            assert not os.path.exists(rs.BASELINE_MD), "held file not consumed"

            # second release must not re-send
            before = len(sent())
            assert rs.deliver_baseline() == 0
            assert len(sent()) == before, "released the baseline twice"
        finally:
            rs.ROOT, rs.BASELINE_MD, rs.REVIEWS_MD, rs.DESIGN_TXT = saved
    print("  ok  baseline held (0 msgs), released once verbatim, not twice")


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
    test_apply_routes_every_answered_piece()
    test_deliver_reaches_both_seats()
    test_baseline_held_then_released()
    print("  all checks passed")


if __name__ == "__main__":
    main()
