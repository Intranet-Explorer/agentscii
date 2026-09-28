"""Validation for self_check's repeated-row test.

The check must separate the pieces we already know the verdict on. If this
fails, the check is not shippable -- a check that cannot tell known-bad from
known-good is worse than none, because it launders a bad piece as passing.

  known bad : _mask, _mask.v1  (100% generated; 10 of 21 grid rows identical)
  known good: duo3.s7 (shipped as pack55) + accepted gallery pieces

Run: python3 test_self_check.py
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness

INK = {"\u2588": 1.0, "\u2593": .75, "\u2592": .5, "\u2591": .25,
       "\u2580": .5, "\u2584": .5, " ": 0.0}


def rows_from_ans(path):
    grid, _ = harness._parse_ans_grid(path)
    if not grid:
        return []
    maxr = max(r for r, _ in grid)
    maxc = max(c for _, c in grid)
    return [[grid.get((r, c), (" ", 7, 0)) for c in range(maxc + 1)]
            for r in range(maxr + 1)]


def longest_repeat_run(rows):
    """Same rule as canvas_tools.self_check, on an .ans instead of a canvas."""
    profs = [[INK.get(ch, .6) for ch, fg, bg in row] for row in rows]
    runs, start = [], None
    for i in range(1, len(rows)):
        a, b = profs[i - 1], profs[i]
        if max(sum(a) / len(a), sum(b) / len(b)) <= 0.03:
            same = False
        else:
            same = sum(1 for x, y in zip(a, b) if abs(x - y) < 1e-9) / len(a) >= 0.90
        if same and start is None:
            start = i - 1
        elif not same and start is not None:
            runs.append((start, i - 1)); start = None
    if start is not None:
        runs.append((start, len(rows) - 1))
    runs = [(a, b) for a, b in runs if b > a]
    return max((b - a + 1 for a, b in runs), default=0), runs


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    bad = [("_mask", "workspace/rejected/_mask.ans"),
           ("_mask.v1", "workspace/rejected/_mask.v1.ans")]
    good = [("duo3.s7", "workspace/scratch/duo3_sessions/duo3.s7.ans")]
    good += [(os.path.basename(p), p)
             for p in sorted(glob.glob(os.path.join(root, "workspace/gallery/pack5*/*.ans")))[:5]]

    print(f"{'piece':34s} {'verdict':8s} {'rows':>5s} {'longest repeat run':>19s}")
    worst_good, best_bad = 0, 99
    for label, path in bad + good:
        full = path if os.path.isabs(path) else os.path.join(root, path)
        if not os.path.exists(full):
            print(f"{label:34s} MISSING")
            continue
        rows = rows_from_ans(full)
        longest, runs = longest_repeat_run(rows)
        kind = "BAD" if (label, path) in bad else "good"
        print(f"{label:34s} {kind:8s} {len(rows):5d} {longest:19d}")
        if kind == "BAD":
            best_bad = min(best_bad, longest)
        else:
            worst_good = max(worst_good, longest)

    print()
    print(f"worst known-good run: {worst_good}   best known-bad run: {best_bad}")
    assert best_bad >= 6, f"check missed a known-bad piece (run {best_bad})"
    assert worst_good <= 5, f"check fires on known-good work (run {worst_good})"
    assert best_bad > worst_good, "known-bad and known-good overlap: not shippable"
    print("PASS: the check separates known-bad from known-good.")


if __name__ == "__main__":
    main()
